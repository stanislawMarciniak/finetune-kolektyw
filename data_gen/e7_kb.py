"""E7: baza wiedzy v2 — luki w podtematach, syntezy aspektowe, kluczowe zagadnienia, uzupełnienie osi czasu,
postaci i pojęć, weryfikacja faktów. Limit etapu 3,5 USD. Generowane wyłącznie z taksonomii CKE.

  python -m data_gen.e7_kb gen      # faza generowania (wznawialna)
  python -m data_gen.e7_kb gen3     # v3: pogłębienie (druga runda zagadnień, syntezy połówkowe, argumenty, oś czasu)
  python -m data_gen.e7_kb gen4     # v3: zagadnienia społeczno-gospodarcze i kulturowe
  python -m data_gen.e7_kb verify   # weryfikacja luną → data/kb/e7/*.verified.jsonl
  python -m data_gen.e7_kb build    # kompendium_v2.jsonl, kb_all_notes_v2.jsonl, KB_V2_STATS.md
"""

import argparse
import json
import re
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_gen.common import BudgetExceeded, Forge, ROOT, append_jsonl, polish_word_count, read_jsonl, safe_err, spent_by_stage
from data_gen.e5_bulk import load_metas
from data_gen.e6_kb import has_date, norm_name, valid_person, valid_term, valid_timeline

KB = ROOT / "data" / "kb"
OUT = KB / "e7"
MODEL = "gpt-6-luna"
STAGE = "E7"
ASPECTS = ("polityczny", "społeczno-gospodarczy", "kulturowo-religijny")
BROAD = {"II", "III", "IV", "V", "VI", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XVII", "XXII", "XXIII", "XXIV",
         "XXX", "XXXIII", "XXXIV", "XXXV", "XXXVI", "XLII", "XLIII", "LI", "LII", "LIII", "LVII", "LX"}
FILES = {k: OUT / f"{k}.jsonl" for k in ("notes", "timeline", "persons", "terms", "topics", "topics2", "topics3")}
stop = threading.Event()
lock = threading.Lock()

NOTE_RULES = """Piszesz notatki kompendium do matury z historii (poziom rozszerzony), po polsku, każda 280–330 słów.
Tylko pewne, szkolne fakty — bez zmyślonych dat, liczb i nazwisk. Konkret zamiast ogólników: co najmniej 5 dat, nazwiska, nazwy aktów prawnych, bitew, instytucji, miejsc; przyczyny i skutki.
Tekst w 3–4 akapitach rozdzielonych pustą linią. Ostatnie zdanie: wniosek/ocena przydatna jako argument w wypracowaniu."""

