"""E3: syntetyczne wiązki (sol) i weryfikacja (luna). Limit 14 USD.

Wynik: data/sft/synthetic_items.jsonl (tylko zweryfikowane).
Odrzucone: data/sft/synthetic_rejected.jsonl.
"""

import argparse
import json
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_gen.common import (
    BudgetExceeded,
    CLOSED_TYPES,
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
    load_ids,
    mentions_image,
    normalize_closed,
    polish_word_count,
    read_jsonl,
    safe_err,
    valid_model_answer,
    word_ngrams,
)
from data_gen.sections import canon_section

OUT = SFT / "synthetic_items.jsonl"
REJECTED = SFT / "synthetic_rejected.jsonl"
DONE = ROOT / "data_gen" / "state" / "e3_bundles.jsonl"
COUNTS_PATH = ROOT / "data_gen" / "state" / "e3_counts.json"
TAXONOMY = ROOT / "data_gen" / "taxonomy.json"
E2_DONE = ROOT / "data_gen" / "state" / "e2_done"
EVAL_DIR = ROOT / "eval" / "data"

# 100 pozycji ≈ rozkład CKE bez esejów (ok. 24% zamkniętych).
SEQUENCE = (
    ["closed_tf"] * 10
    + ["closed_choice"] * 7
    + ["closed_match"] * 4
    + ["closed_multi"] * 3
    + ["rozstrzygnij"] * 25
    + ["podaj"] * 25
    + ["wyjasnij"] * 15
    + ["porownaj"] * 11
)
KIND_RULES = {
    "closed_tf": "type=closed_tf. Polecenie zaczyna się od „Oceń prawdziwość poniższych stwierdzeń. Zaznacz P, jeśli stwierdzenie jest prawdziwe, albo F – jeśli jest fałszywe.” Dalej dokładnie trzy numerowane stwierdzenia. model_answer to trzy linie w postaci „1: P” lub „1: F”; ma być wśród nich i P, i F.",
    "closed_choice": "type=closed_choice. Polecenie: „Dokończ zdanie. Zaznacz właściwą odpowiedź spośród podanych.” Jedno zdanie i opcje A–D, tylko jedna poprawna. model_answer to sama litera.",
    "closed_match": "type=closed_match. Polecenie zaczyna się od „Przyporządkuj”. Dwa opisy oznaczone A i B oraz trzy numerowane możliwości. model_answer to dwie linie, np. „A: 3\\nB: 1”.",
    "closed_multi": "type=closed_multi. Dwa niezależne zdania do dokończenia, każde z opcjami A–D. model_answer to dwie linie, np. „1: B\\n2: C”.",
    "rozstrzygnij": "type=open, open_kind=rozstrzygnij. Polecenie zaczyna się od „Rozstrzygnij” i zawiera etykiety w osobnych liniach: „Rozstrzygnięcie:” oraz „Uzasadnienie:”. Klucz używa tych etykiet. Nie ustawiaj zawsze rozstrzygnięcia „Nie” — część odpowiedzi ma być twierdząca.",
    "podaj": "type=open, open_kind=podaj. Polecenie zaczyna się od „Podaj” albo „Wymień”. Klucz krótki i jednoznaczny.",
    "wyjasnij": "type=open, open_kind=wyjasnij. Polecenie zaczyna się od „Wyjaśnij”. Klucz to jedno do trzech zdań (przyczyna, skutek albo mechanizm).",
    "porownaj": "type=open, open_kind=porownaj. Polecenie zaczyna się od „Porównaj” i zawiera etykiety „Podobieństwo:” oraz „Różnica:”. Klucz używa tych etykiet.",
}

