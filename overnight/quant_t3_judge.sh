#!/usr/bin/env bash
# Pobiera przebiegi A/B kwantyzacji T3 (q35-4b-cq-*) z L40S i ocenia je lokalnie (sędzia gpt-6-luna, limit $1.50).
#   overnight/quant_t3_judge.sh [budżet_usd]
set -eu
cd "$(dirname "$0")/.."
BUDGET=${1:-1.5}
ssh -i ~/.ssh/id_rsa kolektyw@89.169.112.149 'cd ~/repo && tar czf - runs/test202[456]_v2/q35-4b-cq-* 2>/dev/null' | tar xzf -
for d in runs/test202[456]_v2/q35-4b-cq-*/; do
  [ -f "$d/answers.json" ] && .venv/bin/python harness/to_results.py "$d" > /dev/null
done
.venv/bin/python eval/grade.py results/ > /dev/null
set -a; . ./.env; set +a
.venv/bin/python eval/judge_openai.py grade --model gpt-6-luna --essay-model gpt-6-luna --key-env FORGEHAND_API_KEY \
  --base-url https://app.forgehand.app/api/v1/teams/01a0da5f-05f4-700d-a554-4c8f829182f1/llm/v1 \
  --budget "$BUDGET" --only "q35-4b-cq-"
