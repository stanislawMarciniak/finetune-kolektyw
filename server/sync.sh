#!/usr/bin/env bash
# Wysyła kod i małe dane na serwer Forgehand (/workspace/repo). Użycie: server/sync.sh <sesja>
set -eu
cd "$(dirname "$0")/.."
SESSION=${1:-01a0dd91}
tar czf - harness eval/*.py eval/data/*.jsonl eval/data/img exams assets/mock-2023 server overnight/local \
  | fh session ssh "$SESSION" -- 'mkdir -p /workspace/repo && tar xzf - -C /workspace/repo && echo synced'
