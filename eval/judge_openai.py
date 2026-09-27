"""Sędzia LLM (OpenAI) dla pytań otwartych i esejów, wg zasad oceniania CKE.

    # kalibracja na odpowiedziach ocenionych przez oficjalnego sędziego benchmarku (DEV-2023)
    python eval/judge_openai.py calib --model gpt-4.1-mini --budget 0.3
    # ocena wszystkich pozycji czekających w results/grades/*/*.auto.json
    python eval/judge_openai.py grade --model gpt-4.1-mini --essay-model gpt-5.4-mini --budget 3.0

Koszt liczony z usage i cennika poniżej; po przekroczeniu --budget skrypt przerywa (oceny zapisane do tej pory zostają).
"""

import argparse
import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from openai import BadRequestError, OpenAI

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "eval" / "data"
RES = ROOT / "results"
ESSAY_RUBRIC = (ROOT / "eval" / "essay_rubric_cke.txt").read_text()

# USD za 1M tokenów (wejście, wyjście) — szacunek; nieznane modele liczone ostrożnie jak droższe.
PRICES = {"gpt-4.1-mini": (0.40, 1.60), "gpt-4.1-nano": (0.10, 0.40), "gpt-4.1": (2.0, 8.0),
          "gpt-5-mini": (0.25, 2.0), "gpt-5-nano": (0.05, 0.40), "gpt-5.4-mini": (0.75, 4.5), "gpt-5.4-nano": (0.20, 1.25),
          # cennik Forgehand nieznany — ostrożne założenie; realne zużycie sprawdzać w panelu zespołu
          "gpt-6-luna": (1.0, 6.0), "gpt-6-sol": (5.0, 30.0)}

SYSTEM_OPEN = """Jesteś egzaminatorem matury z historii (poziom rozszerzony, CKE). Oceniasz JEDNĄ odpowiedź zdającego na JEDNO zadanie, wyłącznie według podanych zasad oceniania CKE.
Zasady:
- Akceptuj wszystkie odpowiedzi merytorycznie poprawne i spełniające warunki zadania, także sformułowane inaczej niż rozwiązanie przykładowe.
- Nie poprawiaj odpowiedzi „po cichu”: jeśli zawiera sprzeczne wskazania, kilka alternatyw do wyboru albo etykietę niezgodną z treścią — nie wybieraj za zdającego; punkt tylko za elementy jednoznacznie poprawne.
- Jeśli polecenie wymaga rozstrzygnięcia i uzasadnienia (lub odwołania do źródła), punkt wymaga obu elementów.
- Stosuj dokładnie punkty częściowe z zasad oceniania. Pusta odpowiedź = 0. Odpowiedź uciętą oceniaj tak, jak jest.
- Nieistotne, ale nieszkodliwe dodatki nie odbierają punktów; powtarzanie w kółko tego samego nie dodaje punktów.
Zwróć wyłącznie JSON: {"points": <liczba całkowita>, "reason": "<1–2 zdania po polsku>"}"""

SYSTEM_ESSAY = """Jesteś egzaminatorem matury z historii (poziom rozszerzony, CKE). Oceniasz wypracowanie według oficjalnych kryteriów CKE podanych niżej.
- Oceniaj tylko pierwszy wyraźnie wybrany temat.
- Kryterium A (0–12): dla każdego z trzech elementów tematu określ poziom argumentacji: bogata (4), zadowalająca (3), powierzchowna (1), brak/niefunkcjonalna (0); zastosuj tabelę CKE. Policz odrębne błędy merytoryczne (chronologia, terminologia, związki przyczynowo-skutkowe): 1–2 → −1, 3–5 → −2, >5 → −3; minimum 0.
- Kryterium B (0–3): liczba słów jest podana; <300 słów → 0. Inaczej: spójna 3, drobne zaburzenia 2, istotne 1, nieuporządkowana 0. Powtarzanie tych samych fragmentów to zaburzenie spójności.
Kryteria CKE:
""" + ESSAY_RUBRIC + """
Zwróć wyłącznie JSON: {"topic": <nr>, "components": [{"name": "...", "level": "bogata|zadowalająca|powierzchowna|brak", "points": n}], "historical_before": n, "errors": n, "deduction": n, "historical": n, "coherence": n, "points": <suma A+B>, "reason": "<2–3 zdania po polsku>"}"""

