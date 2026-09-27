#!/usr/bin/env bash
# Czeka na koniec fali 4 na Modal, pobiera wyniki, ocenia zamknięte automatycznie i otwarte sędzią OpenAI (limit kosztu).
set -u
cd "$(dirname "$0")/.."
until modal volume ls matura-results 2>/dev/null | grep -q "summary-wave4.json"; do sleep 120; done
modal volume get matura-results / results/ --force
.venv/bin/python eval/grade.py results/
set -a; . ./.env; set +a
# najpierw eseje (H-H14) i modele z T1/T3, potem reszta — w granicach limitu
.venv/bin/python eval/judge_openai.py grade --model gpt-5.4-mini --essay-model gpt-5.4-mini --budget 0.6 --only "essays12_rag"
.venv/bin/python eval/judge_openai.py grade --model gpt-5.4-mini --essay-model gpt-5.4-mini --budget 0.7 --only "test2024_split"
.venv/bin/python eval/report.py
echo "AFTER_WAVE4_DONE"
