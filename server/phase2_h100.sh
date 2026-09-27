#!/usr/bin/env bash
# Faza 2 na H100: T2 PLLuM-12B-base, LoRA BF16 na danych v2 w wariancie „think” (uzasadnienie w <think>), potem ewaluacja v2.
# Wariant „answer” (kontrola) i T3 z maską myślenia trenują równolegle na Modal (overnight/modal_train.py).
#   bash server/phase2_h100.sh [think|answer]
set -u
cd ~/repo
. server/lib_eval.sh
V=${1:-think}
NAME=${NAME:-pllum-v2-$V}
DATA=${DATA:-data/sft/v2}
EPOCHS=${EPOCHS:-1}
OUT=$HOME/train/$NAME
if [ ! -f $OUT/lora.gguf ]; then
  $HOME/venv-unsloth/bin/python train/sft_lora.py --model CYFRAGOVPL/PLLuM-12B-base-2512 \
    --template-from CYFRAGOVPL/PLLuM-12B-instruct-2512 --train $DATA/train_$V.jsonl --val $DATA/val_$V.jsonl \
    --out $OUT --epochs $EPOCHS --rank 32 --lr 1e-4 --batch 4 --grad-acc 4 --max-len 4096 > $L/train_$NAME.log 2>&1
  $HOME/venv-hf/bin/python $HOME/llama.cpp/convert_lora_to_gguf.py $OUT/adapter --base-model-id CYFRAGOVPL/PLLuM-12B-base-2512 \
    --outtype f16 --outfile $OUT/lora.gguf >> $L/train_$NAME.log 2>&1
fi
ls -la $OUT/lora.gguf || { tail -30 $L/train_$NAME.log; exit 1; }
M=$HOME/models/mradermacher/PLLuM-12B-base-2512-GGUF/PLLuM-12B-base-2512.Q4_K_M.gguf
serve 8221 -m $M --lora $OUT/lora.gguf --chat-template-file $HOME/train/pllum-12b-base/chat_template.jinja -c 65536 -np 8
G="--no-think-kwargs --temperature 0.0 --top-p 1.0 --top-k 1 --parallel 4 --answer-max-tokens 3072 --essay-answer-max-tokens 6144"
run $NAME exams/test2024_v2 8221 $G &
run $NAME exams/test2025_v2 8221 $G &
wait_runs
run ${NAME}-kbrag exams/test2024_v2 8221 $G --kb-essay data/kb/kompendium.jsonl --kb-rag data/kb/kb_all_notes.jsonl --kb-rag-k 3 \
  --rag-types podaj,rozstrz,open &
run ${NAME}-kbrag exams/test2025_v2 8221 $G --kb-essay data/kb/kompendium.jsonl --kb-rag data/kb/kb_all_notes.jsonl --kb-rag-k 3 \
  --rag-types podaj,rozstrz,open &
wait_runs
stop 8221
echo "PHASE2_DONE $NAME"
