#!/usr/bin/env bash
# Forgehand (1 serwer naraz): Bielik-4.5B-v3.0-Instruct Q4_K_M (kwantyzacja z FP16) na paczkach v2 2024/2025.
# Porównanie z Qwen3.5-4B na zadaniach z historii Polski (warunek routingu T3, H-N23).
set -u
cd /workspace/repo
N=/opt/conda/lib/python3.11/site-packages/nvidia
export LD_LIBRARY_PATH=$N/cuda_runtime/lib:$N/cublas/lib:${LD_LIBRARY_PATH:-}
B=/workspace/llama.cpp/build/bin
M=/scratch/models/bielik45
mkdir -p $M /workspace/logs
BIN=$B/llama-server PY=python L=/workspace/logs
. server/lib_eval.sh
if [ ! -f $M/Bielik-4.5B-v3.0-Instruct-Q4_K_M.gguf ]; then
  python -c "from huggingface_hub import hf_hub_download as d; print(d('speakleash/Bielik-4.5B-v3.0-Instruct-GGUF', 'Bielik-4.5B-v3.0-Instruct-fp16.gguf', local_dir='$M'))"
  $B/llama-quantize $M/Bielik-4.5B-v3.0-Instruct-fp16.gguf $M/Bielik-4.5B-v3.0-Instruct-Q4_K_M.gguf Q4_K_M
  $B/llama-quantize $M/Bielik-4.5B-v3.0-Instruct-fp16.gguf $M/Bielik-4.5B-v3.0-Instruct-Q3_K_M.gguf Q3_K_M
fi
ls -la $M
G="--no-think-kwargs --temperature 0.0 --top-p 1.0 --top-k 1 --parallel 4 --kb-essay data/kb/kompendium.jsonl"
serve 8301 -m $M/Bielik-4.5B-v3.0-Instruct-Q4_K_M.gguf -c 32768 -np 8
run bielik-4.5b-q4__v2 exams/test2024_v2 8301 $G &
run bielik-4.5b-q4__v2 exams/test2025_v2 8301 $G &
wait_runs
stop 8301
serve 8302 -m $M/Bielik-4.5B-v3.0-Instruct-Q3_K_M.gguf -c 32768 -np 8
run bielik-4.5b-q3km__v2 exams/test2024_v2 8302 $G &
run bielik-4.5b-q3km__v2 exams/test2025_v2 8302 $G &
wait_runs
stop 8302
echo FH_BIELIK45_DONE
