#!/usr/bin/env bash
# Egzamin (nd): jeden track i wariant na H100, bez sieci i bez kluczy w środowisku.
#   bash server/exam_run.sh <katalog egzaminu z exam.json> <T1|T2|T3> <tuned|base> [port]
# Wynik: runs/final/<track>-<wariant>/answers.json (do wgrania z TEAM_KEY) + debug.jsonl + meta.json
set -u
EXAM=$1 TRACK=$2 VAR=$3 PORT=${4:-8400}
cd ~/repo
unset FORGEHAND_API_KEY OPENAI_API_KEY HF_TOKEN
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
# grafy CUDA: mmproj Qwen3.5 na H100 przy kilku serwerach naraz pada w clip_encode (illegal instruction, Xid 13); wyniki bez zmian
[ "$TRACK" = T3 ] && export GGML_CUDA_DISABLE_GRAPHS=1
. server/lib_eval.sh
CFG=$(python3 -c "import json; c = json.load(open('server/final_configs.json'))['$TRACK']['$VAR']; print(json.dumps(c))")
SRV=$(python3 -c "import json,sys,os; c=json.loads(sys.argv[1]); print(c['server'].replace('models/', os.path.expanduser('~/models/')).replace('train/', os.path.expanduser('~/train/')))" "$CFG")
HARN=$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['harness'])" "$CFG")
RBM=$(python3 -c "import json,sys; print(json.loads(sys.argv[1]).get('reasoning_budget_message', '') + 'X')" "$CFG")
RBM=${RBM%X}
CAP=$(python3 -c "import json,sys,os; print(json.loads(sys.argv[1]).get('caption_server', '').replace('models/', os.path.expanduser('~/models/')))" "$CFG")
CPORT=$((PORT + 50))
if [ -n "$CAP" ]; then
  # bez opisów obrazów T2 i tak działa (zostaje --ocr), więc brak plików albo awaria VLM nie zatrzymuje egzaminu
  # grafy CUDA wyłączone tylko dla VLM opisów (mmproj Qwen3.5, jak T3); PLLuM T2 zostaje z grafami
  CAPF=$(echo $CAP | tr ' ' '\n' | grep '\.gguf$')
  if ls $CAPF > /dev/null 2>&1 && GGML_CUDA_DISABLE_GRAPHS=1 serve "$CPORT" $CAP; then HARN="$HARN --caption-url http://127.0.0.1:$CPORT/v1"
  else echo "UWAGA: serwer opisów obrazów nie wstał — T2 bez opisów (tylko --ocr)"; stop "$CPORT"; CAP=""; fi
fi
if [ -n "$RBM" ]; then serve "$PORT" $SRV --reasoning-budget-message "$RBM"; else serve "$PORT" $SRV; fi
OUT=runs/final/$TRACK-$VAR
mkdir -p runs/final
$PY harness/run_exam.py --exam "$EXAM" --out "$OUT" --base-url "http://127.0.0.1:$PORT/v1" --name "$TRACK-$VAR" $HARN
stop "$PORT"
[ -n "$CAP" ] && stop "$CPORT"
python3 -c "import json; a = json.load(open('$OUT/answers.json')); print('answers.json OK:', a['exam_id'], len(a['answers']), 'odpowiedzi')"
