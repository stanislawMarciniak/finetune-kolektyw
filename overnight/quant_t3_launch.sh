#!/usr/bin/env bash
# Czeka na wolny VRAM na L40S i startuje sparowany A/B T3 (stock UD-IQ3_XXS + własne kwanty, identyczne flagi).
# ≥ 26 GB wolne: stock + IQ3_XXS-PL + IQ3_XXS-PL-E4K; ≥ 17.5 GB: stock + IQ3_XXS-PL (E4K dochodzi, gdy zwolni się ~9 GB).
# Nie startuje nowych przebiegów po DEADLINE_UTC (maszyna potrzebna rano do egzaminu).
set -u
W=$HOME/models/custom/qwen35-4b/work
O=$HOME/models/custom/qwen35-4b
S=$HOME/models/unsloth/Qwen3.5-4B-GGUF
DEADLINE_UTC=${DEADLINE_UTC:-04:30}
cd "$W"
free_mb() { nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1; }
late() { [ "$(date -u +%H:%M)" \> "$DEADLINE_UTC" ]; }
go() { (PORT0=$1 setsid nohup ./quant_t3_exam.sh 42 "$2" > "exam_$1.out" 2>&1 < /dev/null &); echo "$(date -u +%T) start $2 port $1"; sleep 90; }
started_pair=0
if [ -n "${E4K_FIRST:-}" ]; then  # E4K startuje od razu (starczy ~9 GB), potem para stock + PL
  go 8603 "iq3xxs-pl-e4k=$O/Qwen3.5-4B-IQ3_XXS-PL-E4K.gguf"
  while ! late; do
    [ "$(free_mb)" -ge 17500 ] && { go 8601 "stock-iq3xxs=$S/Qwen3.5-4B-UD-IQ3_XXS.gguf"; go 8602 "iq3xxs-pl=$O/Qwen3.5-4B-IQ3_XXS-PL.gguf"; exit 0; }
    sleep 30
  done
  exit 0
fi
while ! late; do
  f=$(free_mb)
  if [ "$started_pair" = 0 ] && [ "$f" -ge 26000 ]; then
    go 8601 "stock-iq3xxs=$S/Qwen3.5-4B-UD-IQ3_XXS.gguf"
    go 8602 "iq3xxs-pl=$O/Qwen3.5-4B-IQ3_XXS-PL.gguf"
    go 8603 "iq3xxs-pl-e4k=$O/Qwen3.5-4B-IQ3_XXS-PL-E4K.gguf"
    exit 0
  elif [ "$started_pair" = 0 ] && [ "$f" -ge 17500 ]; then
    go 8601 "stock-iq3xxs=$S/Qwen3.5-4B-UD-IQ3_XXS.gguf"
    go 8602 "iq3xxs-pl=$O/Qwen3.5-4B-IQ3_XXS-PL.gguf"
    started_pair=1
  elif [ "$started_pair" = 1 ] && [ "$f" -ge 9000 ]; then
    go 8603 "iq3xxs-pl-e4k=$O/Qwen3.5-4B-IQ3_XXS-PL-E4K.gguf"
    exit 0
  fi
  sleep 30
done
echo "$(date -u +%T) deadline reached, started_pair=$started_pair"
