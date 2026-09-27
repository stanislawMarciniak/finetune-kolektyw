"""Audyt odpowiedzi: straty punktów finałów i wariantów bliskich najlepszym wg typu zadania, epoki i rodzaju błędu.

Korzysta tylko z istniejących ocen (results/grades/<zbiór>/<przebieg>.{auto,judge}.json), odpowiedzi i debug.jsonl
z runs/. Bez GPU i bez sędziego.

  python eval/audit.py                                   # grupy z eval/audit_groups.json -> stdout (markdown)
  python eval/audit.py --out /tmp/audit.md
  python eval/audit.py --add 'T1-vote=T1:T1-final:test2024_v2=runA,runB;test2025_v2=runA'   # nowy wariant ad hoc
  python eval/audit.py --only T1-final,T1-vote           # tylko wybrane grupy (+ ich 'vs')
  python eval/audit.py --item test2024_v2/25             # zrzut odpowiedzi i ocen jednego zadania we wszystkich grupach

Strata = max − średnia punktów z seedów grupy. Rodzaj błędu przypisywany per przebieg (heurystyki na ocenie sędziego,
debug.jsonl i odpowiedzi; ręczne etykiety z raportu 12 jako priorytet dla T1/T2), strata rozdzielana proporcjonalnie.
Zadanie 2024/21 (filtr treści sędziego) poza mianownikiem.
"""

import argparse
import ast
import json
import random
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRADES = ROOT / "results/grades"
RUNS = ROOT / "runs"
DATA = ROOT / "eval/data"
MAIN = ["test2024_v2", "test2025_v2"]
CONFIRM = ["test2026_v2"]
SETS = MAIN + CONFIRM
EXCLUDE = {("test2024_v2", "21")}

EPOCHS = ["staro", "sred", "nowo", "xix", "1914-39", "iiws", "1945-89", "po1989"]
TYPES = ["closed_choice", "closed_tf", "closed_match", "podaj", "rozstrz", "wyjasnij", "essay"]
ERRORS = ["wiedza", "obraz", "tekst", "polecenie", "niepelna", "rozumowanie", "harness", "sedzia",
          "esej-A-aspekty", "esej-A-bledy", "esej-B-spojnosc"]
ERR_PL = {"wiedza": "wiedza/fakt", "obraz": "źle odczytany obraz", "tekst": "źle odczytany tekst źródła",
          "polecenie": "polecenie/format", "niepelna": "odpowiedź niepełna", "rozumowanie": "rozumowanie/logika",
          "harness": "harness (fallback/urwanie/błąd)", "sedzia": "sędzia/grader za surowy (tylko ewaluacja)",
          "esej-A-aspekty": "esej A: aspekty (powierzchowne/brak)", "esej-A-bledy": "esej A: błędy merytoryczne",
          "esej-B-spojnosc": "esej B: spójność/długość"}

# Ręczne kategorie z raportu 12 (/tmp/ana/taxo.py): a polecenie, b niepełna, c tekst, d obraz, e wiedza,
# f harness/format (rozstrzygane niżej), g sędzia, h esej.
PRIOR = {"T1": {
    "test2024_v2": {"1": "d", "5.1": "d", "7": "e", "8.1": "e", "10": "e", "11.1": "e", "12.1": "d", "14.1": "d", "15.2": "c",
                    "19.1": "d", "19.2": "d", "20.2": "c", "23.2": "d", "25": "d"},
    "test2025_v2": {"3.1": "g", "4": "f", "5.1": "f", "7.1": "g", "9.3": "e", "11.1": "f", "14.1": "d", "14.2": "d", "18": "d",
                    "19": "e", "21.1": "f", "22": "e"},
    "test2026_v2": {"6.2": "e", "12.2": "d", "14.2": "d", "17": "c", "18.2": "c", "19.1": "c", "24": "d"}},
    "T2": {
    "test2024_v2": {"2": "e", "4": "d", "5.1": "d", "5.2": "e", "6": "b", "7": "e", "11.1": "f", "12.3": "d", "13": "b",
                    "14.1": "d", "15.2": "c", "16.1": "e", "18": "b", "19.1": "d", "19.2": "d", "20.2": "c", "22.2": "c",
                    "23.1": "d", "23.2": "d", "24": "d", "25": "d"},
    "test2025_v2": {"2": "b", "3.1": "d", "5.1": "f", "6": "d", "8": "d", "10": "d", "12": "d", "14.1": "d", "15.2": "c",
                    "16.1": "d", "16.2": "d", "17.2": "e", "18": "d", "19": "b", "21.1": "d", "21.2": "e", "22": "e", "23": "d"},
    "test2026_v2": {"1": "b", "2": "f", "3.1": "d", "3.2": "e", "4.1": "d", "5.1": "b", "7": "d", "10.1": "c", "12.2": "d",
                    "13": "b", "14.2": "b", "14.3": "e", "15.2": "d", "18.1": "d", "18.2": "d", "19.1": "d", "20": "b",
                    "22": "e", "24": "d", "25": "d"}}}
