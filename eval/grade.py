"""Ocena przebiegów: zamknięte automatycznie, otwarte i eseje -> kolejka do oceny (sędzia: Claude / później GPT).

    python eval/grade.py results/              # ocenia wszystko, co jest w results/<zbiór>/<przebieg>.jsonl
Wyniki:
    results/grades/<zbiór>/<przebieg>.auto.json     punkty zamkniętych (+ niejednoznaczne do przeglądu)
    results/review/<zbiór>/<przebieg>.md            otwarte i eseje do oceny przez sędziego
    results/grades/<zbiór>/<przebieg>.judge.json    (uzupełnia sędzia) {"id": {"points": n, "reason": "..."}}
    results/report.md                               tabela zbiorcza (python eval/report.py)
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "eval" / "data"


def norm(s):
    s = unicodedata.normalize("NFKC", s).lower()
    return re.sub(r"[\*\_`#]", "", s)


def strip_think(answer):
    return re.sub(r"<think>.*?</think>", "", answer, flags=re.S).strip()


def parse_choice(answer, n_parts, question):
    """Zwraca listę wybranych liter (po jednej na część) albo None, gdy niejednoznacznie."""
    a = norm(answer)
    if n_parts > 1:
        got = {}
        for m in re.finditer(r"(?m)^\s*(?:część\s*)?(\d)\s*[\.\):–-]*\s*(?:odpowiedź\s*)?[:\-–]?\s*\(?([a-f])\b", a):
            got.setdefault(m.group(1), m.group(2).upper())
        return [got.get(str(i + 1)) for i in range(n_parts)] if got else None
    explicit = re.findall(r"odpowied[źz][^:\n]{0,20}:\s*\**\(?([a-f])\b", a)
    if explicit and len(set(explicit)) == 1:
        return [explicit[-1].upper()]
    cands = set(re.findall(r"(?:^|[\s\*\(\[])([a-f])(?:[\.\)\]:]|\s*$|\s+[–-]|\*\*)", a, flags=re.M))
    if len(cands) == 1:
        return [cands.pop().upper()]
    # dopasowanie po treści opcji
    opts = dict(re.findall(r"(?m)^([A-F])\.\s+(.+?)\.?\s*$", question))
    hits = [k for k, v in opts.items() if len(v) > 4 and norm(v) in a]
    return [hits[0]] if len(hits) == 1 else None


def parse_tf(answer, n):
    a = norm(answer)
    a = re.sub(r"prawdziwe|prawda|true", "P", a, flags=re.I)
    a = re.sub(r"fałszywe|fałsz|false", "F", a, flags=re.I)
    got = {}
    for m in re.finditer(r"(?m)(?:^|\s)(\d)\s*[\.\):–-]*\s*[–\-:]?\s*\**\s*\(?([pfPF])\b", a):
        got.setdefault(m.group(1), m.group(2).upper())
    if len(got) >= n:
        return [got.get(str(i + 1)) for i in range(n)]
    seq = re.findall(r"\b([PF])\b", answer)
    return seq[-n:] if len(seq) >= n else None


def parse_match(answer, key):
    a = norm(answer)
    out = {}
    for k, v in key.items():
        if v.isdigit():
            m = re.search(rf"(?m)(?:^|\s|fragment\s){k.lower()}\s*[\.\):–\-]*\s*[–\-:→>]*\s*(?:fragment\s*|źródło\s*)?(\d)", a)
            out[k] = m.group(1) if m else None
        else:
            alts = [re.sub(r"[\[\]]", "", x).strip() for x in re.split(r"/", v)]
            alts += [re.sub(r"\[.*?\]", "", x).strip() for x in re.split(r"/", v)]
            line = re.search(rf"(?m)(?:^|\s|fragment\s){k.lower()}\s*[\.\):–\-]*\s*[–\-:→>]\s*(.+)$", a)
            seg = line.group(1) if line else ""
            out[k] = v if any(x and norm(x) in seg for x in alts) else ("?" if not line else "WRONG")
    return out


def score(n_ok, n, max_points):
    if max_points == 1:
        return int(n_ok == n)
    if n == 3 and max_points == 2:
        return 2 if n_ok == 3 else 1 if n_ok == 2 else 0
    if max_points == n:
        return n_ok
    return int(max_points * n_ok // n)


def grade_closed(item, answer):
    key, t = item["key"], item["type"]
    if t == "closed_tf":
        got = parse_tf(answer, len(key))
        if got is None:
            return None, "nie rozpoznano P/F"
        ok = sum(g == key[str(i + 1)] for i, g in enumerate(got))
        return score(ok, len(key), item["max_points"]), f"odp {got} klucz {list(key.values())}"
    if t == "closed_match":
        got = parse_match(answer, key)
        if any(v in (None, "?") for v in got.values()):
            return None, f"niejednoznaczne dopasowanie {got}"
        ok = sum(got[k] == v for k, v in key.items())
        return score(ok, len(key), item["max_points"]), f"odp {got} klucz {key}"
    got = parse_choice(answer, len(key), item["question"])
    if got is None or any(g is None for g in got):
        return None, "nie rozpoznano wyboru"
    ok = sum(g == key[str(i + 1)] for i, g in enumerate(got))
    return score(ok, len(key), item["max_points"]), f"odp {got} klucz {list(key.values())}"


def review_md(run, dataset, items, answers, pending):
    out = [f"# {dataset} / {run}\n", "Oceń każdą pozycję wg zasad CKE (raport 02). Zapis: results/grades/"
           f"{dataset}/{run}.judge.json\n"]
    for iid in pending:
        it, ans = items[iid], answers[iid]
        body = strip_think(ans.get("answer", ""))
        limit = 6000 if it["type"] == "essay" else 1800
        out += [f"\n## {iid} ({it['max_points']} pkt, {it['type']})",
                f"**Polecenie:** {it['question'][:700]}",
                f"**Zasady:** {it['rubric'][:500]}",
                f"**Rozwiązanie CKE:** {it['solution'][:900]}",
                f"**Odpowiedź** (finish={ans.get('finish_reason')}, {len(body.split())} słów):\n\n{body[:limit]}"]
    return "\n".join(out)


def main(results_dir):
    results_dir = Path(results_dir)
    for f in sorted(results_dir.glob("*/*.jsonl")):
        dataset, run = f.parent.name, f.stem
        data_file = DATA / f"{dataset}.jsonl"
        if not data_file.exists():
            continue
        items = {json.loads(l)["id"]: json.loads(l) for l in open(data_file)}
        answers = {json.loads(l)["id"]: json.loads(l) for l in open(f)}
        auto, pending = {}, []
        for iid, it in items.items():
            ans = answers.get(iid, {})
            text = strip_think(ans.get("answer", ""))
            if not text.strip():
                auto[iid] = {"points": 0, "reason": "brak odpowiedzi" + (f" ({ans.get('error', '')[:80]})" if ans.get("error") else "")}
                continue
            if it.get("key"):
                pts, why = grade_closed(it, text)
                if pts is not None:
                    auto[iid] = {"points": pts, "reason": why}
                    continue
            pending.append(iid)
        gdir = results_dir / "grades" / dataset
        rdir = results_dir / "review" / dataset
        gdir.mkdir(parents=True, exist_ok=True)
        rdir.mkdir(parents=True, exist_ok=True)
        (gdir / f"{run}.auto.json").write_text(json.dumps(auto, ensure_ascii=False, indent=1))
        (rdir / f"{run}.md").write_text(review_md(run, dataset, items, answers, pending))
        print(f"{dataset}/{run}: auto {len(auto)} ({sum(v['points'] for v in auto.values())} pkt), do oceny {len(pending)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ROOT / "results")
