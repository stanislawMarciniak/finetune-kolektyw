#!/usr/bin/env bash
# Raport 22, druga wersja wymagań (2–3 pewne fakty, bez wyboru tematu „po faktach”): tylko esej, bez scalania.
#   bash server/ek22_run3.sh <port> [seedy]
set -u
cd ~/repo
. server/lib_eval.sh
P=${1:-8578}; SEEDS=${2:-"42 43 44 45 46"}
G=$HOME/models/google/gemma-4-12B-it-qat-q4_0-gguf
serve $P -m $G/gemma-4-12b-it-qat-q4_0.gguf --mmproj $G/mmproj-gemma-4-12b-it-qat-q4_0.gguf -ub 4096 -b 4096 -c 131072 -np 8 \
  --reasoning-format deepseek || exit 1
T1="--parallel 8 --rag none --vision --think essay,rozstrz,open,podaj,closed --temperature 1.0 --top-p 0.95 --top-k 64 --rozstrz-hint"
declare -A E=([test2024_v2]=26 [test2025_v2]=25 [test2026_v2]=26)
for ds in test2024_v2 test2025_v2 test2026_v2; do
  for s in $SEEDS; do
    run ek22S-s$s exams/$ds $P $T1 --seed $s --essay-mode rubric --only-ids ${E[$ds]} &
    run ek22SK-s$s exams/$ds $P $T1 --seed $s --essay-mode rubric --essay-refine-kb data/kb/kb_all_notes.jsonl \
      --essay-refine-think --only-ids ${E[$ds]} &
  done
done
wait_runs
stop $P
echo EK22_3_DONE
