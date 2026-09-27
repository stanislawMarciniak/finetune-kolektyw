"""E5: masowe pary zadań SFT (luna) z weryfikacją na ślepo. Limit etapu 13 USD.

Pilot (--tag pilot) ma osobny sufit 0,5 USD. Zapis przyrostowy, wznawianie po ID.
Weryfikacja zamkniętych i otwartych: blind_solve / judge_open / verify z e3.
Esej: ocena kryteriami CKE (judge z e4), próg 12/15.
"""

import argparse
import json
import random
import re
import sys
import threading
import time
from collections import Counter
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_gen.common import (
    CLOSED_TYPES,
    COST_LOG,
    STAGE_LIMITS,
    BudgetExceeded,
    Forge,
    KB,
    ROOT,
    SFT,
    append_jsonl,
    canonical_format,
    collapse_alternatives,
    ensure_dirs,
    has_alternative_marker,
    jaccard,
    normalize_closed,
    polish_word_count,
    read_jsonl,
    safe_err,
    spent_by_stage,
    valid_model_answer,
    word_ngrams,
)
from data_gen.e3_synthetic import verify
from data_gen.e4_essays import judge as judge_essay
from data_gen.sections import canon_section
from eval.judge_openai import word_count

OUT = SFT / "e5_items.jsonl"
REJECTED = SFT / "e5_rejected.jsonl"
STATS = SFT / "e5_STATS.md"
EVAL_DIR = ROOT / "eval" / "data"
TAXONOMY = ROOT / "data_gen" / "taxonomy.json"
SYN = SFT / "synthetic_items.jsonl"
REAL = SFT / "real_cke.jsonl"
SEQ_PATH = ROOT / "data_gen" / "state" / "e5_seq.txt"

PROMPT_VERSION = "e5-v2"
MODEL = "gpt-6-luna"
ESSAY_HEAD = (
    "Zadanie zawiera trzy tematy. Wybierz jeden z nich do opracowania. "
    "Twoja wypowiedź powinna liczyć minimum 300 wyrazów."
)
IMG_MARK = re.compile(r"\[Obraz: images/[A-Za-z0-9_\-]+\.png\]")
CAP_RE = re.compile(
    r"\b(fotograf\w*|ilustracj\w*|karykatur\w*|plakat\w*|rycin\w*|obraz\w*|map\w*|monet\w*|rysunk\w*|plan\w*|malowid\w*|drzeworyt\w*|medal\w*)",
    re.I,
)
LABEL_RE = re.compile(
    r"^(rozstrzygnięcie|rozstrzygniecie|uzasadnienie|podobieństwo|podobienstwo|różnica|roznica)\s*:\s*",
    re.I,
)
KEY_WORD = re.compile(r"\b(klucz|klucza|kluczu|wzorc\w*)\b", re.I)

EPOCH_W = {
    "starożytność": 0.11,
    "średniowiecze": 0.14,
    "nowożytność": 0.30,
    "XIX w.": 0.16,
    "1914–1945": 0.18,
    "po 1945": 0.11,
}
SUBTYPE_W = {
    "closed_match": 0.14,
    "closed_tf": 0.10,
    "closed_choice": 0.10,
    "closed_multi": 0.06,
    "rozstrzygnij": 0.20,
    "podaj": 0.16,
    "wyjasnij": 0.12,
    "porownaj_inne": 0.06,
    "essay": 0.06,
}
SOURCE_W = {"opracowanie": 0.25, "dokument": 0.25, "tabela": 0.25, "ilustracja": 0.25}
DIFF_W = {"latwe": 0.30, "srednie": 0.50, "trudne": 0.20}
DIFF_PL = {"latwe": "łatwe", "srednie": "średnie", "trudne": "trudne"}

# Działy podstawy: epoka zgodna z miejscem w programie, zakres dominujący.
ROMAN_EPOCH = {}
for _rom in ("II", "III", "IV"):
    ROMAN_EPOCH[_rom] = "starożytność"
for _rom in ("V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII"):
    ROMAN_EPOCH[_rom] = "średniowiecze"
for _rom in (
    "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX", "XXI", "XXII", "XXIII",
    "XXIV", "XXV", "XXVI", "XXVII", "XXVIII",
):
    ROMAN_EPOCH[_rom] = "nowożytność"
for _rom in ("XXIX", "XXX", "XXXI", "XXXII", "XXXIII", "XXXIV", "XXXV", "XXXVI"):
    ROMAN_EPOCH[_rom] = "XIX w."
for _rom in (
    "XXXVII", "XXXVIII", "XXXIX", "XL", "XLI", "XLII", "XLIII", "XLIV", "XLV",
    "XLVI", "XLVII", "XLVIII", "XLIX", "L",
):
    ROMAN_EPOCH[_rom] = "1914–1945"
for _rom in ("LI", "LII", "LIII", "LIV", "LV", "LVI", "LVII", "LVIII", "LIX", "LX"):
    ROMAN_EPOCH[_rom] = "po 1945"
POLAND = {
    "IX", "X", "XII",
    "XVIII", "XIX", "XX", "XXI", "XXII", "XXIII", "XXVI", "XXVII", "XXVIII",
    "XXXI", "XXXII", "XXXV", "XXXVI",
    "XXXVIII", "XLI", "XLII", "XLIII", "XLIV", "XLVI", "XLVIII", "XLIX", "L",
    "LV", "LVI", "LVII", "LVIII", "LIX", "LX",
}

