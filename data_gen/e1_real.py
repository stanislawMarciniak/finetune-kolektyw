"""E1: prawdziwe zadania CKE (informator + formuła 2015) → data/sft/real_cke.jsonl.

Luna. Limit etapu 3 USD. Pomija arkusze formuły 2023 (MHIP-R0-100-23/24/25/26) i egzamin próbny.
"""

import argparse
import re
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_gen.common import (
    BudgetExceeded,
    Forge,
    ROOT,
    SFT,
    append_jsonl,
    canonical_format,
    chunk_pages,
    collapse_alternatives,
    ensure_dirs,
    has_alternative_marker,
    load_ids,
    load_pages,
    mentions_image,
    normalize_closed,
    pages_block,
    read_jsonl,
    safe_err,
    valid_model_answer,
)
from data_gen.sections import SECTIONS, canon_section

OUT = SFT / "real_cke.jsonl"
TOPICS = SFT / "real_essay_topics.jsonl"
DONE = ROOT / "data_gen" / "state" / "e1_chunks.jsonl"
EXTRACTED = ROOT / "data" / "cke" / "extracted"

SYSTEM = """Jesteś redaktorem zbioru zadań maturalnych z historii (CKE, poziom rozszerzony).
Z podanego tekstu OCR arkusza (i zasad oceniania, jeśli są) wyciągasz zadania do JSON.
Zasady:
- Nie wymyślaj treści. Bierz polecenie, źródło, punktację, zasady i rozwiązanie wyłącznie z podanego tekstu.
- Pomiń zadanie, jeśli polecenie albo rozwiązanie jest ucięte (zaczyna się przed porcją albo urywa się na jej końcu).
- model_answer to JEDNA najlepsza wersja z rozwiązania CKE. Usuń warianty ze znakiem „/” i „albo” — zostaw jedną, pełną formę. Nie zostawiaj „Przykładowe uzasadnienie:”.
- Jeśli polecenie ma etykiety (Rozstrzygnięcie, Uzasadnienie, Podobieństwo, Różnica, Nazwa…), klucz używa tych samych etykiet.
- needs_image=true, gdy bez mapy, ilustracji, fotografii, ryciny albo planu nie da się rozwiązać zadania. W image_pages podaj numery stron z tym materiałem.
- Wypracowania (wypowiedź argumentacyjna, „Zajmij stanowisko”) NIE trafiają do items. Każdy temat osobno do essay_topics.
- type to dokładnie: closed_tf, closed_choice, closed_match, closed_multi albo open.
- closed_tf: model_answer jak „1: F\\n2: P” (tyle linii, ile stwierdzeń).
- closed_choice: jedna litera, np. „C”.
- closed_match: linie „A: 3” albo „A: nazwa”.
- closed_multi: linie „1: B\\n2: C”.
- section_roman to numer działu podstawy formuły 2023 (II–LX), nawet jeśli arkusz używa starej numeracji. Mapowanie: cywilizacje Wschodu=II, Grecja=III, Rzym=IV, Bizancjum/islam=V, wczesne średniowiecze=VI, krucjaty=VII, gospodarka średniowiecza=VIII, Piastowie do rozbicia=IX, rozbicie=X, późne średniowiecze Europy=XI, Polska XIV–XV=XII, kultura średniowiecza=XIII, odkrycia=XIV, renesans=XV, reformacja=XVI, Europa XVI–XVII=XVII, ostatni Jagiellonowie=XVIII, unia lubelska=XIX, wolne elekcje=XX, renesans w Polsce=XXI, polityka RP szlacheckiej=XXII, ustrój RP=XXIII, oświecenie europejskie=XXIV, rewolucje XVIII=XXV, Polska saska i Sejm Wielki=XXVI, rozbiory i Kościuszko=XXVII, kultura oświecenia=XXVIII, Napoleon=XXIX, po Wiedniu=XXX, ziemie polskie 1815–1848=XXXI, powstanie styczniowe=XXXII, świat II poł. XIX=XXXIII, industrializacja i ideologie=XXXIV, zabory II poł. XIX=XXXV, kultura polska XIX=XXXVI, I wojna=XXXVII, sprawa polska 1914–1918=XXXVIII, ład wersalski=XXXIX, totalitaryzmy=XL, odrodzenie Polski=XLI, polityka II RP=XLII, społeczeństwo i gospodarka II RP=XLIII, kultura II RP=XLIV, droga do II wojny=XLV, 1939=XLVI, II wojna=XLVII, okupacja=XLVIII, Zagłada=XLIX, władze RP=L, zimna wojna=LI, dekolonizacja=LII, przemiany cywilizacyjne=LIII, przełom tysiącleci=LIV, Polska 1944–1948=LV, stalinizm=LVI, 1957–1981=LVII, 1981–1989=LVIII, III RP=LIX, Polska po 1989=LX.
Zwróć wyłącznie JSON: {"items": [...], "essay_topics": [...]}."""


