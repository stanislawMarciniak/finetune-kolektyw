#!/usr/bin/env bash
# T1 (raport 10, dogrywka): --image-min-tokens 1120 na 2026 (s42, s43) + trzeci seed (s44) 2024+2025 dla finału i 1120.
set -u
cd ~/repo
. server/lib_eval.sh
Q=$HOME/models/google/gemma-4-12B-it-qat-q4_0-gguf
SRV="-m $Q/gemma-4-12b-it-qat-q4_0.gguf --mmproj $Q/mmproj-gemma-4-12b-it-qat-q4_0.gguf -ub 4096 -b 4096 -c 131072 -np 8 --reasoning-format deepseek"
serve 8571 $SRV --image-min-tokens 1120 --image-max-tokens 1120
serve 8572 $SRV
T1="--parallel 4 --rag none --vision --think essay,rozstrz,open,podaj,closed --temperature 1.0 --top-p 0.95 --top-k 64"
run gemma4-qat__nt1img1120-s42 exams/test2026_v2 8571 $T1 --seed 42 &
run gemma4-qat__nt1img1120-s43 exams/test2026_v2 8571 $T1 --seed 43 &
for ds in test2024_v2 test2025_v2; do
  run gemma4-qat__nt1img1120-s44 exams/$ds 8571 $T1 --seed 44 &
  run gemma4-qat__nt1final-s44 exams/$ds 8572 $T1 --seed 44 &
done
wait_runs
stop 8571 8572
echo NT_T1_IMG2_DONE
