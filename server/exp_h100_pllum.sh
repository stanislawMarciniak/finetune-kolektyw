#!/usr/bin/env bash
# T2 na Nebius H100: PLLuM-12B-base + LoRA z harnessem po poprawce eseju (≥ 300 wyrazów, numer tematu), bez RAG i z HyDE.
set -u
wait_runs() {  # czeka na zadania w tle poza llama-server (serwer nigdy sam się nie kończy)
  for p in $(jobs -p); do ps -p "$p" -o args= | grep -q llama-server || wait "$p"; done
}
cd ~/repo
BIN=~/llama.cpp/build/bin/llama-server
PY=${PY:-~/venv-unsloth/bin/python}
L=~/logs
T=~/train/pllum-12b-base

nohup $BIN -m ~/models/mradermacher/PLLuM-12B-base-2512-GGUF/PLLuM-12B-base-2512.Q4_K_M.gguf --lora $T/lora.gguf \
  --chat-template-file $T/chat_template.jinja --host 127.0.0.1 --port 8088 -ngl 999 -c 65536 -np 8 --kv-unified --jinja \
  > $L/server_8088.log 2>&1 &
for i in $(seq 1 180); do curl -s localhost:8088/health | grep -q ok && break; sleep 2; done

GREEDY="--no-think-kwargs --temperature 0.0 --top-p 1.0 --top-k 1 --parallel 4"
for ds in test2024_split test2025_split; do
  for v in fix hyde_all; do
    rag="--rag none"; [ $v = hyde_all ] && rag="--rag hyde --rag-types podaj,open,rozstrz,essay"
    out=runs/$ds/pllum-12b-base-sft__$v
    [ -f $out/answers.json ] || $PY harness/run_exam.py --exam exams/$ds --out $out --base-url http://127.0.0.1:8088/v1 $rag $GREEDY \
      > $L/run_pllum_${ds}_$v.log 2>&1 &
  done
done
wait_runs
tail -qn1 $L/run_pllum_*.log
pkill -f "port 8088"
echo EXP_PLLUM_DONE
