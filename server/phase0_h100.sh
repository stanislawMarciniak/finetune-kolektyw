#!/usr/bin/env bash
# Faza 0 na H100 (paczki v2): T2 (Gemma pt scalona, gołe bazy, obecne PLLuM + LoRA), Qwen3.5-2B z myśleniem + HyDE (T3),
# potem T1: stara konfiguracja vs t1final, po 2 seedy (H-N1). Najwyżej 2 ciężkie przebiegi naraz.
set -u
cd ~/repo
. server/lib_eval.sh
M=$HOME/models
P=$M/gemma4-pt
V24=exams/test2024_v2
V25=exams/test2025_v2
both() {  # nazwa port argumenty...: 2024 i 2025 równolegle
  local name=$1 port=$2; shift 2
  run "$name" $V24 "$port" "$@" &
  run "$name" $V25 "$port" "$@" &
  wait_runs
}
GREEDY="--no-think-kwargs --temperature 0.0 --top-p 1.0 --top-k 1 --parallel 4"

# --- T2 ---
serve 8201 -m $P/gemma-4-12B-sft-Q4_K_M.gguf --mmproj $P/mmproj-gemma-4-12B-F16.gguf -ub 4096 -b 4096 \
  --chat-template-file $HOME/repo/train/templates/gemma4_turns.jinja -c 65536 -np 8
serve 8202 -m $M/mradermacher/PLLuM-12B-base-2512-GGUF/PLLuM-12B-base-2512.Q4_K_M.gguf -c 32768 -np 8
both gemma4-12b-pt-sft-merged 8201 --vision --no-think-kwargs --temperature 0.3 --top-p 0.95 --top-k 64 --parallel 4 &
both pllum-12b-base__bare 8202 --bare $GREEDY &
wait_runs
stop 8201 8202
serve 8203 -m $P/gemma-4-12B-Q4_K_M.gguf --mmproj $P/mmproj-gemma-4-12B-F16.gguf -ub 4096 -b 4096 -c 65536 -np 8
serve 8204 -m $M/mradermacher/PLLuM-12B-base-2512-GGUF/PLLuM-12B-base-2512.Q4_K_M.gguf --lora $HOME/train/pllum-12b-base/lora.gguf \
  --chat-template-file $HOME/train/pllum-12b-base/chat_template.jinja -c 32768 -np 8
both gemma4-12b-pt__bare 8203 --bare --vision $GREEDY &
both pllum-12b-base-sft__v2 8204 $GREEDY &
wait_runs
stop 8203 8204

# --- T3: Qwen3.5-2B z myśleniem + HyDE dla „podaj” (indeks PolQA jest tylko tutaj) ---
Q2=$M/unsloth/Qwen3.5-2B-GGUF
serve 8205 -m $Q2/Qwen3.5-2B-Q4_K_M.gguf --mmproj $Q2/mmproj-F16.gguf -ub 4096 -b 4096 -c 98304 -np 8 --reasoning-format deepseek
both q35-2b-q4__t3cfg-hyde 8205 --parallel 4 --vision --think rozstrz,open,podaj,closed --temperature 1.0 --top-p 0.95 --top-k 20 \
  --max-tokens 8000 --kb-essay data/kb/kompendium.jsonl --rag hyde --rag-types podaj
stop 8205

# --- T1: H-N1 ---
Q=$M/google/gemma-4-12B-it-qat-q4_0-gguf
serve 8206 -m $Q/gemma-4-12b-it-qat-q4_0.gguf --mmproj $Q/mmproj-gemma-4-12b-it-qat-q4_0.gguf -ub 4096 -b 4096 -c 131072 -np 8 \
  --reasoning-format deepseek
T1="--parallel 4 --rag none --vision --think essay,rozstrz,open,podaj,closed --temperature 1.0 --top-p 0.95 --top-k 64"
for seed in 42 43; do
  both gemma4-qat-t1final__s$seed 8206 $T1 --seed $seed
  both gemma4-qat-legacy__s$seed 8206 $T1 --seed $seed --legacy-prompt
done
stop 8206
echo PHASE0_H100_DONE
