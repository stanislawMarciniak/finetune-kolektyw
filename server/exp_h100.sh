#!/usr/bin/env bash
# Kolejka na Nebius H100 (ścieżki z server/NEBIUS.md):
#   T2: Gemma-4-12B pt + LoRA (train/sft_peft.py) na 2024 i 2025, z obrazami;
#   T1: Gemma-4-12B-it QAT, docelowa konfiguracja (myślenie, obrazy, powtórka przy urwaniu, poprawka eseju) na 2024–2026 i mocku.
# Wyniki: ~/repo/runs/<zbiór>/<przebieg>; logi ~/logs
set -u
wait_runs() {  # czeka na zadania w tle poza llama-server (serwer nigdy sam się nie kończy)
  for p in $(jobs -p); do ps -p "$p" -o args= | grep -q llama-server || wait "$p"; done
}
cd ~/repo
BIN=~/llama.cpp/build/bin/llama-server
PY=${PY:-~/venv-unsloth/bin/python}
L=~/logs
P=~/models/gemma4-pt
A=~/train/gemma4-12b-pt

serve() {  # port ctx np model args...
  local port=$1 ctx=$2 np=$3 model=$4; shift 4
  nohup $BIN -m "$model" "$@" --host 127.0.0.1 --port "$port" -ngl 999 -c "$ctx" -np "$np" --kv-unified --jinja \
    --reasoning-format deepseek > $L/server_$port.log 2>&1 &
  for i in $(seq 1 180); do curl -s "localhost:$port/health" | grep -q ok && return 0; sleep 2; done
  echo "server $port failed"; tail -20 $L/server_$port.log; return 1
}

run() {  # exam_dir name port args...
  local exam=$1 name=$2 port=$3; shift 3
  local ds; ds=$(basename "$exam")
  [ "$ds" = mock-2023 ] && ds=mock-2023
  local out=runs/$ds/$name
  [ -f "$out/answers.json" ] || $PY harness/run_exam.py --exam "$exam" --out "$out" --base-url "http://127.0.0.1:$port/v1" "$@" \
    > "$L/run_${name}_$ds.log" 2>&1
  tail -1 "$L/run_${name}_$ds.log"
}

# T1 od razu (nie czeka na trening)
Q=~/models/google/gemma-4-12B-it-qat-q4_0-gguf
serve 8087 131072 8 $Q/gemma-4-12b-it-qat-q4_0.gguf --mmproj $Q/mmproj-gemma-4-12b-it-qat-q4_0.gguf -ub 4096 -b 4096
T1="--parallel 4 --rag none --vision --think essay,rozstrz,open,podaj,closed --temperature 1.0 --top-p 0.95 --top-k 64"
( for e in exams/test2024_split exams/test2025_split exams/test2026_split assets/mock-2023; do
    run $e gemma4-qat-t1final 8087 $T1 &
  done; wait_runs; echo T1_DONE ) &

# T2: czekamy na adapter i bazę GGUF
until [ -f $A/adapter/adapter_model.safetensors ] && grep -q CONVERT_DONE $L/convert_gemma_pt.log 2>/dev/null; do sleep 30; done
[ -f $A/lora.gguf ] || ~/venv-hf/bin/python ~/llama.cpp/convert_lora_to_gguf.py $A/adapter --base-model-id google/gemma-4-12B \
  --outtype f16 --outfile $A/lora.gguf > $L/convert_lora_gemma_pt.log 2>&1
ls -la $A/lora.gguf || { tail -20 $L/convert_lora_gemma_pt.log; exit 1; }
serve 8086 65536 8 $P/gemma-4-12B-Q4_K_M.gguf --lora $A/lora.gguf --mmproj $P/mmproj-gemma-4-12B-F16.gguf -ub 4096 -b 4096 \
  --chat-template-file $A/adapter/chat_template.jinja
SFT="--parallel 4 --vision --temperature 0.3 --top-p 0.95 --top-k 64"
run exams/test2024_split gemma4-12b-pt-sft__none 8086 --rag none $SFT &
run exams/test2025_split gemma4-12b-pt-sft__none 8086 --rag none $SFT &
wait_runs
echo EXP_H100_DONE
