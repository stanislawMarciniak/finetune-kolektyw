#!/usr/bin/env bash
# Raport 15: obrazy w T1. --image-tiles tylko na zadaniach z obrazami (reszta z t1final), 2 seedy.
#   bash server/img_run.sh t1tiles [port]
set -u
cd ~/repo
. server/lib_eval.sh
SETS="test2024_v2 test2025_v2 test2026_v2"
declare -A IMG=(
  [test2024_v2]="1,2,4,5.1,5.2,6,8.1,8.2,9,10,11.1,11.2,12.1,12.2,12.3,13,14.1,14.2,16.1,16.2,17.1,17.2,18,19.1,19.2,21,23.1,23.2,24,25"
  [test2025_v2]="1.1,1.2,3.1,3.2,6,7.1,7.2,8,10,12,14.1,14.2,16.1,16.2,17.1,17.2,18,20,21.1,21.2,23"
  [test2026_v2]="1,3.1,3.2,4.1,4.2,7,12.1,12.2,13,14.1,14.2,14.3,15.1,15.2,16.1,16.2,18.1,18.2,19.1,19.2,20,23.1,23.2,24,25"
)
G=$HOME/models/google/gemma-4-12B-it-qat-q4_0-gguf
T1="--parallel 8 --rag none --vision --think essay,rozstrz,open,podaj,closed --temperature 1.0 --top-p 0.95 --top-k 64"
base_of() {  # $1 zbiór, $2 seed -> przebieg bazowy t1final
  local d=runs/$1/gemma4-qat-t1final__s$2
  [ -d $d ] || d=runs/$1/fx-t1base-s$2
  [ -d $d ] || d=runs/$1/gemma4-qat-t1final__s42
  echo $d
}
if [ "$1" = t1tiles ]; then
  P=${2:-8811}
  serve $P -m $G/gemma-4-12b-it-qat-q4_0.gguf --mmproj $G/mmproj-gemma-4-12b-it-qat-q4_0.gguf -ub 4096 -b 4096 -c 131072 -np 8 \
    --reasoning-format deepseek || exit 1
  for ds in $SETS; do
    for s in 42 43; do
      run img-t1tiles-s$s exams/$ds $P $T1 --seed $s --image-tiles --only-ids ${IMG[$ds]} --merge-from $(base_of $ds $s) &
    done
  done
  wait_runs
  stop $P
  echo IMG_T1_DONE
fi
if [ "$1" = t2cap ]; then
  P=${2:-8823} PC=${3:-8822}
  Q=$HOME/models/unsloth/Qwen3.5-0.8B-GGUF
  T2="--parallel 8 --no-think-kwargs --temperature 0.0 --top-p 1.0 --top-k 1 --kb-essay data/kb/kompendium.jsonl --rag bm25 --rag-types podaj,rozstrz,open --rag-k 3 --kb-rag data/kb/kb_all_notes.jsonl --kb-rag-k 1 --fill-fields"
  serve $PC -m $Q/Qwen3.5-0.8B-Q8_0.gguf --mmproj $Q/mmproj-F16.gguf -c 32768 -np 8 || exit 1
  serve $P -m $HOME/models/mradermacher/PLLuM-12B-base-2512-GGUF/PLLuM-12B-base-2512.Q4_K_M.gguf --lora $HOME/train/pllum-v1recipe-full/lora.gguf \
    --chat-template-file $HOME/train/pllum-12b-base/chat_template.jinja -c 65536 -np 8 || exit 1
  for r in a b; do
    for ds in $SETS; do
      run img-t2base-$r exams/$ds $P $T2 --only-ids ${IMG[$ds]} --merge-from runs/$ds/fx-t2ff4
      run img-t2cap-$r exams/$ds $P $T2 --caption-url http://127.0.0.1:$PC/v1 --only-ids ${IMG[$ds]} --merge-from runs/$ds/fx-t2ff4
    done
  done
  [ -n "${CAP2:-}" ] && for r in a b; do for ds in $SETS; do
    run img-t2cap2-$r exams/$ds $P $T2 --caption-url http://127.0.0.1:$PC/v1 --only-ids ${IMG[$ds]} --merge-from runs/$ds/fx-t2ff4
  done; done
  stop $P; stop $PC
  echo IMG_T2_DONE
fi
if [ "$1" = t2ocr ]; then  # konfiguracja z --ocr (dodane 05:33): OCR vs OCR + opisy
  P=${2:-8823} PC=${3:-8822}
  Q=$HOME/models/unsloth/Qwen3.5-0.8B-GGUF
  T2="--parallel 8 --no-think-kwargs --temperature 0.0 --top-p 1.0 --top-k 1 --kb-essay data/kb/kompendium.jsonl --rag bm25 --rag-types podaj,rozstrz,open --rag-k 3 --kb-rag data/kb/kb_all_notes.jsonl --kb-rag-k 1 --fill-fields --ocr"
  serve $PC -m $Q/Qwen3.5-0.8B-Q8_0.gguf --mmproj $Q/mmproj-F16.gguf -c 32768 -np 8 || exit 1
  serve $P -m $HOME/models/mradermacher/PLLuM-12B-base-2512-GGUF/PLLuM-12B-base-2512.Q4_K_M.gguf --lora $HOME/train/pllum-v1recipe-full/lora.gguf \
    --chat-template-file $HOME/train/pllum-12b-base/chat_template.jinja -c 65536 -np 8 || exit 1
  for r in a b; do
    for ds in $SETS; do
      run img-t2ocr-$r exams/$ds $P $T2 --only-ids ${IMG[$ds]} --merge-from runs/$ds/fx-t2ff4
      run img-t2ocrcap-$r exams/$ds $P $T2 --caption-url http://127.0.0.1:$PC/v1 --only-ids ${IMG[$ds]} --merge-from runs/$ds/fx-t2ff4
    done
  done
  stop $P; stop $PC
  echo IMG_T2OCR_DONE
fi
