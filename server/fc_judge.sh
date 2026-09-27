#!/usr/bin/env bash
# Raport 17: jak nt_judge.sh, ale dla przebiegów "__fc*" (recenzent faktów).

set -u
cd "$(dirname "$0")/.."
BUDGET=${1:-0.5}
ONLY=${2:-__fc}
for host in; do
  ssh -i ~/.ssh/id_rsa -o ConnectTimeout=10 kolektyw@$host \
    'cd ~/repo && ls -d runs/*_v2/*__fc*/answers.json 2>/dev/null | xargs -r -n1 dirname | xargs -r tar czf -' | tar xzf - 2>/dev/null
done
for d in runs/*_v2/*__fc*/; do
  [ -f "$d/answers.json" ] && .venv/bin/python harness/to_results.py "$d" > /dev/null
done
.venv/bin/python eval/grade.py results/ > /dev/null
.venv/bin/python eval/judge_reuse.py --only "$ONLY"
set -a; . ./.env; set +a
.venv/bin/python eval/judge_openai.py grade --model gpt-6-luna --essay-model gpt-6-luna --key-env FORGEHAND_API_KEY \
  --base-url https://app.forgehand.app/api/v1/teams/01a0da5f-05f4-700d-a554-4c8f829182f1/llm/v1 \
  --budget "$BUDGET" --only "$ONLY" 2>&1 | tail -3 | tee -a /tmp/fc_judge_cost.log
