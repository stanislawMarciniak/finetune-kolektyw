#!/usr/bin/env bash
# Forgehand (1 serwer): eseje Gemmy QAT (T1). H-N6: kompendium jako kontekst (BM25 / hybryda e5) na 12 tematach;
# H-H8: samoocena i wybór tematu na 3 esejach trzytematowych z 2024–2026, po 3 seedy.
set -u
cd /workspace/repo
N=/opt/conda/lib/python3.11/site-packages/nvidia
export LD_LIBRARY_PATH=$N/cuda_runtime/lib:$N/cublas/lib:${LD_LIBRARY_PATH:-}
BIN=/workspace/llama.cpp/build/bin/llama-server PY=python L=/workspace/logs
. server/lib_eval.sh
G=/scratch/models/google/gemma-4-12B-it-qat-q4_0-gguf
python -c "
from huggingface_hub import hf_hub_download as d
for f in ('gemma-4-12b-it-qat-q4_0.gguf', 'mmproj-gemma-4-12b-it-qat-q4_0.gguf'):
    d('google/gemma-4-12B-it-qat-q4_0-gguf', f, local_dir='$G')"
serve 8311 -m $G/gemma-4-12b-it-qat-q4_0.gguf -c 65536 -np 6 --reasoning-format deepseek
T1="--parallel 6 --rag none --think essay,rozstrz,open,podaj,closed --temperature 1.0 --top-p 0.95 --top-k 64"
run gemma4-qat-essay__base exams/essays12_rag 8311 $T1
run gemma4-qat-essay__kb exams/essays12_rag 8311 $T1 --kb-essay data/kb/kompendium.jsonl
run gemma4-qat-essay__kbdense exams/essays12_rag 8311 $T1 --kb-essay data/kb/kompendium.jsonl --kb-dense
for s in 42 43 44; do
  run gemma4-qat-essay3__s$s exams/essays3_v2 8311 $T1 --seed $s &
  run gemma4-qat-essay3-choose__s$s exams/essays3_v2 8311 $T1 --seed $s --essay-choose &
  wait_runs
done
stop 8311
echo FH_T1_ESSAY_DONE
