#!/usr/bin/env bash
# T2: ewaluacja adaptera PLLuM w najlepszej dotąd konfiguracji RAG (PolQA BM25 top-3 + 1 notatka z bazy wiedzy) i bez RAG.
#   bash server/t2_eval_polqa.sh <nazwa adaptera w ~/train>
set -u
cd ~/repo
. server/lib_eval.sh
NAME=$1
M=$HOME/models/mradermacher/PLLuM-12B-base-2512-GGUF/PLLuM-12B-base-2512.Q4_K_M.gguf
serve 8251 -m $M --lora $HOME/train/$NAME/lora.gguf --chat-template-file $HOME/train/pllum-12b-base/chat_template.jinja -c 65536 -np 8
G="--no-think-kwargs --temperature 0.0 --top-p 1.0 --top-k 1 --parallel 4"
for ds in test2024_v2 test2025_v2; do
  run $NAME exams/$ds 8251 $G &
  run $NAME-polqa exams/$ds 8251 $G --kb-essay data/kb/kompendium.jsonl --rag bm25 --rag-types podaj,rozstrz,open --rag-k 3 \
    --kb-rag data/kb/kb_all_notes.jsonl --kb-rag-k 1 &
done
wait_runs
stop 8251
echo "T2_EVAL_DONE $NAME"
