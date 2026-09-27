"""Wspólny format zadań egzaminacyjnych i rozpoznawanie typu zadania.

Pozycja (jedna linia JSONL):
{
  "exam": "2023-05", "id": "3", "max_points": 2,
  "type": "closed_choice | closed_tf | closed_match | open | essay",
  "question": "polecenie", "sources": "teksty źródeł (może być puste)",
  "images": ["ścieżki względem katalogu zbioru"],
  "key": {"1": "F", ...} | null      # tylko zamknięte
  "rubric": "zasady oceniania CKE", "solution": "rozwiązanie / przykładowe rozwiązanie CKE",
  "model_answer": "wzorowa odpowiedź w formacie egzaminu"
}
"""

import re

PAIR = re.compile(r"^\s*([A-Z0-9]{1,2})\.?\s*[–—-]\s*([A-Z0-9]{1,2})\s*\.?\s*$")
NAMED = re.compile(r"^\s*(?:Fragment\s+)?([A-F])\.?\s*[–—-]\s*([^\s].{1,80}?)\s*$")
LETTER = re.compile(r"^\s*([A-F])\s*\.?\s*$")
TFSTR = re.compile(r"^\s*([PF]{2,5})\s*$")

# Reguły na podstawie stałych formuł poleceń CKE.
TYPE_RULES = [
    ("essay", re.compile(r"Wybierz jeden z nich do opracowania|minimum 300 wyrazów|Twoja wypowiedź powinna", re.I)),
    ("closed_tf", re.compile(r"Oceń prawdziwość|Zaznacz P,? jeśli", re.I)),
    ("closed_match", re.compile(r"Przyporządkuj|Dopasuj|Uzupełnij tabelę.*(numer|liter)|Wpisz w .* numer", re.I)),
    ("closed_choice", re.compile(r"Zaznacz właściwą odpowiedź|Zaznacz (poprawne|prawidłowe) dokończenie|Dokończ zdanie\. Zaznacz|Zaznacz odpowiedź|spośród podanych", re.I)),
]


def classify(question: str) -> str:
    for name, rx in TYPE_RULES:
        if rx.search(question):
            return name
    return "open"


def parse_key(solution: str):
    """Klucz dla zadań zamkniętych z pola 'Rozwiązanie' zasad CKE; None, jeśli to nie zamknięte."""
    lines = [l for l in solution.splitlines() if l.strip() and not l.strip().startswith("Rozwiązani")]
    if len(lines) == 1 and "," in lines[0]:
        lines = [p for p in lines[0].split(",") if p.strip()]
    if not lines or any(l.strip().lower().startswith(("przykład", "uzasadn")) for l in lines):
        return None
    if len(lines) == 1 and LETTER.match(lines[0]):
        return {"1": LETTER.match(lines[0]).group(1)}
    if len(lines) == 1 and TFSTR.match(lines[0]):
        return {str(i + 1): c for i, c in enumerate(TFSTR.match(lines[0]).group(1))}
    pairs = [PAIR.match(l) for l in lines]
    if all(pairs):
        return {m.group(1): m.group(2) for m in pairs}
    named = [NAMED.match(l) for l in lines]
    if all(named) and len(named) <= 6:
        return {m.group(1): m.group(2) for m in named}
    return None


def key_type(key, question):
    vals = set(key.values())
    if vals <= {"P", "F"}:
        return "closed_tf"
    if all(k.isalpha() for k in key):
        return "closed_match"
    return "closed_choice"


def first_alt(value):
    """'Bizancjum / Cesarstwo Bizantyjskie' -> 'Bizancjum'; '[Ignacy] Łukasiewicz' -> 'Ignacy Łukasiewicz'."""
    v = value.split(" / ")[0] if " / " in value else value
    return re.sub(r"\s+", " ", v.replace("[", "").replace("]", "")).strip()


def format_key(key):
    if list(key) == ["1"] and len(key) == 1:
        return key["1"]
    return "\n".join(f"{k} – {first_alt(v)}" for k, v in key.items())


LABEL = re.compile(r"^(Rozstrzygnięcie|Uzasadnienie|Nazwa [^:]{1,30}|Wydarzenie|Podobieństw[oa](?: [A-C])?|Różnic[aey]|"
                   r"Przyczyna|Skutek|Argument|Cecha|Imię|Nazwisko|Fragment [A-C]|Postać|Władca|Pojęcie|Styl|Data|"
                   r"Nazwa|Wyjaśnienie|Odpowiedź)\s*[:–-]", re.I)
