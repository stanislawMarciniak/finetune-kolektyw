#!/usr/bin/env bash
# T2: PLLuM + LoRA v2 answer (trenowany z kontekstem RAFT) z RAG z bazy wiedzy w ewaluacji, jak w treningu (H-N26).
set -u
cd ~/repo
. server/lib_eval.sh
M=$HOME/models/mradermacher/PLLuM-12B-base-2512-GGUF/PLLuM-12B-base-2512.Q4_K_M.gguf
serve 8241 -m $M --lora $HOME/train/pllum-v2-answer/lora.gguf --chat-template-file $HOME/train/pllum-12b-base/chat_template.jinja -c 65536 -np 8
G="--no-think-kwargs --temperature 0.0 --top-p 1.0 --top-k 1 --parallel 4 --kb-essay data/kb/kompendium.jsonl"
for ds in test2024_v2 test2025_v2; do
  run pllum-v2-answer-kbrag exams/$ds 8241 $G --kb-rag data/kb/kb_all_notes.jsonl --kb-rag-k 3 --rag-types podaj,rozstrz,open &
  run pllum-v2-answer-polqa exams/$ds 8241 $G --rag bm25 --rag-types podaj,rozstrz,open --rag-k 3 \
    --kb-rag data/kb/kb_all_notes.jsonl --kb-rag-k 1 &
done
wait_runs
stop 8241
echo PHASE2B_DONE
