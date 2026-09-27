#!/usr/bin/env bash
# Forgehand L40S: T3 tuned (final_configs) z plikiem MIX, esej structured, seed 43, arkusz 2026 (drugi seed 2026; raport 10c).
#   bash server/fh_mix_s43.sh [exam...]   (domyślnie test2026_v2)
# Jeden llama-server z obrazami naraz — 32 GB RAM, dwa serwery Qwen z mmproj wywracały montaż /workspace.
set -u
cd /scratch/repo
N=/opt/conda/lib/python3.11/site-packages/nvidia
LB=${LB:-/scratch/llama-81bc6b8}
export LD_LIBRARY_PATH=$LB:$N/cuda_runtime/lib:$N/cublas/lib:${LD_LIBRARY_PATH:-}
BIN=$LB/llama-server PY=/scratch/.venv/bin/python L=/scratch/logs
. server/lib_eval.sh
M=/scratch/models
NAME=q35-4b-q2-iq2mpl-e4k-mix__struct2-s43-2026-fh
serve 8331 -m $M/custom/qwen35-4b/Qwen3.5-4B-IQ2_M-PL-E4K-MIX.gguf --mmproj $M/unsloth/Qwen3.5-4B-GGUF/mmproj-F16.gguf \
  -ub 4096 -b 4096 -c 98304 -np 8 --reasoning-format deepseek --reasoning-budget 5000 \
  --reasoning-budget-message $'\n\nNa podstawie powyższych rozważań podaję ostateczną odpowiedź.\n' || exit 1
for ds in ${@:-test2026_v2}; do
  run $NAME exams/$ds 8331 --parallel 8 --rag none --vision --think rozstrz,open,podaj,closed --temperature 0.6 \
    --top-p 0.95 --top-k 20 --max-tokens 8000 --kb-essay data/kb/kompendium.jsonl --essay-mode structured --seed 43
done
stop 8331
echo FH_MIX_S43_DONE
