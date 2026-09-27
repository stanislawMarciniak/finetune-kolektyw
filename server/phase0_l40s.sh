#!/usr/bin/env bash
# Faza 0 na L40S: drabina rozmiaru T3 w jednej konfiguracji (paczki v2 ze znacznikami obrazów).
# Myślenie dla zadań krótkich, esej bez myślenia z kompendium jako kontekstem, obrazy.
set -u
cd ~/repo
PY=$HOME/venv-eval/bin/python
. server/lib_eval.sh
Q=$HOME/models/unsloth/Qwen3.5-4B-GGUF
Q2=$HOME/models/unsloth/Qwen3.5-2B-GGUF
SRV="-ub 4096 -b 4096 -c 98304 -np 8 --reasoning-format deepseek"
T3="--parallel 4 --rag none --vision --think rozstrz,open,podaj,closed --temperature 1.0 --top-p 0.95 --top-k 20 --max-tokens 8000 --kb-essay data/kb/kompendium.jsonl"

pair() {  # nazwa port: 2024 i 2025 równolegle na jednym serwerze
  run "$1" exams/test2024_v2 "$2" $T3 &
  run "$1" exams/test2025_v2 "$2" $T3 &
  wait_runs
}

serve 8101 -m $Q/Qwen3.5-4B-Q4_K_M.gguf --mmproj $Q/mmproj-F16.gguf $SRV
serve 8102 -m $Q/Qwen3.5-4B-UD-IQ3_XXS.gguf --mmproj $Q/mmproj-F16.gguf $SRV
pair q35-4b-q4__t3cfg 8101 &
pair q35-4b-iq3xxs__t3cfg 8102 &
wait_runs
stop 8101 8102
serve 8103 -m $Q/Qwen3.5-4B-UD-IQ2_M.gguf --mmproj $Q/mmproj-F16.gguf $SRV
serve 8104 -m $Q2/Qwen3.5-2B-Q4_K_M.gguf --mmproj $Q2/mmproj-F16.gguf $SRV
pair q35-4b-iq2m__t3cfg 8103 &
pair q35-2b-q4__t3cfg 8104 &
wait_runs
stop 8103 8104
echo PHASE0_L40S_DONE
