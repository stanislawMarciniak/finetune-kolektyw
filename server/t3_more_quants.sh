#!/usr/bin/env bash
# T3: pośrednie kwantyzacje Qwen3.5-4B (IQ4_XS 2.48 GB, Q3_K_M 2.29 GB) w konfiguracji T3, paczki v2.
set -u
cd ~/repo
PY=$HOME/venv-eval/bin/python
. server/lib_eval.sh
Q=$HOME/models/unsloth/Qwen3.5-4B-GGUF
$PY -c "
import os
from huggingface_hub import hf_hub_download as d
for f in ('Qwen3.5-4B-IQ4_XS.gguf', 'Qwen3.5-4B-Q3_K_M.gguf'):
    d('unsloth/Qwen3.5-4B-GGUF', f, local_dir=os.path.expanduser('~/models/unsloth/Qwen3.5-4B-GGUF'))"
SRV="-ub 4096 -b 4096 -c 98304 -np 8 --reasoning-format deepseek"
T3="--parallel 4 --rag none --vision --think rozstrz,open,podaj,closed --temperature 1.0 --top-p 0.95 --top-k 20 --max-tokens 8000 --kb-essay data/kb/kompendium.jsonl"
serve 8131 -m $Q/Qwen3.5-4B-IQ4_XS.gguf --mmproj $Q/mmproj-F16.gguf $SRV
serve 8132 -m $Q/Qwen3.5-4B-Q3_K_M.gguf --mmproj $Q/mmproj-F16.gguf $SRV
for ds in test2024_v2 test2025_v2; do
  run q35-4b-iq4xs__t3cfg exams/$ds 8131 $T3 &
  run q35-4b-q3km__t3cfg exams/$ds 8132 $T3 &
done
wait_runs
stop 8131 8132
echo T3_MORE_DONE
