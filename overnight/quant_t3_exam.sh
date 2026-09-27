#!/usr/bin/env bash
# A/B egzaminu T3: własne kwantyzacje vs stock UD-IQ3_XXS, identyczne flagi (jak server/nt_t3_wave1.sh), 2024+2025.
#   quant_t3_exam.sh <seed> <nazwa=ścieżka.gguf>...   (porty 8601+)
set -u
cd ~/repo
. server/lib_eval.sh
seed=$1; shift
SRV="-ub 4096 -b 4096 -c 98304 -np 8 --reasoning-format deepseek"
RBM=$'\n\nNa podstawie powyższych rozważań podaję ostateczną odpowiedź.\n'
T3="--parallel 4 --rag none --vision --think rozstrz,open,podaj,closed --temperature 0.6 --top-p 0.95 --top-k 20 --max-tokens 8000 --kb-essay data/kb/kompendium.jsonl --seed $seed"
MMP=$HOME/models/unsloth/Qwen3.5-4B-GGUF/mmproj-F16.gguf
port=${PORT0:-8601}; ports=()
for spec in "$@"; do
  name=${spec%%=*}; gguf=${spec#*=}
  serve $port -m "$gguf" --mmproj "$MMP" $SRV --reasoning-budget 5000 --reasoning-budget-message "$RBM" || exit 1
  for ds in test2024_v2 test2025_v2; do run "q35-4b-cq-${name}__bf5k-s$seed" exams/$ds $port $T3 & done
  ports+=($port); port=$((port + 1))
done
wait_runs
stop "${ports[@]}"
echo "CQ_EXAM_DONE s$seed"
