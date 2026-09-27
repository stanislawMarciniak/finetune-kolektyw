#!/usr/bin/env bash
# T3: Qwen3.5-4B IQ3_XXS z myśleniem i obrazami, samodzielnie (serwer Qwen3.5 z mmproj zajmuje ~10 GB RAM; Forgehand ma 30 GB).
set -u
wait_runs() {  # czeka na zadania w tle poza llama-server (serwer nigdy sam się nie kończy)
  for p in $(jobs -p); do ps -p "$p" -o args= | grep -q llama-server || wait "$p"; done
}
cd /workspace/repo
BIN=/workspace/llama.cpp/build/bin/llama-server
N=/opt/conda/lib/python3.11/site-packages/nvidia
export LD_LIBRARY_PATH=$N/cuda_runtime/lib:$N/cublas/lib:${LD_LIBRARY_PATH:-}
Q=/scratch/models/unsloth/Qwen3.5-4B-GGUF
L=/workspace/logs

while pgrep -f "^bash server/exp_t3b\.sh" > /dev/null; do sleep 30; done
nohup $BIN -m $Q/Qwen3.5-4B-UD-IQ3_XXS.gguf --mmproj $Q/mmproj-F16.gguf -ub 4096 -b 4096 --host 127.0.0.1 --port 8081 -ngl 999 \
  -c 98304 -np 8 --kv-unified --jinja --reasoning-format deepseek > $L/server_8081.log 2>&1 &
for i in $(seq 1 120); do curl -s localhost:8081/health | grep -q ok && break; sleep 2; done
THINK="--vision --think essay,rozstrz,open,podaj,closed --temperature 1.0 --top-p 0.95 --top-k 20 --max-tokens 8000 --essay-max-tokens 12000"
for ds in test2024_split test2025_split; do
  python harness/run_exam.py --exam exams/$ds --out runs/$ds/q35-4b-iq3xxs-think__none --base-url http://127.0.0.1:8081/v1 \
    --parallel 4 --rag none $THINK > $L/run_q35-4b-iq3xxs-think_$ds.log 2>&1 &
done
wait_runs
tail -qn1 $L/run_q35-4b-iq3xxs-think_test202[45]_split.log
pkill -f "port 8081"
echo EXP_T3C_DONE