SYS_GEN = """Jesteś autorem zadań matury rozszerzonej z historii (styl CKE, formuła 2023).
Dostajesz notatkę kompendium. Ułóż wiązkę: jedno źródło i dokładnie 2 zadania różnych typów.
Źródło (60–200 słów) to: fragment opracowania historycznego napisany na podstawie notatki, pewny cytat dokumentu epoki albo krótka tabela. Czasem źródło może być puste — tylko gdy o to poproszono.
Fakty wyłącznie z notatki. Nie dopisuj dat, osób ani liczb, których notatka nie zawiera.
Zadania mają być rozwiązywalne ze źródła i wiedzy z notatki. Styl poleceń: „Rozstrzygnij…”, „Podaj…”, „Wymień…”, „Wyjaśnij…”, „Porównaj…”, „Oceń prawdziwość…”, „Dokończ zdanie. Zaznacz właściwą odpowiedź spośród podanych.”, „Przyporządkuj…”.
Gdy polecenie ma etykiety (Rozstrzygnięcie:, Uzasadnienie:, Podobieństwo:, Różnica:), klucz używa tych samych etykiet.
Klucz jest jeden, jednoznaczny, bez „albo”, bez „/” i bez wariantów.
Nie odwołuj się do mapy, ilustracji, fotografii, ryciny, obrazu ani planu, których nie ma w tekście.
Rubryka jak w CKE, zwięźle: „1 pkt – za …\\n0 pkt – za odpowiedź niepełną lub błędną albo za brak odpowiedzi.”
type: closed_tf | closed_choice | closed_match | closed_multi | open.
Dla open podaj open_kind: rozstrzygnij | podaj | wyjasnij | porownaj.
closed_tf: 3 stwierdzenia, model_answer „1: F\\n2: P\\n3: P”.
closed_choice: opcje A–D, model_answer jedna litera.
closed_match: dwa opisy A i B oraz trzy numerowane możliwości, model_answer „A: 2\\nB: 3”.
closed_multi: dwa niezależne wybory, model_answer „1: B\\n2: C”.
max_points: 1, rzadko 2 (gdy polecenie wymaga dwóch elementów).
Zwróć wyłącznie JSON:
{"source_text": "...", "items": [{"type": "...", "open_kind": "", "question": "...", "max_points": 1, "model_answer": "...", "rubric": "..."}]}"""

SYS_BLIND = """Rozwiązujesz jedno zadanie matury rozszerzonej z historii. Masz tylko źródło, polecenie i informację o formacie odpowiedzi.
Odpowiedz wyłącznie JSON: {"answer": "..."}.
Dla prawda/fałsz: linie „1: P” albo „1: F”. Dla wyboru: sama litera. Dla przyporządkowania: linie „A: 2”. Dla kilku wyborów: linie „1: B”.
Dla zadania otwartego: zwięźle, po polsku, z etykietami z polecenia. Jedna odpowiedź, bez „albo” i bez wariantów."""

SYS_JUDGE = """Porównujesz dwie odpowiedzi na zadanie matury z historii: klucz autorski i odpowiedź napisaną bez klucza.
Oceń, czy są merytorycznie zgodne (inne sformułowanie może być poprawne) oraz czy klucz jest faktograficznie poprawny i jednoznaczny.
agree=true, gdy obie są merytorycznie do przyjęcia i nie są sprzeczne.
key_ok=false tylko przy wyraźnym błędzie faktu w kluczu.
unambiguous=false, gdy klucz zawiera warianty albo nie spełnia polecenia.
fix_answer podaj tylko gdy klucz jest ewidentnie błędny; ma to być jedna poprawna odpowiedź. W przeciwnym razie null.
Zwróć wyłącznie JSON: {"agree": true, "key_ok": true, "unambiguous": true, "fix_answer": null, "note": "krótko po polsku"}"""

lock = threading.Lock()


def load_counts():
    if COUNTS_PATH.exists():
        try:
            return json.loads(COUNTS_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"_cursor": 0}


def save_counts(counts):
    COUNTS_PATH.write_text(json.dumps(counts, ensure_ascii=False), encoding="utf-8")


def take_kinds(n=2):
    with lock:
        counts = load_counts()
        cursor = int(counts.get("_cursor") or 0)
        kinds = [SEQUENCE[(cursor + i) % len(SEQUENCE)] for i in range(n)]
        counts["_cursor"] = cursor + n
        save_counts(counts)
    return kinds


def kind_of(item):
    if item["type"] == "open":
        q = item["question"].lower()
        if q.startswith("rozstrzygnij") or "rozstrzygnij" in q[:80]:
            return "rozstrzygnij"
        if q.startswith("porównaj") or q.startswith("porownaj") or "podobieństwo" in q or "różnic" in q[:120]:
            return "porownaj"
        if q.startswith("wyjaśnij") or q.startswith("wyjasnij"):
            return "wyjasnij"
        return "podaj"
    return item["type"]