def user_prompt(source_id, pages, zasady):
    section_list = "\n".join(SECTIONS)
    zasady_block = ""
    if zasady:
        zasady_block = "\n\n[ZASADY OCENIANIA — CAŁOŚĆ]\n" + zasady
    return (
        f"Źródło: {source_id}\n"
        "Wyciągnij tylko zadania, których pełne polecenie i pełne rozwiązanie są w tej porcji stron "
        "(rozwiązanie może być w zasadach oceniania, dopasuj po numerze zadania).\n"
        "Pola item: task_id, section_roman, subtopic, type, max_points, question, source_text, "
        "model_answer, rubric, needs_image, image_pages.\n"
        "question = samo polecenie (ze stwierdzeniami albo opcjami A–D). source_text = źródła, bez polecenia. "
        "Tabele zapisz jako tekst. rubric = zasady punktowania tego zadania.\n"
        "essay_topics: {task_id, section_roman, topic} — sama treść tematu wypracowania.\n"
        f"Działy (section_roman = człon przed kropką):\n{section_list}\n\n"
        f"[STRONY]\n{pages_block(pages)}"
        + zasady_block
    )


# Pary z kluczem. Świadomie bez MHIP-R0-100-* (formuła 2023, zbiór testowy) i bez egzaminu próbnego.
EXAMS = [
    ("MHI-R1_1P-152", "f2015/MHI-R1_1P-152", "f2015/MHI-R1-N"),
    ("MHI-R1_1P-182", "f2015/MHI-R1_1P-182", "f2015/MHI-R1_1P-182_zasady_oceniania"),
    ("MHI-R1_1P-192", "f2015/MHI-R1_1P-192", "f2015/MHI-R1_1P-192_model"),
    ("MHI-R1_1P-202", "f2015/MHI-R1_1P-202", "f2015/MHI-PR-202_zasady"),
    ("EHIP-R0-100-2305", "f2015/EHIP-R0-100-2305", "f2015/EHIP-R0-100-2305-zasady"),
    ("stara-MHI-R1-182", "stara/MHI-R1_1P-182", "stara/MHI-R1_1P-182_zasady_oceniania"),
    ("stara-MHI-R1-192", "stara/MHI-R1_1P-192", "stara/MHI-R1_1P-192_model"),
]

ESSAY_ONLY = [
    ("MHI-R1_1P-162", "f2015/MHI-R1_1P-162"),
    ("MHI-R1_1P-172", "f2015/MHI-R1_1P-172"),
    ("EHIP-R0-100-2105", "f2015/EHIP-R0-100-2105"),
    ("EHIP-R0-100-2205", "f2015/EHIP-R0-100-2205"),
]


