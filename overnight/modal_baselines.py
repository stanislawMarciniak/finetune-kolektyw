"""Nocne przebiegi bazowe na Modal: llama.cpp (llama-server, GGUF) + prompt organizatorów z benchmarku.

Weryfikuje m.in. H-M1, H-M2, H-M3, H-M4, H-M6, H-M8, H-I1, H-I2, H-E4 (raport 07).

Uruchomienie (aplikacja wdrożona, zadania działają niezależnie od laptopa):
    modal deploy overnight/modal_baselines.py
    python overnight/launch_modal.py            # spawn orkiestratora
Test dymny:
    modal run overnight/modal_baselines.py::smoke
Wyniki:
    modal volume get matura-results / results/
"""

import base64
import json
import re
import mimetypes
import os
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parents[1]
app = modal.App("matura-baselines")
models_vol = modal.Volume.from_name("matura-models", create_if_missing=True)
results_vol = modal.Volume.from_name("matura-results", create_if_missing=True)

image = (
    modal.Image.from_registry("ghcr.io/ggml-org/llama.cpp:server-cuda", add_python="3.11")
    .entrypoint([])
    .pip_install("openai>=1.40", "huggingface_hub>=0.34", "hf_xet", "requests")
    .add_local_dir(ROOT / "eval" / "data", "/repo/eval/data")
    .add_local_dir(ROOT / "assets" / "benchmark-2023" / "vision-pages", "/repo/assets/benchmark-2023/vision-pages")
    .add_local_dir(ROOT / "results", "/repo/results", ignore=["review/**", "grades/**"])
)

SYSTEM_TEXT = ("Rozwiąż zadanie z historii po polsku. Otrzymujesz tekst źródeł, a obrazy zastąpiono opisami. "
               "Wykorzystaj źródła i własną wiedzę zgodnie z poleceniem. Udziel tylko odpowiedzi na podane zadanie. "
               "Nie dopisuj innych zadań. Nie masz dostępu do narzędzi ani internetu.")
SYSTEM_IMG = ("Rozwiąż zadanie z historii po polsku. Otrzymujesz obrazy oryginalnych stron arkusza ze źródłami i poleceniami. "
              "Wykorzystaj widoczne źródła i własną wiedzę zgodnie z poleceniem. Udziel tylko odpowiedzi na wskazane zadanie. "
              "Inne zadania widoczne na tych samych stronach pomiń. Nie masz dostępu do narzędzi ani internetu.")
SYSTEM_SPLIT = ("Rozwiąż zadanie z historii po polsku. Otrzymujesz polecenie, teksty źródeł oraz osobno obrazy źródeł (jeśli są). "
                "Wykorzystaj źródła i własną wiedzę zgodnie z poleceniem. Udziel tylko odpowiedzi na podane zadanie. "
                "Nie masz dostępu do narzędzi ani internetu.")

V1_COMMON = ("Jesteś zdającym maturę z historii (poziom rozszerzony). Odpowiadaj po polsku, zwięźle i jednoznacznie. "
             "Podaj tylko jedną odpowiedź – nie podawaj alternatyw ani wariantów do wyboru i nie zmieniaj zdania w trakcie. "
             "Nie powtarzaj polecenia. Jeśli polecenie zawiera etykiety (np. „Rozstrzygnięcie:”, „Uzasadnienie:”), użyj ich. "
             "Gdy polecenie wymaga odwołania do źródła, wskaż konkretną informację ze źródła. Nie masz dostępu do internetu.")
V1_TYPE = {
    "closed_choice": "To zadanie zamknięte. Podaj wyłącznie literę poprawnej odpowiedzi (np. „C”). Jeśli zadanie ma kilka części, "
                     "podaj w osobnych wierszach numer części i literę (np. „1. B”).",
    "closed_tf": "Dla każdego stwierdzenia podaj w osobnym wierszu jego numer i literę P (prawda) albo F (fałsz), np. „1. P”. Nic więcej.",
    "closed_match": "Podaj przyporządkowanie w osobnych wierszach w formacie „A – …”, „B – …”. Nic więcej.",
    "open": "Odpowiedz w 1–3 zdaniach. Podawaj konkretne nazwy, nazwiska, daty i pojęcia historyczne. Nie dodawaj informacji, których nie jesteś pewien.",
    "essay": "Wybierz JEDEN temat i zacznij od „Temat nr X”. Napisz wypracowanie liczące 450–650 słów: wstęp z jednoznacznym stanowiskiem "
             "wobec tezy; trzy akapity – po jednym na każdy element wskazany w temacie – z konkretnymi faktami (daty, postacie, pojęcia) "
             "i wnioskiem wiążącym akapit z tezą; zakończenie wynikające z argumentów. Nie zmyślaj faktów – jeśli nie jesteś pewien daty, pomiń ją.",
}
RAG_HEAD = "Materiały pomocnicze (fragmenty encyklopedii; mogą być częściowo nieistotne – korzystaj tylko z pasujących):"

