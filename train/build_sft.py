"""Buduje zbiór SFT (rozmowy) z danych w data/sft/*.jsonl, w tym samym formacie promptu co harness/run_exam.py.

    python train/build_sft.py [--include-image-items] [--val 0.05]
Wynik: data/sft/train.jsonl, data/sft/val.jsonl  ({"messages": [...], "meta": {...}})
Zadania wymagające obrazu są domyślnie pomijane (dane tekstowe; obraz nie jest dostępny w rekordzie).
"""

import argparse
import json
import random
import re
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "harness"))
from run_exam import SYSTEM  # noqa: E402

FILES = ["real_cke.jsonl", "synthetic_items.jsonl", "essays.jsonl"]


def exam_id(r):
    """Numer w stylu arkusza CKE („7”, „11.2”), taki jak w nagłówku harnessu; id syntetyczne typu XL-0-b2 nie występują na egzaminie."""
    rid = str(r.get("id", ""))
    m = re.search(r"(\d{1,2}(?:\.\d)?)$", rid)
    if m and not rid.startswith("syn-"):
        return m.group(1)
    n = zlib.crc32(str(r.get("group") or rid).encode()) % 25 + 1
    sub = re.search(r"-(\d+)$", rid)
    return f"{n}.{sub.group(1)}" if sub else str(n)


def user_text(r):
    head = f"Zadanie {exam_id(r)} ({r.get('max_points', 1)} pkt)"
    body = f"{head}\n\n{r.get('source_text', '')}\n\n{r['question']}"
    if str(r.get("type", "")).startswith("closed"):
        body += f"\n\nZapisz odpowiedź dokładnie w formacie:\n{r['answer_format']}"
    return body


def words(text):
    return {w for w in re.findall(r"\w{4,}", text.lower())}


def dedup(rows, thr):
    """Odrzuca syntetyczne zadania zbyt podobne (polecenie + klucz) do wcześniejszych z innej grupy tej samej sekcji
    i typu. Zadania jednej grupy dzielą źródło, więc źródło nie wchodzi do porównania."""
    syn = [r for r in rows if r["meta"]["origin"] == "synthetic"]
    sets = {id(r): words(r["meta"].pop("dup_text")) for r in syn}
    df = {}
    for ws in sets.values():
        for w in ws:
            df[w] = df.get(w, 0) + 1
    common = {w for w, n in df.items() if n > 0.02 * len(syn)}
    kept, seen, dropped = [], {}, 0
    for r in rows:
        if r["meta"]["origin"] != "synthetic":
            kept.append(r)
            continue
        ws = sets[id(r)] - common
        key = (r["meta"]["section"], r["meta"]["type"])
        if any(g != r["meta"]["group"] and len(ws & o) / max(1, len(ws | o)) >= thr for g, o in seen.get(key, [])):
            dropped += 1
            continue
        seen.setdefault(key, []).append((r["meta"]["group"], ws))
        kept.append(r)
    return kept, dropped


EVAL_SETS = ["dev2023_text", "dev2023_img", "test2024_split", "test2025_split", "test2026_split"]


def drop_eval_overlap(rows):
    """Usuwa przykłady, których polecenie pokrywa się z zadaniem z naszych arkuszy ewaluacyjnych (początek polecenia)."""
    norm = lambda s: re.sub(r"\W+", " ", s.lower()).strip()[:120]
    seen = set()
    for name in EVAL_SETS:
        path = ROOT / "eval" / "data" / f"{name}.jsonl"
        if path.exists():
            seen |= {norm(json.loads(l)["question"]) for l in open(path, encoding="utf-8")}
    kept = [r for r in rows if norm(r["meta"].pop("q")) not in seen]
    return kept, len(rows) - len(kept)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--include-image-items", action="store_true")
    p.add_argument("--val", type=float, default=0.05)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--dup", type=float, default=0.5, help="próg Jaccarda (słowa) dla bliskich duplikatów w tej samej sekcji")
    a = p.parse_args()
    rows, skipped = [], {"image": 0, "unverified": 0, "empty": 0}
    for name in FILES:
        path = ROOT / "data" / "sft" / name
        if not path.exists():
            continue
        for l in open(path, encoding="utf-8"):
            r = json.loads(l)
            if not r.get("model_answer") or not r.get("question"):
                skipped["empty"] += 1
                continue
            if r.get("verified") is False:
                skipped["unverified"] += 1
                continue
            if r.get("needs_image") and not a.include_image_items:
                skipped["image"] += 1
                continue
            rows.append({"messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user_text(r)},
                                      {"role": "assistant", "content": r["model_answer"].strip()}],
                         "meta": {"origin": r.get("origin"), "type": r.get("type"), "section": r.get("section"), "id": r.get("id"),
                                  "group": r.get("group"), "q": r["question"],
                                  "dup_text": f"{r['question']} {r['model_answer']}"}})
    for r in rows:
        if r["meta"]["origin"] != "synthetic":
            r["meta"].pop("dup_text")
    rows, skipped["near_dup"] = dedup(rows, a.dup)
    rows, skipped["eval_overlap"] = drop_eval_overlap(rows)
    random.Random(a.seed).shuffle(rows)
    n_val = max(1, int(len(rows) * a.val))
    out = ROOT / "data" / "sft"
    for name, part in (("val", rows[:n_val]), ("train", rows[n_val:])):
        with open(out / f"{name}.jsonl", "w", encoding="utf-8") as f:
            for r in part:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    by = {}
    for r in rows:
        k = f"{r['meta']['origin']}/{r['meta']['type']}"
        by[k] = by.get(k, 0) + 1
    print(json.dumps({"train": len(rows) - n_val, "val": n_val, "skipped": skipped, "by_origin_type": by}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