SYS = {
    "gap": NOTE_RULES + """
Jedna notatka na każdy podany podtemat. Pole subtopic przepisz dokładnie z polecenia.
Zwróć wyłącznie JSON: {"items": [{"subtopic": "...", "title": "...", "text": "..."}]}""",
    "aspect": NOTE_RULES + """
To synteza aspektowa działu do wypracowania: tylko wskazany aspekt, uporządkowany chronologicznie lub problemowo.
Aspekt społeczno-gospodarczy = struktura społeczna, stany/klasy, położenie chłopów i mieszczan, rolnictwo, handel, rzemiosło/przemysł, miasta, demografia, skarbowość, reformy agrarne — z konkretnymi przykładami i datami.
Aspekt kulturowo-religijny = religia, Kościół/wyznania, oświata, nauka, literatura, sztuka, architektura, ideologie — z nazwiskami twórców i dziełami.
Aspekt polityczny = władcy/rządy, ustrój, wojny i traktaty, polityka zagraniczna — z datami.
Zwróć wyłącznie JSON: {"items": [{"title": "...", "text": "..."}]}""",
    "topics": """Układasz listę kluczowych zagadnień do matury z historii (poziom rozszerzony, podstawa programowa CKE) dla jednego działu.
Zagadnienie = konkretne panowanie, wydarzenie, proces, reforma, konflikt, dzieło lub postać, o którą egzaminator może zapytać (np. „Panowanie Karola Wielkiego i odnowienie cesarstwa”, „Unia w Krewie 1385”).
Nie powtarzaj tematów z listy już opisanych. Zwróć wyłącznie JSON: {"topics": ["...", "..."]}""",
    "topic": NOTE_RULES + """
Jedna notatka na każde podane zagadnienie. Pole topic przepisz dokładnie z polecenia.
Zwróć wyłącznie JSON: {"items": [{"topic": "...", "title": "...", "text": "..."}]}""",
    "timeline": """Układasz hasła osi czasu do matury z historii (pewne fakty szkolne, bez wymyślonych dat).
Każde hasło: rok jako liczba (p.n.e. ujemnie), data_text po polsku (np. „15 lipca 1410 r.”), krótki title, text 2–4 zdania (co, kto, gdzie, przyczyna albo skutek, z nazwami i datą), persons (lista osób).
Dział jest wiążący; obejmij różne aspekty: polityczny, społeczno-gospodarczy i kulturalno-religijny. Nie powtarzaj haseł z listy unikania (także pod innym tytułem).
Zwróć wyłącznie JSON: {"items": [{"year": 1410, "date_text": "15 lipca 1410 r.", "title": "...", "text": "...", "persons": ["..."]}]}""",
    "persons": """Układasz biogramy do matury z historii. Same pewne fakty.
Każda postać: name, years (np. „1467–1548” albo „ok. 100–44 p.n.e.”), role (krótko), text z 3–5 faktami i datami.
Dział jest wiążący. Nie powtarzaj osób z listy unikania. Uwzględnij też twórców kultury, duchownych, uczonych, reformatorów gospodarczych.
Zwróć wyłącznie JSON: {"items": [{"name": "...", "years": "...", "role": "...", "text": "..."}]}""",
    "terms": """Układasz pojęcia i nazwy stosowane w historiografii (jak „pacta conventa”, „konstytucja nihil novi”, „rekonkwista”, „pozytywizm”) dla wskazanego działu.
Każde: term, text = definicja + kontekst historyczny + daty. Bez daty odrzuć pojęcie. Nie powtarzaj pojęć z listy unikania.
Zwróć wyłącznie JSON: {"items": [{"term": "...", "text": "..."}]}""",
    "verify": """Jesteś recenzentem merytorycznym materiałów do matury z historii. Sprawdź każdą pozycję pod kątem błędów faktograficznych: złe daty, lata panowania, nazwiska, przypisanie wydarzeń/dzieł/aktów niewłaściwym osobom lub miejscom, zmyślone fakty.
Nie zgłaszaj stylu ani spraw interpretacyjnych. Zgłaszaj tylko błędy, których jesteś pewien.
Dla każdej pozycji: verdict "ok" (brak błędów), "fix" (błędy do poprawienia) albo "drop" (dużo błędów lub pozycja zmyślona).
Przy "fix" podaj fixes: [{"old": "DOKŁADNY fragment z tekstu (znak w znak)", "new": "poprawiony fragment"}]; gdy błędny jest rok liczbowy hasła, dodaj "year": poprawny_rok.
Zwróć wyłącznie JSON: {"results": [{"i": 0, "verdict": "ok|fix|drop", "fixes": [], "why": "krótko"}]}""",
}


def roman(sec):
    return sec.split(".")[0].strip()


class Names:
    def __init__(self):
        self.seen = set()
        for f in ("kompendium", "kompendium_extra", "timeline", "persons", "terms"):
            for r in read_jsonl(KB / f"{f}.jsonl"):
                self.add(r.get("title") or r.get("name") or r.get("term") or "")
        for f in ("notes", "timeline", "persons", "terms"):
            for r in read_jsonl(FILES[f]):
                self.add(r.get("title") or "")

    def add(self, name):
        key = norm_name(name)
        with lock:
            if not key or key in self.seen:
                return False
            self.seen.add(key)
            return True


def call(forge, kind, user, max_tokens, tag):
    data, _, _ = forge.call_json(STAGE, MODEL, SYS[kind], user, max_tokens, 0.012, tag)
    return data if isinstance(data, dict) else {}


def items_of(data, key="items"):
    items = data.get(key)
    if isinstance(items, dict):
        items = [items]
    return [x for x in items if isinstance(x, (dict, str))] if isinstance(items, list) else []


def clean_note(raw):
    title = " ".join(str(raw.get("title") or "").split())
    text = re.sub(r"[ \t]+", " ", str(raw.get("text") or "")).strip()
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    wc = polish_word_count(text)
    if len(title) < 3 or not has_date(text) or not (220 <= wc <= 420):
        return None
    return title, text, wc