KIND_RULES = {
    "closed_tf": "Zamknięte prawda/fałsz. Polecenie zaczyna się od „Oceń prawdziwość poniższych stwierdzeń. Zaznacz P, jeśli stwierdzenie jest prawdziwe, albo F – jeśli jest fałszywe.” Potem dokładnie trzy numerowane stwierdzenia. model_answer to dokładnie trzy linie, np. „1: F\\n2: P\\n3: P”, i jest wśród nich zarówno P, jak i F.",
    "closed_choice": "Zamknięte jednokrotnego wyboru. Polecenie zaczyna się od „Dokończ zdanie. Zaznacz właściwą odpowiedź spośród podanych.” Jedno zdanie i opcje A–D, tylko jedna poprawna. model_answer to sama litera, np. „C”.",
    "closed_match": "Przyporządkowanie. Polecenie zaczyna się od „Przyporządkuj”. Dwa opisy oznaczone A i B oraz trzy numerowane możliwości. model_answer to dwie linie, np. „A: 3\\nB: 1”.",
    "closed_multi": "Dwa niezależne dokończenia. Dwa zdania numerowane 1. i 2., każde z opcjami A–D. model_answer to dwie linie, np. „1: B\\n2: C”.",
    "rozstrzygnij": "Zadanie otwarte. Polecenie zaczyna się od „Rozstrzygnij” i kończy się etykietami w osobnych liniach: „Rozstrzygnięcie:” oraz „Uzasadnienie:”. model_answer używa tych samych etykiet. Rozstrzygnięcie jest jednoznaczne (tak/nie albo wskazanie jednej z nazwanych możliwości).",
    "podaj": "Zadanie otwarte. Polecenie zaczyna się od „Podaj”, „Wymień” albo „Nazwij”. model_answer jest krótki i jednoznaczny, bez wariantów.",
    "wyjasnij": "Zadanie otwarte. Polecenie zaczyna się od „Wyjaśnij” albo „Uzasadnij”. model_answer to jedno do trzech zdań (przyczyna, skutek albo mechanizm).",
    "porownaj_inne": "Zadanie otwarte innego typu niż rozstrzygnięcie, podanie i wyjaśnienie. Polecenie zaczyna się od „Porównaj” (albo „Wskaż podobieństwo”, „Wskaż różnicę”) i zawiera etykiety „Podobieństwo:” oraz „Różnica:”. model_answer używa tych etykiet.",
    "essay": "Esej. Osobne wywołanie, bez drugiego zadania.",
}
SOURCE_RULES = {
    "opracowanie": "Rodzaj źródła: fragment opracowania historycznego (60–180 słów). Zacznij od linii „Fragment opracowania historycznego.” Tekst jest nowy, napisany na podstawie notatki, ale nie jest jej skrótem. Nie wstawiaj znacznika obrazu.",
    "dokument": "Rodzaj źródła: fragment dokumentu, kroniki albo pamiętnika jako parafraza w stylu epoki (60–180 słów), nie cytat z kanonicznej edycji. Zacznij od linii „Fragment dokumentu.” albo „Fragment kroniki.” albo „Fragment pamiętnika.” Nie wstawiaj znacznika obrazu.",
    "tabela": "Rodzaj źródła: tabela z danymi liczbowymi (markdown, ze znakami |). Nagłówek w rodzaju „Tabela. …”. 4–8 wierszy danych. Nie wstawiaj znacznika obrazu.",
    "ilustracja": "Rodzaj źródła: ilustracja. source_text zaczyna się od neutralnego podpisu w stylu CKE, a w następnej linii jest DOKŁADNIE podany znacznik obrazu. Podpis podaje tylko rodzaj źródła (fotografia, rycina, karykatura, plakat, obraz, medale), rok albo autora i najwyżej ogólny kontekst (miejsce, stulecie). Nie wolno wpisać nazwy wydarzenia, postaci ani pojęcia, o które pyta którekolwiek zadanie tej wiązki. Zły podpis: „Rycina przedstawiająca zamach na arcyksięcia Franciszka Ferdynanda w Sarajewie”. Dobry: „Rycina z 1914 r.” albo „Karykatura z prasy codziennej, początek XX w.”. Zadanie ma dać się rozwiązać z podpisu i wiedzy, ale podpis nie jest gotową odpowiedzią.",
}
DOC_BY_EPOCH = {
    "starożytność": "Dokument w starożytności to parafraza inskrypcji, rocznika albo dzieła historiograficznego, nie nowożytny akt. Dla pradziejów (paleolit, neolit, zanim powstało pismo) nie używaj fragmentu dokumentu.",
    "średniowiecze": "Dokument w średniowieczu to parafraza kroniki, przywileju, bulli albo listu z epoki.",
    "nowożytność": "Dokument w nowożytności to parafraza aktu, diariusza, uniwersału, mowy albo pamiętnika.",
    "XIX w.": "Dokument w XIX w. to parafraza odezwy, pamiętnika, mowy albo artykułu z tamtego stulecia.",
    "1914–1945": "Dokument z lat 1914–1945 to parafraza odezwy, przemówienia, wspomnienia albo komunikatu z tego okresu.",
    "po 1945": "Dokument po 1945 r. to parafraza przemówienia, wspomnienia, umowy albo komunikatu z drugiej połowy XX w.",
}
STOP_WORDS = {
    "przez", "oraz", "jednak", "także", "takze", "między", "miedzy", "według", "wedlug",
    "wobec", "jeśli", "jesli", "jeżeli", "jezeli", "czyli", "dlatego", "ponieważ", "poniewaz",
    "podczas", "następnie", "nastepnie", "również", "rowniez", "można", "mozna", "należy", "nalezy",
    "został", "zostal", "została", "zostala", "zostało", "zostalo", "zostały", "zostaly",
    "który", "ktory", "która", "ktora", "które", "ktore", "którzy", "ktorzy", "której", "ktorej",
    "którego", "ktorego", "których", "ktorych", "którym", "ktorym", "tylko", "bardzo",
    "może", "moze", "mogą", "moga", "zostanie", "miała", "miala", "miał", "mial", "miało", "mialo",
    "aby", "żeby", "zeby", "tego", "była", "byla", "były", "byly", "było", "bylo", "jego",
    "zatem", "bowiem", "także", "właśnie", "wlasnie", "zostać", "zostac",
}
DIFF_RULES = {
    "latwe": "Trudność łatwa: większość tropu jest w źródle, ale jeden element odpowiedzi wymaga wiedzy spoza źródła.",
    "srednie": "Trudność średnia: źródło trzeba połączyć z wiedzą (data, przyczyna, skutek albo postać), której źródło nie podaje wprost.",
    "trudne": "Trudność trudna: źródło jest tylko punktem wyjścia. Poprawna odpowiedź wymaga faktów, których w source_text nie ma.",
}

SYS_GEN = """Jesteś autorem zadań matury rozszerzonej z historii (styl CKE, formuła 2023).
Ukladasz JEDNO źródło i zadania do niego. Fakty mają być pewne: zgodne z notatką i z podręcznikiem szkolnym. Nie wymyślaj dat, osób ani liczb.
Źródło nie może zawierać gotowej odpowiedzi. Uczeń ma skorzystać ze źródła ORAZ z własnej wiedzy.
Gdy polecenie ma etykiety (Rozstrzygnięcie:, Uzasadnienie:, Podobieństwo:, Różnica:), model_answer używa tych samych etykiet.
model_answer jest jeden, jednoznaczny, bez „albo”, bez „/” i bez wariantów.
Rubryka zwięźle, jak w CKE: „1 pkt – za …\\n0 pkt – za odpowiedź niepełną lub błędną albo za brak odpowiedzi.”
Nie odwołuj się do mapy ani ilustracji, której nie ma w source_text. Przy ilustracji jedyny obraz to podany znacznik.
rationale: 80–220 słów po polsku (nie mniej niż 80 i nie więcej niż 400). To rozumowanie ucznia: co mówi źródło, jaka wiedza jest potrzebna, jak odpadają inne możliwości. Nie używaj słów „klucz”, „wzorzec”, „wzorcowa”.
hyde: jedno albo dwa zdania w stylu hasła encyklopedii, z nazwami, datami i postaciami potrzebnymi do odpowiedzi.
kb_facts: lista 3–5 krótkich faktów w postaci „rok – wydarzenie – postać/skutek”.
Zwróć wyłącznie JSON:
{"source_text": "...", "items": [{"question": "...", "model_answer": "...", "rubric": "...", "rationale": "...", "hyde": "...", "kb_facts": ["...", "...", "..."]}]}"""

SYS_ESSAY = """Jesteś autorem tematu i wzorcowego wypracowania matury rozszerzonej z historii (CKE, formuła 2023).
question zaczyna się DOKŁADNIE od zdania: „Zadanie zawiera trzy tematy. Wybierz jeden z nich do opracowania. Twoja wypowiedź powinna liczyć minimum 300 wyrazów.”
Potem trzy tematy numerowane 1. 2. 3. Każdy ma tezę oraz zdanie „Zajmij stanowisko wobec powyższej tezy i je uzasadnij, uwzględniając w swojej argumentacji” i trzy konkretne elementy.
model_answer zaczyna się od linii „Temat nr 1” albo „Temat nr 2” albo „Temat nr 3”, potem pusta linia, potem wypracowanie 450–650 słów: wstęp ze stanowiskiem, trzy akapity (po jednym na element) z datami i postaciami, zakończenie wynikające z argumentów. Bez list, bez markdown, bez wymyślonych faktów.
rationale to plan (80–250 słów): teza, trzy elementy, po 2–3 fakty na element. Bez słów „klucz” i „wzorzec”.
hyde: 1–2 zdania encyklopedyczne. kb_facts: 3–5 faktów „rok – wydarzenie – postać/skutek”.
source_text ustaw na pusty string.
Zwróć wyłącznie JSON:
{"source_text": "", "items": [{"question": "...", "model_answer": "...", "rubric": "Kryteria CKE: A narracja 0–12, B spójność 0–3.", "rationale": "...", "hyde": "...", "kb_facts": ["...", "...", "..."]}]}"""

SYS_FIX = """Poprawiasz jedno zadanie zamknięte matury z historii. Rozwiązanie bez podanego klucza nie zgadza się z kluczem.
Ustal jedną poprawną merytorycznie odpowiedź. Możesz zmienić polecenie albo klucz. Zachowaj typ i format odpowiedzi.
Zwróć wyłącznie JSON: {"question": "...", "model_answer": "...", "rubric": "..."}"""

SYS_RAT = """Rozwiń albo skróć rozumowanie do 180–300 słów po polsku. Zachowaj fakty i sens.
Nie używaj słów „klucz”, „wzorzec”, „wzorcowa”.
Zwróć wyłącznie JSON: {"rationale": "..."}"""

SYS_LEN = """Poprawiasz wypracowanie maturalne z historii. Ma mieć 480–620 słów.
Zacznij od linii „Temat nr 1”, „Temat nr 2” albo „Temat nr 3” (zostaw numer, jeśli już jest), potem pusta linia, potem wypracowanie.
Zachowaj stanowisko, trzy elementy i konkretne fakty. Nie dopisuj niepewnych dat.
Zwróć wyłącznie JSON: {"model_answer": "Temat nr 1\\n\\n..."}"""

