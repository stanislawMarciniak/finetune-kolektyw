"""Greedy decoding identity check between two servers.  python greedy_cmp.py PORT_A PORT_B"""
import json, sys, urllib.request

pa, pb = sys.argv[1:3]
prompts = [
    "Kto był pierwszym cesarzem rzymskim i jaki urząd zapewniał mu nietykalność? Odpowiedz krótko.",
    "Wyjaśnij przyczyny wybuchu powstania styczniowego w 1863 roku.",
    "Rozstrzygnij, czy pokój w Wersalu (1919) wzmocnił pozycję Polski. Uzasadnij odpowiedź jednym argumentem.",
    "Podaj nazwę dynastii, z której pochodził cesarz proklamowany w Wersalu 18 stycznia 1871 roku.",
    "Which Polish king won the Battle of Vienna in 1683? Answer in one sentence.",
    "Scharakteryzuj reformy Kazimierza Wielkiego w zakresie prawa, gospodarki i obronności.",
]


def gen(port, p):
    body = {"messages": [{"role": "user", "content": p}], "max_tokens": 600, "temperature": 0, "top_k": 1, "seed": 1}
    r = json.load(urllib.request.urlopen(urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/chat/completions", json.dumps(body).encode(), {"Content-Type": "application/json"}), timeout=600))
    m = r["choices"][0]["message"]
    return (m.get("reasoning_content") or "") + "\n<<>>\n" + (m.get("content") or ""), r["usage"]["completion_tokens"]


for p in prompts:
    a, na = gen(pa, p)
    b, nb = gen(pb, p)
    k = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    print(f"{'IDENTICAL' if a == b else 'DIFF@char ' + str(k)}  tokens {na}/{nb}  chars {len(a)}/{len(b)}  | {p[:50]}")
    if a != b:
        print("   A:", repr(a[max(0, k - 60):k + 80]))
        print("   B:", repr(b[max(0, k - 60):k + 80]))
