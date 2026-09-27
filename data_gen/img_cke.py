"""Obrazy z dawnych arkuszy CKE (bez 2024/2025/2026 — to zbiory testowe) z podpisem z tekstu strony nad/pod obrazem.

Wejście: data/cke/extracted/<formuła>/<dok>/images.json (page, bbox) + PDF w data/cke/raw. Wyjście jak img_commons.py:
OUT/imgs/<n>.jpg + OUT/meta.jsonl. Raport 23.

  python data_gen/img_cke.py --out data/imgret/cke
"""
import argparse, json, re
from pathlib import Path

import pymupdf
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
EXCL = re.compile(r"2405|2505|2605|EM202[456]")
SRC = re.compile(r"^(Źródło|Zadanie|Mapa|Fotografia|Plakat|Rysunek|Karykatura|Obraz|Moneta|Znaczek|Ilustracja|Schemat|"
                 r"Plan|Grafika|Portret|Pomnik|Medal|Herb|Pieczęć|Tabela|Wykres|Fragment|Na podstawie|Poprawna|Przykładowe)",
                 re.I)


def caption(page, bbox, above=140, below=70):
    x0, y0, x1, y1 = bbox
    lines = []
    for b in page.get_text("blocks"):
        bx0, by0, bx1, by1, txt = b[:5]
        if bx1 < x0 - 150 or bx0 > x1 + 150:
            continue
        if y0 - above <= by1 <= y0 + 5 or y1 - 5 <= by0 <= y1 + below:
            t = re.sub(r"\s+", " ", txt).strip()
            if t and not re.fullmatch(r"[\d\s.,/|–-]*", t) and "Strona" not in t[:8]:
                lines.append((by0, t))
    lines.sort()
    txt = " ".join(t for _, t in lines)
    return txt[:500]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "data/imgret/cke"))
    ap.add_argument("--min-side", type=int, default=90)
    a = ap.parse_args()
    out = Path(a.out); (out / "imgs").mkdir(parents=True, exist_ok=True)
    recs, n = [], 0
    for ij in sorted((ROOT / "data/cke/extracted").glob("*/*/images.json")):
        doc_dir = ij.parent
        form, name = doc_dir.parent.name, doc_dir.name
        if EXCL.search(name):
            continue
        pdf = ROOT / "data/cke/raw" / form / f"{name}.pdf"
        doc = pymupdf.open(pdf) if pdf.exists() else None
        for im in json.load(ij.open()):
            p = doc_dir / im["file"]
            try:
                img = Image.open(p).convert("RGB")
            except Exception:
                continue
            if min(img.size) < a.min_side:
                continue
            cap = ""
            if doc is not None and 1 <= im["page"] <= len(doc):
                cap = caption(doc[im["page"] - 1], im["bbox"])
            img.thumbnail((512, 512))
            img.save(out / "imgs" / f"{n}.jpg", quality=88)
            kind = "historia sztuki" if form == "art" else "historia"
            recs.append({"id": n, "file": f"imgs/{n}.jpg", "title": f"CKE {name} s.{im['page']}",
                         "name": f"Arkusz CKE ({kind}) {name}", "objname": "", "desc": cap, "date": "", "cat": f"cke/{form}"})
            n += 1
    with (out / "meta.jsonl").open("w") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("obrazy CKE:", n)


if __name__ == "__main__":
    main()