stop_event = threading.Event()
DEDUP = None


def roman_of(section):
    return str(section).split(".", 1)[0].strip()


def largest_remainder(weights, n):
    keys = list(weights)
    if n <= 0:
        return {k: 0 for k in keys}
    raw = {k: weights[k] * n for k in keys}
    base = {k: int(raw[k]) for k in keys}
    left = n - sum(base.values())
    order = sorted(keys, key=lambda k: (raw[k] - base[k], weights[k]), reverse=True)
    for k in order[: max(0, left)]:
        base[k] += 1
    return base


def load_metas():
    tax = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    metas = []
    for sec in tax.get("sections") or []:
        name = canon_section(sec.get("section")) or sec.get("section")
        rom = roman_of(name)
        if rom not in ROMAN_EPOCH:
            raise RuntimeError(f"brak epoki dla {name}")
        metas.append({
            "section": name,
            "roman": rom,
            "epoch": ROMAN_EPOCH[rom],
            "scope": "Polska" if rom in POLAND else "powszechna",
            "subtopics": list(sec.get("subtopics") or []),
        })
    if len(metas) != 59:
        raise RuntimeError(f"taksonomia ma {len(metas)} działów, oczekiwano 59")
    return metas


def allocate_sections(metas, n):
    sections = [m["section"] for m in metas]
    min_each = 80 if n >= 10000 else (1 if n >= len(sections) else 0)
    if min_each and min_each * len(sections) > n:
        min_each = n // len(sections)
    counts = {s: min_each for s in sections}
    left = n - min_each * len(sections)
    epoch_t = largest_remainder(EPOCH_W, n)
    pol = int(round(n * 0.65))
    scope_t = {"Polska": pol, "powszechna": n - pol}
    by = {m["section"]: m for m in metas}
    guard = 0
    while left > 0 and guard < n * 5 + 10:
        guard += 1
        ep_now = Counter()
        sc_now = Counter()
        for m in metas:
            ep_now[m["epoch"]] += counts[m["section"]]
            sc_now[m["scope"]] += counts[m["section"]]
        best = None
        best_key = None
        for m in metas:
            s = m["section"]
            ep_def = epoch_t[m["epoch"]] - ep_now[m["epoch"]]
            sc_def = scope_t[m["scope"]] - sc_now[m["scope"]]
            key = (1 if ep_def > 0 else 0, 1 if sc_def > 0 else 0, ep_def, sc_def, -counts[s], -sections.index(s))
            if best_key is None or key > best_key:
                best_key = key
                best = s
        counts[best] += 1
        left -= 1
    return counts, epoch_t, scope_t


def subtype_of_type(subtype):
    if subtype == "essay":
        return "essay"
    if subtype.startswith("closed_"):
        return subtype
    return "open"


def load_notes():
    idx = {}
    for row in read_jsonl(KB):
        idx[(row.get("section"), row.get("subtopic"))] = row
        idx[(canon_section(row.get("section") or ""), row.get("subtopic"))] = row
    return idx


def norm_text(text):
    s = (text or "").lower().replace("–", "-").replace("—", "-")
    s = re.sub(r"\[obraz:[^\]]+\]", " ", s, flags=re.I)
    s = re.sub(r"[^0-9a-ząćęłńóśźż\- ]+", " ", s, flags=re.I)
    return re.sub(r"\s+", " ", s).strip()


def literal_leak(source, answer):
    src = norm_text(source)
    if len(src) < 12:
        return False
    chunks = []
    for part in re.split(r"\n+", answer or ""):
        part = LABEL_RE.sub("", part).strip()
        if part:
            chunks.append(part)
    if not chunks:
        chunks = [answer or ""]
    for chunk in chunks:
        n = norm_text(chunk)
        if len(n) >= 12 and n in src:
            return True
        words = n.split()
        if len(words) >= 6:
            for i in range(len(words) - 5):
                gram = " ".join(words[i:i + 6])
                if len(gram) >= 25 and gram in src:
                    return True
    return False


def source_problem(text, kind, marker, subtopic=""):
    text = text or ""
    if is_prehistory(subtopic) and (kind == "dokument" or re.search(r"fragment dokumentu", text, re.I)):
        return "dokument w pradziejach"
    if kind == "ilustracja":
        if marker not in text and not IMG_MARK.search(text):
            return "brak znacznika obrazu"
        head = text.split("[Obraz:", 1)[0]
        if polish_word_count(head) < 3:
            return "za krótki podpis"
        if not CAP_RE.search(head):
            return "podpis bez typu ilustracji"
        return ""
    if IMG_MARK.search(text) or "[Obraz:" in text:
        return "obraz w źródle tekstowym"
    wc = polish_word_count(text)
    if kind == "tabela":
        if "|" not in text:
            return "brak tabeli"
        if not (15 <= wc <= 240):
            return f"długość tabeli {wc}"
        return ""
    if not (40 <= wc <= 240):
        return f"długość źródła {wc}"
    return ""


def fix_essay_answer(text):
    text = (text or "").strip()
    m = re.match(r"(Temat nr [123])\s*", text)
    if not m:
        return text
    body = text[m.end():].strip()
    return m.group(1) + "\n\n" + body


def opener_ok(subtype, question):
    q = " ".join((question or "").split())
    low = q.lower()
    if subtype == "essay":
        return q.startswith(ESSAY_HEAD) and low.count("zajmij stanowisko") >= 3
    if subtype == "closed_tf":
        return low.startswith("oceń prawdziwość")
    if subtype == "closed_choice":
        return low.startswith("dokończ zdanie")
    if subtype == "closed_match":
        return low.startswith("przyporządkuj")
    if subtype == "closed_multi":
        return bool(re.search(r"1[\.\)]", q) and re.search(r"2[\.\)]", q) and "A" in q)
    if subtype == "rozstrzygnij":
        return low.startswith("rozstrzygnij") and "Rozstrzygnięcie:" in q and "Uzasadnienie:" in q
    if subtype == "podaj":
        return low.startswith("podaj") or low.startswith("wymień") or low.startswith("wymien") or low.startswith("nazwij")
    if subtype == "wyjasnij":
        return low.startswith("wyjaśnij") or low.startswith("wyjasnij") or low.startswith("uzasadnij")
    if subtype == "porownaj_inne":
        return low.startswith("porównaj") or low.startswith("porownaj") or low.startswith("wskaż") or low.startswith("wskaz")
    return False


def answer_ok(subtype, typ, answer):
    if typ == "essay":
        if not re.match(r"Temat nr [123]\n\n", answer or ""):
            return False
        wc = word_count(answer)
        return 450 <= wc <= 720
    if typ in CLOSED_TYPES:
        if not valid_model_answer(typ, answer):
            return False
        lines = normalize_closed(typ, answer).splitlines()
        if typ == "closed_tf":
            if len(lines) != 3:
                return False
            marks = {ln[-1] for ln in lines}
            return "P" in marks and "F" in marks
        if typ == "closed_choice":
            return normalize_closed(typ, answer) in "ABCD"
        if typ in ("closed_match", "closed_multi"):
            return len(lines) == 2
        return True
    if not valid_model_answer("open", answer):
        return False
    if subtype == "rozstrzygnij":
        return "Rozstrzygnięcie:" in answer and "Uzasadnienie:" in answer
    if subtype == "porownaj_inne":
        return "Podobieństwo:" in answer and "Różnica:" in answer
    return True


def normalize_answer(typ, answer):
    answer = str(answer or "").strip()
    if typ in CLOSED_TYPES:
        return normalize_closed(typ, answer)
    if typ == "essay":
        return fix_essay_answer(answer)
    return collapse_alternatives(answer)


def content_stems(text):
    stems = []
    for word in re.findall(r"[A-Za-zĄąĆćĘęŁłŃńÓóŚśŹźŻż]{5,}", text or ""):
        low = word.lower()
        if low in STOP_WORDS:
            continue
        stems.append(low[:6])
    return stems


def leak_terms(source, answer_text):
    """Co najmniej połowa słów treściowych odpowiedzi jest w źródle."""
    stems = content_stems(answer_text)
    if not stems:
        return False
    src = set(content_stems(source))
    hit = sum(1 for stem in stems if stem in src)
    return hit / len(stems) >= 0.5


