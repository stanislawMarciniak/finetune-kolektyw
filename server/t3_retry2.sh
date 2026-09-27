#!/usr/bin/env bash
# H100: więcej próbek na zadaniach z fallbackiem (raport 21): myślenie + flagi (seedy 44, 45) vs bez myślenia
# (= to, co daje obecny fallback), plus dopasowania z nazwami. Reszta arkusza z --merge-from struct2-s42.
#   bash server/t3_retry2.sh [port]   (domyślnie 8932)
set -u
cd ~/repo
. server/lib_eval.sh
P=${1:-8932}
M=$HOME/models
B=q35-4b-q2-iq2mpl-e4k-mix__struct2
C="--parallel 8 --rag none --vision --temperature 0.6 --top-p 0.95 --top-k 20 --max-tokens 8000 \
  --kb-essay data/kb/kompendium.jsonl --essay-mode structured"
serve $P -m $M/custom/qwen35-4b/Qwen3.5-4B-IQ2_M-PL-E4K-MIX.gguf --mmproj $M/unsloth/Qwen3.5-4B-GGUF/mmproj-F16.gguf \
  -ub 4096 -b 4096 -c 98304 -np 8 --reasoning-format deepseek --reasoning-budget 5000 \
  --reasoning-budget-message $'\n\nNa podstawie powyższych rozważań podaję ostateczną odpowiedź.\n' || exit 1
declare -A IDS=([test2024_v2]=9,25,19.2,11.1 [test2025_v2]=5.2,9.3,14.1,4,5.1 [test2026_v2]=6.2,8,16.2)
for s in 44 45; do
  for ds in test2024_v2 test2025_v2 test2026_v2; do
    run $B-rt-s$s exams/$ds $P $C --think rozstrz,open,podaj,closed --think-retry --match-retry --seed $s \
      --only-ids ${IDS[$ds]} --merge-from runs/$ds/$B-s42 &
    run $B-nt-s$s exams/$ds $P $C --think "" --seed $s --only-ids ${IDS[$ds]} --merge-from runs/$ds/$B-s42 &
  done
  wait_runs
done
# ścieżka kodu: --max-tokens 1200 wymusza urwanie -> powtórka z myśleniem (też urwana) -> bez myślenia
run $B-rt-smoke exams/test2024_v2 $P ${C/--max-tokens 8000/--max-tokens 1200} --think rozstrz,open,podaj,closed \
  --think-retry --match-retry --seed 42 --only-ids 9,4
stop $P
echo T3_RETRY2_DONE
