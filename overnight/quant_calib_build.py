"""Składa korpus kalibracyjny imatrix + zbiory do perplexity dla kwantyzacji Qwen3.5-4B (T3).
Źródła: baza wiedzy (kompendium, oś czasu, postacie, pojęcia), zadania E5 z odpowiedziami, ślady rozumowania BF16
(quant_calib_gen.py) w szablonie czatu Qwen. Arkusze testowe 2024–2026 nie są używane.
Wynik w katalogu roboczym: calib.txt, ppl_pl.txt (tekst historyczny), ppl_reason.txt (ślady w szablonie czatu).
"""
import json
import random
import sys
from pathlib import Path

W = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
rnd = random.Random(11)


def jl(name):
    p = W / name
    return [json.loads(l) for l in open(p)] if p.exists() else []


def chat(system, user, reasoning, answer, think):
    s = f"<|im_start|>system\n{system}<|im_end|>\n<|im_start|>user\n{user}<|im_end|>\n<|im_start|>assistant\n"
    s += f"<think>\n{reasoning.strip()}\n</think>\n\n" if think else "<think>\n\n</think>\n\n"
    return s + answer.strip() + "<|im_end|>\n"


calib, ppl_pl, ppl_reason = [], [], []

komp = jl("kompendium.jsonl") + jl("kompendium_extra.jsonl")
rnd.shuffle(komp)
k_hold = len(komp) // 10
ppl_pl += [f"{d['title']}\n\n{d['text']}\n" for d in komp[:k_hold]]
calib += [f"{d['title']}\n\n{d['text']}\n" for d in komp[k_hold:]]

for name, fmt in [("timeline.jsonl", lambda d: f"{d['date_text']} – {d['title']}. {d['text']}"),
                  ("persons.jsonl", lambda d: f"{d['name']} ({d['years']}), {d['role']}. {d['text']}"),
                  ("terms.jsonl", lambda d: f"{d['term']} – {d['text']}")]:
    rows = jl(name)
    rnd.shuffle(rows)
    hold = rows[:len(rows) // 12]
    ppl_pl.append("\n".join(fmt(d) for d in hold) + "\n")
    take = rows[len(rows) // 12: len(rows) // 12 + len(rows) // 3]
    for i in range(0, len(take), 25):
        calib.append("\n".join(fmt(d) for d in take[i:i + 25]) + "\n")

traces = [t for t in jl("traces.jsonl") if t.get("answer") or t.get("reasoning")]
used = {t["id"] for t in traces}
rnd.shuffle(traces)
t_hold = max(1, len(traces) * 15 // 100)
ppl_reason += [chat(t["system"], t["user"], t["reasoning"], t["answer"], t["think"]) for t in traces[:t_hold]]
calib += [chat(t["system"], t["user"], t["reasoning"], t["answer"], t["think"]) for t in traces[t_hold:]]

e5 = [e for e in jl("e5_items.jsonl") if e["id"] not in used and str(e.get("leak")) == "False" and e["type"] != "essay"]
rnd.shuffle(e5)
for e in e5[:400]:
    calib.append(f"{e.get('source_text', '')}\n\n{e['question']}\n\nOdpowiedź: {e['model_answer']}\n")

rnd.shuffle(calib)
# ślady rozumowania w całości, reszta przycięta do KB_CAP znaków (proporcja ok. pół na pół)
KB_CAP = 650_000
kept, n_kb = [], 0
for c in calib:
    if c.startswith("<|im_start|>"):
        kept.append(c)
    elif n_kb < KB_CAP:
        kept.append(c)
        n_kb += len(c)
calib = kept
(W / "calib.txt").write_text("\n".join(calib))
(W / "ppl_pl.txt").write_text("\n".join(ppl_pl))
(W / "ppl_reason.txt").write_text("".join(ppl_reason))
for f in ["calib.txt", "ppl_pl.txt", "ppl_reason.txt"]:
    print(f, (W / f).stat().st_size, "bytes")
print("traces", len(traces), "held-out", t_hold, "komp docs", len(komp), "held-out", k_hold)