lock = threading.Lock()
spent = {"usd": 0.0, "calls": 0}


def strip_think(a):
    return re.sub(r"<think>.*?</think>", "", a or "", flags=re.S).strip()


def word_count(text):
    t = re.sub(r"[#*_`>]+", " ", text)
    t = re.sub(r"(?m)^\s*(\d+[\.\)]|[-•])\s+", "", t)
    return len(t.split())


def ask(client, model, system, user, budget):
    with lock:
        if spent["usd"] >= budget:
            raise RuntimeError("budget exceeded")
    kw = {}
    if model.startswith(("gpt-5", "gpt-6", "o")):
        kw["reasoning_effort"] = "low"
    else:
        kw["temperature"] = 0
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    try:
        r = client.chat.completions.create(model=model, messages=msgs, response_format={"type": "json_object"}, **kw)
    except Exception as e:  # np. brak obsługi response_format / reasoning_effort w danym API
        if "response_format" in str(e) or "reasoning" in str(e):
            kw.pop("reasoning_effort", None)
            r = client.chat.completions.create(model=model, messages=msgs, **kw)
        else:
            raise
    pin, pout = PRICES.get(model, (2.0, 8.0))
    cost = r.usage.prompt_tokens * pin / 1e6 + r.usage.completion_tokens * pout / 1e6
    with lock:
        spent["usd"] += cost
        spent["calls"] += 1
    content = r.choices[0].message.content or ""
    m = re.search(r"\{.*\}", content, re.S)
    return json.loads(m.group(0) if m else content)


def user_open(item, answer):
    src = (item.get("sources") or "")[:1500]
    return (f"[ZADANIE {item['id']}, maks. {item['max_points']} pkt]\n{item['question']}\n\n"
            + (f"[ŹRÓDŁA (skrót)]\n{src}\n\n" if src else "")
            + f"[ZASADY OCENIANIA CKE]\n{item.get('rubric', '')}\n\n[ROZWIĄZANIE / PRZYKŁADOWE ODPOWIEDZI CKE]\n{item.get('solution', '')}\n\n"
            f"[ODPOWIEDŹ ZDAJĄCEGO]\n{answer[:3000]}")


def user_essay(item, answer):
    return (f"[TEMATY]\n{item['question']}\n\n[LICZBA SŁÓW WYPRACOWANIA] {word_count(answer)}\n\n"
            f"[WYPRACOWANIE]\n{answer[:9000]}")


def judge_item(client, item, answer, model, essay_model, budget):
    answer = strip_think(answer)
    if not answer:
        return {"points": 0, "reason": "brak odpowiedzi"}
    if item["type"] == "essay":
        out = ask(client, essay_model, SYSTEM_ESSAY, user_essay(item, answer), budget)
    else:
        out = ask(client, model, SYSTEM_OPEN, user_open(item, answer), budget)
    out["points"] = max(0, min(int(out.get("points", 0)), item["max_points"]))
    return out


def load_items(dataset):
    return {json.loads(l)["id"]: json.loads(l) for l in open(DATA / f"{dataset}.jsonl")}


