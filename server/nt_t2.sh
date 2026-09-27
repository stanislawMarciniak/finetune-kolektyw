#!/usr/bin/env bash
# T2 bez treningu (raport 10): PLLuM + LoRA v1recipe-full, warianty harnessu (temp. 0 — jeden przebieg na wariant).
#   bash server/nt_t2.sh <port> <wariant...>        np. bash server/nt_t2.sh 8531 ref hyde k2 k3 ocr
#   SETS="test2026_v2" bash server/nt_t2.sh 8531 ref hyde
set -u
cd ~/repo
. server/lib_eval.sh
PORT=$1; shift
M=$HOME/models/mradermacher/PLLuM-12B-base-2512-GGUF/PLLuM-12B-base-2512.Q4_K_M.gguf
BASE="--parallel 3 --no-think-kwargs --temperature 0.0 --top-p 1.0 --top-k 1 --rag-types podaj,rozstrz,open --rag-k 3 --kb-rag-k 1"
KB1="--kb-essay data/kb/kompendium.jsonl --kb-rag data/kb/kb_all_notes.jsonl"
KB2="--kb-essay data/kb/kompendium_v2.jsonl --kb-rag data/kb/kb_all_notes_v2.jsonl"
declare -A C=(
  [ref]="$BASE $KB1 --rag bm25"
  [hyde]="$BASE $KB1 --rag hyde"
  [k2]="$BASE $KB1 --rag bm25 --kb-rag-k 2"
  [k3]="$BASE $KB1 --rag bm25 --kb-rag-k 3"
  [ocr]="$BASE $KB1 --rag bm25 --ocr"
  [clean]="$BASE $KB1 --rag bm25 --rag-clean-query"
  [essay]="$BASE $KB1 --rag bm25 --essay-topic-detect --essay-extend 2"
  [refine]="$BASE $KB1 --rag bm25 --essay-topic-detect --essay-extend 2 --essay-refine-kb data/kb/kb_all_notes.jsonl"
  [kb2]="$BASE $KB2 --rag bm25"
  [kb2k2]="$BASE $KB2 --rag bm25 --kb-rag-k 2"
  [kb3]="$BASE --kb-essay data/kb/kompendium_v3.jsonl --kb-rag data/kb/kb_all_notes_v3.jsonl --rag bm25"
  [kb3ess]="$BASE --kb-essay data/kb/kompendium_v3.jsonl --kb-rag data/kb/kb_all_notes.jsonl --rag bm25"
  [kb3rag]="$BASE --kb-essay data/kb/kompendium.jsonl --kb-rag data/kb/kb_all_notes_v3.jsonl --rag bm25"
  [kb2ess]="$BASE --kb-essay data/kb/kompendium_v2.jsonl --kb-rag data/kb/kb_all_notes.jsonl --rag bm25"
  [kb2rag]="$BASE --kb-essay data/kb/kompendium.jsonl --kb-rag data/kb/kb_all_notes_v2.jsonl --rag bm25"
  [combo]="$BASE $KB1 --rag bm25 ${COMBO:-}"
)
serve "$PORT" -m "$M" --lora ~/train/pllum-v1recipe-full/lora.gguf \
  --chat-template-file ~/train/pllum-12b-base/chat_template.jinja -c 49152 -np 8
for v in "$@"; do
  for ds in ${SETS:-test2024_v2 test2025_v2}; do
    run pllum-v1r__nt2$v exams/$ds "$PORT" ${C[$v]} &
  done
done
wait_runs
stop "$PORT"
echo NT_T2_DONE "$@"
