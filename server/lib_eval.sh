# Wspólne funkcje skryptów ewaluacji na maszynach Nebius (source server/lib_eval.sh).
#   serve <port> <argumenty llama-server...>   uruchamia serwer w tle i czeka na /health
#   run <nazwa> <katalog egzaminu> <port> <argumenty harnessu...>   jeden przebieg (pomija gotowe)
#   stop <port...>   zatrzymuje serwery; wait_runs czeka na przebiegi w tle (nie na serwery)
BIN=${BIN:-$HOME/llama.cpp/build/bin/llama-server}
if [ -z "${PY:-}" ]; then
  PY=$HOME/venv-unsloth/bin/python
  [ -x "$PY" ] || PY=$HOME/venv-eval/bin/python
fi
L=${L:-$HOME/logs}
mkdir -p "$L"

wait_runs() {
  for p in $(jobs -p); do ps -p "$p" -o args= | grep -q llama-server || wait "$p"; done
}

serve() {  # z nadzorcą: Gemma 4 na H100 potrafi paść z „CUDA error: illegal instruction”, więc serwer wstaje sam
  local port=$1; shift
  nohup bash -c 'while true; do "$0" "$@"; echo "SUPERVISOR restart $(date +%T)"; sleep 2; done' \
    "$BIN" "$@" --host 127.0.0.1 --port "$port" -ngl 999 --kv-unified --jinja > "$L/server_$port.log" 2>&1 &
  for i in $(seq 1 240); do curl -s "localhost:$port/health" | grep -q ok && return 0; sleep 2; done
  echo "server $port failed"; tail -20 "$L/server_$port.log"; return 1
}

stop() {  # dwa razy: nadzorca mógłby zdążyć wskrzesić serwer
  for port in "$@"; do pkill -f "[-]-port $port( |$)"; done
  sleep 3
  for port in "$@"; do pkill -9 -f "[-]-port $port( |$)"; done
  sleep 1
}

run() {
  local name=$1 exam=$2 port=$3; shift 3
  local ds; ds=$(basename "$exam")
  local out=runs/$ds/$name
  if [ ! -f "$out/answers.json" ]; then
    "$PY" harness/run_exam.py --exam "$exam" --out "$out" --base-url "http://127.0.0.1:$port/v1" --name "$name" "$@" \
      > "$L/run_${name}_$ds.log" 2>&1
  fi
  echo "$(date +%T) $name $ds $(tail -1 "$L/run_${name}_$ds.log" 2>/dev/null)"
}