def save(kind, row, names):
    if not names.add(row.get("title") or ""):
        return False
    append_jsonl(FILES[kind], row)
    return True


def done_jobs(kind):
    return Counter(r.get("job") for r in read_jsonl(FILES[kind]))


def section_titles(sec, files):
    out = []
    for path in files:
        for r in read_jsonl(path):
            if r.get("section") == sec:
                out.append(str(r.get("title") or r.get("name") or "")[:70])
    return out


# ---------- zadania ----------

def job_gap(forge, names, pairs, meta_by):
    lines = [f"Napisz {len(pairs)} notatki, po jednej na podtemat."]
    lines += [f"- dział: {s} | podtemat: {sub}" for s, sub in pairs]
    data = call(forge, "gap", "\n".join(lines), 7000, "gap")
    sub_map = {" ".join(sub.split()): s for s, sub in pairs}
    kept = 0
    for raw in items_of(data)[: len(pairs) + 1]:
        if not isinstance(raw, dict):
            continue
        sub = " ".join(str(raw.get("subtopic") or "").split())
        sec = sub_map.get(sub)
        c = clean_note(raw)
        if not sec or not c:
            continue
        m = meta_by[sec]
        row = {"section": sec, "subtopic": sub, "title": c[0], "text": c[1], "words": c[2], "kind": "gap",
               "epoch": m["epoch"], "scope": m["scope"], "job": f"gap|{sec}|{sub}"}
        kept += save("notes", row, names)
    return kept


def job_aspect(forge, names, meta, aspect, part):
    period = ""
    if part:
        period = (f"\nTo notatka {part} z 2: obejmij {'pierwszą (wcześniejszą)' if part == 1 else 'drugą (późniejszą)'} "
                  "połowę okresu działu. W tytule wskaż zakres chronologiczny.")
    user = (f"Dział: {meta['section']}\nEpoka: {meta['epoch']} | zakres: {meta['scope']}\nAspekt: {aspect}{period}\n"
            "Podtematy działu (punkt odniesienia, nie musisz omawiać wszystkich):\n" + "\n".join(f"- {s}" for s in meta["subtopics"]) +
            f"\nTytuł zacznij od: „{meta['section'].split('. ', 1)[-1]} — aspekt {aspect}”.")
    data = call(forge, "aspect", user, 5000, "aspect")
    for raw in items_of(data)[:1]:
        c = clean_note(raw) if isinstance(raw, dict) else None
        if not c:
            return 0
        row = {"section": meta["section"], "subtopic": f"{meta['section']} — synteza, aspekt {aspect}", "title": c[0],
               "text": c[1], "words": c[2], "kind": "aspect", "aspect": aspect, "epoch": meta["epoch"],
               "scope": meta["scope"], "job": f"aspect|{meta['section']}|{aspect}|{part}"}
        return int(save("notes", row, names))
    return 0


def job_topics(forge, names, meta):
    have = section_titles(meta["section"], [KB / "kompendium.jsonl", KB / "kompendium_extra.jsonl"])
    user = (f"Dział: {meta['section']}\nEpoka: {meta['epoch']} | zakres: {meta['scope']}\nPodtematy:\n" +
            "\n".join(f"- {s}" for s in meta["subtopics"]) + "\nJuż opisane (nie powtarzaj):\n" + "\n".join(have) +
            "\nPodaj 10 zagadnień: najważniejsze panowania, wydarzenia, reformy, procesy społeczno-gospodarcze i zjawiska kultury tego działu.")
    data = call(forge, "topics", user, 2500, "topics")
    topics = [" ".join(str(t).split()) for t in items_of(data, "topics") if isinstance(t, str)][:12]
    append_jsonl(FILES["topics"], {"section": meta["section"], "topics": topics, "job": f"topics|{meta['section']}"})
    return len(topics)


