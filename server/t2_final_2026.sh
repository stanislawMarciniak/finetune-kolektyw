#!/usr/bin/env bash
# T2: potwierdzenie zwycięzcy (przepis v1 na pełnych danych + RAG PolQA + 1 notatka z bazy) na 2026 v2.
set -u
cd ~/repo
. server/lib_eval.sh
M=$HOME/models/mradermacher/PLLuM-12B-base-2512-GGUF/PLLuM-12B-base-2512.Q4_K_M.gguf
serve 8271 -m $M --lora $HOME/train/pllum-v1recipe-full/lora.gguf --chat-template-file $HOME/train/pllum-12b-base/chat_template.jinja -c 65536 -np 8
G="--no-think-kwargs --temperature 0.0 --top-p 1.0 --top-k 1 --parallel 4"
P="--kb-essay data/kb/kompendium.jsonl --rag bm25 --rag-types podaj,rozstrz,open --rag-k 3 --kb-rag data/kb/kb_all_notes.jsonl --kb-rag-k 1"
run pllum-v1recipe-full-polqa exams/test2026_v2 8271 $G $P &
run pllum-v1recipe-full exams/test2026_v2 8271 $G &
wait_runs
stop 8271
echo T2_FINAL_2026_DONE
