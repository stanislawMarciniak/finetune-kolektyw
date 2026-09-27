"""Harness egzaminacyjny: exam.json (+ images/) -> answers.json, przez serwer zgodny z OpenAI (llama-server).

    python harness/run_exam.py --exam assets/mock-2023 --out runs/mock/gemma --base-url http://127.0.0.1:8080/v1 \
        --vision --think essay,rozstrz,open,closed --rag hyde --rag-types podaj,open,essay --index data/kb/polqa_index

Wynik: <out>/answers.json (format organizatorów) + <out>/debug.jsonl (surowe odpowiedzi, myślenie, kontekst RAG).
Typ zadania wynika z `answer_format`. Odpowiedzi zamknięte są normalizowane do dokładnej składni `answer_format`.
"""

import argparse
import base64
import json
import re
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from openai import APIConnectionError, APITimeoutError, InternalServerError, OpenAI

sys.path.insert(0, str(Path(__file__).resolve().parent))
from topics import item_scope  # noqa: E402

SYSTEM = ("Rozwiąż zadanie z historii po polsku. Otrzymujesz polecenie, teksty źródeł oraz osobno obrazy źródeł (jeśli są). "
          "Wykorzystaj źródła i własną wiedzę zgodnie z poleceniem. Udziel tylko odpowiedzi na podane zadanie. "
          "Nie masz dostępu do narzędzi ani internetu.")
RAG_HEAD = "Materiały pomocnicze (fragmenty encyklopedii; mogą być częściowo nieistotne – korzystaj tylko z pasujących):"
# prompt z pierwszych przebiegów na Modal (H-N1): zadania bez obrazów dostawały inny system i nie miały dopisku o formacie
SYSTEM_TEXT_LEGACY = ("Rozwiąż zadanie z historii po polsku. Otrzymujesz tekst źródeł, a obrazy zastąpiono opisami. "
                      "Wykorzystaj źródła i własną wiedzę zgodnie z poleceniem. Udziel tylko odpowiedzi na podane zadanie. "
                      "Nie dopisuj innych zadań. Nie masz dostępu do narzędzi ani internetu.")
HYDE_PROMPT = ("Nie rozwiązuj zadania. Napisz jedno–dwa zdania w stylu hasła encyklopedii, które zawierałyby potrzebne fakty "
               "(nazwy, daty, postacie).")
CAREFUL = ("Pisz tylko o faktach, których jesteś pewien. Każdy błąd merytoryczny (zła data, postać, nazwa) obniża ocenę, "
           "więc lepiej pominąć niepewny szczegół niż podać błędny. Omów wszystkie elementy wymienione w poleceniu.")
CHOOSE_PROMPT = ("Nie pisz jeszcze wypracowania. Oceń w skali 1–5, jak dobrze znasz fakty potrzebne do każdego z tematów, "
                 "i wybierz temat, o którym wiesz najwięcej. Odpowiedz dokładnie w formacie:\nTemat 1: <ocena>\nTemat 2: <ocena>\n"
                 "Temat 3: <ocena>\nWybór: <numer>")
ROZSTRZ_HINT = ("Wskazówka: najpierw ustal, czego dotyczy każde źródło, na podstawie konkretnych szczegółów (daty, nazwy "
                "miejscowości i bitew, napisy, postacie, instytucje) i sprawdź, czy wszystkie te szczegóły pasują do Twojej "
                "identyfikacji. W uzasadnieniu odwołaj się do każdego źródła wymienionego w poleceniu, przytaczając te "
                "szczegóły. Nie dopisuj dat, nazw ani identyfikacji, których nie jesteś pewien — jeden błędny szczegół "
                "w uzasadnieniu odbiera punkt.")
MATCH_NAMES_HINT = ("Wskazówka: polecenie wymaga nazw (np. władcy, państwa, postaci), a nie numerów. Po literze wpisz pełną "
                    "nazwę, np. „A: <nazwa>”; cyfra we wzorze pokazuje tylko składnię.")
FIELDS_RETRY = ("Odpowiedź musi zawierać wszystkie elementy, których wymaga polecenie. Zapisz ją dokładnie według wzoru, "
                "wypełniając każde pole (każdy punkt „•” to osobny element):\n")


def answer_template(question):
    """Wzór odpowiedzi z końca polecenia: linie „Etykieta:” i „•” (np. „Wydarzenie 1.:\\nWydarzenie 2.:”)."""
    tpl = []
    for line in reversed(question.strip().splitlines()):
        s = line.strip()
        if s == "•" or (s.endswith(":") and len(s) <= 90):
            tpl.append(s)
        else:
            break
    return tpl[::-1]


def template_filled(tpl, answer):
    """Ile pól wzoru jest w odpowiedzi (etykiety po kolei, punkty „•” jako osobne linie)."""
    a, pos, n = answer.lower(), 0, 0
    labs = [re.sub(r"\s+", " ", t[:-1].lower()).strip() for t in tpl if t != "•"]
    for j, key in enumerate(labs):
        i = a.find(key, pos)
        if i < 0:
            continue
        pos = i + len(key)
        nxt = a.find(labs[j + 1], pos) if j + 1 < len(labs) else -1
        if len(re.sub(r"[\s:•*\-–]", "", a[pos:nxt if nxt >= 0 else None])) >= 2:
            n += 1
    bullets = sum(t == "•" for t in tpl)
    if bullets:
        items = [l for l in answer.splitlines() if re.match(r"\s*(?:[•*\-–]|\d+[.)])\s*\S", l)]
        n += min(bullets, len(items))
    return n


def build_body(item, kind, legacy=False):
    """Treść zadania dokładnie tak, jak widzi ją model (wspólne dla harnessu i danych SFT)."""
    body = f"Zadanie {item['id']} ({item['max_points']} pkt)\n\n{item.get('source_text', '')}\n\n{item['question']}"
    if kind.startswith("closed") and not legacy:
        body += f"\n\nZapisz odpowiedź dokładnie w formacie:\n{item['answer_format']}"
    return body


def build_text(body, rag_ctx):
    if not rag_ctx:
        return body
    return RAG_HEAD + "\n" + "\n".join(f"- {c['title']}: {c['text']}" for c in rag_ctx) + "\n\n" + body


def system_for(item, legacy=False):
    return SYSTEM_TEXT_LEGACY if legacy and not item.get("images") else SYSTEM


def item_type(item):
    """Typ z answer_format; dla otwartych rozróżnienie wg polecenia (do bramkowania RAG i myślenia)."""
    fmt, q = item.get("answer_format", ""), item["question"]
    if fmt.startswith("Jeden tekst") or "Wybierz jeden z nich" in q:
        return "essay"
    if re.fullmatch(r"(\d+: [PF]\n?)+", fmt.strip() + "\n"):
        return "closed_tf"
    if re.fullmatch(r"[A-F]", fmt.strip()):
        return "closed_choice"
    if re.fullmatch(r"([A-F]: \S+\n?)+", fmt.strip() + "\n"):
        return "closed_match"
    if re.fullmatch(r"(\d+: [A-F]\n?)+", fmt.strip() + "\n"):
        return "closed_multi"
    if q.startswith("Rozstrzygnij"):
        return "rozstrz"
    if q.startswith(("Podaj", "Wymień", "Nazwij")):
        return "podaj"
    return "open"


def match_wants_names(item):
    """Dopasowanie ze wzorem „A: 1”, choć polecenie nie mówi o numerach/literach (np. 2024/11.1 — imiona władców)."""
    fmt = item.get("answer_format", "").strip()
    return (item_type(item) == "closed_match" and fmt.splitlines()[0].split(":")[1].strip().isdigit()
            and not re.search(r"(?i)numer|cyfr|liczb|oznacz|liter", item["question"]))


def match_digits(fmt, answer):
    """Dopasowanie, w którym choć jedna wartość to same cyfry („A: 1”, „B: 1598”)."""
    parts = closed_parts("closed_match", fmt, answer)
    return bool(parts) and any(not re.search(r"[^\W\d_]", v) for v in parts.values())


def match_names_retry(chat, messages, max_tokens, think, item, pre_norm, answer, seed):
    """--match-retry (raport 21): gdy polecenie chce nazw, a wyszły cyfry — najpierw bez redukcji do numeru
    (model podał „Władysław II (1140–1158)”), potem jedna powtórka tego samego zapytania z innym seedem.
    Nowa odpowiedź tylko wtedy, gdy wszystkie wartości zawierają litery."""
    fmt = item["answer_format"]
    log = {"before": answer}
    k0 = re.escape(fmt.strip().splitlines()[0].split(":")[0].strip())

    def names_of(text):  # ostatni blok „A: …” (wcześniejsze linie „A:” bywają rozważaniami)
        starts = [m.start() for m in re.finditer(rf"(?m)^\s*{k0}\s*[.):–-]*\s*[:–\-→]", text)]
        return normalize_closed("closed_match", fmt, text[starts[-1]:] if starts else text, True)

    def ok(cand):
        parts = closed_parts("closed_match", fmt, cand)
        return bool(parts) and not match_digits(fmt, cand) and all(len(v) <= 60 for v in parts.values())

    cand = names_of(pre_norm)
    if ok(cand):
        return cand, {**log, "via": "no-reduce", "after": cand}
    try:
        raw, _, fin = chat(messages, max_tokens, think, seed=seed + 11)
        a = clean_answer(raw)
        cand = names_of(a) if a.strip() and fin != "length" else ""
        log.update(retry_raw=a[-300:], retry_finish=fin)
    except Exception as e:
        cand, log["why"] = "", repr(e)[:200]
    if cand and ok(cand):
        return cand, {**log, "via": "retry", "after": cand}
    return answer, {**log, "via": "none"}


def normalize_closed(kind, fmt, text, names=False):
    """Przepisuje odpowiedź modelu do składni answer_format; gdy się nie da, zostawia tekst.
    names=True: nie redukuje wartości dopasowania do liczby (nazwy z datami, np. „Henryk IV (1589–1610)”)."""
    t = re.sub(r"[*_`#]", "", text)
    if kind == "closed_choice":
        m = re.findall(r"(?:^|[\s(])([A-F])(?:[).:\s]|$)", t)
        return m[-1] if m else text.strip()
    keys = [l.split(":")[0].strip() for l in fmt.strip().splitlines()]
    out = {}
    for k in keys:
        if kind == "closed_tf":
            t2 = re.sub(r"(?i)prawd\w*", "P", re.sub(r"(?i)fałsz\w*", "F", t))
            m = re.search(rf"(?m)(?:^|\s){re.escape(k)}\s*[.):–-]*\s*[:–-]?\s*([PF])\b", t2)
        elif kind == "closed_multi":
            m = re.search(rf"(?m)(?:^|\s){re.escape(k)}\s*[.):–-]*\s*[:–-]?\s*\(?([A-F])\b", t)
        else:  # closed_match: litera -> numer / nazwa
            m = re.search(rf"(?m)(?:^|\s){re.escape(k)}\s*[.):–-]*\s*[:–\-→]\s*(.+?)\s*$", t)
        if m:
            val = m.group(1).strip()
            if kind == "closed_match" and not names and fmt.strip().splitlines()[0].split(":")[1].strip().isdigit():
                num = re.search(r"\d+", val)
                val = num.group(0) if num else val
            out[k] = val
    if len(out) == len(keys):
        return "\n".join(f"{k}: {out[k]}" for k in keys)
    return text.strip()


def closed_parts(kind, fmt, answer):
    """Znormalizowana odpowiedź zamknięta -> {klucz: wartość}; None, gdy nie ma pełnej składni answer_format."""
    if kind == "closed_choice":
        return {"": answer.strip()} if re.fullmatch(r"[A-F]", answer.strip()) else None
    keys = [l.split(":")[0].strip() for l in fmt.strip().splitlines()]
    got = dict(re.findall(r"(?m)^\s*([^:\n]+?)\s*:\s*(.+?)\s*$", answer))
    return {k: got[k] for k in keys} if all(k in got for k in keys) else None


