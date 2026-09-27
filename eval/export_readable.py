"""Czytelna wersja arkuszy z wzorowymi odpowiedziami (do przeglądu przez człowieka).

    python eval/export_readable.py      # -> eval/data/readable/<zbiór>.md
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "eval" / "data"


def main():
    out_dir = DATA / "readable"
    out_dir.mkdir(exist_ok=True)
    for f in sorted(DATA.glob("*.jsonl")):
        rows = [json.loads(l) for l in open(f)]
        md = [f"# {f.stem} — {len(rows)} zadań, {sum(r['max_points'] for r in rows)} pkt\n"]
        for r in rows:
            md += [f"\n## Zadanie {r['id']} ({r['max_points']} pkt, {r['type']})"]
            if r.get("sources"):
                md += ["**Źródła:**", "```", r["sources"], "```"]
            for img in r.get("images", []):
                md += [f"![{r['id']}](../../../{img})"]
            md += ["**Polecenie:**", r["question"], "", "**Wzorowa odpowiedź:**", "```", r.get("model_answer") or "(esej — oceniany wg kryteriów CKE)", "```",
                   "<details><summary>Zasady oceniania i rozwiązanie CKE</summary>", "", r.get("rubric", ""), "", r.get("solution", ""), "</details>"]
        (out_dir / f"{f.stem}.md").write_text("\n".join(md))
        print("written", out_dir / f"{f.stem}.md")


if __name__ == "__main__":
    main()
