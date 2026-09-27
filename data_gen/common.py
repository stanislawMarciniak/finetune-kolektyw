"""Klient Forgehand, budżet (z zapasem 1,2), JSONL i narzędzia jakości."""

import fcntl
import json
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
COST_LOG = ROOT / "data_gen" / "cost_log.jsonl"
STATE = ROOT / "data_gen" / "state"
SFT = ROOT / "data" / "sft"
KB = ROOT / "data" / "kb" / "kompendium.jsonl"

BASE_URL = "https://app.forgehand.app/api/v1/teams/01a0da5f-05f4-700d-a554-4c8f829182f1/llm/v1"
PRICES = {"gpt-6-luna": (0.10, 0.45), "gpt-6-sol": (2.04, 12.2)}
MARKUP = 1.2
STAGE_LIMITS = {"E1": 3.0, "E2": 5.0, "E3": 14.0, "E4": 9.0, "E5": 13.0, "E6": 4.0, "E7": 8.0}
# E1–E4 = 31 USD, E5 = 13 USD, E6 = 4 USD, E7 (baza wiedzy v2/v3) = 8 USD.
TOTAL_LIMIT = 52.0
RESERVE_PATH = STATE / "reservations.json"

ANSWER_FORMAT = {
    "open": "Tekst po polsku. Podaj wszystkie wymagane elementy odpowiedzi.",
    "essay": "Jeden tekst: numer wybranego tematu i całe wypracowanie. Minimum 300 wyrazów zgodnie z poleceniem.",
    "closed_choice": "A",
}

OPEN_KINDS = ("rozstrzygnij", "podaj", "wyjasnij", "porownaj")
CLOSED_TYPES = ("closed_tf", "closed_choice", "closed_match", "closed_multi")
ITEM_TYPES = CLOSED_TYPES + ("open", "essay")


class BudgetExceeded(RuntimeError):
    pass


def ensure_dirs():
    for p in (STATE, SFT, SFT / "samples", ROOT / "data_gen" / "logs", KB.parent):
        p.mkdir(parents=True, exist_ok=True)


def load_env():
    path = ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def safe_err(exc):
    text = f"{type(exc).__name__}: {exc}"
    text = re.sub(r"fh_[A-Za-z0-9_\-]+", "fh_***", text)
    text = re.sub(r"sk-[A-Za-z0-9_\-]+", "sk-***", text)
    return text[:400]