def closed_answer_text(typ, question, model_answer):
    q = question or ""
    if typ == "closed_choice":
        letter = normalize_closed(typ, model_answer)
        m = re.search(rf"(?:^|\n|\s){letter}[\.\)\:]\s*(.+?)(?=(?:\s+[A-D][\.\)\:])|$)", q)
        return m.group(1).strip() if m else ""
    if typ == "closed_tf":
        parts = []
        for ln in normalize_closed(typ, model_answer).splitlines():
            if not ln.endswith("P"):
                continue
            num = ln.split(":", 1)[0].strip()
            m = re.search(rf"(?:^|\n|\s){num}[\.\)]\s*(.+?)(?=(?:\s+\d[\.\)])|$)", q)
            if m:
                parts.append(m.group(1))
        return " ".join(parts)
    if typ == "closed_multi":
        parts = []
        for ln in normalize_closed(typ, model_answer).splitlines():
            num, _, letter = ln.partition(":")
            m = re.search(
                rf"(?:^|\n|\s){num.strip()}[\.\)]\s*.*?{letter.strip()}[\.\)\:]\s*(.+?)(?=(?:\s+[A-D][\.\)\:])|(?:\s+\d[\.\)])|$)",
                q,
            )
            if m:
                parts.append(m.group(1))
        return " ".join(parts)
    if typ == "closed_match":
        parts = []
        for ln in normalize_closed(typ, model_answer).splitlines():
            letter, _, rhs = ln.partition(":")
            letter = letter.strip()
            rhs = rhs.strip()
            m = re.search(rf"(?:^|\n|\s){letter}[\.\)\:]\s*(.+?)(?=(?:\s+[A-B][\.\)\:])|(?:\s+\d[\.\)])|$)", q)
            if m:
                parts.append(m.group(1))
            if rhs:
                m2 = re.search(rf"(?:^|\n|\s){re.escape(rhs)}[\.\)\:]\s*(.+?)(?=(?:\s+\d[\.\)])|$)", q)
                if m2:
                    parts.append(m2.group(1))
        return " ".join(parts)
    return model_answer or ""


def answer_for_leak(rec):
    if rec["type"] in CLOSED_TYPES:
        extracted = closed_answer_text(rec["type"], rec.get("question"), rec.get("model_answer"))
        return extracted or rec.get("model_answer") or ""
    return rec.get("model_answer") or ""


def is_prehistory(subtopic):
    return bool(re.search(r"paleolit|neolit|pradziej", subtopic or "", flags=re.I))


def rationale_problem(text, essay=False):
    wc = polish_word_count(text)
    if not (80 <= wc <= 400):
        return f"rationale {wc} słów"
    if KEY_WORD.search(text or ""):
        return "rationale wspomina klucz lub wzorzec"
    return ""


def facts_ok(facts):
    if not isinstance(facts, list):
        return False
    clean = [str(x).strip() for x in facts if str(x).strip()]
    return 3 <= len(clean) <= 5


def coerce_facts(raw):
    facts = raw if isinstance(raw, list) else []
    if isinstance(raw, str):
        facts = [x.strip(" -\t") for x in raw.split("\n") if x.strip()]
    return [str(x).strip() for x in facts if str(x).strip()][:5]


class Deduper:
    def __init__(self):
        self.lock = threading.Lock()
        self.corpus = []
        self.eval_q = []
        seen_eval = set()
        for path in sorted(EVAL_DIR.glob("*.jsonl")):
            for row in read_jsonl(path):
                q = row.get("question") or ""
                if not q or q in seen_eval:
                    continue
                seen_eval.add(q)
                self.eval_q.append(word_ngrams(q))
        for path in (SYN, REAL, OUT, REJECTED):
            for row in read_jsonl(path):
                q = row.get("question") or ""
                if not q:
                    continue
                self.corpus.append(word_ngrams(q + "\n" + (row.get("model_answer") or "")))

    def check(self, question, answer):
        qg = word_ngrams(question)
        both = word_ngrams((question or "") + "\n" + (answer or ""))
        with self.lock:
            for eg in self.eval_q:
                jac = jaccard(qg, eg)
                if jac > 0.35:
                    return f"eval jaccard {jac:.2f}"
            for og in self.corpus:
                jac = jaccard(both, og)
                if jac > 0.35:
                    return f"dedup jaccard {jac:.2f}"
        return ""

    def add(self, question, answer):
        both = word_ngrams((question or "") + "\n" + (answer or ""))
        with self.lock:
            self.corpus.append(both)


