"""Baza wiedzy v0: korpus PolQA (7 mln pasaży polskiej Wikipedii, CC BY-SA 4.0) + indeks BM25 (tantivy).

Indeks ma dwa pola wyszukiwania:
  raw   - słowa po lowercase
  stem  - słowa obcięte do 6 znaków (tani "stemming" dla polskiej fleksji)
Na koniec mierzy recall@k na pytaniach walidacyjnych PolQA dla raw / stem / raw+stem
(weryfikacja H-H2: czy normalizacja słów pomaga wyszukiwaniu po polsku).
Pobiera też polską Wikipedię (wikimedia/wikipedia 20231101.pl) do późniejszego użycia.
"""

import csv
import json
import os
import re
import sys
import time
from pathlib import Path

os.environ.setdefault("HF_XET_HIGH_PERFORMANCE", "1")
from huggingface_hub import hf_hub_download, snapshot_download  # noqa: E402
import tantivy  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
KB = ROOT / "data" / "kb"
INDEX = KB / "polqa_index"
WORD = re.compile(r"\w+", re.UNICODE)
PREFIX = 6

csv.field_size_limit(sys.maxsize)


def toks_raw(text):
    return [w.lower() for w in WORD.findall(text)]


def toks_stem(text):
    return [w[:PREFIX] for w in toks_raw(text)]


def schema():
    sb = tantivy.SchemaBuilder()
    sb.add_text_field("id", stored=True, tokenizer_name="raw")
    sb.add_text_field("title", stored=True)
    sb.add_text_field("text", stored=True)
    sb.add_text_field("raw", stored=False, tokenizer_name="whitespace")
    sb.add_text_field("stem", stored=False, tokenizer_name="whitespace")
    return sb.build()


def build_index(passages):
    if (INDEX / "DONE").exists():
        print("index exists", flush=True)
        return
    INDEX.mkdir(parents=True, exist_ok=True)
    idx = tantivy.Index(schema(), path=str(INDEX))
    writer = idx.writer(heap_size=1_500_000_000, num_threads=2)
    t0 = time.time()
    with open(passages, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            d = json.loads(line)
            body = f"{d.get('title', '')} {d.get('text', '')}"
            raw = toks_raw(body)
            writer.add_document(tantivy.Document(
                id=d["id"], title=d.get("title", ""), text=d.get("text", ""),
                raw=" ".join(raw), stem=" ".join(w[:PREFIX] for w in raw)))
            if n % 500_000 == 0:
                writer.commit()
                print(f"indexed {n:,} ({time.time() - t0:.0f}s)", flush=True)
    writer.commit()
    writer.wait_merging_threads()
    (INDEX / "DONE").write_text(str(n))
    print(f"index done: {n:,} docs in {time.time() - t0:.0f}s", flush=True)


def evaluate(split_csv, limit=1500):
    idx = tantivy.Index.open(str(INDEX))
    idx.reload()
    searcher = idx.searcher()
    sch = idx.schema
    gold = {}
    with open(split_csv, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("relevant", "").lower() == "true" and r.get("passage_id"):
                gold.setdefault(r["question"], set()).add(r["passage_id"])
    questions = list(gold.items())[:limit]

    def query(q, fields):
        parts = []
        for field in fields:
            tk = toks_stem(q) if field == "stem" else toks_raw(q)
            parts += [(tantivy.Occur.Should, tantivy.Query.term_query(sch, field, t)) for t in set(tk)]
        return tantivy.Query.boolean_query(parts)

    ks = (1, 5, 10, 20, 50)
    report = {}
    for name, fields in {"raw": ["raw"], "stem": ["stem"], "raw+stem": ["raw", "stem"]}.items():
        hits = {k: 0 for k in ks}
        t0 = time.time()
        for q, ids in questions:
            res = searcher.search(query(q, fields), max(ks)).hits
            got = [searcher.doc(a)["id"][0] for _, a in res]
            for k in ks:
                hits[k] += bool(ids & set(got[:k]))
        report[name] = {f"recall@{k}": round(hits[k] / len(questions), 4) for k in ks}
        report[name]["sec_per_query"] = round((time.time() - t0) / len(questions), 4)
        print(name, report[name], flush=True)
    report["n_questions"] = len(questions)
    (KB / "retrieval_eval_polqa.json").write_text(json.dumps(report, indent=2))


def main():
    KB.mkdir(parents=True, exist_ok=True)
    passages = hf_hub_download("ipipan/polqa", "data/passages.jsonl", repo_type="dataset", local_dir=KB / "polqa")
    for split in ("train", "valid", "test"):
        hf_hub_download("ipipan/polqa", f"data/{split}.csv", repo_type="dataset", local_dir=KB / "polqa")
    print("polqa downloaded", flush=True)
    build_index(passages)
    evaluate(KB / "polqa" / "data" / "valid.csv")
    snapshot_download("wikimedia/wikipedia", repo_type="dataset", allow_patterns=["20231101.pl/*"],
                      local_dir=KB / "wikipedia")
    print("wikipedia pl downloaded", flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    sys.exit(main())
