"""Symulacja offline głosowania większościowego na zadaniach zamkniętych (raport 19).

    python eval/vote_sim.py            # tabela: pojedynczy seed vs głos z K próbek, per arkusz i pula

Próbki = niezależne przebiegi tej samej konfiguracji w runs/<zbiór>/*/debug.jsonl (pomijane rekordy
`merged_from` i duplikaty po treści rozumowania). Głos per część odpowiedzi (litera / "n: P" / "A: x"),
remis → pierwsza próbka. Oceny jak eval/grade.py (nierozpoznana część = zła).
"""

import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from grade import norm, parse_choice, parse_tf, score, strip_think  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SETS = ["test2024_v2", "test2025_v2", "test2026_v2"]
EXCL = {"test2024_v2": {"21"}}


def pool_of(name, a):
    if a.get("bare") or a.get("legacy_prompt") or a.get("rag") != "none" or "closed" not in (a.get("think") or ""):
        return []
    if name.startswith(("gemma4-qat", "fx-t1")):
        if a.get("temperature") != 1.0 or "img560" in name:
                return []
        wide = "T1 Gemma QAT t1.0 +img1120"
        return [wide] if "img1120" in name else ["T1 Gemma QAT t1.0", wide]
    if name.startswith("q35-4b") and a.get("temperature") == 0.6:
        for pat, lab in [("iq2mpl-e4k", "T3 IQ2_M-PL-E4K(-MIX)"), ("iq3xxs", "T3 IQ3_XXS (stock/PL)"),
                         ("q3km", "T3 Q3_K_M"), ("q3ks", "T3 Q3_K_S"), ("iq2m", "T3 IQ2_M stock")]:
            if pat in name:
                return [lab]
    return []


LENIENT = "--lenient" in sys.argv
ALIASES = {"stany zjednoczone": ["usa", "stany zjednoczone"]}


def lenient_ok(seg, alts):
    """Przybliżenie sędziego AI: formy fleksyjne ("zakon franciszkanów") i aliasy ("USA")."""
    for x in alts:
        x = norm(x)
        if any(k in x and any(y in seg for y in v) for k, v in ALIASES.items()):
            return True
        stems = [w[:6] for w in re.findall(r"\w+", x) if len(w) >= 4]
        if stems and all(s in seg for s in stems):
            return True
    return False


def match_parts(answer, key):
    a = norm(answer)
    out = []
    for k, v in key.items():
        line = re.search(rf"(?m)(?:^|\s|fragment\s){k.lower()}\s*[\.\):–\-]*\s*[–\-:→>]\s*(.+)$", a)
        if not line:
            out.append(None)
            continue
        seg = line.group(1)
        alts = [re.sub(r"[\[\]]", "", x).strip() for x in v.split("/")] + [re.sub(r"\[.*?\]", "", x).strip() for x in v.split("/")]
        if any(x and norm(x) in seg for x in alts) or (LENIENT and lenient_ok(seg, alts)):
            out.append("OK")
        else:
            out.append(re.sub(r"[^\w ]", "", seg).strip()[:40] or None)
    return out


def parts(item, text):
    key, t = item["key"], item["type"]
    if t == "closed_tf":
        return parse_tf(text, len(key)) or [None] * len(key)
    if t == "closed_match":
        return match_parts(text, key)
    return parse_choice(text, len(key), item["question"]) or [None] * len(key)


def pts(item, p):
    key = item["key"]
    gold = ["OK"] * len(key) if item["type"] == "closed_match" else list(key.values())
    return score(sum(g == x for g, x in zip(gold, p)), len(key), item["max_points"])


def vote(samples):
    out = []
    for j in range(len(samples[0])):
        vals = [s[j] for s in samples if s[j] is not None]
        if not vals:
            out.append(None)
            continue
        c = Counter(vals)
        top = max(c.values())
        out.append(next(v for v in vals if c[v] == top))
    return out


def load():
    data = {}
    for ds in SETS:
        items = {json.loads(l)["id"]: json.loads(l) for l in open(ROOT / "eval/data" / f"{ds}.jsonl")}
        closed = {i: it for i, it in items.items() if it.get("key") and i not in EXCL.get(ds, ())}
        for d in sorted((ROOT / "runs" / ds).glob("*")):
            try:
                a = json.load(open(d / "meta.json"))["args"]
            except Exception:
                continue
            pools = pool_of(d.name, a)
            if not pools or not (d / "debug.jsonl").exists():
                continue
            for l in open(d / "debug.jsonl", encoding="utf-8"):
                r = json.loads(l)
                if r["id"] not in closed or r.get("merged_from"):
                    continue
                if r.get("vote"):  # przebieg z --vote-closed: każda próbka osobno, nie wynik głosowania
                    draws = [((d.name, j), s) for j, s in enumerate(r["vote"]["samples"])]
                else:
                    draws = [((r.get("answer", ""), (r.get("reasoning") or "")[:400]), r.get("answer") or "")]
                for sig, txt in draws:
                    p = parts(closed[r["id"]], strip_think(txt))
                    for pool in pools:
                        slot = data.setdefault((pool, ds), {}).setdefault(r["id"], {})
                        if sig not in slot:
                            slot[sig] = {"run": d.name, "parts": p, "pts": pts(closed[r["id"]], p),
                                         "unparsed": any(x is None for x in p)}
        for key in [k for k in data if k[1] == ds]:
            data[key] = {i: (closed[i], list(v.values())) for i, v in data[key].items()}
    return data


