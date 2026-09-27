"""Sprawdza answers.json tak jak strona zgłoszeń (submission-validation.mjs + submissions.mjs organizatorów), offline.

    python harness/check_answers.py runs/final/T1-tuned/answers.json exams/final/answers-template.json
Drugi argument: answers-template.json albo exam.json z paczki (z niego exam_id i lista ID).
BŁĄD = strona odrzuci plik (kod wyjścia 1). UWAGA = reguły treści z przewodnika JSON (esej, bez śladów rozumowania,
po polsku) albo niespójność paczki — plik przejdzie format, ale warto spojrzeć.
"""

import json
import re
import sys
from pathlib import Path

MAX_BYTES = 1048576
LEAKS = re.compile(r"</?think>|<\|?channel\|?>|<\|?(start|end)_of_turn\|?>|<\|im_(start|end)\|>|<\|end\|>|</s>|<eos>|"
                   r"<\|endoftext\|>|<\|turn>|<turn\|>")
MOJIBAKE = re.compile(r"Ã[\x80-\xbf³]|Å[\x80-\xbf‚›»¼]|Ä[\x80-\xbf…™‡]|\\u0[0-9a-fA-F]{3}|\ufffd")
ENGLISH = re.compile(r"(?i)\b(the|and|of|is|answer|because|which)\b")


def load_ref(ref):
    d = json.loads(Path(ref).read_text(encoding="utf-8"))
    rows = d.get("answers") or d.get("items") or []
    return d, d["exam_id"], [r["id"] for r in rows]


def expected(ref):
    _, exam_id, ids = load_ref(ref)
    return exam_id, ids


def essay_ids(exam):
    return [i["id"] for i in exam.get("items", [])
            if i.get("answer_format", "").startswith("Jeden tekst") or "Wybierz jeden z nich" in i.get("question", "")]


def warnings_for(path, raw, p, ref):
    warns = []
    if Path(path).name != "answers.json":
        warns.append(f"Plik nazywa się {Path(path).name}, przewodnik: zapisz jako answers.json.")
    if raw.startswith(b"\xef\xbb\xbf"):
        warns.append("Plik zaczyna się od BOM UTF-8.")
    d, exam_id, ids = load_ref(ref)
    exam = d if "items" in d else None
    sibling = Path(ref).with_name("exam.json" if exam is None else "answers-template.json")
    if sibling.exists():
        d2, exam_id2, ids2 = load_ref(sibling)
        exam = exam or d2
        if exam_id2 != exam_id or sorted(ids2) != sorted(ids):
            warns.append(f"exam.json i answers-template.json niezgodne (exam_id / lista ID) — wzorcem jest {Path(ref).name}.")
    ess = essay_ids(exam) if exam else []
    if not ess and "26" in ids:
        ess = ["26"]
    answers = {a.get("id"): a.get("answer") for a in p["answers"] if isinstance(a, dict) and isinstance(a.get("answer"), str)}
    for eid in ess:
        e = answers.get(eid, "")
        words = len(re.findall(r"[^\W\d_]+", e))
        if words < 300:
            warns.append(f"Esej {eid}: {words} wyrazów (< 300).")
        if not re.search(r"(?i)^\W*\d\s*[.):]", e) and not re.search(r"(?i)temat\w*\s*(nr\.?|numer)?\s*\d", e[:300]):
            warns.append(f"Esej {eid}: brak numeru tematu na początku.")
    for i, a in answers.items():
        if LEAKS.search(a):
            warns.append(f"Odpowiedź {i}: znacznik rozumowania/czatu ({LEAKS.search(a).group(0)}).")
        if MOJIBAKE.search(a):
            warns.append(f"Odpowiedź {i}: zepsute kodowanie znaków ({MOJIBAKE.search(a).group(0)!r}).")
        if "```" in a or re.search(r"(?m)^#{1,6}\s", a):
            warns.append(f"Odpowiedź {i}: markdown (``` albo nagłówek #).")
        if len(a) >= 200 and len(ENGLISH.findall(a)) >= 5:
            warns.append(f"Odpowiedź {i}: wygląda na angielską (odpowiedzi mają być po polsku).")
    return warns


def check(path, ref):
    """Zwraca (błędy, puste ID); błędy = to, co odrzuci strona."""
    raw = Path(path).read_bytes()
    if not Path(path).name.lower().endswith(".json") or not raw:
        return ["Plik musi być niepustym .json."], []
    if len(raw) > MAX_BYTES:
        return [f"Plik ma {len(raw)} B > 1 MiB ({MAX_BYTES} B)."], []
    try:
        p = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        return [f"To nie jest poprawny JSON w UTF-8: {e}."], []
    exam_id, ids = expected(ref)
    errors, blanks = [], []
    if not isinstance(p, dict) or set(p) != {"exam_id", "answers"}:
        return ["Tylko exam_id i answers na najwyższym poziomie."], []
    if p["exam_id"] != exam_id:
        errors.append(f"Zły exam_id: {p['exam_id']!r}, ma być {exam_id!r}.")
    if not isinstance(p["answers"], list):
        return errors + ["answers musi być listą."], []
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
    if len(json.dumps(p, ensure_ascii=False, separators=(",", ":")).encode("utf-8")) > MAX_BYTES:
        errors.append("JSON > 1 MiB.")
    return errors, blanks


if __name__ == "__main__":
    errs, blanks = check(sys.argv[1], sys.argv[2])
    for e in errs:
        print("BŁĄD:", e)
    warns = []
    if not errs:
        raw = Path(sys.argv[1]).read_bytes()
        warns = warnings_for(sys.argv[1], raw, json.loads(raw.decode("utf-8-sig")), sys.argv[2])
        for w in warns:
            print("UWAGA:", w)
        print(f"rozmiar {len(raw)} B ({len(raw) / MAX_BYTES:.1%} limitu 1 MiB)")
    print(f"{'OK' if not errs else 'NIE DO WGRANIA'}: puste odpowiedzi {len(blanks)} {blanks if blanks else ''}"
          f"{f', uwagi {len(warns)}' if warns else ''}")
    sys.exit(1 if errs else 0)
