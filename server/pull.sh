#!/usr/bin/env bash
# Ściąga przebiegi i oceny (wystawione na maszynach przez grade_loop.sh) z maszyn Nebius, bez ponownego oceniania.
#   server/pull.sh            # H100 + L40S, potem raporty 09 i 08
set -u
cd "$(dirname "$0")/.."
for host in 89.169.126.236 89.169.112.149; do
  ssh -i ~/.ssh/id_rsa -o ConnectTimeout=10 kolektyw@$host \
    'cd ~/repo && tar czf - runs/*_v2 runs/probe60_v2 results/*_v2 results/probe60_v2 results/grades/*_v2 results/grades/probe60_v2 2>/dev/null' \
    | tar xzf - 2>/dev/null && echo "pulled $host"
done
.venv/bin/python eval/report.py > /dev/null
.venv/bin/python eval/analyze.py --registry eval/runs_registry_v2.json > /dev/null && echo "raport 09 zaktualizowany"
