#!/usr/bin/env bash
# Przebiegi T3 z FINALNĄ konfiguracją (server/final_configs.json) na podmienionym pliku modelu.
#   quant_t3_final.sh <port> <nazwa> <plik.gguf> <seed:egzamin>...   np. 8701 iq3xxs-pl-e4k ~/m.gguf 42:test2024_v2 42:test2025_v2
set -u
cd ~/repo
. server/lib_eval.sh
port=$1 name=$2 gguf=$3; shift 3
SRV="-ub 4096 -b 4096 -c 98304 -np 8 --reasoning-format deepseek --reasoning-budget 5000"
RBM=$'\n\nNa podstawie powyższych rozważań podaję ostateczną odpowiedź.\n'
T3="--parallel 8 --rag none --vision --think rozstrz,open,podaj,closed --temperature 0.6 --top-p 0.95 --top-k 20 --max-tokens 8000 --kb-essay data/kb/kompendium.jsonl --essay-topic-detect --essay-extend 2 --essay-min-words 300"
serve $port -m "$gguf" --mmproj $HOME/models/unsloth/Qwen3.5-4B-GGUF/mmproj-F16.gguf $SRV --reasoning-budget-message "$RBM" || exit 1
for sd in "$@"; do
  seed=${sd%%:*} ds=${sd#*:}
  run "q35-4b-cq-${name}__final-s$seed" exams/$ds $port $T3 --seed $seed &
done
wait_runs
stop $port
echo "CQ_FINAL_DONE $name $*"