PRIOR_MAP = {"a": "polecenie", "b": "niepelna", "c": "tekst", "d": "obraz", "e": "wiedza", "f": "polecenie", "g": "sedzia"}

RX_INCOMPLETE = re.compile(r"brak (wymaganego |jakiegokolwiek )?uzasadnieni|\bnie podano (drugiego|uzasadnieni|imienia|nazw|"
                           r"żadnego|wymagan|cech)|podano (tylko |jedynie )?jedn|tylko jedn|jedynie jedn|niepełn|brak drugi|"
                           r"\bnie odwołano się do (obu|drugiego|źródła|treści)|brak odwołania|pominięto|brak (drugiej|drugiego|"
                           r"wskazania|cechy|rozstrzygnięcia)|\bnie wskazano", re.I)
RX_FORMAT = re.compile(r"numer\w* zamiast|zamiast nazw|niezgodn\w* z poleceniem|nie odpowiada na polecenie|format", re.I)
RX_IMGWORD = re.compile(r"map|rysun|karykatur|plakat|ilustracj|fotografi|znacz|herb|monet|relief|rycin|drzeworyt|obraz|plan\b|"
                        r"planie|ulotk|czasopism|gazet|banknot|medal|okładk|grafi|wykres|tabel|kadr|pomnik|budowl|naczy", re.I)
RX_WRONG = re.compile(r"błędn|niepoprawn|myl|nie przedstawia|zamiast|niewłaściw|nie ukazuje|nieprawidłow|niezgodn|"
                      r"nietrafn|nie dotyczy|inn\w+ (wydarzen|bitw|powstan|wojn|okres)", re.I)
RX_FACT = re.compile(r"błąd merytoryczn|błędn\w* (dat|rok|nazw|imi|informacj|twierdz|przypisan|stwierdz)|nieprawd|"
                     r"faktograf|anachroni|pomylon|nieścisł", re.I)
RX_TEXT = re.compile(r"źródł\w* 1|źródł\w* 2|tekst|fragment|dokument|relacj|autor|pieśn|list", re.I)
SYN = {"usa": "stany zjednoczone", "stany zjednoczone ameryki": "stany zjednoczone", "anjou": "andegawenowie",
       "rzeczpospolita obojga narodow": "polska", "rzeczpospolita": "polska"}
ROMAN = re.compile(r"\b[ivxl]+\b")


