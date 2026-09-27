#!/usr/bin/env bash
# T3: potwierdzenie Qwen3.5-4B Q3_K_M (2.29 GB; 48.7% na 2024+2025): drugi seed + 2026; oraz Q3_K_S (2.11 GB).
set -u
cd ~/repo
PY=$HOME/venv-eval/bin/python
. server/lib_eval.sh
Q=$HOME/models/unsloth/Qwen3.5-4B-GGUF
$PY -c "
import os
from huggingface_hub import hf_hub_download as d
d('unsloth/Qwen3.5-4B-GGUF', 'Qwen3.5-4B-Q3_K_S.gguf', local_dir=os.path.expanduser('~/models/unsloth/Qwen3.5-4B-GGUF'))"
SRV="-ub 4096 -b 4096 -c 98304 -np 8 --reasoning-format deepseek"
T3="--parallel 4 --rag none --vision --think rozstrz,open,podaj,closed --temperature 1.0 --top-p 0.95 --top-k 20 --max-tokens 8000 --kb-essay data/kb/kompendium.jsonl"
serve 8151 -m $Q/Qwen3.5-4B-Q3_K_M.gguf --mmproj $Q/mmproj-F16.gguf $SRV
serve 8152 -m $Q/Qwen3.5-4B-Q3_K_S.gguf --mmproj $Q/mmproj-F16.gguf $SRV
run q35-4b-q3km__t3cfg exams/test2026_v2 8151 $T3 &
run q35-4b-q3ks__t3cfg exams/test2024_v2 8152 $T3 &
run q35-4b-q3ks__t3cfg exams/test2025_v2 8152 $T3 &
wait_runs
run q35-4b-q3km__t3cfg-s43 exams/test2024_v2 8151 $T3 --seed 43 &
run q35-4b-q3km__t3cfg-s43 exams/test2025_v2 8151 $T3 --seed 43 &
run q35-4b-q3ks__t3cfg exams/test2026_v2 8152 $T3 &
wait_runs
stop 8151 8152
echo T3_Q3_DONE
