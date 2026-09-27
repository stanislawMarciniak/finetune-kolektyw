"""Benchmark trafności wyszukiwania (CPU): bazy × metody × zapytania, trafność top-k na zadaniach „podaj/wymień/nazwij”.

    python eval/retrieval_bench.py [--dense] [--k 3]   # -> raports/08b-wyszukiwanie.md
Trafienie: w pobranych tekstach są dwa pierwsze rdzenie słów kluczowych odpowiedzi z klucza (jak eval/rag_coverage.py).
Bazy: PolQA (BM25 tantivy), kompendium, zadania z kluczem (real_cke + syntetyczne), oś czasu / postacie / pojęcia (jeśli są).
Metody: BM25, dense (intfloat/multilingual-e5-small, CPU), hybryda RRF. Zapytania: polecenie + źródła, nazwy własne,
HyDE napisane przez Qwen3.5-2B w harnessie (runs/*/q35-2b__hyde_podaj/debug.jsonl).
"""

import argparse
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))
sys.path.insert(0, str(ROOT / "harness"))
from rag_coverage import entity_query, key_terms  # noqa: E402
from rag_precompute import terms  # noqa: E402
from topics import scope_of  # noqa: E402

SETS = ["test2024_split", "test2025_split", "test2026_split", "dev2023_text"]


class BM25:
    def __init__(self, docs, k1=1.5, b=0.75):
        self.docs = [terms(d["title"] + " " + d["text"]) for d in docs]
        self.avg = sum(map(len, self.docs)) / max(1, len(self.docs))
        df = defaultdict(int)
        for d in self.docs:
            for t in set(d):
                df[t] += 1
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}
        self.tf = [defaultdict(int) for _ in self.docs]
        for tf, d in zip(self.tf, self.docs):
            for t in d:
                tf[t] += 1
        self.k1, self.b = k1, b

    def rank(self, q, k):
        qt = set(terms(q))
        sc = []
        for i, tf in enumerate(self.tf):
            s = sum(self.idf[t] * tf[t] * (self.k1 + 1) / (tf[t] + self.k1 * (1 - self.b + self.b * len(self.docs[i]) / self.avg))
                    for t in qt if t in tf)
            if s > 0:
                sc.append((s, i))
        return [i for _, i in sorted(sc, reverse=True)[:k]]


class Dense:
    def __init__(self, docs, model="intfloat/multilingual-e5-small"):
        import torch
        from transformers import AutoModel, AutoTokenizer
        self.torch = torch
        self.tok, self.m = AutoTokenizer.from_pretrained(model), AutoModel.from_pretrained(model).eval()
        self.emb = self.encode([f"passage: {d['title']} {d['text']}" for d in docs])

    def encode(self, texts, bs=32):
        out = []
        with self.torch.no_grad():
            for i in range(0, len(texts), bs):
                x = self.tok(texts[i:i + bs], padding=True, truncation=True, max_length=256, return_tensors="pt")
                h = self.m(**x).last_hidden_state
                e = (h * x["attention_mask"][..., None]).sum(1) / x["attention_mask"].sum(1, keepdim=True)
                out.append(self.torch.nn.functional.normalize(e, dim=-1))
        return self.torch.cat(out)

    def rank(self, q, k):
        s = (self.encode([f"query: {q}"]) @ self.emb.T)[0]
        return s.topk(min(k, len(s))).indices.tolist()


def rrf(rankings, k, c=60):
    sc = defaultdict(float)
    for r in rankings:
        for pos, i in enumerate(r):
            sc[i] += 1 / (c + pos + 1)
    return [i for i, _ in sorted(sc.items(), key=lambda x: -x[1])[:k]]