def vote_closed(kind, fmt, answers):
    """Głos większościowy per część (litera / „1: P” / „A: nazwa”); remis -> pierwsza próbka."""
    parsed = [closed_parts(kind, fmt, a) for a in answers]
    ok = [p for p in parsed if p]
    if not ok:
        return answers[0]
    # rdzenie 5 liter: odmiany i warianty zapisu nazw („Rurykowicze”/„Rurykowie”, „Anjou”/„Anjoujczycy”) głosują razem
    key = lambda v: " ".join(w[:5] for w in re.findall(r"\w+", v.casefold()))
    out = {}
    for k in ok[0]:
        vals = [p[k] for p in ok]
        c = Counter(key(v) for v in vals)
        top = max(c.values())
        out[k] = next(v for v in vals if c[key(v)] == top)
    return out[""] if kind == "closed_choice" else "\n".join(f"{k}: {v}" for k, v in out.items())


def clean_answer(text):
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S)
    if "</think>" in text:  # Qwen3.5 bez myślenia potrafi napisać szkic i samotne </think> przed właściwą odpowiedzią
        head, _, tail = text.rpartition("</think>")
        text = tail if tail.strip() else head
    return re.sub(r"\*\*(.+?)\*\*", r"\1", text).strip()


def fix_essay(chat, content, answer, min_words=300, header=True):
    """Esej poniżej 300 wyrazów dostaje 0 za spójność, a bez numeru tematu sędzia nie wie, co oceniać."""
    base = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": content}]
    for _ in range(2):
        n = len(answer.split())
        if n >= min_words:
            break
        try:
            longer, _, _ = chat(base + [{"role": "assistant", "content": answer}, {"role": "user", "content":
                                f"Wypracowanie ma {n} wyrazów, a wymagane minimum to 300. Napisz całe wypracowanie od nowa, "
                                "rozbudowując argumentację o kolejne fakty, do około 450 wyrazów. Zacznij od numeru wybranego tematu."}],
                                4096, False)
        except Exception:
            break
        longer = clean_answer(longer)
        if len(longer.split()) > n:
            answer = longer
    if header and not re.search(r"(?i)temat\w*\s*(nr\.?\s*)?\d", answer[:300]):
        try:
            num, _, _ = chat(base + [{"role": "assistant", "content": answer}, {"role": "user", "content":
                             "Podaj tylko numer tematu, który wybrałeś (jedna cyfra)."}], 20, False)
            m = re.search(r"\d", num)
            if m:
                answer = f"Temat nr {m.group(0)}\n\n{answer}"
        except Exception:
            pass
    return answer


HEADER_RE = re.compile(r"(?i)temat\w*\s*(?:nr\.?\s*)?(\d)")


def terms(text):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eval"))
    from rag_precompute import terms as t
    return t(text)


def parse_topics(question):
    """Trzy tematy wypracowania z polecenia: {numer: pełny tekst tematu}."""
    parts = re.split(r"(?m)^\s*([1-3])\.\s+", question)
    return {int(parts[i]): " ".join(parts[i + 1].split()) for i in range(1, len(parts) - 1, 2)}


def topic_thesis(topic):
    return re.split(r"Zajmij\s+stanowisko", topic)[0].strip()


def topic_aspects(topic):
    m = re.search(r"aspekty:\s*(.+?)\.?$", topic)
    if m:
        return [a.strip(" .") for a in re.split(r",\s*|\s+i\s+", m.group(1).replace("-\n", "").replace("- -", "-")) if a.strip(" .")]
    m = re.search(r"uwzględniając w swojej argumentacji\s+(.+?)\.?$", topic)
    return [m.group(1)] if m else []


def detect_topic(question, essay):
    """Temat wypracowania po nakładaniu się słów: liczy wystąpienia w eseju słów charakterystycznych tylko dla danego tematu.
    Zwraca (numer | None, wyniki); numer tylko przy wyraźnej przewadze."""
    topics = parse_topics(question)
    if len(topics) < 2:
        return None, {}
    tset = {n: set(terms(topic_thesis(t))) for n, t in topics.items()}
    words = [w.lower()[:6] for w in re.findall(r"\w+", essay)]
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    scores = {}
    for n, ts in tset.items():
        uniq = ts - set().union(*(o for m, o in tset.items() if m != n))
        scores[n] = sum(min(freq.get(t, 0), 5) for t in uniq)
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    best, second = ranked[0], ranked[1]
    if best[1] >= 3 and best[1] >= 2 * second[1] + 1:
        return best[0], scores
    return None, scores


def essay_topic(question, essay):
    """Numer tematu: nagłówek napisany przez model, a bez niego — wykrycie po treści."""
    m = HEADER_RE.search(essay[:300])
    if m:
        return int(m.group(1)), "header"
    n, _ = detect_topic(question, essay)
    return n, "detect" if n else None


def insert_before_last(essay, extra):
    paras = [p for p in re.split(r"\n\s*\n", essay.strip()) if p.strip()]
    if len(paras) >= 3:
        return "\n\n".join(paras[:-1] + [extra.strip()] + paras[-1:])
    return essay.strip() + "\n\n" + extra.strip()


def extend_essay(chat, base, question, answer, min_words=350, rounds=2):
    """Za krótki esej: zamiast przepisywania całości (małe modele znów piszą ~250 wyrazów) dopisujemy 1–2 akapity
    rozwinięcia z nowymi faktami i wstawiamy je przed zakończeniem."""
    log = []
    n_topic, _ = essay_topic(question, answer)
    topic = parse_topics(question).get(n_topic, "") if n_topic else ""
    aspects = topic_aspects(topic) if topic else []
    for _ in range(rounds):
        n = len(answer.split())
        if n >= min_words:
            break
        need = max(120, min_words - n + 60)
        asp = f" (zwłaszcza aspekt: {', '.join(aspects)} — rozwiń ten, który omówiłeś najsłabiej)" if aspects else ""
        try:
            extra, _, _ = chat(base + [{"role": "assistant", "content": answer}, {"role": "user", "content":
                               f"Wypracowanie ma {n} wyrazów, a powinno mieć co najmniej {min_words}. Nie przepisuj go. "
                               f"Napisz tylko 1–2 nowe akapity rozwinięcia (łącznie około {need} wyrazów), które wzmacniają "
                               f"argumentację nowymi, konkretnymi faktami: datami, postaciami, wydarzeniami{asp}. "
                               "Nie powtarzaj tego, co już napisałeś, nie pisz wstępu, zakończenia ani numeru tematu. "
                               "Podaj wyłącznie nowe akapity."}], 2048, False)
        except Exception:
            break
        extra = clean_answer(extra)
        extra = re.sub(r"(?im)^\s*(temat\w*\s*(nr\.?\s*)?\d.*|oto .{0,60}:|nowe akapity:?)\s*$", "", extra).strip()
        ne = len(extra.split())
        if ne < 40 or ne > 1.2 * n:  # za krótkie albo model przepisał całość
            log.append({"words": n, "added": ne, "ok": False})
            continue
        answer = insert_before_last(answer, extra)
        log.append({"words": n, "added": ne, "ok": True})
    return answer, log


def add_header(chat, base, question, answer, detect):
    """Nagłówek „Temat nr N”: zostawia napisany przez model; z --essay-topic-detect bierze temat z treści, a dopiero
    przy niejasnym wyniku pyta model o cyfrę (stare zachowanie)."""
    m = HEADER_RE.search(answer[:300])
    if m:
        if detect:  # nagłówek sprzeczny z bardzo wyraźną treścią (np. „Temat nr 3” nad esejem o Jagielle) poprawiamy
            n, sc = detect_topic(question, answer[:m.start()] + answer[m.end():])
            if n and n != int(m.group(1)) and sc[n] >= 10 and sc[n] >= 3 * max(v for k, v in sc.items() if k != n):
                return answer[:m.start(1)] + str(n) + answer[m.end(1):], "fixed"
        return answer, "model"
    if detect:
        n, _ = detect_topic(question, answer)
        if n:
            return f"Temat nr {n}\n\n{answer}", "detect"
    try:
        num, _, _ = chat(base + [{"role": "assistant", "content": answer}, {"role": "user", "content":
                         "Podaj tylko numer tematu, który wybrałeś (jedna cyfra)."}], 20, False)
        m = re.search(r"\d", num)
        if m:
            return f"Temat nr {m.group(0)}\n\n{answer}", "ask"
    except Exception:
        pass
    return answer, None


REFINE_PROMPT = ("Poniżej materiały pomocnicze (notatki encyklopedyczne; korzystaj tylko z pasujących):\n{notes}\n\n"
                 "Popraw swoje wypracowanie na temat nr {n}:\n"
                 "1) popraw błędy merytoryczne (daty, nazwy, postacie); jeśli materiały przeczą twojemu twierdzeniu, zaufaj materiałom;\n"
                 "2) w każdym aspekcie ({aspects}) dodaj konkretne fakty — zwłaszcza tam, gdzie argumentacja jest ogólnikowa;\n"
                 "3) zachowaj ten sam temat i to samo stanowisko, nie zmieniaj tezy;\n"
                 "4) wypracowanie ma mieć co najmniej 350 wyrazów.\n"
                 "Napisz całe poprawione wypracowanie, zaczynając od „Temat nr {n}”.")


GENERIC_NAMES = {"polska", "polski", "polsce", "polską", "polacy", "europa", "europy", "europie", "temat", "zadani", "wypowi",
                 "w", "we", "na", "to", "ten", "ta", "jego", "jednak", "choć", "podsum", "wniose", "aspekt", "ponadt", "również"}


ASPECT_WORDS = {"społ": "społeczeństwo przywilej szlachta chłopi mieszczaństwo miasta", "gospod": "gospodarka handel rolnictwo przemysł",
                "ustroj": "ustrój sejm przywilej konstytucja władza", "militar": "wojna bitwa armia wojsko",
                "kultur": "kultura sztuka uniwersytet literatura szkoła", "polity": "polityka sojusz unia traktat",
                "dyplomat": "dyplomacja traktat pokój sojusz", "wydarzenia": "powstanie protest odwilż"}


def proper_stems(text):
    """Rdzenie (6 znaków) słów pisanych wielką literą w środku zdania — przybliżenie nazw własnych."""
    out = set()
    for m in re.finditer(r"(?<![.!?:\n]\s)(?<!^)\b([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]{2,})", text):
        s = m.group(1).lower()[:6]
        if s not in GENERIC_NAMES:
            out.add(s)
    return out


def refine_essay(chat, base, question, answer, notes, k=6, max_tokens=4096, think=False):
    """Drugie przejście eseju z bazą wiedzy: temat wybiera model bez kontekstu (bez przeskakiwania tematu),
    notatki szukamy dla tezy wybranego tematu i dla każdego aspektu. Przyjmujemy tylko ten sam temat i nie krótszy tekst."""
    n, how = essay_topic(question, answer)
    if not n:
        return answer, {"ok": False, "why": "no_topic"}
    topic = parse_topics(question).get(n, "")
    thesis, aspects = topic_thesis(topic), topic_aspects(topic)
    names = proper_stems(thesis + "\n" + answer)
    subject = " ".join(re.findall(r"\b[A-ZĄĆĘŁŃÓŚŹŻ][\wąćęłńóśźż]+|\b\d{3,4}\b", thesis))
    found, seen = [], set()
    queries = [(thesis, 3)] + [(f"{subject} {' '.join(w for key, w in ASPECT_WORDS.items() if key in a) or a}", 2)
                               for a in aspects]
    for q, kk in queries:
        for c in notes.search(q, kk + 2):
            if proper_stems(thesis) and not proper_stems(c["title"] + " " + c["text"]) & names:  # „Dżoser” trafiony przez „dynastii”
                continue
            key = " ".join(c["title"].lower().split()[:3])
            if key not in seen:
                seen.add(key)
                found.append(c)
    found = found[:k]
    if not found:
        return answer, {"ok": False, "why": "no_notes", "topic": n}
    prompt = REFINE_PROMPT.format(notes="\n".join(f"- {c['title']}: {c['text']}" for c in found), n=n,
                                  aspects=", ".join(aspects) or "wszystkie wymienione w poleceniu")
    try:
        raw, _, finish = chat(base + [{"role": "assistant", "content": answer}, {"role": "user", "content": prompt}],
                              max_tokens, think)
    except Exception as e:
        return answer, {"ok": False, "why": repr(e)[:200], "topic": n}
    new = clean_answer(raw)
    n2, _ = essay_topic(question, new)
    info = {"topic": n, "topic_how": how, "new_topic": n2, "words": len(answer.split()), "new_words": len(new.split()),
            "finish": finish, "notes": [c["title"] for c in found]}
    if n2 != n or len(new.split()) < len(answer.split()) or finish == "length":
        return answer, {**info, "ok": False, "candidate": new[:6000]}
    return new, {**info, "ok": True, "before": answer[:6000]}


