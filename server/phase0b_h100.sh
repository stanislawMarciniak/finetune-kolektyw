#!/usr/bin/env bash
# Faza 0b na H100 (zanim przyjdą dane v2): T2 PLLuM + LoRA v1 z kompendium w eseju (BM25 i hybryda e5), T1 t1final na 2026 (potwierdzenie).
set -u
cd ~/repo
. server/lib_eval.sh
M=$HOME/models
serve 8231 -m $M/mradermacher/PLLuM-12B-base-2512-GGUF/PLLuM-12B-base-2512.Q4_K_M.gguf --lora $HOME/train/pllum-12b-base/lora.gguf \
  --chat-template-file $HOME/train/pllum-12b-base/chat_template.jinja -c 65536 -np 8
G="--no-think-kwargs --temperature 0.0 --top-p 1.0 --top-k 1 --parallel 4"
run pllum-12b-base-sft__v2-kb exams/test2024_v2 8231 $G --kb-essay data/kb/kompendium.jsonl &
run pllum-12b-base-sft__v2-kb exams/test2025_v2 8231 $G --kb-essay data/kb/kompendium.jsonl &
wait_runs
run pllum-12b-base-sft__v2-kbdense exams/test2024_v2 8231 $G --kb-essay data/kb/kompendium.jsonl --kb-dense &
run pllum-12b-base-sft__v2-kbdense exams/test2025_v2 8231 $G --kb-essay data/kb/kompendium.jsonl --kb-dense &
wait_runs
stop 8231
Q=$M/google/gemma-4-12B-it-qat-q4_0-gguf
serve 8232 -m $Q/gemma-4-12b-it-qat-q4_0.gguf --mmproj $Q/mmproj-gemma-4-12b-it-qat-q4_0.gguf -ub 4096 -b 4096 -c 131072 -np 8 \
  --reasoning-format deepseek
run gemma4-qat-t1final__s42 exams/test2026_v2 8232 --parallel 8 --rag none --vision --think essay,rozstrz,open,podaj,closed \
  --temperature 1.0 --top-p 0.95 --top-k 64 --seed 42
stop 8232
echo PHASE0B_DONE
