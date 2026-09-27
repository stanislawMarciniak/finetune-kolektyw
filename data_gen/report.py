"""Raport końcowy: data/sft/STATS.md i próbki w data/sft/samples/."""

import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_gen.common import COST_LOG, KB, ROOT, SFT, ensure_dirs, read_jsonl
from data_gen.sections import SECTIONS

SAMPLES = SFT / "samples"


def cost_table():
    per = Counter()
    for row in read_jsonl(COST_LOG):
        per[row.get("stage") or "?"] += float(row.get("cost_usd") or 0)
    return per


def type_counts(rows):
    return Counter(r.get("type") or "?" for r in rows)


def section_counts(rows):
    c = Counter()
    for r in rows:
        c[r.get("section") or "(brak)"] += 1
    return c


def md_record(row):
    lines = [
        f"### {row.get('id')}",
        f"- dział: {row.get('section')}",
        f"- typ: {row.get('type')} | punkty: {row.get('max_points')} | verified: {row.get('verified')}",
        f"- verify: {row.get('verify_note')}",
        "",
        "**Źródło**",
        "",
        (row.get("source_text") or row.get("text") or "—").strip(),
        "",
        "**Pytanie / temat**",
        "",
        (row.get("question") or row.get("subtopic") or row.get("title") or "").strip(),
        "",
        "**Format**",
        "",
        (row.get("answer_format") or "").strip() or "—",
        "",
        "**Odpowiedź**",
        "",
        (row.get("model_answer") or "").strip() or "—",
        "",
        "**Zasady**",
        "",
        (row.get("rubric") or "").strip() or "—",
        "",
    ]
    if row.get("score") is not None:
        lines.append(f"**Ocena:** {row.get('score')}/15")
        lines.append("")
    return "\n".join(lines)


def dump_samples(name, rows, k=15):
    rng = random.Random(2026)
    pick = rows if len(rows) <= k else rng.sample(rows, k)
    text = f"# {name}\n\nLiczba w zbiorze: {len(rows)}. Poniżej {len(pick)} losowych rekordów.\n\n"
    text += "\n".join(md_record(r) for r in pick)
    (SAMPLES / f"{name}.md").write_text(text, encoding="utf-8")


