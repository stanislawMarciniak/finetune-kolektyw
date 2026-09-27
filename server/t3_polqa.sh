#!/usr/bin/env bash
# T3 (H100, bo tu jest indeks PolQA): Qwen3.5-4B Q3_K_M + RAG PolQA top-3 + 1 notatka z bazy dla „podaj / rozstrzygnij / otwartych”.
set -u
cd ~/repo
. server/lib_eval.sh
Q=$HOME/models/unsloth/Qwen3.5-4B-GGUF
serve 8181 -m $Q/Qwen3.5-4B-Q3_K_M.gguf --mmproj $Q/mmproj-F16.gguf -ub 4096 -b 4096 -c 98304 -np 8 --reasoning-format deepseek
T="--parallel 4 --vision --think rozstrz,open,podaj,closed --temperature 1.0 --top-p 0.95 --top-k 20 --max-tokens 8000 --kb-essay data/kb/kompendium.jsonl"
P="--rag bm25 --rag-types podaj,rozstrz,open --rag-k 3 --kb-rag data/kb/kb_all_notes.jsonl --kb-rag-k 1"
for ds in test2024_v2 test2025_v2; do
  run q35-4b-q3km__t3cfg-polqa exams/$ds 8181 $T $P &
done
wait_runs
stop 8181
echo T3_POLQA_DONE