def job_topic(forge, names, meta, topics):
    user = (f"Dział: {meta['section']}\nEpoka: {meta['epoch']} | zakres: {meta['scope']}\nNapisz {len(topics)} notatki, po jednej na zagadnienie:\n" +
            "\n".join(f"- {t}" for t in topics))
    data = call(forge, "topic", user, 7000, "topic")
    want = {t: t for t in topics}
    kept = 0
    for i, raw in enumerate(items_of(data)[: len(topics) + 1]):
        if not isinstance(raw, dict):
            continue
        t = " ".join(str(raw.get("topic") or "").split())
        t = want.get(t) or (topics[i] if i < len(topics) else None)
        c = clean_note(raw)
        if not t or not c:
            continue
        row = {"section": meta["section"], "subtopic": t, "title": c[0], "text": c[1], "words": c[2], "kind": "topic",
               "epoch": meta["epoch"], "scope": meta["scope"], "job": f"topic|{meta['section']}|{t}"}
        kept += save("notes", row, names)
    return kept


def job_short(forge, names, kind, meta, n):
    if kind == "terms":
        avoid = [r["term"][:60] for r in read_jsonl(KB / "terms.jsonl") if r.get("epoch") == meta["epoch"]]
        avoid += [r["title"][:60] for r in read_jsonl(FILES["terms"]) if r.get("epoch") == meta["epoch"]]
    else:
        src = {"timeline": [KB / "timeline.jsonl", FILES["timeline"]], "persons": [KB / "persons.jsonl", FILES["persons"]]}[kind]
        avoid = section_titles(meta["section"], src)
    user = (f"Dział: {meta['section']}\nEpoka: {meta['epoch']}\nZakres: {meta['scope']}\nLiczba haseł: {n}.\n"
            "Podtematy działu:\n" + "\n".join(f"- {s}" for s in meta["subtopics"]) +
            "\nUnikaj (już są w bazie):\n" + "\n".join(avoid[-150:]))
    data = call(forge, kind, user, 4500, kind)
    kept = 0
    for raw in items_of(data)[: n + 2]:
        if not isinstance(raw, dict):
            continue
        row = {"timeline": valid_timeline, "persons": valid_person, "terms": valid_term}[kind](raw, meta)
        if not row:
            continue
        if kind == "terms":
            row["section"] = meta["section"]
        row["job"] = f"{kind}|{meta['section']}"
        kept += save(kind, row, names)
    return kept


def job_topics2(forge, names, meta):
    have = section_titles(meta["section"], [KB / "kompendium.jsonl", KB / "kompendium_extra.jsonl", FILES["notes"]])
    user = (f"Dział: {meta['section']}\nEpoka: {meta['epoch']} | zakres: {meta['scope']}\nPodtematy:\n" +
            "\n".join(f"- {s}" for s in meta["subtopics"]) + "\nJuż opisane (nie powtarzaj, także pod inną nazwą):\n" + "\n".join(have) +
            "\nPodaj 12 kolejnych zagadnień: panowania i rządy (każdy ważny władca/przywódca działu), wojny i traktaty, akty prawne, "
            "przemiany gospodarcze i społeczne, wyznania i Kościół, oświata, nauka, sztuka i literatura, ważne postaci.")
    data = call(forge, "topics", user, 2500, "topics2")
    topics = [" ".join(str(t).split()) for t in items_of(data, "topics") if isinstance(t, str)][:14]
    append_jsonl(FILES["topics2"], {"section": meta["section"], "topics": topics, "job": f"topics2|{meta['section']}"})
    return len(topics)


ARG_KINDS = {
    "przyczyny": "przyczyny, przebieg przemian i skutki (krótko- i długofalowe) najważniejszych procesów działu; "
                 "zestaw argumentów za i przeciw typowym tezom oceniającym",
    "porownanie": "ciągłość i zmiana oraz porównania (np. Polska a Europa, różne państwa lub okresy działu), "
                  "z konkretnymi przykładami do wykorzystania w wypracowaniu",
}


def job_argument(forge, names, meta, arg):
    user = (f"Dział: {meta['section']}\nEpoka: {meta['epoch']} | zakres: {meta['scope']}\nTemat notatki: {ARG_KINDS[arg]}.\n"
            "Podtematy działu:\n" + "\n".join(f"- {s}" for s in meta["subtopics"]) +
            f"\nTytuł zacznij od: „{meta['section'].split('. ', 1)[-1]} — {'przyczyny i skutki' if arg == 'przyczyny' else 'ciągłość, zmiana, porównania'}”.")
    data = call(forge, "aspect", user, 5000, "argument")
    for raw in items_of(data)[:1]:
        c = clean_note(raw) if isinstance(raw, dict) else None
        if not c:
            return 0
        row = {"section": meta["section"], "subtopic": f"{meta['section']} — argumenty do wypracowania: {arg}", "title": c[0],
               "text": c[1], "words": c[2], "kind": "argument", "aspect": arg, "epoch": meta["epoch"],
               "scope": meta["scope"], "job": f"argument|{meta['section']}|{arg}"}
        return int(save("notes", row, names))
    return 0


