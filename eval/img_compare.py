"""Raport 15: porównanie przebiegów na zadaniach z obrazami (oceny auto + sędzia z results/grades).
    python eval/img_compare.py "base:runA,runB" "cand:runC,runD" [--sets test2024_v2,test2025_v2,test2026_v2] [--items]
Przebieg może mieć inny katalog bazowy na zbiorze: "run@test2026_v2=inny".
"""
import argparse
import json
from pathlib import Path

G = Path("results/grades")
EXCL = {("test2024_v2", "21")}


def load(ds, run):
    pts = {}
    for kind in ("auto", "judge"):
        f = G / ds / f"{run}.{kind}.json"
        if f.exists():
            for k, v in json.loads(f.read_text()).items():
                if v.get("points") is not None:
                    pts[k] = v["points"]
    return pts


def main():
    p = argparse.ArgumentParser()
    p.add_argument("groups", nargs="+")
    p.add_argument("--sets", default="test2024_v2,test2025_v2,test2026_v2")
    p.add_argument("--items", action="store_true")
    a = p.parse_args()
    groups = []
    for g in a.groups:
        name, runs = g.split(":", 1)
        groups.append((name, runs.split(",")))
    for ds in a.sets.split(","):
        exam = json.loads(Path(f"exams/{ds}/exam.json").read_text())
        items = [i for i in exam["items"] if (ds, i["id"]) not in EXCL]
        img = [i["id"] for i in items if i.get("images")]
        maxp = {i["id"]: i["max_points"] for i in items}
        tot_max, img_max = sum(maxp.values()), sum(maxp[i] for i in img)
        per = {}
        for name, runs in groups:
            per[name] = []
            for r in runs:
                r = dict(x.split("=") for x in r.split("@")[1:]).get(ds, r.split("@")[0])
                s = load(ds, r)
                miss = [i for i in maxp if i not in s]
                per[name].append((r, s, miss))
        print(f"== {ds}: obrazy {len(img)} zadań / {img_max} pkt (arkusz {tot_max})")
        for name, lst in per.items():
            ims = [sum(s.get(i, 0) for i in img) for _, s, _ in lst]
            tots = [100 * sum(s.get(i, 0) for i in maxp) / tot_max for _, s, _ in lst]
            miss = sum(len(m) for _, _, m in lst)
            print(f"  {name:8s} obrazy: {' / '.join(f'{x:g}' for x in ims)} (śr. {sum(ims) / len(ims):.2f})  "
                  f"arkusz %: {' / '.join(f'{x:.1f}' for x in tots)}" + (f"  BRAK ocen: {miss}" if miss else ""))
        if a.items:
            for i in img:
                row = {name: [s.get(i, "-") for _, s, _ in lst] for name, lst in per.items()}
                vals = list(row.values())
                if any(v != vals[0] for v in vals[1:]) and any(
                        sum(x for x in v if x != "-") / len(v) != sum(x for x in vals[0] if x != "-") / len(vals[0]) for v in vals[1:]):
                    print(f"    {i:5s} /{maxp[i]}: " + "  ".join(f"{n}={v}" for n, v in row.items()))


if __name__ == "__main__":
    main()