FC_ABBR = {"r", "w", "wr", "np", "tzw", "św", "ok", "in", "ks", "gen", "im", "pt", "tj", "zob", "ur", "zm", "e", "n", "p",
           "cz", "t", "s", "ss", "tys", "mln", "mld", "godz", "płk", "kpt", "por", "hr", "bp", "abp", "kard", "dr", "prof", "al",
           "ul", "pl", "woj", "pow", "ew", "itd", "itp", "jw", "wg", "tzn", "przyp", "red", "wyd", "nr", "rozdz", "art", "ust"}
FC_SENT = re.compile(r"\S.*?(?:[.!?…]+[”\"»)]*(?=\s|$)|$)", re.S)
FC_LABEL = re.compile(r"^\s*(?:[•*\-–]\s*|\d+[.)]\s+)?(?:[A-ZĄĆĘŁŃÓŚŹŻ][^:\n]{0,40}:\s+)?")
FC_PROMPT = (
    "Jesteś surowym egzaminatorem-historykiem. Poniżej ponumerowane zdania z odpowiedzi ucznia{what}. "
    "Sprawdź każde zdanie wyłącznie pod kątem błędów faktograficznych: daty, nazwy, postacie, miejsca, kto co zrobił, "
    "przyczyny i skutki. Nie oceniaj stylu, argumentacji, kompletności ani opinii; uproszczenie to nie błąd. "
    "Zgłoś zdanie tylko wtedy, gdy jesteś pewien, że zawiera błąd faktograficzny.{src}\n\n"
    "Dla każdego błędnego zdania wypisz dokładnie dwie linie:\n"
    "[n] BŁĄD: <krótko, na czym polega błąd>\n"
    "[n] POPRAWKA: <całe zdanie po poprawce: to samo zdanie, zmieniony tylko błędny fragment; jeśli nie znasz poprawnej "
    "wartości, usuń błędny szczegół>\n"
    "Jeśli żadne zdanie nie zawiera błędu, napisz tylko: BRAK BŁĘDÓW.\n\n{notes}Zdania:\n{sents}")
FC_CONFIRM = ("Które z dwóch zdań jest zgodne z faktami historycznymi?\nA: {a}\nB: {b}\n"
              "Odpowiedz jedną literą: A, B albo X (jeśli oba są równie poprawne lub nie wiesz).")


def fc_units(answer, essay):
    """Zdania do sprawdzenia: (start, end, tekst) w odpowiedzi; bez nagłówka tematu, etykiet pól i krótkich wtrąceń."""
    units, pos = [], 0
    for line in answer.split("\n"):
        start = pos
        pos += len(line) + 1
        if not line.strip() or (essay and HEADER_RE.match(line.strip()) and len(line.split()) <= 6):
            continue
        off = FC_LABEL.match(line).end()
        if re.match(r"\s*Rozstrzygni", line):  # samo rozstrzygnięcie zostaje (zamiana Tak/Nie to zmiana odpowiedzi)
            continue
        cur = None
        for m in FC_SENT.finditer(line, off):
            s, e = m.start(), m.end()
            if cur is not None:
                last = re.findall(r"(\w+)[.…]*[”\"»)]*$", line[cur:s].strip())
                if last and (last[0].lower() in FC_ABBR or (len(last[0]) == 1 and last[0].isupper())
                             or (last[0].isdigit() and line[s:s + 1].islower())):
                    continue  # „w 1410 r. Jagiełło…”, „J. Piłsudski” — ten sam fragment
                units.append((start + cur, start + s))
            cur = s
        if cur is not None:
            units.append((start + cur, start + len(line)))
    return [(s, e, answer[s:e].rstrip()) for s, e in units if len(answer[s:e].split()) >= 4]


def fc_ok(old, new, max_add):
    """Poprawka zachowuje rolę zdania: podobne słowa, bez dużego wydłużenia, jedno zdanie."""
    ow, nw = re.findall(r"\w+", old.lower()), re.findall(r"\w+", new.lower())
    if not ow or not nw or new.strip() == old.strip() or len(nw) > len(ow) + max_add or len(nw) < 0.5 * len(ow):
        return False
    keep = sum(w in set(nw) for w in ow) / len(ow)
    splits = re.compile(r"[.!?]\s+[A-ZĄĆĘŁŃÓŚŹŻ]")
    return keep >= 0.5 and len(splits.findall(new)) <= len(splits.findall(old))


def factcheck(chat, item, kind, answer, notes=None, think=False, images=None, confirm=True, max_changes=6,
              think_tokens=8000):
    """Recenzent faktów: numerowane zdania → model zgłasza błędne i daje poprawione zdanie; podmieniamy tylko te zdania
    (po sprawdzeniu zachowania roli i, z confirm, gdy model w osobnym pytaniu A/B wybiera poprawkę)."""
    essay = kind == "essay"
    units = fc_units(answer, essay)
    log = {"n_sent": len(units), "changes": []}
    if not units:
        return answer, log
    found, seen = [], set()
    if notes:
        subject = ""
        if essay:
            n_topic, _ = essay_topic(item["question"], answer)
            thesis = topic_thesis(parse_topics(item["question"]).get(n_topic, "")) if n_topic else ""
            subject = " ".join(re.findall(r"\b[A-ZĄĆĘŁŃÓŚŹŻ][\wąćęłńóśźż]+|\b\d{3,4}\b", thesis)[1:])
        for _, _, s in units:
            if not proper_stems(s) and not re.search(r"\b\d{3,4}\b", s):
                continue
            t = [x for x in dict.fromkeys(notes.terms(s)) if x in notes.idf]  # najrzadsze słowa: nazwy, daty
            q = " ".join(sorted(t, key=lambda x: -notes.idf[x])[:6]) + " " + subject
            for c in notes.search(q, 2):
                if c["title"] not in seen:
                    seen.add(c["title"])
                    found.append((c["score"], c))
        found = [c for _, c in sorted(found, key=lambda x: -x[0])[:10 if essay else 4]]
    log["notes"] = [c["title"] for c in found]
    notes_txt = ("Materiały pomocnicze (notatki encyklopedyczne; mogą być nieistotne, ale jeśli dotyczą tego samego faktu "
                 "i podają inną datę lub nazwę niż zdanie, zaufaj notatkom):\n"
                 + "\n".join(f"- {c['title']}{' (' + c['sub'] + ')' if 0 < len(c.get('sub', '')) <= 40 else ''}: "
                             f"{c['text'][:500]}" for c in found) + "\n\n") if found else ""
    if essay:
        what, src = " (wypracowanie maturalne)", ""
    else:
        what = ""
        src = ("\nTwierdzenia zgodne z treścią źródeł zadania są poprawne. Treść zadania:\n"
               + build_body(item, kind)[:4000])
    sents = "\n".join(f"[{i}] {s}" for i, (_, _, s) in enumerate(units, 1))
    text = FC_PROMPT.format(what=what, src=src, notes=notes_txt, sents=sents)
    content = [*images, {"type": "text", "text": text}] if images else text
    try:
        raw, reasoning, finish = chat([{"role": "user", "content": content}], think_tokens if think else 2048, think)
    except Exception as e:
        log["why"] = repr(e)[:200]
        return answer, log
    raw = clean_answer(raw)
    log.update(finish=finish, raw=raw[:3000])
    if finish == "length":
        return answer, log
    errs, fixes = {}, {}
    for m in re.finditer(r"(?m)^\s*\[?(\d+)\]?\s*(BŁĄD|POPRAWKA)\s*:\s*(.+?)\s*$", raw):
        (errs if m.group(2) == "BŁĄD" else fixes)[int(m.group(1))] = m.group(3).strip().strip("„”\"")
    repl = []
    for n, new in sorted(fixes.items()):
        if not 1 <= n <= len(units) or n not in errs:
            continue
        s, e, old = units[n - 1]
        ch = {"n": n, "old": old, "new": new, "why": errs[n]}
        if not fc_ok(old, new, 12 if essay else 8):
            ch["ok"] = "shape"
        elif confirm:
            flip = sum(map(ord, old)) % 2 == 1
            a, b = (new, old) if flip else (old, new)
            try:
                r, _, _ = chat([{"role": "user", "content": FC_CONFIRM.format(a=a, b=b)}], 1500 if think else 10, think)
                pick = (re.findall(r"\b([ABX])\b", clean_answer(r)) or ["X"])[-1]
            except Exception:
                pick = "X"
            ch["pick"] = pick
            ch["ok"] = pick == ("A" if flip else "B")
        else:
            ch["ok"] = True
        log["changes"].append(ch)
        if ch["ok"] is True:
            repl.append((s, e, new))
    for s, e, new in sorted(repl, reverse=True)[:max_changes]:
        answer = answer[:s] + new + answer[e:]
    log["applied"] = min(len(repl), max_changes)
    return answer, log


DEFAULT_ASPECTS = ["polityczny", "społeczno-gospodarczy", "kulturowy"]
S_NOTES = "Materiały pomocnicze (notatki encyklopedyczne; korzystaj tylko z pasujących, nie przepisuj ich dosłownie):\n{notes}\n\n"
S_PLAN = ("Temat wypracowania: {topic}\n\n{notes}Nie pisz jeszcze wypracowania. Przygotuj plan. Zgadzasz się z tezą tematu — wszystkie argumenty mają ją potwierdzać. {what}\n"
          "Każdy argument to jeden konkretny fakt: wydarzenie, data, postać, dokument — tylko takie, których jesteś pewien "
          "(błędy merytoryczne obniżają ocenę). Odpowiedz dokładnie w formacie:\n"
          "TEZA: <jedno zdanie: zgadzasz się z tezą tematu i krótko mówisz dlaczego>\n{fmt}")
S_PARA = ("Temat wypracowania: {topic}\nStanowisko: {thesis}\n\n{notes}Napisz JEDEN akapit rozwinięcia wypracowania "
          "({words} wyrazów) — {focus}. Plan tego akapitu: {args}\n"
          "Zacznij akapit od słów „{link}” i zdania-argumentu, które łączy ten {kind} ze stanowiskiem. Potem podaj 2–3 "
          "konkretne fakty (data, postać, nazwa, termin) — najlepiej z materiałów — i po każdym wyjaśnij, jak dowodzi "
          "stanowiska. Pisz tylko o faktach, których jesteś pewien; nie powtarzaj się. Bez wstępu, zakończenia, "
          "tytułu i wypunktowań — tylko tekst akapitu.")
S_LINKS = ["Po pierwsze,", "Po drugie,", "Po trzecie,", "Ponadto", "Warto też dodać, że"]
S_INTRO = ("Temat wypracowania: {topic}\nStanowisko: {thesis}\nArgumenty w rozwinięciu: {plan}\n\n"
           "Napisz WSTĘP wypracowania (50–70 wyrazów): krótko przedstaw kontekst historyczny (epoka, daty) i na końcu "
           "wyraźnie sformułuj stanowisko. Bez tytułu — tylko tekst akapitu.")
S_END = ("Temat wypracowania: {topic}\nStanowisko: {thesis}\nArgumenty w rozwinięciu: {plan}\n\n"
         "Napisz ZAKOŃCZENIE wypracowania (40–60 wyrazów), zaczynając od słów „Podsumowując,”: podsumuj najważniejsze argumenty i potwierdź stanowisko. "
         "Nie dodawaj nowych faktów. Bez tytułu — tylko tekst akapitu.")