QWEN_THINK = {"temperature": 1.0, "top_p": 0.95, "top_k": 20, "min_p": 0.0}
QWEN_FAST = {"temperature": 0.7, "top_p": 0.8, "top_k": 20, "min_p": 0.0}
GEMMA = {"temperature": 1.0, "top_p": 0.95, "top_k": 64}
GREEDY = {"temperature": 0.0}

U = "unsloth"
MODELS = {
    # --- T3 / małe (L4) ---
    "q35-0.8b-q4": dict(repo=f"{U}/Qwen3.5-0.8B-GGUF", file="Qwen3.5-0.8B-Q4_K_M.gguf", mmproj="mmproj-F16.gguf", gpu="L4", think=False, samp=QWEN_FAST),
    "q35-0.8b-q8": dict(repo=f"{U}/Qwen3.5-0.8B-GGUF", file="Qwen3.5-0.8B-Q8_0.gguf", gpu="L4", think=False, samp=QWEN_FAST),
    "q35-2b-q4": dict(repo=f"{U}/Qwen3.5-2B-GGUF", file="Qwen3.5-2B-Q4_K_M.gguf", mmproj="mmproj-F16.gguf", gpu="L4", think=False, samp=QWEN_FAST),
    "q35-2b-q4-think": dict(repo=f"{U}/Qwen3.5-2B-GGUF", file="Qwen3.5-2B-Q4_K_M.gguf", gpu="L4", think=True, samp=QWEN_THINK),
    "q35-2b-q8": dict(repo=f"{U}/Qwen3.5-2B-GGUF", file="Qwen3.5-2B-Q8_0.gguf", gpu="L4", think=False, samp=QWEN_FAST),
    "q35-4b-q4": dict(repo=f"{U}/Qwen3.5-4B-GGUF", file="Qwen3.5-4B-Q4_K_M.gguf", mmproj="mmproj-F16.gguf", gpu="L4", think=False, samp=QWEN_FAST),
    "q35-4b-q4-think": dict(repo=f"{U}/Qwen3.5-4B-GGUF", file="Qwen3.5-4B-Q4_K_M.gguf", gpu="L4", think=True, samp=QWEN_THINK),
    "bielik-1.5b-q4": dict(repo="second-state/Bielik-1.5B-v3.0-Instruct-GGUF", file="Bielik-1.5B-v3.0-Instruct-Q4_K_M.gguf", gpu="L4", think=None, samp=GREEDY),
    "bielik-1.5b-q8": dict(repo="second-state/Bielik-1.5B-v3.0-Instruct-GGUF", file="Bielik-1.5B-v3.0-Instruct-Q8_0.gguf", gpu="L4", think=None, samp=GREEDY),
    # --- T2 / goły -Base ---
    "q35-2b-base-q4": dict(repo="mradermacher/Qwen3.5-2B-Base-GGUF", file="Qwen3.5-2B-Base.Q4_K_M.gguf", gpu="L4", think=None, samp=GREEDY),
    "q35-0.8b-base-q8": dict(repo="ggml-org/Qwen3.5-0.8B-Base-GGUF", file="Qwen3.5-0.8B-Base-Q8_0.gguf", gpu="L4", think=None, samp=GREEDY),
    "pllum-12b-base-q4": dict(repo="mradermacher/PLLuM-12B-base-2512-GGUF", file="PLLuM-12B-base-2512.Q4_K_M.gguf", gpu="L40S", think=None, samp=GREEDY),
    # --- T1 / duże (L40S) ---
    "gemma4-12b-qat": dict(repo="google/gemma-4-12B-it-qat-q4_0-gguf", file="gemma-4-12b-it-qat-q4_0.gguf", mmproj="mmproj-gemma-4-12b-it-qat-q4_0.gguf", gpu="L40S", think=True, samp=GEMMA),
    "gemma4-12b-qat-nothink": dict(repo="google/gemma-4-12B-it-qat-q4_0-gguf", file="gemma-4-12b-it-qat-q4_0.gguf", gpu="L40S", think=False, samp=GEMMA),
    "q35-9b-q5": dict(repo=f"{U}/Qwen3.5-9B-GGUF", file="Qwen3.5-9B-Q5_K_M.gguf", mmproj="mmproj-F16.gguf", gpu="L40S", think=True, samp=QWEN_THINK),
    "bielik-11b-v3-q5": dict(repo="bartowski/speakleash_Bielik-11B-v3.0-Instruct-GGUF", file="speakleash_Bielik-11B-v3.0-Instruct-Q5_K_M.gguf", gpu="L40S", think=None, samp=GREEDY),
    "pllum-12b-q4": dict(repo="mradermacher/PLLuM-12B-instruct-2512-GGUF", file="PLLuM-12B-instruct-2512.Q4_K_M.gguf", gpu="L40S", think=None, samp=GREEDY),
    "bielik-pl-11b-q5": dict(repo="macszym/Bielik-PL-11B-v3.0-Instruct-GGUF", file="Bielik-PL-11B-v3.0-Instruct.Q5_K_M.gguf", gpu="L40S", think=None, samp=GREEDY),
    "q35-4b-q4-think-img": dict(repo=f"{U}/Qwen3.5-4B-GGUF", file="Qwen3.5-4B-Q4_K_M.gguf", mmproj="mmproj-F16.gguf", gpu="L4", think=True, samp=QWEN_THINK),
    # --- T2 / gołe bazy ---
    "bielik-1.5b-base-q8": dict(repo="mradermacher/Bielik-1.5B-v3-ungated-GGUF", file="Bielik-1.5B-v3-ungated.Q8_0.gguf", gpu="L4", think=None, samp=GREEDY),
    "bielik-4.5b-base-q5": dict(repo="mradermacher/Bielik-4.5B-v3-Base-ungated-GGUF", file="Bielik-4.5B-v3-Base-ungated.Q5_K_M.gguf", gpu="L4", think=None, samp=GREEDY),
    "bielik-11b-base-q5": dict(repo="converted/Bielik-11B-v3-Base-20250730", file="Bielik-11B-v3-Base-20250730-Q5_K_M.gguf", gpu="L40S", think=None, samp=GREEDY),
    "gemma4-12b-pt-q4": dict(repo="converted/gemma-4-12B", file="gemma-4-12B-Q4_K_M.gguf", gpu="L40S", think=None, samp=GREEDY),
}