class Deduper:
    def __init__(self):
        self.rows = []
        self._load_eval()
        for row in read_jsonl(OUT):
            self._add(row.get("question", ""), row.get("model_answer", ""), external=False)

    def _load_eval(self):
        for path in EVAL_DIR.glob("*.jsonl"):
            for row in read_jsonl(path):
                q = row.get("question") or ""
                a = row.get("model_answer") or row.get("solution") or ""
                self._add(q, a, external=True)

    def _add(self, question, answer, external):
        self.rows.append((word_ngrams(question), word_ngrams(answer), external))

    def check(self, question, answer):
        qg = word_ngrams(question)
        ag = word_ngrams(answer)
        if not qg:
            return "puste pytanie"
        for og, oa, external in self.rows:
            qj = jaccard(qg, og)
            aj = jaccard(ag, oa) if ag and oa else 0.0
            shared = len(qg & og)
            if qj > 0.35 and shared >= 6:
                return f"jaccard {qj:.2f} shared {shared} external={external}"
            if qj > 0.28 and aj > 0.35 and shared >= 4:
                return f"q+a {qj:.2f}/{aj:.2f} external={external}"
        return ""

    def add(self, question, answer):
        self._add(question, answer, external=False)


DEDUP = None


def notes_by_subtopic():
    out = {}
    for row in read_jsonl(KB):
        out[(row.get("section"), row.get("subtopic"))] = row
    return out


def jobs_from_taxonomy(bundles_per_subtopic, pilot):
    if not TAXONOMY.exists():
        return []
    tax = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    notes = notes_by_subtopic()
    done = load_ids(DONE, "bundle_id")
    jobs = []
    sections = tax.get("sections") or []
    if pilot:
        sections = sections[:2]
    for b in range(bundles_per_subtopic):
        for sec in sections:
            section = canon_section(sec.get("section")) or sec.get("section")
            for i, sub in enumerate(sec.get("subtopics") or []):
                note = notes.get((section, sub)) or notes.get((sec.get("section"), sub))
                if not note:
                    continue
                bid = f"{section.split('.', 1)[0].strip()}-{i}-b{b}"
                if bid in done:
                    continue
                jobs.append({
                    "bundle_id": bid,
                    "section": section,
                    "subtopic": sub,
                    "note": note.get("text") or "",
                    "bundle_index": b,
                    "no_source": (b + i) % 6 == 0,
                })
                if pilot and len(jobs) >= 4:
                    return jobs
    return jobs


def build_record(job, item, source_text, idx):
    typ = str(item.get("type") or "")
    if typ not in ("closed_tf", "closed_choice", "closed_match", "closed_multi", "open"):
        return None, "zły typ"
    question = " ".join(str(item.get("question") or "").split())
    if len(question) < 20:
        return None, "krótkie pytanie"
    if mentions_image(question):
        return None, "wymaga obrazu"
    answer = collapse_alternatives(str(item.get("model_answer") or ""))
    if typ in CLOSED_TYPES:
        answer = normalize_closed(typ, answer)
    if not valid_model_answer(typ, answer):
        return None, "zły klucz"
    if typ == "open" and has_alternative_marker(answer):
        return None, "alternatywy w kluczu"
    src = source_text.strip()
    if src and not (50 <= polish_word_count(src) <= 260):
        return None, f"długość źródła {polish_word_count(src)}"
    if src and not re.search(r"[.!?…]$", src.rstrip()):
        return None, "urywek źródła"
    try:
        pts = int(item.get("max_points") or 1)
    except (TypeError, ValueError):
        pts = 1
    pts = min(3, max(1, pts))
    rec = {
        "id": f"syn-{job['bundle_id']}-{idx}",
        "origin": "synthetic",
        "source_doc": "kompendium",
        "section": job["section"],
        "subtopic": job["subtopic"],
        "type": typ,
        "group": job["bundle_id"],
        "max_points": pts,
        "question": question,
        "source_text": src,
        "answer_format": canonical_format(typ, answer),
        "model_answer": answer,
        "rubric": str(item.get("rubric") or "").strip(),
        "needs_image": False,
        "image_refs": [],
        "verified": False,
        "verify_note": "",
        "open_kind": str(item.get("open_kind") or ""),
    }
    return rec, ""


