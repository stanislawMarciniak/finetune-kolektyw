"""Trening LoRA (train/sft_lora.py) na Modal + konwersja adaptera do GGUF, zapis do wolumenu matura-results.

    modal run --detach overnight/modal_train.py --jobs bielik-1.5b,q35-2b,pllum-12b-base,gemma4-12b-pt
Wynik: /results/train/<nazwa>/{adapter/,train_log.json,lora.gguf,train.log}; pobieranie:
    modal volume get matura-results train/<nazwa>/lora.gguf .
"""

import subprocess
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parents[1]
app = modal.App("matura-train")
results_vol = modal.Volume.from_name("matura-results", create_if_missing=True)
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "build-essential")
    .pip_install("unsloth", "unsloth_zoo", "hf_xet", "sentencepiece", "protobuf")
    .run_commands("git clone --depth 1 https://github.com/ggml-org/llama.cpp /llama.cpp", "pip install -e /llama.cpp/gguf-py")
    .add_local_file(ROOT / "train" / "sft_lora.py", "/repo/train/sft_lora.py")
    .add_local_file(ROOT / "data" / "sft" / "train.jsonl", "/repo/data/sft/train.jsonl")
    .add_local_file(ROOT / "data" / "sft" / "val.jsonl", "/repo/data/sft/val.jsonl")
    .add_local_dir(ROOT / "data" / "sft" / "v2", "/repo/data/sft/v2", ignore=["manifest.jsonl", "STATS.md"])
    .add_local_dir(ROOT / "data" / "sft" / "v2plain", "/repo/data/sft/v2plain", ignore=["manifest.jsonl", "STATS.md", "*_think.jsonl"])
)

JOBS = {
    "bielik-1.5b": ("speakleash/Bielik-1.5B-v3.0-Instruct", ["--epochs", "2", "--rank", "32", "--lr", "2e-4"]),
    "q35-2b": ("Qwen/Qwen3.5-2B", ["--epochs", "2", "--rank", "32", "--lr", "2e-4", "--no-think"]),
    "pllum-12b-base": ("CYFRAGOVPL/PLLuM-12B-base-2512", ["--load-4bit", "--epochs", "2", "--rank", "32", "--batch", "2",
                       "--grad-acc", "8", "--template-from", "CYFRAGOVPL/PLLuM-12B-instruct-2512"]),
    "gemma4-12b-pt": ("google/gemma-4-12B", ["--load-4bit", "--epochs", "2", "--rank", "32", "--batch", "2",
                      "--grad-acc", "8", "--template-from", "google/gemma-4-12B-it"]),
    # faza 2 (dane v2 wierne harnessowi): kontrola T2 bez rozumowania i T3 z zamaskowanym myśleniem (H-N15, H-N22)
    "pllum-v2-think": ("CYFRAGOVPL/PLLuM-12B-base-2512", ["--epochs", "1", "--rank", "32", "--lr", "1e-4", "--batch", "4",
                       "--grad-acc", "4", "--template-from", "CYFRAGOVPL/PLLuM-12B-instruct-2512",
                       "--train", "data/sft/v2/train_think.jsonl", "--val", "data/sft/v2/val_think.jsonl"]),
    "pllum-v2-answer": ("CYFRAGOVPL/PLLuM-12B-base-2512", ["--epochs", "1", "--rank", "32", "--lr", "1e-4", "--batch", "4",
                        "--grad-acc", "4", "--template-from", "CYFRAGOVPL/PLLuM-12B-instruct-2512",
                        "--train", "data/sft/v2/train_answer.jsonl", "--val", "data/sft/v2/val_answer.jsonl"]),
    # runda 2 T2: przepis v1 (2 epoki, bez kontekstu RAG) na wszystkich danych (v1 + E5)
    "pllum-v1recipe-full": ("CYFRAGOVPL/PLLuM-12B-base-2512", ["--epochs", "2", "--rank", "32", "--lr", "1e-4", "--batch", "4",
                            "--grad-acc", "4", "--template-from", "CYFRAGOVPL/PLLuM-12B-instruct-2512",
                            "--train", "data/sft/v2plain/train_answer.jsonl", "--val", "data/sft/v2plain/val_answer.jsonl"]),
    "q35-4b-maskthink": ("Qwen/Qwen3.5-4B", ["--epochs", "1", "--rank", "16", "--lr", "5e-5", "--mask-think",
                         "--train", "data/sft/v2/train_answer.jsonl", "--val", "data/sft/v2/val_answer.jsonl"]),
}


def _train(name: str):
    base, extra = JOBS[name]
    out = Path("/results/train") / name
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "train.log", "w") as log:
        rc = subprocess.run(["python", "train/sft_lora.py", "--model", base, "--out", str(out), *extra],
                            cwd="/repo", stdout=log, stderr=subprocess.STDOUT).returncode
        results_vol.commit()
        if rc == 0:
            subprocess.run(["python", "/llama.cpp/convert_lora_to_gguf.py", str(out / "adapter"), "--base-model-id", base,
                            "--outtype", "f16", "--outfile", str(out / "lora.gguf")], stdout=log, stderr=subprocess.STDOUT)
    results_vol.commit()
    return f"{name}: rc={rc} lora.gguf={'ok' if (out / 'lora.gguf').exists() else 'FAIL'}"


common = dict(image=image, volumes={"/results": results_vol}, secrets=[modal.Secret.from_name("hf-token")])


@app.function(gpu="L40S", timeout=3 * 3600, **common)
def train_big(name: str):
    return _train(name)


@app.function(gpu="L4", timeout=2 * 3600, **common)
def train_small(name: str):
    return _train(name)


@app.function(gpu="H100", timeout=3 * 3600, **common)
def train_h100(name: str):
    return _train(name)


@app.local_entrypoint()
def main(jobs: str):
    pick = lambda n: train_h100 if n.startswith(("pllum-v2", "pllum-v1recipe")) else train_big if ("12b" in n or "4b" in n) else train_small
    calls = [pick(n).spawn(n) for n in jobs.split(",")]
    for c in calls:
        print(c.get())
