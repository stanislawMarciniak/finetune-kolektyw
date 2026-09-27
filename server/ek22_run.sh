#!/usr/bin/env bash
# Raport 22: esej T1 z wymaganiami CKE (--essay-mode rubric [--essay-rubric-plan]); tylko esej, reszta z bazowego przebiegu.
#   bash server/ek22_run.sh <port> [seedy]
set -u
cd ~/repo
. server/lib_eval.sh
P=${1:-8577}; SEEDS=${2:-"42 43 44"}
T1="--parallel 8 --rag none --vision --think essay,rozstrz,open,podaj,closed --temperature 1.0 --top-p 0.95 --top-k 64 --rozstrz-hint"
declare -A E=([test2024_v2]=26 [test2025_v2]=25 [test2026_v2]=26)
for ds in test2024_v2 test2025_v2 test2026_v2; do
  for s in $SEEDS; do
    src=runs/$ds/gemma4-qat-t1final__s$s; [ -d $src ] || src=runs/$ds/gemma4-qat__nt1final-s$s; [ -d $src ] || src=runs/$ds/gemma4-qat-t1final__s42
    run ek22R-s$s exams/$ds $P $T1 --seed $s --essay-mode rubric --only-ids ${E[$ds]} --merge-from $src &
    run ek22RP-s$s exams/$ds $P $T1 --seed $s --essay-mode rubric --essay-rubric-plan --only-ids ${E[$ds]} --merge-from $src &
    [ $ds = test2026_v2 ] && [ $s != 42 ] && run ek22B-s$s exams/$ds $P $T1 --seed $s --only-ids ${E[$ds]} --merge-from $src &
  done
done
wait_runs
echo EK22_DONE
