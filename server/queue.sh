#!/usr/bin/env bash
# Kolejka zadań na maszynie: każda linia ~/repo/jobs.txt to jedno polecenie (np. `bash server/phase2_h100.sh`).
# Wykonuje po kolei, zakończone dopisuje do jobs.done; pusta kolejka = czekanie (strażnik bezczynności wyłączy maszynę).
#   setsid nohup server/queue.sh > ~/logs/queue.log 2>&1 &      # dopisywanie: echo "bash server/x.sh" >> ~/repo/jobs.txt
set -u
cd ~/repo
touch jobs.txt jobs.done
while true; do
  line=$(grep -v '^\s*#' jobs.txt | grep -v '^\s*$' | grep -vxF -f jobs.done | head -1)
  if [ -z "$line" ]; then
    sleep 60
    continue
  fi
  echo "$(date +%T) START $line"
  bash -c "$line"
  echo "$line" >> jobs.done
  echo "$(date +%T) END $line"
done