def timeline_target(meta, v3=False):
    if meta["epoch"] == "starożytność":
        return 250 if v3 else 100
    if meta["epoch"] == "średniowiecze":
        if meta["scope"] == "powszechna":
            return 140 if v3 else 60
        return 90 if v3 else 40
    if meta["scope"] == "powszechna":
        return 70 if v3 else 30
    return 25 if v3 else 0


def job_topics3(forge, names, meta):
    have = section_titles(meta["section"], [KB / "kompendium.jsonl", KB / "kompendium_extra.jsonl", FILES["notes"]])
    user = (f"Dział: {meta['section']}\nEpoka: {meta['epoch']} | zakres: {meta['scope']}\nPodtematy:\n" +
            "\n".join(f"- {s}" for s in meta["subtopics"]) + "\nJuż opisane (nie powtarzaj, także pod inną nazwą):\n" + "\n".join(have) +
            "\nPodaj 8 kolejnych zagadnień WYŁĄCZNIE społeczno-gospodarczych i kulturowo-religijnych: struktura i położenie grup społecznych, "
            "rolnictwo, handel, miasta, przemysł, skarb i pieniądz, demografia, życie codzienne; religia i Kościół, oświata, nauka, literatura, sztuka.")
    data = call(forge, "topics", user, 2500, "topics3")
    topics = [" ".join(str(t).split()) for t in items_of(data, "topics") if isinstance(t, str)][:10]
    append_jsonl(FILES["topics3"], {"section": meta["section"], "topics": topics, "job": f"topics3|{meta['section']}"})
    return len(topics)


def gen4(workers):
    metas = load_metas()
    meta_by = {m["section"]: m for m in metas}
    forge, names = Forge(), Names()
    done = {r["section"] for r in read_jsonl(FILES["topics3"])}
    run_pool([(job_topics3, forge, names, m) for m in metas if m["section"] not in done], workers)
    notes_done = done_jobs("notes")
    jobs = []
    for r in read_jsonl(FILES["topics3"]):
        m = meta_by[r["section"]]
        todo = [t for t in r["topics"] if not notes_done[f"topic|{m['section']}|{t}"]]
        jobs += [(job_topic, forge, names, m, todo[i:i + 2]) for i in range(0, len(todo), 2)]
    print(f"v3 gen4: {len(jobs)} zadań", flush=True)
    if not stop.is_set():
        run_pool(jobs, workers)
    print("E7 gen4 koniec, koszt E7 $%.3f" % spent_by_stage()[0]["E7"], flush=True)