class Planner:
    def __init__(self, n, metas, notes, tag):
        self.n = n
        self.metas = metas
        self.by_section = {m["section"]: m for m in metas}
        self.notes = notes
        self.tag = tag
        self.lock = threading.Lock()
        self.section_target, self.epoch_target, self.scope_target = allocate_sections(metas, n)
        self.subtype_target = largest_remainder(SUBTYPE_W, n)
        n_rest = n - self.subtype_target.get("essay", 0)
        self.source_target = largest_remainder(SOURCE_W, n_rest)
        self.diff_target = largest_remainder(DIFF_W, n)
        self.have_section = Counter()
        self.have_sub = Counter()
        self.have_src = Counter()
        self.have_diff = Counter()
        self.fly_section = Counter()
        self.fly_sub = Counter()
        self.fly_src = Counter()
        self.fly_diff = Counter()
        self.sub_i = Counter()
        self.accepted = 0
        self.inflight_items = 0
        self.attempts = 0
        self.seq = self._load_seq()
        self._seed_existing()

    def _load_seq(self):
        if SEQ_PATH.exists():
            try:
                return int(SEQ_PATH.read_text(encoding="utf-8").strip() or "0")
            except ValueError:
                return 0
        return 0

    def _bump_seq(self):
        self.seq += 1
        SEQ_PATH.parent.mkdir(parents=True, exist_ok=True)
        SEQ_PATH.write_text(str(self.seq), encoding="utf-8")
        return self.seq

    def _seed_existing(self):
        for row in read_jsonl(OUT):
            self.accepted += 1
            sec = row.get("section") or ""
            sub = row.get("subtype") or ""
            self.have_section[sec] += 1
            self.have_sub[sub] += 1
            self.have_diff[row.get("difficulty") or ""] += 1
            if row.get("type") != "essay":
                self.have_src[row.get("source_kind") or ""] += 1

    def _def_sub(self, key):
        return self.subtype_target.get(key, 0) - self.have_sub[key] - self.fly_sub[key]

    def _def_src(self, key):
        return self.source_target.get(key, 0) - self.have_src[key] - self.fly_src[key]

    def _def_diff(self, key):
        return self.diff_target.get(key, 0) - self.have_diff[key] - self.fly_diff[key]

    def _rem_section(self, section):
        return self.section_target.get(section, 0) - self.have_section[section] - self.fly_section[section]

    def reserve(self, limit, attempt_cap):
        with self.lock:
            if self.accepted >= limit or self.attempts >= attempt_cap:
                return None
            if self.accepted + self.inflight_items >= limit:
                return None
            mode, subs = self._pick_mode()
            if mode is None:
                return None
            need = 1 if mode != "pair" else 2
            section = self._pick_section(need)
            if section is None and need == 2:
                mode, subs = "single", subs[:1]
                section = self._pick_section(1)
            if section is None:
                return None
            if mode == "pair" and len(subs) < 2:
                mode = "single"
                subs = subs[:1]
            if mode == "essay":
                subs = ["essay"]
            elif mode == "single":
                subs = subs[:1] or [self._best_sub(exclude_essay=True)]
            else:
                if len(subs) < 2:
                    return None
            meta = self.by_section[section]
            idx = self.sub_i[section]
            self.sub_i[section] += 1
            subtopic = meta["subtopics"][idx % len(meta["subtopics"])] if meta["subtopics"] else ""
            if mode == "essay":
                kinds = []
            else:
                kind = self._pick_src(len(subs), subtopic)
                kinds = [kind] * len(subs)
            diffs = [self._pick_diff() for _ in subs]
            seq = self._bump_seq()
            bid = f"e5-{self.tag}-{seq:05d}"
            spec = {
                "bid": bid,
                "section": section,
                "subtopic": subtopic,
                "epoch": meta["epoch"],
                "scope": meta["scope"],
                "source_kind": kinds[0] if kinds else "opracowanie",
                "items": [
                    {"subtype": sub, "difficulty": diff}
                    for sub, diff in zip(subs, diffs)
                ],
            }
            self.attempts += 1
            self.inflight_items += len(spec["items"])
            self.fly_section[section] += len(spec["items"])
            for it in spec["items"]:
                self.fly_sub[it["subtype"]] += 1
                self.fly_diff[it["difficulty"]] += 1
                if it["subtype"] != "essay":
                    self.fly_src[spec["source_kind"]] += 1
            return spec

    def _pick_mode(self):
        essay_def = self._def_sub("essay")
        rest = [s for s in SUBTYPE_W if s != "essay" and self._def_sub(s) > 0]
        rest.sort(key=lambda s: self._def_sub(s), reverse=True)

        def fill(key):
            t = self.subtype_target.get(key) or 1
            return (self.have_sub[key] + self.fly_sub[key]) / t

        if essay_def > 0 and (not rest or fill("essay") <= min(fill(s) for s in rest)):
            return "essay", ["essay"]
        if len(rest) >= 2 and self._def_sub(rest[0]) > 0 and self._def_sub(rest[1]) > 0:
            return "pair", rest[:2]
        if rest:
            return "single", rest[:1]
        if essay_def > 0:
            return "essay", ["essay"]
        return None, []

    def _best_sub(self, exclude_essay):
        pool = [s for s in SUBTYPE_W if not (exclude_essay and s == "essay")]
        pool.sort(key=lambda s: self._def_sub(s), reverse=True)
        return pool[0]

    def _pick_section(self, need):
        cands = [m["section"] for m in self.metas if self._rem_section(m["section"]) >= need]
        if not cands:
            return None
        cands.sort(key=lambda s: (self._rem_section(s), -self.have_section[s]), reverse=True)
        top = self._rem_section(cands[0])
        tied = [s for s in cands if self._rem_section(s) == top]
        return random.choice(tied[:4] or tied)

    def _pick_src(self, k, subtopic=""):
        keys = [s for s in SOURCE_W if not (s == "dokument" and is_prehistory(subtopic))]
        if not keys:
            keys = ["opracowanie"]
        keys.sort(key=lambda s: self._def_src(s), reverse=True)
        for key in keys:
            if self._def_src(key) >= k:
                return key
        return keys[0]

    def _pick_diff(self):
        keys = list(DIFF_W)
        keys.sort(key=lambda s: self._def_diff(s), reverse=True)
        return keys[0]

    def release(self, spec):
        with self.lock:
            self._unfly(spec)

    def commit(self, spec, accepted_recs):
        with self.lock:
            self._unfly(spec)
            for rec in accepted_recs:
                self.accepted += 1
                self.have_section[rec["section"]] += 1
                self.have_sub[rec["subtype"]] += 1
                self.have_diff[rec["difficulty"]] += 1
                if rec["type"] != "essay":
                    self.have_src[rec["source_kind"]] += 1

    def _unfly(self, spec):
        k = len(spec["items"])
        self.inflight_items = max(0, self.inflight_items - k)
        self.fly_section[spec["section"]] = max(0, self.fly_section[spec["section"]] - k)
        for it in spec["items"]:
            self.fly_sub[it["subtype"]] = max(0, self.fly_sub[it["subtype"]] - 1)
            self.fly_diff[it["difficulty"]] = max(0, self.fly_diff[it["difficulty"]] - 1)
            if it["subtype"] != "essay":
                self.fly_src[spec["source_kind"]] = max(0, self.fly_src[spec["source_kind"]] - 1)


def note_for(notes, section, subtopic):
    row = notes.get((section, subtopic))
    if row:
        return row
    for (sec, sub), val in notes.items():
        if sub == subtopic:
            return val
    return None


def user_prompt(spec, notes):
    note = note_for(notes, spec["section"], spec["subtopic"])
    note_txt = (note.get("text") if note else "") or "Brak notatki. Użyj wyłącznie faktów pewnych z podręcznika."
    lines = [
        f"Dział: {spec['section']}",
        f"Podtemat: {spec['subtopic']}",
        f"Epoka: {spec['epoch']}",
        f"Zakres: {'historia Polski' if spec['scope'] == 'Polska' else 'historia powszechna'}",
    ]
    if spec["items"][0]["subtype"] == "essay":
        lines.append(DIFF_RULES[spec["items"][0]["difficulty"]])
        lines.append(f"\nNotatka:\n{note_txt[:3500]}")
        return "\n".join(lines)
    marker = f"[Obraz: images/{spec['bid']}.png]"
    lines.append(SOURCE_RULES[spec["source_kind"]])
    if spec["source_kind"] == "dokument":
        lines.append(DOC_BY_EPOCH.get(spec["epoch"], ""))
    if is_prehistory(spec["subtopic"]):
        lines.append("Temat jest pradziejowy: nie pisz „Fragment dokumentu”. Użyj opracowania, tabeli albo ilustracji.")
    if spec["source_kind"] == "ilustracja":
        lines.append(f"Wstaw dokładnie ten znacznik w osobnej linii: {marker}")
    lines.append("Zadania (dokładnie tyle, w tej kolejności, bez zmiany typu):")
    for i, it in enumerate(spec["items"], start=1):
        lines.append(f"{i}. {KIND_RULES[it['subtype']]} {DIFF_RULES[it['difficulty']]}")
    lines.append(f"\nNotatka:\n{note_txt[:3500]}")
    return "\n".join(lines)


def empty_verify(max_points):
    return {"blind_answer": "", "match": False, "judge_points": 0, "judge_max": max_points}


def base_record(spec, idx, question, source, answer, rubric, rationale, hyde, facts, leak, cost):
    it = spec["items"][idx - 1]
    subtype = it["subtype"]
    typ = subtype_of_type(subtype)
    pts = 15 if typ == "essay" else 1
    return {
        "id": f"{spec['bid']}-{idx}",
        "origin": "synthetic",
        "source_doc": "e5",
        "section": spec["section"],
        "subtopic": spec["subtopic"],
        "type": typ,
        "group": spec["bid"],
        "max_points": pts,
        "question": question,
        "source_text": source,
        "answer_format": canonical_format(typ, answer),
        "model_answer": answer,
        "rubric": rubric,
        "needs_image": False,
        "image_refs": [],
        "verified": False,
        "verify_note": "",
        "epoch": spec["epoch"],
        "scope": spec["scope"],
        "subtype": subtype,
        "difficulty": it["difficulty"],
        "source_kind": spec["source_kind"],
        "rationale": rationale,
        "hyde": hyde,
        "kb_facts": facts,
        "leak": leak,
        "verify": empty_verify(pts),
        "prompt_version": PROMPT_VERSION,
        "cost_usd": round(cost, 6),
    }


