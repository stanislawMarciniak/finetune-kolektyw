#!/usr/bin/env bash
# repro.sh <label> <model gguf (względem ~/models)> <tries> [dodatkowe flagi llama-server]
# Serwer bez nadzorcy (awaria = koniec procesu), flagi jak T3 w final_configs.json.
# Env: PORT (8771), MMPROJ, BASEFLAGS, SYNC=<n> (czekaj, aż n serwerów wstanie, i strzelaj razem), ENVX (np. GGML_CUDA_DISABLE_GRAPHS=1)
set -u
LABEL=$1 MODEL=$2 TRIES=$3; shift 3
PORT=${PORT:-8771}
MMPROJ=${MMPROJ:-unsloth/Qwen3.5-4B-GGUF/mmproj-F16.gguf}
BASEFLAGS=${BASEFLAGS:--ub 4096 -b 4096 -c 98304 -np 8 --reasoning-format deepseek}
BIN=$HOME/llama.cpp/build/bin/llama-server
D=$HOME/repo/work/illegal; mkdir -p $D/logs $D/sync
cd ~/repo
for t in $(seq 1 $TRIES); do
  LOG=$D/logs/${LABEL}_try$t.log
  env ${ENVX:-X=1} $BIN -m $HOME/models/$MODEL --mmproj $HOME/models/$MMPROJ $BASEFLAGS "$@" \
    --host 127.0.0.1 --port $PORT -ngl 999 --kv-unified --jinja > $LOG 2>&1 &
  SP=$!
  for i in $(seq 1 180); do curl -s localhost:$PORT/health | grep -q ok && break; kill -0 $SP 2>/dev/null || break; sleep 1; done
  if [ -n "${SYNC:-}" ]; then
    touch $D/sync/t${t}_$PORT
    for i in $(seq 1 300); do [ $(ls $D/sync/t${t}_* 2>/dev/null | wc -l) -ge $SYNC ] && break; sleep 0.2; done
  fi
  OUT=$(python3 $D/img_client.py http://127.0.0.1:$PORT/v1 8 assets/mock-2023 exams/test2024_v2:10 2>&1 | tail -3 | tr '\n' ' ')
  if kill -0 $SP 2>/dev/null; then alive=alive; else alive=DEAD; fi
  echo "$(date +%T) $LABEL try$t server=$alive illegal=$(grep -ci 'illegal' $LOG) cudaerr=$(grep -c 'CUDA error' $LOG) | $OUT"
  if [ -n "${SYNC:-}" ]; then
    touch $D/sync/done${t}_$PORT
    for i in $(seq 1 600); do [ $(ls $D/sync/done${t}_* 2>/dev/null | wc -l) -ge $SYNC ] && break; sleep 0.5; done
  fi
  kill $SP 2>/dev/null; sleep 2; kill -9 $SP 2>/dev/null; wait $SP 2>/dev/null
done
