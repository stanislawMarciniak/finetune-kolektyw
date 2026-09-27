"""Tabela wyników: łączy oceny automatyczne (zamknięte) i sędziego (otwarte, esej).

    python eval/report.py            # -> results/report.md (+ wypis na ekran)
Przebieg bez pliku .judge.json dostaje tylko punkty zamknięte i oznaczenie "otwarte: nieocenione".
"""

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
DATA = ROOT / "eval" / "data"


def main():
    rows = []
    for auto_f in sorted((RES / "grades").glob("*/*.auto.json")):
        dataset, run = auto_f.parent.name, auto_f.name.removesuffix(".auto.json")
        items = {json.loads(l)["id"]: json.loads(l) for l in open(DATA / f"{dataset}.jsonl")}
        grades = json.load(open(auto_f))
        judge_f = auto_f.with_name(f"{run}.judge.json")
        judged = judge_f.exists()
        if judged:
            grades.update(json.load(open(judge_f)))
        cat = defaultdict(lambda: [0, 0])
        missing = 0
        for iid, it in items.items():
            c = "zamknięte" if it["type"].startswith("closed") and it.get("key") else ("esej" if it["type"] == "essay" else "otwarte")
            if grades.get(iid, {}).get("filtered"):  # sędzia API odrzucił treść (filtr Azure) — pozycja poza mianownikiem
                continue
            cat[c][1] += it["max_points"]
            if iid in grades:
                cat[c][0] += grades[iid]["points"]
            else:
                missing += 1
        meta_f = RES / dataset / f"{run}.meta.json"
        meta = json.load(open(meta_f)) if meta_f.exists() else {}
        total = sum(v[0] for v in cat.values())
        maxp = sum(v[1] for v in cat.values())
        rows.append({"dataset": dataset, "run": run, "total": total, "max": maxp, "cat": dict(cat),
                     "complete": judged and missing == 0, "missing": missing,
                     "truncated": meta.get("truncated"), "wall_s": meta.get("wall_seconds"),
                     "tokens": meta.get("completion_tokens")})
    lines = ["| zbiór | przebieg | wynik | zamknięte | otwarte | esej | kompletne | ucięte | czas [s] |", "|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: (r["dataset"], -r["total"])):
        c = r["cat"]
        f = lambda k: f"{c.get(k, [0, 0])[0]}/{c.get(k, [0, 0])[1]}"
        pct = f"{100 * r['total'] / r['max']:.1f}%" if r["complete"] else f"≥{r['total']}/{r['max']} (brak {r['missing']})"
        lines.append(f"| {r['dataset']} | {r['run']} | {pct} | {f('zamknięte')} | {f('otwarte')} | {f('esej')} | "
                     f"{'tak' if r['complete'] else 'nie'} | {r['truncated']} | {r['wall_s']} |")
    (RES / "report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
