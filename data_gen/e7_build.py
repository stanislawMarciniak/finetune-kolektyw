"""Składa bazę wiedzy v2/v3 z plików v1 i wyników E7; waliduje przez NoteRetriever harnessu.

  python -m data_gen.e7_build v2
"""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_gen.common import ROOT, read_jsonl, spent_by_stage
from data_gen.e5_bulk import load_metas

KB = ROOT / "data" / "kb"
E7 = KB / "e7"
QUERIES = [
    "Panowanie Karola Wielkiego i odnowienie cesarstwa na Zachodzie",
    "Rządy Władysława Jagiełły i unia polsko-litewska",
    "Przemiany społeczno-gospodarcze w Rzeczypospolitej szlacheckiej w XVI wieku, gospodarka folwarczno-pańszczyźniana",
    "Reformy Solona i Klejstenesa w Atenach",
    "Rewolucja przemysłowa i jej skutki społeczne",
    "Polityka gospodarcza Edwarda Gierka",
]


def e7_rows(kind):
    ver = E7 / f"{kind}.verified.jsonl"
    rows = read_jsonl(ver) if ver.exists() and ver.stat().st_size else read_jsonl(E7 / f"{kind}.jsonl")
    return [{k: v for k, v in r.items() if k != "job"} for r in rows]


def dedup(rows, key):
    seen, out = set(), []
    for r in rows:
        k = key(r)
        if k in seen or not str(r.get("text") or "").strip():
            continue
        seen.add(k)
        out.append(r)
    return out


def _toks(s):
    return {w[:5] for w in re.findall(r"\w+", s.lower()) if len(w) > 3}


def near_dedup_timeline(old, new, thr=0.35):
    by = defaultdict(list)
    for r in old:
        by[r["year"]].append(_toks(r["title"] + " " + r["text"]))
    out = []
    for r in new:
        t = _toks(r["title"] + " " + r["text"])
        if any(len(t & o) / max(1, len(t | o)) >= thr for o in by[r["year"]]):
            continue
        by[r["year"]].append(t)
        out.append(r)
    return out


def near_dedup_persons(old, new):
    seen = set()
    for r in old:
        for w in re.findall(r"\w{5,}", r["name"].lower()):
            seen.add((w, re.sub(r"\D", "", r["years"])[:8]))
    out = []
    for r in new:
        keys = {(w, re.sub(r"\D", "", r["years"])[:8]) for w in re.findall(r"\w{5,}", r["name"].lower())}
        if keys & seen:
            continue
        seen |= keys
        out.append(r)
    return out


