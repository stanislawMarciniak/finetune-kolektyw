#!/usr/bin/env bash
# T3: Q3_K_M z temperaturą 0.6 na 2026 v2 (potwierdzenie zwycięzcy).
set -u
cd ~/repo
PY=$HOME/venv-eval/bin/python
. server/lib_eval.sh
Q=$HOME/models/unsloth/Qwen3.5-4B-GGUF
serve 8191 -m $Q/Qwen3.5-4B-Q3_K_M.gguf --mmproj $Q/mmproj-F16.gguf -ub 4096 -b 4096 -c 98304 -np 8 --reasoning-format deepseek
T="--parallel 8 --rag none --vision --think rozstrz,open,podaj,closed --temperature 0.6 --top-p 0.95 --top-k 20 --max-tokens 8000 --kb-essay data/kb/kompendium.jsonl"
run q35-4b-q3km__t3cfg-t06 exams/test2026_v2 8191 $T --seed 42
stop 8191
echo T3_T06_2026_DONE
