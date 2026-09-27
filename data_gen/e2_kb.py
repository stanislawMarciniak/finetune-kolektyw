"""E2: taksonomia działów i notatki kompendium. Model sol, limit 5 USD."""

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_gen.common import (
    BudgetExceeded,
    Forge,
    KB,
    ROOT,
    append_jsonl,
    ensure_dirs,
    load_ids,
    polish_word_count,
    read_jsonl,
    safe_err,
)
from data_gen.sections import SECTIONS, canon_section

TAXONOMY = ROOT / "data_gen" / "taxonomy.json"
DONE_NOTES = ROOT / "data_gen" / "state" / "e2_notes.jsonl"
E2_DONE = ROOT / "data_gen" / "state" / "e2_done"

SYS_TAX = """Jesteś metodykiem historii w liceum (zakres rozszerzony, podstawa programowa 2018, matura CKE).
Dla podanych działów wypisz po 6 konkretnych podtematów egzaminacyjnych.
Podtemat to jedno zdanie: fakt, proces albo umiejętność, o którą naprawdę pyta matura (daty, postacie, pojęcia, przyczyny i skutki).
Nie powtarzaj tego samego wątku. Rozdziel politykę, społeczeństwo, gospodarkę i kulturę, jeśli dział je obejmuje.
Dla działu XLII uwzględnij także politykę zagraniczną II Rzeczypospolitej.
Zwróć wyłącznie JSON: {"sections": [{"section": "<dokładny tytuł z listy>", "subtopics": ["...", "..."]}]}."""

SYS_NOTE = """Jesteś autorem kompendium do matury rozszerzonej z historii. Piszesz po polsku, tylko pewne fakty.
Notatka ma mieć 340–430 słów: kluczowe fakty, daty, postacie, pojęcia, przyczyny i skutki oraz 2–3 typowe pułapki egzaminacyjne.
Proza z akapitami. Zero wariantów „albo” przy datach i nazwach.
Nie pisz, że jesteś modelem, i nie zaznaczaj niepewności. Jeśli czegoś nie jesteś pewien, po prostu to pomiń.
Zwróć wyłącznie JSON: {"title": "...", "text": "..."}."""


def load_taxonomy():
    if not TAXONOMY.exists():
        return {"sections": []}
    return json.loads(TAXONOMY.read_text(encoding="utf-8"))


def save_taxonomy(data):
    TAXONOMY.parent.mkdir(parents=True, exist_ok=True)
    tmp = TAXONOMY.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(TAXONOMY)


def missing_sections(data):
    have = {canon_section(s.get("section")) for s in data.get("sections", [])}
    have.discard("")
    return [s for s in SECTIONS if s not in have]


def generate_taxonomy(forge, sections):
    user = "Działy:\n" + "\n".join(f"- {s}" for s in sections) + "\nWypisz dokładnie 6 podtematów dla każdego."
    data, _, _ = forge.call_json("E2", "gpt-6-sol", SYS_TAX, user, 2200, 0.04, "tax:" + sections[0][:12])
    current = load_taxonomy()
    by = {canon_section(s.get("section")): s for s in current.get("sections", [])}
    for row in data.get("sections") or []:
        section = canon_section(row.get("section"))
        if not section:
            # dopasuj po kolejności, jeśli model skrócił tytuł
            continue
        topics = []
        for t in row.get("subtopics") or []:
            t = " ".join(str(t).split())
            if len(t) >= 20:
                topics.append(t)
        topics = topics[:8]
        if len(topics) < 4:
            continue
        by[section] = {"section": section, "subtopics": topics[:6] if len(topics) >= 6 else topics}
    # jeśli model pominął dopasowanie tytułu, sparuj po roman w odpowiedzi surowej
    if len(by) < len(current.get("sections", [])) + len(sections) // 2:
        for row in data.get("sections") or []:
            raw = str(row.get("section") or "")
            section = canon_section(raw)
            if section:
                continue
            for s in sections:
                rom = s.split(".", 1)[0]
                if raw.strip().startswith(rom):
                    topics = [" ".join(str(t).split()) for t in (row.get("subtopics") or [])]
                    topics = [t for t in topics if len(t) >= 20][:6]
                    if len(topics) >= 4:
                        by[s] = {"section": s, "subtopics": topics}
    ordered = [by[s] for s in SECTIONS if s in by]
    save_taxonomy({"sections": ordered})
    print(f"taxonomy now {len(ordered)}", flush=True)


