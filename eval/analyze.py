"""Analiza wyników na poziomie zadań: typ zadania, epoka, Polska / powszechna, obraz / bez obrazu.

    python eval/analyze.py            # -> raports/08-wyniki-tabele.md (+ results/item_scores.csv)
Źródła: eval/data/<zbiór>.jsonl (zadania) + results/grades/<zbiór>/<przebieg>.{auto,judge}.json (punkty).
Zamknięte ocenia kod (niezależne od sędziego). Otwarte i eseje bierzemy tylko z przebiegów ocenianych przez gpt-6-luna
(H-E6: starszy sędzia był o ~4 pp łaskawszy).
"""

import csv
import json
import re
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA, GRADES = ROOT / "eval" / "data", ROOT / "results" / "grades"
SETS = ["test2024_split", "test2025_split", "test2026_split", "dev2023_img"]
MAIN = ["test2024_split", "test2025_split"]

# przebiegi oceniane lunką (harness z sob po 14:00 albo ponownie ocenione kopie __s42L), z etykietą do tabel
LUNA_RUNS = {
    "gemma4-12b-qat__s42L": "T1 Gemma-4-12B QAT, stara konfiguracja (myślenie)",
    "gemma4-qat-t1final": "T1 Gemma-4-12B QAT, t1final (myślenie)",
    "pllum-12b-base-sft__none": "T2 PLLuM-12B-base + LoRA",
    "pllum-12b-base-sft__fix": "T2 PLLuM-12B-base + LoRA, poprawka eseju",
    "pllum-12b-base-sft__hyde_all": "T2 PLLuM-12B-base + LoRA + HyDE",
    "q35-4b-think__none": "T3 Qwen3.5-4B Q4 myślenie",
    "q35-4b-q4-think-fb__none": "T3 Qwen3.5-4B Q4 myślenie + powtórka",
    "q35-4b-think__hyde_all": "T3 Qwen3.5-4B Q4 myślenie + HyDE",
    "q35-2b__none": "Qwen3.5-2B Q4",
    "q35-2b__hyde_podaj": "Qwen3.5-2B Q4 + HyDE (podaj)",
    "q35-2b-sft__none": "Qwen3.5-2B Q4 + LoRA",
    "bielik-1.5b__none": "Bielik-1.5B Q8",
    "bielik-1.5b__hyde_all": "Bielik-1.5B Q8 + HyDE",
    "bielik-1.5b-q4-sft__none": "Bielik-1.5B Q4 + LoRA",
}
# stare przebiegi z Modal: tylko do tabel zamkniętych (ocena automatyczna)
CLOSED_ONLY = {
    "gemma4-12b-qat__s42": "Gemma-4-12B QAT myślenie (Modal)",
    "bielik-11b-v3-q5__s42": "Bielik-11B-v3 Q5",
    "bielik-pl-11b-q5__s42": "Bielik-PL-11B Q5",
    "q35-9b-q5__s42": "Qwen3.5-9B Q5",
    "q35-4b-q4__s42": "Qwen3.5-4B Q4 bez myślenia",
    "q35-4b-q4-think-img__s42": "Qwen3.5-4B Q4 myślenie (Modal)",
    "q35-2b-q4__s42": "Qwen3.5-2B Q4 (Modal)",
    "bielik-1.5b-q8__s42": "Bielik-1.5B Q8 (Modal)",
    "bielik-11b-base-q5__s42": "Bielik-11B-Base (goły)",
    "bielik-4.5b-base-q5__s42": "Bielik-4.5B-Base (goły)",
    "gemma4-12b-pt-q4__s42": "Gemma-4-12B pt (goły)",
}
# wpływ myślenia na zamknięte (pary tych samych modeli, ocena automatyczna)
THINK_PAIRS = [
    ("dev2023_text", "gemma4-12b-qat-nothink__s42", "gemma4-12b-qat__s42", "Gemma-4-12B QAT"),
    ("dev2023_text", "q35-4b-q4__s42", "q35-4b-q4-think__s42", "Qwen3.5-4B Q4"),
    ("dev2023_text", "q35-2b-q4__s42", "q35-2b-q4-think__s42", "Qwen3.5-2B Q4"),
    ("test2024_split", "q35-4b-q4__s42", "q35-4b-q4-think-img__s42", "Qwen3.5-4B Q4"),
    ("test2025_split", "q35-4b-q4__s42", "q35-4b-q4-think-img__s42", "Qwen3.5-4B Q4"),
]

