#!/usr/bin/env bash
# Test samych esejów (12 tematów z lat ubiegłych, exams/essays12_rag) na Nebius H100:
# wariant bazowy, --careful i --careful + kompendium (--kb-essay). Model: $1 = q35-4b | pllum-sft
set -u
wait_runs() {  # czeka na zadania w tle poza llama-server (serwer nigdy sam się nie kończy)
  for p in $(jobs -p); do ps -p "$p" -o args= | grep -q llama-server || wait "$p"; done
}
cd ~/repo
BIN=~/llama.cpp/build/bin/llama-server
PY=${PY:-~/venv-unsloth/bin/python}
L=~/logs
case "$1" in
q35-4b)
  port=8089; name=q35-4b-q4
  $PY -c "from huggingface_hub import hf_hub_download as d; [d('unsloth/Qwen3.5-4B-GGUF', f, local_dir='$HOME/models/unsloth/Qwen3.5-4B-GGUF') for f in ('Qwen3.5-4B-Q4_K_M.gguf',)]"
  srv=(-m ~/models/unsloth/Qwen3.5-4B-GGUF/Qwen3.5-4B-Q4_K_M.gguf)
  samp="--temperature 0.7 --top-p 0.8 --top-k 20" ;;
pllum-sft)
  port=8090; name=pllum-12b-base-sft
  srv=(-m ~/models/mradermacher/PLLuM-12B-base-2512-GGUF/PLLuM-12B-base-2512.Q4_K_M.gguf --lora ~/train/pllum-12b-base/lora.gguf
       --chat-template-file ~/train/pllum-12b-base/chat_template.jinja)
  samp="--no-think-kwargs --temperature 0.0 --top-p 1.0 --top-k 1" ;;
esac
nohup $BIN "${srv[@]}" --host 127.0.0.1 --port $port -ngl 999 -c 32768 -np 12 --kv-unified --jinja --reasoning-format deepseek \
  > $L/server_$port.log 2>&1 &
for i in $(seq 1 180); do curl -s localhost:$port/health | grep -q ok && break; sleep 2; done
for v in base careful careful_kb; do
  extra=""; [ $v != base ] && extra="--careful"; [ $v = careful_kb ] && extra="--careful --kb-essay data/kb/kompendium.jsonl"
  $PY harness/run_exam.py --exam exams/essays12_rag --out runs/essays12_rag/${name}__$v --base-url http://127.0.0.1:$port/v1 \
    --parallel 12 --rag none $samp $extra > $L/run_essay_${name}_$v.log 2>&1 &
done
wait_runs
tail -qn1 $L/run_essay_${name}_*.log
pkill -f "port $port"
echo EXP_ESSAY_DONE $1
