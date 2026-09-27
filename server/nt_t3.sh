#!/usr/bin/env bash
# T3 bez treningu (raport 10): jeden serwer Qwen3.5-4B, jedna konfiguracja, kilka seedów.
#   bash server/nt_t3.sh <port> <kwant: iq2m|iq3xxs|q3ks|q3km|iq2xxs|...> <serwer: stock|rb|rbpp> <nazwa> "<seedy>" [dodatkowe flagi harnessu]
#   SETS="test2026_v2" bash server/nt_t3.sh 8541 iq3xxs rb rbE "42 43" --essay-extend 2 --essay-topic-detect
set -u
cd ~/repo
. server/lib_eval.sh
PORT=$1 Q=$2 SV=$3 NAME=$4 SEEDS=$5
shift 5
D=$HOME/models/unsloth/Qwen3.5-4B-GGUF
declare -A F=([iq3xxs]=UD-IQ3_XXS [q3ks]=Q3_K_S [iq2m]=UD-IQ2_M [q3km]=Q3_K_M [iq2xxs]=UD-IQ2_XXS [q2kxl]=UD-Q2_K_XL [iq3s]=IQ3_S)
RBM=$'\n\nNa podstawie powyższych rozważań podaję ostateczną odpowiedź.\n'
SRV=(-m "$D/Qwen3.5-4B-${F[$Q]}.gguf" --mmproj "$D/mmproj-F16.gguf" -ub 4096 -b 4096 -c ${CTX:-98304} -np 8 --reasoning-format deepseek)
case $SV in
  rb) SRV+=(--reasoning-budget "${RB:-5000}" --reasoning-budget-message "$RBM") ;;
  rbpp) SRV+=(--reasoning-budget "${RB:-5000}" --reasoning-budget-message "$RBM" --presence-penalty 1.0) ;;
esac
serve "$PORT" "${SRV[@]}" || exit 1
for s in $SEEDS; do
  for ds in ${SETS:-test2024_v2 test2025_v2}; do
    run q35-4b-${Q}__nt3$NAME-s$s exams/$ds "$PORT" --parallel 4 --rag none --vision --think rozstrz,open,podaj,closed \
      --temperature 0.6 --top-p 0.95 --top-k 20 --max-tokens 8000 --kb-essay data/kb/kompendium.jsonl --seed "$s" "$@" &
  done
done
wait_runs
stop "$PORT"
echo NT_T3_DONE "$Q" "$SV" "$NAME"