def blind_solve(forge, rec, stage="E3", max_tokens=400, estimate=0.004):
    user = (
        f"Format odpowiedzi:\n{rec['answer_format']}\n\n"
        + (f"Źródło:\n{rec['source_text']}\n\n" if rec["source_text"] else "Brak źródła. Korzystaj z wiedzy historycznej.\n\n")
        + f"Polecenie:\n{rec['question']}"
    )
    data, _, cost = forge.call_json(stage, "gpt-6-luna", SYS_BLIND, user, max_tokens, estimate, "blind")
    return str(data.get("answer") or "").strip(), cost


def judge_open(forge, rec, blind, stage="E3", max_tokens=350, estimate=0.004):
    user = (
        f"Polecenie:\n{rec['question']}\n\nŹródło:\n{rec['source_text']}\n\n"
        f"Klucz:\n{rec['model_answer']}\n\nOdpowiedź bez klucza:\n{blind}"
    )
    data, _, cost = forge.call_json(stage, "gpt-6-luna", SYS_JUDGE, user, max_tokens, estimate, "judge")
    return data, cost


def verify(forge, rec, stage="E3"):
    blind_tokens = 800 if stage == "E5" else 400
    judge_tokens = 500 if stage == "E5" else 350
    blind, cost = blind_solve(forge, rec, stage=stage, max_tokens=blind_tokens)
    rec["_blind"] = blind
    if rec["type"] in CLOSED_TYPES:
        ok = normalize_closed(rec["type"], blind) == normalize_closed(rec["type"], rec["model_answer"])
        rec["verified"] = ok
        rec["verify_note"] = "zgodny klucz" if ok else f"rozbieżność, odpowiedź na ślepo: {blind[:180]}"
        return rec, cost
    data, c2 = judge_open(forge, rec, blind, stage=stage, max_tokens=judge_tokens)
    cost += c2
    agree = bool(data.get("agree"))
    key_ok = bool(data.get("key_ok"))
    unambiguous = data.get("unambiguous", True)
    note = str(data.get("note") or "")
    fix = data.get("fix_answer")
    if agree and key_ok and unambiguous is not False:
        rec["verified"] = True
        rec["verify_note"] = note or "zgodne merytorycznie"
        return rec, cost
    if (not key_ok) and isinstance(fix, str) and valid_model_answer(rec["type"], collapse_alternatives(fix)):
        fixed = collapse_alternatives(fix)
        if rec["type"] in CLOSED_TYPES:
            fixed = normalize_closed(rec["type"], fixed)
        rec["model_answer"] = fixed
        rec["answer_format"] = canonical_format(rec["type"], fixed)
        rec["verified"] = True
        rec["verify_note"] = "poprawiono klucz: " + note
        return rec, cost
    rec["verified"] = False
    rec["verify_note"] = note or f"odrzucone; ślepa: {blind[:160]}"
    return rec, cost


def bump(counts, rec):
    key = kind_of(rec)
    if key not in counts:
        key = "podaj" if rec["type"] == "open" else rec["type"]
    counts[key] = counts.get(key, 0) + 1