def gen3(workers):
    metas = load_metas()
    meta_by = {m["section"]: m for m in metas}
    forge, names = Forge(), Names()
    have = {(r["section"], r["subtopic"]) for f in ("kompendium", "kompendium_extra") for r in read_jsonl(KB / f"{f}.jsonl")}
    have |= {(r["section"], r["subtopic"]) for r in read_jsonl(FILES["notes"]) if r.get("kind") == "gap"}
    gaps = [(m["section"], s) for m in metas for s in m["subtopics"] if (m["section"], s) not in have]
    notes_done = done_jobs("notes")
    jobs = [(job_gap, forge, names, [g], meta_by) for g in gaps]
    for m in metas:
        for a in ASPECTS:
            for part in (1, 2):
                if not notes_done[f"aspect|{m['section']}|{a}|{part}"]:
                    jobs.append((job_aspect, forge, names, m, a, part))
        for arg in ARG_KINDS:
            if not notes_done[f"argument|{m['section']}|{arg}"]:
                jobs.append((job_argument, forge, names, m, arg))
    t2_done = {r["section"] for r in read_jsonl(FILES["topics2"])}
    jobs += [(job_topics2, forge, names, m) for m in metas if m["section"] not in t2_done]
    print(f"v3 faza A: {len(jobs)} zadań (luki {len(gaps)})", flush=True)
    run_pool(jobs, workers)

    notes_done = done_jobs("notes")
    jobs = []
    for r in read_jsonl(FILES["topics2"]):
        m = meta_by[r["section"]]
        todo = [t for t in r["topics"] if not notes_done[f"topic|{m['section']}|{t}"]]
        jobs += [(job_topic, forge, names, m, todo[i:i + 2]) for i in range(0, len(todo), 2)]
    tl_have = Counter(r["section"] for r in read_jsonl(FILES["timeline"]))
    per_have = Counter(r["section"] for r in read_jsonl(FILES["persons"]))
    te_have = Counter(r["section"] for r in read_jsonl(FILES["terms"]))
    for m in metas:
        need = timeline_target(m, True) - tl_have[m["section"]]
        jobs += [(job_short, forge, names, "timeline", m, 15) for _ in range(max(0, (need + 14) // 15))]
        jobs += [(job_short, forge, names, "persons", m, 10) for _ in range(max(0, (26 - per_have[m["section"]] + 9) // 10))]
        jobs += [(job_short, forge, names, "terms", m, 10) for _ in range(max(0, (26 - te_have[m["section"]] + 9) // 10))]
    print(f"v3 faza B: {len(jobs)} zadań", flush=True)
    if not stop.is_set():
        run_pool(jobs, workers)
    print("E7 gen3 koniec, koszt E7 $%.3f" % spent_by_stage()[0]["E7"], flush=True)


def run_pool(jobs, workers):
    total = 0
    with ThreadPoolExecutor(workers) as ex:
        futs = {ex.submit(guard, fn, *a): (fn.__name__, a[-1] if a else None) for fn, *a in jobs}
        for f in as_completed(futs):
            total += f.result() or 0
    return total


def guard(fn, *a):
    if stop.is_set():
        return 0
    try:
        k = fn(*a)
        print(f"{fn.__name__} +{k}", flush=True)
        return k
    except BudgetExceeded:
        stop.set()
        print("E7 budżet wyczerpany", flush=True)
    except Exception as exc:
        print(f"{fn.__name__} błąd {safe_err(exc)}", flush=True)
    return 0


def gen(workers):
    OUT.mkdir(parents=True, exist_ok=True)
    metas = load_metas()
    meta_by = {m["section"]: m for m in metas}
    forge, names = Forge(), Names()
    have = {(r["section"], r["subtopic"]) for f in ("kompendium", "kompendium_extra") for r in read_jsonl(KB / f"{f}.jsonl")}
    have |= {(r["section"], r["subtopic"]) for r in read_jsonl(FILES["notes"]) if r.get("kind") == "gap"}
    gaps = [(m["section"], s) for m in metas for s in m["subtopics"] if (m["section"], s) not in have]
    notes_done = done_jobs("notes")
    jobs = [(job_gap, forge, names, gaps[i:i + 2], meta_by) for i in range(0, len(gaps), 2)]
    for m in metas:
        for a in ASPECTS:
            for part in ((1, 2) if roman(m["section"]) in BROAD else (0,)):
                if not notes_done[f"aspect|{m['section']}|{a}|{part}"]:
                    jobs.append((job_aspect, forge, names, m, a, part))
    topics_done = {r["section"] for r in read_jsonl(FILES["topics"])}
    jobs += [(job_topics, forge, names, m) for m in metas if m["section"] not in topics_done]
    print(f"faza A: {len(jobs)} zadań (luki {len(gaps)})", flush=True)
    run_pool(jobs, workers)

    jobs = []
    for r in read_jsonl(FILES["topics"]):
        m = meta_by[r["section"]]
        todo = [t for t in r["topics"] if not notes_done[f"topic|{m['section']}|{t}"]]
        jobs += [(job_topic, forge, names, m, todo[i:i + 2]) for i in range(0, len(todo), 2)]
    tl_have = Counter(r["section"] for r in read_jsonl(FILES["timeline"]))
    for m in metas:
        need = timeline_target(m) - tl_have[m["section"]]
        jobs += [(job_short, forge, names, "timeline", m, 15) for _ in range(max(0, (need + 14) // 15))]
    per_have = Counter(r["section"] for r in read_jsonl(FILES["persons"]))
    te_have = Counter(r["section"] for r in read_jsonl(FILES["terms"]))
    jobs += [(job_short, forge, names, "persons", m, 10) for m in metas if per_have[m["section"]] < 6]
    jobs += [(job_short, forge, names, "terms", m, 10) for m in metas if te_have[m["section"]] < 6]
    print(f"faza B: {len(jobs)} zadań", flush=True)
    if not stop.is_set():
        run_pool(jobs, workers)
    print("E7 gen koniec, koszt E7 $%.3f" % spent_by_stage()[0]["E7"], flush=True)


# ---------- weryfikacja ----------

def show(kind, r):
    if kind == "notes":
        return f"[{r['title']}]\n{r['text']}"
    if kind == "timeline":
        return f"rok: {r['year']} | data: {r['date_text']} | {r['title']}: {r['text']}"
    if kind == "persons":
        return f"{r['name']} ({r['years']}), {r['role']}: {r['text']}"
    return f"{r['title']}: {r['text']}"


def apply_fixes(kind, r, res):
    verdict = str(res.get("verdict") or "ok").lower()
    if verdict == "drop":
        return None, "drop"
    if verdict != "fix":
        return r, "ok"
    r = dict(r)
    fields = [f for f in ("title", "text", "date_text", "years", "role", "name") if f in r]
    applied = 0
    fixes = [f for f in (res.get("fixes") or []) if isinstance(f, dict)]
    for fx in fixes:
        old, new = str(fx.get("old") or ""), str(fx.get("new") or "")
        if not old or old == new:
            continue
        for f in fields:
            if old in str(r[f]):
                r[f] = str(r[f]).replace(old, new)
                applied += 1
                break
    if kind == "timeline" and res.get("year") is not None:
        try:
            r["year"] = int(res["year"])
            applied += 1
        except (TypeError, ValueError):
            pass
    if not applied:
        return None, "fix-unapplied"
    if kind == "persons":
        r["title"] = r["name"]
    if kind == "notes":
        r["words"] = polish_word_count(r["text"])
    r["verified"] = "fixed"
    return r, "fixed"


def verify_batch(forge, kind, rows, out_path, log_path):
    user = "Pozycje do sprawdzenia:\n\n" + "\n\n".join(f"### {i}\n{show(kind, r)}" for i, r in enumerate(rows))
    data = call(forge, "verify", user, 6000, f"verify-{kind}")
    res = {}
    for x in items_of(data, "results"):
        if isinstance(x, dict):
            try:
                res[int(x.get("i"))] = x
            except (TypeError, ValueError):
                pass
    stats = Counter()
    for i, r in enumerate(rows):
        x = res.get(i)
        if x is None:
            row, st = dict(r, verified="unchecked"), "unchecked"
        else:
            row, st = apply_fixes(kind, r, x)
            if row is not None and st == "ok":
                row = dict(row, verified="ok")
        stats[st] += 1
        append_jsonl(log_path, {"kind": kind, "title": r.get("title"), "status": st, "why": (x or {}).get("why"),
                                "fixes": (x or {}).get("fixes")})
        if row is not None:
            append_jsonl(out_path, row)
    return sum(stats.values())


def verify(workers):
    forge = Forge()
    log_path = OUT / "verify_log.jsonl"
    jobs = []
    for kind, bs in (("notes", 3), ("timeline", 15), ("persons", 12), ("terms", 15)):
        out_path = OUT / f"{kind}.verified.jsonl"
        seen = {r["title"] for r in read_jsonl(log_path) if r.get("kind") == kind}
        rows = [r for r in read_jsonl(FILES[kind]) if r["title"] not in seen]
        jobs += [(verify_batch, forge, kind, rows[i:i + bs], out_path, log_path) for i in range(0, len(rows), bs)]
    print(f"weryfikacja: {len(jobs)} partii", flush=True)
    run_pool(jobs, workers)
    print("E7 verify koniec, koszt E7 $%.3f" % spent_by_stage()[0]["E7"], flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["gen", "gen3", "gen4", "verify"])
    p.add_argument("--workers", type=int, default=32)
    a = p.parse_args()
    t0 = time.time()
    {"gen": gen, "gen3": gen3, "gen4": gen4, "verify": verify}[a.cmd](a.workers)
    print(f"czas {(time.time() - t0) / 60:.1f} min", flush=True)