# (model, zbiór, seed)
RUNS = [
    *[(m, "dev2023_text", 42) for m in [
        "q35-0.8b-q4", "q35-0.8b-q8", "q35-2b-q4", "q35-2b-q4-think", "q35-2b-q8", "q35-4b-q4", "q35-4b-q4-think",
        "bielik-1.5b-q4", "bielik-1.5b-q8", "q35-2b-base-q4", "q35-0.8b-base-q8", "pllum-12b-base-q4",
        "gemma4-12b-qat", "gemma4-12b-qat-nothink", "q35-9b-q5", "bielik-11b-v3-q5", "pllum-12b-q4"]],
    *[(m, "dev2023_img", 42) for m in ["gemma4-12b-qat", "q35-9b-q5", "q35-2b-q4", "q35-0.8b-q4", "q35-4b-q4"]],
    # powtórzenia do oszacowania szumu (H-E4)
    ("q35-2b-q4", "dev2023_text", 43), ("q35-2b-q4", "dev2023_text", 44), ("gemma4-12b-qat", "dev2023_text", 43),
]


def model_paths(cfg):
    base = Path("/models") / cfg["repo"]
    return base / cfg["file"], (base / cfg["mmproj"]) if cfg.get("mmproj") else None


@app.function(image=image, volumes={"/models": models_vol}, timeout=3 * 3600, cpu=4)
def prefetch(names: list[str]):
    from huggingface_hub import hf_hub_download
    os.environ["HF_XET_HIGH_PERFORMANCE"] = "1"
    for n in names:
        cfg = MODELS[n]
        if cfg["repo"].startswith("converted/"):  # powstały w modal_convert.py
            continue
        for f in [cfg["file"], cfg.get("mmproj")]:
            if not f:
                continue
            dest = Path("/models") / cfg["repo"] / f
            if dest.exists():
                continue
            t0 = time.time()
            hf_hub_download(cfg["repo"], f, local_dir=str(Path("/models") / cfg["repo"]))
            print(f"downloaded {cfg['repo']}/{f} {dest.stat().st_size / 1e9:.2f} GB in {time.time() - t0:.0f}s", flush=True)
        models_vol.commit()