EPOCHS = [(-10000, 476, "1 starożytność"), (476, 1492, "2 średniowiecze"), (1492, 1815, "3 nowożytność"),
          (1815, 1914, "4 XIX w. (1815–1914)"), (1914, 1945, "5 1914–1945"), (1945, 2100, "6 po 1945")]
ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10, "XI": 11, "XII": 12,
         "XIII": 13, "XIV": 14, "XV": 15, "XVI": 16, "XVII": 17, "XVIII": 18, "XIX": 19, "XX": 20, "XXI": 21}
KEYWORDS = [  # zapas, gdy w tekście nie ma dat
    (r"starożyt|faraon|Egip|Mezopotam|Aten|Sparta|Rzym(?!sko-katol)|cesarstw\w+ rzymsk|polis|p\.\s?n\.\s?e", 0),
    (r"średniow|Piast|Chrobr|Mieszk|krucja|rycer|zakon krzyż|feudal|Karol\w* Wielk", 1100),
    (r"szlacht|Rzeczpospolit\w+ Obojga|sejmik|reformac|Jagiellon|Waz|Sobiesk|oświeceni", 1650),
    (r"zabor|powstani\w+ (listopad|stycz)|Napoleon|Księstw\w+ Warszawsk|pozytywi|Królestw\w+ Polsk", 1860),
    (r"I wojn\w+ światow|II Rzeczpospolit|Piłsudsk|II wojn\w+ światow|okupac|Hitler|Stalin|getto", 1930),
    (r"PRL|Solidarno|stan\w* wojenn|zimn\w+ wojn|Gomułk|Gierk|komunist", 1970),
]
POLAND = re.compile(r"Polsk|Polak|Polacy|Rzeczpospolit|Piast|Jagiell|Krak|Warszaw|sejm|szlacht|PRL|Solidarno|"
                    r"Piłsud|Gomułk|Gierk|Mieszk|Chrobr|Kościuszk|zabor|Galicj|Litw", re.I)


CITATION = re.compile(r"(?:Za|Na podstawie|Źródło)\s*:[^\n]{0,250}|"
                      r"(?:Warszawa|Kraków|Wrocław|Poznań|Lublin|Łódź|Gdańsk|Katowice|Toruń|Olsztyn|Białystok|Rzeszów|"
                      r"Kielce|Opole|Londyn|Paryż|Berlin|Wiedeń|Oxford|London|Paris|New York|Bydgoszcz|Częstochowa)"
                      r"[\s,]*(?:\d{4}(?:[–-]\d{2,4})?)|\bs\.\s*\d+(?:[–-]\d+)?|\bt\.\s*[IVX\d]+|https?://\S+|dostęp[^\n]{0,40}")


def years_in(text):
    text = CITATION.sub(" ", text)
    ys = []
    for m in re.finditer(r"\b(\d{1,4})\s*(?:r\.|roku|rok)?\s*(p\.\s?n\.\s?e\.)?", text):
        n, bc = int(m.group(1)), bool(m.group(2))
        if bc:
            ys.append(-n)
        elif 1000 <= n <= 2025 and not re.match(r"\s*(zł|km|osób|tys|mln|%)", text[m.end():m.end() + 6]):
            ys.append(n)
    for m in re.finditer(r"\b([IVX]{1,5})\s*(?:–|-)?\s*(?:[IVX]{1,5}\s*)?w(?:iek\w*|\.)", text):
        if m.group(1) in ROMAN:
            ys.append((ROMAN[m.group(1)] - 1) * 100 + 50)
    return ys


def epoch_of(text):
    ys = years_in(text)
    if ys:
        y = statistics.median(ys)
    else:
        hits = [y for pat, y in KEYWORDS if re.search(pat, text)]
        if not hits:
            return "? nieokreślona"
        y = statistics.median(hits)
    return next(name for lo, hi, name in EPOCHS if lo <= y < hi)


