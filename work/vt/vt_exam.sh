#!/usr/bin/env bash
# vt_exam.sh <port> <tag> <gguf> <sheets...>  -- T3 final config (+ essay structured), one server with 8 slots per sheet
set -u
cd ~/repo
. server/lib_eval.sh
port=$1 tag=$2 gguf=$3; shift 3
ns=$#; np=$((8 * ns)); ctx=$((98304 * ns))
RBM=$'\n\nNa podstawie powyższych rozważań podaję ostateczną odpowiedź.\n'
MMP=$HOME/models/unsloth/Qwen3.5-4B-GGUF/mmproj-F16.gguf
T3="--parallel 8 --rag none --vision --think rozstrz,open,podaj,closed --temperature 0.6 --top-p 0.95 --top-k 20 --max-tokens 8000 --kb-essay data/kb/kompendium.jsonl --essay-mode structured --think-retry --match-retry --seed ${SEED:-42}"
serve $port -m "$gguf" --mmproj "$MMP" -ub 4096 -b 4096 -c $ctx -np $np --reasoning-format deepseek --reasoning-budget 5000 --reasoning-budget-message "$RBM" || exit 1
for ds in "$@"; do run "q35-4b-vt-${tag}__struct2-s${SEED:-42}" exams/$ds $port $T3 & done
wait_runs
stop $port
echo "VT_EXAM_DONE $tag"
