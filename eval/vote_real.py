"""Przebiegi z --vote-closed: pierwsza próbka vs wynik głosowania (sparowane), czas zamkniętych (raport 19).

    python eval/vote_real.py runs/test2024_v2/gemma4-qat__vote5-s47 [...]
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vote_sim import ROOT, parts, pts  # noqa: E402


def main(dirs):
    for d in map(Path, dirs):
        ds = d.parent.name
        items = {json.loads(l)["id"]: json.loads(l) for l in open(ROOT / "eval/data" / f"{ds}.jsonl")}
        recs = [json.loads(l) for l in open(d / "debug.jsonl", encoding="utf-8")]
        meta = json.load(open(d / "meta.json"))["summary"]
        s1 = sv = n = 0
        rows = []
        for r in recs:
            it = items.get(r["id"])
            if not (it and it.get("key") and r.get("vote")):
                continue
            smp = r["vote"]["samples"]
            a, b = pts(it, parts(it, smp[0])), pts(it, parts(it, r["answer"]))
            s1, sv, n = s1 + a, sv + b, n + 1
            rows.append(f"  {r['id']:5} {len(smp)} próbek, {r['seconds']:6.0f} s, {r['usage']['completion_tokens']:6} tok: "
                        f"{a} → {b}  {[x.replace(chr(10), ' ') for x in smp]}")
        other = [r for r in recs if not (items.get(r["id"], {}).get("key"))]
        print(f"{ds}/{d.name}: zamknięte {n}, pierwsza próbka {s1} → głos {sv} pkt ({sv - s1:+d}); "
              f"wall {meta['wall_seconds']:.0f} s, tokeny {meta['completion_tokens']}; "
              f"maks. czas zamkniętego {max((r['seconds'] for r in recs if r.get('vote')), default=0):.0f} s, "
              f"pozostałych {max((r['seconds'] for r in other), default=0):.0f} s")
        print("\n".join(rows))


if __name__ == "__main__":
    main(sys.argv[1:])
