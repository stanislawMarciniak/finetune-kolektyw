#!/usr/bin/env bash
# Przygotowanie maszyny Nebius tylko do ewaluacji (bez treningu): llama.cpp z CUDA pod lokalną kartę + lekki venv harnessu.
# Potem uruchamia podany skrypt eksperymentu i strażnika bezczynności.
#   bash server/bootstrap_eval_vm.sh server/exp_h100_t3.sh
set -x
EXP=${1:-}
export PATH=/usr/local/cuda/bin:$HOME/.local/bin:$PATH
sudo apt-get update -qq && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq cmake build-essential git ccache rsync python3-dev >/dev/null
command -v uv || curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv --python 3.12 ~/venv-eval
uv pip install --python ~/venv-eval/bin/python openai tantivy huggingface_hub hf_xet
ARCH=$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader | head -1 | tr -d .)
[ -d ~/llama.cpp ] || git clone --depth 1 https://github.com/ggml-org/llama.cpp ~/llama.cpp
cd ~/llama.cpp
cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=$ARCH -DLLAMA_CURL=OFF -DCMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc
cmake --build build -j $(nproc) --target llama-server
~/venv-eval/bin/python - <<'EOF'
import os
from huggingface_hub import hf_hub_download as d
for r, fs in [("unsloth/Qwen3.5-4B-GGUF", ["Qwen3.5-4B-Q4_K_M.gguf", "Qwen3.5-4B-UD-IQ3_XXS.gguf", "Qwen3.5-4B-UD-IQ2_M.gguf", "mmproj-F16.gguf"]),
              ("unsloth/Qwen3.5-2B-GGUF", ["Qwen3.5-2B-Q4_K_M.gguf", "mmproj-F16.gguf"])]:
    for f in fs:
        d(r, f, local_dir=os.path.expanduser(f"~/models/{r}"))
EOF
echo BOOTSTRAP_DONE
cd ~/repo
(IDLE_MIN=${IDLE_MIN:-60} setsid nohup bash server/idle_shutdown.sh > ~/logs/idle_shutdown.log 2>&1 < /dev/null &)
[ -n "$EXP" ] && PY=~/venv-eval/bin/python bash "$EXP"
