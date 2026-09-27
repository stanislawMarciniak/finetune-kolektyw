#!/usr/bin/env bash
# T3: rozrzut między seedami (Q3_K_M s42 48.7% vs s43 38.7%): Q4_K_M s43, Q3_K_M s44 i Q3_K_M z temperaturą 0.6 (s42, s43).
set -u
cd ~/repo
PY=$HOME/venv-eval/bin/python
. server/lib_eval.sh
Q=$HOME/models/unsloth/Qwen3.5-4B-GGUF
SRV="-ub 4096 -b 4096 -c 98304 -np 8 --reasoning-format deepseek"
T="--parallel 4 --rag none --vision --think rozstrz,open,podaj,closed --top-p 0.95 --top-k 20 --max-tokens 8000 --kb-essay data/kb/kompendium.jsonl"
serve 8171 -m $Q/Qwen3.5-4B-Q3_K_M.gguf --mmproj $Q/mmproj-F16.gguf $SRV
serve 8172 -m $Q/Qwen3.5-4B-Q4_K_M.gguf --mmproj $Q/mmproj-F16.gguf $SRV
for ds in test2024_v2 test2025_v2; do
  run q35-4b-q3km__t3cfg-t06 exams/$ds 8171 $T --temperature 0.6 --seed 42 &
  run q35-4b-q4__t3cfg-s43 exams/$ds 8172 $T --temperature 1.0 --seed 43 &
done
wait_runs
for ds in test2024_v2 test2025_v2; do
  run q35-4b-q3km__t3cfg-t06-s43 exams/$ds 8171 $T --temperature 0.6 --seed 43 &
  run q35-4b-q3km__t3cfg-s44 exams/$ds 8171 $T --temperature 1.0 --seed 44 &
done
wait_runs
stop 8171 8172
echo T3_VAR_DONE
