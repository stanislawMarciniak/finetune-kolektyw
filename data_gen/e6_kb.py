"""E6: oś czasu, postaci, pojęcia i brakujące notatki. Limit etapu 4 USD.

Zapis przyrostowy i wznawianie. Model gpt-6-luna, 16 wątków.
"""

import argparse
import json
import re
import sys
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_gen.common import (
    BudgetExceeded,
    Forge,
    KB,
    ROOT,
    append_jsonl,
    ensure_dirs,
    polish_word_count,
    read_jsonl,
    safe_err,
    spent_by_stage,
)
from data_gen.e5_bulk import load_metas

OUT_DIR = ROOT / "data" / "kb"
TIMELINE = OUT_DIR / "timeline.jsonl"
PERSONS = OUT_DIR / "persons.jsonl"
TERMS = OUT_DIR / "terms.jsonl"
EXTRA = OUT_DIR / "kompendium_extra.jsonl"
STATS = OUT_DIR / "KB_STATS.md"
MODEL = "gpt-6-luna"

TARGETS = {
    "timeline": {"Polska": 2000, "powszechna": 1000},
    "persons": {"Polska": 800, "powszechna": 400},
    "terms": 500,
    "notes": 300,
}
BATCH = {"timeline": 15, "persons": 12, "terms": 15, "notes": 5}

DATE_RE = re.compile(r"\b\d{3,4}\b|p\.n\.e\.|\bwieku\b|\br\.", re.I)
stop_event = threading.Event()


def norm_name(text):
    s = (text or "").lower().replace("–", "-").replace("—", "-")
    s = re.sub(r"[^a-ząćęłńóśźż0-9 ]+", " ", s, flags=re.I)
    return re.sub(r"\s+", " ", s).strip()


def has_date(text):
    return bool(DATE_RE.search(text or ""))


SYS = {
    "timeline": """Ukladasz hasła osi czasu do matury z historii (pewne fakty szkolne, bez wymyślonych dat).
Każde hasło: rok jako liczba (p.n.e. ujemnie), data_text po polsku (np. „15 lipca 1410 r.”), krótki title, text 2–4 zdania (co, kto, gdzie, przyczyna albo skutek, z nazwami i datą), persons (lista osób).
Zakres i dział podane w poleceniu są wiążące. Nie powtarzaj tytułów z listy unikania.
Zwróć wyłącznie JSON: {"items": [{"year": 1410, "date_text": "15 lipca 1410 r.", "title": "...", "text": "...", "persons": ["..."]}]}""",
    "persons": """Ukladasz biogramy do matury z historii. Same pewne fakty.
Każda postać: name, years (np. „1467–1548” albo „ok. 100–44 p.n.e.”), role (krótko), text z 3–5 faktami i datami.
Nie powtarzaj nazw z listy unikania. Zakres i dział są wiążące.
Zwróć wyłącznie JSON: {"items": [{"name": "...", "years": "...", "role": "...", "text": "..."}]}""",
    "terms": """Ukladasz pojęcia i nazwy stosowane w historiografii (jak „pacta conventa”, „konstytucja nihil novi”, „rekonkwista”, „pozytywizm”).
Każde: term, text = definicja + kontekst historyczny + daty. Bez daty odrzuć pojęcie i nie umieszczaj go w JSON.
Nie powtarzaj terminów z listy unikania.
Zwróć wyłącznie JSON: {"items": [{"term": "...", "text": "..."}]}""",
    "notes": """Piszesz notatki kompendium do matury z historii, po polsku, 250–350 słów.
Każda notatka: title, text (fakty, daty, postacie, przyczyny i skutki, typowa pułapka egzaminacyjna). Tylko pewne fakty. Musi paść co najmniej jedna data.
Nie powtarzaj tytułów z listy unikania.
Zwróć wyłącznie JSON: {"items": [{"subtopic": "<dokładnie jak w poleceniu>", "title": "...", "text": "..."}]}""",
}


