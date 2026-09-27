#!/usr/bin/env bash
# Kwantyzacje Qwen3.5-4B dla T3 (L40S): imatrix na korpusie PL + ślady, warianty wg przepisu UD unsloth,
# perplexity i KL-dywergencja względem BF16.  Użycie: quant_t3_pipeline.sh [imatrix|quant|ppl|all]
set -u
W=$HOME/models/custom/qwen35-4b/work
O=$HOME/models/custom/qwen35-4b
S=$HOME/models/unsloth/Qwen3.5-4B-GGUF
B=$HOME/llama.cpp/build/bin
BF16=$S/Qwen3.5-4B-BF16.gguf
IMX=$W/imatrix-pl.gguf
cd "$W"
step=${1:-all}

if [ "$step" = imatrix ] || [ "$step" = all ]; then
  # zmodyfikowany llama-imatrix: przy --process-output zbiera też token_embd.weight (osadzenia wiązane = głowica wyjściowa)
  $B/llama-imatrix-tiedout -m "$BF16" -f calib.txt -o "$IMX" -ngl 999 -c 2048 -b 2048 -ub 2048 \
    --parse-special --process-output --output-frequency 20 > imatrix.log 2>&1
  tail -5 imatrix.log
fi

q() {  # q <nazwa> <plik tt> <typ bazowy> <typ osadzeń> [imatrix]
  local name=$1 tt=$2 base=$3 emb=$4 imx=${5:-$IMX}
  [ -f "$O/$name.gguf" ] && return 0
  $B/llama-quantize --imatrix "$imx" --tensor-type-file "$tt" --token-embedding-type "$emb" \
    "$BF16" "$O/$name.gguf" "$base" 16 > "quant_$name.log" 2>&1
  echo "$name $(stat -c %s "$O/$name.gguf") bytes"
}

if [ "$step" = quant ] || [ "$step" = all ]; then
  q Qwen3.5-4B-IQ3_XXS-PL        tt_UD-IQ3_XXS.txt IQ3_XXS q5_k
  q Qwen3.5-4B-IQ3_XXS-PL-E4XS   tt_UD-IQ3_XXS.txt IQ3_XXS iq4_xs
  q Qwen3.5-4B-IQ3_XXS-PL-E4K    tt_UD-IQ3_XXS.txt IQ3_XXS q4_k
  q Qwen3.5-4B-IQ3_XXS-PL-E3K    tt_UD-IQ3_XXS.txt IQ3_XXS q3_k
  q Qwen3.5-4B-IQ2_M-PL          tt_UD-IQ2_M.txt   IQ2_M   q5_k
  # kontrola: imatrix unsloth + osadzenia iq4_xs (bez danych dla token_embd) — izoluje wpływ naszego imatrix na osadzenia
  mkdir -p ctrl
  [ -f ctrl/Qwen3.5-4B-IQ3_XXS-U-E4XS.gguf ] || $B/llama-quantize --imatrix "$S/imatrix_unsloth.gguf_file" \
    --tensor-type-file tt_UD-IQ3_XXS.txt --token-embedding-type iq4_xs "$BF16" ctrl/Qwen3.5-4B-IQ3_XXS-U-E4XS.gguf IQ3_XXS 16 \
    > quant_ctrl.log 2>&1
fi

if [ "$step" = ppl ] || [ "$step" = all ]; then
  # bazowe logity BF16 do KLD (8 bloków po 2048 tokenów śladów rozumowania)
  [ -f kld_base_reason.bin ] || $B/llama-perplexity -m "$BF16" -f ppl_reason.txt -c 2048 -b 2048 -ngl 999 --chunks 8 \
    --kl-divergence-base kld_base_reason.bin > ppl_BF16_kldbase.log 2>&1
  for m in "$BF16" $S/Qwen3.5-4B-Q3_K_M.gguf $S/Qwen3.5-4B-UD-IQ3_XXS.gguf $S/Qwen3.5-4B-UD-IQ2_M.gguf $O/Qwen3.5-4B-*.gguf ctrl/*.gguf; do
    n=$(basename "$m" .gguf)
    [ -f "ppl_pl_$n.log" ] || $B/llama-perplexity -m "$m" -f ppl_pl.txt -c 2048 -b 2048 -ngl 999 > "ppl_pl_$n.log" 2>&1
    [ -f "ppl_reason_$n.log" ] || $B/llama-perplexity -m "$m" -f ppl_reason.txt -c 2048 -b 2048 -ngl 999 > "ppl_reason_$n.log" 2>&1
    [ "$m" = "$BF16" ] || [ -f "kld_$n.log" ] || $B/llama-perplexity -m "$m" -c 2048 -b 2048 -ngl 999 --chunks 8 \
      --kl-divergence-base kld_base_reason.bin --kl-divergence > "kld_$n.log" 2>&1
    echo "$n pl=$(grep -o 'Final estimate: PPL = [0-9.]* +/- [0-9.]*' "ppl_pl_$n.log") reason=$(grep -o 'Final estimate: PPL = [0-9.]* +/- [0-9.]*' "ppl_reason_$n.log") kld=$(grep -E '^Mean +KLD' "kld_$n.log" 2>/dev/null | tr -s ' ') top1=$(grep -E '^Same top p' "kld_$n.log" 2>/dev/null | tr -s ' ')"
  done
fi
