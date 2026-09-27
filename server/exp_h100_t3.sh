#!/usr/bin/env bash
# T3 na Nebius H100: drabina rozmiaru w jednej konfiguracji — myślenie dla zadań krótkich, esej bez myślenia
# (myślenie w eseju i tak się urywało) z kompendium jako kontekstem, obrazy.
#   Qwen3.5-4B Q4_K_M (2.74 GB), UD-IQ3_XXS (1.95 GB), UD-IQ2_M (1.76 GB); Qwen3.5-2B Q4_K_M (1.28 GB)
set -u
wait_runs() {  # czeka na zadania w tle poza llama-server (serwer nigdy sam się nie kończy)
  for p in $(jobs -p); do ps -p "$p" -o args= | grep -q llama-server || wait "$p"; done
}
cd ~/repo
BIN=~/llama.cpp/build/bin/llama-server
PY=${PY:-~/venv-unsloth/bin/python}
L=~/logs
Q4=~/models/unsloth/Qwen3.5-4B-GGUF
Q2=~/models/unsloth/Qwen3.5-2B-GGUF

$PY - <<'EOF'
from huggingface_hub import hf_hub_download as d
import os
for r, fs in [("unsloth/Qwen3.5-4B-GGUF", ["Qwen3.5-4B-Q4_K_M.gguf", "Qwen3.5-4B-UD-IQ3_XXS.gguf", "Qwen3.5-4B-UD-IQ2_M.gguf", "mmproj-F16.gguf"]),
              ("unsloth/Qwen3.5-2B-GGUF", ["Qwen3.5-2B-Q4_K_M.gguf", "mmproj-F16.gguf"])]:
    for f in fs:
        d(r, f, local_dir=os.path.expanduser(f"~/models/{r}"))
EOF

serve() {  # port model mmproj
  nohup $BIN -m "$2" --mmproj "$3" -ub 4096 -b 4096 --host 127.0.0.1 --port "$1" -ngl 999 -c 98304 -np 8 --kv-unified --jinja \
    --reasoning-format deepseek > $L/server_$1.log 2>&1 &
  for i in $(seq 1 120); do curl -s "localhost:$1/health" | grep -q ok && return 0; sleep 2; done
  echo "server $1 failed"; return 1
}
T3="--parallel 4 --rag none --vision --think rozstrz,open,podaj,closed --temperature 1.0 --top-p 0.95 --top-k 20 --max-tokens 8000 \
  --kb-essay data/kb/kompendium.jsonl"
run() {  # name port
  for ds in test2024_split test2025_split; do
    out=runs/$ds/$1__t3cfg
    [ -f $out/answers.json ] || $PY harness/run_exam.py --exam exams/$ds --out $out --base-url http://127.0.0.1:$2/v1 $T3 \
      > $L/run_$1_$ds.log 2>&1 &
  done
  wait_runs
}
serve 8101 $Q4/Qwen3.5-4B-Q4_K_M.gguf $Q4/mmproj-F16.gguf
serve 8102 $Q4/Qwen3.5-4B-UD-IQ3_XXS.gguf $Q4/mmproj-F16.gguf
serve 8103 $Q4/Qwen3.5-4B-UD-IQ2_M.gguf $Q4/mmproj-F16.gguf
serve 8104 $Q2/Qwen3.5-2B-Q4_K_M.gguf $Q2/mmproj-F16.gguf
run q35-4b-q4 8101 & run q35-4b-iq3xxs 8102 & run q35-4b-iq2m 8103 & run q35-2b-q4 8104 &
wait_runs
tail -qn1 $L/run_q35-*_test202[45]_split.log
pkill -f "port 810[1-4]"
echo EXP_H100_T3_DONE
