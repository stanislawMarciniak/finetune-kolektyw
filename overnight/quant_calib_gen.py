"""Ślady rozumowania Qwen3.5-4B (BF16) na syntetycznych zadaniach E5 — korpus kalibracyjny imatrix i perplexity (T3).
Bez arkuszy testowych 2024–2026. Wynik: JSONL z promptem, rozumowaniem i odpowiedzią.
  python quant_calib_gen.py --items e5_items.jsonl --out traces.jsonl --base-url http://127.0.0.1:8090/v1 --n 380
"""
import argparse
import json
import random
from concurrent.futures import ThreadPoolExecutor

import requests

SYSTEM = ("Rozwiąż zadanie z historii po polsku. Otrzymujesz polecenie, teksty źródeł oraz osobno obrazy źródeł (jeśli są). "
          "Wykorzystaj źródła i własną wiedzę zgodnie z poleceniem. Udziel tylko odpowiedzi na podane zadanie. "
          "Nie masz dostępu do narzędzi ani internetu.")


def body(e, i):
    b = f"Zadanie {i} ({e['max_points']} pkt)\n\n{e.get('source_text', '')}\n\n{e['question']}"
    if e["type"].startswith("closed"):
        b += f"\n\nZapisz odpowiedź dokładnie w formacie:\n{e['answer_format']}"
    return b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--n", type=int, default=380)
    ap.add_argument("--essays", type=int, default=24)
    ap.add_argument("--max-tokens", type=int, default=3000)
    ap.add_argument("--parallel", type=int, default=16)
    a = ap.parse_args()
    items = [json.loads(l) for l in open(a.items)]
    items = [e for e in items if str(e.get("leak")) == "False" and str(e.get("verified")) == "True" and not str(e.get("needs_image")) == "True"]
    rnd = random.Random(7)
    rnd.shuffle(items)
    essays = [e for e in items if e["type"] == "essay"][: a.essays]
    rest = [e for e in items if e["type"] != "essay"][: a.n]
    jobs = [(e, i) for i, e in enumerate(rest + essays)]

    def one(job):
        e, i = job
        think = e["type"] != "essay"
        msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": body(e, i % 30 + 1)}]
        r = requests.post(a.base_url + "/chat/completions", json={
            "messages": msgs, "max_tokens": a.max_tokens if think else 1800, "temperature": 0.6, "top_p": 0.95, "top_k": 20,
            "chat_template_kwargs": {"enable_thinking": think}}, timeout=1200).json()
        m = r["choices"][0]["message"]
        return {"id": e["id"], "type": e["type"], "think": think, "system": SYSTEM, "user": msgs[1]["content"],
                "reasoning": m.get("reasoning_content") or "", "answer": m.get("content") or "",
                "finish": r["choices"][0]["finish_reason"], "model_answer": e["model_answer"]}

    with ThreadPoolExecutor(a.parallel) as ex, open(a.out, "w") as f:
        for n, rec in enumerate(ex.map(one, jobs)):
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if n % 50 == 0:
                print(n, flush=True)


if __name__ == "__main__":
    main()
