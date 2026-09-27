"""Wyciąga tekst, rendery stron i wycinki obrazów z pobranych PDF-ów CKE.

Wynik dla każdego PDF: data/cke/extracted/<formula>/<nazwa>/
  pages.json            tekst każdej strony
  page-XX.png           render strony (tylko arkusze i karty, 150 dpi)
  images.json + img-*.png  osadzone obrazy wycięte z renderu 200 dpi (z bbox)
"""

import json
import sys
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "cke" / "raw"
OUT = ROOT / "data" / "cke" / "extracted"
MIN_IMG_PX = 120  # pomija ikonki, logotypy i ramki


def extract(rec):
    pdf = ROOT / rec["path"]
    dest = OUT / rec["formula"] / pdf.stem
    if (dest / "pages.json").exists():
        return "skip"
    dest.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(pdf)
    pages = [{"page": i + 1, "text": p.get_text()} for i, p in enumerate(doc)]
    (dest / "pages.json").write_text(json.dumps(pages, ensure_ascii=False, indent=1))
    if rec["kind"] not in ("arkusz", "karta"):
        return f"text-only {len(pages)}p"
    images = []
    for i, page in enumerate(doc):
        page.get_pixmap(dpi=150).save(dest / f"page-{i + 1:02d}.png")
        seen = set()
        for k, info in enumerate(page.get_image_info(xrefs=True)):
            x0, y0, x1, y1 = info["bbox"]
            w_pt, h_pt = x1 - x0, y1 - y0
            if w_pt * 200 / 72 < MIN_IMG_PX or h_pt * 200 / 72 < MIN_IMG_PX:
                continue
            key = tuple(round(v) for v in info["bbox"])
            if key in seen:
                continue
            seen.add(key)
            clip = pymupdf.Rect(info["bbox"]) & page.rect
            name = f"img-p{i + 1:02d}-{k:02d}.png"
            page.get_pixmap(dpi=200, clip=clip).save(dest / name)
            images.append({"file": name, "page": i + 1, "bbox": [round(v, 1) for v in clip]})
    (dest / "images.json").write_text(json.dumps(images, ensure_ascii=False, indent=1))
    return f"{len(pages)}p {len(images)}img"


def main():
    manifest = RAW / "manifest.jsonl"
    recs = [json.loads(l) for l in manifest.open()]
    for rec in recs:
        try:
            print(rec["path"], extract(rec), flush=True)
        except Exception as e:  # uszkodzony PDF nie może zatrzymać całej nocy
            print("ERR", rec["path"], e, flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    sys.exit(main())
