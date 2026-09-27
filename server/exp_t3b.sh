#!/usr/bin/env bash
# T3, powtórka po awarii OOM: Qwen3.5-4B IQ3_XXS i IQ2_M oraz Qwen3.5-2B Q4_K_M, wszystkie z myśleniem i obrazami.
# Startuje dopiero po zakończeniu exp_t3.sh i exp_lora.sh (Forgehand ma 30 GB RAM; więcej niż 3 serwery = OOM).
set -u
wait_runs() {  # czeka na zadania w tle poza llama-server (serwer nigdy sam się nie kończy)
  for p in $(jobs -p); do ps -p "$p" -o args= | grep -q llama-server || wait "$p"; done
}
cd /workspace/repo
BIN=/workspace/llama.cpp/build/bin/llama-server
N=/opt/conda/lib/python3.11/site-packages/nvidia
export LD_LIBRARY_PATH=$N/cuda_runtime/lib:$N/cublas/lib:${LD_LIBRARY_PATH:-}
M=/scratch/models
L=/workspace/logs

while pgrep -f "^bash server/exp_(t3|lora)\.sh" > /dev/null; do sleep 30; done

serve() {  # port model mmproj
  nohup $BIN -m "$2" --mmproj "$3" -ub 4096 -b 4096 --host 127.0.0.1 --port "$1" -ngl 999 -c 98304 -np 6 --kv-unified --jinja \
    --reasoning-format deepseek > $L/server_$1.log 2>&1 &
  for i in $(seq 1 120); do curl -s "localhost:$1/health" | grep -q ok && return 0; sleep 2; done
  echo "server $1 failed"; tail -20 $L/server_$1.log; return 1
}

THINK="--vision --think essay,rozstrz,open,podaj,closed --temperature 1.0 --top-p 0.95 --top-k 20 --max-tokens 8000 --essay-max-tokens 12000"
run() {  # name port
  for ds in test2024_split test2025_split; do
    out=runs/$ds/$1__none
    [ -f "$out/answers.json" ] || python harness/run_exam.py --exam exams/$ds --out "$out" --base-url "http://127.0.0.1:$2/v1" \
      --parallel 3 --rag none $THINK > "$L/run_$1_$ds.log" 2>&1 &
  done
  wait_runs
  tail -qn1 $L/run_$1_test202[45]_split.log
}

Q=$M/unsloth/Qwen3.5-4B-GGUF
serve 8081 $Q/Qwen3.5-4B-UD-IQ3_XXS.gguf $Q/mmproj-F16.gguf
serve 8082 $Q/Qwen3.5-4B-UD-IQ2_M.gguf $Q/mmproj-F16.gguf
serve 8083 $M/unsloth/Qwen3.5-2B-GGUF/Qwen3.5-2B-Q4_K_M.gguf $M/unsloth/Qwen3.5-2B-GGUF/mmproj-F16.gguf
run q35-4b-iq3xxs-think 8081 &
run q35-4b-iq2m-think 8082 &
run q35-2b-think 8083 &
wait_runs
pkill -f "port 808[123]"
echo EXP_T3B_DONE
