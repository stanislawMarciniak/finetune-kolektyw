#!/usr/bin/env bash
# Raport 14: --match-names-hint tylko na dopasowaniach z nazwami (reszta z przebiegu bazowego), 2 seedy.
#   bash server/mn_run.sh t1|t3
set -u
cd ~/repo
. server/lib_eval.sh
SETS="test2024_v2 test2025_v2 test2026_v2"
declare -A MN=([test2024_v2]="11.1" [test2025_v2]="4,5.1,11.1" [test2026_v2]="6.1,21")
if [ "$1" = t1 ]; then
  P=8811
  G=$HOME/models/google/gemma-4-12B-it-qat-q4_0-gguf
  H="--parallel 8 --rag none --vision --think essay,rozstrz,open,podaj,closed --temperature 1.0 --top-p 0.95 --top-k 64"
  serve $P -m $G/gemma-4-12b-it-qat-q4_0.gguf --mmproj $G/mmproj-gemma-4-12b-it-qat-q4_0.gguf -ub 4096 -b 4096 -c 131072 -np 8 \
    --reasoning-format deepseek || exit 1
  SRC=gemma4-qat-t1final__s42 NAME=fx-t1mn
fi
if [ "$1" = t3 ]; then
  P=8812
  Q=$HOME/models/unsloth/Qwen3.5-4B-GGUF
  H="--parallel 8 --rag none --vision --think rozstrz,open,podaj,closed --temperature 0.6 --top-p 0.95 --top-k 20 --max-tokens 8000 --kb-essay data/kb/kompendium.jsonl --essay-topic-detect --essay-extend 2 --essay-min-words 300"
  serve $P -m $Q/Qwen3.5-4B-UD-IQ3_XXS.gguf --mmproj $Q/mmproj-F16.gguf -ub 4096 -b 4096 -c 98304 -np 8 --reasoning-format deepseek \
    --reasoning-budget 5000 --reasoning-budget-message $'\n\nNa podstawie powyższych rozważań podaję ostateczną odpowiedź.\n' || exit 1
  SRC=q35-4b-iq3xxs__nt3rb-s42 NAME=fx-t3mn
fi
if [ "$1" = t2 ]; then
  P=8813
  H="--parallel 8 --no-think-kwargs --temperature 0.0 --top-p 1.0 --top-k 1 --kb-essay data/kb/kompendium.jsonl --rag bm25 --rag-types podaj,rozstrz,open --rag-k 3 --kb-rag data/kb/kb_all_notes.jsonl --kb-rag-k 1 --fill-fields"
  serve $P -m $HOME/models/mradermacher/PLLuM-12B-base-2512-GGUF/PLLuM-12B-base-2512.Q4_K_M.gguf --lora $HOME/train/pllum-v1recipe-full/lora.gguf \
    --chat-template-file $HOME/train/pllum-12b-base/chat_template.jinja -c 65536 -np 8 || exit 1
  SRC=fx-t2ff NAME=fx-t2mn
fi
for ds in $SETS; do
  for s in 42 43; do
    m=""; [ -f runs/$ds/$SRC/debug.jsonl ] && m="--merge-from runs/$ds/$SRC"
    run $NAME-s$s exams/$ds $P $H --seed $s --match-names-hint --only-ids ${MN[$ds]} $m &
  done
done
wait_runs
stop $P
echo MN_DONE
