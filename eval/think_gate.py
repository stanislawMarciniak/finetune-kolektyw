"""Bramka ochrony myślenia (WS3): porównuje przebieg sondy przed treningiem LoRA i po nim.

    python eval/think_gate.py make                       # -> exams/probe60_v2 + eval/data/probe60_v2.jsonl
    python eval/think_gate.py check runs/probe60_v2/<przed> runs/probe60_v2/<po>
Kryteria (wszystkie muszą przejść):
  1. mediana znaków myślenia (zadania z myśleniem) po >= 80% przed,
  2. puste myślenie + powtórki bez myślenia po <= przed + 2 pp,
  3. zamknięte (klucz, bez sędziego) po >= przed - 2 pp.
"""

import json
import random
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "harness"))
sys.path.insert(0, str(ROOT / "eval"))


def make():
    """60 zadań z 2024 + 2025 (v2): wszystkie zamknięte z kluczem + losowe otwarte; ID z prefiksem roku."""
    rnd = random.Random(0)
    items, data = [], []
    for year, ds in (("24", "test2024_v2"), ("25", "test2025_v2")):
        exam = json.loads((ROOT / "exams" / ds / "exam.json").read_text(encoding="utf-8"))
        rows = {json.loads(l)["id"]: json.loads(l) for l in open(ROOT / "eval" / "data" / f"{ds}.jsonl", encoding="utf-8")}
        for it in exam["items"]:
            r = rows[it["id"]]
            if r["type"] == "essay":
                continue
            new = dict(it, id=f"{year}-{it['id']}", images=[dict(im, path=f"images/{year}-{Path(im['path']).name}") for im in it["images"]],
                       source_text=it["source_text"].replace("[Obraz: images/", f"[Obraz: images/{year}-"))
            items.append((r["type"].startswith("closed") and bool(r.get("key")), new, dict(r, id=new["id"]), ds, it))
    closed = [x for x in items if x[0]]
    opened = [x for x in items if not x[0]]
    pick = closed + rnd.sample(opened, 60 - len(closed))
    dest = ROOT / "exams" / "probe60_v2"
    (dest / "images").mkdir(parents=True, exist_ok=True)
    for _, new, r, ds, orig in pick:
        for im_new, im_old in zip(new["images"], orig["images"]):
            (dest / im_new["path"]).write_bytes((ROOT / "exams" / ds / im_old["path"]).read_bytes())
        data.append(r)
    exam = {"exam_id": "probe60_v2", "title": "probe60_v2", "language": "pl", "input_format": "separate-text-and-images-v1",
            "max_points": sum(float(r["max_points"]) for r in data), "instructions": "", "items": [p[1] for p in pick]}
    (dest / "exam.json").write_text(json.dumps(exam, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(ROOT / "eval" / "data" / "probe60_v2.jsonl", "w", encoding="utf-8") as f:
        for r in data:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"probe60_v2: {len(pick)} zadań, zamkniętych {len(closed)}")


def stats(run_dir):
    from grade import grade_closed
    data = {json.loads(l)["id"]: json.loads(l) for l in open(ROOT / "eval" / "data" / "probe60_v2.jsonl", encoding="utf-8")}
    rows = [json.loads(l) for l in open(Path(run_dir) / "debug.jsonl", encoding="utf-8")]
    think = [r for r in rows if r.get("think")]
    pts = mx = 0.0
    for r in rows:
        it = data[r["id"]]
        if it["type"].startswith("closed") and it.get("key"):
            got, _ = grade_closed(it, r["answer"])
            pts += got or 0
            mx += float(it["max_points"])
    return {"median_reasoning": statistics.median([r.get("reasoning_chars", 0) for r in think]) if think else 0,
            "empty_or_fallback": 100 * sum(1 for r in think if not r.get("reasoning_chars") or r.get("fallback")) / max(1, len(think)),
            "closed": 100 * pts / mx if mx else 0}


def check(before, after):
    b, a = stats(before), stats(after)
    tests = [("mediana myślenia >= 80%", a["median_reasoning"] >= 0.8 * b["median_reasoning"]),
             ("puste/powtórki <= +2 pp", a["empty_or_fallback"] <= b["empty_or_fallback"] + 2),
             ("zamknięte >= -2 pp", a["closed"] >= b["closed"] - 2)]
    print(json.dumps({"przed": b, "po": a}, ensure_ascii=False))
    for name, ok in tests:
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
    print("GATE_PASS" if all(ok for _, ok in tests) else "GATE_FAIL")


if __name__ == "__main__":
    if sys.argv[1] == "make":
        make()
    else:
        check(sys.argv[2], sys.argv[3])