def build_item(spec, idx, raw, source, cost):
    it = spec["items"][idx - 1]
    subtype = it["subtype"]
    typ = subtype_of_type(subtype)
    question = str(raw.get("question") or "").strip()
    question = re.sub(r"[ \t]+", " ", question)
    question = re.sub(r" *\n *", "\n", question).strip()
    answer = normalize_answer(typ, raw.get("model_answer"))
    rubric = str(raw.get("rubric") or "").strip()
    if typ != "essay" and "pkt" not in rubric.lower():
        rubric = "1 pkt – za poprawną, jednoznaczną odpowiedź.\n0 pkt – za odpowiedź niepełną lub błędną albo za brak odpowiedzi."
    if typ == "essay" and not rubric:
        rubric = "Kryteria CKE wypowiedzi argumentacyjnej: A narracja historyczna 0–12, B spójność 0–3."
    rationale = str(raw.get("rationale") or "").strip()
    hyde = " ".join(str(raw.get("hyde") or "").split())
    facts = coerce_facts(raw.get("kb_facts"))
    if len(question) < 40:
        return None, "krótkie polecenie"
    if not opener_ok(subtype, question):
        return None, "zły początek polecenia"
    if typ == "essay" and answer:
        found = re.search(r"Temat nr [123]", answer)
        if found:
            answer = fix_essay_answer(answer[found.start():])
        else:
            answer = "Temat nr 1\n\n" + answer.strip()
    if typ == "essay" and re.match(r"Temat nr [123]\n\n", answer or "") and not answer_ok(subtype, typ, answer):
        rec = base_record(spec, idx, question, source, answer, rubric, rationale, hyde, facts, False, cost)
        return rec, f"esej_dlugosc {word_count(answer)}"
    if not answer_ok(subtype, typ, answer):
        head = (answer or "").replace("\n", " ")[:60]
        return None, f"zły format odpowiedzi {head}"
    if len(hyde) < 40:
        return None, "hyde"
    if not facts_ok(facts):
        return None, "kb_facts"
    rp = rationale_problem(rationale, essay=(typ == "essay"))
    if rp:
        rec = base_record(spec, idx, question, source, answer, rubric, rationale, hyde, facts, False, cost)
        return rec, rp
    leak = literal_leak(source, answer)
    term_blob = ""
    if subtype in ("podaj", "rozstrzygnij"):  # w zamkniętych treść opcji z natury pokrywa się ze źródłem
        term_blob = answer
    terms = bool(term_blob) and leak_terms(source, term_blob)
    if terms or (leak and subtype in ("podaj", "rozstrzygnij")):
        rec = base_record(spec, idx, question, source, answer, rubric, rationale, hyde, facts, True, cost)
        return rec, "leak_terms" if terms else "leak"
    rec = base_record(spec, idx, question, source, answer, rubric, rationale, hyde, facts, leak, cost)
    return rec, ""


def expand_rationale(forge, rec):
    data, _, cost = forge.call_json(
        "E5", MODEL, SYS_RAT, rec.get("rationale") or "", 1400, 0.006, "rationale"
    )
    text = str(data.get("rationale") or "").strip()
    rec["cost_usd"] = round(float(rec.get("cost_usd") or 0) + cost, 6)
    if rationale_problem(text):
        return False
    rec["rationale"] = text
    return True


def rewrite_essay(forge, rec):
    data, _, cost = forge.call_json(
        "E5", MODEL, SYS_LEN, (rec.get("model_answer") or "")[:8000], 5000, 0.02, "essay-len"
    )
    answer = normalize_answer("essay", data.get("model_answer"))
    rec["cost_usd"] = round(float(rec.get("cost_usd") or 0) + cost, 6)
    if not answer_ok("essay", "essay", answer):
        return False
    rec["model_answer"] = answer
    rec["answer_format"] = canonical_format("essay", answer)
    return True


def apply_fix(forge, rec):
    user = (
        f"Typ: {rec['type']}\nPolecenie:\n{rec['question']}\n\n"
        f"Klucz:\n{rec['model_answer']}\n\nOdpowiedź na ślepo:\n{rec['verify'].get('blind_answer') or rec.get('_blind') or ''}"
    )
    data, _, cost = forge.call_json("E5", MODEL, SYS_FIX, user, 900, 0.008, "fix")
    question = " ".join(str(data.get("question") or "").split())
    answer = normalize_answer(rec["type"], data.get("model_answer"))
    if not opener_ok(rec["subtype"], question) or not answer_ok(rec["subtype"], rec["type"], answer):
        return None, cost
    rec = dict(rec)
    rec["question"] = question
    rec["model_answer"] = answer
    rec["answer_format"] = canonical_format(rec["type"], answer)
    if str(data.get("rubric") or "").strip():
        rec["rubric"] = str(data.get("rubric")).strip()
    rec["leak"] = literal_leak(rec["source_text"], answer)
    rec["cost_usd"] = round(rec["cost_usd"] + cost, 6)
    return rec, cost


def attach_verify(rec, blind, matched):
    rec["verify"] = {
        "blind_answer": blind or "",
        "match": bool(matched),
        "judge_points": rec["max_points"] if matched else 0,
        "judge_max": rec["max_points"],
    }


def publish_reject(rec, reason):
    row = dict(rec)
    row["verified"] = False
    row["reason"] = reason
    row.pop("_blind", None)
    if DEDUP is not None and row.get("question") and not str(reason).startswith(("dedup", "eval")):
        DEDUP.add(row.get("question"), row.get("model_answer") or "")
    append_jsonl(REJECTED, row)
    print(f"odrzucone {row.get('id')} {reason}", flush=True)


def publish_ok(rec):
    rec["verified"] = True
    rec.pop("_blind", None)
    append_jsonl(OUT, rec)
    print(f"przyjęte {rec['id']} {rec['subtype']} {rec['epoch']} {rec['scope']}", flush=True)


def verify_one(forge, dedup, rec):
    why = dedup.check(rec["question"], rec["model_answer"])
    if why:
        publish_reject(rec, why)
        return None
    if rec["type"] == "essay":
        judged = judge_essay(forge, rec, stage="E5", max_tokens=1200, estimate=0.01)
        cost = float(judged.pop("_cost", 0) or 0)
        pts = int(judged.get("points") or 0)
        rec["cost_usd"] = round(rec["cost_usd"] + cost, 6)
        rec["verify"] = {
            "blind_answer": "",
            "match": pts >= 12,
            "judge_points": pts,
            "judge_max": 15,
        }
        rec["verify_note"] = f"{pts}/15; {judged.get('reason', '')}"
        if pts < 12:
            publish_reject(rec, f"esej_ocena {pts}/15")
            return None
        publish_ok(rec)
        return rec
    checked, vcost = verify(forge, rec, stage="E5")
    rec = checked
    rec["cost_usd"] = round(float(rec.get("cost_usd") or 0) + vcost, 6)
    blind = rec.get("_blind") or ""
    if rec["type"] in CLOSED_TYPES and not rec["verified"]:
        attach_verify(rec, blind, False)
        try:
            fixed, _ = apply_fix(forge, rec)
        except BudgetExceeded:
            publish_reject(rec, "weryfikacja")
            raise
        except Exception as exc:
            fixed = None
            rec["verify_note"] = (rec.get("verify_note") or "") + " | naprawa: " + safe_err(exc)
        if fixed is None:
            publish_reject(rec, "weryfikacja")
            return None
        why = dedup.check(fixed["question"], fixed["model_answer"])
        if why or (fixed["leak"] and fixed["subtype"] in ("podaj", "rozstrzygnij")):
            publish_reject(fixed, why or "leak")
            return None
        checked, vcost = verify(forge, fixed, stage="E5")
        rec = checked
        rec["cost_usd"] = round(float(rec.get("cost_usd") or 0) + vcost, 6)
        blind = rec.get("_blind") or ""
    matched = bool(rec.get("verified"))
    attach_verify(rec, blind, matched)
    if not matched:
        publish_reject(rec, "weryfikacja")
        return None
    if rec["leak"] and rec["subtype"] in ("podaj", "rozstrzygnij"):
        publish_reject(rec, "leak")
        return None
    blob = answer_for_leak(rec)
    if rec["subtype"] in ("podaj", "rozstrzygnij"):
        if leak_terms(rec.get("source_text") or "", blob):
            rec["leak"] = True
            publish_reject(rec, "leak_terms")
            return None
    again = dedup.check(rec["question"], rec["model_answer"])
    if again:
        publish_reject(rec, again)
        return None
    dedup.add(rec["question"], rec["model_answer"])
    publish_ok(rec)
    return rec


def prepare_source(spec, text):
    text = str(text or "").strip()
    if spec["items"][0]["subtype"] == "essay":
        return "", ""
    marker = f"[Obraz: images/{spec['bid']}.png]"
    if spec["source_kind"] == "ilustracja":
        if IMG_MARK.search(text):
            text = IMG_MARK.sub(marker, text, count=1)
        elif marker not in text:
            text = text.rstrip() + "\n" + marker
    problem = source_problem(text, spec["source_kind"], marker, spec.get("subtopic") or "")
    return text, problem


