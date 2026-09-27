"""Parsowanie tekstu zasad oceniania CKE (formuła 2023) na pozycje: zasady punktowania + rozwiązanie."""

import re

HEADER = re.compile(r"^Zadanie\s+(\d+(?:\.\d+)?)\.\s*\((0\s*[–-]\s*(\d+))\)", re.M)
NOISE = [
    re.compile(r"^=== s\.\d+\s*$", re.M),
    re.compile(r"^Strona \d+ z \d+\s*$", re.M),
    re.compile(r"^Zasady oceniania rozwiązań zadań\s*$", re.M),
    re.compile(r"^Egzamin maturalny z historii.*$", re.M),
    re.compile(r"^\s*\d+\s+Rozporządzenie[^\n]*(?:\n[^\n]*){0,3}?\)\.\s*$", re.M),
]


def clean(text):
    for rx in NOISE:
        text = rx.sub("", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def parse_zasady(text):
    """Zwraca {id: {max_points, rubric, solution, raw}}."""
    text = clean(text)
    heads = list(HEADER.finditer(text))
    items = {}
    for i, h in enumerate(heads):
        body = text[h.end(): heads[i + 1].start() if i + 1 < len(heads) else len(text)]
        rubric, solution = "", ""
        m = re.search(r"Zasady oceniania\s*\n(.*?)(?:\n\s*(?:Rozwiązanie|Rozwiązania|Przykładowe rozwiązani[ae]|Przykładowa odpowiedź|Przykładowe odpowiedzi)\b)", body, re.S)
        if m:
            rubric = m.group(1).strip()
            solution = body[m.end() - len(m.group(0).splitlines()[-1]):].strip()
        else:
            m2 = re.search(r"Zasady oceniania\s*\n(.*)", body, re.S)
            rubric = m2.group(1).strip() if m2 else body.strip()
        items[h.group(1)] = {"max_points": int(h.group(3)), "rubric": rubric,
                             "solution": solution, "raw": body.strip()}
    return items
