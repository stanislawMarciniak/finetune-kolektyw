#!/usr/bin/env bash
# Eksperyment RAG (HyDE pisane przez ten sam model, bramkowane typem zadania) dla kandydatów T3 na arkuszach 2024 i 2025.
# Wyniki: /workspace/repo/runs/<zbiór>/<model>__<wariant>/{answers.json,debug.jsonl}
set -u
wait_runs() {  # czeka na zadania w tle poza llama-server (serwer nigdy sam się nie kończy)
  for p in $(jobs -p); do ps -p "$p" -o args= | grep -q llama-server || wait "$p"; done
}
cd /workspace/repo
BIN=/workspace/llama.cpp/build/bin/llama-server
M=/scratch/models

serve() {  # port model mmproj
  local port=$1 model=$2 mmproj=${3:-}
  local extra=""; [ -n "$mmproj" ] && extra="--mmproj $mmproj -ub 4096 -b 4096"
  nohup $BIN -m "$model" $extra --host 127.0.0.1 --port "$port" -ngl 999 -c 98304 -np 6 --kv-unified --jinja \
    --reasoning-format deepseek > /workspace/logs/server_$port.log 2>&1 &
  for i in $(seq 1 120); do curl -s "localhost:$port/health" | grep -q ok && return 0; sleep 2; done
  echo "server $port failed"; tail -20 /workspace/logs/server_$port.log; return 1
}

run_model() {  # name port think_args extra_args...
  local name=$1 port=$2; shift 2
  for ds in test2024_split test2025_split; do
    for variant in none hyde_podaj hyde_all; do
      case $variant in
        none) rag="--rag none" ;;
        hyde_podaj) rag="--rag hyde --rag-types podaj" ;;
        hyde_all) rag="--rag hyde --rag-types podaj,open,rozstrz,essay" ;;
      esac
      out=runs/$ds/${name}__$variant
      [ -f "$out/answers.json" ] && continue
      python harness/run_exam.py --exam exams/$ds --out "$out" --base-url "http://127.0.0.1:$port/v1" --parallel 6 $rag "$@" \
        > "/workspace/logs/run_${name}_${ds}_${variant}.log" 2>&1
      tail -1 "/workspace/logs/run_${name}_${ds}_${variant}.log"
    done
  done
}

serve 8081 $M/unsloth/Qwen3.5-4B-GGUF/Qwen3.5-4B-Q4_K_M.gguf $M/unsloth/Qwen3.5-4B-GGUF/mmproj-F16.gguf
serve 8082 $M/unsloth/Qwen3.5-2B-GGUF/Qwen3.5-2B-Q4_K_M.gguf $M/unsloth/Qwen3.5-2B-GGUF/mmproj-F16.gguf
( run_model q35-4b-think 8081 --vision --think essay,rozstrz,open,podaj,closed --temperature 1.0 --top-p 0.95 --top-k 20 ) &
( run_model q35-2b 8082 --vision --temperature 0.7 --top-p 0.8 --top-k 20
  pkill -f "port 8082"; sleep 3
  serve 8082 $M/second-state/Bielik-1.5B-v3.0-Instruct-GGUF/Bielik-1.5B-v3.0-Instruct-Q8_0.gguf
  run_model bielik-1.5b 8082 --no-think-kwargs --temperature 0.0 --top-p 1.0 --top-k 1 ) &
wait_runs
pkill -f llama-server
echo EXP_RAG_DONE
