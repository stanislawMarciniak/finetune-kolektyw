"""Konwertuje arkusz CKE (formuła 2023) + zasady oceniania do formatu jak na finale:
tekst polecenia i źródeł osobno, obrazy źródeł jako osobne wycinki PNG.

    python eval/build_exam.py 2024     # oczekuje assets/cke/2024/{arkusz,zasady}.pdf
Wynik: eval/data/test2024_split.jsonl + eval/data/img/2024/*.png
"""

import json
import re
import sys
from pathlib import Path

import pymupdf

from cke_parse import parse_zasady
from items import classify, format_key, key_type, make_model_answer, parse_key

ROOT = Path(__file__).resolve().parents[1]
HEAD = re.compile(r"^Zadanie\s+(\d+)(?:\.(\d+))?\.?\s*(?:\((0\s*[–-]\s*(\d+))\))?\s*$")
VERBS = ("Rozstrzygnij", "Podaj", "Wyjaśnij", "Oceń", "Zaznacz", "Porównaj", "Wymień", "Przyporządkuj", "Uzupełnij",
         "Określ", "Wskaż", "Scharakteryzuj", "Dokończ", "Napisz", "Przedstaw", "Uzasadnij", "Sformułuj", "Rozpoznaj",
         "Wybierz", "Przeanalizuj", "Zidentyfikuj", "Ustal", "Wpisz", "Odwołując", "Na podstawie ", "Które", "Który",
         "Która", "Czy ", "Zadanie zawiera", "Wykaż", "Opisz", "Nazwij")
DROP = [re.compile(p) for p in (
    r"^\s*Strona \d+ z \d+\s*$", r"^\s*MHIP-R0[_-]100\s*$", r"^\s*\.{5,}.*$", r"^\s*[•·]\s*$",
    r"^\s*\d+(\.\d+)?\.\s*$", r"^\s*0\s*[–-]\s*\d+\s*$", r"^\s*0\s*[–-]\s*1\s*[–-](\s*\d\s*[–-]?)*\s*$",
    r"^\s*\d\s*[–-]\s*\d\s*$", r"^\s*[PF]\s*$", r"^\s*$", r"^\s*BRUDNOPIS.*$",
    r"^\s*\(nie podlega ocenie\)\s*$", r"^\s*Wypełnia\s*$", r"^\s*egzaminator\s*$")]
MIN_PX = 140


def lines_and_images(doc):
    stream = []
    for pno, page in enumerate(doc):
        d = page.get_text("dict")
        for b in d["blocks"]:
            if b["type"] != 0:
                continue
            for ln in b["lines"]:
                txt = "".join(s["text"] for s in ln["spans"]).rstrip()
                if txt.strip():
                    stream.append(("t", pno, ln["bbox"][1], ln["bbox"][0], txt))
        for info in page.get_image_info(xrefs=True):
            x0, y0, x1, y1 = info["bbox"]
            if (x1 - x0) * 200 / 72 >= MIN_PX and (y1 - y0) * 200 / 72 >= MIN_PX:
                stream.append(("i", pno, y0, x0, tuple(info["bbox"])))
    stream.sort(key=lambda e: (e[1], round(e[2]), e[3]))
    return stream


def merge_images(boxes):
    """Scala nakładające się / stykające się bboxy z tej samej strony (np. mapa z legendą)."""
    boxes = [list(b) for b in boxes]
    merged = True
    while merged:
        merged = False
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b = boxes[i], boxes[j]
                if a[0] <= b[2] + 6 and b[0] <= a[2] + 6 and a[1] <= b[3] + 6 and b[1] <= a[3] + 6:
                    boxes[i] = [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]
                    boxes.pop(j)
                    merged = True
                    break
            if merged:
                break
    return boxes


def clean(lines):
    out = []
    for l in lines:
        if any(rx.match(l) for rx in DROP):
            continue
        l = re.sub(r"\.{4,}", "", l).rstrip()
        out.append(l.strip())
    text = "\n".join(out)
    return re.sub(r"\n{2,}", "\n", text).strip()