class Store:
    def __init__(self, metas):
        self.metas = metas
        self.by_section = {m["section"]: m for m in metas}
        self.lock = threading.Lock()
        self.names = set()
        self.counts = {
            "timeline": Counter(),
            "persons": Counter(),
            "terms": Counter(),
            "notes": Counter(),
        }
        self.scope_counts = {
            "timeline": Counter(),
            "persons": Counter(),
            "terms": Counter(),
        }
        self.seq = Counter()
        self.inflight_subs = set()
        self._load()

    def _take_name(self, name):
        key = norm_name(name)
        if not key or key in self.names:
            return False
        self.names.add(key)
        return True

    def _load(self):
        for kind, path, field in (
            ("timeline", TIMELINE, "title"),
            ("persons", PERSONS, "name"),
            ("terms", TERMS, "term"),
            ("notes", EXTRA, "title"),
        ):
            for row in read_jsonl(path):
                self._take_name(row.get(field) or row.get("title") or "")
                sec = row.get("section") or ""
                self.counts[kind][sec] += 1
                if kind != "notes":
                    self.scope_counts[kind][row.get("scope") or ""] += 1
                self.seq[kind] += 1
        for row in read_jsonl(KB):
            self._take_name(row.get("title") or "")
        for row in read_jsonl(EXTRA):
            self._take_name(row.get("title") or "")

    def next_id(self, kind):
        self.seq[kind] += 1
        prefix = {"timeline": "tl", "persons": "per", "terms": "term", "notes": "extra"}[kind]
        return f"{prefix}-{self.seq[kind]:05d}"

    def scope_need(self, kind, scope):
        if kind == "terms":
            return 0
        have = self.scope_counts[kind][scope]
        return TARGETS[kind][scope] - have

    def note_need(self):
        return TARGETS["notes"] - sum(self.counts["notes"].values())

    def section_quota(self, kind, meta):
        scope = meta["scope"]
        pool = [m for m in self.metas if m["scope"] == scope] or self.metas
        if kind == "terms":
            base = TARGETS["terms"] // len(self.metas)
            extra = TARGETS["terms"] % len(self.metas)
            target = base + (1 if self.metas.index(meta) < extra else 0)
        elif kind == "notes":
            target = 0
        else:
            total = TARGETS[kind][scope]
            base = total // len(pool)
            extra = total % len(pool)
            target = base + (1 if pool.index(meta) < extra else 0)
        return target

    def pick_job(self):
        with self.lock:
            best = None
            best_key = None
            for kind in ("timeline", "persons", "terms"):
                for meta in self.metas:
                    if kind != "terms" and self.scope_need(kind, meta["scope"]) <= 0:
                        continue
                    quota = self.section_quota(kind, meta)
                    deficit = quota - self.counts[kind][meta["section"]]
                    if deficit <= 0:
                        continue
                    key = (deficit, self.scope_need(kind, meta["scope"]) if kind != "terms" else deficit)
                    if best_key is None or key > best_key:
                        best_key = key
                        best = (kind, meta, min(BATCH[kind], deficit))
            if best:
                kind, meta, n = best
                self.counts[kind][meta["section"]] += n
                if kind != "terms":
                    self.scope_counts[kind][meta["scope"]] += n
                return {"kind": kind, "meta": meta, "n": n, "subtopics": None}
            gaps = [g for g in self._note_gaps() if g not in self.inflight_subs]
            if not gaps or self.note_need() <= 0:
                return None
            n = min(BATCH["notes"], len(gaps), self.note_need())
            chosen = gaps[:n]
            for sec, sub in chosen:
                self.counts["notes"][sec] += 1
                self.inflight_subs.add((sec, sub))
            return {"kind": "notes", "meta": None, "n": n, "subtopics": chosen}

    def release_job(self, job, kept):
        with self.lock:
            kind = job["kind"]
            if kind == "notes":
                for sec, sub in job.get("subtopics") or []:
                    self.inflight_subs.discard((sec, sub))
                missed = job["n"] - kept
                if missed > 0 and job["subtopics"]:
                    for sec, _sub in job["subtopics"][:missed]:
                        self.counts["notes"][sec] = max(0, self.counts["notes"][sec] - 1)
                return
            meta = job["meta"]
            missed = job["n"] - kept
            if missed <= 0:
                return
            self.counts[kind][meta["section"]] = max(0, self.counts[kind][meta["section"]] - missed)
            if kind != "terms":
                self.scope_counts[kind][meta["scope"]] = max(0, self.scope_counts[kind][meta["scope"]] - missed)

    def _note_gaps(self):
        have_sub = set()
        for row in read_jsonl(KB):
            have_sub.add((row.get("section"), row.get("subtopic")))
        for row in read_jsonl(EXTRA):
            have_sub.add((row.get("section"), row.get("subtopic")))
        # rezerwa inflight jest już doliczona do counts, nie do pliku — odejmij zaplanowane
        gaps = []
        for meta in self.metas:
            for sub in meta["subtopics"]:
                if (meta["section"], sub) in have_sub:
                    continue
                gaps.append((meta["section"], sub))
        if gaps:
            return gaps
        # drugie ujęcie, żeby dojść do ~300, gdy brakujących podtematów jest mniej
        for meta in self.metas:
            for sub in meta["subtopics"]:
                if self.counts["notes"][meta["section"]] >= 8:
                    continue
                gaps.append((meta["section"], sub + " — ujęcie uzupełniające"))
                if len(gaps) >= self.note_need():
                    return gaps
        return gaps

    def avoid_list(self, kind):
        path = {"timeline": TIMELINE, "persons": PERSONS, "terms": TERMS, "notes": EXTRA}[kind]
        field = {"timeline": "title", "persons": "name", "terms": "term", "notes": "title"}[kind]
        names = []
        for row in read_jsonl(path)[-40:]:
            names.append(str(row.get(field) or "")[:80])
        return names[-80:]


