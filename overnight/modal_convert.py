"""Konwersja modelu HF -> GGUF (+ kwantyzacja) na Modal, zapis do wolumenu matura-models.

    modal run overnight/modal_convert.py --repo speakleash/Bielik-11B-v3-Base-20250730 --quant Q4_K_M
Wynik: /models/converted/<nazwa>/<nazwa>-<QUANT>.gguf (widoczne dla modal_baselines jako repo "converted/<nazwa>").
Wymaga sekretu Modal `hf-token` (HF_TOKEN) dla modeli z bramką.
"""

import os
import subprocess
from pathlib import Path

import modal

app = modal.App("matura-convert")
models_vol = modal.Volume.from_name("matura-models", create_if_missing=True)
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "build-essential", "cmake", "libcurl4-openssl-dev")
    .run_commands(
        "git clone --depth 1 https://github.com/ggml-org/llama.cpp /llama.cpp",
        "cd /llama.cpp && cmake -B build -DGGML_NATIVE=OFF -DLLAMA_CURL=OFF && cmake --build build --target llama-quantize -j 8",
        "pip install -r /llama.cpp/requirements/requirements-convert_hf_to_gguf.txt",
    )
    .pip_install("huggingface_hub>=0.34", "hf_xet")
    .run_commands("pip install -U transformers")  # wymagania llama.cpp przypinają wersję, która nie czyta tokenizera Gemmy 4
)


@app.function(image=image, volumes={"/models": models_vol}, cpu=8, memory=65536, timeout=4 * 3600,
              secrets=[modal.Secret.from_name("hf-token")])
def convert(repo: str, quant: str = "Q4_K_M", tokenizer_from: str = ""):
    from huggingface_hub import hf_hub_download, snapshot_download
    name = repo.split("/")[-1]
    out_dir = Path("/models/converted") / name
    out_dir.mkdir(parents=True, exist_ok=True)
    final = out_dir / f"{name}-{quant}.gguf"
    if final.exists():
        return str(final)
    src = snapshot_download(repo, local_dir=f"/tmp/{name}", token=os.environ.get("HF_TOKEN"),
                            allow_patterns=["*.json", "*.safetensors", "*.model", "*.txt", "*.jinja", "tokenizer*"])
    if tokenizer_from:  # np. Bielik-11B-v3-Base ma tylko tokenizer.json; ten sam słownik jest w wersji instruct
        for f in ("tokenizer.model",):
            hf_hub_download(tokenizer_from, f, local_dir=src, token=os.environ.get("HF_TOKEN"))
    f16 = f"/tmp/{name}-F16.gguf"
    subprocess.run(["python", "/llama.cpp/convert_hf_to_gguf.py", src, "--outfile", f16, "--outtype", "f16"], check=True)
    subprocess.run(["/llama.cpp/build/bin/llama-quantize", f16, str(final), quant], check=True)
    models_vol.commit()
    return f"{final} {final.stat().st_size / 1e9:.2f} GB"


@app.local_entrypoint()
def main(repo: str, quant: str = "Q4_K_M", tokenizer_from: str = ""):
    print(convert.remote(repo, quant, tokenizer_from))
