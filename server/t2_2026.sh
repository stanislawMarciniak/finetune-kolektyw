#!/usr/bin/env bash
# T2 potwierdzenie na 2026 (v2): PLLuM + LoRA v1 bez RAG oraz v2 answer z RAG PolQA + baza; bramka RAG (H-N25) na 2024/2025.
set -u
cd ~/repo
. server/lib_eval.sh
M=$HOME/models/mradermacher/PLLuM-12B-base-2512-GGUF/PLLuM-12B-base-2512.Q4_K_M.gguf
TPL=$HOME/train/pllum-12b-base/chat_template.jinja
G="--no-think-kwargs --temperature 0.0 --top-p 1.0 --top-k 1 --parallel 4"
P="--kb-essay data/kb/kompendium.jsonl --rag bm25 --rag-types podaj,rozstrz,open --rag-k 3 --kb-rag data/kb/kb_all_notes.jsonl --kb-rag-k 1"
serve 8261 -m $M --lora $HOME/train/pllum-12b-base/lora.gguf --chat-template-file $TPL -c 32768 -np 4
serve 8262 -m $M --lora $HOME/train/pllum-v2-answer/lora.gguf --chat-template-file $TPL -c 65536 -np 8
run pllum-12b-base-sft__v2 exams/test2026_v2 8261 $G &
run pllum-v2-answer-polqa exams/test2026_v2 8262 $G $P &
run pllum-v2-answer-polqa-gate exams/test2024_v2 8262 $G $P --rag-min-score 12 &
run pllum-v2-answer-polqa-gate exams/test2025_v2 8262 $G $P --rag-min-score 12 &
wait_runs
stop 8261 8262
echo T2_2026_DONE
