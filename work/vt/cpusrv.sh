#!/usr/bin/env bash
# cpusrv.sh <port> <gguf>  -- CPU llama-server for tokenizer checks (stops previous one on that port)
cd ~/models/custom/qwen35-4b/work/vt
pid=$(ss -ltnp 2>/dev/null | grep "127.0.0.1:$1 " | grep -o "pid=[0-9]*" | cut -d= -f2)
[ -n "$pid" ] && kill $pid && sleep 2
CUDA_VISIBLE_DEVICES= setsid nohup ~/llama.cpp/build/bin/llama-server -m "$2" -ngl 0 -c 4096 -t 2 --host 127.0.0.1 --port $1 > srv_$1.log 2>&1 < /dev/null &
for i in $(seq 60); do curl -s localhost:$1/health | grep -q ok && echo up && exit 0; sleep 1; done; echo fail
