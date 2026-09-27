#!/usr/bin/env bash
# Ewaluacja adapterów LoRA z $T/<nazwa>/lora.gguf na 2024 i 2025.
#   server/exp_lora.sh bielik / q35-2b   # T3
#   CTX=32768 NP=4 server/exp_lora.sh pllum   # T2
# Ścieżki (Forgehand domyślnie) nadpisuje się zmiennymi REPO, BIN, M, T, LOGS.
# Wyniki: runs/<zbiór>/<nazwa>-sft__<wariant>
set -u
wait_runs() {  # czeka na zadania w tle poza llama-server (serwer nigdy sam się nie kończy)
  for p in $(jobs -p); do ps -p "$p" -o args= | grep -q llama-server || wait "$p"; done
}
cd ${REPO:-/workspace/repo}
BIN=${BIN:-/workspace/llama.cpp/build/bin/llama-server}
N=/opt/conda/lib/python3.11/site-packages/nvidia
export LD_LIBRARY_PATH=$N/cuda_runtime/lib:$N/cublas/lib:${LD_LIBRARY_PATH:-}
M=${M:-/scratch/models}
T=${T:-/workspace/train}

serve() {  # port model lora extra...
  local port=$1 model=$2 lora=$3; shift 3
  nohup $BIN -m "$model" --lora "$lora" "$@" --host 127.0.0.1 --port "$port" -ngl 999 -c ${CTX:-65536} -np ${NP:-8} --kv-unified --jinja \
    > ${LOGS:-/workspace/logs}/server_$port.log 2>&1 &
  for i in $(seq 1 150); do curl -s "localhost:$port/health" | grep -q ok && return 0; sleep 2; done
  echo "server $port failed"; tail -20 ${LOGS:-/workspace/logs}/server_$port.log; return 1
}

run() {  # name port variant args...
  local name=$1 port=$2 variant=$3; shift 3
  local rag="--rag none"
  case $variant in
    hyde_podaj) rag="--rag hyde --rag-types podaj" ;;
    hyde_all) rag="--rag hyde --rag-types podaj,open,rozstrz,essay" ;;
  esac
  for ds in test2024_split test2025_split; do
    out=runs/$ds/${name}__$variant
    [ -f "$out/answers.json" ] || python harness/run_exam.py --exam exams/$ds --out "$out" --base-url "http://127.0.0.1:$port/v1" \
      --parallel 4 $rag "$@" > "${LOGS:-/workspace/logs}/run_${name}_${ds}_$variant.log" 2>&1 &
  done
  wait_runs
  tail -qn1 ${LOGS:-/workspace/logs}/run_${name}_test202[45]_split_$variant.log
}

GREEDY="--no-think-kwargs --temperature 0.0 --top-p 1.0 --top-k 1"
case "$1" in
bielik)
    serve 8083 $M/second-state/Bielik-1.5B-v3.0-Instruct-GGUF/Bielik-1.5B-v3.0-Instruct-Q4_K_M.gguf $T/bielik-1.5b/lora.gguf
    run bielik-1.5b-q4-sft 8083 none $GREEDY &
    run bielik-1.5b-q4-sft 8083 hyde_all $GREEDY &
    wait_runs
    pkill -f "port 8083"
    ;;
q35-2b)
    Q=$M/unsloth/Qwen3.5-2B-GGUF
    serve 8084 $Q/Qwen3.5-2B-Q4_K_M.gguf $T/q35-2b/lora.gguf --mmproj $Q/mmproj-F16.gguf -ub 4096 -b 4096
    run q35-2b-sft 8084 none --vision --temperature 0.7 --top-p 0.8 --top-k 20 &
    run q35-2b-sft 8084 hyde_all --vision --temperature 0.7 --top-p 0.8 --top-k 20 &
    wait_runs
    pkill -f "port 8084"
    ;;
pllum)
    serve 8085 $M/mradermacher/PLLuM-12B-base-2512-GGUF/PLLuM-12B-base-2512.Q4_K_M.gguf $T/pllum-12b-base/lora.gguf \
        --chat-template-file $T/pllum-12b-base/chat_template.jinja
    run pllum-12b-base-sft 8085 none $GREEDY
    run pllum-12b-base-sft 8085 hyde_all $GREEDY
    pkill -f "port 8085"
    ;;
esac
echo "EXP_LORA_DONE $1"