def start_server(model, mmproj, think, ctx=73728, parallel=3):
    binary = shutil.which("llama-server") or "/app/llama-server"
    base = [binary, "-m", str(model), "--host", "127.0.0.1", "--port", "8080", "-ngl", "999",
            "-c", str(ctx), "-np", str(parallel), "--jinja", "--reasoning-format", "deepseek"]
    if mmproj:
        # obrazy Gemmy 4 używają atencji niekauzalnej: cały fragment obrazu musi zmieścić się w jednym ubatchu
        base += ["--mmproj", str(mmproj), "-ub", "4096", "-b", "4096"]
    if think is False:
        base += ["--reasoning-budget", "0"]
    import requests
    for extra in (["--kv-unified"], []):
        cmd = base + extra
        log = open("/tmp/server.log", "w")
        proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
        t0 = time.time()
        while time.time() - t0 < 1200:
            if proc.poll() is not None:
                break
            try:
                if requests.get("http://127.0.0.1:8080/health", timeout=2).status_code == 200:
                    return proc, cmd
            except requests.RequestException:
                pass
            time.sleep(2)
        print("server failed with", extra, open("/tmp/server.log").read()[-3000:], flush=True)
        proc.kill()
    raise RuntimeError("llama-server did not start")


def image_part(path):
    mime = mimetypes.guess_type(path)[0] or "image/png"
    data = base64.b64encode(Path(path).read_bytes()).decode()
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{data}"}}


def rag_block(item, topic=None):
    rag = item.get("rag") or []
    if item.get("type") == "essay":
        chunks = [p for t in rag if topic is None or t["topic"] == topic for p in t["passages"]][:6]
    else:
        chunks = rag[:4]
    if not chunks:
        return ""
    return RAG_HEAD + "\n" + "\n".join(f"- {c['title']}: {c['text']}" for c in chunks) + "\n\n"


def build_messages(item, dataset, use_images=True, variant="base"):
    msgs = _build_base(item, dataset, use_images)
    if variant == "base":
        return msgs
    if variant.startswith("v1"):
        qtype = item.get("type", "open")
        msgs[0]["content"] = V1_COMMON + "\n" + V1_TYPE.get(qtype, V1_TYPE["open"])
    if "rag" in variant:
        block = rag_block(item)
        if block:
            if isinstance(msgs[1]["content"], str):
                msgs[1]["content"] = block + msgs[1]["content"]
            else:
                msgs[1]["content"][-1]["text"] = block + msgs[1]["content"][-1]["text"]
    return msgs


NO_LABELS = " Pisz ciągłą prozą: bez nagłówków, bez etykiet typu „Wstęp:”, „Stanowisko:”, bez wypunktowań i bez pogrubień."


def clean_section(text):
    text = re.sub(r"(?m)^\s*\**\s*(Wstęp|Zakończenie|Rozwinięcie|Akapit[^:\n]*|Stanowisko|Teza|Temat[^:\n]*)\s*\**\s*:?\s*\**\s*$", "", text)
    text = re.sub(r"(?i)\**(Stanowisko|Teza|Wstęp|Zakończenie)\**\s*:\s*", "", text)
    text = re.sub(r"[*#]+", "", text)
    return re.sub(r"\n{2,}", "\n", text).strip()


