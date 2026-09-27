#!/usr/bin/env bash
# T1 na pełnych arkuszach v2: t1final + kompendium w eseju (H-N6 potwierdziło +9 pp na 12 esejach), 2 seedy.
set -u
cd ~/repo
. server/lib_eval.sh
Q=$HOME/models/google/gemma-4-12B-it-qat-q4_0-gguf
serve 8233 -m $Q/gemma-4-12b-it-qat-q4_0.gguf --mmproj $Q/mmproj-gemma-4-12b-it-qat-q4_0.gguf -ub 4096 -b 4096 -c 131072 -np 8 \
  --reasoning-format deepseek
T1="--parallel 4 --rag none --vision --think essay,rozstrz,open,podaj,closed --temperature 1.0 --top-p 0.95 --top-k 64 --kb-essay data/kb/kompendium.jsonl"
for s in 42 43; do
  run gemma4-qat-t1kb__s$s exams/test2024_v2 8233 $T1 --seed $s &
  run gemma4-qat-t1kb__s$s exams/test2025_v2 8233 $T1 --seed $s &
  wait_runs
done
stop 8233
echo PHASE0C_DONE