def user_for(store, job):
    if job["kind"] == "notes":
        lines = [f"Napisz {job['n']} notatek, po jednej na podtemat. Podtemat w JSON ma być identyczny."]
        for sec, sub in job["subtopics"]:
            lines.append(f"- dział: {sec} | podtemat: {sub}")
        lines.append("Unikaj tytułów:\n" + "\n".join(store.avoid_list("notes")))
        return "\n".join(lines)
    meta = job["meta"]
    kind = job["kind"]
    lines = [
        f"Dział: {meta['section']}",
        f"Epoka: {meta['epoch']}",
        f"Zakres: {meta['scope']}",
        f"Liczba haseł: {job['n']}. Mają być różne od listy unikania.",
        "Dla postaci wybieraj osoby z podtematów działu, także mniej oczywiste (wodzowie, biskupi, ministrowie, uczeni), nie tylko najsłynniejsze nazwiska.",
        "Podtematy działu (dobierz hasła do nich, nie wychodź poza dział):",
    ]
    lines.extend(f"- {s}" for s in meta["subtopics"])
    lines.append("Unikaj:\n" + "\n".join(store.avoid_list(kind)))
    return "\n".join(lines)


def valid_timeline(row, meta):
    try:
        year = int(row.get("year"))
    except (TypeError, ValueError):
        return None
    title = " ".join(str(row.get("title") or "").split())
    text = " ".join(str(row.get("text") or "").split())
    date_text = " ".join(str(row.get("date_text") or "").split())
    persons = [str(p).strip() for p in (row.get("persons") or []) if str(p).strip()]
    if len(title) < 3 or len(text) < 40 or not date_text or not has_date(date_text + " " + text):
        return None
    return {
        "scope": meta["scope"],
        "epoch": meta["epoch"],
        "section": meta["section"],
        "year": year,
        "date_text": date_text,
        "title": title,
        "text": text,
        "persons": persons[:8],
    }


def valid_person(row, meta):
    name = " ".join(str(row.get("name") or "").split())
    years = " ".join(str(row.get("years") or "").split())
    text = " ".join(str(row.get("text") or "").split())
    role = " ".join(str(row.get("role") or "").split())
    if len(name) < 3 or not has_date(years + " " + text) or len(text) < 40:
        return None
    return {
        "scope": meta["scope"],
        "name": name,
        "years": years,
        "title": name,
        "role": role or "postać historyczna",
        "text": text,
        "section": meta["section"],
    }


def valid_term(row, meta):
    term = " ".join(str(row.get("term") or "").split())
    text = " ".join(str(row.get("text") or "").split())
    if len(term) < 2 or len(text) < 40 or not has_date(text):
        return None
    return {
        "scope": meta["scope"],
        "term": term,
        "title": term,
        "epoch": meta["epoch"],
        "text": text,
    }


def valid_note(row, sub_map):
    sub = " ".join(str(row.get("subtopic") or "").split())
    title = " ".join(str(row.get("title") or "").split())
    text = str(row.get("text") or "").strip()
    sec = sub_map.get(sub) or sub_map.get(sub.replace(" — ujęcie uzupełniające", ""))
    if not sec or len(title) < 3 or not has_date(text):
        return None
    wc = polish_word_count(text)
    if not (250 <= wc <= 350):
        return None
    return {"section": sec, "subtopic": sub, "title": title, "text": text, "words": wc}


def save_row(store, kind, row):
    path = {"timeline": TIMELINE, "persons": PERSONS, "terms": TERMS, "notes": EXTRA}[kind]
    name = row.get("title") or row.get("name") or row.get("term")
    with store.lock:
        if not store._take_name(name):
            return False
        row = dict(row)
        row["id"] = store.next_id(kind)
        append_jsonl(path, row)
        return True