def essay_sectioned(client, item, gen):
    """Esej akapit po akapicie: plan (JSON) -> 3 akapity -> wstęp i zakończenie -> złożenie (H-H14)."""
    topics = item["question"]
    plan_prompt = (f"{topics}\n\n" + rag_block(item) +
                   "Wybierz temat, do którego znasz najwięcej konkretnych faktów. Zwróć JSON: "
                   '{"temat": <numer 1-3>, "stanowisko": "<jednozdaniowa teza: zgadzam się / nie zgadzam się / częściowo, z uzasadnieniem>", '
                   '"elementy": [{"nazwa": "<element tematu, np. władca lub aspekt>", "fakty": ["<konkretny fakt z datą lub pojęciem>", "...", "..."]}, ... 3 elementy]}')
    plan_raw = gen([{"role": "system", "content": V1_COMMON}, {"role": "user", "content": plan_prompt}], 1500, json_mode=True)
    try:
        plan = json.loads(plan_raw)
        elems = plan["elementy"][:3]
        topic_no = int(plan.get("temat", 1))
        thesis = plan.get("stanowisko", "")
    except Exception:
        return None, plan_raw
    topic_line = next((l for l in topics.splitlines() if l.strip().startswith(f"{topic_no}.")), "")
    paras = []
    for e in elems:
        facts = "; ".join(e.get("fakty", [])[:5])
        p = gen([{"role": "system", "content": V1_COMMON},
                 {"role": "user", "content": f"Temat wypracowania: {topic_line}\nStanowisko: {thesis}\n\n" + rag_block(item, topic_no) +
                  f"Napisz JEDEN akapit rozwinięcia (170–220 słów) dotyczący wyłącznie elementu: {e.get('nazwa', '')}. Wykorzystaj fakty: {facts}. "
                  "Zacznij od zdania wiążącego akapit z tezą, podaj konkretne fakty (daty, postacie, pojęcia), zakończ wnioskiem („Świadczy to o…”)."
                  + NO_LABELS + " Zwróć sam akapit."}], 900)
        paras.append(clean_section(p))
    body = "\n\n".join(paras)
    intro = gen([{"role": "system", "content": V1_COMMON},
                 {"role": "user", "content": f"Temat: {topic_line}\nStanowisko: {thesis}\nRozwinięcie:\n{body}\n\n"
                  "Napisz wstęp wypracowania (80–110 słów) wprowadzający w problem i kończący się jednoznaczną tezą." + NO_LABELS + " Zwróć sam wstęp."}], 500)
    concl = gen([{"role": "system", "content": V1_COMMON},
                 {"role": "user", "content": f"Temat: {topic_line}\nStanowisko: {thesis}\nRozwinięcie:\n{body}\n\n"
                  "Napisz zakończenie (80–110 słów), które podsumowuje trzy argumenty z rozwinięcia i potwierdza tezę." + NO_LABELS + " Zwróć samo zakończenie."}], 500)
    essay = f"{clean_section(intro)}\n\n{body}\n\n{clean_section(concl)}"
    if len(essay.split()) < 330:  # próg 300 słów decyduje o punktach za spójność
        extra = gen([{"role": "system", "content": V1_COMMON},
                     {"role": "user", "content": f"Temat: {topic_line}\nStanowisko: {thesis}\nWypracowanie:\n{essay}\n\n"
                      "Napisz jeszcze jeden akapit rozwinięcia (150–200 słów) z dodatkowymi konkretnymi faktami wspierającymi tezę." + NO_LABELS}], 800)
        essay = f"{clean_section(intro)}\n\n{body}\n\n{clean_section(extra)}\n\n{clean_section(concl)}"
    return f"Temat nr {topic_no}\n\n{essay}", plan_raw


def _build_base(item, dataset, use_images=True):
    head = f"Zadanie {item['id']} ({item['max_points']} pkt)"
    if item.get("images") and not use_images:
        text = f"{head}\n\n{item.get('sources', '')}\n\n{item['question']}"
        return [{"role": "system", "content": SYSTEM_SPLIT}, {"role": "user", "content": text}]
    if item.get("images"):
        system = SYSTEM_IMG if dataset.endswith("_img") else SYSTEM_SPLIT
        text = f"{head}\n\n{item['sources']}\n\n{item['question']}" if item.get("sources") else f"{head}\n\n{item['question']}"
        content = [image_part("/repo/" + p) for p in item["images"]] + [{"type": "text", "text": text}]
    else:
        system = SYSTEM_TEXT
        content = f"{head}\n\n{item.get('sources', '')}\n\n{item['question']}"
    return [{"role": "system", "content": system}, {"role": "user", "content": content}]


