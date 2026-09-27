#!/usr/bin/env bash
# T3: jak nisko można skwantyzować Qwen3.5-4B (myślenie + obrazy + powtórka bez myślenia przy urwaniu), 2024 i 2025.
# Najpierw pobiera modele potrzebne do dalszych ewaluacji. Wyniki: runs/<zbiór>/<model>__none
set -u
wait_runs() {  # czeka na zadania w tle poza llama-server (serwer nigdy sam się nie kończy)
  for p in $(jobs -p); do ps -p "$p" -o args= | grep -q llama-server || wait "$p"; done
}
cd ${REPO:-/workspace/repo}
BIN=${BIN:-/workspace/llama.cpp/build/bin/llama-server}
N=/opt/conda/lib/python3.11/site-packages/nvidia
export LD_LIBRARY_PATH=$N/cuda_runtime/lib:$N/cublas/lib:${LD_LIBRARY_PATH:-}
M=${M:-/scratch/models}
mkdir -p $M ${LOGS:-/workspace/logs}

python - <<'EOF'
from huggingface_hub import hf_hub_download as d
for r, fs in [("unsloth/Qwen3.5-4B-GGUF", ["Qwen3.5-4B-UD-IQ3_XXS.gguf", "Qwen3.5-4B-UD-IQ2_M.gguf", "Qwen3.5-4B-Q4_K_M.gguf", "mmproj-F16.gguf"]),
              ("unsloth/Qwen3.5-2B-GGUF", ["Qwen3.5-2B-Q4_K_M.gguf", "mmproj-F16.gguf"]),
              ("second-state/Bielik-1.5B-v3.0-Instruct-GGUF", ["Bielik-1.5B-v3.0-Instruct-Q4_K_M.gguf", "Bielik-1.5B-v3.0-Instruct-Q8_0.gguf"]),
              ("mradermacher/PLLuM-12B-base-2512-GGUF", ["PLLuM-12B-base-2512.Q4_K_M.gguf"]),
              ("google/gemma-4-12B-it-qat-q4_0-gguf", ["gemma-4-12b-it-qat-q4_0.gguf", "mmproj-gemma-4-12b-it-qat-q4_0.gguf"])]:
    for f in fs:
        print(d(r, f, local_dir=f"/scratch/models/{r}"), flush=True)
EOF

serve() {  # port model mmproj
  local port=$1 model=$2 mmproj=${3:-}
  local extra=""; [ -n "$mmproj" ] && extra="--mmproj $mmproj -ub 4096 -b 4096"
  nohup $BIN -m "$model" $extra --host 127.0.0.1 --port "$port" -ngl 999 -c 131072 -np 8 --kv-unified --jinja \
    --reasoning-format deepseek > ${LOGS:-/workspace/logs}/server_$port.log 2>&1 &
  for i in $(seq 1 120); do curl -s "localhost:$port/health" | grep -q ok && return 0; sleep 2; done
  echo "server $port failed"; tail -20 ${LOGS:-/workspace/logs}/server_$port.log; return 1
}

THINK="--vision --think essay,rozstrz,open,podaj,closed --temperature 1.0 --top-p 0.95 --top-k 20 --max-tokens 8000 --essay-max-tokens 12000"
run() {  # name port
  for ds in test2024_split test2025_split; do
    out=runs/$ds/$1__none
    [ -f "$out/answers.json" ] || python harness/run_exam.py --exam exams/$ds --out "$out" --base-url "http://127.0.0.1:$2/v1" \
      --parallel 4 --rag none $THINK > "${LOGS:-/workspace/logs}/run_$1_$ds.log" 2>&1 &
  done
  wait_runs
  tail -qn1 ${LOGS:-/workspace/logs}/run_$1_test202[45]_split.log
}

Q=$M/unsloth/Qwen3.5-4B-GGUF
serve 8081 $Q/Qwen3.5-4B-UD-IQ3_XXS.gguf $Q/mmproj-F16.gguf
serve 8082 $Q/Qwen3.5-4B-UD-IQ2_M.gguf $Q/mmproj-F16.gguf
run q35-4b-iq3xxs-think 8081 &
run q35-4b-iq2m-think 8082 &
wait_runs
pkill -f "port 8082"; sleep 3
serve 8082 $Q/Qwen3.5-4B-Q4_K_M.gguf $Q/mmproj-F16.gguf
run q35-4b-q4-think-fb 8082
pkill -f llama-server
echo EXP_T3_DONE