def split_command(text):
    lines = text.split("\n")
    for i, l in enumerate(lines):
        if l.startswith(VERBS):
            return "\n".join(lines[:i]).strip(), "\n".join(lines[i:]).strip()
    return "", text.strip()


def build(year):
    base = ROOT / "assets" / "cke" / str(year)
    doc = pymupdf.open(base / "arkusz.pdf")
    zasady_text = "\n".join(p.get_text() for p in pymupdf.open(base / "zasady.pdf"))
    zasady = parse_zasady(zasady_text)
    img_dir = ROOT / "eval" / "data" / "img" / str(year)
    img_dir.mkdir(parents=True, exist_ok=True)

    # segmentacja strumienia na nagłówki zadań
    segs, cur = [], None
    for e in lines_and_images(doc):
        m = HEAD.match(e[4]) if e[0] == "t" else None
        if m:
            cur = {"group": m.group(1), "sub": m.group(2), "pts": m.group(4), "lines": [], "images": []}
            segs.append(cur)
            continue
        if cur is None:
            continue
        if e[0] == "t":
            cur["lines"].append(e[4])
        else:
            cur["images"].append((e[1], e[4]))

    items, group_ctx = [], {}
    for s in segs:
        if s["pts"] is None:  # nagłówek grupy: wspólne źródła
            group_ctx[s["group"]] = s
            continue
        iid = s["group"] + (f".{s['sub']}" if s["sub"] else "")
        own = clean(s["lines"])
        if s["pts"] == "15":
            own = own.split("\nWYPRACOWANIE")[0].strip()
        pre, command = split_command(own)
        g = group_ctx.get(s["group"]) if s["sub"] else None
        sources = "\n".join(x for x in [clean(g["lines"]) if g else "", pre] if x).strip()
        imgs = [] if s["pts"] == "15" else (g["images"] if g else []) + s["images"]
        files = []
        by_page = {}
        for pno, bbox in imgs:
            by_page.setdefault(pno, []).append(bbox)
        k = 0
        for pno, boxes in sorted(by_page.items()):
            for bb in merge_images(boxes):
                name = f"{iid}-{k}.png"
                clip = pymupdf.Rect(bb) & doc[pno].rect
                doc[pno].get_pixmap(dpi=200, clip=clip).save(img_dir / name)
                files.append(f"eval/data/img/{year}/{name}")
                k += 1
        z = zasady.get(iid, {})
        key = parse_key(z.get("solution", "")) if z else None
        qtype = "essay" if s["pts"] == "15" else (key_type(key, command) if key else classify(command))
        sol = re.sub(r"^Rozwiązani[ae]\s*\n", "", z.get("solution", "")).strip()
        items.append({"exam": f"{year}-05", "id": iid, "max_points": int(s["pts"]), "type": qtype,
                      "question": command, "sources": sources, "images": files, "key": key,
                      "auto_gradable": key is not None,
                      "rubric": z.get("rubric", "") if qtype != "essay" else "KRYTERIA_ESEJU_CKE",
                      "solution": sol, "model_answer": make_model_answer(sol, key, command) if qtype != "essay" else ""})
    overrides = json.load(open(ROOT / "eval" / "model_answer_overrides.json"))
    for it in items:
        if f"{year}:{it['id']}" in overrides:
            it["model_answer"] = overrides[f"{year}:{it['id']}"]
    out = ROOT / "eval" / "data" / f"test{year}_split.jsonl"
    with open(out, "w") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    tot = sum(i["max_points"] for i in items)
    missing = [i["id"] for i in items if not i["rubric"]]
    print(f"{year}: {len(items)} items, {tot} pts, zasady items {len(zasady)} ({sum(v['max_points'] for v in zasady.values())} pts), "
          f"images {sum(len(i['images']) for i in items)}, no-rubric {missing}")
    return items


if __name__ == "__main__":
    for y in sys.argv[1:] or ["2024", "2025", "2026"]:
        build(int(y))