def main():
    ensure_dirs()
    SAMPLES.mkdir(parents=True, exist_ok=True)
    real = read_jsonl(SFT / "real_cke.jsonl")
    syn = read_jsonl(SFT / "synthetic_items.jsonl")
    rej = read_jsonl(SFT / "synthetic_rejected.jsonl")
    essays = read_jsonl(SFT / "essays.jsonl")
    ess_rej = read_jsonl(SFT / "essays_rejected.jsonl")
    notes = read_jsonl(KB)
    topics = read_jsonl(SFT / "real_essay_topics.jsonl")
    essay_topics = read_jsonl(SFT / "essay_topics.jsonl")
    costs = cost_table()

    syn_closed = [r for r in syn if str(r.get("type", "")).startswith("closed")]
    syn_open = [r for r in syn if r.get("type") == "open"]
    verified_syn = [r for r in syn if r.get("verified")]
    syn_pass = len(verified_syn) / len(syn) if syn else 0
    # odrzucone + przyjęte
    decided = len(syn) + len(rej)
    pass_rate = len(syn) / decided if decided else 0
    ess_decided = len(essays) + len(ess_rej)
    ess_rate = len(essays) / ess_decided if ess_decided else 0

    all_items = real + syn + essays
    sec = section_counts(all_items)
    note_sec = section_counts(notes)

    lines = []
    lines.append("# Statystyki zbioru SFT — matura z historii")
    lines.append("")
    lines.append("## Liczby rekordów")
    lines.append("")
    lines.append("| Zbiór | Rekordy |")
    lines.append("|---|---:|")
    lines.append(f"| E1 real_cke | {len(real)} |")
    lines.append(f"| E2 kompendium | {len(notes)} |")
    lines.append(f"| E3 synthetic (zostawione) | {len(syn)} |")
    lines.append(f"| E3 odrzucone | {len(rej)} |")
    lines.append(f"| E4 eseje ≥ 12/15 | {len(essays)} |")
    lines.append(f"| E4 eseje odrzucone | {len(ess_rej)} |")
    lines.append(f"| tematy wypracowań z arkuszy | {len(topics)} |")
    lines.append(f"| tematy użyte w E4 | {len(essay_topics)} |")
    lines.append("")
    lines.append("### Typy")
    lines.append("")
    lines.append("| Typ | real | synthetic | eseje |")
    lines.append("|---|---:|---:|---:|")
    types = ["closed_tf", "closed_choice", "closed_match", "closed_multi", "open", "essay"]
    rc, sc = type_counts(real), type_counts(syn)
    ec = type_counts(essays)
    for t in types:
        lines.append(f"| {t} | {rc.get(t, 0)} | {sc.get(t, 0)} | {ec.get(t, 0)} |")
    lines.append("")
    lines.append("## Weryfikacja")
    lines.append("")
    lines.append(f"- Syntetyczne zostawione / (zostawione + odrzucone): {len(syn)}/{decided} = {pass_rate:.1%}.")
    lines.append(f"- Wśród zostawionych syntetycznych pole verified=true: {len(verified_syn)}/{len(syn) or 1} = {syn_pass:.1%}.")
    lines.append(f"- Eseje ≥ 12/15: {len(essays)}/{ess_decided} = {ess_rate:.1%}.")
    img = sum(1 for r in real if r.get("needs_image"))
    lines.append(f"- Zadania real z needs_image=true: {img} / {len(real)}.")
    dedup = sum(1 for r in rej if "dedup" in str(r.get("reason") or r.get("verify_note") or ""))
    lines.append(f"- Odrzucenia z adnotacją dedup: {dedup}.")
    lines.append("")
    lines.append("## Koszt (szacunek usage × cena × 1,2)")
    lines.append("")
    lines.append("| Etap | USD |")
    lines.append("|---|---:|")
    total = 0.0
    for stage in ("E1", "E2", "E3", "E4"):
        val = costs.get(stage, 0.0)
        total += val
        lines.append(f"| {stage} | {val:.3f} |")
    other = sum(v for k, v in costs.items() if k not in ("E1", "E2", "E3", "E4"))
    total += other
    if other:
        lines.append(f"| inne | {other:.3f} |")
    lines.append(f"| **razem** | **{total:.3f}** |")
    lines.append("")
    lines.append("## Pokrycie działów")
    lines.append("")
    lines.append("| Dział | zadania (real+syn+esej) | notatki |")
    lines.append("|---|---:|---:|")
    for s in SECTIONS:
        lines.append(f"| {s} | {sec.get(s, 0)} | {note_sec.get(s, 0)} |")
    extra = set(sec) - set(SECTIONS) - {""}
    for s in sorted(extra):
        lines.append(f"| {s} | {sec.get(s, 0)} | {note_sec.get(s, 0)} |")
    empty = [s for s in SECTIONS if sec.get(s, 0) == 0]
    lines.append("")
    lines.append(f"Działy bez zadań: {len(empty)}.")
    if empty:
        lines.append("")
        for s in empty:
            lines.append(f"- {s}")
    lines.append("")
    lines.append("## Ograniczenia")
    lines.append("")
    lines.append("- Zadania wymagające mapy, ilustracji albo fotografii mają `needs_image=true` i nie nadają się do treningu czysto tekstowego bez osobnego opisu obrazu.")
    lines.append("- Arkusze formuły 2023 z lat 2023–2026 oraz egzamin próbny nie wchodzą do zbioru (zbiory testowe).")
    lines.append("- Z arkusza EHIP-R0-100-2305 usunięto 27 zadań identycznych ze zbiorem dev2023 (nakładają się na egzamin próbny / maturę 2023).")
    lines.append("- Kompendium ma po kilka notatek na dział (budżet E2 wyczerpał się przy 218 notatkach, nie przy pełnych 6 na każdy podtemat). Część notatek ma nieco poniżej 300 słów.")
    lines.append("- Żaden esej nie spadł poniżej 12/15 u sędziego luna; rozkład 12–15 wskazuje oceny zróżnicowane, ale próg mógł być łagodny. Jest ich 244, tuż pod celem 250–400, bo reszta limitu E4 zeszła na tematy.")
    lines.append("- Formuła 2015 z lat 2016, 2017, 2021 i 2022 nie ma w repozytorium własnych zasad oceniania, więc nie wyciągnięto z nich kluczy — tylko tematy wypracowań, jeśli były na końcu arkusza.")
    lines.append("- Tytuły działów XXVIII (kultura polskiego oświecenia), XLIV (kultura i nauka w II RP), XLIX (Zagłada) oraz LIX–LX (III RP) uzupełniono według podstawy; polityka zagraniczna II RP jest w podtematach XLII.")
    lines.append("- Klucze syntetyczne przeszły weryfikację drugim modelem, nie egzaminatorem CKE.")
    lines.append("")
    (SFT / "STATS.md").write_text("\n".join(lines), encoding="utf-8")

    dump_samples("real_cke", real)
    dump_samples("synthetic_closed", syn_closed)
    dump_samples("synthetic_open", syn_open)
    dump_samples("kompendium", notes)
    dump_samples("essays", essays)
    print("wrote", SFT / "STATS.md", flush=True)


if __name__ == "__main__":
    main()
