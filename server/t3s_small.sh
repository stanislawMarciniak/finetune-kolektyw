#!/usr/bin/env bash
# T3 z modelem < 0.97 GB (raport 16): Qwen3.5-2B (UD-IQ3_XXS / UD-IQ2_M) w harnessie T3 oraz ocena zagrożenia
# (SlayerLab bielik-1.5b sft2 — tylko pomiar, nie do zgłoszenia).
#   bash server/t3s_small.sh <faza> [seed]    fazy: q2b | slayer | bielik | q2b26
set -u
cd ~/repo
. server/lib_eval.sh
PH=$1 SEED=${2:-42}
M=$HOME/models
RBM=$'\n\nNa podstawie powyższych rozważań podaję ostateczną odpowiedź.\n'
Q_SRV="-ub 4096 -b 4096 -c 262144 -np 16 --reasoning-format deepseek --reasoning-budget 5000"
T3="--parallel 8 --vision --think rozstrz,open,podaj,closed --temperature 0.6 --top-p 0.95 --top-k 20 --max-tokens 8000 --kb-essay data/kb/kompendium.jsonl --essay-mode structured"
RAG="--rag bm25 --rag-types podaj,rozstrz,open --rag-k 3 --kb-rag data/kb/kb_all_notes.jsonl --kb-rag-k 1"
T2H="--parallel 8 --no-think-kwargs --temperature 0.0 --top-p 1.0 --top-k 1 --kb-essay data/kb/kompendium.jsonl $RAG --ocr"
BARE="--bare --parallel 8 --no-think-kwargs --temperature 0.0 --top-p 1.0 --top-k 1"
case $PH in
q2b)
  serve 8811 -m $M/unsloth/Qwen3.5-2B-GGUF/Qwen3.5-2B-UD-IQ3_XXS.gguf --mmproj $M/unsloth/Qwen3.5-2B-GGUF/mmproj-F16.gguf $Q_SRV --reasoning-budget-message "$RBM" || exit 1
  serve 8812 -m $M/unsloth/Qwen3.5-2B-GGUF/Qwen3.5-2B-UD-IQ2_M.gguf --mmproj $M/unsloth/Qwen3.5-2B-GGUF/mmproj-F16.gguf -ub 4096 -b 4096 -c 131072 -np 8 --reasoning-format deepseek --reasoning-budget 5000 --reasoning-budget-message "$RBM" || exit 1
  for ds in test2024_v2 test2025_v2; do
    run "q35-2b-iq3xxs__t3s-s$SEED" exams/$ds 8811 $T3 --rag none --seed $SEED &
    run "q35-2b-iq3xxs__t3srag-s$SEED" exams/$ds 8811 $T3 $RAG --seed $SEED &
    run "q35-2b-iq2m__t3s-s$SEED" exams/$ds 8812 $T3 --rag none --seed $SEED &
  done
  wait_runs; stop 8811 8812 ;;
q2b26)  # potwierdzenie: 2026 + drugi seed na 2024/2025; $3 = plik, $4 = nazwa, $5 = dodatkowe flagi (np. RAG)
  F=$3 N=$4 EXTRA=${5:-}
  serve 8811 -m "$F" --mmproj $M/unsloth/Qwen3.5-2B-GGUF/mmproj-F16.gguf $Q_SRV --reasoning-budget-message "$RBM" || exit 1
  run "q35-2b-${N}-s42" exams/test2026_v2 8811 $T3 --rag none $EXTRA --seed 42 &
  for ds in test2024_v2 test2025_v2; do run "q35-2b-${N}-s43" exams/$ds 8811 $T3 --rag none $EXTRA --seed 43 & done
  wait_runs; stop 8811 ;;
custom)  # $3 = plik, $4 = nazwa, $5 = port: 2024 + 2025, seed $SEED
  F=$3 N=$4 P=$5
  serve $P -m "$F" --mmproj $M/unsloth/Qwen3.5-2B-GGUF/mmproj-F16.gguf -ub 4096 -b 4096 -c 131072 -np 8 --reasoning-format deepseek --reasoning-budget 5000 --reasoning-budget-message "$RBM" || exit 1
  for ds in test2024_v2 test2025_v2; do run "q35-2b-${N}-s$SEED" exams/$ds $P $T3 --rag none --seed $SEED & done
  wait_runs; stop $P ;;
slayer)
  serve 8813 -m $M/SlayerLab/bielik-1.5b-v3-matura-history-sft2/sft2-IQ4_XS.gguf -c 131072 -np 16 || exit 1
  for ds in test2024_v2 test2025_v2 test2026_v2; do
    run "slayer-sft2-iq4xs__bare" exams/$ds 8813 $BARE &
    run "slayer-sft2-iq4xs__t2h" exams/$ds 8813 $T2H &
  done
  wait_runs; stop 8813 ;;
bielik)
  F=$M/speakleash/Bielik-1.5B-v3.0-Instruct-GGUF/Bielik-1.5B-v3.0-Instruct-Q4_K_M.gguf
  [ -f "$F" ] || ~/llama.cpp/build/bin/llama-quantize $M/speakleash/Bielik-1.5B-v3.0-Instruct-GGUF/Bielik-1.5B-v3.0-Instruct-fp16.gguf "$F" Q4_K_M > $L/t3s_bielik_quant.log 2>&1
  serve 8814 -m "$F" -c 131072 -np 16 || exit 1
  for ds in test2024_v2 test2025_v2; do run "bielik-1.5b-q4km__t2h" exams/$ds 8814 $T2H & done
  wait_runs; stop 8814 ;;
esac
echo "T3S_DONE $PH"
