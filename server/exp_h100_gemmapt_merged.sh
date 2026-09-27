#!/usr/bin/env bash
# T2: Gemma-4-12B pt z LoRA scaloną w wagi (runtime LoRA w llama.cpp psuje Gemmę 4 przy -ub 4096 / wielu slotach:
# powtarzany <unused49>, potem błąd CUDA). Scalenie w BF16 -> Q4_K_M, potem ewaluacja 2024/2025 z obrazami.
set -u
wait_runs() {  # czeka na zadania w tle poza llama-server (serwer nigdy sam się nie kończy)
  for p in $(jobs -p); do ps -p "$p" -o args= | grep -q llama-server || wait "$p"; done
}
cd ~/repo
B=~/llama.cpp/build/bin
PY=${PY:-~/venv-unsloth/bin/python}
L=~/logs
P=~/models/gemma4-pt
A=~/train/gemma4-12b-pt

if [ ! -f $P/gemma-4-12B-sft-Q4_K_M.gguf ]; then
  [ -f $P/gemma-4-12B-itok-BF16.gguf ] || ~/venv-hf/bin/python ~/llama.cpp/convert_hf_to_gguf.py ~/models/gemma4-pt-src \
    --outtype bf16 --outfile $P/gemma-4-12B-itok-BF16.gguf
  $B/llama-export-lora -m $P/gemma-4-12B-itok-BF16.gguf --lora $A/lora.gguf -o $P/gemma-4-12B-sft-BF16.gguf
  $B/llama-quantize $P/gemma-4-12B-sft-BF16.gguf $P/gemma-4-12B-sft-Q4_K_M.gguf Q4_K_M
  rm -f $P/gemma-4-12B-sft-BF16.gguf
fi
ls -la $P/gemma-4-12B-sft-Q4_K_M.gguf || exit 1

nohup $B/llama-server -m $P/gemma-4-12B-sft-Q4_K_M.gguf --mmproj $P/mmproj-gemma-4-12B-F16.gguf -ub 4096 -b 4096 \
  --chat-template-file $P/turns.jinja --host 127.0.0.1 --port 8086 -ngl 999 -c 65536 -np 8 --kv-unified --jinja \
  > $L/server_8086.log 2>&1 &
for i in $(seq 1 180); do curl -s localhost:8086/health | grep -q ok && break; sleep 2; done

SFT="--parallel 4 --vision --no-think-kwargs --temperature 0.3 --top-p 0.95 --top-k 64"
for ds in test2024_split test2025_split; do
  out=runs/$ds/gemma4-12b-pt-sft__merged
  [ -f $out/answers.json ] || $PY harness/run_exam.py --exam exams/$ds --out $out --base-url http://127.0.0.1:8086/v1 \
    --rag none $SFT > $L/run_gemmapt_merged_$ds.log 2>&1 &
done
wait_runs
tail -qn1 $L/run_gemmapt_merged_*.log
pkill -f "[-]-port 8086"
echo EXP_GEMMAPT_MERGED_DONE