def build_jobs(pilot, include_stara):
    jobs = []
    info = load_pages(EXTRACTED / "f2023/Informator_EM2025_historia_2025_2026/pages.json")
    info = [p for p in info if 14 <= p["page"] <= 120]
    for sl in chunk_pages(info, 5, 3):
        jobs.append({
            "chunk_id": f"informator:{sl[0]['page']}-{sl[-1]['page']}",
            "source_id": "Informator_EM2025_historia_2025_2026",
            "pages": sl,
            "zasady": "",
            "kind": "items",
        })
    exams = [e for e in EXAMS if include_stara or not e[0].startswith("stara")]
    for source_id, ark, zas in exams:
        pages = load_pages(EXTRACTED / ark / "pages.json")
        zasady = pages_block(load_pages(EXTRACTED / zas / "pages.json"))
        # okładki pomijamy: pierwsza strona zwykle bez zadań
        body = [p for p in pages if p["page"] >= 2]
        for sl in chunk_pages(body, 4, 3):
            jobs.append({
                "chunk_id": f"{source_id}:{sl[0]['page']}-{sl[-1]['page']}",
                "source_id": source_id,
                "pages": sl,
                "zasady": zasady,
                "kind": "items",
            })
    for source_id, ark in ESSAY_ONLY:
        pages = load_pages(EXTRACTED / ark / "pages.json")
        tail = pages[-4:]
        jobs.append({
            "chunk_id": f"{source_id}:essay:{tail[0]['page']}-{tail[-1]['page']}",
            "source_id": source_id,
            "pages": tail,
            "zasady": "",
            "kind": "essay_only",
        })
    if pilot:
        wanted = []
        for job in jobs:
            cid = job["chunk_id"]
            if cid in ("informator:14-18", "informator:41-45") or cid.startswith("MHI-R1_1P-182:3-"):
                wanted.append(job)
            elif cid.startswith("MHI-R1_1P-182:") and any(p["page"] == 3 for p in job["pages"]) and len(wanted) < 4:
                wanted.append(job)
        # unikalne i maks. 4
        seen = set()
        pilot_jobs = []
        for job in wanted:
            if job["chunk_id"] in seen:
                continue
            seen.add(job["chunk_id"])
            pilot_jobs.append(job)
            if len(pilot_jobs) >= 4:
                break
        return pilot_jobs
    return jobs


def norm_task_id(raw):
    text = str(raw or "").strip()
    text = re.sub(r"(?i)^zadanie\s+", "", text)
    m = re.search(r"\d+(?:\.\d+)?", text)
    return m.group(0) if m else text


def record_from_item(source_id, item):
    typ = str(item.get("type") or "").strip()
    if typ not in ("closed_tf", "closed_choice", "closed_match", "closed_multi", "open"):
        return None
    task_id = norm_task_id(item.get("task_id"))
    if not task_id:
        return None
    question = re.sub(r"[ \t]+", " ", str(item.get("question") or "")).strip()
    question = re.sub(r"\n{3,}", "\n\n", question)
    if len(question) < 15:
        return None
    answer = collapse_alternatives(str(item.get("model_answer") or ""))
    if typ in ("closed_tf", "closed_choice", "closed_match", "closed_multi"):
        answer = normalize_closed(typ, answer)
    if not valid_model_answer(typ, answer):
        return None
    if typ == "open" and has_alternative_marker(answer):
        return None
    section = canon_section(str(item.get("section_roman") or ""))
    if not section:
        section = canon_section(str(item.get("section") or ""))
    needs = bool(item.get("needs_image")) or (
        mentions_image(question) and polish_len(str(item.get("source_text") or "")) < 25
    )
    pages = item.get("image_pages") or []
    try:
        max_points = int(item.get("max_points") or 1)
    except (TypeError, ValueError):
        max_points = 1
    max_points = min(3, max(1, max_points))
    group = task_id.split(".", 1)[0]
    return {
        "id": f"{source_id}:{task_id}",
        "origin": "real",
        "source_doc": source_id,
        "section": section,
        "subtopic": " ".join(str(item.get("subtopic") or "").split())[:180],
        "type": typ,
        "group": group,
        "max_points": max_points,
        "question": question,
        "source_text": str(item.get("source_text") or "").strip(),
        "answer_format": canonical_format(typ, answer),
        "model_answer": answer,
        "rubric": str(item.get("rubric") or "").strip(),
        "needs_image": needs,
        "image_refs": [str(p) for p in pages],
        "verified": True,
        "verify_note": "klucz z zasad CKE; zadanie wymaga obrazu" if needs else "klucz z zasad CKE",
    }