def subtype(it):
    t, q = it["type"], it["question"]
    if t.startswith("closed") and it.get("key"):
        return t
    if t == "essay":
        return "essay"
    if q.startswith("Rozstrzygnij"):
        return "open: rozstrzygnij"
    if q.startswith(("Podaj", "Wymień", "Nazwij")):
        return "open: podaj"
    if q.startswith(("Wyjaśnij", "Uzasadnij")):
        return "open: wyjaśnij/uzasadnij"
    return "open: inne"


def load(sets=None):
    items = {}
    for ds in sets or SETS + ["dev2023_text"]:
        path = DATA / f"{ds}.jsonl"
        if not path.exists():
            continue
        rows = [json.loads(l) for l in open(path, encoding="utf-8")]
        groups = defaultdict(str)
        for it in rows:  # klucz i rozwiązanie CKE zwykle zawierają nazwiska i daty, których brak w poleceniu
            groups[it["id"].split(".")[0]] += (f" {it['question']} {it.get('sources', '')} {it.get('solution') or ''} "
                                               f"{it.get('model_answer') or ''} {json.dumps(it.get('key') or '', ensure_ascii=False)}")
        # arkusz CKE jest ułożony chronologicznie, więc grupa bez dat dostaje epokę poprzedniej grupy
        group_epoch, prev = {}, None
        for gid in groups:
            e = epoch_of(groups[gid])
            if e.startswith("?") and prev:
                e = prev
            group_epoch[gid], prev = e, e
        for it in rows:
            gid = it["id"].split(".")[0]
            g = groups[gid]
            items[(ds, it["id"])] = {
                "ds": ds, "id": it["id"], "max": float(it["max_points"]), "sub": subtype(it),
                "closed": it["type"].startswith("closed") and bool(it.get("key")),
                "img": bool(it.get("images")), "epoch": "essay" if it["type"] == "essay" else group_epoch[gid],
                "pl": "essay" if it["type"] == "essay" else ("Polska" if POLAND.search(CITATION.sub(" ", g)) else "powszechna"),
            }
    return items


def grades(ds, run):
    auto_f = GRADES / ds / f"{run}.auto.json"
    if not auto_f.exists():
        return None
    g = json.load(open(auto_f))
    judge_f = GRADES / ds / f"{run}.judge.json"
    if judge_f.exists():
        g.update(json.load(open(judge_f)))
    return g


def table(rows, runs, key, sets, closed_only=False):
    """rows: dict[(ds,id)] -> item; zwraca wiersze tabeli: run × wartości key (procent punktów)."""
    cats = sorted({it[key] for (ds, _), it in rows.items() if ds in sets and (it["closed"] or not closed_only)})
    out = []
    for run, label in runs.items():
        acc = defaultdict(lambda: [0.0, 0.0])
        found = False
        for ds in sets:
            g = grades(ds, run)
            if g is None:
                continue
            found = True
            for (d, iid), it in rows.items():
                if d != ds or (closed_only and not it["closed"]) or g.get(iid, {}).get("filtered"):
                    continue
                if iid not in g:
                    continue
                acc[it[key]][0] += float(g[iid]["points"])
                acc[it[key]][1] += it["max"]
        if found:
            out.append((label, run, {c: acc[c] for c in cats}))
    return cats, out


def md(cats, out, title):
    lines = [f"### {title}", "", "| przebieg | " + " | ".join(cats) + " | razem |", "|---" * (len(cats) + 2) + "|"]
    for label, run, acc in out:
        tot = [sum(v[0] for v in acc.values()), sum(v[1] for v in acc.values())]
        cell = lambda v: f"{100 * v[0] / v[1]:.0f}% ({v[0]:g}/{v[1]:g})" if v[1] else "—"
        lines.append(f"| {label} | " + " | ".join(cell(acc[c]) for c in cats) + f" | **{cell(tot)}** |")
    return "\n".join(lines) + "\n"


