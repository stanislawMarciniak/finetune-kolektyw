"""Przed sędzią: kopiuje oceny dla odpowiedzi identycznych (po normalizacji białych znaków) z już ocenionymi w innych
przebiegach tego samego zbioru. Oszczędza koszt przy przebiegach deterministycznych (T2, temp. 0) i przy
przebiegach --only-ids --merge-from (np. tylko eseje).

    python eval/judge_reuse.py --only "__nt"
"""
import argparse
import json
from pathlib import Path

RES = Path(__file__).resolve().parents[1] / "results"


def norm(s):
    return " ".join((s or "").split())


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--only", required=True, help="filtr przebiegów do uzupełnienia (jak w judge_openai.py)")
    args = p.parse_args()
    pats = args.only.split(",")
    total = 0
    for dsdir in sorted((RES / "grades").iterdir()):
        ds = dsdir.name
        known = {}
        for jf in dsdir.glob("*.judge.json"):
            run = jf.name.removesuffix(".judge.json")
            af = RES / ds / f"{run}.jsonl"
            if not af.exists():
                continue
            grades = json.load(open(jf))
            for l in open(af, encoding="utf-8"):
                r = json.loads(l)
                g = grades.get(r["id"])
                if g and not g.get("reused_from") and g.get("points") is not None:
                    known.setdefault((r["id"], norm(r["answer"])), (run, g))
        for af in dsdir.glob("*.auto.json"):
            run = af.name.removesuffix(".auto.json")
            if not any(s in f"{ds}/{run}" for s in pats):
                continue
            auto = json.load(open(af))
            jf = dsdir / f"{run}.judge.json"
            done = json.load(open(jf)) if jf.exists() else {}
            added = 0
            for l in open(RES / ds / f"{run}.jsonl", encoding="utf-8"):
                r = json.loads(l)
                if r["id"] in auto or r["id"] in done:
                    continue
                hit = known.get((r["id"], norm(r["answer"])))
                if hit and hit[0] != run:
                    done[r["id"]] = {**hit[1], "reused_from": hit[0]}
                    added += 1
            if added:
                jf.write_text(json.dumps(done, ensure_ascii=False, indent=1))
                total += added
                print(f"{ds}/{run}: +{added}")
    print("reused", total)


if __name__ == "__main__":
    main()
