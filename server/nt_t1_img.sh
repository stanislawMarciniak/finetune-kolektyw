#!/usr/bin/env bash
# T1 bez treningu (raport 10): więcej tokenów obrazu w Gemma-4 (--image-min-tokens 560 / 1120), t1final, 2 seedy, 2024+2025.
#   SEEDS="42 43" bash server/nt_t1_img.sh
set -u
cd ~/repo
. server/lib_eval.sh
Q=$HOME/models/google/gemma-4-12B-it-qat-q4_0-gguf
SRV="-m $Q/gemma-4-12b-it-qat-q4_0.gguf --mmproj $Q/mmproj-gemma-4-12b-it-qat-q4_0.gguf -ub 4096 -b 4096 -c 98304 -np 4 --reasoning-format deepseek"
serve 8521 $SRV --image-min-tokens 560 --image-max-tokens 1120
serve 8522 $SRV --image-min-tokens 1120 --image-max-tokens 1120
for s in ${SEEDS:-42 43}; do
  T1="--parallel 2 --rag none --vision --think essay,rozstrz,open,podaj,closed --temperature 1.0 --top-p 0.95 --top-k 64 --seed $s"
  for ds in test2024_v2 test2025_v2; do
    run gemma4-qat__nt1img560-s$s exams/$ds 8521 $T1 &
    run gemma4-qat__nt1img1120-s$s exams/$ds 8522 $T1 &
  done
  wait_runs
done
stop 8521 8522
echo NT_T1_IMG_DONE