def evaluate(name, dataset, seed, limit=None, variant="base"):
    from openai import OpenAI
    cfg = MODELS[name]
    model, mmproj = model_paths(cfg)
    items = [json.loads(l) for l in open(f"/repo/eval/data/{dataset}.jsonl")][:limit]
    if variant.endswith("sect"):  # wariant eseju: pozostałe zadania są identyczne jak w v1rag
        items = [it for it in items if it.get("type") == "essay"]
    has_images = any(it.get("images") for it in items)
    if dataset.endswith("_img") and not mmproj:
        raise ValueError(f"{name} has no mmproj for {dataset}")
    use_images = bool(mmproj) and has_images  # modele tekstowe dostają sam tekst, jak na finale
    t_load = time.time()
    proc, cmd = start_server(model, mmproj if use_images else None, cfg["think"])
    load_s = time.time() - t_load
    client = OpenAI(base_url="http://127.0.0.1:8080/v1", api_key="x", timeout=1800)
    samp = dict(cfg["samp"])

    def solve(item):
        essay = item.get("type") == "essay"
        if cfg["think"]:
            max_tokens = 20000 if essay else 10000
        else:
            max_tokens = 4096 if essay else 2048
        extra = {"seed": seed}
        for k in ("top_k", "min_p"):
            if k in samp:
                extra[k] = samp[k]
        if cfg["think"] is not None:
            extra["chat_template_kwargs"] = {"enable_thinking": bool(cfg["think"])}
        t0 = time.time()
        if essay and variant.endswith("sect"):
            def gen(messages, mt, json_mode=False):
                kw = {"response_format": {"type": "json_object"}} if json_mode else {}
                ex = dict(extra)
                ex["chat_template_kwargs"] = {"enable_thinking": False} if cfg["think"] is not None else ex.get("chat_template_kwargs")
                if ex.get("chat_template_kwargs") is None:
                    ex.pop("chat_template_kwargs", None)
                rr = client.chat.completions.create(model="m", messages=messages, max_tokens=mt,
                                                    temperature=min(samp.get("temperature", 0.0), 0.7),
                                                    top_p=samp.get("top_p", 1.0), extra_body=ex, **kw)
                return rr.choices[0].message.content or ""
            try:
                text, plan = essay_sectioned(client, item, gen)
                return {"id": item["id"], "type": "essay", "max_points": item["max_points"], "answer": text or "",
                        "reasoning": plan, "finish_reason": "stop" if text else "plan_failed",
                        "seconds": round(time.time() - t0, 2)}
            except Exception as e:
                return {"id": item["id"], "type": "essay", "max_points": item["max_points"], "answer": "",
                        "error": repr(e)[:2000], "seconds": round(time.time() - t0, 2)}
        try:
            r = client.chat.completions.create(
                model="m", messages=build_messages(item, dataset, use_images, variant), max_tokens=max_tokens,
                temperature=samp.get("temperature", 0.0), top_p=samp.get("top_p", 1.0), extra_body=extra)
            msg = r.choices[0].message
            return {"id": item["id"], "type": item.get("type"), "max_points": item["max_points"],
                    "answer": msg.content or "", "reasoning": getattr(msg, "reasoning_content", None) or "",
                    "finish_reason": r.choices[0].finish_reason,
                    "prompt_tokens": r.usage.prompt_tokens, "completion_tokens": r.usage.completion_tokens,
                    "seconds": round(time.time() - t0, 2)}
        except Exception as e:
            return {"id": item["id"], "type": item.get("type"), "max_points": item["max_points"],
                    "answer": "", "error": repr(e)[:2000], "seconds": round(time.time() - t0, 2)}

    t0 = time.time()
    with ThreadPoolExecutor(3) as ex:
        out = list(ex.map(solve, items))
    wall = time.time() - t0
    version = subprocess.run([cmd[0], "--version"], capture_output=True, text=True)
    alive = proc.poll() is None
    proc.kill()
    server_tail = open("/tmp/server.log", errors="replace").read()[-4000:]
    run = f"{name}__s{seed}" if variant == "base" else f"{name}__{variant}__s{seed}"
    dest = Path("/results") / dataset
    dest.mkdir(parents=True, exist_ok=True)
    with open(dest / f"{run}.jsonl", "w") as f:
        for o in out:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
    meta = {"run": run, "model": name, "dataset": dataset, "seed": seed, "variant": variant, "cfg": cfg, "server_cmd": cmd,
            "used_images": use_images, "server_alive_at_end": alive,
            "server_log_tail": server_tail if any("error" in o for o in out) else "",
            "llama_version": (version.stdout + version.stderr)[-500:], "load_seconds": round(load_s, 1),
            "wall_seconds": round(wall, 1), "n": len(out), "errors": sum("error" in o for o in out),
            "truncated": sum(o.get("finish_reason") == "length" for o in out),
            "completion_tokens": sum(o.get("completion_tokens", 0) for o in out)}
    (dest / f"{run}.meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    results_vol.commit()
    print(json.dumps(meta, ensure_ascii=False), flush=True)
    return meta


GPU_KW = dict(image=image, volumes={"/models": models_vol, "/results": results_vol}, timeout=4 * 3600)

SELECT_SYS = ("Jesteś doświadczonym egzaminatorem matury z historii (CKE). Porównujesz dwie odpowiedzi na to samo zadanie. "
              "Wybierz tę, która dostałaby więcej punktów według zasad CKE: poprawność merytoryczna, dokładne wykonanie polecenia, "
              "odwołanie do źródeł, gdy jest wymagane, brak sprzeczności i brak wariantów do wyboru. "
              "W eseju liczą się też konkretne fakty dla trzech elementów tematu, brak błędów merytorycznych i spójność. "
              "Na końcu napisz w osobnej linii tylko: WYBÓR: A albo WYBÓR: B.")


@app.function(gpu="L40S", **GPU_KW)
def select_eval(dataset: str, run_a: str, run_b: str, judge: str = "gemma4-12b-qat", seed: int = 42):
    """Selektor zespołu (H-H9): sędzia lokalny wybiera lepszą z dwóch odpowiedzi; ocena wyboru z istniejących ocen."""
    import random
    from openai import OpenAI
    cfg = MODELS[judge]
    model, mmproj = model_paths(cfg)
    items = [json.loads(l) for l in open(f"/repo/eval/data/{dataset}.jsonl")]
    ans = {r: {json.loads(l)["id"]: json.loads(l).get("answer", "") for l in open(f"/repo/results/{dataset}/{r}.jsonl")}
           for r in (run_a, run_b)}
    proc, cmd = start_server(model, mmproj, cfg["think"])
    client = OpenAI(base_url="http://127.0.0.1:8080/v1", api_key="x", timeout=1800)
    rng = random.Random(seed)

    def pick(item):
        a, b = ans[run_a].get(item["id"], ""), ans[run_b].get(item["id"], "")
        a, b = re.sub(r"<think>.*?</think>", "", a, flags=re.S).strip(), re.sub(r"<think>.*?</think>", "", b, flags=re.S).strip()
        if not a or not b or a == b:
            return {"id": item["id"], "choice": run_a if a else run_b, "note": "trivial"}
        swap = rng.random() < 0.5
        first, second = (b, a) if swap else (a, b)
        base = _build_base(item, dataset, use_images=bool(mmproj))
        tail = f"\n\n=== ODPOWIEDŹ A ===\n{first[:6000]}\n\n=== ODPOWIEDŹ B ===\n{second[:6000]}\n\nKtóra odpowiedź jest lepsza?"
        user = base[1]["content"]
        if isinstance(user, str):
            user = user + tail
        else:
            user = user[:-1] + [{"type": "text", "text": user[-1]["text"] + tail}]
        try:
            r = client.chat.completions.create(model="m", messages=[{"role": "system", "content": SELECT_SYS}, {"role": "user", "content": user}],
                                               max_tokens=6000, temperature=0.6, top_p=0.95,
                                               extra_body={"top_k": 64, "seed": seed, "chat_template_kwargs": {"enable_thinking": True}})
            text = r.choices[0].message.content or ""
        except Exception as e:
            return {"id": item["id"], "choice": run_a, "note": f"error {e!r}"[:300]}
        m = re.findall(r"WYB[ÓO]R:\s*\**\s*([AB])", text)
        letter = m[-1] if m else "A"
        chosen_first = letter == "A"
        choice = (run_b if swap else run_a) if chosen_first else (run_a if swap else run_b)
        return {"id": item["id"], "choice": choice, "raw": text[-300:]}

    with ThreadPoolExecutor(3) as ex:
        out = list(ex.map(pick, items))
    proc.kill()
    dest = Path("/results/select") / dataset
    dest.mkdir(parents=True, exist_ok=True)
    name = f"{judge}__{run_a}__VS__{run_b}"
    with open(dest / f"{name}.jsonl", "w") as f:
        for o in out:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
    results_vol.commit()
    return {"dataset": dataset, "name": name, "n": len(out)}


@app.local_entrypoint()
def wave_select():
    calls = [select_eval.spawn(d, "gemma4-12b-qat__s42", "bielik-11b-v3-q5__s42")
             for d in ("test2024_split", "test2025_split", "test2026_split")]
    print([c.get() for c in calls])


@app.function(gpu="L4", **GPU_KW)
def run_l4(name: str, dataset: str, seed: int = 42, limit: int | None = None, variant: str = "base"):
    return evaluate(name, dataset, seed, limit, variant)


@app.function(gpu="L40S", **GPU_KW)
def run_l40s(name: str, dataset: str, seed: int = 42, limit: int | None = None, variant: str = "base"):
    return evaluate(name, dataset, seed, limit, variant)


@app.function(image=image, timeout=12 * 3600, volumes={"/results": results_vol})
def orchestrate(runs: list | None = None, tag: str = "wave1"):
    runs = runs or RUNS
    prefetch.remote(sorted({r[0] for r in runs}))
    calls = []
    for r in runs:
        name, dataset, seed = r[0], r[1], r[2]
        variant = r[3] if len(r) > 3 else "base"
        fn = run_l4 if MODELS[name]["gpu"] == "L4" else run_l40s
        calls.append((name, dataset, seed, fn.spawn(name, dataset, seed, None, variant)))
    summary = []
    for name, dataset, seed, c in calls:
        try:
            summary.append(c.get())
        except Exception as e:
            summary.append({"run": f"{name}__s{seed}", "dataset": dataset, "error": repr(e)[:1000]})
            print("FAILED", name, dataset, seed, repr(e)[:500], flush=True)
    Path(f"/results/summary-{tag}.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    results_vol.commit()
    return summary


@app.function(image=image)
def list_data():
    import glob
    return sorted(glob.glob("/repo/eval/data/*")) + sorted(glob.glob("/repo/eval/data/img/*/*"))[:5]


@app.local_entrypoint()
def debug():
    print(list_data.remote())


WAVE3 = [("gemma4-12b-qat", d, 42) for d in ("dev2023_img", "test2024_split", "test2025_split", "test2026_split")]


W4_MODELS = ["gemma4-12b-qat", "bielik-11b-v3-q5", "q35-4b-q4", "q35-2b-q4", "bielik-1.5b-q8"]
WAVE4 = (
    [(m, d, 42, "v1") for m in W4_MODELS for d in ("test2024_split", "test2025_split")]
    + [(m, d, 42, "v1rag") for m in W4_MODELS for d in ("test2024_split_rag", "test2025_split_rag")]
    + [(m, "essays12_rag", 42, v) for m in W4_MODELS for v in ("v1rag", "v1sect")]
)


WAVE5 = (
    # czysty test RAG: prompt organizatorów + kontekst (H-H2), bez instrukcji v1, które szkodziły
    [(m, d, 42, "rag") for m in W4_MODELS for d in ("test2024_split_rag", "test2025_split_rag")]
    # Qwen3.5-4B z myśleniem i obrazami, z RAG i bez (T3)
    + [("q35-4b-q4-think-img", d, 42) for d in ("test2024_split", "test2025_split")]
    + [("q35-4b-q4-think-img", d, 42, "rag") for d in ("test2024_split_rag", "test2025_split_rag")]
    # Bielik-PL-11B (H-M11) i gołe bazy Bielika (T2)
    + [(m, d, 42) for m in ("bielik-pl-11b-q5", "bielik-1.5b-base-q8", "bielik-4.5b-base-q5") for d in ("test2024_split", "test2025_split")]
)
WAVE5B = [(m, d, 42) for m in ("bielik-11b-base-q5", "gemma4-12b-pt-q4") for d in ("test2024_split", "test2025_split")]


@app.local_entrypoint()
def wave5():
    print(orchestrate.remote(WAVE5, "wave5"))


@app.local_entrypoint()
def wave5b():
    """Gołe bazy przekonwertowane w modal_convert.py (uruchamiać po zakończeniu konwersji)."""
    print(orchestrate.remote(WAVE5B, "wave5b"))


@app.local_entrypoint()
def wave4():
    """Harness v1 (format per typ), v1 + RAG, esej jednoprzebiegowy vs akapit po akapicie (H-H1, H-H2, H-H14)."""
    print(orchestrate.remote(WAVE4, "wave4"))


@app.local_entrypoint()
def smoke_v1():
    prefetch.remote(["q35-2b-q4"])
    print(run_l4.remote("q35-2b-q4", "essays12_rag", 42, 1, "v1sect"))
    print(run_l4.remote("q35-2b-q4", "test2024_split_rag", 42, 3, "v1rag"))


@app.local_entrypoint()
def wave3():
    """Ponowienie przebiegów obrazowych Gemmy 4 po poprawce -ub/-b (aplikacja tymczasowa z aktualnym kodem)."""
    print(orchestrate.remote(WAVE3, "wave3"))


@app.local_entrypoint()
def debug_gemma():
    m = run_l40s.remote("gemma4-12b-qat", "dev2023_img", 42, 1)
    print({k: m.get(k) for k in ("errors", "wall_seconds", "server_alive_at_end")})
    print(m.get("server_log_tail", "")[-3500:])


@app.local_entrypoint()
def smoke():
    prefetch.remote(["q35-0.8b-q4"])
    print(run_l4.remote("q35-0.8b-q4", "dev2023_img", 42, 2))
    print(run_l4.remote("q35-0.8b-q4", "dev2023_text", 42, 2))
