#!/usr/bin/env bash
# Zadania nocne na lokalnym komputerze (CPU). Niezależne łańcuchy działają równolegle,
# każdy z własnym logiem w overnight/logs/. Bezpieczne do ponownego uruchomienia (pomija gotowe kroki).
# setsid odłącza procesy od terminala, więc przeżywają zamknięcie okna / sesji.
set -u
cd "$(dirname "$0")/.."
PY=.venv/bin/python
mkdir -p overnight/logs

setsid nohup bash -c "$PY overnight/local/cke_crawl.py && $PY overnight/local/pdf_extract.py" \
  > overnight/logs/cke.log 2>&1 < /dev/null &
echo "cke chain pid $!"

setsid nohup $PY overnight/local/build_kb.py > overnight/logs/kb.log 2>&1 < /dev/null &
echo "kb chain pid $!"

echo "Postęp: tail -f overnight/logs/*.log"
