#!/usr/bin/env bash
# T1 bez treningu (raport 10), fala 2 na gotowym serwerze Gemmy (port $1):
#  - poprawki eseju na istniejących esejach (para przed/po): --essay-from <przebieg> + refine z bazą + nagłówek + dopisywanie;
#  - OCR jako uzupełnienie: tylko zadania z obrazami, reszta z t1final (--only-ids/--merge-from).
set -u
cd ~/repo
. server/lib_eval.sh
PORT=$1
KB=${KB:-data/kb/kb_all_notes.jsonl}
TAG=${TAG:-}
T1="--parallel 2 --rag none --vision --think essay,rozstrz,open,podaj,closed --temperature 1.0 --top-p 0.95 --top-k 64"
ESSAY_ID() { "$PY" -c "import json,sys; sys.path.insert(0,'harness'); import run_exam as R; print(','.join(i['id'] for i in json.load(open('exams/$1/exam.json'))['items'] if R.item_type(i)=='essay'))"; }
IMG_IDS() { "$PY" -c "import json; print(','.join(i['id'] for i in json.load(open('exams/$1/exam.json'))['items'] if i.get('images')))"; }
for src in ${SRCS:-gemma4-qat-t1final__s42 gemma4-qat-t1final__s43 gemma4-qat-legacy__s42 gemma4-qat-legacy__s43 gemma4-qat-t1kb__s42 gemma4-qat-t1kb__s43}; do
  for ds in test2024_v2 test2025_v2 test2026_v2; do
    [ -f runs/$ds/$src/debug.jsonl ] || continue
    s=${src##*__}
    run gemma4-qat__nt1ref${TAG}-${src#gemma4-qat-} exams/$ds "$PORT" $T1 --seed 42 --only-ids "$(ESSAY_ID $ds)" --merge-from runs/$ds/$src \
      --essay-from runs/$ds/$src --essay-refine-kb "$KB" --essay-refine-think --essay-topic-detect --essay-extend 2 &
  done
done
if [ -z "${NO_OCR:-}" ]; then
  for s in 42 43; do
    for ds in test2024_v2 test2025_v2; do
      run gemma4-qat__nt1ocr-s$s exams/$ds "$PORT" $T1 --seed $s --ocr --only-ids "$(IMG_IDS $ds)" \
        --merge-from runs/$ds/gemma4-qat-t1final__s$s &
    done
  done
fi
wait_runs
echo NT_T1_W2_DONE
