#!/usr/bin/env bash
# H100 CPU: quantize finer-MIX variants in parallel, trim to V124K, CPU PPL
cd ~/models/custom/qwen35-4b/work/vt
B=~/llama.cpp/build/bin; O=~/models/custom/qwen35-4b; BF16=Qwen3.5-4B-BF16.gguf
one() { v=$1; lv=$(echo $v | tr A-Z a-z)
  full=Qwen3.5-4B-IQ2_M-PL-E4K-MIX-$v.gguf; out=$O/Qwen3.5-4B-IQ2_M-PL-E4K-MIX-$v-V124K.gguf
  [ -f $full ] || { nice -n 5 $B/llama-quantize --imatrix imatrix-pl.gguf --tensor-type-file tt_mix_$lv.txt --token-embedding-type q4_k $BF16 $full.tmp IQ2_M 6 > quant_$v.log 2>&1 && mv $full.tmp $full; }
  nice ~/venv-unsloth/bin/python trim.py $full K_seen_a60k.txt $out > trim_$v.log 2>&1
  echo "$(date +%T) $v full=$(stat -c %s $full) trim=$(stat -c %s $out)"
  for set in pl reason; do
    CUDA_VISIBLE_DEVICES= nice -n 5 $B/llama-perplexity -m $out -f ppl_$set.txt -c 2048 -b 512 -ngl 0 -t 3 --chunks 4 > cpu_ppl_${set}_$v.log 2>&1 &
  done
  wait
  echo "$v pl=$(grep -o 'PPL = [0-9.]* +/- [0-9.]*' cpu_ppl_pl_$v.log | tail -1) reason=$(grep -o 'PPL = [0-9.]* +/- [0-9.]*' cpu_ppl_reason_$v.log | tail -1)"
}
for v in "$@"; do one $v & done
wait; echo FINE_H100_DONE