def decide(it, pick, K):
    """K > 0: stały głos z K próbek; K < 0: adaptacyjnie — 2 próbki, przy niezgodzie dobór do |K|."""
    if K > 0:
        return pts(it, vote([x["parts"] for x in pick[:K]])), min(K, len(pick))
    if len(pick) < 2 or pick[0]["parts"] == pick[1]["parts"]:
        return pick[0]["pts"], min(2, len(pick))
    k = min(-K, len(pick))
    return pts(it, vote([x["parts"] for x in pick[:k]])), k


def simulate(pool_items, K, draws=20000, rng=None):
    rng = rng or random.Random(0)
    single, voted, per_item, used = [], [], {}, []
    for _ in range(draws):
        s1 = sv = nu = 0
        for iid, (it, samples) in pool_items.items():
            pick = rng.sample(samples, min(abs(K), len(samples)))
            a = pick[0]["pts"]
            b, k = decide(it, pick, K)
            s1 += a
            sv += b
            nu += k
            per_item.setdefault(iid, []).append(b - a)
        single.append(s1)
        voted.append(sv)
        used.append(nu / len(pool_items))
    return single, voted, {i: sum(v) / len(v) for i, v in per_item.items()}, sum(used) / len(used)


def item_boot(per_item_by_sheet, B=4000, rng=None):
    """Bootstrap po zadaniach (warstwy = arkusze) oczekiwanego zysku w pkt."""
    rng = rng or random.Random(2)
    out = []
    for _ in range(B):
        tot = 0.0
        for per in per_item_by_sheet:
            vals = list(per.values())
            tot += sum(rng.choice(vals) for _ in vals)
        out.append(tot)
    return out


def pct(xs, q):
    xs = sorted(xs)
    return xs[int(q * (len(xs) - 1))]


def main():
    data = load()
    rng = random.Random(1)
    rows, per_store = [], {}
    modes = [(3, "K=3"), (5, "K=5"), (-5, "2→5 adapt.")]
    for (pool, ds), pi in sorted(data.items()):
        n = [len(s) for _, s in pi.values()]
        maxp = sum(it["max_points"] for it, _ in pi.values())
        unp = sum(x["unparsed"] for _, s in pi.values() for x in s)
        tot = sum(len(s) for _, s in pi.values())
        unanim = sum(len({tuple(x["parts"]) for x in s}) == 1 for _, s in pi.values())
        line = [pool, ds, f"{min(n)}–{max(n)}", f"{len(pi)}/{maxp}", f"{unp}/{tot}", f"{unanim}/{len(pi)}"]
        moved = ""
        for K, lab in modes:
            if max(n) < abs(K):
                line += ["—"]
                continue
            s1, sv, per, used = simulate(pi, K, 4000, rng)
            per_store[(pool, ds, K)] = per
            d = [b - a for a, b in zip(s1, sv)]
            m1, mv = sum(s1) / len(s1), sum(sv) / len(sv)
            line += [f"{m1:.2f} → {mv:.2f} (**{(mv - m1):+.2f}**; 90%: {pct(d, .05):+d}…{pct(d, .95):+d}; {used:.1f} próbki)"]
            if K == 3:
                moved = json.dumps({i: round(v, 2) for i, v in per.items() if abs(v) >= 0.05}, ensure_ascii=False)
        rows.append(line + [moved])
    hdr = ["pula", "arkusz", "próbek/zad.", "zadań/pkt", "nierozp.", "jednomyślne"] + [f"{lab}: 1 seed → głos" for _, lab in modes] + ["zadania ruszone K=3 (Δpkt)"]
    print("| " + " | ".join(hdr) + " |")
    print("|" + "---|" * len(hdr))
    for r in rows:
        print("| " + " | ".join(r) + " |")
    print("\nBootstrap po zadaniach, 2024+2025 (119 pkt): oczekiwany zysk w pkt i pp, 95% CI")
    for pool in sorted({p for p, _ in data}):
        for K, lab in modes:
            pers = [per_store.get((pool, ds, K)) for ds in SETS[:2]]
            if any(p is None for p in pers):
                continue
            bs = item_boot(pers)
            m = sum(sum(p.values()) for p in pers)
            print(f"- {pool} {lab}: {m:+.2f} pkt = {100 * m / 119:+.2f} pp; 95% CI [{100 * pct(bs, .025) / 119:+.2f}, {100 * pct(bs, .975) / 119:+.2f}] pp")
    if "-v" in sys.argv:
        for (pool, ds), pi in sorted(data.items()):
            print(f"\n## {pool} {ds}")
            for iid, (it, s) in pi.items():
                print(iid, it["type"], it["max_points"], [x["pts"] for x in s], Counter(tuple(x["parts"]) for x in s).most_common(4))


if __name__ == "__main__":
    main()
