#!/usr/bin/env bash
# T3 (raport 10): poprawki eseju na istniejących esejach danej kwantyzacji (para przed/po), na gotowym serwerze (port $1).
#   bash server/nt_t3_essay.sh <port> "<przebiegi źródłowe>"
#   warianty: E = nagłówek z treści + dopisywanie akapitów; ER = E + drugie przejście z bazą wiedzy
set -u
cd ~/repo
. server/lib_eval.sh
PORT=$1 SRCS=$2
KB=${KB:-data/kb/kb_all_notes.jsonl}
TAG=${TAG:-}
T3="--parallel 2 --rag none --vision --think rozstrz,open,podaj,closed --temperature 0.6 --top-p 0.95 --top-k 20 --max-tokens 8000"
ESSAY_ID() { "$PY" -c "import json,sys; sys.path.insert(0,'harness'); import run_exam as R; print(','.join(i['id'] for i in json.load(open('exams/$1/exam.json'))['items'] if R.item_type(i)=='essay'))"; }
for src in $SRCS; do
  for ds in test2024_v2 test2025_v2 test2026_v2; do
    [ -f runs/$ds/$src/debug.jsonl ] || continue
    E="--only-ids $(ESSAY_ID $ds) --merge-from runs/$ds/$src --essay-from runs/$ds/$src"
    run ${src%%__*}__nt3E${TAG}-${src#*__} exams/$ds "$PORT" $T3 $E --essay-topic-detect --essay-extend 2 &
    run ${src%%__*}__nt3ER${TAG}-${src#*__} exams/$ds "$PORT" $T3 $E --essay-topic-detect --essay-extend 2 --essay-refine-kb "$KB" &
  done
done
wait_runs
echo NT_T3_ESSAY_DONE
