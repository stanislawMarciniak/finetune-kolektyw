#!/usr/bin/env bash
# Diagnostyka Gemma-4-12B pt w llama.cpp: z obrazami (-ub 4096, 8 slotów, kv-unified) serwer pada z „illegal instruction”.
# Warianty: A) bez mmproj, 4 sloty, bez kv-unified; B) z mmproj, 1 slot. Tylko 2024 v2.
set -u
cd ~/repo
. server/lib_eval.sh
P=$HOME/models/gemma4-pt
TPL=$HOME/repo/train/templates/gemma4_turns.jinja
S="--no-think-kwargs --temperature 0.3 --top-p 0.95 --top-k 64"
nohup "$BIN" -m $P/gemma-4-12B-sft-Q4_K_M.gguf --chat-template-file $TPL -c 32768 -np 4 --host 127.0.0.1 --port 8211 -ngl 999 --jinja \
  > $L/server_8211.log 2>&1 &
for i in $(seq 1 120); do curl -s localhost:8211/health | grep -q ok && break; sleep 2; done
run gemma4-12b-pt-sft-merged__diagA exams/test2024_v2 8211 $S --parallel 4
stop 8211
nohup "$BIN" -m $P/gemma-4-12B-sft-Q4_K_M.gguf --mmproj $P/mmproj-gemma-4-12B-F16.gguf -ub 4096 -b 4096 --chat-template-file $TPL \
  -c 16384 -np 1 --host 127.0.0.1 --port 8212 -ngl 999 --jinja > $L/server_8212.log 2>&1 &
for i in $(seq 1 120); do curl -s localhost:8212/health | grep -q ok && break; sleep 2; done
run gemma4-12b-pt-sft-merged__diagB exams/test2024_v2 8212 $S --vision --parallel 1
stop 8212
grep -c "illegal" $L/server_8211.log $L/server_8212.log
echo DIAG_GEMMAPT_DONE
