"""Buduje DEV-2023 (tekst 34 zad. / obrazy 37 zad.) we wspólnym formacie z kluczem CKE."""

import json
import re
from pathlib import Path

from cke_parse import parse_zasady
from items import classify, format_key, key_type, make_model_answer, parse_key

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets" / "benchmark-2023"
OUT = ROOT / "eval" / "data"


def enrich(item, zasady):
    z = zasady[item["id"]]
    key = parse_key(z["solution"])
    qtype = key_type(key, item["question"]) if key else classify(item["question"])
    if item["id"] == "26":
        qtype = "essay"
    sol = re.sub(r"^Rozwiązani[ae]\s*\n", "", z["solution"]).strip()
    item.update(type=qtype, key=key, rubric=z["rubric"] if qtype != "essay" else "KRYTERIA_ESEJU_CKE",
                solution=sol, model_answer=make_model_answer(sol, key, item["question"]) if qtype != "essay" else "")
    return item


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    zasady = parse_zasady((SRC / "cke-2023-zasady-oceniania.txt").read_text())
    text = json.load(open(SRC / "exam-text-34items.json"))
    img = json.load(open(SRC / "exam-images-37items.json"))
    with open(OUT / "dev2023_text.jsonl", "w") as f:
        for it in text["items"]:
            rec = enrich({"exam": "2023-05", "id": it["id"], "max_points": it["max_points"],
                          "question": it["question"], "sources": it.get("sources", ""), "images": []}, zasady)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    with open(OUT / "dev2023_img.jsonl", "w") as f:
        for it in img["items"]:
            rec = enrich({"exam": "2023-05", "id": it["id"], "max_points": it["max_points"],
                          "question": it["question"], "sources": "",
                          "images": ["assets/benchmark-2023/" + p for p in it["page_images"]]}, zasady)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    overrides = json.load(open(ROOT / "eval" / "model_answer_overrides.json"))
    for name in ("dev2023_text", "dev2023_img"):
        rows = [json.loads(l) for l in open(OUT / f"{name}.jsonl")]
        for r in rows:
            r["model_answer"] = overrides.get(f"2023:{r['id']}", r["model_answer"])
        with open(OUT / f"{name}.jsonl", "w") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        by = {}
        for r in rows:
            by.setdefault(r["type"], [0, 0])
            by[r["type"]][0] += 1
            by[r["type"]][1] += r["max_points"]
        print(name, len(rows), sum(r["max_points"] for r in rows), by)


if __name__ == "__main__":
    main()
