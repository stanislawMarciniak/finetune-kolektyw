#!/usr/bin/env bash
# H100: test --think-retry + --match-retry (raport 21) na T3 tuned (final_configs), tylko zadania z fallbackiem / cyframi
# w przebiegach bazowych struct2 (--only-ids + --merge-from; reszta arkusza bez zmian).
#   bash server/t3_retry.sh [port]   (domyślnie 8931)
set -u
cd ~/repo
. server/lib_eval.sh
P=${1:-8931}
M=$HOME/models
B=q35-4b-q2-iq2mpl-e4k-mix__struct2
T3="--parallel 8 --rag none --vision --think rozstrz,open,podaj,closed --temperature 0.6 --top-p 0.95 --top-k 20 --max-tokens 8000 \
  --kb-essay data/kb/kompendium.jsonl --essay-mode structured --think-retry --match-retry"
serve $P -m $M/custom/qwen35-4b/Qwen3.5-4B-IQ2_M-PL-E4K-MIX.gguf --mmproj $M/unsloth/Qwen3.5-4B-GGUF/mmproj-F16.gguf \
  -ub 4096 -b 4096 -c 98304 -np 8 --reasoning-format deepseek --reasoning-budget 5000 \
  --reasoning-budget-message $'\n\nNa podstawie powyższych rozważań podaję ostateczną odpowiedź.\n' || exit 1
run $B-rt-s42 exams/test2024_v2 $P $T3 --seed 42 --only-ids 9,25 --merge-from runs/test2024_v2/$B-s42 &
run $B-rt-s43 exams/test2024_v2 $P $T3 --seed 43 --only-ids 19.2,11.1 --merge-from runs/test2024_v2/$B-s43 &
run $B-rt-s43 exams/test2025_v2 $P $T3 --seed 43 --only-ids 5.2,9.3,14.1,4,5.1 --merge-from runs/test2025_v2/$B-s43 &
run $B-rt-s42 exams/test2026_v2 $P $T3 --seed 42 --only-ids 6.2,8,16.2 --merge-from runs/test2026_v2/$B-s42 &
wait_runs
stop $P
echo T3_RETRY_DONE
