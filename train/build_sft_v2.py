"""Zbiór SFT v2 wierny wejściu harnessu: te same funkcje promptu co harness/run_exam.py, kontekst RAG z tego samego wyszukiwania.

    python train/build_sft_v2.py [--no-polqa] [--val 0.03]
Wejście: data/sft/{real_cke,synthetic_items,essays,e5_items}.jsonl; bazy do kontekstu: data/kb/{kompendium,timeline,persons,terms}.jsonl
Wynik (data/sft/v2/):
  train_answer.jsonl / val_answer.jsonl  — sama odpowiedź (modele myślące, trening z --mask-think),
  train_think.jsonl  / val_think.jsonl   — `<think>uzasadnienie</think>` + odpowiedź (bazy T2),
  manifest.jsonl (metadane każdego przykładu) i STATS.md.
Co odtwarzamy z harnessu: prompt systemowy, „Zadanie N (p pkt)”, źródła ze znacznikami `[Obraz: …]`, dopisek o formacie przy
zamkniętych, blok „Materiały pomocnicze” (RAFT: trafny fakt + wyniki wyszukiwarki / same wyniki / bez kontekstu), kompendium przy
eseju, prośba HyDE i dopytanie o numer tematu eseju (rozmowy wieloturowe: strata tylko na ostatniej odpowiedzi).
"""

import argparse
import hashlib
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "harness"))
sys.path.insert(0, str(ROOT / "eval"))
sys.path.insert(0, str(ROOT / "train"))
from run_exam import HYDE_PROMPT, SYSTEM, NoteRetriever, Retriever, build_body, build_text, item_type  # noqa: E402
from topics import scope_of  # noqa: E402
from analyze import epoch_of  # noqa: E402
from build_sft import dedup, exam_id, EVAL_SETS  # noqa: E402

SOURCES = ["real_cke.jsonl", "synthetic_items.jsonl", "essays.jsonl", "e5_items.jsonl"]
KB_FILES = ["kompendium.jsonl", "kompendium_extra.jsonl", "timeline.jsonl", "persons.jsonl", "terms.jsonl"]
RAG_KINDS = {"podaj", "rozstrz", "open", "essay"}
TOPIC_Q = "Podaj tylko numer tematu, który wybrałeś (jedna cyfra)."


def bucket(key, salt):
    return int(hashlib.md5(f"{salt}:{key}".encode()).hexdigest(), 16) % 100


def load_kb():
    """Wszystkie bazy jako notatki {title, subtopic, text}; wpisy osi czasu / postaci / pojęć sprowadzone do tego formatu."""
    path = ROOT / "data" / "kb" / "kb_all_notes.jsonl"
    rows = []
    for name in KB_FILES:
        f = ROOT / "data" / "kb" / name
        if not f.exists():
            continue
        for l in open(f, encoding="utf-8"):
            r = json.loads(l)
            title = r.get("title") or r.get("name") or r.get("event") or r.get("term") or ""
            text = r.get("text") or r.get("description") or r.get("summary") or json.dumps(r, ensure_ascii=False)
            rows.append({"title": str(title), "subtopic": str(r.get("subtopic") or r.get("years") or r.get("year") or ""),
                         "text": str(text)})
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return NoteRetriever(path), len(rows)


