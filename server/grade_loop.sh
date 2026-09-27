#!/usr/bin/env bash
# Ocenianie na maszynie, bez laptopa: co INTERVAL sekund zamienia gotowe przebiegi na format oceniania, ocenia zamknięte
# i odpala sędziego gpt-6-luna dla przebiegów pasujących do FILTER. Klucz API w ~/.fh_key (chmod 600; usunąć przed egzaminem).
#   setsid nohup server/grade_loop.sh ~/venv-unsloth/bin/python "_v2" 600 > ~/logs/grade_loop.log 2>&1 &
set -u
cd ~/repo
PY=${1:-$HOME/venv-unsloth/bin/python}
FILTER=${2:-_v2}
INTERVAL=${3:-600}
set -a; . ~/.fh_key; set +a
while true; do
  for d in runs/*/*/; do
    [ -f "$d/answers.json" ] && [ "$d/debug.jsonl" -nt "results/$(basename "$(dirname "$d")")/$(basename "$d").jsonl" ] \
      && "$PY" harness/to_results.py "$d" > /dev/null 2>&1
  done
  "$PY" eval/grade.py results/ > /dev/null 2>&1
  "$PY" eval/judge_openai.py grade --model gpt-6-luna --essay-model gpt-6-luna --key-env FORGEHAND_API_KEY \
    --base-url https://app.forgehand.app/api/v1/teams/01a0da5f-05f4-700d-a554-4c8f829182f1/llm/v1 \
    --budget 1.0 --only "$FILTER" 2>&1 | grep -v "^retry" | tail -1
  sleep "$INTERVAL"
done