def note_id(section, subtopic):
    return f"{section}||{subtopic}"


def write_note(forge, section, subtopic):
    user = f"Dział: {section}\nPodtemat: {subtopic}\nNapisz notatkę kompendium."
    data, _, _ = forge.call_json("E2", "gpt-6-sol", SYS_NOTE, user, 1800, 0.02, "note")
    text = str(data.get("text") or "").strip()
    title = " ".join(str(data.get("title") or subtopic).split())
    wc = polish_word_count(text)
    if wc < 300:
        data, _, _ = forge.call_json(
            "E2", "gpt-6-sol", SYS_NOTE,
            user + "\nPoprzednia wersja była za krótka. Napisz 340–430 słów.",
            1800, 0.02, "note-retry",
        )
        text = str(data.get("text") or "").strip()
        title = " ".join(str(data.get("title") or subtopic).split())
        wc = polish_word_count(text)
    if wc < 220 or wc > 700:
        print(f"skip note words={wc} {section[:40]}", flush=True)
        append_jsonl(DONE_NOTES, {"id": note_id(section, subtopic), "skip": True, "words": wc})
        return False
    if any(bad in text.lower() for bad in ("jako model", "nie jestem pew", "nie mam pewności")):
        append_jsonl(DONE_NOTES, {"id": note_id(section, subtopic), "skip": True, "words": wc})
        return False
    append_jsonl(KB, {"section": section, "subtopic": subtopic, "title": title, "text": text, "words": wc})
    append_jsonl(DONE_NOTES, {"id": note_id(section, subtopic), "words": wc})
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    ensure_dirs()
    forge = Forge()
    data = load_taxonomy()
    missing = missing_sections(data)
    if args.pilot:
        missing = missing[:2]
    print(f"taxonomy missing {len(missing)}", flush=True)
    batch = 3
    for i in range(0, len(missing), batch):
        group = missing[i:i + batch]
        try:
            generate_taxonomy(forge, group)
        except BudgetExceeded as exc:
            print("budget stop taxonomy", exc, flush=True)
            return
        except Exception as exc:
            print("taxonomy fail", safe_err(exc), flush=True)
    data = load_taxonomy()
    done = load_ids(DONE_NOTES)
    for row in read_jsonl(KB):
        if int(row.get("words") or 0) >= 300:
            done.add(note_id(row.get("section", ""), row.get("subtopic", "")))
    buckets = {}
    for sec in data.get("sections", []):
        if args.pilot and sec["section"] not in SECTIONS[:2]:
            continue
        for i, sub in enumerate(sec.get("subtopics") or []):
            nid = note_id(sec["section"], sub)
            if nid not in done:
                buckets.setdefault(i, []).append((sec["section"], sub))
    jobs = []
    for i in sorted(buckets):
        jobs.extend(buckets[i])
    if args.pilot:
        jobs = jobs[:8]
    print(f"notes pending {len(jobs)}", flush=True)

    def work(job):
        section, sub = job
        try:
            return write_note(forge, section, sub)
        except BudgetExceeded as exc:
            print("budget stop", exc, flush=True)
            return None
        except Exception as exc:
            print("note fail", safe_err(exc), flush=True)
            return False

    with ThreadPoolExecutor(max(1, args.workers)) as ex:
        futs = [ex.submit(work, job) for job in jobs]
        for fut in as_completed(futs):
            if fut.result() is None:
                break
    if not args.pilot and not missing_sections(load_taxonomy()):
        pending_left = 0
        done = load_ids(DONE_NOTES)
        for sec in load_taxonomy().get("sections", []):
            for sub in sec.get("subtopics") or []:
                if note_id(sec["section"], sub) not in done:
                    pending_left += 1
        if pending_left == 0:
            E2_DONE.write_text("ok\n", encoding="utf-8")
            print("E2 complete", flush=True)
        else:
            print(f"E2 paused, notes left {pending_left}", flush=True)
    else:
        print("E2 pilot or partial finished", "notes", len(read_jsonl(KB)), flush=True)


if __name__ == "__main__":
    main()