def _flock_path(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    return open(path, "a+", encoding="utf-8")


def append_jsonl(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(obj, ensure_ascii=False) + "\n"
    with _flock_path(path) as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        fh.seek(0, os.SEEK_END)
        fh.write(line)
        fh.flush()
        fcntl.flock(fh, fcntl.LOCK_UN)


def read_jsonl(path):
    path = Path(path)
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def load_ids(path, key="id"):
    return {row[key] for row in read_jsonl(path) if key in row}


def spent_by_stage():
    totals = {s: 0.0 for s in STAGE_LIMITS}
    total = 0.0
    for row in read_jsonl(COST_LOG):
        cost = float(row.get("cost_usd") or 0)
        total += cost
        stage = row.get("stage")
        if stage in totals:
            totals[stage] += cost
    return totals, total


def _reservations():
    if not RESERVE_PATH.exists():
        return []
    try:
        data = json.loads(RESERVE_PATH.read_text(encoding="utf-8") or "{}")
    except json.JSONDecodeError:
        return []
    now = time.time()
    return [r for r in data.get("reservations", []) if now - r.get("ts", 0) < 360]


def _write_reservations(rows):
    RESERVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = RESERVE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps({"reservations": rows}, ensure_ascii=False), encoding="utf-8")
    tmp.replace(RESERVE_PATH)


def _budget_lock():
    ensure_dirs()
    return _flock_path(STATE / "budget.lock")


class Forge:
    def __init__(self):
        load_env()
        key = os.environ.get("FORGEHAND_API_KEY", "")
        if not key:
            raise RuntimeError("Brak FORGEHAND_API_KEY")
        self.client = OpenAI(api_key=key, base_url=BASE_URL, timeout=180.0, max_retries=0)

    def call(self, stage, model, system, user, max_tokens, estimate, tag=""):
        if stage not in STAGE_LIMITS:
            raise ValueError(stage)
        if model not in PRICES:
            raise ValueError(model)
        rid = self._reserve(stage, estimate)
        try:
            content, usage = self._request(model, system, user, max_tokens)
            cost = self._cost(model, usage)
            self._commit(rid, stage, model, usage, cost, tag)
            return content, usage, cost
        except Exception:
            self._release(rid)
            raise

    def call_json(self, stage, model, system, user, max_tokens, estimate, tag=""):
        last = None
        for attempt in range(3):
            try:
                content, usage, cost = self.call(stage, model, system, user, max_tokens, estimate, tag)
                return parse_json(content), usage, cost
            except BudgetExceeded:
                raise
            except Exception as exc:
                last = exc
                msg = safe_err(exc).lower()
                if "budget" in msg:
                    raise
                wait = min(60, 4 * (attempt + 1))
                if any(s in msg for s in ("429", "rate", "timeout", "503", "502", "500", "overloaded")):
                    print(f"retry {tag} {safe_err(exc)[:180]} sleep {wait}s", flush=True)
                    time.sleep(wait)
                    continue
                if isinstance(exc, json.JSONDecodeError) or "json" in msg or "expecting" in msg:
                    print(f"retry-json {tag} {safe_err(exc)[:180]}", flush=True)
                    time.sleep(2)
                    continue
                print(f"retry {tag} {safe_err(exc)[:180]} sleep {wait}s", flush=True)
                time.sleep(wait)
        raise RuntimeError(f"call failed {tag}: {safe_err(last)}")

    def _reserve(self, stage, estimate):
        rid = uuid.uuid4().hex
        with _budget_lock() as fh:
            fcntl.flock(fh, fcntl.LOCK_EX)
            try:
                rows = _reservations()
                spent, total = spent_by_stage()
                inflight_stage = sum(r["usd"] for r in rows if r["stage"] == stage)
                inflight_total = sum(r["usd"] for r in rows)
                if spent[stage] + inflight_stage + estimate > STAGE_LIMITS[stage] + 1e-9:
                    raise BudgetExceeded(stage)
                if total + inflight_total + estimate > TOTAL_LIMIT + 1e-9:
                    raise BudgetExceeded("TOTAL")
                rows.append({"id": rid, "stage": stage, "usd": estimate, "ts": time.time()})
                _write_reservations(rows)
            finally:
                fcntl.flock(fh, fcntl.LOCK_UN)
        return rid

    def _release(self, rid):
        with _budget_lock() as fh:
            fcntl.flock(fh, fcntl.LOCK_EX)
            try:
                rows = [r for r in _reservations() if r["id"] != rid]
                _write_reservations(rows)
            finally:
                fcntl.flock(fh, fcntl.LOCK_UN)

    def _commit(self, rid, stage, model, usage, cost, tag):
        with _budget_lock() as fh:
            fcntl.flock(fh, fcntl.LOCK_EX)
            try:
                rows = [r for r in _reservations() if r["id"] != rid]
                _write_reservations(rows)
                append_jsonl(COST_LOG, {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "stage": stage,
                    "model": model,
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "cost_usd": round(cost, 6),
                    "tag": tag,
                })
            finally:
                fcntl.flock(fh, fcntl.LOCK_UN)
        spent, total = spent_by_stage()
        print(f"cost {stage} {tag} ${cost:.4f} stage ${spent[stage]:.3f} total ${total:.3f}", flush=True)

    def _request(self, model, system, user, max_tokens):
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        variants = [
            {"max_completion_tokens": max_tokens, "reasoning_effort": "low", "response_format": {"type": "json_object"}},
            {"max_tokens": max_tokens, "reasoning_effort": "low", "response_format": {"type": "json_object"}},
            {"max_completion_tokens": max_tokens, "response_format": {"type": "json_object"}},
            {"max_tokens": max_tokens},
        ]
        last = None
        for kw in variants:
            try:
                resp = self.client.chat.completions.create(model=model, messages=messages, **kw)
                content = resp.choices[0].message.content or ""
                details = getattr(resp.usage, "completion_tokens_details", None)
                usage = {
                    "prompt_tokens": int(getattr(resp.usage, "prompt_tokens", 0) or 0),
                    "completion_tokens": int(getattr(resp.usage, "completion_tokens", 0) or 0),
                    "reasoning_tokens": int(getattr(details, "reasoning_tokens", 0) or 0),
                }
                # Przy niskim limicie model zużywa go na reasoning i zwraca pustą treść.
                if not content.strip() and "reasoning_effort" in kw and max_tokens < 6000:
                    kw2 = dict(kw)
                    kw2["max_completion_tokens"] = min(6000, max(max_tokens * 2, 2000))
                    kw2.pop("max_tokens", None)
                    resp = self.client.chat.completions.create(model=model, messages=messages, **kw2)
                    content = resp.choices[0].message.content or ""
                    details = getattr(resp.usage, "completion_tokens_details", None)
                    usage = {
                        "prompt_tokens": usage["prompt_tokens"] + int(getattr(resp.usage, "prompt_tokens", 0) or 0),
                        "completion_tokens": usage["completion_tokens"] + int(getattr(resp.usage, "completion_tokens", 0) or 0),
                        "reasoning_tokens": usage["reasoning_tokens"] + int(getattr(details, "reasoning_tokens", 0) or 0),
                    }
                return content, usage
            except Exception as exc:
                last = exc
                msg = safe_err(exc).lower()
                if any(s in msg for s in ("429", "timeout", "503", "502", "500", "overloaded", "rate")):
                    raise
                continue
        raise last

    @staticmethod
    def _cost(model, usage):
        pin, pout = PRICES[model]
        raw = usage.get("prompt_tokens", 0) * pin / 1e6 + usage.get("completion_tokens", 0) * pout / 1e6
        return raw * MARKUP


def parse_json(content):
    text = re.sub(r"<think>.*?</think>", "", content or "", flags=re.S).strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def word_ngrams(text, n=4):
    words = re.findall(r"\w+", (text or "").lower(), flags=re.UNICODE)
    if len(words) < n:
        return {tuple(words)} if words else set()
    return {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}


def jaccard(a, b):
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def collapse_alternatives(text):
    text = text or ""
    text = re.sub(r"(\d)\s*/\s*(\d)", r"\1–\2", text)
    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"\s+/\s+[^,.;:\n]{1,90}", "", text)
    text = re.sub(r"(?i)\bprzykładowe uzasadnienie:\s*", "", text)
    text = re.sub(r"(?i)\bprzykładowa odpowiedź:\s*", "", text)
    text = re.sub(r"(?i)\bprzykładowe rozwiązanie:?\s*", "", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def has_alternative_marker(text):
    if re.search(r"\salbo\s", text or "", flags=re.I):
        return True
    if " / " in (text or ""):
        return True
    return False


def tf_template(n):
    lines = []
    for i in range(1, n + 1):
        lines.append(f"{i}: {'P' if i % 2 else 'F'}")
    return "\n".join(lines)


def match_template(n):
    letters = "ABCDEF"
    return "\n".join(f"{letters[i]}: 1" for i in range(n))


def multi_template(n):
    return "\n".join(f"{i}: A" for i in range(1, n + 1))


def answer_lines(ans):
    return [ln.strip() for ln in (ans or "").splitlines() if ln.strip()]


def canonical_format(typ, model_answer):
    n = max(1, len(answer_lines(model_answer)))
    if typ == "closed_tf":
        return tf_template(n)
    if typ == "closed_match":
        return match_template(n)
    if typ == "closed_multi":
        return multi_template(n)
    if typ == "closed_choice":
        return ANSWER_FORMAT["closed_choice"]
    if typ == "essay":
        return ANSWER_FORMAT["essay"]
    return ANSWER_FORMAT["open"]


def normalize_closed(typ, ans):
    lines = answer_lines(ans)
    out = []
    for ln in lines:
        ln = re.sub(r"\s+", " ", ln).strip()
        if typ == "closed_choice":
            m = re.search(r"\b([A-Fa-f])\b", ln)
            return m.group(1).upper() if m else ln.upper()
        if typ == "closed_tf":
            m = re.match(r"(\d+)\s*[\.\)\-:]\s*([PpFf])", ln)
            if m:
                out.append(f"{int(m.group(1))}: {m.group(2).upper()}")
            continue
        if typ == "closed_multi":
            m = re.match(r"(\d+)\s*[\.\)\-:]\s*([A-Fa-f])", ln)
            if m:
                out.append(f"{int(m.group(1))}: {m.group(2).upper()}")
            continue
        if typ == "closed_match":
            m = re.match(r"([A-Fa-f])\s*[\.\)\-:]\s*(.+)", ln)
            if m:
                out.append(f"{m.group(1).upper()}: {m.group(2).strip()}")
            continue
    if typ == "closed_choice":
        m = re.search(r"\b([A-Fa-f])\b", ans or "")
        return m.group(1).upper() if m else (ans or "").strip().upper()
    return "\n".join(out)


def valid_model_answer(typ, ans):
    ans = (ans or "").strip()
    if not ans:
        return False
    if typ == "closed_choice":
        return bool(re.fullmatch(r"[A-F]", normalize_closed(typ, ans)))
    if typ == "closed_tf":
        lines = normalize_closed(typ, ans).splitlines()
        return len(lines) >= 2 and all(re.fullmatch(r"\d+: [PF]", ln) for ln in lines)
    if typ == "closed_multi":
        lines = normalize_closed(typ, ans).splitlines()
        return len(lines) >= 2 and all(re.fullmatch(r"\d+: [A-F]", ln) for ln in lines)
    if typ == "closed_match":
        lines = normalize_closed(typ, ans).splitlines()
        return len(lines) >= 2 and all(re.fullmatch(r"[A-F]: \S.*", ln) for ln in lines)
    if typ == "open":
        return len(ans) >= 2 and not has_alternative_marker(ans)
    if typ == "essay":
        return ans.startswith("Temat nr") and len(ans.split()) >= 300
    return False


def polish_word_count(text):
    return len(re.findall(r"\w+", text or "", flags=re.UNICODE))


def load_pages(path):
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    out = []
    for row in rows:
        out.append({"page": int(row["page"]), "text": row.get("text") or ""})
    return out


def pages_block(pages):
    return "\n\n".join(f"=== s.{p['page']} ===\n{p['text']}" for p in pages)


def chunk_pages(pages, window=5, step=3):
    chunks = []
    i = 0
    while i < len(pages):
        sl = pages[i:i + window]
        chunks.append(sl)
        if i + window >= len(pages):
            break
        i += step
    return chunks


IMG_RE = re.compile(
    r"\b(ilustracj\w*|fotograf\w*|rycin\w*|malowid\w*|map[ayęą]\w*|plakat\w*|rysunk\w*|zdjęci\w*|monet\w*|plan bitw\w*|tablic\w+ genealogiczn\w*)",
    re.I,
)


def mentions_image(text):
    return bool(IMG_RE.search(text or ""))
