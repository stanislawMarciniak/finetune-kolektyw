#!/usr/bin/env bash
# Fala 5b po konwersjach, potem pobranie i ocena fal 5, 5b i selektora (łączny limit ~1 $ w OpenAI).
set -u
cd "$(dirname "$0")/.."
PY=.venv/bin/python
has() { modal volume ls matura-models "$1" 2>/dev/null | grep -q "$2"; }
until has converted/Bielik-11B-v3-Base-20250730 Q5_K_M.gguf && has converted/gemma-4-12B Q4_K_M.gguf; do
  sleep 120
  if grep -q "Error" overnight/logs/convert_gemma.log && ! pgrep -f "modal_convert.py --repo google" >/dev/null; then
    echo "gemma conversion failed — wave5b only with Bielik"; break
  fi
done
modal run overnight/modal_baselines.py::wave5b > overnight/logs/modal_wave5b.log 2>&1
until modal volume ls matura-results 2>/dev/null | grep -q "summary-wave5.json"; do sleep 120; done
until [ "$(modal volume ls matura-results select/test2026_split 2>/dev/null | grep -c jsonl)" -ge 1 ]; do sleep 120; done
modal volume get matura-results / results/ --force
$PY eval/grade.py results/
set -a; . ./.env; set +a
J="$PY eval/judge_openai.py grade --model gpt-5.4-mini --essay-model gpt-5.4-mini"
$J --budget 0.22 --only "q35-4b-q4-think-img"
$J --budget 0.33 --only "test2024_split_rag/q35-2b-q4__rag,test2024_split_rag/bielik-1.5b-q8__rag,test2024_split_rag/q35-4b-q4__rag,test2025_split_rag/q35-2b-q4__rag,test2025_split_rag/bielik-1.5b-q8__rag,test2025_split_rag/q35-4b-q4__rag"
$J --budget 0.25 --only "test2024_split/bielik-1.5b-base,test2024_split/bielik-4.5b-base,test2024_split/bielik-11b-base,test2024_split/gemma4-12b-pt,test2024_split/bielik-pl-11b"
$J --budget 0.15 --only "test2024_split_rag/gemma4-12b-qat__rag,test2024_split_rag/bielik-11b-v3-q5__rag"
$PY eval/report.py
$PY eval/select_report.py
echo "AFTER_WAVE5_DONE"
