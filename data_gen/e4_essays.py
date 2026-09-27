"""E4: tematy i eseje wzorcowe. Pisze sol, ocenia luna (kryteria CKE). Limit 9 USD.

Zostają wypracowania z wynikiem >= 12/15.
"""

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from eval.judge_openai import SYSTEM_ESSAY, word_count
from data_gen.common import (
    BudgetExceeded,
    Forge,
    KB,
    ROOT,
    SFT,
    append_jsonl,
    ensure_dirs,
    load_ids,
    read_jsonl,
    safe_err,
)
from data_gen.sections import SECTIONS, canon_section

TOPICS = SFT / "essay_topics.jsonl"
OUT = SFT / "essays.jsonl"
REJECTED = SFT / "essays_rejected.jsonl"
REAL_TOPICS = SFT / "real_essay_topics.jsonl"
TAXONOMY = ROOT / "data_gen" / "taxonomy.json"
E2_DONE = ROOT / "data_gen" / "state" / "e2_done"
DONE_TOPICS = ROOT / "data_gen" / "state" / "e4_topic_batches.jsonl"

ANSWER_FORMAT = "Jeden tekst: numer wybranego tematu i całe wypracowanie. Minimum 300 wyrazów zgodnie z poleceniem."

SYS_TOPIC = """Układasz tematy wypowiedzi argumentacyjnej na maturę rozszerzoną z historii (formuła CKE 2023).
Każdy temat ma postać:
„<teza>. Zajmij stanowisko wobec powyższej tezy i je uzasadnij, uwzględniając w swojej argumentacji <trzy konkretne elementy>.”
Trzy elementy są nazwane w temacie (trzech władców, trzy wydarzenia albo trzy aspekty: polityczny, społeczno-gospodarczy, kulturowy — dobierz do działu).
Tezy mają być różne: część trafnych, część zbyt jednostronnych, tak aby dało się zająć stanowisko i obronić je faktami.
Nie powtarzaj tematów z listy unikania. Nie wymyślaj działów spoza listy.
Zwróć wyłącznie JSON: {"topics": [{"section": "<dokładny tytuł>", "topic": "<pełna treść tematu>"}]}"""

SYS_ESSAY = """Piszesz wzorcowe wypracowanie maturalne z historii po polsku.
Wymagania:
- 450–700 słów.
- Zacznij dokładnie od linii „Temat nr 1”, potem pusta linia, potem wypracowanie.
- Wstęp: jednoznaczne stanowisko wobec tezy.
- Trzy akapity rozwinięcia, po jednym na każdy element wskazany w temacie, z datami, postaciami i pojęciami.
- Zakończenie wynika z argumentów.
- Zero wymyślonych faktów. Korzystaj z notatek i pewnej wiedzy. Pomiń fakt, którego nie jesteś pewien.
- Bez list punktowanych, bez nagłówków markdown, bez „albo” jako wariantu faktu.
Zwróć wyłącznie JSON: {"essay": "Temat nr 1\\n\\n..."}"""


def notes_for(section):
    chunks = []
    for row in read_jsonl(KB):
        if row.get("section") == section:
            chunks.append(f"{row.get('subtopic')}: {row.get('text')}")
    text = "\n\n".join(chunks)
    return text[:6000]


def existing_topics():
    rows = []
    for path in (TOPICS, REAL_TOPICS):
        rows.extend(read_jsonl(path))
    return rows


def generate_topics(forge, sections, avoid, per_section):
    user = (
        f"Dla każdego działu podaj {per_section} tematy.\nDziały:\n"
        + "\n".join(f"- {s}" for s in sections)
        + "\n\nUnikaj podobieństwa do:\n"
        + "\n".join(f"- {t.get('topic','')[:180]}" for t in avoid[-40:])
    )
    data, _, _ = forge.call_json("E4", "gpt-6-sol", SYS_TOPIC, user, 1800, 0.03, "topics")
    n = 0
    have = {row.get("topic") for row in existing_topics()}
    for row in data.get("topics") or []:
        section = canon_section(row.get("section"))
        topic = " ".join(str(row.get("topic") or "").split())
        if not section or section not in sections or len(topic) < 80 or topic in have:
            continue
        if "Zajmij stanowisko" not in topic:
            continue
        have.add(topic)
        rom = section.split(".", 1)[0].strip()
        append_jsonl(TOPICS, {
            "id": f"topic-{rom}-{abs(hash(topic)) % 10**8}",
            "source_doc": "synthetic",
            "section": section,
            "topic": topic,
        })
        n += 1
    return n


def import_real_topics():
    have = {row.get("topic") for row in read_jsonl(TOPICS)}
    n = 0
    for row in read_jsonl(REAL_TOPICS):
        topic = " ".join(str(row.get("topic") or "").split())
        if "Zajmij stanowisko" not in topic or topic in have or len(topic) < 80:
            continue
        have.add(topic)
        append_jsonl(TOPICS, {
            "id": "real-" + str(row.get("id")),
            "source_doc": row.get("source_doc") or "real",
            "section": canon_section(row.get("section") or "") or row.get("section") or "",
            "topic": topic,
            "origin_topic": "real",
        })
        n += 1
    return n


def question_for(topic):
    return (
        "Zadanie zawiera jeden temat. Napisz wypowiedź argumentacyjną. "
        "Twoja wypowiedź powinna liczyć minimum 300 wyrazów.\n"
        f"1. {topic}"
    )