def process_call(forge, dedup, notes, spec):
    if stop_event.is_set():
        return []
    saved = []
    essay = spec["items"][0]["subtype"] == "essay"
    system = SYS_ESSAY if essay else SYS_GEN
    estimate = 0.025 if essay else 0.015
    max_tokens = 8000 if essay else 7000
    try:
        data, _, gen_cost = forge.call_json(
            "E5", MODEL, system, user_prompt(spec, notes), max_tokens, estimate, spec["bid"]
        )
    except BudgetExceeded:
        stop_event.set()
        return saved
    raw_items = data.get("items") if isinstance(data, dict) else None
    if isinstance(raw_items, dict):
        raw_items = [raw_items]
    if not isinstance(raw_items, list):
        raw_items = []
    source, problem = prepare_source(spec, data.get("source_text") if isinstance(data, dict) else "")
    n = max(1, len(raw_items))
    share = gen_cost / n
    if problem or not raw_items:
        reason = problem or "brak zadań"
        append_jsonl(REJECTED, {
            "id": spec["bid"],
            "reason": "zrodlo" if problem else "format",
            "verify_note": reason,
            "section": spec["section"],
            "subtype": ",".join(it["subtype"] for it in spec["items"]),
            "source_text": source[:500],
            "cost_usd": round(gen_cost, 6),
            "prompt_version": PROMPT_VERSION,
        })
        print(f"odrzucone {spec['bid']} {reason}", flush=True)
        return saved
    for idx, raw in enumerate(raw_items[: len(spec["items"])], start=1):
        if stop_event.is_set():
            break
        if not isinstance(raw, dict):
            publish_reject({"id": f"{spec['bid']}-{idx}", "reason": "format", "cost_usd": round(share, 6), "section": spec["section"]}, "format")
            continue
        rec, reason = build_item(spec, idx, raw, source, share)
        if rec and reason and (reason.startswith("rationale") or reason.startswith("esej_dlugosc")):
            try:
                fixed = expand_rationale(forge, rec) if reason.startswith("rationale") else rewrite_essay(forge, rec)
            except BudgetExceeded:
                stop_event.set()
                publish_reject(rec, reason)
                break
            except Exception as exc:
                fixed = False
                rec["verify_note"] = safe_err(exc)
            if fixed and reason.startswith("esej_dlugosc"):
                rp = rationale_problem(rec.get("rationale") or "", essay=True)
                if rp:
                    try:
                        fixed = expand_rationale(forge, rec)
                    except BudgetExceeded:
                        stop_event.set()
                        publish_reject(rec, rp)
                        break
                    except Exception:
                        fixed = False
                    reason = "" if fixed else rp
                else:
                    reason = ""
            elif fixed:
                reason = ""
        if rec and not reason:
            if len(str(rec.get("hyde") or "")) < 40:
                reason = "hyde"
            elif not facts_ok(rec.get("kb_facts") or []):
                reason = "kb_facts"
            elif rec.get("leak") and rec.get("subtype") in ("podaj", "rozstrzygnij"):
                reason = "leak"
        if reason:
            if rec:
                publish_reject(rec, reason)
            else:
                publish_reject({
                    "id": f"{spec['bid']}-{idx}",
                    "reason": reason,
                    "section": spec["section"],
                    "subtype": spec["items"][idx - 1]["subtype"],
                    "question": str(raw.get("question") or "")[:400],
                    "cost_usd": round(share, 6),
                    "prompt_version": PROMPT_VERSION,
                }, reason)
            continue
        try:
            kept = verify_one(forge, dedup, rec)
        except BudgetExceeded:
            stop_event.set()
            break
        if kept:
            saved.append(kept)
    return saved


def self_check():
    metas = load_metas()
    assert set(ROMAN_EPOCH) == {m["roman"] for m in metas}
    for n in (100, 10000):
        counts, epoch_t, scope_t = allocate_sections(metas, n)
        assert sum(counts.values()) == n, n
        ep = Counter()
        sc = Counter()
        for m in metas:
            ep[m["epoch"]] += counts[m["section"]]
            sc[m["scope"]] += counts[m["section"]]
        assert ep == Counter(epoch_t), (n, ep, epoch_t)
        assert abs(sc["Polska"] - scope_t["Polska"]) <= 2, (n, sc, scope_t)
        if n >= 10000:
            assert min(counts.values()) >= 80
        if n == 100:
            assert min(counts.values()) >= 1
    assert literal_leak(
        "Fragment opracowania. Bitwa pod Grunwaldem rozegrała się piętnastego lipca.",
        "Bitwa pod Grunwaldem rozegrała się piętnastego lipca.",
    )
    assert not literal_leak(
        "Fragment opracowania. Wojska stanęły na polach pod wsią.",
        "Rozstrzygnięcie: 1410\nUzasadnienie: Starcie kojarzy się z wielką wojną z zakonem.",
    )
    subs = largest_remainder(SUBTYPE_W, 100)
    assert sum(subs.values()) == 100
    assert subs["closed_match"] == 14
    assert subs["essay"] == 6
    assert not leak_terms(
        "Rycina z 1914 r.",
        "zamach na arcyksięcia Franciszka Ferdynanda w Sarajewie",
    )
    assert leak_terms(
        "Rycina przedstawiająca zamach na arcyksięcia Franciszka Ferdynanda w Sarajewie.",
        "zamach na arcyksięcia Franciszka Ferdynanda w Sarajewie",
    )
    assert not rationale_problem("słowo " * 90)
    assert rationale_problem("słowo " * 40)
    print("self_check ok", flush=True)


def counter_table(title, rows, key):
    c = Counter(r.get(key) or "—" for r in rows)
    lines = [f"### {title}", "", "| wartość | liczba | udział |", "|---|---:|---:|"]
    total = sum(c.values()) or 1
    for name, k in c.most_common():
        lines.append(f"| {name} | {k} | {k / total:.0%} |")
    lines.append("")
    return "\n".join(lines)


def reason_bucket(row):
    raw = str(row.get("reason") or row.get("verify_note") or "inne")
    for name in (
        "eval", "dedup", "leak_terms", "leak", "weryfikacja", "esej_ocena", "esej", "rationale",
        "zrodlo", "format", "hyde", "kb_facts", "api", "zły", "krótkie", "brak",
    ):
        if raw.startswith(name) or name in raw[:40]:
            return name if name not in ("zły", "krótkie", "brak") else "format"
    return raw.split()[0][:40]


def write_stats(elapsed, new_accepted, base_e5, base_calls):
    items = read_jsonl(OUT)
    rej = read_jsonl(REJECTED)
    e5_rows = [r for r in read_jsonl(COST_LOG) if r.get("stage") == "E5"]
    cost = sum(float(r.get("cost_usd") or 0) for r in e5_rows) - base_e5
    calls = len(e5_rows) - base_calls
    buckets = Counter(reason_bucket(r) for r in rej)
    decided = len(items) + len(rej)
    lines = [
        "# E5 — statystyki",
        "",
        f"- Zaakceptowane: **{len(items)}**",
        f"- Odrzucone: **{len(rej)}**",
        f"- Odsetek odrzuceń: {(len(rej) / decided):.0%}" if decided else "- Odsetek odrzuceń: —",
        f"- Koszt tego uruchomienia (usage × 1,2): **${cost:.4f}**",
        f"- Wywołania API w tym uruchomieniu: {calls}",
        f"- Czas uruchomienia: {elapsed / 60:.1f} min",
    ]
    if new_accepted:
        avg = elapsed / new_accepted
        lines.append(f"- Średni czas ścienny na zaakceptowane zadanie: {avg:.1f} s")
        lines.append(f"- Szacunek 10 000 zadań przy tej współbieżności: {avg * 10000 / 3600:.1f} h")
    lines.append("")
    lines.append("## Odrzucenia wg powodu")
    lines.append("")
    lines.append("| powód | liczba | udział odrzuceń |")
    lines.append("|---|---:|---:|")
    rt = sum(buckets.values()) or 1
    for name, k in buckets.most_common():
        lines.append(f"| {name} | {k} | {k / rt:.0%} |")
    lines.append("")
    lines.append(counter_table("Typ", items, "type"))
    lines.append(counter_table("Subtype", items, "subtype"))
    lines.append(counter_table("Epoka", items, "epoch"))
    lines.append(counter_table("Zakres", items, "scope"))
    lines.append(counter_table("Rodzaj źródła", items, "source_kind"))
    lines.append(counter_table("Trudność", items, "difficulty"))
    lines.append("### Dział")
    lines.append("")
    lines.append("| dział | liczba |")
    lines.append("|---|---:|")
    by_sec = Counter(r.get("section") or "—" for r in items)
    for sec, k in sorted(by_sec.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"| {sec} | {k} |")
    lines.append("")
    STATS.write_text("\n".join(lines), encoding="utf-8")


