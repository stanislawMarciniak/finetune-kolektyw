#!/usr/bin/env bash
# Raport 12: poprawki po analizie porażek. T2: --fill-fields (pełny przebieg + baza tej samej maszyny);
# T1: --rozstrz-hint tylko na zadaniach „rozstrzygnij” (reszta z t1final), 2 seedy.
#   bash server/fx_run.sh t2|t1
set -u
cd ~/repo
. server/lib_eval.sh
SETS="test2024_v2 test2025_v2 test2026_v2"
declare -A RZ=(
  [test2024_v2]="1,2,5.1,7,8.2,9,12.3,14.1,15.2,16.1,18,20.1,23.2,24"
  [test2025_v2]="1.1,2,3.2,5.2,6,7.1,11.2,12,14.1,15.2,16.1,16.2,21.2,22"
  [test2026_v2]="3.1,4.1,6.2,8,12.2,14.2,15.1,17,18.2,19.1,20,22,23.1,25"
)
if [ "$1" = t2 ]; then
  P=8802
  T2="--parallel 8 --no-think-kwargs --temperature 0.0 --top-p 1.0 --top-k 1 --kb-essay data/kb/kompendium.jsonl --rag bm25 --rag-types podaj,rozstrz,open --rag-k 3 --kb-rag data/kb/kb_all_notes.jsonl --kb-rag-k 1"
  serve $P -m $HOME/models/mradermacher/PLLuM-12B-base-2512-GGUF/PLLuM-12B-base-2512.Q4_K_M.gguf --lora $HOME/train/pllum-v1recipe-full/lora.gguf \
    --chat-template-file $HOME/train/pllum-12b-base/chat_template.jinja -c 65536 -np 8 || exit 1
  for ds in $SETS; do run fx-t2base exams/$ds $P $T2; done
  for ds in $SETS; do run fx-t2ff exams/$ds $P $T2 --fill-fields; done
  declare -A FF=([test2024_v2]="13" [test2025_v2]="8,19,20,23" [test2026_v2]="5.1,13,20")
  for ds in $SETS; do run fx-t2ff2 exams/$ds $P $T2 --fill-fields --only-ids ${FF[$ds]} --merge-from runs/$ds/fx-t2base; done
  for ds in $SETS; do run fx-t2ff3 exams/$ds $P $T2 --fill-fields --only-ids ${FF[$ds]} --merge-from runs/$ds/fx-t2base; done
  for ds in $SETS; do run fx-t2ff4 exams/$ds $P $T2 --fill-fields --only-ids ${FF[$ds]} --merge-from runs/$ds/fx-t2base; done
  stop $P
  echo FX_T2_DONE
fi
if [ "$1" = t1 ]; then
  P=8801
  G=$HOME/models/google/gemma-4-12B-it-qat-q4_0-gguf
  T1="--parallel 8 --rag none --vision --think essay,rozstrz,open,podaj,closed --temperature 1.0 --top-p 0.95 --top-k 64"
  serve $P -m $G/gemma-4-12b-it-qat-q4_0.gguf --mmproj $G/mmproj-gemma-4-12b-it-qat-q4_0.gguf -ub 4096 -b 4096 -c 131072 -np 8 \
    --reasoning-format deepseek || exit 1
  for ds in $SETS; do
    for s in 42 43; do
      src=runs/$ds/gemma4-qat-t1final__s$s; [ -d $src ] || src=runs/$ds/gemma4-qat-t1final__s42
      run fx-t1rh-s$s exams/$ds $P $T1 --seed $s --rozstrz-hint --only-ids ${RZ[$ds]} --merge-from $src &
    done
  done
  run fx-t1base-s43 exams/test2026_v2 $P $T1 --seed 43 --only-ids ${RZ[test2026_v2]} --merge-from runs/test2026_v2/gemma4-qat-t1final__s42 &
  wait_runs
  stop $P
  echo FX_T1_DONE
fi
if [ "$1" = t1s44 ]; then
  P=8801
  G=$HOME/models/google/gemma-4-12B-it-qat-q4_0-gguf
  T1="--parallel 8 --rag none --vision --think essay,rozstrz,open,podaj,closed --temperature 1.0 --top-p 0.95 --top-k 64"
  serve $P -m $G/gemma-4-12b-it-qat-q4_0.gguf --mmproj $G/mmproj-gemma-4-12b-it-qat-q4_0.gguf -ub 4096 -b 4096 -c 131072 -np 8 \
    --reasoning-format deepseek || exit 1
  for ds in $SETS; do
    src=runs/$ds/gemma4-qat__nt1final-s44; [ -d $src ] || src=runs/$ds/gemma4-qat-t1final__s42
    run fx-t1rh-s44 exams/$ds $P $T1 --seed 44 --rozstrz-hint --only-ids ${RZ[$ds]} --merge-from $src &
  done
  wait_runs
  stop $P
  echo FX_T1S44_DONE
fi
