"""Zamienia wynik harnessu (runs/<zbiór>/<przebieg>/debug.jsonl) na format oceniania (results/<zbiór>/<przebieg>.jsonl).

    python harness/to_results.py runs/test2024_split/q35-4b-hyde [--dataset test2024_split]
Egzamin próbny (history-2023-mock-v1) oceniamy kluczem z dev2023_img (te same ID i klucze).
"""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALIASES = {"mock-2023": "dev2023_img"}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("run_dir")
    p.add_argument("--dataset")
    a = p.parse_args()
    run_dir = Path(a.run_dir)
    dataset = a.dataset or ALIASES.get(run_dir.parent.name, run_dir.parent.name)
    dest = ROOT / "results" / dataset
    dest.mkdir(parents=True, exist_ok=True)
    items = {json.loads(l)["id"]: json.loads(l) for l in open(ROOT / "eval" / "data" / f"{dataset}.jsonl")}
    with open(dest / f"{run_dir.name}.jsonl", "w", encoding="utf-8") as f:
        for l in open(run_dir / "debug.jsonl", encoding="utf-8"):
            r = json.loads(l)
            it = items.get(r["id"], {})
            f.write(json.dumps({"id": r["id"], "type": it.get("type"), "max_points": it.get("max_points"),
                                "answer": r["answer"], "finish_reason": r["finish_reason"], "error": r.get("error")},
                               ensure_ascii=False) + "\n")
    print(dest / f"{run_dir.name}.jsonl")


if __name__ == "__main__":
    main()
