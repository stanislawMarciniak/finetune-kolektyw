#!/usr/bin/env bash
# Fetch q35-4b-vt-* runs from a machine and judge locally (gpt-6-luna).  vt_judge.sh <host> <budget_usd>
set -eu
cd "$(dirname "$0")/../.."
H=${1:-89.169.112.149}; BUDGET=${2:-0.8}
ssh -i ~/.ssh/id_rsa kolektyw@$H 'cd ~/repo && tar czf - runs/test202[456]_v2/q35-4b-vt-* 2>/dev/null' | tar xzf -
for d in runs/test202[456]_v2/q35-4b-vt-*/; do
  [ -f "$d/answers.json" ] && .venv/bin/python harness/to_results.py "$d" > /dev/null
done
.venv/bin/python eval/grade.py results/ > /dev/null
set -a; . ./.env; set +a
.venv/bin/python eval/judge_openai.py grade --model gpt-6-luna --essay-model gpt-6-luna --key-env FORGEHAND_API_KEY \
  --base-url https://app.forgehand.app/api/v1/teams/01a0da5f-05f4-700d-a554-4c8f829182f1/llm/v1 \
  --budget "$BUDGET" --only "q35-4b-vt-"