def load_corpora():
    corp = {}
    kb = ROOT / "data" / "kb"
    if (kb / "kompendium.jsonl").exists():
        corp["kompendium"] = [{"title": r["title"], "text": r["text"]} for r in map(json.loads, open(kb / "kompendium.jsonl"))]
    for name, fields in (("timeline", ("event", "title", "year")), ("persons", ("name", "title")), ("terms", ("term", "title"))):
        f = kb / f"{name}.jsonl"
        if f.exists():
            rows = []
            for r in map(json.loads, open(f, encoding="utf-8")):
                title = next((str(r[x]) for x in fields if r.get(x)), "")
                rows.append({"title": title, "text": json.dumps(r, ensure_ascii=False)})
            corp[name] = rows
    qa = []
    for name in ("real_cke.jsonl", "synthetic_items.jsonl", "e5_items.jsonl"):
        f = ROOT / "data" / "sft" / name
        if f.exists():
            for r in map(json.loads, open(f, encoding="utf-8")):
                if r.get("type") != "essay":
                    qa.append({"title": r["question"][:200], "text": f"{r.get('model_answer', '')} {r.get('source_text', '')[:400]}"})
    corp["zadania_z_kluczem"] = qa
    return corp


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dense", action="store_true")
    p.add_argument("--k", type=int, default=3)
    a = p.parse_args()
    items = []
    for ds in SETS:
        for l in open(ROOT / "eval" / "data" / f"{ds}.jsonl", encoding="utf-8"):
            it = json.loads(l)
            ans = it.get("model_answer", "")
            if it["type"] == "open" and 0 < len(ans) < 80 and it["question"].startswith(("Podaj", "Wymień", "Nazwij")) and key_terms(ans):
                it["ds"] = ds
                it["scope"] = scope_of(f"{it['question']} {it.get('sources', '')}")
                items.append(it)
    hyde = {}
    for ds in SETS:
        f = ROOT / "runs" / ds / "q35-2b__hyde_podaj" / "debug.jsonl"
        if f.exists():
            for r in map(json.loads, open(f, encoding="utf-8")):
                if r.get("hyde"):
                    hyde[(ds, r["id"])] = r["hyde"]
    queries = {
        "polecenie+źródła": lambda it: f"{it['question']} {it.get('sources', '')[:600]}",
        "nazwy własne": entity_query,
        "HyDE Qwen-2B + polecenie": lambda it: f"{hyde.get((it['ds'], it['id']), '')} {it['question']} {it.get('sources', '')[:600]}",
    }
    corp = load_corpora()
    methods = {}
    for name, docs in corp.items():
        methods[(name, "BM25")] = (docs, BM25(docs))
        if a.dense:
            methods[(name, "dense")] = (docs, Dense(docs))
    import tantivy
    idx = tantivy.Index.open(str(ROOT / "data" / "kb" / "polqa_index"))
    idx.reload()
    s, sch = idx.searcher(), idx.schema

    def polqa(q, k):
        tk = terms(q)[:80]
        if not tk:
            return []
        qq = tantivy.Query.boolean_query([(tantivy.Occur.Should, tantivy.Query.term_query(sch, "stem", t)) for t in tk])
        return [(s.doc(x)["title"][0] + " " + s.doc(x)["text"][0]).lower() for _, x in s.search(qq, k).hits]

    def hit(texts, it):
        kt = key_terms(it["model_answer"])
        return any(all(t in tx for t in kt[:2]) for tx in texts)

    res = defaultdict(lambda: defaultdict(lambda: [0, 0]))  # (baza, metoda) -> (zapytanie, zakres) -> [trafienia, n]
    for it in items:
        for qn, qf in queries.items():
            q = qf(it)
            cand = {("PolQA", "BM25"): polqa(q, a.k)}
            for (name, meth), (docs, m) in methods.items():
                cand[(name, meth)] = [(docs[i]["title"] + " " + docs[i]["text"]).lower() for i in m.rank(q, a.k)]
            if a.dense:
                for name in corp:
                    ids = rrf([methods[(name, "BM25")][1].rank(q, 20), methods[(name, "dense")][1].rank(q, 20)], a.k)
                    cand[(name, "hybryda RRF")] = [(corp[name][i]["title"] + " " + corp[name][i]["text"]).lower() for i in ids]
            notes_all = [t for (n, mth), txt in cand.items() if n != "PolQA" and mth == "BM25" for t in txt[:1]]
            cand[("PolQA + top-1 z każdej bazy", "BM25")] = cand[("PolQA", "BM25")] + notes_all
            for key, texts in cand.items():
                for scope in (it["scope"], "razem"):
                    cell = res[key][(qn, scope)]
                    cell[0] += hit(texts, it)
                    cell[1] += 1
    cols = [(qn, sc) for qn in queries for sc in ("Polska", "powszechna", "razem")]
    lines = [f"# 08b — Trafność wyszukiwania (top-{a.k}), zadania „podaj/wymień/nazwij” z krótkim kluczem", "",
             f"Zadań: {len(items)} (Polska {sum(i['scope'] == 'Polska' for i in items)}, powszechna "
             f"{sum(i['scope'] == 'powszechna' for i in items)}). HyDE Qwen-2B dostępne dla {len(hyde)} zadań. "
             "Generowane przez `eval/retrieval_bench.py`.", "",
             "| baza | metoda | " + " | ".join(f"{qn} / {sc}" for qn, sc in cols) + " |", "|---|---|" + "---|" * len(cols)]
    for (name, meth), cells in sorted(res.items()):
        lines.append(f"| {name} | {meth} | " + " | ".join(
            f"{100 * cells[c][0] / cells[c][1]:.0f}%" if cells[c][1] else "—" for c in cols) + " |")
    out = ROOT / "raports" / "08b-wyszukiwanie.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