def main(ver):
    old = {f: read_jsonl(KB / f"{f}.jsonl") for f in ("kompendium", "kompendium_extra", "timeline", "persons", "terms")}
    old_titles = {" ".join((r.get("title") or "").lower().split()) for f in old.values() for r in f}
    new = {}
    for kind in ("notes", "timeline", "persons", "terms"):
        rows = dedup(e7_rows(kind), lambda r: " ".join(r["title"].lower().split()))
        new[kind] = [r for r in rows if " ".join(r["title"].lower().split()) not in old_titles]
    if ver != "v2":
        before = (len(new["timeline"]), len(new["persons"]))
        new["timeline"] = near_dedup_timeline(old["timeline"], new["timeline"])
        new["persons"] = near_dedup_persons(old["persons"], new["persons"])
        print(f"near-dedup: oś czasu {before[0]}→{len(new['timeline'])}, postaci {before[1]}→{len(new['persons'])}")
    for kind, prefix in (("notes", "e7n"), ("timeline", "e7tl"), ("persons", "e7per"), ("terms", "e7term")):
        for i, r in enumerate(new[kind], 1):
            r["id"] = f"{prefix}-{i:05d}"

    komp = old["kompendium"] + old["kompendium_extra"] + new["notes"]
    allnotes = [{"title": r["title"], "subtopic": r.get("subtopic", ""), "text": r["text"]} for r in komp]
    allnotes += [{"title": r["title"], "subtopic": str(r["year"]), "text": r["text"]} for r in old["timeline"] + new["timeline"]]
    allnotes += [{"title": r["name"], "subtopic": r["years"], "text": r["text"]} for r in old["persons"] + new["persons"]]
    allnotes += [{"title": r["term"], "subtopic": "", "text": r["text"]} for r in old["terms"] + new["terms"]]

    kp, ap = KB / f"kompendium_{ver}.jsonl", KB / f"kb_all_notes_{ver}.jsonl"
    for path, rows in ((kp, komp), (ap, allnotes)):
        if path.exists() and (KB / f"KB_{ver.upper()}_READY").exists():
            raise SystemExit(f"{path.name} jest już wydany (marker READY) — nie nadpisuję")
        with open(path, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    # walidacja
    problems = []
    for path in (kp, ap):
        rows = read_jsonl(path)
        empty = sum(1 for r in rows if not str(r.get("text") or "").strip() or not str(r.get("title") or "").strip())
        dup_text = len(rows) - len({r["text"] for r in rows})
        dup_title = len(rows) - len({(r["title"], r.get("subtopic", "")) for r in rows})
        problems.append(f"{path.name}: {len(rows)} wierszy, puste {empty}, duplikaty tekstu {dup_text}, duplikaty tytuł+podtemat {dup_title}")
    sys.path.insert(0, str(ROOT / "harness"))
    import run_exam
    retrieval = []
    for path in (kp, ap):
        nr = run_exam.NoteRetriever(str(path))
        for q in QUERIES:
            hits = nr.search(q, 3)
            retrieval.append(f"- `{path.name}` | {q} → " + " / ".join(h["title"][:60] for h in hits))

    spent = spent_by_stage()[0]["E7"]
    cost_file = E7 / "release_costs.json"
    costs = json.loads(cost_file.read_text()) if cost_file.exists() else {}
    costs[ver] = round(spent, 4)
    cost_file.write_text(json.dumps(costs))
    write_stats(ver, old, new, komp, allnotes, costs, problems, retrieval)
    print("\n".join(problems))
    print("\n".join(retrieval))


def table(title, before, after):
    keys = sorted(set(before) | set(after), key=lambda k: (-after.get(k, 0), str(k)))
    out = [f"### {title}", "", "| klucz | przed | po | + |", "|---|---:|---:|---:|"]
    out += [f"| {k} | {before.get(k, 0)} | {after.get(k, 0)} | {after.get(k, 0) - before.get(k, 0)} |" for k in keys]
    return out + [""]


def write_stats(ver, old, new, komp, allnotes, costs, problems, retrieval):
    metas = load_metas()
    sec_epoch = {m["section"]: m["epoch"] for m in metas}
    v1_notes = old["kompendium"] + old["kompendium_extra"]
    prev_cost = costs.get("v2", 0.0) if ver != "v2" else 0.0
    lines = [
        f"# Baza wiedzy {ver} (E7)", "",
        f"- Koszt E7 łącznie do wydania {ver}: **${costs[ver]:.3f}**" + (f" (v2: ${costs.get('v2', 0):.3f}, przyrost {ver}: ${costs[ver] - prev_cost:.3f})" if ver != "v2" else ""),
        f"- Pliki: `data/kb/kompendium_{ver}.jsonl` ({len(komp)}), `data/kb/kb_all_notes_{ver}.jsonl` ({len(allnotes)})",
        "- Źródło nowych pozycji: wyłącznie taksonomia CKE (`data_gen/taxonomy.json`), model gpt-6-luna, skrypt `data_gen/e7_kb.py`.",
        "",
        "| typ | v1 | nowe | razem |", "|---|---:|---:|---:|",
        f"| notatki kompendium | {len(v1_notes)} | {len(new['notes'])} | {len(komp)} |",
        f"| oś czasu | {len(old['timeline'])} | {len(new['timeline'])} | {len(old['timeline']) + len(new['timeline'])} |",
        f"| postaci | {len(old['persons'])} | {len(new['persons'])} | {len(old['persons']) + len(new['persons'])} |",
        f"| pojęcia | {len(old['terms'])} | {len(new['terms'])} | {len(old['terms']) + len(new['terms'])} |",
        f"| kb_all_notes | {len(v1_notes) + len(old['timeline']) + len(old['persons']) + len(old['terms'])} | | {len(allnotes)} |",
        "",
    ]
    lines += table("Nowe notatki — rodzaj (gap = brakujący podtemat, aspect = synteza aspektowa, topic = kluczowe zagadnienie)", {}, Counter(r.get("kind") for r in new["notes"]))
    lines += table("Syntezy aspektowe — aspekt", {}, Counter(r.get("aspect") for r in new["notes"] if r.get("kind") == "aspect"))
    ver_counts = Counter(r.get("verified", "—") for k in new for r in new[k])
    lines += table("Weryfikacja nowych pozycji (ok / fixed = poprawione / unchecked; odrzucone nie weszły)", {}, ver_counts)
    lines += table("Notatki kompendium — epoka", Counter(sec_epoch.get(r["section"], "—") for r in v1_notes), Counter(sec_epoch.get(r["section"], "—") for r in komp))
    lines += table("Oś czasu — epoka", Counter(r["epoch"] for r in old["timeline"]), Counter(r["epoch"] for r in old["timeline"] + new["timeline"]))
    lines += table("Oś czasu — zakres", Counter(r["scope"] for r in old["timeline"]), Counter(r["scope"] for r in old["timeline"] + new["timeline"]))
    lines += table("Postaci — zakres", Counter(r["scope"] for r in old["persons"]), Counter(r["scope"] for r in old["persons"] + new["persons"]))
    lines += table("Pojęcia — epoka", Counter(r["epoch"] for r in old["terms"]), Counter(r["epoch"] for r in old["terms"] + new["terms"]))
    lines += table("Notatki kompendium — dział", Counter(r["section"] for r in v1_notes), Counter(r["section"] for r in komp))
    lines += table("Oś czasu — dział", Counter(r["section"] for r in old["timeline"]), Counter(r["section"] for r in old["timeline"] + new["timeline"]))
    lines += table("Postaci — dział", Counter(r["section"] for r in old["persons"]), Counter(r["section"] for r in old["persons"] + new["persons"]))
    lines += ["### Walidacja", ""] + [f"- {p}" for p in problems] + ["", "### Próbne zapytania (programowe, nie z arkuszy)", ""] + retrieval + [""]
    (KB / f"KB_{ver.upper()}_STATS.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1])
