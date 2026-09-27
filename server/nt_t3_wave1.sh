#!/usr/bin/env bash
# T3 bez treningu (raport 10): limit myślenia --reasoning-budget 5000 vs stock przy temp. 0.6, s42, 2024+2025.
set -u
cd ~/repo
. server/lib_eval.sh
Q=$HOME/models/unsloth/Qwen3.5-4B-GGUF
SRV="-ub 4096 -b 4096 -c 98304 -np 8 --reasoning-format deepseek"
RBM=$'\n\nNa podstawie powyższych rozważań podaję ostateczną odpowiedź.\n'
T3="--parallel 4 --rag none --vision --think rozstrz,open,podaj,closed --temperature 0.6 --top-p 0.95 --top-k 20 --max-tokens 8000 --kb-essay data/kb/kompendium.jsonl --seed 42"
for i in $(seq 1 120); do [ -f $Q/Qwen3.5-4B-Q3_K_S.gguf ] && break; sleep 5; done
declare -A F=([iq3xxs]=UD-IQ3_XXS [q3ks]=Q3_K_S [iq2m]=UD-IQ2_M [q3km]=Q3_K_M)
declare -A P=([iq3xxs]=8501 [q3ks]=8502 [iq2m]=8503 [q3km]=8504)
declare -A PB=([iq3xxs]=8511 [q3ks]=8512 [iq2m]=8513)
for q in iq3xxs q3ks iq2m q3km; do
  serve ${P[$q]} -m $Q/Qwen3.5-4B-${F[$q]}.gguf --mmproj $Q/mmproj-F16.gguf $SRV --reasoning-budget 5000 --reasoning-budget-message "$RBM"
done
for q in iq3xxs q3ks iq2m; do
  serve ${PB[$q]} -m $Q/Qwen3.5-4B-${F[$q]}.gguf --mmproj $Q/mmproj-F16.gguf $SRV
done
for ds in test2024_v2 test2025_v2; do
  for q in iq3xxs q3ks iq2m q3km; do run q35-4b-${q}__nt3rb-s42 exams/$ds ${P[$q]} $T3 & done
  for q in iq3xxs q3ks iq2m; do run q35-4b-${q}__nt3t06-s42 exams/$ds ${PB[$q]} $T3 & done
done
wait_runs
stop 8501 8502 8503 8504 8511 8512 8513
echo NT_T3_WAVE1_DONE