def process_bundle(forge, job):
    want = take_kinds(2)
    hint = (
        f"Dział: {job['section']}\nPodtemat: {job['subtopic']}\n"
        "Zrób DOKŁADNIE dwa zadania, w tej kolejności, bez zmiany typu:\n"
        f"1. {KIND_RULES[want[0]]}\n"
        f"2. {KIND_RULES[want[1]]}\n"
        "Źródło, jeśli jest, kończy się pełnym zdaniem (kropką), bez urwania w pół słowa.\n"
    )
    if job["no_source"]:
        hint += "Ta wiązka ma być bez źródła: source_text ustaw na pusty string. Pytania sprawdzają wiedzę z notatki.\n"
    else:
        hint += "Użyj źródła tekstowego albo tabeli.\n"
    hint += f"\nNotatka:\n{job['note'][:3500]}"
    data, _, _ = forge.call_json("E3", "gpt-6-sol", SYS_GEN, hint, 2200, 0.028, job["bundle_id"])
    source = str(data.get("source_text") or "")
    if job["no_source"]:
        source = ""
    written = 0
    for idx, item in enumerate((data.get("items") or [])[:2], start=1):
        expected = want[idx - 1]
        got = str(item.get("type") or "")
        if expected.startswith("closed") and got != expected:
            append_jsonl(REJECTED, {"id": f"syn-{job['bundle_id']}-{idx}", "reason": f"typ {got} zamiast {expected}", "section": job["section"]})
            continue
        if not expected.startswith("closed") and (got != "open" or str(item.get("open_kind") or "") != expected):
            # akceptuj otwarte, jeśli rodzaj da się poznać z polecenia
            q = str(item.get("question") or "").lower()
            ok_kind = (
                (expected == "rozstrzygnij" and "rozstrzygnij" in q)
                or (expected == "podaj" and (q.startswith("podaj") or q.startswith("wymień") or q.startswith("wymien")))
                or (expected == "wyjasnij" and (q.startswith("wyjaśnij") or q.startswith("wyjasnij")))
                or (expected == "porownaj" and (q.startswith("porównaj") or q.startswith("porownaj")))
            )
            if got != "open" or not ok_kind:
                append_jsonl(REJECTED, {"id": f"syn-{job['bundle_id']}-{idx}", "reason": f"typ {got}/{item.get('open_kind')} zamiast {expected}", "section": job["section"]})
                continue
        rec, reason = build_record(job, item, source, idx)
        if rec is None:
            append_jsonl(REJECTED, {"id": f"syn-{job['bundle_id']}-{idx}", "reason": reason, "section": job["section"]})
            continue
        with lock:
            why = DEDUP.check(rec["question"], rec["model_answer"])
            if why:
                append_jsonl(REJECTED, {"id": rec["id"], "reason": "dedup " + why, "section": job["section"], "question": rec["question"]})
                continue
            DEDUP.add(rec["question"], rec["model_answer"])
        try:
            rec, _ = verify(forge, rec)
        except BudgetExceeded:
            raise
        except Exception as exc:
            rec["verified"] = False
            rec["verify_note"] = "błąd weryfikacji: " + safe_err(exc)
        rec.pop("_blind", None)
        rec.pop("open_kind", None)
        if rec["verified"]:
            append_jsonl(OUT, rec)
            with lock:
                counts = load_counts()
                bump(counts, rec)
                save_counts(counts)
            written += 1
        else:
            append_jsonl(REJECTED, rec)
    append_jsonl(DONE, {"bundle_id": job["bundle_id"], "n": written})
    print(f"bundle {job['bundle_id']} kept {written}", flush=True)
    return written


def main():
    global DEDUP
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--bundles", type=int, default=2, help="wiązki na podtemat")
    parser.add_argument("--follow", action="store_true")
    args = parser.parse_args()
    ensure_dirs()
    forge = Forge()
    DEDUP = Deduper()
    bundles = 1 if args.pilot else args.bundles

    while True:
        jobs = jobs_from_taxonomy(bundles, args.pilot)
        print(f"E3 pending bundles {len(jobs)}", flush=True)
        if not jobs:
            if args.follow and not E2_DONE.exists() and not args.pilot:
                print("E3 czeka na kompendium", flush=True)
                time.sleep(45)
                continue
            break

        def work(job):
            try:
                return process_bundle(forge, job)
            except BudgetExceeded as exc:
                print("budget stop", exc, flush=True)
                return None
            except Exception as exc:
                print("bundle fail", job["bundle_id"], safe_err(exc), flush=True)
                return 0

        stop = False
        with ThreadPoolExecutor(max(1, args.workers)) as ex:
            futs = [ex.submit(work, job) for job in jobs]
            for fut in as_completed(futs):
                if fut.result() is None:
                    stop = True
        if stop or args.pilot or not args.follow:
            break
        if E2_DONE.exists():
            # jeszcze jedna runda po nowych notatkach, potem wyjście gdy pusto
            time.sleep(5)
            continue
    print("E3 stop kept", len(load_ids(OUT)), "rejected", len(read_jsonl(REJECTED)), flush=True)


if __name__ == "__main__":
    main()
