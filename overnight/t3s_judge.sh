#!/usr/bin/env bash
# Raport 16: pobiera przebiegi T3 < 0.97 GB (q35-2b-iq*, slayer-*, bielik-1.5b-q4km*) z L40S i ocenia je (luna).
#   [HOST=89.169.126.236] overnight/t3s_judge.sh [budżet_usd]
set -eu
cd "$(dirname "$0")/.."
BUDGET=${1:-0.8}
PAT="q35-2b-iq,slayer-sft2,bielik-1.5b-q4km"
ssh -i ~/.ssh/id_rsa kolektyw@${HOST:-89.169.112.149} 'cd ~/repo && for d in runs/test202[456]_v2/q35-2b-iq* runs/test202[456]_v2/slayer-* runs/test202[456]_v2/bielik-1.5b-q4km*; do [ -f $d/answers.json ] && echo $d; done | tar czf - -T -' | tar xzf -
for d in runs/test202[456]_v2/{q35-2b-iq,slayer-sft2,bielik-1.5b-q4km}*/; do
  [ -f "$d/answers.json" ] && .venv/bin/python harness/to_results.py "$d" > /dev/null
done
.venv/bin/python eval/grade.py results/ > /dev/null
.venv/bin/python eval/judge_reuse.py --only "$PAT"
set -a; . ./.env; set +a
.venv/bin/python eval/judge_openai.py grade --model gpt-6-luna --essay-model gpt-6-luna --key-env FORGEHAND_API_KEY \
  --base-url https://app.forgehand.app/api/v1/teams/01a0da5f-05f4-700d-a554-4c8f829182f1/llm/v1 \
  --budget "$BUDGET" --only "$PAT" 2>&1 | tail -5
.venv/bin/python eval/report.py 2>/dev/null | grep -E "_v2 \| ($(echo $PAT | tr , '|'))"
