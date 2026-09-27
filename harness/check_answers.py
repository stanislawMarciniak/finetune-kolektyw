"""Sprawdza answers.json tak jak strona zgłoszeń (submission-validation.mjs organizatorów), offline.

    python harness/check_answers.py runs/final/T1-tuned/answers.json exams/final/answers-template.json
Drugi argument: answers-template.json albo exam.json z paczki (z niego exam_id i lista ID).
"""

import json
import sys
from pathlib import Path

MAX_BYTES = 1048576


def expected(ref):
    d = json.loads(Path(ref).read_text(encoding="utf-8"))
    rows = d.get("answers") or d.get("items") or []
    return d["exam_id"], [r["id"] for r in rows]


def check(path, ref):
    raw = Path(path).read_bytes()
    p = json.loads(raw.decode("utf-8"))
    exam_id, ids = expected(ref)
    errors, blanks = [], []
    if not isinstance(p, dict) or set(p) != {"exam_id", "answers"}:
        return ["Tylko exam_id i answers na najwyższym poziomie."], []
    if p["exam_id"] != exam_id:
        errors.append(f"Zły exam_id: {p['exam_id']!r}, ma być {exam_id!r}.")
    seen = set()
    for n, a in enumerate(p["answers"], 1):
        if not isinstance(a, dict) or set(a) != {"id", "answer"} or not all(isinstance(a[k], str) for k in ("id", "answer")):
            errors.append(f"Wpis {n}: tylko id i answer, oba jako tekst.")
            continue
        if a["id"] not in ids:
            errors.append(f"Nieznane ID: {a['id']}.")
        if a["id"] in seen:
            errors.append(f"Duplikat ID: {a['id']}.")
        seen.add(a["id"])
        if len(a["answer"]) > 100000:
            errors.append(f"Odpowiedź {a['id']} > 100 000 znaków.")
        if not a["answer"].strip():
            blanks.append(a["id"])
    missing = [i for i in ids if i not in seen]
    if missing:
        errors.append(f"Brak ID: {', '.join(missing)}.")
    if len(p["answers"]) != len(ids):
        errors.append(f"Oczekiwano {len(ids)} wpisów, jest {len(p['answers'])}.")
    if len(json.dumps(p, ensure_ascii=False).encode("utf-8")) > MAX_BYTES:
        errors.append("JSON > 1 MiB.")
    return errors, blanks


if __name__ == "__main__":
    errs, blanks = check(sys.argv[1], sys.argv[2])
    for e in errs:
        print("BŁĄD:", e)
    print(f"{'OK' if not errs else 'NIE DO WGRANIA'}: puste odpowiedzi {len(blanks)} {blanks if blanks else ''}")
    sys.exit(1 if errs else 0)
