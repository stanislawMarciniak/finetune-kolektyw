#!/usr/bin/env bash
# Pobiera wyniki harnessu (runs/) z serwera, zamienia na format oceniania i ocenia: zamknięte automatycznie,
# otwarte i eseje sędzią gpt-6-luna (Forgehand API).
#   server/fetch_runs.sh [sesja Forgehand | nebius] [budżet_usd] [filtr przebiegów, np. "__fix,t1final"]
set -eu
cd "$(dirname "$0")/.."
SRC=${1:-01a0de3a}
BUDGET=${2:-1.0}
ONLY=${3:-"__,t1final"}
if [ "$SRC" = nebius ]; then
    ssh -i ~/.ssh/id_rsa kolektyw@89.169.126.236 'cd ~/repo && tar czf - runs' | tar xzf -
else
    fh session ssh "$SRC" -- 'cd /workspace/repo && tar czf - runs' | tar xzf -
fi
for d in runs/*/*/; do
    [ -f "$d/debug.jsonl" ] && .venv/bin/python harness/to_results.py "$d" > /dev/null
done
.venv/bin/python eval/grade.py results/ > /dev/null
set -a; . ./.env; set +a
.venv/bin/python eval/judge_openai.py grade --model gpt-6-luna --essay-model gpt-6-luna --key-env FORGEHAND_API_KEY \
  --base-url https://app.forgehand.app/api/v1/teams/01a0da5f-05f4-700d-a554-4c8f829182f1/llm/v1 \
  --budget "$BUDGET" --only "$ONLY"
.venv/bin/python eval/report.py > /dev/null
