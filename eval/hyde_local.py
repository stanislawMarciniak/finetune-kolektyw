"""HyDE pisane przez sam lokalny model: pokrycie odpowiedzi w top-k i „ratunek” pytań, na które model nie zna odpowiedzi.

    python eval/hyde_local.py --base-url http://127.0.0.1:8090/v1 --name q35-2b
"""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import tantivy
from openai import OpenAI

from rag_coverage import key_terms
from rag_precompute import terms

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ("Rozwiąż zadanie z historii po polsku. Otrzymujesz polecenie, teksty źródeł oraz osobno obrazy źródeł (jeśli są). "
          "Wykorzystaj źródła i własną wiedzę zgodnie z poleceniem. Udziel tylko odpowiedzi na podane zadanie. "
          "Nie masz dostępu do narzędzi ani internetu.")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--no-think-kwargs", action="store_true")
    a = p.parse_args()
    client = OpenAI(base_url=a.base_url, api_key="x", timeout=600)
    idx = tantivy.Index.open(str(ROOT / "data" / "kb" / "polqa_index"))
    idx.reload()
    s, sch = idx.searcher(), idx.schema
    items = []
    for ds in ("test2024_split", "test2025_split", "test2026_split", "dev2023_text"):
        for l in open(ROOT / "eval" / "data" / f"{ds}.jsonl"):
            it = json.loads(l)
            ans = it.get("model_answer", "")
            if it["type"] == "open" and 0 < len(ans) < 60 and it["question"].startswith(("Podaj", "Wymień", "Nazwij")):
                items.append(it)

    def hyde(it):
        body = f"Zadanie {it['id']} ({it['max_points']} pkt)\n\n{it.get('sources', '')}\n\n{it['question']}"
        extra = {} if a.no_think_kwargs else {"chat_template_kwargs": {"enable_thinking": False}}
        r = client.chat.completions.create(model="m", max_tokens=150, temperature=0.0, extra_body=extra, messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": body + "\n\nNie rozwiązuj zadania. Napisz jedno–dwa zdania w stylu hasła encyklopedii, "
                                               "które zawierałyby potrzebne fakty (nazwy, daty, postacie)."}])
        return r.choices[0].message.content or ""

    with ThreadPoolExecutor(2) as ex:
        H = list(ex.map(hyde, items))

    def top(q, k=10):
        tk = terms(q)[:80]
        qq = tantivy.Query.boolean_query([(tantivy.Occur.Should, tantivy.Query.term_query(sch, "stem", t)) for t in tk])
        return [(s.doc(x)["title"][0] + " " + s.doc(x)["text"][0]).lower() for _, x in s.search(qq, k).hits]

    stats = {"n": len(items), "knows": 0, "base@4": 0, "hyde@4": 0, "hyde@10": 0, "rescue_base@4": 0, "rescue_hyde@4": 0}
    for it, h in zip(items, H):
        kt = key_terms(it["model_answer"])[:2]
        has = lambda txt: bool(kt) and all(t in txt for t in kt)
        knows = has(h.lower())
        base = top(f"{it['question']} {it.get('sources', '')[:600]}")
        hy = top(f"{h} {it['question']} {it.get('sources', '')[:600]}")
        stats["knows"] += knows
        stats["base@4"] += any(has(t) for t in base[:4])
        stats["hyde@4"] += any(has(t) for t in hy[:4])
        stats["hyde@10"] += any(has(t) for t in hy[:10])
        if not knows:
            stats["rescue_base@4"] += any(has(t) for t in base[:4])
            stats["rescue_hyde@4"] += any(has(t) for t in hy[:4])
    n = stats["n"]
    print(a.name, {k: (f"{100 * v / n:.0f}%" if k != "n" else v) for k, v in stats.items()},
          f"| nie zna: {n - stats['knows']}")


if __name__ == "__main__":
    main()
