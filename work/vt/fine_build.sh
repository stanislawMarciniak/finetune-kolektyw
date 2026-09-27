#!/usr/bin/env bash
# finer MIX variants: quantize BF16 with imatrix-pl + tt file, token_embd q4_k, trim to V124K, CPU PPL
cd ~/models/custom/qwen35-4b/work
B=~/llama.cpp/build/bin; O=~/models/custom/qwen35-4b; BF16=~/models/unsloth/Qwen3.5-4B-GGUF/Qwen3.5-4B-BF16.gguf
for v in "$@"; do
  full=vt/Qwen3.5-4B-IQ2_M-PL-E4K-MIX-$v.gguf
  [ -f $full ] || nice -n 5 $B/llama-quantize --imatrix imatrix-pl.gguf --tensor-type-file vt/tt_mix_$(echo $v | tr A-Z a-z).txt --token-embedding-type q4_k "$BF16" $full.tmp IQ2_M 8 > vt/quant_$v.log 2>&1 && mv $full.tmp $full
  out=$O/Qwen3.5-4B-IQ2_M-PL-E4K-MIX-$v-V124K.gguf
  nice ~/venv-quant/bin/python trim.py $full vt/K_seen_a60k.txt $out > vt/trim_$v.log 2>&1
  echo "$(date +%T) $v full=$(stat -c %s $full) trim=$(stat -c %s $out)"
  for set in pl reason; do
    CUDA_VISIBLE_DEVICES= setsid nohup nice -n 5 $B/llama-perplexity -m $out -f ppl_$set.txt -c 2048 -b 512 -ngl 0 -t 3 --chunks 4 > vt/cpu_ppl_${set}_$v.log 2>&1 < /dev/null &
  done
done
echo FINE_BUILD_DONE
