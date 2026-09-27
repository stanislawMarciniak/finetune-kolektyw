"""Offline go/no-go dla wyszukiwania podobnych obrazów (raport 23): top-k podpisów dla każdego obrazu z paczek testowych.

  python eval/img_retrieval_eval.py --index data/imgret/idx_dino --exams exams/test2024_v2 exams/test2025_v2 exams/test2026_v2 \
      --out results/imgret_eval_dino.jsonl
"""
import argparse, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
from img_retrieval import Index  # noqa: E402


def src_title(item, path):
    lines = item.get("source_text", "").split("\n")
    marker = f"[Obraz: {path}]"
    at = next((i for i, l in enumerate(lines) if marker in l), None)
    if at is None:
        return ""
    for l in reversed(lines[max(0, at - 6):at]):
        if l.strip() and "[Obraz:" not in l:
            return l.strip()[:120]
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", required=True)
    ap.add_argument("--exams", nargs="+", required=True)
    ap.add_argument("-k", type=int, default=3)
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default=None)
    a = ap.parse_args()
    idx = Index(a.index, a.device or "cuda")
    rows = []
    for ex in a.exams:
        ex = Path(ex)
        d = json.load((ex / "exam.json").open())
        for it in d["items"]:
            for im in it.get("images", []):
                rows.append({"exam": d["exam_id"], "id": it["id"], "path": im["path"], "title": src_title(it, im["path"]),
                             "q": it["question"][:160].replace("\n", " "), "file": str(ex / im["path"])})
    hits = idx.search([r["file"] for r in rows], a.k)
    with open(a.out, "w") as f:
        for r, h in zip(rows, hits):
            r["hits"] = h
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    sims = sorted(h[0]["sim"] for h in hits if h)
    print(f"{len(rows)} obrazów; top1 sim: min {sims[0]:.2f} med {sims[len(sims)//2]:.2f} max {sims[-1]:.2f}")


if __name__ == "__main__":
    main()
