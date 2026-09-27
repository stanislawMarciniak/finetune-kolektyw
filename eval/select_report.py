"""Wynik selektora zespołu (H-H9): punkty wybranych odpowiedzi wg istniejących ocen vs pojedyncze modele i wyrocznia."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"


def grades(ds, run):
    g = json.load(open(RES / "grades" / ds / f"{run}.auto.json"))
    jf = RES / "grades" / ds / f"{run}.judge.json"
    if jf.exists():
        g.update(json.load(open(jf)))
    return {k: v["points"] for k, v in g.items()}


def main():
    lines = ["| zbiór | selektor | model A | model B | wybór | wyrocznia |", "|---|---|---|---|---|---|"]
    for f in sorted((RES / "select").glob("*/*.jsonl")):
        ds = f.parent.name
        judge, rest = f.stem.split("__", 1)
        run_a, run_b = rest.split("__VS__")
        ga, gb = grades(ds, run_a), grades(ds, run_b)
        picks = [json.loads(l) for l in open(f)]
        chosen = sum((ga if p["choice"] == run_a else gb).get(p["id"], 0) for p in picks)
        oracle = sum(max(ga.get(p["id"], 0), gb.get(p["id"], 0)) for p in picks)
        lines.append(f"| {ds} | {judge} | {sum(ga.values())} | {sum(gb.values())} | **{chosen}** | {oracle} |")
    out = "\n".join(lines)
    (RES / "select_report.md").write_text(out + "\n")
    print(out)


if __name__ == "__main__":
    main()
