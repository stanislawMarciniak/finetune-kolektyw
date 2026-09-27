#!/usr/bin/env bash
# T2 na Nebius H100: Gemma-4-12B pt + LoRA (train/sft_peft.py), z obrazami.
# Baza GGUF skonwertowana z tokenizerem -it (znaczniki tur jako tokeny specjalne, <turn|> kończy generowanie),
# szablon bez kanału myślenia (turns.jinja), zgodny z tym, co model widział w treningu.
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

nohup $BIN -m $P/gemma-4-12B-itok-Q4_K_M.gguf --lora $A/lora.gguf --mmproj $P/mmproj-gemma-4-12B-F16.gguf -ub 4096 -b 4096 \
  --chat-template-file $P/turns.jinja --host 127.0.0.1 --port 8086 -ngl 999 -c 65536 -np 8 --kv-unified --jinja \
  > $L/server_8086.log 2>&1 &
for i in $(seq 1 180); do curl -s localhost:8086/health | grep -q ok && break; sleep 2; done

SFT="--parallel 4 --vision --no-think-kwargs --temperature 0.3 --top-p 0.95 --top-k 64"
for ds in test2024_split test2025_split; do
  for v in fix careful_kb; do
    extra=""; [ $v = careful_kb ] && extra="--careful --kb-essay data/kb/kompendium.jsonl"
    out=runs/$ds/gemma4-12b-pt-sft__$v
    [ -f $out/answers.json ] || $PY harness/run_exam.py --exam exams/$ds --out $out --base-url http://127.0.0.1:8086/v1 \
      --rag none $SFT $extra > $L/run_gemmapt_${ds}_$v.log 2>&1 &
  done
done
wait_runs
tail -qn1 $L/run_gemmapt_*.log
pkill -f "port 8086"
echo EXP_GEMMAPT_DONE