def essay_aspects(topic):
    """(aspekty, wybór): aspekty z tematu; przy „trzech wybranych X” pusta lista i opis X (elementy wskazuje plan)."""
    m = re.search(r"(?:uwzględniając w swojej argumentacji|charakteryzując)\s+(.+?)\.?\s*$", topic)
    tail = re.sub(r"^aspekt\w*:?\s+", "", m.group(1).strip()) if m else ""
    if re.search(r"\btrz(y|ech)\b", tail):
        return [], tail
    parts = [a.strip(" .") for a in re.split(r",\s*|\s+i\s+", tail.replace("- -", "-")) if a.strip(" .")]
    return (parts if len(parts) >= 2 else DEFAULT_ASPECTS), None


def s_clean(text):
    """Jeden akapit prozy: bez myślenia, markdown, nagłówków i wypunktowań; usuwa powtórzone zdania (pętle)."""
    t = clean_answer(text)
    t = re.sub(r"(?m)^\s*(#+.*|temat\w*\s*(nr\.?\s*)?\d.*|(akapit|wstęp|zakończenie|rozwinięcie)\b[^\n]{0,40}:\s*)$", "", t,
               flags=re.I)
    t = re.sub(r"(?m)^\s*(?:[-•*]|\d+[.)])\s+", "", t)
    t = re.sub(r"(?i)^(akapit|wstęp|zakończenie)\s*:\s*", "", t.strip())
    sents, seen = [], set()
    for s in re.split(r"(?<=[.!?])\s+", " ".join(t.split())):
        k = re.sub(r"\W+", " ", s.lower()).strip()
        if k and k not in seen:
            seen.add(k)
            sents.append(s)
    return " ".join(sents).strip()


def s_trim(text, finish, max_words):
    """Urwany albo rozgadany akapit: do ostatniego pełnego zdania w limicie wyrazów."""
    words = text.split()
    if finish != "length" and len(words) <= max_words:
        return text
    cut = " ".join(words[:max_words])
    m = re.search(r"^(.*[.!?])", cut, re.S)
    return m.group(1) if m and len(m.group(1).split()) >= 30 else cut


def s_notes(notes, query, names, k, seen, check_names=True):
    out = []
    for c in notes.search(query, k + 4):
        if check_names and names and not proper_stems(c["title"] + " " + c["text"]) & names:
            continue
        key = " ".join(c["title"].lower().split()[:3])
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
        if len(out) >= k:
            break
    return out


def fmt_notes(cs, n_chars=700):
    return S_NOTES.format(notes="\n".join(f"- {c['title']}: {c['text'][:n_chars]}" for c in cs)) if cs else ""


def s_pick_topic(chat, question, notes, how):
    """Temat: ocena modelu (CHOOSE_PROMPT) i/lub pokrycie bazy wiedzy (suma BM25 3 najlepszych notatek zgodnych z nazwami)."""
    topics = parse_topics(question)
    if len(topics) <= 1:
        return (next(iter(topics)) if topics else None), {}
    info = {}
    if how in ("model", "mix"):
        try:
            r, _, _ = chat([{"role": "system", "content": SYSTEM},
                            {"role": "user", "content": question + "\n\n" + CHOOSE_PROMPT}], 300, False)
            info["rating"] = {int(a): int(b) for a, b in re.findall(r"Temat\s*(\d)\s*:\s*(\d)", r) if int(a) in topics}
            m = re.search(r"Wybór:\s*(\d)", r)
            info["model"] = int(m.group(1)) if m and int(m.group(1)) in topics else None
        except Exception:
            info["model"] = None
    if how in ("kb", "mix") and notes:
        cov = {}
        for n, t in topics.items():
            th = topic_thesis(t)
            names = proper_stems(th)
            cs = s_notes(notes, th, names, 3, set())
            cov[n] = round(sum(c["score"] for c in cs), 1)
        info["kb"] = cov
    if how == "model" or not info.get("kb"):
        return info.get("model") or 1, info
    if how == "kb":
        return max(info["kb"], key=info["kb"].get), info
    top = max(info["kb"].values()) or 1
    rating = info.get("rating") or {}
    score = {n: rating.get(n, 3) + 2 * info["kb"][n] / top + (0.5 if n == info.get("model") else 0) for n in topics}
    info["mix"] = {n: round(s, 2) for n, s in score.items()}
    return max(score, key=score.get), info


