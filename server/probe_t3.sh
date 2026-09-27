#!/usr/bin/env bash
# Sonda ochrony myślenia (WS3): 60 zadań (exams/probe60_v2) w konfiguracji T3 na Qwen3.5-4B Q4_K_M, bez LoRA albo z LoRA.
#   bash server/probe_t3.sh q35-4b-q4__probe                          # przed treningiem
#   bash server/probe_t3.sh q35-4b-q4-maskthink__probe ~/train/q35-4b-maskthink/lora.gguf
# Potem: python eval/think_gate.py check runs/probe60_v2/<przed> runs/probe60_v2/<po>
set -u
cd ~/repo
PY=${PY:-$HOME/venv-eval/bin/python}
. server/lib_eval.sh
NAME=$1
LORA=${2:-}
Q=$HOME/models/unsloth/Qwen3.5-4B-GGUF
EXTRA=""
[ -n "$LORA" ] && EXTRA="--lora $LORA"
serve 8121 -m $Q/Qwen3.5-4B-Q4_K_M.gguf --mmproj $Q/mmproj-F16.gguf $EXTRA -ub 4096 -b 4096 -c 98304 -np 8 --reasoning-format deepseek
run "$NAME" exams/probe60_v2 8121 --parallel 8 --rag none --vision --think rozstrz,open,podaj,closed --temperature 1.0 \
  --top-p 0.95 --top-k 20 --max-tokens 8000 --kb-essay data/kb/kompendium.jsonl
stop 8121
echo "PROBE_DONE $NAME"