def calib(args, client):
    """Porównanie z oceniami oficjalnego sędziego benchmarku (4 przebiegi tekstowe DEV-2023)."""
    items = load_items("dev2023_text")
    runs = {"bielik-4-5b": "bielik-4-5b", "qwen3-4b-instruct-2507": "qwen3-4b-instruct-2507",
            "gemma-3-4b-text": "gemma-3-4b-text", "ministral-3-14b-text": "ministral-3-14b-text"}
    jobs = []
    for run in runs:
        ans = {str(a["id"]): a["answer"] for a in json.load(open(ROOT / "assets/benchmark-2023/runs" / f"{run}.json"))["answers"]}
        off = {str(r["id"]): r["points"] for r in json.load(open(ROOT / "assets/benchmark-2023/reviews" / f"{run}.reviews.json"))}
        for iid, it in items.items():
            if it.get("key") or iid not in ans:
                continue
            if it["type"] == "essay" and not args.essays:
                continue
            jobs.append((run, iid, it, ans[iid], off[iid]))
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(lambda j: (j, judge_item(client, j[2], j[3], args.model, args.essay_model, args.budget)), jobs))
    agree = sum(int(r["points"] == j[4]) for j, r in res)
    diff_by_run = {}
    for j, r in res:
        diff_by_run.setdefault(j[0], [0, 0])
        diff_by_run[j[0]][0] += r["points"]
        diff_by_run[j[0]][1] += j[4]
    report = {"model": args.model, "n": len(res), "item_agreement": round(agree / len(res), 3),
              "sum_ours_vs_official": diff_by_run, "usd": round(spent["usd"], 4),
              "disagreements": [{"run": j[0], "id": j[1], "ours": r["points"], "official": j[4], "reason": r.get("reason")}
                                for j, r in res if r["points"] != j[4]]}
    out = RES / f"judge_calib_{args.model}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1))
    print(json.dumps({k: report[k] for k in ("model", "n", "item_agreement", "sum_ours_vs_official", "usd")}, ensure_ascii=False))


def grade(args, client):
    jobs = []
    for auto_f in sorted((RES / "grades").glob("*/*.auto.json")):
        dataset, run = auto_f.parent.name, auto_f.name.removesuffix(".auto.json")
        if args.only and not any(s in f"{dataset}/{run}" for s in args.only.split(",")):
            continue
        judge_f = auto_f.with_name(f"{run}.judge.json")
        done = json.load(open(judge_f)) if judge_f.exists() else {}
        items = load_items(dataset)
        auto = json.load(open(auto_f))
        answers = {json.loads(l)["id"]: json.loads(l) for l in open(RES / dataset / f"{run}.jsonl")}
        for iid, it in items.items():
            if iid in auto or iid in done:
                continue
            jobs.append((judge_f, iid, it, answers.get(iid, {}).get("answer", "")))
    print(f"do oceny: {len(jobs)} pozycji", flush=True)
    results = {}

    def flush():
        for judge_f, grades in results.items():
            old = json.load(open(judge_f)) if judge_f.exists() else {}
            old.update(grades)
            judge_f.write_text(json.dumps(old, ensure_ascii=False, indent=1))
        results.clear()

    def work(j):
        for attempt in range(6):
            try:
                return j, judge_item(client, j[2], j[3], args.model, args.essay_model, args.budget)
            except RuntimeError:
                return j, None
            except BadRequestError as e:
                if "rejected" in str(e):  # filtr treści Azure (np. kadr z wiecu NSDAP); ponawianie nic nie da
                    return j, {"points": 0, "filtered": True, "reason": "odrzucone przez filtr treści API sędziego"}
                print("retry", j[1], type(e).__name__, flush=True)
                time.sleep(5 * (attempt + 1))
            except Exception as e:  # limity TPM / chwilowe błędy API
                print("retry", j[1], type(e).__name__, flush=True)
                time.sleep(5 * (attempt + 1))
        return j, None

    n = 0
    with ThreadPoolExecutor(4) as ex:
        for j, r in ex.map(work, jobs):
            if r is not None:
                results.setdefault(j[0], {})[j[1]] = r
                n += 1
                if n % 25 == 0:
                    flush()
                    print(f"  {n} ocen, ≈ {spent['usd']:.3f} USD", flush=True)
    flush()
    print(f"ocenione: {n}, koszt ≈ {spent['usd']:.3f} USD, wywołań {spent['calls']}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["calib", "grade"])
    p.add_argument("--model", default="gpt-4.1-mini")
    p.add_argument("--essay-model", default="gpt-5.4-mini")
    p.add_argument("--budget", type=float, default=0.5)
    p.add_argument("--essays", action="store_true")
    p.add_argument("--only", default="")
    p.add_argument("--base-url", default=os.environ.get("JUDGE_BASE_URL"))
    p.add_argument("--key-env", default="OPENAI_API_KEY", help="np. FORGEHAND_API_KEY")
    args = p.parse_args()
    client = OpenAI(api_key=os.environ[args.key_env], base_url=args.base_url, max_retries=8, timeout=180)
    (calib if args.mode == "calib" else grade)(args, client)


if __name__ == "__main__":
    main()