def structured_essay(chat, question, notes, pick="model", plan_think=False, plan_tokens=700, min_words=300,
                     think_tokens=8000):
    """Esej krok po kroku dla małych modeli: temat → plan (teza + 2 argumenty na aspekt, z notatkami) → akapit na aspekt
    w osobnym wywołaniu → wstęp i zakończenie → złożenie z nagłówkiem „Temat nr N”. Zwraca (esej | None, log)."""
    log = {}
    n, log["pick"] = s_pick_topic(chat, question, notes, pick)
    topic = parse_topics(question).get(n, "")
    if not topic:
        return None, {**log, "why": "no_topic"}
    thesis_t = topic_thesis(topic)
    aspects, choose = essay_aspects(topic)
    names = proper_stems(thesis_t)
    seen = set()
    base_notes = s_notes(notes, thesis_t, names, 3, seen) if notes else []
    if choose:
        what = f"Temat wymaga: {choose}. Wybierz trzy takie elementy i dla każdego podaj 2 argumenty."
        fmt = "1. <nazwa pierwszego elementu>: <argument 1>; <argument 2>\n2. <nazwa drugiego>: ...\n3. <nazwa trzeciego>: ..."
    else:
        what = f"Dla każdego aspektu ({', '.join(aspects)}) podaj 2 argumenty uzasadniające twoje stanowisko."
        fmt = "\n".join(f"{i}. {a}: <argument 1>; <argument 2>" for i, a in enumerate(aspects, 1))
    msgs = [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": S_PLAN.format(topic=topic, notes=fmt_notes(base_notes), what=what, fmt=fmt)}]
    try:
        plan, _, finish = chat(msgs, think_tokens if plan_think else plan_tokens, plan_think)
        if plan_think and (finish == "length" or not clean_answer(plan)):
            plan, _, finish = chat(msgs, plan_tokens, False)
    except Exception as e:
        return None, {**log, "why": repr(e)[:200]}
    plan = clean_answer(plan)
    m = re.search(r"(?im)^\W*TEZA\W*:?\s*(.+)$", plan)
    thesis = m.group(1).strip() if m else ""
    if not thesis or re.search(r"(?i)\bnie\s+(zgadzam|była|był|było|były|jest)|\bnie\w*\s+słuszn", thesis):
        thesis = f"Zgadzam się z tezą: {thesis_t}"  # małe modele zmieniają stanowisko między akapitami
    rows = re.findall(r"(?m)^\W*([1-3])[.)]\s*([^:\n]{1,80}):\s*(.+)$", plan)
    items = []
    for i in range(3 if choose else len(aspects)):
        row = next((r for r in rows if int(r[0]) == i + 1), None)
        label = (row[1].strip(" *") if row else "") if choose else aspects[i]
        items.append({"label": label or f"element {i + 1}", "args": row[2].strip() if row else ""})
    log.update({"topic": n, "thesis": thesis, "plan": plan[:2000], "aspects": [it["label"] for it in items]})
    kind = "element" if choose else "aspekt"
    # notatki akapitów tylko z puli pasującej do tezy i planu (notatka spoza tematu na 1. miejscu szkodzi — A/B T2)
    pool = {c["title"] for c in s_notes(notes, f"{thesis_t} {plan}", names, 8, set())} if notes else set()

    def aspect_notes(query, k):
        out = []
        for c in notes.search(query, 40) if notes else []:
            key = " ".join(c["title"].lower().split()[:3])
            if c["title"] in pool and key not in seen:
                seen.add(key)
                out.append(c)
                if len(out) >= k:
                    break
        return out

    paras = []
    for it in items:
        aw = " ".join(w for key, w in ASPECT_WORDS.items() if key in it["label"]) or it["label"]
        cs = aspect_notes(f"{thesis_t} {it['label']} {aw} {it['args']}", 2)
        focus = (f"o elemencie: {it['label']}" if choose else f"o aspekcie {it['label']}m" if it["label"].endswith("y")
                 else f"o aspekcie: {it['label']}")
        try:
            raw, _, fin = chat([{"role": "system", "content": SYSTEM}, {"role": "user", "content": S_PARA.format(
                topic=topic, thesis=thesis, notes=fmt_notes(cs), words="130–160", focus=focus, link=S_LINKS[min(len(paras), len(S_LINKS) - 1)],
                args=it["args"] or "wybierz 2–3 pewne fakty", kind=kind)}], 550, False)
        except Exception:
            continue
        p = s_trim(s_clean(raw), fin, 190)
        if len(p.split()) >= 30:
            paras.append(p)
        it["notes"] = [c["title"] for c in cs]
    if len(paras) < 2:
        return None, {**log, "why": "few_paragraphs", "paras": paras}
    plan_short = "; ".join(f"{it['label']}: {it['args'][:150]}" for it in items)
    parts = {}
    for key, prompt, lim in (("intro", S_INTRO, 100), ("end", S_END, 90)):
        try:
            raw, _, fin = chat([{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt.format(
                topic=topic, thesis=thesis, plan=plan_short)}], 250, False)
            parts[key] = s_trim(s_clean(raw), fin, lim)
        except Exception:
            parts[key] = ""
    if not parts["intro"]:
        parts["intro"] = thesis
    body = parts["intro"] + "\n\n" + "\n\n".join(paras) + ("\n\n" + parts["end"] if parts["end"] else "")
    extra_i = 0
    while len(body.split()) < max(min_words + 100, 420) and extra_i < 1:  # cel ~450–550: bogata argumentacja
        it = items[extra_i % len(items)]
        extra_i += 1
        cs = aspect_notes(f"{thesis_t} {it['label']} {it['args']}", 1)
        try:
            raw, _, fin = chat([{"role": "system", "content": SYSTEM}, {"role": "user", "content": S_PARA.format(
                topic=topic, thesis=thesis, notes=fmt_notes(cs), words="80–110", focus=f"kolejny argument ({it['label']}), "
                "inny niż: " + it["args"][:200], args="nowy, pewny fakt", kind=kind,
                link=S_LINKS[min(len(paras), len(S_LINKS) - 1)])}], 400, False)
        except Exception:
            break
        p = s_trim(s_clean(raw), fin, 150)
        if len(p.split()) >= 30:
            paras.append(p)
            body = parts["intro"] + "\n\n" + "\n\n".join(paras) + ("\n\n" + parts["end"] if parts["end"] else "")
    if len(body.split()) > 650:  # twardy limit: dłuższe teksty małych modeli to powtórzenia
        paras = [s_trim(p, "length", 150) for p in paras]
        while len(paras) > 3 and len((parts["intro"] + " ".join(paras) + parts["end"]).split()) > 650:
            paras.pop()
        body = parts["intro"] + "\n\n" + "\n\n".join(paras) + ("\n\n" + parts["end"] if parts["end"] else "")
    essay = f"Temat nr {n}\n\n{body}"
    log.update({"words": len(essay.split()), "paras": len(paras), "extra": extra_i,
                "notes": [c["title"] for c in base_notes] + [t for it in items for t in it.get("notes", [])]})
    return essay, log


RUBRIC_HINT = (
    "Wymagania egzaminatora CKE: każdy z trzech elementów tematu jest oceniany osobno. Najwyższa ocena elementu "
    "(„bogata argumentacja”, 4 pkt) wymaga argumentacji rzeczowej i pogłębionej, popartej szczegółową faktografią "
    "i terminologią; ogólniki bez konkretnych faktów to „argumentacja powierzchowna” (1 pkt).\n"
    "Elementy do omówienia w poszczególnych tematach:\n{elements}\n"
    "Najpierw w myślach zajmij jednoznaczne stanowisko i dla każdego elementu zaplanuj 2–3 fakty, których jesteś "
    "całkowicie pewien (daty, postacie, bitwy, traktaty, dokumenty, instytucje, reformy), oraz to, jak każdy z nich "
    "potwierdza albo osłabia tezę. Sprawdź każdą datę i nazwę; wątpliwe odrzuć. Potem napisz wypracowanie:\n"
    "1. Pierwsza linia: „Temat nr N”, potem od razu wstęp. Bez komentarzy do polecenia, bez przepisywania tematu, "
    "bez śródtytułów i wypunktowań.\n"
    "2. Wstęp (ok. 60 wyrazów): kontekst epoki z ramami czasowymi i jednoznaczne stanowisko wobec tezy.\n"
    "3. Rozwinięcie: na każdy element osobny akapit (130–170 wyrazów), w kolejności z tematu, zaczynający się od "
    "nazwy elementu (np. „W aspekcie politycznym…”). W każdym takim akapicie:\n"
    "   - 2–3 pewne, konkretne fakty z datami i nazwami własnymi oraz właściwe terminy historyczne, każdy "
    "wyjaśniony (co się stało, dlaczego, jakie miało skutki), a nie tylko wymieniony;\n"
    "   - co najmniej jeden związek przyczynowo-skutkowy (przyczyna → skutek);\n"
    "   - zdanie oceny, które wiąże argument z tezą (dlaczego potwierdza ją albo osłabia);\n"
    "   - gdy teza porównuje lub wartościuje (np. „najbardziej”, „najwybitniejszy”, „przede wszystkim”, "
    "„bardziej niż”, „niesłusznie”), porównanie z alternatywą (inny władca, konflikt, czynnik) albo jeden "
    "kontrargument i jego odparcie.\n"
    "4. {span}\n"
    "5. Zakończenie (ok. 50 wyrazów): wniosek wynikający z argumentów, bez nowych faktów.\n"
    "6. Długość: 450–600 wyrazów. Każdy błąd merytoryczny (zła data, postać, nazwa, zły związek przyczynowy, "
    "przypisanie władcy zjawiska z innej epoki) odejmuje punkty i jest gorszy niż brak szczegółu: lepiej mniej "
    "faktów, ale pewnych i dobrze wyjaśnionych; niepewny szczegół pomiń albo ujmij ogólniej (sam rok albo wiek).")
RUBRIC_PLAN = ("Nie pisz jeszcze wypracowania. Najpierw przygotuj plan dokładnie w formacie:\n"
               "Temat nr <N>\nStanowisko: <jedno zdanie>\nRamy czasowe: <od–do>\n"
               "1. <element>: fakty: <2–3 pewne fakty z datami i nazwami>; przyczyna → skutek: <…>; ocena: <…>\n"
               "2. <element>: …\n3. <element>: …\nWniosek: <jedno zdanie>")
RUBRIC_WRITE = ("Teraz napisz całe wypracowanie według tego planu, spełniając wszystkie wymagania z polecenia "
                "(pewne, wyjaśnione fakty, związek przyczynowo-skutkowy i ocena w każdym elemencie; 450–600 wyrazów). "
                "Zacznij od „Temat nr N”.")


def rubric_hint(question, only=None):
    """Wymagania najwyższego poziomu CKE z elementami każdego tematu (albo tylko tematu `only`) i ramami czasowymi."""
    lines, spans = [], []
    for n, t in sorted(parse_topics(question).items()):
        if only and n != only:
            continue
        aspects, choose = essay_aspects(t)
        el = f"{choose} (każde to osobny element; nazwij je we wstępie)" if choose else ", ".join(aspects)
        lines.append(f"Temat {n}: {el}")
        th = topic_thesis(t)
        m = re.search(r"\b1?\d{3}\s*[–-]\s*1?\d{3}\b|\b[XVI]+-wieczn\w+|\b[XVI]+\s+w(?:ieku|\.)", th)
        if m:
            spans.append(f"temat {n}: {m.group(0)}")
    span = ("Argumenty rozłóż na cały okres, którego dotyczy teza (" + "".join(s + "; " for s in spans) +
            "przy władcy — całe panowanie; przy jednym wydarzeniu — przyczyny z lat poprzedzających, przebieg i skutki): "
            "przykłady z początku, środka i końca okresu, a nie jedno wydarzenie.")
    return RUBRIC_HINT.format(elements="\n".join(lines), span=span)


def rubric_clean(answer):
    """Bez wstępnych komentarzy („Ponieważ nie załączyłeś…”), separatorów i przepisanego tematu w nagłówku."""
    m = re.search(r"(?im)^\W*temat\w*\s*(?:nr\.?\s*)?([1-3])\b[.:)*]*[ \t]*(.*)$", answer[:1500])
    if m and len(answer[:m.start()].split()) <= 80:
        line = m.group(2).strip()  # „Temat nr 1 Wiek VIII…” to już wstęp; „Temat 1: <treść tematu>” — do usunięcia
        if re.search(r"Zajmij\s+stanowisko|uwzględniając", line) or len(line.split()) <= 8:
            line = ""
        answer = f"Temat nr {m.group(1)}\n\n" + (line + " " if line else "") + answer[m.end():].lstrip()
    answer = re.sub(r"(?m)^\s*(\*{3,}|-{3,}|#+\s.*)\s*$\n?", "", answer)
    return re.sub(r"\n{3,}", "\n\n", answer).strip()


def rubric_rewrite(chat, system, text, question, answer, max_tokens, think):
    """--essay-rubric-fixed: temat z pierwszego eseju (bez wskazówek), potem nowy esej na ten sam temat z wymaganiami
    CKE tylko dla niego. Przyjmowany przy tym samym temacie, ≥ 300 wyrazach i nieuciętym wyjściu."""
    n, how = essay_topic(question, answer)
    if not n:
        return answer, {"ok": False, "why": "no_topic"}
    prompt = text + "\n\n" + rubric_hint(question, n) + f"\n\nNapisz wypracowanie na temat nr {n}."
    try:
        raw, _, fin = chat([{"role": "system", "content": system}, {"role": "user", "content": prompt}], max_tokens, think)
    except Exception as e:
        return answer, {"ok": False, "why": repr(e)[:200], "topic": n}
    new = rubric_clean(clean_answer(raw))
    n2, _ = essay_topic(question, new)
    info = {"topic": n, "topic_how": how, "new_topic": n2, "finish": fin, "words": len(answer.split()),
            "new_words": len(new.split())}
    if n2 != n or len(new.split()) < 300 or fin == "length":
        return answer, {**info, "ok": False, "candidate": new[:6000]}
    return new, {**info, "ok": True, "before": answer[:6000]}


OCR_HEAD = "[Tekst odczytany z obrazu (OCR, może zawierać błędy): "
_ocr_lock = threading.Lock()


TILES_NOTE = ("Uwaga: po każdym dużym obrazie dołączono jego powiększone fragmenty (ten sam obraz, nie osobne źródła) — "
              "użyj ich do odczytania drobnych napisów, dat, nazw i granic na mapach oraz szczegółów rysunków.")
TILE_NAMES = {(2, 2): ["lewa górna", "prawa górna", "lewa dolna", "prawa dolna"],
              (2, 1): ["lewa połowa", "prawa połowa"], (1, 2): ["górna połowa", "dolna połowa"]}


def png_b64(im):
    import io
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def image_parts(path, k, tiles, min_side=700, overlap=0.2, target_px=640 * 640):
    """Obraz w całości + (przy --image-tiles) nachodzące na siebie powiększone fragmenty: 2×2 albo 2 połowy wzdłuż
    dłuższego boku. Każdy fragment dostaje osobny budżet tokenów obrazu, więc drobne napisy i granice są czytelniejsze."""
    parts = [{"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()}}]
    if not tiles:
        return parts
    from PIL import Image
    im = Image.open(path).convert("RGB")
    w, h = im.size
    if max(w, h) < min_side:
        return parts
    cols, rows = (2, 2) if min(w, h) >= 500 and max(w, h) / min(w, h) < 1.8 else ((2, 1) if w >= h else (1, 2))
    tw, th = w / cols / (1 - overlap) if cols > 1 else w, h / rows / (1 - overlap) if rows > 1 else h
    crops = []
    for r in range(rows):
        for c in range(cols):
            x0 = 0 if cols == 1 else c * (w - tw) / (cols - 1)
            y0 = 0 if rows == 1 else r * (h - th) / (rows - 1)
            cr = im.crop((round(x0), round(y0), round(x0 + tw), round(y0 + th)))
            s = (target_px / (cr.width * cr.height)) ** 0.5
            if s > 1:
                cr = cr.resize((round(cr.width * min(s, 2.5)), round(cr.height * min(s, 2.5))), Image.LANCZOS)
            crops.append(cr)
    parts.append({"type": "text", "text": f"Powiększone fragmenty obrazu {k} ({', '.join(TILE_NAMES[(cols, rows)])}):"})
    parts += [{"type": "image_url", "image_url": {"url": "data:image/png;base64," + png_b64(cr)}} for cr in crops]
    return parts


def ocr_image(path, cache_dir, min_good=3):
    """Tesseract (pol+eng) lokalnie; wynik w pamięci podręcznej po sha1 obrazu. Zwraca oczyszczony tekst albo ''."""
    import hashlib
    import os
    import subprocess
    data = Path(path).read_bytes()
    h = hashlib.sha1(data).hexdigest()
    raws = {}
    for psm in ("3", "11"):  # 3: bloki tekstu (gazety, dokumenty), 11: rozproszone napisy (mapy, legendy)
        cache = Path(cache_dir) / (h + ("" if psm == "3" else f".psm{psm}") + ".txt")
        if cache.exists():
            raws[psm] = cache.read_text(encoding="utf-8")
            continue
        try:
            raws[psm] = subprocess.run(["tesseract", str(path), "stdout", "-l", "pol+eng", "--psm", psm], capture_output=True,
                                       text=True, timeout=300, env={**os.environ, "OMP_THREAD_LIMIT": "1"}).stdout
        except Exception:
            raws[psm] = ""
            continue
        with _ocr_lock:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(raws[psm], encoding="utf-8")
    good_re = re.compile(r"^[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż]{3,}[.,;:!?)»”\"]*$|^\(?\d{3,4}[.,)–-]*$")

    def good(t):
        return bool(good_re.match(t.strip("(„«\"'")))

    keep, seen = [], set()
    for line in raws["3"].splitlines():
        toks = [t for t in line.split() if re.search(r"\w", t)]
        g = [t for t in toks if good(t)]
        if g and len(g) >= 0.6 * len(toks):
            keep.append(" ".join(toks))
            seen.update(t.lower().strip(".,;:()") for t in g)
    sparse = []
    for t in raws["11"].split():
        k = t.lower().strip(".,;:()„”\"'")
        if good(t) and len(k) >= 4 and k not in seen:
            seen.add(k)
            sparse.append(t.strip(".,;:()"))
    text = " / ".join(keep + ([" ".join(sparse)] if len(sparse) >= 2 else []))
    if sum(1 for t in text.split() if good(t)) < min_good:
        return ""
    return text[:600]


def add_ocr(item, exam_dir, cache_dir):
    """Wstawia tekst OCR obok znacznika [Obraz: ...] w source_text (albo na końcu). Zwraca (nowe zadanie, teksty OCR)."""
    src, found = item.get("source_text", ""), {}
    for im in item.get("images") or []:
        t = ocr_image(exam_dir / im["path"], cache_dir)
        if not t:
            continue
        found[im["path"]] = t
        marker = f"[Obraz: {im['path']}]"
        block = OCR_HEAD + t + "]"
        src = src.replace(marker, marker + "\n" + block, 1) if marker in src else src + "\n" + block
    return ({**item, "source_text": src} if found else item), found


CAPTION_HEAD = "[Opis obrazu (automatyczny, może zawierać błędy): "
CAPTION_PROMPT = (
    "This image is a source from a Polish history exam (matura). Its title/caption in the exam:\n{ctx}\n\n"
    "Describe the image for a student who cannot see it:\n"
    "1. Type of image (map, caricature/cartoon, poster, photograph, painting, drawing, coin, seal, document, chart, table).\n"
    "2. Transcribe ALL text visible IN THE IMAGE exactly as written (labels, dates, place names, legend, signatures); "
    "do not repeat the title above.\n"
    "3. People, symbols, objects, clothing, flags, coats of arms and what is happening.\n"
    "4. For maps: region shown, marked borders, areas, arrows, battles and the legend.\n"
    "Be factual and concise (max 150 words). Do not invent names or dates you cannot see.")


def caption_image(client, path, ctx, max_tokens=400):
    """Opis obrazu przez pomocniczy mały VLM (osobny llama-server) — dla modelu bez wizji (T2)."""
    r = client.chat.completions.create(
        model="m", max_tokens=max_tokens, temperature=0.2, top_p=0.9,
        messages=[{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()}},
            {"type": "text", "text": CAPTION_PROMPT.format(ctx=ctx)}]}],
        extra_body={"seed": 42, "top_k": 20, "repeat_penalty": 1.1, "chat_template_kwargs": {"enable_thinking": False}})
    return re.sub(r"\s+", " ", (r.choices[0].message.content or "")).strip()[:1500]


