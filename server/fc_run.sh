#!/usr/bin/env bash
# Raport 17: recenzent faktów na odpowiedziach istniejących przebiegów (--answer-from), tylko eseje i otwarte.
#   bash server/fc_run.sh <port> <nazwa wariantu> <przebieg bazowy> "<zbiory>" <argumenty harnessu...>
# Wynik: runs/<zbiór>/<przebieg bazowy>__fc<wariant>/ (reszta zadań scalona z bazy).
# KINDS=essay ogranicza zadania (domyślnie essay,podaj,rozstrz,open).
set -u
PORT=$1 VAR=$2 BASE=$3 SETS=$4; shift 4
cd ~/repo
. server/lib_eval.sh
for ds in $SETS; do
  src=runs/$ds/$BASE
  ids=$(python3 -c "import json; print(','.join(r['id'] for r in map(json.loads, open('$src/debug.jsonl')) if r['kind'] in '${KINDS:-essay,podaj,rozstrz,open}'.split(',')))")
  name=${BASE}__fc$VAR
  [ -f runs/$ds/$name/answers.json ] && continue
  $PY harness/run_exam.py --exam exams/$ds --out runs/$ds/$name --base-url http://127.0.0.1:$PORT/v1 --name "$name" \
    --answer-from "$src" --merge-from "$src" --only-ids "$ids" "$@" > "$L/fc_${name}_$ds.log" 2>&1 &
done
wait_runs
echo "done $VAR $BASE"
