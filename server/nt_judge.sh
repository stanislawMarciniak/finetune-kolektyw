#!/usr/bin/env bash
# Raport 10: ściąga gotowe przebiegi "__nt*" z obu maszyn, ocenia zamknięte, kopiuje oceny identycznych odpowiedzi
# (eval/judge_reuse.py) i ocenia resztę sędzią gpt-6-luna.   server/nt_judge.sh <budżet_usd> [filtr]
set -u
cd "$(dirname "$0")/.."
BUDGET=${1:-0.5}
ONLY=${2:-__nt}
for host in 89.169.126.236 89.169.112.149; do
  ssh -i ~/.ssh/id_rsa -o ConnectTimeout=10 kolektyw@$host \
    'cd ~/repo && ls -d runs/*_v2/*__nt*/answers.json 2>/dev/null | xargs -r -n1 dirname | xargs -r tar czf -' | tar xzf - 2>/dev/null
done
for d in runs/*_v2/*__nt*/; do
  [ -f "$d/answers.json" ] && .venv/bin/python harness/to_results.py "$d" > /dev/null
done
.venv/bin/python eval/grade.py results/ > /dev/null
.venv/bin/python eval/judge_reuse.py --only "$ONLY"
set -a; . ./.env; set +a
.venv/bin/python eval/judge_openai.py grade --model gpt-6-luna --essay-model gpt-6-luna --key-env FORGEHAND_API_KEY \
  --base-url https://app.forgehand.app/api/v1/teams/01a0da5f-05f4-700d-a554-4c8f829182f1/llm/v1 \
  --budget "$BUDGET" --only "$ONLY" 2>&1 | tail -3 | tee -a /tmp/nt_judge_cost.log