def report08():
    items = load()
    main_items = {k: v for k, v in items.items() if k[0] in MAIN}
    parts = ["# 08 — Wyniki według typu zadania i zagadnienia (tabele generowane)", "",
             "Wygenerowane przez `eval/analyze.py`. Komórka = procent punktów (zdobyte/maksymalne). "
             "Otwarte i eseje: tylko przebiegi oceniane przez `gpt-6-luna`. Zamknięte: ocena automatyczna, więc także stare przebiegi. "
             "Zadanie 2024/21 (odrzucone przez filtr treści sędziego) pominięte.", ""]

    counts = defaultdict(lambda: defaultdict(float))
    for it in main_items.values():
        counts["sub"][it["sub"]] += it["max"]
        counts["epoch"][it["epoch"]] += it["max"]
        counts["pl"][it["pl"]] += it["max"]
    parts.append("## Skład arkuszy 2024 + 2025 (punkty)\n")
    for k, name in (("sub", "typ"), ("epoch", "epoka"), ("pl", "zakres")):
        parts.append(f"- **{name}:** " + ", ".join(f"{c} {v:g}" for c, v in sorted(counts[k].items())))
    parts.append("")

    parts.append("## A. Arkusze 2024 + 2025, przebiegi oceniane lunką\n")
    for key, title in (("sub", "Typ zadania"), ("epoch", "Epoka (z dat w poleceniu i źródłach grupy; esej osobno)"),
                       ("pl", "Historia Polski vs powszechna"), ("img", "Zadanie z obrazem (True) vs bez (False)")):
        rows = main_items
        if key == "img":
            rows = {k: {**v, "img": "z obrazem" if v["img"] else "bez obrazu"} for k, v in main_items.items()}
        cats, out = table(rows, LUNA_RUNS, key, MAIN)
        parts.append(md(cats, out, title))

    parts.append("## B. T1 na wszystkich arkuszach (2024, 2025, 2026, mock 2023)\n")
    t1 = {k: v for k, v in LUNA_RUNS.items() if k.startswith("gemma4")}
    for key, title in (("sub", "Typ zadania"), ("epoch", "Epoka")):
        cats, out = table(items, t1, key, SETS)
        parts.append(md(cats, out, title))

    parts.append("## C. Zamknięte (ocena automatyczna), 2024 + 2025 — także stare przebiegi i gołe bazy\n")
    cats, out = table(main_items, {**CLOSED_ONLY, **LUNA_RUNS}, "sub", MAIN, closed_only=True)
    parts.append(md(cats, out, "Zamknięte według typu"))

    parts.append("## D. Wpływ myślenia na zamknięte (te same modele, ocena automatyczna)\n")
    lines = ["| zbiór | model | bez myślenia | z myśleniem |", "|---|---|---|---|"]
    for ds, off, on, name in THINK_PAIRS:
        vals = []
        for run in (off, on):
            g = grades(ds, run)
            pts = mx = 0.0
            for (d, iid), it in items.items():
                if d == ds and it["closed"] and g and iid in g:
                    pts += float(g[iid]["points"])
                    mx += it["max"]
            vals.append(f"{100 * pts / mx:.0f}% ({pts:g}/{mx:g})" if mx else "—")
        lines.append(f"| {ds} | {name} | {vals[0]} | {vals[1]} |")
    parts.append("\n".join(lines) + "\n")

    parts.append("## E. Najtrudniejsze zadania 2024 + 2025 (średni odsetek punktów w przebiegach T1–T3 ocenianych lunką)\n")
    per_item = defaultdict(list)
    runs_for_hard = [r for r in LUNA_RUNS if r.startswith(("gemma4", "pllum-12b-base-sft__fix", "q35-4b-q4-think-fb"))]
    with open(ROOT / "results" / "item_scores.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["dataset", "id", "subtype", "epoch", "scope", "image", "max", "run", "points"])
        for (ds, iid), it in main_items.items():
            for run in LUNA_RUNS:
                g = grades(ds, run)
                if g and iid in g and not g[iid].get("filtered"):
                    w.writerow([ds, iid, it["sub"], it["epoch"], it["pl"], it["img"], it["max"], run, g[iid]["points"]])
                    if run in runs_for_hard:
                        per_item[(ds, iid)].append(float(g[iid]["points"]) / it["max"])
    hard = sorted(((statistics.mean(v), k) for k, v in per_item.items() if len(v) >= 3))[:20]
    lines = ["| zbiór | zadanie | typ | epoka | obraz | średnio |", "|---|---|---|---|---|---|"]
    for m, (ds, iid) in hard:
        it = items[(ds, iid)]
        lines.append(f"| {ds[4:8]} | {iid} | {it['sub']} | {it['epoch']} | {'tak' if it['img'] else 'nie'} | {100 * m:.0f}% |")
    parts.append("\n".join(lines) + f"\n\nPrzebiegi do średniej: {', '.join(runs_for_hard)}. Pełne dane per zadanie: `results/item_scores.csv`.\n")

    out = ROOT / "raports" / "08-wyniki-tabele.md"
    out.write_text("\n".join(parts), encoding="utf-8")
    print(out)


def run_debug_stats(ds, run):
    """Statystyki przebiegu z debug.jsonl (myślenie, powtórki, urwania, tokeny, czas)."""
    f = ROOT / "runs" / ds / run / "debug.jsonl"
    if not f.exists():
        return None
    rows = [json.loads(l) for l in open(f, encoding="utf-8")]
    think = [r for r in rows if r.get("think")]
    return {"n": len(rows), "think": len(think),
            "reasoning_chars": statistics.median([r.get("reasoning_chars", 0) for r in think]) if think else 0,
            "empty_reasoning": sum(1 for r in think if not r.get("reasoning_chars")),
            "fallback": sum(bool(r.get("fallback")) for r in rows), "truncated": sum(r.get("finish_reason") == "length" for r in rows),
            "completion_tokens": sum((r.get("usage") or {}).get("completion_tokens", 0) for r in rows),
            "seconds": round(sum(r.get("seconds", 0) for r in rows))}


def total(g, items, ds, need_all=False):
    """Punkty i maksimum na ocenionych zadaniach; przy need_all zwraca (0, 0), gdy nie wszystkie zadania mają ocenę."""
    pts = mx = 0.0
    n_items = n_graded = 0
    for (d, iid), it in items.items():
        if d != ds or (g or {}).get(iid, {}).get("filtered"):
            continue
        n_items += 1
        if iid in (g or {}):
            n_graded += 1
            pts += float(g[iid]["points"])
            mx += it["max"]
    if need_all and n_graded < n_items:
        return 0.0, 0.0
    return pts, mx


def report_registry(reg_path, out_path):
    """Raport „przed / po” z rejestru przebiegów (paczki v2, jeden sędzia): wyniki, różnice per kategoria, myślenie, dane."""
    reg = json.loads(Path(reg_path).read_text(encoding="utf-8"))
    main_sets, confirm = reg["main_sets"], reg.get("confirm_sets", [])
    items = load(main_sets + confirm)
    main_items = {k: v for k, v in items.items() if k[0] in main_sets}
    runs = {r: c["label"] for r, c in reg["runs"].items()}
    parts = [f"# {reg.get('title', 'Porównanie przebiegów')}", "", reg.get("intro", ""), ""]

    parts.append(f"## A. Wyniki łączne ({' + '.join(main_sets)}; potwierdzenie: {', '.join(confirm) or '—'})\n")
    lines = ["| track | przebieg | rozmiar [GB] | wynik główny | przyrost vs baza | potwierdzenie | stan |", "|---|---|---|---|---|---|---|"]
    scores = {}
    for run, cfg in reg["runs"].items():
        pts = mx = 0.0
        complete = True
        for ds in main_sets:
            p_, m_ = total(grades(ds, run), items, ds, need_all=True)
            complete = complete and m_ > 0
            pts, mx = pts + p_, mx + m_
        scores[run] = 100 * pts / mx if mx and complete else None
    for run, cfg in reg["runs"].items():
        sc = scores[run]
        conf = []
        for ds in confirm:
            p_, m_ = total(grades(ds, run), items, ds, need_all=True)
            conf.append(f"{100 * p_ / m_:.1f}%" if m_ else "—")
        base = cfg.get("baseline")
        delta = f"{sc - scores[base]:+.1f} pp" if base and sc is not None and scores.get(base) is not None else ""
        full = sc is not None
        lines.append(f"| {cfg.get('track', '')} | {cfg['label']} | {cfg.get('size_gb', '')} | "
                     f"{f'{sc:.1f}%' if sc is not None else '—'} | {delta} | {', '.join(conf) or '—'} | {'pełny' if full else 'niepełny'} |")
    parts.append("\n".join(lines) + "\n")

    parts.append("## B. Wyniki według kategorii\n")
    for key, title in (("sub", "Typ zadania"), ("epoch", "Epoka"), ("pl", "Historia Polski vs powszechna"), ("img", "Obraz")):
        rows = main_items
        if key == "img":
            rows = {k: {**v, "img": "z obrazem" if v["img"] else "bez obrazu"} for k, v in main_items.items()}
        cats, out = table(rows, runs, key, main_sets)
        parts.append(md(cats, out, title))

    parts.append("## C. Porównania przed / po (różnica w punktach procentowych)\n")
    for cmp in reg.get("compare", []):
        b, a = cmp["before"], cmp["after"]
        lines = [f"### {cmp['title']}: {runs.get(b, b)} → {runs.get(a, a)}", "", "| kategoria | przed | po | różnica |", "|---|---|---|---|"]
        for key in ("sub", "epoch", "pl"):
            cats, out = table(main_items, {b: "przed", a: "po"}, key, main_sets)
            accs = {lab: acc for lab, _, acc in out}
            for c in cats:
                vb, va = accs.get("przed", {}).get(c, [0, 0]), accs.get("po", {}).get(c, [0, 0])
                if vb[1] and va[1]:
                    pb, pa = 100 * vb[0] / vb[1], 100 * va[0] / va[1]
                    lines.append(f"| {c} | {pb:.0f}% | {pa:.0f}% | {pa - pb:+.0f} pp |")
        better = worse = 0
        for ds in main_sets:
            gb, ga = grades(ds, b) or {}, grades(ds, a) or {}
            for (d, iid), it in items.items():
                if d == ds and iid in gb and iid in ga:
                    diff = float(ga[iid]["points"]) - float(gb[iid]["points"])
                    better += diff > 0
                    worse += diff < 0
        lines.append(f"\nZadania lepsze: {better}, gorsze: {worse}.\n")
        parts.append("\n".join(lines))

    parts.append("## D. Myślenie, powtórki i koszt czasu (z debug.jsonl)\n")
    lines = ["| przebieg | zbiór | z myśleniem | mediana znaków myślenia | puste myślenie | powtórki | urwane | tokeny wyjścia | czas [s] |",
             "|---|---|---|---|---|---|---|---|---|"]
    for run, lab in runs.items():
        for ds in main_sets:
            st = run_debug_stats(ds, run)
            if st:
                lines.append(f"| {lab} | {ds} | {st['think']}/{st['n']} | {st['reasoning_chars']:.0f} | {st['empty_reasoning']} | "
                             f"{st['fallback']} | {st['truncated']} | {st['completion_tokens']} | {st['seconds']} |")
    parts.append("\n".join(lines) + "\n")

    man = ROOT / reg.get("data_manifest", "data/sft/v2/manifest.jsonl")
    if man.exists():
        rows = [json.loads(l) for l in open(man, encoding="utf-8")]
        parts.append(f"## E. Dane SFT v2 ({len(rows)} przykładów)\n")
        for key in ("origin", "task", "kind", "epoch", "scope", "rag_mode", "has_rationale"):
            c = defaultdict(int)
            for r in rows:
                c[str(r.get(key))] += 1
            parts.append(f"- **{key}:** " + ", ".join(f"{k} {v}" for k, v in sorted(c.items(), key=lambda x: -x[1])))
        parts.append("")
    Path(out_path).write_text("\n".join(parts), encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", help="rejestr przebiegów (JSON); bez niego raport 08 jak dotąd")
    ap.add_argument("--out", default="raports/09-zmiany-po-treningach.md")
    args = ap.parse_args()
    if args.registry:
        report_registry(args.registry, ROOT / args.out)
    else:
        report08()

