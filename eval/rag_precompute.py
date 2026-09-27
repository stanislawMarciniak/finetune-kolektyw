"""Dopisuje do zadań kontekst RAG z indeksu BM25 (PolQA, pole `stem`) -> eval/data/<zbiór>_rag.jsonl.

Zapytanie = polecenie + początek źródeł; dla eseju osobne zapytanie na każdy temat.
    python eval/rag_precompute.py test2024_split test2025_split test2026_split dev2023_text
"""

import json
import re
import sys
from pathlib import Path

import tantivy

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "eval" / "data"
INDEX = ROOT / "data" / "kb" / "polqa_index"
WORD = re.compile(r"\w+", re.UNICODE)
STOP = set("i w z na do że się nie jest to o a od po jak czy który która które oraz lub dla przez jego jej ich ten ta te "
           "tym tego tej źródło źródła źródle odpowiedź uzasadnij rozstrzygnij podaj wyjaśnij tekst tekstu fragment "
           "fragmentu informacji odwołując odwołaj obu zadanie".split())


def terms(text):
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = "\n".join(l for l in text.splitlines() if not re.search(r"\b(s\.|t\.|red\.|oprac\.)\s*\d|Warszawa|Kraków|Wrocław|Poznań", l))
    return list(dict.fromkeys(w.lower()[:6] for w in WORD.findall(text) if w.lower() not in STOP and len(w) > 2))


def search(searcher, schema, text, k):
    q = tantivy.Query.boolean_query([(tantivy.Occur.Should, tantivy.Query.term_query(schema, "stem", t)) for t in terms(text)[:60]])
    out = []
    for _, addr in searcher.search(q, k).hits:
        d = searcher.doc(addr)
        out.append({"title": d["title"][0], "text": d["text"][0][:700]})
    return out


def main(names):
    idx = tantivy.Index.open(str(INDEX))
    idx.reload()
    searcher, schema = idx.searcher(), idx.schema
    for name in names:
        rows = [json.loads(l) for l in open(DATA / f"{name}.jsonl")]
        for r in rows:
            if r["type"] == "essay":
                topics = re.findall(r"(?ms)^\d\.\s+(.+?)(?=^\d\.\s|\Z)", r["question"])
                r["rag"] = [{"topic": i + 1, "passages": search(searcher, schema, t, 4)} for i, t in enumerate(topics)]
            else:
                r["rag"] = search(searcher, schema, f"{r['question']} {r.get('sources', '')[:600]}", 4)
        with open(DATA / f"{name}_rag.jsonl", "w") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(name, "ok", len(rows))


if __name__ == "__main__":
    main(sys.argv[1:])
