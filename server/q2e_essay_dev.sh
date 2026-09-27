#!/usr/bin/env bash
# Esej T3: obecna ścieżka (topic-detect + extend) vs --essay-mode structured, na essays12_rag + essays3_v2.
#   q2e_essay_dev.sh <port> <tag modelu> <seeds> [warianty: base,struct,structmix,structthink]
cd ~/repo && source server/lib_eval.sh
port=$1 tag=$2 seeds=${3:-42} vars=${4:-base,struct}
T3="--parallel 8 --rag none --vision --think rozstrz,open,podaj,closed --temperature 0.6 --top-p 0.95 --top-k 20 --max-tokens 8000 --kb-essay data/kb/kompendium.jsonl"
for s in ${seeds//,/ }; do for v in ${vars//,/ }; do
  case $v in
    base) extra="--essay-topic-detect --essay-extend 2 --essay-min-words 300";;
    struct) extra="--essay-mode structured";;
    structmix) extra="--essay-mode structured --essay-pick mix";;
    structthink) extra="--essay-mode structured --essay-plan-think";;
  esac
  for ex in exams/essays12_rag exams/essays3_v2; do
    run q35-4b-essay-$tag-$v-s$s $ex $port $T3 --seed $s $extra &
  done
done; done
wait_runs
echo ALLDONE
