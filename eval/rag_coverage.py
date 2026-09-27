"""Jakość wyszukiwania bez GPU: czy top-k pasaży zawiera odpowiedź z klucza (zadania z krótką odpowiedzią).

    python eval/rag_coverage.py
Porównuje warianty zapytania na indeksie PolQA (pole `stem`).
"""

import json
import re
from pathlib import Path

import tantivy

from rag_precompute import STOP, WORD, terms

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "eval" / "data"


def key_terms(answer):
    words = [w for w in WORD.findall(answer) if len(w) > 3 and w.lower() not in STOP]
    return [w.lower()[:5] for w in words][:3]


def entity_query(item):
    """Nazwy własne, liczby i słowa kluczowe z polecenia i źródeł (bez przypisów i URL-i)."""
    text = f"{item['question']}\n{item.get('sources', '')}"
    text = re.sub(r"https?://\S+", " ", text)
    caps = re.findall(r"\b[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]{2,}(?:\s+[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]{2,})*", text)
    years = re.findall(r"\b1\d{3}\b|\b[1-9]\d{2}\b(?= r)", text)
    return " ".join(caps + years) + " " + item["question"]


def main():
    idx = tantivy.Index.open(str(ROOT / "data" / "kb" / "polqa_index"))
    idx.reload()
    s, sch = idx.searcher(), idx.schema
    items = []
    for ds in ("test2024_split", "test2025_split", "test2026_split", "dev2023_text"):
        for l in open(DATA / f"{ds}.jsonl"):
            it = json.loads(l)
            ans = it.get("model_answer", "")
            if it["type"] == "open" and 0 < len(ans) < 60 and it["question"].startswith(("Podaj", "Wymień", "Nazwij")):
                items.append(it)
    variants = {
        "V0 polecenie+źródła": lambda it: f"{it['question']} {it.get('sources', '')[:600]}",
        "V1 tylko polecenie": lambda it: it["question"],
        "V2 nazwy własne+polecenie": entity_query,
        "V3 całe źródła": lambda it: f"{it['question']} {it.get('sources', '')}",
    }
    print(f"{len(items)} zadań „podaj/wymień” z krótkim kluczem")
    for name, qf in variants.items():
        hits = {4: 0, 10: 0, 30: 0}
        for it in items:
            tk = terms(qf(it))[:80]
            if not tk:
                continue
            q = tantivy.Query.boolean_query([(tantivy.Occur.Should, tantivy.Query.term_query(sch, "stem", t)) for t in tk])
            docs = [s.doc(a) for _, a in s.search(q, 30).hits]
            texts = [(d["title"][0] + " " + d["text"][0]).lower() for d in docs]
            kt = key_terms(it["model_answer"])
            for k in hits:
                if kt and any(all(t in tx for t in kt[:2]) for tx in texts[:k]):
                    hits[k] += 1
        print(f"{name:28s} " + "  ".join(f"@{k}: {100 * v / len(items):.0f}%" for k, v in hits.items()))


if __name__ == "__main__":
    main()