def pseudo_item(r):
    """Rekord danych → zadanie w formacie exam.json (to widzi harness)."""
    return {"id": exam_id(r), "max_points": r.get("max_points", 1), "question": r["question"],
            "source_text": r.get("source_text", "") or "", "answer_format": r.get("answer_format", ""),
            "images": [{"path": p} for p in r.get("image_refs", []) if str(p).startswith("images/")]}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--val", type=float, default=0.03)
    p.add_argument("--dup", type=float, default=0.4)
    p.add_argument("--no-polqa", action="store_true", help="bez indeksu PolQA (kontekst tylko z baz notatek)")
    p.add_argument("--hyde-examples", type=int, default=500)
    p.add_argument("--topic-examples", type=int, default=150)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--no-raft", action="store_true", help="bez kontekstu RAG i bez kompendium przy eseju (przepis v1 na nowych danych)")
    p.add_argument("--out-dir", default="data/sft/v2")
    a = p.parse_args()
    rnd = random.Random(a.seed)
    out = ROOT / a.out_dir
    out.mkdir(parents=True, exist_ok=True)

    retriever = None if a.no_polqa else Retriever(ROOT / "data" / "kb" / "polqa_index")
    notes, n_notes = load_kb()
    essay_notes = NoteRetriever(ROOT / "data" / "kb" / "kompendium.jsonl")

    # rekordy + deduplikacja (ta sama co w v1) i filtr zbieżności z arkuszami
    recs, skipped = [], Counter()
    for name in SOURCES:
        f = ROOT / "data" / "sft" / name
        if not f.exists():
            continue
        for l in open(f, encoding="utf-8"):
            r = json.loads(l)
            if not r.get("model_answer") or not r.get("question"):
                skipped["empty"] += 1
            elif r.get("verified") is False:
                skipped["unverified"] += 1
            elif r.get("needs_image"):
                skipped["image_without_file"] += 1
            elif r.get("leak") and r.get("subtype") in ("podaj", "rozstrzygnij"):
                skipped["leak"] += 1
            else:
                r.setdefault("origin", name.split(".")[0])
                recs.append(r)
    wrapped = [{"messages": [{}, {"content": r["question"]}, {"content": r["model_answer"]}],
                "meta": {"origin": "synthetic" if r.get("origin") == "synthetic" else r.get("origin"), "section": r.get("section"),
                         "type": r.get("type"), "group": r.get("group"), "dup_text": f"{r['question']} {r['model_answer']}",
                         "idx": i}} for i, r in enumerate(recs)]
    for w in wrapped:
        if w["meta"]["origin"] != "synthetic":
            w["meta"].pop("dup_text")
    kept, skipped["near_dup"] = dedup(wrapped, a.dup)
    recs = [recs[w["meta"]["idx"]] for w in kept]
    norm = lambda s: " ".join("".join(ch.lower() if ch.isalnum() else " " for ch in s).split())[:120]
    seen = set()
    for name in EVAL_SETS:
        f = ROOT / "eval" / "data" / f"{name}.jsonl"
        if f.exists():
            seen |= {norm(json.loads(l)["question"]) for l in open(f, encoding="utf-8")}
    before = len(recs)
    recs = [r for r in recs if norm(r["question"]) not in seen]
    skipped["eval_overlap"] = before - len(recs)

    examples = []  # (split, variant-agnostic example)
    for r in recs:
        item = pseudo_item(r)
        kind = item_type(item)
        body = build_body(item, kind)
        key = r.get("id") or r["question"][:80]
        ctx, rag_mode, gold_in = [], "none", False
        if a.no_raft:
            pass
        elif kind == "essay":
            ctx, rag_mode = essay_notes.search(r["question"], 3), "kb_essay"
        elif kind in RAG_KINDS:
            b = bucket(key, "rag")
            if b < 80:
                query = f"{r.get('hyde', '')} {r['question']} {item['source_text'][:600]}"
                ctx = retriever.search(query, 3) if retriever else []
                ctx += notes.search(query, 1)
                rag_mode = "retrieved"
                if b < 40:
                    facts = r.get("kb_facts") or []
                    gold = ({"title": "Fakty", "text": "; ".join(map(str, facts))} if facts
                            else (notes.search(r["question"], 1) or [None])[0])
                    if gold:
                        ctx.insert(rnd.randrange(len(ctx) + 1), {"title": gold["title"], "text": gold["text"]})
                        rag_mode, gold_in = "gold+retrieved", True
        user = build_text(body, [{"title": c["title"], "text": c["text"]} for c in ctx])
        answer = r["model_answer"].strip()
        rationale = (r.get("rationale") or "").strip()
        meta = {"id": key, "origin": r.get("origin"), "kind": kind, "subtype": r.get("subtype") or kind,
                "section": r.get("section"), "epoch": r.get("epoch") or epoch_of(f"{r['question']} {item['source_text']} {answer}"),
                "scope": r.get("scope") or scope_of(f"{r['question']} {item['source_text']}"),
                "rag_mode": rag_mode, "gold_in_ctx": gold_in, "image_marker": "[Obraz:" in item["source_text"],
                "has_rationale": bool(rationale), "multi_turn": False, "task": "solve"}
        examples.append({"user": user, "answer": answer, "rationale": rationale, "meta": meta})

    # zadania HyDE (małe modele piszą zapytanie do wyszukiwarki) i dopytanie o numer tematu eseju
    with_hyde = [r for r in recs if r.get("hyde")]
    for r in rnd.sample(with_hyde, min(a.hyde_examples, len(with_hyde))):
        item = pseudo_item(r)
        examples.append({"user": build_body(item, item_type(item)) + "\n\n" + HYDE_PROMPT, "answer": r["hyde"].strip(), "rationale": "",
                         "meta": {"id": f"hyde-{r.get('id')}", "origin": r.get("origin"), "kind": "hyde", "subtype": "hyde",
                                  "section": r.get("section"), "epoch": r.get("epoch"), "scope": r.get("scope"), "rag_mode": "none",
                                  "gold_in_ctx": False, "image_marker": False, "has_rationale": False, "multi_turn": False,
                                  "task": "hyde"}})
    essays = [e for e in examples if e["meta"]["kind"] == "essay" and e["answer"].startswith("Temat nr")]
    for e in rnd.sample(essays, min(a.topic_examples, len(essays))):
        num, text = e["answer"].split("\n", 1)[0].split()[-1], e["answer"].split("\n", 1)[-1].strip()
        examples.append({"user": e["user"], "answer": num, "rationale": "", "history": text,
                         "meta": {**e["meta"], "id": f"topic-{e['meta']['id']}", "multi_turn": True, "task": "topic_number",
                                  "has_rationale": False}})

    # podział i zapis obu wariantów
    rnd.shuffle(examples)
    n_val = max(1, int(len(examples) * a.val))
    files = {f"{s}_{v}": open(out / f"{s}_{v}.jsonl", "w", encoding="utf-8") for s in ("train", "val") for v in ("answer", "think")}
    manifest = open(out / "manifest.jsonl", "w", encoding="utf-8")
    for i, e in enumerate(examples):
        split = "val" if i < n_val else "train"
        msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": e["user"]}]
        if e["meta"]["multi_turn"]:
            msgs += [{"role": "assistant", "content": e["history"]}, {"role": "user", "content": TOPIC_Q}]
        for variant in ("answer", "think"):
            ans = e["answer"]
            if variant == "think" and e["rationale"]:
                ans = f"<think>\n{e['rationale']}\n</think>\n\n{e['answer']}"
            files[f"{split}_{variant}"].write(json.dumps({"messages": msgs + [{"role": "assistant", "content": ans}],
                                                          "meta": e["meta"]}, ensure_ascii=False) + "\n")
        manifest.write(json.dumps({**e["meta"], "split": split, "user_chars": len(e["user"]), "answer_chars": len(e["answer"]),
                                   "rationale_chars": len(e["rationale"])}, ensure_ascii=False) + "\n")
    for f in list(files.values()) + [manifest]:
        f.close()

    # statystyki
    rows = [json.loads(l) for l in open(out / "manifest.jsonl", encoding="utf-8")]
    lines = [f"# SFT v2 — statystyki", "", f"Przykładów: {len(rows)} (train {sum(r['split'] == 'train' for r in rows)}, "
             f"val {n_val}); notatek w bazie kontekstu: {n_notes}; odrzucone: {dict(skipped)}", ""]
    for key in ("origin", "task", "kind", "subtype", "epoch", "scope", "rag_mode", "gold_in_ctx", "image_marker", "has_rationale"):
        c = Counter(str(r.get(key)) for r in rows)
        lines.append(f"- **{key}:** " + ", ".join(f"{k} {v}" for k, v in c.most_common()))
    lens = defaultdict(list)
    for r in rows:
        lens[r["kind"]].append(r["user_chars"] + r["answer_chars"] + r["rationale_chars"])
    lines += ["", "Średnia długość przykładu (znaki) wg typu: " + ", ".join(f"{k} {sum(v) // len(v)}" for k, v in sorted(lens.items()))]
    (out / "STATS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
