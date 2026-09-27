#!/usr/bin/env bash
# Forgehand (1 serwer): jak podnieść Qwen3.5-4B IQ3_XXS (1.95 GB, 36% w konfiguracji T3) do bezpiecznego marginesu nad 35%.
#   A) + RAG z bazy wiedzy (oś czasu, postacie, pojęcia, kompendium; hybryda e5) dla „podaj / rozstrzygnij” (H-N19, H-N21)
#   B) myślenie tylko dla „rozstrzygnij” i otwartych (przy IQ3 myślenie często się zapętla)
set -u
cd /workspace/repo
N=/opt/conda/lib/python3.11/site-packages/nvidia
export LD_LIBRARY_PATH=$N/cuda_runtime/lib:$N/cublas/lib:${LD_LIBRARY_PATH:-}
BIN=/workspace/llama.cpp/build/bin/llama-server PY=python L=/workspace/logs
. server/lib_eval.sh
Q=/scratch/models/unsloth/Qwen3.5-4B-GGUF
python -c "
from huggingface_hub import hf_hub_download as d
for f in ('Qwen3.5-4B-UD-IQ3_XXS.gguf', 'mmproj-F16.gguf'):
    d('unsloth/Qwen3.5-4B-GGUF', f, local_dir='$Q')"
serve 8331 -m $Q/Qwen3.5-4B-UD-IQ3_XXS.gguf --mmproj $Q/mmproj-F16.gguf -ub 4096 -b 4096 -c 65536 -np 8 --reasoning-format deepseek
BASE="--parallel 4 --vision --temperature 1.0 --top-p 0.95 --top-k 20 --max-tokens 8000 --kb-essay data/kb/kompendium.jsonl"
for ds in test2024_v2 test2025_v2; do
  run q35-4b-iq3xxs__t3kbrag exams/$ds 8331 $BASE --think rozstrz,open,podaj,closed --rag none \
    --kb-rag data/kb/kb_all_notes.jsonl --kb-rag-k 3 --kb-dense --rag-types podaj,rozstrz &
  run q35-4b-iq3xxs__t3lessthink exams/$ds 8331 $BASE --think rozstrz,open --rag none &
  wait_runs
done
stop 8331
echo FH_T3_IQ3_DONE
