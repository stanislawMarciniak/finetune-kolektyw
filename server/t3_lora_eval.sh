#!/usr/bin/env bash
# T3 po treningu z maską myślenia (WS3): sonda z LoRA -> bramka think_gate -> (tylko gdy PASS) konfiguracja T3 na Q4_K_M i IQ3_XXS.
#   bash server/t3_lora_eval.sh ~/train/q35-4b-maskthink/lora.gguf
set -u
cd ~/repo
PY=${PY:-$HOME/venv-eval/bin/python}
. server/lib_eval.sh
LORA=$1
bash server/probe_t3.sh q35-4b-q4-maskthink__probe "$LORA"
$PY eval/think_gate.py check runs/probe60_v2/q35-4b-q4__probe runs/probe60_v2/q35-4b-q4-maskthink__probe | tee $L/think_gate.log
grep -q GATE_PASS $L/think_gate.log || { echo "bramka nie przepuściła adaptera"; exit 0; }
Q=$HOME/models/unsloth/Qwen3.5-4B-GGUF
SRV="-ub 4096 -b 4096 -c 98304 -np 8 --reasoning-format deepseek --lora $LORA"
T3="--parallel 4 --rag none --vision --think rozstrz,open,podaj,closed --temperature 1.0 --top-p 0.95 --top-k 20 --max-tokens 8000 --kb-essay data/kb/kompendium.jsonl"
serve 8141 -m $Q/Qwen3.5-4B-Q4_K_M.gguf --mmproj $Q/mmproj-F16.gguf $SRV
serve 8142 -m $Q/Qwen3.5-4B-UD-IQ3_XXS.gguf --mmproj $Q/mmproj-F16.gguf $SRV
for ds in test2024_v2 test2025_v2; do
  run q35-4b-q4-maskthink__t3cfg exams/$ds 8141 $T3 &
  run q35-4b-iq3xxs-maskthink__t3cfg exams/$ds 8142 $T3 &
done
wait_runs
stop 8141 8142
echo T3_LORA_DONE