def polish_len(text):
    return len(re.findall(r"\w+", text, flags=re.UNICODE))


def save_topic(source_id, topic, seen_topics, guard):
    text = " ".join(str(topic.get("topic") or "").split())
    if len(text) < 40:
        return
    task_id = norm_task_id(topic.get("task_id") or "essay")
    key = f"{source_id}|{text}"
    with guard:
        if key in seen_topics:
            return
        seen_topics.add(key)
        n = len(seen_topics)
    append_jsonl(TOPICS, {
        "id": f"{source_id}:{task_id}:{n}",
        "source_doc": source_id,
        "section": canon_section(str(topic.get("section_roman") or "")),
        "topic": text,
    })


def process_job(forge, job, seen_items, seen_topics, guard):
    if job["chunk_id"] in load_ids(DONE, "chunk_id"):
        print("skip", job["chunk_id"], flush=True)
        return 0
    estimate = 0.02 if job["zasady"] else 0.012
    data, _, _ = forge.call_json(
        "E1", "gpt-6-luna", SYSTEM,
        user_prompt(job["source_id"], job["pages"], job["zasady"] if job["kind"] == "items" else ""),
        4500, estimate, job["chunk_id"],
    )
    n = 0
    if job["kind"] == "items":
        for item in data.get("items") or []:
            rec = record_from_item(job["source_id"], item)
            if not rec:
                continue
            with guard:
                if rec["id"] in seen_items:
                    continue
                seen_items.add(rec["id"])
            append_jsonl(OUT, rec)
            n += 1
    for topic in data.get("essay_topics") or []:
        save_topic(job["source_id"], topic, seen_topics, guard)
    append_jsonl(DONE, {"chunk_id": job["chunk_id"], "n": n})
    print(f"chunk {job['chunk_id']} items {n}", flush=True)
    return n


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--no-stara", action="store_true")
    args = parser.parse_args()
    ensure_dirs()
    # import lokalny, żeby wątki dostały gotowy klient
    from concurrent.futures import ThreadPoolExecutor, as_completed

    jobs = build_jobs(args.pilot, include_stara=not args.no_stara)
    print(f"E1 jobs {len(jobs)} pilot={args.pilot}", flush=True)
    forge = Forge()
    seen_items = load_ids(OUT)
    seen_topics = {f"{row.get('source_doc')}|{row.get('topic')}" for row in read_jsonl(TOPICS)}
    guard = threading.Lock()
    done = load_ids(DONE, "chunk_id")
    pending = [j for j in jobs if j["chunk_id"] not in done]
    print(f"pending {len(pending)} already {len(done)}", flush=True)

    def work(job):
        try:
            return process_job(forge, job, seen_items, seen_topics, guard)
        except BudgetExceeded as exc:
            print("budget stop", exc, flush=True)
            return None
        except Exception as exc:
            print("fail", job["chunk_id"], safe_err(exc), flush=True)
            return 0

    stopped = False
    with ThreadPoolExecutor(max(1, args.workers)) as ex:
        futs = [ex.submit(work, job) for job in pending]
        for fut in as_completed(futs):
            if fut.result() is None:
                stopped = True
    print("E1 done" if not stopped else "E1 stopped on budget", "records", len(load_ids(OUT)), flush=True)


if __name__ == "__main__":
    main()
