#!/usr/bin/env bash
# Powtórka przebiegów T1 zepsutych przez awarię serwera (H-N1): serwer z nadzorcą, harness z ponawianiem.
set -u
cd ~/repo
. server/lib_eval.sh
for r in gemma4-qat-legacy__s42 gemma4-qat-legacy__s43 gemma4-qat-t1final__s43; do rm -rf runs/test2024_v2/$r runs/test2025_v2/$r; done
Q=$HOME/models/google/gemma-4-12B-it-qat-q4_0-gguf
serve 8234 -m $Q/gemma-4-12b-it-qat-q4_0.gguf --mmproj $Q/mmproj-gemma-4-12b-it-qat-q4_0.gguf -ub 4096 -b 4096 -c 131072 -np 8 \
  --reasoning-format deepseek
T1="--parallel 4 --rag none --vision --think essay,rozstrz,open,podaj,closed --temperature 1.0 --top-p 0.95 --top-k 64"
run gemma4-qat-legacy__s42 exams/test2024_v2 8234 $T1 --seed 42 --legacy-prompt &
run gemma4-qat-legacy__s42 exams/test2025_v2 8234 $T1 --seed 42 --legacy-prompt &
wait_runs
run gemma4-qat-t1final__s43 exams/test2024_v2 8234 $T1 --seed 43 &
run gemma4-qat-t1final__s43 exams/test2025_v2 8234 $T1 --seed 43 &
wait_runs
run gemma4-qat-legacy__s43 exams/test2024_v2 8234 $T1 --seed 43 --legacy-prompt &
run gemma4-qat-legacy__s43 exams/test2025_v2 8234 $T1 --seed 43 --legacy-prompt &
wait_runs
stop 8234
grep -c SUPERVISOR $L/server_8234.log
echo PHASE0D_DONE