def add_captions(item, captions):
    """Wstawia opisy obrazów obok znaczników [Obraz: ...] w source_text (albo na końcu)."""
    src, found = item.get("source_text", ""), {}
    for im in item.get("images") or []:
        t = captions.get(im["path"])
        if not t:
            continue
        found[im["path"]] = t
        marker = f"[Obraz: {im['path']}]"
        block = CAPTION_HEAD + t + "]"
        src = src.replace(marker, marker + "\n" + block, 1) if marker in src else src + "\n" + block
    return ({**item, "source_text": src} if found else item), found


def add_img_hints(item, hints):
    """Wstawia podpisy najbliższych obrazów z lokalnego korpusu (--img-retrieval) pod znacznikami [Obraz: ...]."""
    src, found = item.get("source_text", ""), {}
    for im in item.get("images") or []:
        t = hints.get(im["path"])
        if not t:
            continue
        found[im["path"]] = t
        marker = f"[Obraz: {im['path']}]"
        src = src.replace(marker, marker + "\n" + t, 1) if marker in src else src + "\n" + t
    return ({**item, "source_text": src} if found else item), found


class Retriever:
    def __init__(self, index_path):
        import tantivy
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eval"))
        from rag_precompute import terms
        self.terms, self.tantivy = terms, tantivy
        idx = tantivy.Index.open(str(index_path))
        idx.reload()
        self.searcher, self.schema = idx.searcher(), idx.schema

    def search(self, text, k):
        tk = self.terms(text)[:80]
        if not tk:
            return []
        q = self.tantivy.Query.boolean_query(
            [(self.tantivy.Occur.Should, self.tantivy.Query.term_query(self.schema, "stem", t)) for t in tk])
        out = []
        for score, a in self.searcher.search(q, k).hits:
            d = self.searcher.doc(a)
            out.append({"title": d["title"][0], "text": d["text"][0][:700], "score": round(float(score), 2)})
        return out


class Dense:
    """Mały embedder (intfloat/multilingual-e5-small, CPU/GPU przez transformers); osadzenia notatek w pamięci podręcznej .e5.pt."""

    def __init__(self, texts, cache, model="intfloat/multilingual-e5-small"):
        import torch
        from transformers import AutoModel, AutoTokenizer
        self.torch = torch
        self.tok, self.m = AutoTokenizer.from_pretrained(model), AutoModel.from_pretrained(model).eval()
        cache = Path(cache)
        if cache.exists() and cache.stat().st_mtime > 0:
            self.emb = torch.load(cache)
        else:
            self.emb = self.encode([f"passage: {t}" for t in texts])
            torch.save(self.emb, cache)

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


class NoteRetriever:
    """BM25 w pamięci nad krótkimi notatkami (kompendium, oś czasu, postacie); opcjonalnie hybryda z e5-small (RRF)."""

    def __init__(self, path, k1=1.5, b=0.75, dense=False):
        import math
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eval"))
        from rag_precompute import terms
        self.terms = terms
        self.notes = [json.loads(l) for l in open(path, encoding="utf-8")]
        self.docs = [terms(f"{n['title']} {n['subtopic']} {n['text']}") for n in self.notes]
        self.avg = sum(map(len, self.docs)) / len(self.docs)
        df = {}
        for d in self.docs:
            for t in set(d):
                df[t] = df.get(t, 0) + 1
        self.idf = {t: math.log(1 + (len(self.docs) - n + 0.5) / (n + 0.5)) for t, n in df.items()}
        self.k1, self.b = k1, b
        self.dense = Dense([f"{n['title']} {n['text']}" for n in self.notes], f"{path}.e5.pt") if dense else None

    BOILER = re.compile(r"(?i)zadanie zawiera \w+ temat\w*\.?|twoja wypowiedź powinna liczyć minimum 300 wyrazów\.?|"
                        r"napisz wypowiedź argumentacyjną\.?|wybierz jeden z nich i napisz wypowiedź\.?|zajmij stanowisko wobec "
                        r"powyższej tezy i je uzasadnij,?|uwzględniając w swojej argumentacji|minimum 300 wyrazów")

    def search(self, text, k):
        q = set(self.terms(self.BOILER.sub(" ", text)))
        scores = []
        for i, d in enumerate(self.docs):
            tf = {}
            for t in d:
                if t in q:
                    tf[t] = tf.get(t, 0) + 1
            s = sum(self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * len(d) / self.avg)) for t, f in tf.items())
            scores.append((s, i))
        ranked = [(s, i) for s, i in sorted(scores, reverse=True) if s > 0]
        if self.dense:  # hybryda RRF: BM25 łapie nazwy i daty, e5 parafrazy (H-N20)
            rrf = {}
            for ranking in ([i for _, i in ranked[:20]], self.dense.rank(self.BOILER.sub(" ", text), 20)):
                for pos, i in enumerate(ranking):
                    rrf[i] = rrf.get(i, 0) + 1 / (61 + pos)
            bm = dict((i, s) for s, i in ranked)
            return [{"title": self.notes[i]["title"], "text": self.notes[i]["text"], "score": round(bm.get(i, 0.0), 2),
                     "sub": self.notes[i].get("subtopic", "")}
                    for i, _ in sorted(rrf.items(), key=lambda x: -x[1])[:k]]
        return [{"title": self.notes[i]["title"], "text": self.notes[i]["text"], "score": round(s, 2),
                 "sub": self.notes[i].get("subtopic", "")} for s, i in ranked[:k]]


def match_route(route_cfg, item, kind):
    """Pierwsza reguła z route.json, której warunki pasują do zadania (zakres, obraz, typ); inaczej None."""
    for rule in (route_cfg or {}).get("rules", []):
        cond = rule.get("if", {})
        if "scope" in cond and cond["scope"] != item_scope(item):
            continue
        if "has_image" in cond and cond["has_image"] != bool(item.get("images")):
            continue
        if "kinds" in cond and not any(kind == k or (k == "closed" and kind.startswith("closed")) for k in cond["kinds"]):
            continue
        return rule
    return None