EXAMPLE = re.compile(r"^Przykładow[aey]\s+(uzasadnieni[ae]|rozwiązani[ae]|odpowied[źz]i?|wyjaśnieni[ae]|argumenty?|"
                     r"odpowiedzi)\s*:?\s*", re.I)


COUNT = {"jeden": 1, "jedną": 1, "jedno": 1, "jednej": 1, "dwa": 2, "dwie": 2, "dwóch": 2, "dwoma": 2,
         "trzy": 3, "trzech": 3, "cztery": 4}


def required_count(question: str) -> int:
    m = re.search(r"\b(" + "|".join(COUNT) + r")\b", question.lower())
    return COUNT[m.group(1)] if m else 1


def tidy(body: str) -> str:
    body = re.sub(r"-\s+(?=[a-ząćęłńóśźż])", "", body)  # przeniesienia wyrazów
    body = re.sub(r"\s+", " ", body).strip()
    if len(body) < 60:
        return body.replace("[", "").replace("]", "")
    return body.replace("[", "(").replace("]", ")")


def make_model_answer(solution: str, key=None, question: str = "") -> str:
    """Wzorowa odpowiedź w formacie egzaminu z rozwiązania CKE: pierwszy przykład z każdej sekcji
    (albo tyle elementów, ile wymaga polecenie), bez alternatyw ' / ', ze sklejonymi wierszami."""
    if key:
        return format_key(key)
    need = required_count(question)
    sections, cur = [], None
    for raw in solution.splitlines():
        line = raw.strip()
        if not line:
            continue
        m_ex = EXAMPLE.match(line)
        if m_ex:
            kind = m_ex.group(1).lower()
            rest = line[m_ex.end():].strip()
            label = "Uzasadnienie:" if kind.startswith("uzasadn") else ("Wyjaśnienie:" if kind.startswith("wyjaś") else "")
            if cur is not None and cur["label"] and not any(cur["alts"][-1]) and not label:
                pass  # "Podobieństwo:" + "Przykładowe rozwiązania" -> treść należy do etykiety
            else:
                cur = {"label": label, "alts": [[]]}
                sections.append(cur)
            if rest:
                cur["alts"][-1].append(rest)
            continue
        if LABEL.match(line):
            lab, _, rest = line.partition(":") if ":" in line[:40] else (line, "", "")
            cur = {"label": lab.strip() + ":", "alts": [[]]}
            sections.append(cur)
            if rest.strip():
                cur["alts"][-1].append(rest.strip())
            continue
        if cur is None:
            cur = {"label": "", "alts": [[]]}
            sections.append(cur)
        if line in ("•", "–") or line.startswith(("• ", "– ")):
            if any(cur["alts"][-1]):
                cur["alts"].append([])
            line = line.lstrip("•– ").strip()
            if not line:
                continue
        cur["alts"][-1].append(line)
    parts = []
    short_label = re.compile(r"^(Nazwa|Wydarzenie|Imię|Nazwisko|Postać|Władca|Pojęcie|Styl|Data|Rozstrzygnięcie|Fragment)", re.I)
    for s in sections:
        alts = [a for a in s["alts"] if a]
        if not alts:
            continue
        if need > 1 and len(alts) == 1 and len(alts[0]) > 1 and all(len(l) < 40 and not l.endswith(".") for l in alts[0]):
            items = [first_alt(l) for l in alts[0]]  # lista krótkich pozycji, np. dwa urzędy
            body = ", ".join(items)
        elif len(alts) > 1 and need > 1 and not s["label"]:
            body = "; ".join(tidy(" / ".join(a).split(" / ")[0] if len(" ".join(a)) < 60 else " ".join(a))
                             for a in alts[:need])
        elif all(len(l) < 40 and not l.endswith(".") for l in alts[0]):
            body = first_alt(alts[0][0])  # alternatywne krótkie odpowiedzi w osobnych wierszach
        else:
            body = tidy(" ".join(alts[0]))
        if " / " in body and (len(body) < 80 or short_label.match(s["label"])):
            body = body.split(" / ")[0].strip()
        parts.append(f"{s['label']} {body}".strip() if s["label"] else body)
    return "\n".join(p for p in parts if p).strip()