def write_essay(forge, row):
    section = row.get("section") or ""
    user = (
        f"Dział: {section}\nTemat:\n{row['topic']}\n\n"
        f"Notatki kompendium (fakty, nie przepisuj ich):\n{notes_for(section) or 'Brak notatki — użyj tylko pewnych faktów.'}"
    )
    essay = ""
    for attempt in range(2):
        data, _, _ = forge.call_json("E4", "gpt-6-sol", SYS_ESSAY, user, 2800, 0.035, "essay")
        essay = str(data.get("essay") or "").strip()
        if not essay.startswith("Temat nr 1"):
            essay = "Temat nr 1\n\n" + essay
        wc = word_count(essay)
        if 450 <= wc <= 720:
            break
        user += f"\nPoprzednia wersja miała {wc} słów. Zmień długość do 450–700 słów i popraw strukturę."
    wc = word_count(essay)
    rec = {
        "id": "essay-" + str(row["id"]),
        "origin": "essay",
        "source_doc": row.get("source_doc") or "synthetic",
        "section": section,
        "subtopic": "",
        "type": "essay",
        "group": str(row["id"]),
        "max_points": 15,
        "question": question_for(row["topic"]),
        "source_text": "",
        "answer_format": ANSWER_FORMAT,
        "model_answer": essay,
        "rubric": "Kryteria CKE wypowiedzi argumentacyjnej: A narracja historyczna 0–12, B spójność 0–3.",
        "needs_image": False,
        "image_refs": [],
        "verified": False,
        "verify_note": f"słów: {wc}",
        "words": wc,
    }
    if wc < 300:
        rec["verify_note"] = f"za krótkie ({wc})"
        append_jsonl(REJECTED, rec)
        return rec
    judged = judge(forge, rec)
    judged.pop("_cost", None)
    pts = int(judged.get("points") or 0)
    rec["score"] = pts
    rec["score_detail"] = judged
    rec["verified"] = pts >= 12
    rec["verify_note"] = f"{pts}/15; {judged.get('reason','')}"
    append_jsonl(OUT if rec["verified"] else REJECTED, rec)
    print(f"essay {rec['id']} {pts}/15 words {wc}", flush=True)
    return rec


def judge(forge, rec, stage="E4", max_tokens=700, estimate=0.008):
    user = (
        f"[TEMATY]\n{rec['question']}\n\n[LICZBA SŁÓW WYPRACOWANIA] {word_count(rec['model_answer'])}\n\n"
        f"[WYPRACOWANIE]\n{rec['model_answer'][:9000]}"
    )
    data, _, cost = forge.call_json(stage, "gpt-6-luna", SYSTEM_ESSAY, user, max_tokens, estimate, "judge-essay")
    data["points"] = max(0, min(15, int(data.get("points") or 0)))
    data["_cost"] = cost
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--per-section", type=int, default=3)
    parser.add_argument("--follow", action="store_true")
    parser.add_argument("--max-essays", type=int, default=320)
    args = parser.parse_args()
    ensure_dirs()
    forge = Forge()
    if args.pilot:
        args.per_section = 3
        args.max_essays = 6

    while True:
        if not TAXONOMY.exists():
            if args.follow and not args.pilot:
                print("E4 czeka na taksonomię", flush=True)
                time.sleep(40)
                continue
            print("brak taksonomii", flush=True)
            return
        tax = json.loads(TAXONOMY.read_text(encoding="utf-8"))
        sections = [canon_section(s.get("section")) or s.get("section") for s in tax.get("sections") or []]
        sections = [s for s in sections if s]
        if args.pilot:
            sections = sections[:2]
        import_real_topics()
        have_sections = {}
        for row in read_jsonl(TOPICS):
            if row.get("source_doc") == "synthetic":
                have_sections[row.get("section")] = have_sections.get(row.get("section"), 0) + 1
        need = [s for s in sections if have_sections.get(s, 0) < args.per_section]
        print(f"sections needing topics {len(need)}", flush=True)
        for i in range(0, len(need), 4):
            group = need[i:i + 4]
            try:
                n = generate_topics(forge, group, existing_topics(), args.per_section)
                print(f"topics +{n}", flush=True)
            except BudgetExceeded as exc:
                print("budget stop topics", exc, flush=True)
                return
            except Exception as exc:
                print("topics fail", safe_err(exc), flush=True)
        done = load_ids(OUT) | load_ids(REJECTED)
        pending = []
        for row in read_jsonl(TOPICS):
            eid = "essay-" + str(row.get("id"))
            if eid in done:
                continue
            if args.pilot and row.get("section") not in sections:
                continue
            pending.append(row)
            if len(pending) >= args.max_essays:
                break
        print(f"essays pending {len(pending)}", flush=True)
        if not pending:
            if args.follow and not E2_DONE.exists() and not args.pilot:
                time.sleep(40)
                continue
            break

        def work(row):
            try:
                return write_essay(forge, row)
            except BudgetExceeded as exc:
                print("budget stop", exc, flush=True)
                return None
            except Exception as exc:
                print("essay fail", safe_err(exc), flush=True)
                return None

        stop = False
        with ThreadPoolExecutor(max(1, args.workers)) as ex:
            futs = [ex.submit(work, row) for row in pending]
            for fut in as_completed(futs):
                if fut.result() is None and stop is False:
                    # None też przy błędzie jednostkowym; budżet rozpoznajemy po komunikacie
                    pass
        if args.pilot or not args.follow:
            break
        if E2_DONE.exists():
            break
    print("E4 kept", len(read_jsonl(OUT)), "rejected", len(read_jsonl(REJECTED)), flush=True)


if __name__ == "__main__":
    main()