def load_exam(exam_dir):
    """exam.json z `items` (format organizatorów); awaryjnie `questions` albo goła lista (pytania-FORMAT.json)."""
    exam = json.loads((exam_dir / "exam.json").read_text(encoding="utf-8"))
    if isinstance(exam, list):
        exam = {"questions": exam}
    if "items" not in exam and isinstance(exam.get("questions"), list):
        print("UWAGA: brak `items` — konwersja z `questions`; exam_id sprawdź z answers-template.json", file=sys.stderr)
        exam["items"] = [{**q, "id": str(q["id"]), "max_points": q.get("max_points", q.get("points", 1)),
                          "source_text": q.get("source_text", ""), "images": q.get("images", []),
                          "answer_format": q.get("answer_format", "")} for q in exam["questions"]]
    exam.setdefault("exam_id", exam_dir.name)
    return exam


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--exam", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--base-url", default="http://127.0.0.1:8080/v1")
    p.add_argument("--vision", action="store_true", help="wysyłaj obrazy PNG (model z mmproj)")
    p.add_argument("--think", default="", help="typy z myśleniem, np. essay,rozstrz,open,podaj,closed (closed = wszystkie zamknięte)")
    p.add_argument("--no-think-kwargs", action="store_true", help="model bez przełącznika myślenia (np. Bielik)")
    p.add_argument("--rag", choices=["none", "bm25", "hyde"], default="none")
    p.add_argument("--rag-types", default="podaj,open,essay")
    p.add_argument("--rag-k", type=int, default=3)
    p.add_argument("--rag-min-score", type=float, default=0.0, help="odrzucaj fragmenty z wynikiem BM25 poniżej progu (H-N25)")
    p.add_argument("--index", default="data/kb/polqa_index")
    p.add_argument("--kb-essay", help="notatki (jsonl: title, subtopic, text) jako kontekst eseju, np. data/kb/kompendium.jsonl")
    p.add_argument("--kb-k", type=int, default=3)
    p.add_argument("--kb-rag", help="notatki (jsonl) jako kontekst dla typów z --rag-types, obok albo zamiast PolQA (H-N21)")
    p.add_argument("--kb-rag-k", type=int, default=2)
    p.add_argument("--kb-dense", action="store_true", help="hybryda BM25 + e5-small w wyszukiwaniu notatek (H-N20)")
    p.add_argument("--careful", action="store_true", help="w eseju: pomijaj niepewne szczegóły (błędy merytoryczne obniżają ocenę)")
    p.add_argument("--essay-choose", action="store_true", help="przed esejem samoocena wiedzy dla tematów i wybór (H-H8)")
    p.add_argument("--legacy-prompt", action="store_true", help="prompt z przebiegów Modal: inny system bez obrazów, bez dopisku o formacie")
    p.add_argument("--bare", action="store_true", help="goły model (baseline T2): bez dopisku o formacie, powtórek, poprawek eseju i normalizacji")
    p.add_argument("--route", help="route.json: reguły (zakres / obraz / typ) -> inny serwer i ustawienia (H-N23)")
    p.add_argument("--temperature", type=float, default=1.0)
    p.add_argument("--top-p", type=float, default=0.95)
    p.add_argument("--top-k", type=int, default=64)
    p.add_argument("--max-tokens", type=int, default=10000)
    p.add_argument("--essay-max-tokens", type=int, default=20000)
    p.add_argument("--answer-max-tokens", type=int, default=2048, help="limit bez myślenia (modele uczone z <think> potrzebują więcej)")
    p.add_argument("--essay-answer-max-tokens", type=int, default=4096)
    p.add_argument("--parallel", type=int, default=3)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--name", help="nazwa konfiguracji do statystyk (domyślnie nazwa katalogu wyjściowego)")
    p.add_argument("--essay-extend", type=int, default=0,
                   help="za krótki esej: do N rund dopisywania akapitów (zamiast przepisywania całości)")
    p.add_argument("--essay-min-words", type=int, default=350, help="próg dla --essay-extend")
    p.add_argument("--essay-topic-detect", action="store_true",
                   help="nagłówek „Temat nr N” z treści eseju (nakładanie słów); pytanie modelu tylko przy niejasnym wyniku")
    p.add_argument("--essay-refine-kb", help="drugie przejście eseju z notatkami (jsonl) dla wybranego tematu i aspektów")
    p.add_argument("--essay-refine-k", type=int, default=6)
    p.add_argument("--essay-refine-think", action="store_true", help="drugie przejście z myśleniem (jak pierwsze)")
    p.add_argument("--essay-mode", choices=["default", "structured", "rubric"], default="default",
                   help="structured: plan + akapit na aspekt w osobnych wywołaniach + wstęp/zakończenie (małe modele); "
                        "notatki z --essay-kb albo --kb-essay; rubric: wymagania najwyższego poziomu CKE dla każdego "
                        "elementu tematu w poleceniu (raport 22)")
    p.add_argument("--essay-rubric-plan", action="store_true",
                   help="z --essay-mode rubric: najpierw jawny plan (fakty, przyczyna → skutek, ocena na element), "
                        "potem esej według planu")
    p.add_argument("--essay-rubric-fixed", action="store_true",
                   help="z --essay-mode rubric: pierwszy esej bez wskazówek (wybór tematu jak zwykle), potem nowy esej "
                        "na ten sam temat z wymaganiami CKE tylko dla niego")
    p.add_argument("--essay-kb", help="notatki (jsonl) dla --essay-mode structured (domyślnie --kb-essay)")
    p.add_argument("--essay-pick", choices=["model", "kb", "mix"], default="model",
                   help="wybór tematu w trybie structured: samoocena modelu, pokrycie bazy wiedzy albo oba")
    p.add_argument("--essay-plan-think", action="store_true", help="plan eseju (structured) z myśleniem")
    p.add_argument("--ocr", action="store_true", help="tesseract pol+eng na obrazach: tekst do treści zadania i zapytania RAG")
    p.add_argument("--ocr-cache", default=str(Path.home() / ".cache/matura_ocr"))
    p.add_argument("--rag-clean-query", action="store_true", help="bez znaczników [Obraz: …] i adresów w zapytaniu RAG")
    p.add_argument("--only-ids", help="tylko te zadania (np. 26,25); reszta z --merge-from albo pominięta")
    p.add_argument("--essay-from", help="katalog przebiegu: pierwsza wersja eseju z jego debug.jsonl (test poprawek na tych samych esejach)")
    p.add_argument("--merge-from", help="katalog przebiegu, z którego debug.jsonl bierzemy zadania spoza --only-ids")
    p.add_argument("--fill-fields", action="store_true",
                   help="otwarte z wzorem odpowiedzi (Etykieta:/•): gdy brakuje pól, powtórka z prośbą o pełny wzór (raport 12)")
    p.add_argument("--match-names-hint", action="store_true",
                   help="dopasowania ze wzorem „A: 1”, gdy polecenie wymaga nazw: wskazówka i bez redukcji do numeru (raport 13)")
    p.add_argument("--think-retry", action="store_true",
                   help="myślenie urwane / pusta odpowiedź: najpierw jedna powtórka z myśleniem i innym seedem, "
                        "dopiero potem bez myślenia (raport 21)")
    p.add_argument("--match-retry", action="store_true",
                   help="dopasowania, gdzie polecenie chce nazw, a wyszły cyfry: bez redukcji do numeru albo jedna powtórka, "
                        "przyjęta tylko z nazwami; bez wskazówki --match-names-hint (raport 21)")
    p.add_argument("--caption-url", help="pomocniczy VLM (np. Qwen3.5-0.8B + mmproj) do opisów obrazów w treści zadania "
                                         "dla modelu bez wizji, np. http://127.0.0.1:8422/v1 (raport 15)")
    p.add_argument("--image-tiles", action="store_true",
                   help="obok każdego dużego obrazu 2–4 powiększone fragmenty (mapy, drobne napisy; raport 15)")
    p.add_argument("--img-retrieval", help="indeks podobnych obrazów z podpisami (harness/img_retrieval.py build): "
                                           "podpisy top-k pod znacznikiem obrazu i w zapytaniu RAG (raport 23)")
    p.add_argument("--img-retrieval-k", type=int, default=3)
    p.add_argument("--img-retrieval-min-sim", type=float, default=0.0)
    p.add_argument("--img-retrieval-device", default="cpu")
    p.add_argument("--rozstrz-hint", action="store_true",
                   help="„rozstrzygnij”: wskazówka o identyfikacji źródeł po szczegółach i bez niepewnych dopisków (raport 12)")
    p.add_argument("--factcheck", default="",
                   help="recenzent faktów po odpowiedzi dla typów, np. essay,podaj,rozstrz,open: podmienia tylko błędne zdania (raport 17)")
    p.add_argument("--factcheck-kb", help="notatki (jsonl) do recenzenta faktów, BM25 per zdanie")
    p.add_argument("--factcheck-think", action="store_true", help="recenzent z myśleniem")
    p.add_argument("--factcheck-no-confirm", action="store_true", help="bez pytania kontrolnego A/B przed podmianą")
    p.add_argument("--factcheck-max", type=int, default=6, help="maks. podmienionych zdań na odpowiedź")
    p.add_argument("--answer-from", help="katalog przebiegu: odpowiedzi z jego debug.jsonl bez generowania (test --factcheck)")
    p.add_argument("--vote-closed", type=int, default=0,
                   help="zamknięte: głos większościowy z K próbek (seed+1000*j), per część odpowiedzi (raport 19)")
    p.add_argument("--vote-adaptive", action="store_true",
                   help="z --vote-closed: najpierw 2 próbki, dobór do K tylko przy niezgodzie")
    args = p.parse_args()

    exam_dir, out = Path(args.exam), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    exam = load_exam(exam_dir)
    route_cfg = json.loads(Path(args.route).read_text(encoding="utf-8")) if args.route else None
    clients, clients_lock = {}, threading.Lock()
    rag_types = set(filter(None, args.rag_types.split(",")))
    retriever = Retriever(args.index) if args.rag != "none" else None
    notes = NoteRetriever(args.kb_essay, dense=args.kb_dense) if args.kb_essay else None
    kb_rag = NoteRetriever(args.kb_rag, dense=args.kb_dense) if args.kb_rag else None
    refine_notes = NoteRetriever(args.essay_refine_kb) if args.essay_refine_kb else None
    s_kb = args.essay_kb or args.kb_essay
    s_notes_ret = (notes if s_kb == args.kb_essay and notes else NoteRetriever(s_kb)) if (
        args.essay_mode == "structured" and s_kb) else None
    essay_from = ({r["id"]: r for r in (json.loads(l) for l in open(Path(args.essay_from) / "debug.jsonl", encoding="utf-8"))
                   if r["kind"] == "essay"} if args.essay_from else {})
    answer_from = ({r["id"]: r for r in (json.loads(l) for l in open(Path(args.answer_from) / "debug.jsonl", encoding="utf-8"))}
                   if args.answer_from else {})
    fc_types = set(filter(None, args.factcheck.split(",")))
    fc_notes = (NoteRetriever(args.factcheck_kb) if args.factcheck_kb else None) if fc_types else None
    local = threading.local()  # liczniki tokenów bieżącego zadania

    def client_for(url):
        with clients_lock:
            if url not in clients:
                clients[url] = OpenAI(base_url=url, api_key="x", timeout=3600)
            return clients[url]

    def solve(item):
        t0 = time.time()
        kind = item_type(item)
        rule = match_route(route_cfg, item, kind) or {}
        cfg = {"base_url": args.base_url, "no_think_kwargs": args.no_think_kwargs, "think": args.think, "vision": args.vision,
               "temperature": args.temperature, "top_p": args.top_p, "top_k": args.top_k, **rule.get("set", {})}
        think_types = set(filter(None, cfg["think"].split(",")))
        local.usage = {"prompt_tokens": 0, "completion_tokens": 0, "calls": 0, "reasoning_chars": 0}

        def chat(messages, max_tokens, think, seed=None):
            extra = {"seed": args.seed if seed is None else seed, "top_k": cfg["top_k"]}
            if not cfg["no_think_kwargs"]:
                extra["chat_template_kwargs"] = {"enable_thinking": think}
            for attempt in range(8):  # serwer pod nadzorcą wstaje po awarii w ~30–60 s
                try:
                    r = client_for(cfg["base_url"]).chat.completions.create(
                        model="m", messages=messages, max_tokens=max_tokens, temperature=cfg["temperature"], top_p=cfg["top_p"],
                        extra_body=extra)
                    break
                except (APIConnectionError, APITimeoutError, InternalServerError):
                    if attempt == 7:
                        raise
                    local.usage["retries"] = local.usage.get("retries", 0) + 1
                    time.sleep(10 * (attempt + 1))
            m = r.choices[0].message
            reasoning = getattr(m, "reasoning_content", "") or ""
            u = local.usage
            u["calls"] += 1
            u["reasoning_chars"] += len(reasoning)
            if r.usage:
                u["prompt_tokens"] += r.usage.prompt_tokens or 0
                u["completion_tokens"] += r.usage.completion_tokens or 0
            return m.content or "", reasoning, r.choices[0].finish_reason

        def run_factcheck(answer):
            imgs = ([p for k, im in enumerate(item["images"], 1) for p in image_parts(exam_dir / im["path"], k, False)]
                    if cfg["vision"] and item.get("images") and kind != "essay" else None)
            try:
                return factcheck(chat, item, kind, answer, fc_notes, args.factcheck_think, imgs,
                                 not args.factcheck_no_confirm, args.factcheck_max)
            except Exception as e:  # recenzent nie może zatrzymać egzaminu
                return answer, {"why": repr(e)[:300]}

        if item["id"] in answer_from:
            prev = answer_from[item["id"]]
            answer, fc = prev["answer"], None
            if kind in fc_types and answer.strip():
                answer, fc = run_factcheck(answer)
            return {**prev, "answer": answer, "answer_from": str(args.answer_from), "usage": dict(local.usage),
                    "seconds": round(time.time() - t0, 1), **({"factcheck": fc} if fc else {})}

        ocr, essay_log = {}, {}
        if args.ocr and item.get("images"):
            item, ocr = add_ocr(item, exam_dir, args.ocr_cache)
        if captions and item.get("images"):
            item, caps = add_captions(item, captions)
            ocr = {**ocr, **{p + "#opis": t for p, t in caps.items()}}
        if img_hints and item.get("images"):
            item, hs = add_img_hints(item, img_hints)
            ocr = {**ocr, **{p + "#podobne": t for p, t in hs.items()}}
        system = system_for(item, args.legacy_prompt)
        body = build_body(item, kind, args.legacy_prompt or args.bare)
        rag_ctx, hyde, chosen = [], "", None
        rag_on = (retriever or kb_rag) and (kind in rag_types or (kind.startswith("closed") and "closed" in rag_types))
        if rag_on:
            if args.rag == "hyde":
                try:
                    hyde, _, _ = chat([{"role": "system", "content": system},
                                       {"role": "user", "content": body + "\n\n" + HYDE_PROMPT}], 200, False)
                except Exception:
                    hyde = ""
            src = item.get("source_text", "")
            if args.rag_clean_query:
                src = re.sub(r"\[Obraz:[^\]]*\]|https?://\S+|www\.\S+", " ", src)
            query = f"{hyde} {item['question']} {src[:600]}"
            if ocr and OCR_HEAD not in src[:600] and CAPTION_HEAD not in src[:600]:
                query += " " + " ".join(ocr.values())
            if retriever:
                rag_ctx = [c for c in retriever.search(query, args.rag_k) if c["score"] >= args.rag_min_score]
            if kb_rag:
                rag_ctx = kb_rag.search(query, args.kb_rag_k) + rag_ctx
        if kind == "essay" and notes:
            rag_ctx = notes.search(item["question"], args.kb_k) + rag_ctx
        if kind == "essay" and args.careful:
            body += "\n\n" + CAREFUL
        rubric = kind == "essay" and args.essay_mode == "rubric" and not args.bare
        body_plain = body
        if rubric and not args.essay_rubric_fixed:
            body += "\n\n" + rubric_hint(item["question"])
        if kind == "rozstrz" and args.rozstrz_hint:
            body += "\n\n" + ROZSTRZ_HINT
        names = args.match_names_hint and match_wants_names(item)
        if names:
            body += "\n\n" + MATCH_NAMES_HINT
        if kind == "essay" and args.essay_choose:
            try:
                rating, _, _ = chat([{"role": "system", "content": system},
                                     {"role": "user", "content": build_text(body, rag_ctx) + "\n\n" + CHOOSE_PROMPT}], 300, False)
                m = re.search(r"Wybór:\s*(\d)", rating)
                chosen = int(m.group(1)) if m else None
            except Exception:
                chosen = None
            if chosen:
                body += f"\n\nNapisz wypracowanie na temat nr {chosen}."
        text = build_text(body, rag_ctx)
        if cfg["vision"] and item.get("images"):
            content = [p for k, im in enumerate(item["images"], 1)
                       for p in image_parts(exam_dir / im["path"], k, args.image_tiles and not args.bare)]
            if len(content) > len(item["images"]):
                text += "\n\n" + TILES_NOTE
            content.append({"type": "text", "text": text})
        else:
            content = text
        think = kind in think_types or (kind.startswith("closed") and "closed" in think_types)
        max_tokens = args.essay_max_tokens if kind == "essay" else args.max_tokens
        if not think:
            max_tokens = args.essay_answer_max_tokens if kind == "essay" else args.answer_max_tokens
        messages = [{"role": "system", "content": system}, {"role": "user", "content": content}]
        if rubric and args.essay_rubric_plan and not args.essay_rubric_fixed and not essay_from.get(item["id"]):
            c_plan = ([*content[:-1], {"type": "text", "text": content[-1]["text"] + "\n\n" + RUBRIC_PLAN}]
                      if isinstance(content, list) else content + "\n\n" + RUBRIC_PLAN)
            try:
                plan_raw, _, pfin = chat([messages[0], {"role": "user", "content": c_plan}], max_tokens, think)
                plan = clean_answer(plan_raw)
                essay_log["rubric_plan"] = {"finish": pfin, "plan": plan[:3000]}
                if plan and pfin != "length":
                    messages = [messages[0], {"role": "user", "content": c_plan}, {"role": "assistant", "content": plan},
                                {"role": "user", "content": RUBRIC_WRITE}]
            except Exception as e:
                essay_log["rubric_plan"] = {"why": repr(e)[:200]}
        structured = None
        if kind == "essay" and args.essay_mode == "structured" and not args.bare:
            try:
                structured, essay_log["structured"] = structured_essay(
                    chat, item["question"], s_notes_ret, args.essay_pick, args.essay_plan_think,
                    min_words=max(300, args.essay_min_words), think_tokens=args.essay_max_tokens)
            except Exception as e:
                essay_log["structured"] = {"why": repr(e)[:300]}
        if structured:
            raw, reasoning, finish, err = structured, "", "stop", None
        elif kind == "essay" and essay_from.get(item["id"]):  # para przed/po: ten sam esej, tylko nowe poprawki
            prev = essay_from[item["id"]]
            raw, reasoning, finish, err = prev["answer"], prev.get("reasoning", ""), prev["finish_reason"], None
        else:
            try:
                raw, reasoning, finish = chat(messages, max_tokens, think)
                err = None
            except Exception as e:  # awaria jednego zadania nie może zatrzymać egzaminu
                raw, reasoning, finish, err = "", "", "error", repr(e)[:500]
        answer = clean_answer(raw)
        fallback, think_retry = False, None
        if (args.think_retry and think and not args.bare and (finish == "length" or not answer.strip())
                and not essay_from.get(item["id"])):
            think_retry = {"first_finish": finish, "first_reasoning_chars": len(reasoning)}
            try:
                raw2, reasoning2, fin2 = chat(messages, max_tokens, True, seed=args.seed + 7)
                a2 = clean_answer(raw2)
                think_retry.update(finish=fin2, ok=bool(a2.strip()) and fin2 != "length")
                if think_retry["ok"]:
                    raw, reasoning, finish, answer = raw2, reasoning2, fin2, a2
            except Exception as e:
                think_retry["why"] = repr(e)[:200]
        if think and not args.bare and (finish == "length" or not answer.strip()) and not essay_from.get(item["id"]):
            # zapętlone myślenie zjada limit tokenów; lepsza odpowiedź bez myślenia niż żadna
            fallback = True
            try:
                raw, _, finish = chat(messages, 4096 if kind == "essay" else 2048, False)
                answer = clean_answer(raw)
            except Exception as e:
                err = repr(e)[:500]
        fields_log = None
        tpl = answer_template(item["question"]) if args.fill_fields and kind not in ("essay",) and not kind.startswith(
            "closed") else []
        if tpl and answer.strip() and template_filled(tpl, answer) < len(tpl):
            fields_log = {"before": answer, "filled": template_filled(tpl, answer), "need": len(tpl)}
            try:
                ask = "\n\n" + FIELDS_RETRY + "\n".join(tpl)
                c2 = ([*content[:-1], {"type": "text", "text": content[-1]["text"] + ask}] if isinstance(content, list)
                      else content + ask)
                pre = tpl[0] + ("" if tpl[0] == "•" else " ")
                raw2, _, fin2 = chat([messages[0], {"role": "user", "content": c2}, {"role": "assistant", "content": pre}],
                                     args.answer_max_tokens, False)
                raw2 = raw2 if raw2.lstrip().startswith(tpl[0]) else pre + raw2.lstrip()
                a2 = clean_answer(raw2)
                fields_log["after_filled"] = template_filled(tpl, a2)
                if a2.strip() and fin2 != "length" and fields_log["after_filled"] == len(tpl):
                    answer, raw = a2, raw2
                    fields_log["used"] = True
            except Exception as e:
                fields_log["why"] = repr(e)[:200]
        if structured:
            essay_log["words"] = len(answer.split())
        elif kind == "essay" and answer and not args.bare:
            if rubric and args.essay_rubric_fixed:
                answer, essay_log["rubric_fixed"] = rubric_rewrite(
                    chat, system, build_text(body_plain, rag_ctx), item["question"], answer, max_tokens, think)
            if rubric:
                answer = rubric_clean(answer)
            if not (args.essay_extend or args.essay_topic_detect or refine_notes):
                answer = fix_essay(chat, content, answer)
            else:
                base = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": content}]
                if refine_notes:
                    rthink = args.essay_refine_think and think
                    answer, essay_log["refine"] = refine_essay(
                        chat, base, item["question"], answer, refine_notes, args.essay_refine_k,
                        args.essay_max_tokens if rthink else args.essay_answer_max_tokens, rthink)
                if args.essay_extend:
                    answer, essay_log["extend"] = extend_essay(chat, base, item["question"], answer,
                                                               args.essay_min_words, args.essay_extend)
                else:
                    answer = fix_essay(chat, content, answer, header=False)
                answer, essay_log["header"] = add_header(chat, base, item["question"], answer, args.essay_topic_detect)
                essay_log["words"] = len(answer.split())
        fc = None
        if kind in fc_types and answer.strip() and not args.bare:
            answer, fc = run_factcheck(answer)
        vote_log, match_log = None, None
        if kind.startswith("closed") and not args.bare:
            pre_norm = answer
            answer = normalize_closed(kind, item["answer_format"], answer, names)
            if args.match_retry and not names and match_wants_names(item) and match_digits(item["answer_format"], answer):
                answer, match_log = match_names_retry(chat, messages, max_tokens, think, item, pre_norm, answer, args.seed)
            if args.vote_closed > 1 and answer.strip():
                answer, vote_log = vote_samples(chat, messages, max_tokens, think, kind, item["answer_format"], names, answer)
        return {"id": item["id"], "kind": kind, "scope": item_scope(item), "has_image": bool(item.get("images")),
                "route": rule.get("name"), "answer": answer, "raw": raw, "reasoning": reasoning[-4000:],
                "reasoning_chars": len(reasoning), "think": think, "finish_reason": finish, "fallback": fallback, "error": err,
                "hyde": hyde, "rag": rag_ctx, "essay_choice": chosen, "usage": dict(local.usage),
                "seconds": round(time.time() - t0, 1), **({"ocr": ocr} if ocr else {}),
                **({"essay_log": essay_log} if essay_log else {}), **({"fields": fields_log} if fields_log else {}),
                **({"factcheck": fc} if fc else {}), **({"vote": vote_log} if vote_log else {}),
                **({"think_retry": think_retry} if think_retry else {}), **({"match_retry": match_log} if match_log else {})}

    def vote_samples(chat, messages, max_tokens, think, kind, fmt, names, first):
        usage = local.usage

        def one(j):
            local.usage = {"prompt_tokens": 0, "completion_tokens": 0, "calls": 0, "reasoning_chars": 0}
            try:
                raw, _, fin = chat(messages, max_tokens, think, seed=args.seed + 1000 * j)
                a = clean_answer(raw)
                if think and (fin == "length" or not a.strip()):
                    raw, _, fin = chat(messages, 2048, False, seed=args.seed + 1000 * j)
                    a = clean_answer(raw)
                a = normalize_closed(kind, fmt, a, names) if a.strip() else ""
            except Exception:
                a = ""
            return a, local.usage

        def draw(js):
            with ThreadPoolExecutor(len(js)) as ex:
                for a, u in ex.map(one, js):
                    for k, v in u.items():
                        usage[k] = usage.get(k, 0) + v
                    if a:
                        samples.append(a)

        samples = [first]
        K = args.vote_closed
        draw([1] if args.vote_adaptive else list(range(1, K)))
        agree = len(samples) > 1 and closed_parts(kind, fmt, samples[0]) == closed_parts(kind, fmt, samples[1])
        if args.vote_adaptive and K > 2 and not agree:
            draw(list(range(2, K)))
        voted = first if args.vote_adaptive and agree else vote_closed(kind, fmt, samples)
        return voted, {"samples": samples, "voted": voted, "changed": voted != first}

    t_start = time.time()
    todo = exam["items"]
    if args.only_ids:
        only = set(args.only_ids.split(","))
        todo = [i for i in exam["items"] if i["id"] in only]
    captions = {}
    if args.caption_url and not args.bare:
        cap_client = OpenAI(base_url=args.caption_url, api_key="x", timeout=600)
        jobs = {}
        for i in todo:
            for im in i.get("images") or []:
                lines = i.get("source_text", "").splitlines()
                at = next((n for n, l in enumerate(lines) if im["path"] in l), None)
                near = [] if at is None else [l for l in lines[max(0, at - 1):at + 3] if l.strip() and "[Obraz:" not in l]
                jobs.setdefault(im["path"], "\n".join(near)[:300] or "(none)")

        def cap(kv):
            try:
                return kv[0], caption_image(cap_client, exam_dir / kv[0], kv[1])
            except Exception as e:  # brak opisu nie może zatrzymać egzaminu
                print(f"UWAGA: opis obrazu {kv[0]} nieudany: {e!r}"[:300], file=sys.stderr)
                return kv[0], ""
        with ThreadPoolExecutor(args.parallel) as ex:
            captions = dict(ex.map(cap, jobs.items()))
        print(f"opisy obrazów: {sum(1 for v in captions.values() if v)}/{len(jobs)} w {time.time() - t_start:.0f} s", file=sys.stderr)
    img_hints = {}
    if args.img_retrieval and not args.bare:
        try:  # brak indeksu / torcha nie może zatrzymać egzaminu
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from img_retrieval import Index, hint_block
            paths = sorted({im["path"] for i in todo for im in i.get("images") or []})
            hits = Index(args.img_retrieval, args.img_retrieval_device).search(
                [exam_dir / p for p in paths], args.img_retrieval_k, args.img_retrieval_min_sim)
            img_hints = {p: hint_block(h) for p, h in zip(paths, hits) if h}
            print(f"podobne obrazy: {len(img_hints)}/{len(paths)}", file=sys.stderr)
        except Exception as e:
            print(f"UWAGA: --img-retrieval nieudane: {e!r}"[:300], file=sys.stderr)
    with ThreadPoolExecutor(args.parallel) as ex:
        results = list(ex.map(solve, todo))
    if args.only_ids and args.merge_from:
        prev = {r["id"]: r for r in (json.loads(l) for l in open(Path(args.merge_from) / "debug.jsonl", encoding="utf-8"))}
        new = {r["id"]: r for r in results}
        results = [new.get(i["id"]) or {**prev[i["id"]], "merged_from": str(args.merge_from)} for i in exam["items"]]
    with open(out / "debug.jsonl", "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    answers = {"exam_id": exam["exam_id"], "answers": [{"id": r["id"], "answer": r["answer"]} for r in results]}
    (out / "answers.json").write_text(json.dumps(answers, ensure_ascii=False, indent=2), encoding="utf-8")
    ids = {i["id"] for i in exam["items"]} if not args.only_ids or args.merge_from else {r["id"] for r in results}
    assert ids == {a["id"] for a in answers["answers"]} and all(isinstance(a["answer"], str) for a in answers["answers"])
    summary = {"exam_id": exam["exam_id"], "n": len(results), "errors": sum(bool(r["error"]) for r in results),
               "truncated": sum(r["finish_reason"] == "length" for r in results), "empty": sum(not r["answer"] for r in results),
               "fallback": sum(r["fallback"] for r in results), "seconds": round(sum(r["seconds"] for r in results), 1),
               "wall_seconds": round(time.time() - t_start, 1),
               "completion_tokens": sum(r["usage"]["completion_tokens"] for r in results)}
    meta = {"name": args.name or out.name, "args": vars(args), "summary": summary}
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
