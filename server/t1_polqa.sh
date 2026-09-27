#!/usr/bin/env bash
# T1: Gemma QAT t1final + RAG PolQA top-3 + 1 notatka z bazy (konfiguracja, która dała +12.6 pp w T2), s42 na 2024/2025.
set -u
cd ~/repo
. server/lib_eval.sh
Q=$HOME/models/google/gemma-4-12B-it-qat-q4_0-gguf
serve 8281 -m $Q/gemma-4-12b-it-qat-q4_0.gguf --mmproj $Q/mmproj-gemma-4-12b-it-qat-q4_0.gguf -ub 4096 -b 4096 -c 81920 -np 4 \
  --reasoning-format deepseek
T1="--parallel 2 --vision --think essay,rozstrz,open,podaj,closed --temperature 1.0 --top-p 0.95 --top-k 64 --seed 42"
P="--rag bm25 --rag-types podaj,rozstrz,open --rag-k 3 --kb-rag data/kb/kb_all_notes.jsonl --kb-rag-k 1"
run gemma4-qat-t1polqa__s42 exams/test2024_v2 8281 $T1 $P &
run gemma4-qat-t1polqa__s42 exams/test2025_v2 8281 $T1 $P &
wait_runs
stop 8281
echo T1_POLQA_DONE