def strip_acc(s):
    s = s.replace("ł", "l").replace("Ł", "L")
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def norm(s):
    s = strip_acc(str(s)).lower()
    s = re.sub(r"[\[\]()*_.,;:\"„”']", " ", s)
    s = re.sub(r"\b(zakon|dynastia|fragment|krol|cesarz)\b", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return SYN.get(s, s)


def lenient_eq(ans, key):
    """Czy odpowiedź zamknięta jest równoważna kluczowi (synonimy, odmiana, literówka) — test surowości gradera."""
    a = norm(ans)
    for alt in str(key).split("/"):
        k = norm(alt)
        if not k:
            continue
        if a == k:
            return True
        if set(ROMAN.findall(a)) != set(ROMAN.findall(k)):
            continue
        ks = [t[:5] for t in k.split() if len(t) >= 4]
        as_ = {t[:5] for t in a.split() if len(t) >= 4}
        if ks and all(t in as_ for t in ks):
            return True
    return False


# ---------------------------------------------------------------- dane

def load_items():
    lab = json.load(open(ROOT / "eval/audit_labels.json"))
    items = {}
    for ds in SETS:
        for l in open(DATA / f"{ds}.jsonl", encoding="utf-8"):
            it = json.loads(l)
            if (ds, it["id"]) in EXCLUDE:
                continue
            L = lab["items"].get(ds, {}).get(it["id"], {})
            q = it["question"].strip()
            t = it["type"]
            if t == "open":
                if re.match(r"Rozstrzygnij", q):
                    t = "rozstrz"
                elif re.match(r"(Podaj|Wymień|Uzupełnij|Wpisz)", q):
                    t = "podaj"
                else:
                    t = "wyjasnij"
            src = re.sub(r"(Na podstawie|https?://)\S*[^\n]*", "", it.get("sources") or "")
            has_text = len(re.sub(r"\[Obraz[^\]]*\]", "", src).strip()) > 200
            img = bool(it.get("images"))
            items[(ds, it["id"])] = {
                "ds": ds, "id": it["id"], "max": float(it["max_points"]), "type": t, "img": img,
                "img_kind": L.get("img", "—") if img else "brak obrazu",
                "src": ("tekst+obraz" if has_text else "obraz") if img else ("tekst" if has_text else "bez źródła"),
                "epoch": L.get("epoch", "?"), "chrono": bool(L.get("chrono")),
                "question": it["question"], "solution": it.get("solution") or "", "key": it.get("key"),
            }
    return items, lab.get("essay_topics", {})


_cache = {}


def run_data(ds, run):
    k = (ds, run)
    if k in _cache:
        return _cache[k]
    g = {}
    for suf in ("auto", "judge"):
        f = GRADES / ds / f"{run}.{suf}.json"
        if f.exists():
            for iid, v in json.load(open(f)).items():
                v = dict(v)
                v["_src"] = suf
                g[iid] = v
    ans, dbg = {}, {}
    d = RUNS / ds / run
    if (d / "answers.json").exists():
        a = json.load(open(d / "answers.json"))
        ans = {x["id"]: x.get("answer") or "" for x in a.get("answers", [])}
    if (d / "debug.jsonl").exists():
        for l in open(d / "debug.jsonl"):
            try:
                r = json.loads(l)
                dbg[r["id"]] = r
            except Exception:
                pass
    # Przebieg scalony (--only-ids + --merge-from): zadania spoza only_ids biorą oceny i odpowiedzi
    # z przebiegu źródłowego, bo judge_reuse mógł im skopiować oceny innego sędziego.
    meta = d / "meta.json"
    if g and meta.exists():
        m = json.load(open(meta)).get("args") or {}
        if isinstance(m, str):
            try:
                m = eval(m, {"inf": float("inf"), "nan": float("nan"), "Namespace": dict})
            except Exception:
                m = {}
        if not isinstance(m, dict):
            m = vars(m) if hasattr(m, "__dict__") else {}
        only, src = m.get("only_ids"), m.get("merge_from")
        base = run_data(ds, Path(src).name) if only and src and Path(src).name != run else None
        if base:
            keep = set(only.split(","))
            bg, ba, bd = base
            g = {i: v for i, v in g.items() if i in keep} | {i: v for i, v in bg.items() if i not in keep}
            ans = {i: v for i, v in ans.items() if i in keep} | {i: v for i, v in ba.items() if i not in keep}
            dbg = {i: v for i, v in dbg.items() if i in keep} | {i: v for i, v in bd.items() if i not in keep}
    _cache[k] = (g, ans, dbg) if g else None
    return _cache[k]


def points(g, iid):
    v = g.get(iid)
    if not v or v.get("filtered") or v.get("points") is None or isinstance(v.get("points"), str):
        return None
    return float(v["points"])


# ---------------------------------------------------------------- klasyfikacja błędu

def truthy(x):
    return str(x).lower() in ("true", "1")


def classify(track, it, v, ans, dbg):
    """-> dict kategoria -> utracone punkty (dla tego jednego przebiegu)."""
    lost = it["max"] - float(v["points"])
    if lost <= 0:
        return {}
    ds, iid = it["ds"], it["id"]
    if it["type"] == "essay":
        if "historical_before" in v:
            comps = sum(c.get("points", 0) for c in v.get("components", []))
            before = v.get("historical_before", comps)
            out = {"esej-A-aspekty": max(0.0, 12 - before), "esej-A-bledy": float(v.get("deduction", 0)),
                   "esej-B-spojnosc": max(0.0, 3 - float(v.get("coherence", 0)))}
            s = sum(out.values())
            if s > 0 and abs(s - lost) > 0.01:
                out = {k: x * lost / s for k, x in out.items()}
            return {k: x for k, x in out.items() if x > 0}
        return {"esej-A-aspekty": lost}
    if dbg and (dbg.get("error") not in (None, "None", "") or not (ans or "").strip()):
        return {"harness": lost}
    reason = v.get("reason", "") or ""
    if v["_src"] == "auto":
        m = re.match(r"odp (.*) klucz (.*)$", reason, re.S)
        odp = key = None
        if m:
            try:
                odp, key = ast.literal_eval(m.group(1)), ast.literal_eval(m.group(2))
            except Exception:
                pass
        if odp in (None, [], {}, ""):
            return {"polecenie": lost}
        if isinstance(key, dict) and it["type"] == "closed_match" and not all(re.fullmatch(r"\d+", str(x)) for x in key.values()):
            nums = re.findall(r"^\s*(?:Fragment\s+)?[A-F]\s*[:–-]\s*\d+\s*\.?\s*$", ans or "", re.M)
            if len(nums) >= len(key):
                return {"polecenie": lost}
        if isinstance(odp, dict) and isinstance(key, dict):
            raw = dict(re.findall(r"^\s*(?:Fragment\s+)?([A-F])\s*[:–-]\s*(.+?)\s*$", ans or "", re.M))
            odp = {k: (raw.get(k, x) if x == "WRONG" else x) for k, x in odp.items()}
            if any(re.fullmatch(r"\s*\d+\s*", str(odp.get(k, ""))) for k in key) and not all(
                    re.fullmatch(r"\d+", str(x)) for x in key.values()):
                return {"polecenie": lost}
            if all(lenient_eq(odp.get(k, ""), key[k]) for k in key):
                return {"sedzia": lost}
        p = PRIOR.get(track, {}).get(ds, {}).get(iid)
        if p and p not in ("f", "g", "h"):
            return {PRIOR_MAP[p]: lost}
        return {"wiedza": lost}
    if dbg and truthy(dbg.get("fallback")):
        return {"harness": lost}
    if RX_INCOMPLETE.search(reason) and not RX_WRONG.search(reason.split(".")[0]):
        return {"niepelna": lost}
    if RX_FORMAT.search(reason):
        return {"polecenie": lost}
    p = PRIOR.get(track, {}).get(ds, {}).get(iid)
    if p and p != "h" and not (track == "T2" and it["img"]):  # T2: odpowiedzi z obrazem zmienione przez OCR/caption
        return {PRIOR_MAP[p]: lost}
    if it["img"] and RX_IMGWORD.search(reason) and RX_WRONG.search(reason):
        return {"obraz": lost}
    if RX_FACT.search(reason):
        return {"wiedza": lost}
    if RX_INCOMPLETE.search(reason):
        return {"niepelna": lost}
    if RX_TEXT.search(reason) and RX_WRONG.search(reason):
        return {"tekst": lost}
    return {"wiedza" if it["type"] == "podaj" else "rozumowanie": lost}


# ---------------------------------------------------------------- agregacja

def collect(groups, items):
    """-> res[group][(ds,iid)] = {"pts": [..], "err": {cat: lost/n}, "runs": [(run, pts, ans, reason)]}"""
    res = {}
    for gname, G in groups.items():
        R = {}
        for ds, runs in G["runs"].items():
            loaded = []
            for spec in runs:
                r, _, flt = spec.partition("|")
                d = run_data(ds, r)
                if d:
                    loaded.append((r, d, flt))
            for (d_, iid), it in items.items():
                if d_ != ds:
                    continue
                pts, errs, det = [], defaultdict(float), []
                for r, (g, ans, dbg), flt in loaded:
                    if (flt == "essay") != (it["type"] == "essay") and flt in ("essay", "noessay"):
                        continue
                    p = points(g, iid)
                    if p is None:
                        continue
                    pts.append(p)
                    det.append((r, p, ans.get(iid, ""), g[iid].get("reason", ""), g[iid]))
                    for c, x in classify(G["track"], it, g[iid], ans.get(iid, ""), dbg.get(iid)).items():
                        errs[c] += x
                if pts:
                    n = len(pts)
                    R[(ds, iid)] = {"pts": pts, "mean": sum(pts) / n, "lost": it["max"] - sum(pts) / n,
                                    "err": {c: x / n for c, x in errs.items()}, "runs": det}
        res[gname] = R
    return res


def score(R, items, sets):
    got = mx = 0.0
    for (ds, iid), r in R.items():
        if ds in sets:
            got += r["mean"]
            mx += items[(ds, iid)]["max"]
    return got, mx


def essay_epoch(r, ds, topics):
    t = [str(x[4].get("topic")) for x in r["runs"] if x[4].get("topic")]
    if not t:
        return "?"
    return topics.get(ds, {}).get(max(set(t), key=t.count), "?")


def fmt(x, nd=1):
    return f"{x:.{nd}f}" if abs(x) >= 0.05 else ("0" if nd else "0")


def table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(out) + "\n"


def cross(res, items, topics, gnames, key, sets, cats=None):
    """Strata (pkt) wg wymiaru key dla grup; zwraca (kategorie, {g: {kat: [lost, max]}})."""
    acc = {g: defaultdict(lambda: [0.0, 0.0]) for g in gnames}
    for g in gnames:
        for (ds, iid), r in res[g].items():
            if ds not in sets:
                continue
            it = items[(ds, iid)]
            if key == "err":
                for c, x in r["err"].items():
                    acc[g][c][0] += x
                continue
            k = it[key] if key != "epoch" else (essay_epoch(r, ds, topics) + " (esej)" if it["type"] == "essay" else it["epoch"])
            acc[g][k][0] += r["lost"]
            acc[g][k][1] += it["max"]
    allk = set().union(*[set(a) for a in acc.values()])
    if cats:
        ks = [c for c in cats if c in allk] + sorted(allk - set(cats))
    else:
        ks = sorted(allk)
    return ks, acc


# ---------------------------------------------------------------- raport

def report(groups, items, topics, res):
    L = []
    finals = [g for g, G in groups.items() if G["role"] == "final"]
    L.append("## A. Wyniki grup (średnia z seedów, sędzia luna)\n")
    rows = []
    for g, G in groups.items():
        a, am = score(res[g], items, MAIN)
        b, bm = score(res[g], items, CONFIRM)
        ns = {ds: len(v) for ds, v in G["runs"].items()}
        rows.append([g, G["label"], G["role"], f"{100 * a / am:.1f}%" if am else "—", f"{100 * b / bm:.1f}%" if bm else "—",
                     ", ".join(f"{ds[4:8]}×{n}" for ds, n in ns.items())])
    L.append(table(["grupa", "opis", "rola", "2024+2025", "2026", "seedy"], rows))

    for title, key, cats in [("typ zadania", "type", TYPES), ("epoka", "epoch", EPOCHS), ("rodzaj błędu", "err", ERRORS),
                             ("obraz", "img_kind", None), ("rodzaj źródła", "src", None)]:
        L.append(f"## B. Finały — strata wg: {title} (pkt; 2024+2025 = 119 pkt, 2026 = 60 pkt)\n")
        ks1, a1 = cross(res, items, topics, finals, key, MAIN, cats)
        ks2, a2 = cross(res, items, topics, finals, key, CONFIRM, cats)
        ks = ks1 + [k for k in ks2 if k not in ks1]
        hdr = ["kategoria"] + [f"{g} 24+25" for g in finals] + [f"{g} 2026" for g in finals]
        if key != "err":
            hdr.insert(1, "max 24+25")
        rows = []
        for k in ks:
            row = [ERR_PL.get(k, k) if key == "err" else k]
            if key != "err":
                row.append(fmt(max(a1[g][k][1] for g in finals), 0))
            row += [fmt(a1[g][k][0]) for g in finals] + [fmt(a2[g][k][0]) for g in finals]
            rows.append(row)
        rows.append(["**razem**"] + ([""] if key != "err" else []) +
                    [fmt(sum(v[0] for v in a1[g].values())) for g in finals] + [fmt(sum(v[0] for v in a2[g].values())) for g in finals])
        L.append(table(hdr, rows))

    # typ × epoka (suma finałów, 3 arkusze)
    L.append("## C. Typ × epoka — strata finałów razem (pkt, 3 arkusze, suma T1+T2+T3)\n")
    acc = defaultdict(float)
    for g in finals:
        for (ds, iid), r in res[g].items():
            it = items[(ds, iid)]
            ep = essay_epoch(r, ds, topics) if it["type"] == "essay" else it["epoch"]
            acc[(it["type"], ep)] += r["lost"]
    eps = [e for e in EPOCHS if any(acc.get((t, e)) for t in TYPES)]
    rows = [[t] + [fmt(acc.get((t, e), 0)) for e in eps] + [fmt(sum(acc.get((t, e), 0) for e in eps))] for t in TYPES]
    rows.append(["**razem**"] + [fmt(sum(acc.get((t, e), 0) for t in TYPES)) for e in eps] + [fmt(sum(acc.values()))])
    L.append(table(["typ \\ epoka"] + eps + ["razem"], rows))

    # błąd × typ per finał
    for g in finals:
        L.append(f"## D. {g}: rodzaj błędu × typ zadania (pkt, 3 arkusze)\n")
        acc = defaultdict(float)
        for (ds, iid), r in res[g].items():
            for c, x in r["err"].items():
                acc[(c, items[(ds, iid)]["type"])] += x
        errs = [e for e in ERRORS if any(acc.get((e, t)) for t in TYPES)]
        rows = [[ERR_PL[e]] + [fmt(acc.get((e, t), 0)) for t in TYPES] + [fmt(sum(acc.get((e, t), 0) for t in TYPES))] for e in errs]
        L.append(table(["błąd \\ typ"] + TYPES + ["razem"], rows))

    # trudne i rozbieżne
    def frac(g, k):
        r = res[g].get(k)
        return None if r is None else r["mean"] / items[k]["max"]

    def top_err(g, k):
        r = res[g].get(k)
        if not r or not r["err"]:
            return ""
        return max(r["err"].items(), key=lambda x: x[1])[0]

    L.append("## E. Zadania trudne dla wszystkich finałów (średnio ≤ 34% punktów w każdym)\n")
    rows = []
    for k, it in items.items():
        fs = [frac(g, k) for g in finals]
        if any(f is None for f in fs) or it["type"] == "essay":
            continue
        if all(f <= 0.34 for f in fs):
            rows.append([f"{k[0][4:8]}/{k[1]}", it["type"], it["epoch"], it["img_kind"], fmt(it["max"], 0)] +
                        [f"{fmt(res[g][k]['mean'], 2)} ({top_err(g, k)})" for g in finals])
    L.append(table(["zadanie", "typ", "epoka", "obraz", "max"] + [f"{g} śr. pkt (błąd)" for g in finals], rows))

    L.append("## F. Rozbieżności między finałami (różnica ≥ 67 pp udziału punktów)\n")
    rows = []
    for k, it in items.items():
        fs = {g: frac(g, k) for g in finals}
        if any(f is None for f in fs.values()) or it["type"] == "essay":
            continue
        if max(fs.values()) - min(fs.values()) >= 0.67:
            win = [g for g, f in fs.items() if f >= 0.67]
            lose = [f"{g}: {top_err(g, k)}" for g, f in fs.items() if f <= 0.34]
            rows.append([f"{k[0][4:8]}/{k[1]}", it["type"], it["epoch"], it["img_kind"],
                         " ".join(f"{g[:2]}={fmt(100 * f, 0)}%" for g, f in fs.items()), ", ".join(win), "; ".join(lose)])
    L.append(table(["zadanie", "typ", "epoka", "obraz", "udział pkt", "rozwiązuje", "nie rozwiązuje (błąd)"], rows))

    L.append("## I. Eseje — statystyki ocen (wszystkie próbki grupy, 3 arkusze)\n")
    rows = []
    for g, G in groups.items():
        ev = [x[4] for (ds, iid), r in res[g].items() if items[(ds, iid)]["type"] == "essay" for x in r["runs"]]
        ev = [v for v in ev if "components" in v]
        if not ev:
            continue
        lv = defaultdict(int)
        for v in ev:
            for c in v["components"]:
                lv[c.get("level", "?")] += 1
        n = len(ev)
        rows.append([g, n, f"{sum(v['points'] for v in ev) / n:.2f}", f"{sum(v.get('historical_before', 0) for v in ev) / n:.2f}",
                     f"{sum(v.get('errors', 0) for v in ev) / n:.2f}", f"{sum(v.get('deduction', 0) for v in ev) / n:.2f}",
                     f"{sum(v.get('coherence', 0) for v in ev) / n:.2f}",
                     " / ".join(str(lv.get(k, 0)) for k in ("bogata", "zadowalająca", "powierzchowna", "brak"))])
    L.append(table(["grupa", "esejów", "śr. pkt /15", "śr. A przed odjęciem /12", "śr. błędów", "śr. odjęcie", "śr. B /3",
                    "elementy b / z / p / brak"], rows))

    # przed (poprzedni finał) vs obecny finał
    pairs = [(G["before"], g) for g, G in groups.items() if G.get("before") in res and "@" not in g]
    if pairs:
        L.append("## H. Poprzedni stan vs obecny finał — strata (pkt), wg typu, epoki i błędu\n")
    for bg, fg in pairs:
        L.append(f"### {fg} (przed: {bg})\n")
        for title, key, cats in [("typ zadania", "type", TYPES), ("epoka", "epoch", EPOCHS), ("rodzaj błędu", "err", ERRORS)]:
            k1, a1 = cross(res, items, topics, [bg, fg], key, MAIN, cats)
            k2, a2 = cross(res, items, topics, [bg, fg], key, CONFIRM, cats)
            ks = k1 + [k for k in k2 if k not in k1]
            rows = []
            for k in ks:
                b1, f1, b2, f2 = a1[bg][k][0], a1[fg][k][0], a2[bg][k][0], a2[fg][k][0]
                if max(b1, f1, b2, f2) < 0.05:
                    continue
                rows.append([ERR_PL.get(k, k) if key == "err" else k, fmt(b1), fmt(f1), f"{f1 - b1:+.1f}", fmt(b2), fmt(f2), f"{f2 - b2:+.1f}"])
            tot = [sum(v[0] for v in a[g].values()) for a, g in ((a1, bg), (a1, fg), (a2, bg), (a2, fg))]
            rows.append(["**razem**", fmt(tot[0]), fmt(tot[1]), f"{tot[1] - tot[0]:+.1f}", fmt(tot[2]), fmt(tot[3]), f"{tot[3] - tot[2]:+.1f}"])
            L.append(f"Wg: {title}\n")
            L.append(table(["kategoria", "przed 24+25", "finał 24+25", "Δ", "przed 2026", "finał 2026", "Δ"], rows))

    # warianty bliskie najlepszym
    L.append("## G. Warianty bliskie najlepszym vs odniesienie (Δ pkt = średnia wariantu − średnia odniesienia, te same zadania)\n")
    for g, G in groups.items():
        base = G.get("vs")
        if not base or base not in res:
            continue
        A, B = res[g], res[base]
        common = [k for k in A if k in B]
        d = {k: A[k]["mean"] - B[k]["mean"] for k in common}
        per = {ds: sum(x for k, x in d.items() if k[0] == ds) for ds in SETS}
        mx = {ds: sum(items[k]["max"] for k in common if k[0] == ds) for ds in SETS}
        main_d = sum(per[ds] for ds in MAIN)
        main_mx = sum(mx[ds] for ds in MAIN)
        ess = sum(x for k, x in d.items() if items[k]["type"] == "essay" and k[0] in MAIN)
        up = sorted([(x, k) for k, x in d.items() if x > 0.01], reverse=True)
        dn = sorted([(x, k) for k, x in d.items() if x < -0.01])
        L.append(f"### {g} vs {base} — {G['label']}\n")
        L.append(f"- Δ 2024+2025: **{main_d:+.2f} pkt ({100 * main_d / main_mx:+.1f} pp)**" if main_mx else "- Δ 2024+2025: —")
        L.append(f"  (w tym esej {ess:+.2f} pkt; bez eseju {main_d - ess:+.2f}); "
                 + "; ".join(f"{ds[4:8]}: {per[ds]:+.2f}" for ds in SETS if mx[ds]))
        n_up, n_dn = len(up), len(dn)
        L.append(f"- zadania lepsze / gorsze: {n_up} / {n_dn} (suma +{sum(x for x, _ in up):.2f} / {sum(x for x, _ in dn):.2f} pkt)")
        rng = random.Random(0)
        md = [x for k, x in d.items() if k[0] in MAIN]
        if md:
            bs = sorted(sum(rng.choice(md) for _ in md) for _ in range(2000))
            L.append(f"- bootstrap po zadaniach (2024+2025, tylko szum zadań, bez szumu seedów): 95% CI "
                     f"[{bs[50]:+.1f}, {bs[1949]:+.1f}] pkt")
        for dim in ("type", "epoch", "img"):
            acc = defaultdict(float)
            for k, x in d.items():
                acc["esej" if dim == "epoch" and items[k]["type"] == "essay" else items[k][dim]] += x
            nz = {kk: v for kk, v in acc.items() if abs(v) >= 0.05}
            if nz:
                L.append(f"- wg {dim}: " + ", ".join(f"{kk}: {v:+.2f}" for kk, v in sorted(nz.items(), key=lambda z: -abs(z[1]))))
        L.append("- największe zmiany: " + ", ".join(f"{k[0][4:8]}/{k[1]} {x:+.2f}" for x, k in (up[:5] + dn[:5])))
        L.append("")
    return "\n".join(L)


def dump_item(groups, items, res, key):
    ds, iid = key.split("/")
    it = items[(ds, iid)]
    print(f"# {ds}/{iid} [{it['type']}, {it['epoch']}, {it['img_kind']}, max {it['max']}]\nQ: {it['question'][:500]}\nKLUCZ: {it['solution'][:500]}\n")
    for g in groups:
        r = res[g].get((ds, iid))
        if not r:
            continue
        print(f"## {g}: {r['pts']} err={ {c: round(x, 2) for c, x in r['err'].items()} }")
        for run, p, ans, reason, _ in r["runs"]:
            print(f"  - {run}: {p} | ODP: {re.sub(chr(10), ' / ', ans)[:400]}\n    SĘDZIA: {reason[:300]}")


def parse_add(spec):
    # NAME=TRACK:VS:ds=run,run;ds=run
    name, rest = spec.split("=", 1)
    track, vs, runs = rest.split(":", 2)
    rr = {}
    for part in runs.split(";"):
        ds, lst = part.split("=")
        rr[ds] = lst.split(",")
    return name, {"track": track, "role": "near" if vs else "ref", "vs": vs or None, "label": name, "runs": rr}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--groups", default=str(ROOT / "eval/audit_groups.json"))
    p.add_argument("--add", action="append", default=[], help="NAME=TRACK:VS:ds=run,run;ds=run")
    p.add_argument("--only", default="")
    p.add_argument("--out")
    p.add_argument("--item", action="append", default=[])
    p.add_argument("--json", help="zapis per zadanie/grupa (średnie, strata, błędy) do pliku JSON")
    a = p.parse_args()
    groups = json.load(open(a.groups))["groups"]
    for s in a.add:
        n, G = parse_add(s)
        groups[n] = G
    if a.only:
        want = set(a.only.split(","))
        want |= {groups[g]["vs"] for g in list(want) if groups.get(g, {}).get("vs")}
        want |= {g for g, G in groups.items() if G["role"] == "final" and G["track"] in {groups[w]["track"] for w in want}}
        groups = {g: G for g, G in groups.items() if g in want}
    for g, G in list(groups.items()):
        if G.get("vs_runs"):
            bname = f"{G['vs']}@{g}"
            groups[bname] = {**groups[G["vs"]], "role": "ref", "runs": G["vs_runs"], "label": f"{G['vs']} (seedy sparowane z {g})"}
            G["vs"] = bname
    items, topics = load_items()
    res = collect(groups, items)
    if a.item:
        for k in a.item:
            dump_item(groups, items, res, k)
        return
    md = report(groups, items, topics, res)
    if a.json:
        out = {g: {f"{ds}/{iid}": {"mean": r["mean"], "lost": r["lost"], "err": r["err"], "pts": r["pts"],
                                   "type": items[(ds, iid)]["type"], "epoch": items[(ds, iid)]["epoch"]}
                   for (ds, iid), r in R.items()} for g, R in res.items()}
        json.dump(out, open(a.json, "w"), ensure_ascii=False, indent=1)
    if a.out:
        Path(a.out).write_text(md, encoding="utf-8")
    else:
        print(md)


if __name__ == "__main__":
    main()
