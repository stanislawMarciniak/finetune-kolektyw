"""Konwersja naszych zbiorów (eval/data/test20xx_split.jsonl) do oficjalnego formatu paczki egzaminu.

    python harness/make_exam_pack.py test2024_split test2025_split test2026_split
    python harness/make_exam_pack.py --v2 test2024_split ...   # -> exams/test2024_v2 (znaczniki obrazów jak w finale)
Wynik: exams/<zbiór>/exam.json + images/ (kopie wycinków). Dzięki temu dev i finał idą tym samym harnessem.
W wersji v2 `source_text` ma znaczniki `[Obraz: images/X.png]` pod podpisem ilustracji, jak oficjalny exam.json.
"""

import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPEN_FMT = "Tekst po polsku. Podaj wszystkie wymagane elementy odpowiedzi."
ESSAY_FMT = "Jeden tekst: numer wybranego tematu i całe wypracowanie. Minimum 300 wyrazów zgodnie z poleceniem."


def answer_format(it):
    key = it.get("key")
    if it["type"] == "essay":
        return ESSAY_FMT
    if not key:
        return OPEN_FMT
    if it["type"] == "closed_tf":
        return "\n".join(f"{k}: {'P' if i % 2 == 0 else 'F'}" for i, k in enumerate(key))
    if it["type"] == "closed_match":
        return "\n".join(f"{k}: 1" for k in key)
    if list(key) == ["1"]:
        return "A"
    return "\n".join(f"{k}: A" for k in key)


CAPTION = re.compile(r"(?i)fotografi|zdjęci|\bmap[ay]\b|ilustracj|karykatur|plakat|rycin|drzeworyt|obraz|rysun|relief|monet|"
                     r"banknot|herb|schemat|wykres|kadr|grafik|pieczę|medal|znaczek|miniatur|fresk|mozaik|rzeźb|ulotk|afisz|"
                     r"okładk|strona tytułowa|plan miasta|pocztówk|mapk")


def with_markers(text, paths):
    """Wstawia `[Obraz: ...]` pod kolejnymi podpisami ilustracji; nadmiarowe obrazy trafiają pod ostatni podpis albo na koniec."""
    if not paths:
        return text
    lines = text.split("\n")
    caps = [i for i, l in enumerate(lines) if CAPTION.search(l) and len(l) < 160]
    groups = {}
    for k, path in enumerate(paths):
        at = caps[min(k, len(caps) - 1)] if caps else len(lines) - 1
        groups.setdefault(at, []).append(f"[Obraz: {path}]")
    out = []
    for i, l in enumerate(lines):
        out.append(l)
        if i in groups:
            out.extend(groups[i])
            out.append("")
    return "\n".join(out).rstrip("\n") if text else "\n".join(m for g in groups.values() for m in g)


def main(names, v2=False):
    for name in names:
        rows = [json.loads(l) for l in open(ROOT / "eval" / "data" / f"{name}.jsonl")]
        out_name = name.replace("_split", "_v2") if v2 else name
        dest = ROOT / "exams" / out_name
        (dest / "images").mkdir(parents=True, exist_ok=True)
        items = []
        for r in rows:
            imgs = []
            for p in r.get("images", []):
                src = ROOT / p
                shutil.copy(src, dest / "images" / src.name)
                imgs.append({"path": f"images/{src.name}", "source_page": None, "sha256": None})
            src_text = r.get("sources", "")
            if v2:
                src_text = with_markers(src_text, [i["path"] for i in imgs])
            items.append({"id": r["id"], "group": int(r["id"].split(".")[0].split("-")[0]) if r["id"][0].isdigit() else r["id"],
                          "max_points": r["max_points"], "question": r["question"], "source_text": src_text,
                          "images": imgs, "answer_format": answer_format(r)})
        if v2:  # klucze i oceny z tego samego pliku zadań
            link = ROOT / "eval" / "data" / f"{out_name}.jsonl"
            if not link.exists():
                link.symlink_to(f"{name}.jsonl")
        exam = {"exam_id": out_name, "title": out_name, "language": "pl", "input_format": "separate-text-and-images-v1",
                "max_points": sum(r["max_points"] for r in rows), "instructions": "", "items": items}
        (dest / "exam.json").write_text(json.dumps(exam, ensure_ascii=False, indent=1), encoding="utf-8")
        print(out_name, len(items), exam["max_points"])


if __name__ == "__main__":
    args = sys.argv[1:]
    main([a for a in args if a != "--v2"], v2="--v2" in args)