def md_block(title, text):
    return f"### {title}\n\n{(text or '').strip()}\n"


def render_item(rec):
    meta = (
        f"{rec.get('id')} | {rec.get('type')} | {rec.get('subtype')} | {rec.get('epoch')} | "
        f"{rec.get('scope')} | {rec.get('difficulty')} | {rec.get('source_kind')} | "
        f"{rec.get('section')} | {rec.get('max_points')} pkt | leak={rec.get('leak')} | "
        f"verified={rec.get('verified')}"
    )
    facts = rec.get("kb_facts") or []
    if isinstance(facts, list):
        facts_txt = "\n".join(f"- {f}" for f in facts)
    else:
        facts_txt = str(facts)
    verify = rec.get("verify") or {}
    parts = [
        f"## {rec.get('id')}",
        "",
        meta,
        "",
        md_block("Źródło", rec.get("source_text") or "—"),
        md_block("Polecenie", rec.get("question")),
        md_block("answer_format", rec.get("answer_format")),
        md_block("Wzorowa odpowiedź", rec.get("model_answer")),
        md_block("Rationale", rec.get("rationale")),
        md_block("Hyde", rec.get("hyde")),
        "### kb_facts\n\n" + (facts_txt or "—") + "\n",
        md_block("Weryfikacja", json.dumps(verify, ensure_ascii=False)),
        "",
    ]
    return "\n".join(parts)


def pick_rejected(rows, k=10):
    chosen = []
    seen = set()
    for row in rows:
        bucket = reason_bucket(row)
        if bucket in seen:
            continue
        seen.add(bucket)
        chosen.append(row)
        if len(chosen) >= k:
            return chosen
    for row in rows:
        if row in chosen:
            continue
        chosen.append(row)
        if len(chosen) >= k:
            break
    return chosen


def write_sample(tag):
    items = read_jsonl(OUT)
    rej = pick_rejected(read_jsonl(REJECTED), 10)
    name = "e5_pilot.md" if tag == "pilot" else f"e5_{tag}.md"
    path = SFT / "samples" / name
    parts = [f"# E5 próbka ({tag})", "", f"Zaakceptowane: {len(items)}.", ""]
    for rec in items:
        parts.append(render_item(rec))
    parts.append("## Odrzucone\n")
    for rec in rej:
        parts.append(f"### {rec.get('id')} — {rec.get('reason')}")
        parts.append("")
        if rec.get("question"):
            parts.append(md_block("Polecenie", rec.get("question")))
        if rec.get("model_answer"):
            parts.append(md_block("Odpowiedź", rec.get("model_answer")))
        if rec.get("verify_note"):
            parts.append(md_block("Notatka", rec.get("verify_note")))
        parts.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")
    return path


def arm_budget(tag):
    if tag != "pilot":
        return
    # Twardy sufit pilota: całe E5, nie „kolejne 0,5” przy wznowieniu.
    STAGE_LIMITS["E5"] = 0.5


def e5_baseline():
    rows = [r for r in read_jsonl(COST_LOG) if r.get("stage") == "E5"]
    return sum(float(r.get("cost_usd") or 0) for r in rows), len(rows)


def run_wave(forge, dedup, notes, planner, workers, limit, attempt_cap):
    pending = {}
    saved_all = []
    with ThreadPoolExecutor(max(1, workers)) as ex:
        while not stop_event.is_set():
            while len(pending) < workers and not stop_event.is_set():
                spec = planner.reserve(limit, attempt_cap)
                if spec is None:
                    break
                fut = ex.submit(process_call, forge, dedup, notes, spec)
                pending[fut] = spec
            if not pending:
                break
            done, _ = wait(set(pending), return_when=FIRST_COMPLETED)
            for fut in done:
                spec = pending.pop(fut)
                try:
                    saved = fut.result()
                except BudgetExceeded:
                    stop_event.set()
                    planner.release(spec)
                    continue
                except Exception as exc:
                    planner.release(spec)
                    append_jsonl(REJECTED, {
                        "id": spec["bid"],
                        "reason": "api",
                        "verify_note": safe_err(exc),
                        "section": spec["section"],
                        "prompt_version": PROMPT_VERSION,
                    })
                    print("api", spec["bid"], safe_err(exc), flush=True)
                    continue
                if saved is None:
                    planner.release(spec)
                    continue
                planner.commit(spec, saved)
                saved_all.extend(saved)
            if planner.accepted >= limit:
                break
        for fut, spec in list(pending.items()):
            try:
                saved = fut.result()
            except Exception as exc:
                planner.release(spec)
                print("api-late", spec["bid"], safe_err(exc), flush=True)
                continue
            planner.commit(spec, saved or [])
            saved_all.extend(saved or [])
    return saved_all


def write_chunk_sample(n_new, rows):
    if not rows:
        return None
    pick = rows if len(rows) <= 20 else random.sample(rows, 20)
    path = SFT / "samples" / f"e5_chunk_{n_new}.md"
    parts = [f"# E5 paczka — {n_new} nowych zadań", "", f"Losowe {len(pick)} z {len(rows)} w tej paczce.", ""]
    for rec in pick:
        parts.append(render_item(rec))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")
    print(f"próbka {path}", flush=True)
    return path


def file_lines(path):
    path = Path(path)
    if not path.exists():
        return 0
    return sum(1 for line in path.open(encoding="utf-8") if line.strip())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=100)
    parser.add_argument("--tag", default="pilot")
    parser.add_argument("--chunk", type=int, default=2000)
    parser.add_argument("--workers", type=int, default=24)
    args = parser.parse_args()
    if args.n < 1:
        raise SystemExit("--n >= 1")
    workers = min(24, max(1, args.workers))
    ensure_dirs()
    self_check()
    arm_budget(args.tag)
    metas = load_metas()
    notes = load_notes()
    planner = Planner(args.n, metas, notes, args.tag)
    if planner.accepted >= args.n:
        print(f"już jest {planner.accepted} zadań, cel {args.n}", flush=True)
        write_stats(0, 0, 0, 0)
        write_sample(args.tag)
        return
    base_cost, base_calls = e5_baseline()
    forge = Forge()
    global DEDUP
    DEDUP = Deduper()
    dedup = DEDUP
    started = planner.accepted
    t0 = time.perf_counter()
    attempt_cap = max(args.n * 5, 30)
    print(
        f"E5 start accepted {started} cel {args.n} tag {args.tag} "
        f"limit ${STAGE_LIMITS['E5']:.2f} workers {workers}",
        flush=True,
    )
    while planner.accepted < args.n and not stop_event.is_set() and planner.attempts < attempt_cap:
        before = planner.accepted
        rej_before = file_lines(REJECTED)
        wave_limit = min(args.n, before + max(1, args.chunk))
        chunk_rows = run_wave(forge, dedup, notes, planner, workers, wave_limit, attempt_cap)
        elapsed = time.perf_counter() - t0
        write_stats(elapsed, planner.accepted - started, base_cost, base_calls)
        new_total = planner.accepted - started
        write_chunk_sample(new_total, chunk_rows)
        new_rej = file_lines(REJECTED) - rej_before
        decided = (planner.accepted - before) + max(0, new_rej)
        rate = (new_rej / decided) if decided else 0
        print(
            f"fala {planner.accepted}/{args.n} próby {planner.attempts} "
            f"paczka +{planner.accepted - before} odrzucenia {rate:.0%}",
            flush=True,
        )
        if planner.accepted >= wave_limit and decided >= 80 and rate > 0.25:
            print("UWAGA: odrzucenia paczki powyżej 25% — próbka do przeglądu", flush=True)
        if planner.accepted == before:
            break
    elapsed = time.perf_counter() - t0
    if args.tag == "pilot":
        sample = write_sample(args.tag)
    else:
        sample = SFT / "samples"
    write_stats(elapsed, planner.accepted - started, base_cost, base_calls)
    spent, total = spent_by_stage()
    new_acc = planner.accepted - started
    print(
        f"E5 stop accepted {planner.accepted} new {new_acc} rejected {len(read_jsonl(REJECTED))} "
        f"cost ${spent['E5'] - base_cost:.4f} elapsed {elapsed:.0f}s sample {sample}",
        flush=True,
    )


if __name__ == "__main__":
    main()
