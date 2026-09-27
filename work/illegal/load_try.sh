#!/usr/bin/env bash
# load_try.sh <try> <seconds> — pełne obciążenie egzaminu (T1, T2+opisy, T3 tuned, T3 base) na własnych portach 878x,
# kopia exam_run.sh z wynikami w work/illegal/runs i logami w work/illegal/logs; po <seconds> zatrzymuje wszystko swoje.
set -u
T=$1 SECS=$2
D=$HOME/repo/work/illegal; cd ~/repo
sed -e "s#OUT=runs/final/\$TRACK-\$VAR#OUT=$D/runs/t$T-\$TRACK-\$VAR#" server/exam_run.sh > $D/exam_run_x.sh
export L=$D/logs/t$T; mkdir -p $L
S0=$(date +%s)
for spec in "T1 tuned 8781" "T2 tuned 8782" "T3 tuned 8783" "T3 base 8793"; do
  set -- $spec
  bash $D/exam_run_x.sh assets/mock-2023 $1 $2 $3 > $L/exam_$1_$2.log 2>&1 &
done
sleep $SECS
pkill -f "[r]un_exam.py.*work/illegal/runs/t$T-"
. server/lib_eval.sh
stop 8781 8782 8783 8793 8832
sleep 2
echo "try$T $(date +%T): restarts: $(for f in $L/server_*.log; do echo -n "$(basename $f .log)=$(grep -c 'SUPERVISOR restart' $f) "; done) illegal=$(cat $L/server_*.log | grep -ci illegal)"
echo "  xid since start: $(sudo -n dmesg --time-format iso 2>/dev/null | awk -v s=$(date -d @$S0 +%Y-%m-%dT%H:%M:%S) '$1 >= s' | grep -c Xid)"