def process_job(forge, store, job):
    kept = 0
    try:
        if stop_event.is_set():
            return 0
        kind = job["kind"]
        data, _, _ = forge.call_json(
            "E6", MODEL, SYS[kind], user_for(store, job),
            7000 if kind == "notes" else 4500, 0.012, kind,
        )
        items = data.get("items") if isinstance(data, dict) else None
        if isinstance(items, dict):
            items = [items]
        if not isinstance(items, list):
            items = []
        sub_map = {}
        if kind == "notes":
            for sec, sub in job["subtopics"]:
                sub_map[" ".join(sub.split())] = sec
        for raw in items[: job["n"] + 2]:
            if not isinstance(raw, dict):
                continue
            if kind == "timeline":
                row = valid_timeline(raw, job["meta"])
            elif kind == "persons":
                row = valid_person(raw, job["meta"])
            elif kind == "terms":
                row = valid_term(raw, job["meta"])
            else:
                row = valid_note(raw, sub_map)
            if row and save_row(store, kind, row):
                kept += 1
        print(f"{kind} +{kept}/{job['n']}", flush=True)
        return kept
    finally:
        store.release_job(job, kept)


def write_stats(elapsed, base_cost):
    def rows(path):
        return read_jsonl(path)

    tl, pe, te, ex = rows(TIMELINE), rows(PERSONS), rows(TERMS), rows(EXTRA)
    spent, _ = spent_by_stage()
    cost = spent.get("E6", 0) - base_cost
    lines = [
        "# Baza wiedzy E6",
        "",
        f"- Koszt tego uruchomienia (usage × 1,2): **${cost:.4f}**",
        f"- Czas: {elapsed / 60:.1f} min",
        "",
        "| plik | liczba |",
        "|---|---:|",
        f"| timeline.jsonl | {len(tl)} |",
        f"| persons.jsonl | {len(pe)} |",
        f"| terms.jsonl | {len(te)} |",
        f"| kompendium_extra.jsonl | {len(ex)} |",
        "",
    ]
    for title, data, key in (
        ("Oś czasu — zakres", tl, "scope"),
        ("Oś czasu — epoka", tl, "epoch"),
        ("Postaci — zakres", pe, "scope"),
        ("Pojęcia — epoka", te, "epoch"),
        ("Pojęcia — zakres", te, "scope"),
    ):
        c = Counter(r.get(key) or "—" for r in data)
        lines.append(f"### {title}")
        lines.append("")
        lines.append("| wartość | liczba |")
        lines.append("|---|---:|")
        for name, k in c.most_common():
            lines.append(f"| {name} | {k} |")
        lines.append("")
    for title, data in (("Oś czasu — dział", tl), ("Postaci — dział", pe), ("Notatki — dział", ex)):
        c = Counter(r.get("section") or "—" for r in data)
        lines.append(f"### {title}")
        lines.append("")
        lines.append("| dział | liczba |")
        lines.append("|---|---:|")
        for name, k in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:80]:
            lines.append(f"| {name} | {k} |")
        lines.append("")
    STATS.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=16)
    args = parser.parse_args()
    workers = min(16, max(1, args.workers))
    ensure_dirs()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    metas = load_metas()
    store = Store(metas)
    forge = Forge()
    base = spent_by_stage()[0].get("E6", 0.0)
    t0 = time.perf_counter()
    print(
        f"E6 start timeline {sum(store.scope_counts['timeline'].values())} "
        f"persons {sum(store.scope_counts['persons'].values())} "
        f"terms {sum(store.counts['terms'].values())} "
        f"notes {sum(store.counts['notes'].values())} workers {workers}",
        flush=True,
    )
    pending = {}
    waves = 0
    with ThreadPoolExecutor(workers) as ex:
        while not stop_event.is_set():
            while len(pending) < workers and not stop_event.is_set():
                job = store.pick_job()
                if job is None:
                    break
                fut = ex.submit(process_job, forge, store, job)
                pending[fut] = job
            if not pending:
                break
            done, _ = wait(set(pending), return_when=FIRST_COMPLETED)
            for fut in done:
                job = pending.pop(fut)
                try:
                    fut.result()
                except BudgetExceeded:
                    stop_event.set()
                    print("E6 budżet", flush=True)
                except Exception as exc:
                    print("E6 błąd", safe_err(exc), flush=True)
            waves += 1
            if waves % 8 == 0:
                write_stats(time.perf_counter() - t0, base)
    write_stats(time.perf_counter() - t0, base)
    print("E6 stop", flush=True)


if __name__ == "__main__":
    main()
