#!/usr/bin/env bash
# T1: Gemma QAT t1final z temperaturą 0.6 (mniejszy rozrzut eseju? H-N7), s42 na 2024/2025.
set -u
cd ~/repo
. server/lib_eval.sh
Q=$HOME/models/google/gemma-4-12B-it-qat-q4_0-gguf
serve 8291 -m $Q/gemma-4-12b-it-qat-q4_0.gguf --mmproj $Q/mmproj-gemma-4-12b-it-qat-q4_0.gguf -ub 4096 -b 4096 -c 81920 -np 4 \
  --reasoning-format deepseek
T1="--parallel 2 --rag none --vision --think essay,rozstrz,open,podaj,closed --temperature 0.6 --top-p 0.95 --top-k 64 --seed 42"
run gemma4-qat-t1final-t06__s42 exams/test2024_v2 8291 $T1 &
run gemma4-qat-t1final-t06__s42 exams/test2025_v2 8291 $T1 &
wait_runs
stop 8291
echo T1_T06_DONE
