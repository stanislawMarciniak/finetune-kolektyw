#!/usr/bin/env bash
# Kolejki treningów LoRA na serwerze Forgehand (uruchamiać w /workspace/repo przez setsid).
#   server/train_queue.sh small   # T3: Bielik-1.5B, Qwen3.5-2B
#   server/train_queue.sh big     # T2: PLLuM-12B-base, Gemma-4-12B pt (QLoRA)
# Wynik: /workspace/train/<nazwa>/{adapter,train_log.json,lora.gguf}, logi w /workspace/logs/train_<nazwa>.log
set -u
cd /workspace/repo
OUT=/workspace/train
mkdir -p "$OUT" /workspace/logs

run() {  # nazwa, repo bazy, argumenty treningu...
    local name=$1 base=$2; shift 2
    local log=/workspace/logs/train_$name.log
    echo "START $name $(date +%T)" | tee -a /workspace/logs/train_queue.log
    python train/sft_lora.py --model "$base" --out "$OUT/$name" "$@" > "$log" 2>&1 < /dev/null
    if [ -d "$OUT/$name/adapter" ]; then
        python /workspace/llama.cpp/convert_lora_to_gguf.py "$OUT/$name/adapter" --base-model-id "$base" \
            --outtype f16 --outfile "$OUT/$name/lora.gguf" >> "$log" 2>&1
    fi
    echo "END $name $(date +%T) adapter=$([ -f "$OUT/$name/lora.gguf" ] && echo ok || echo FAIL)" | tee -a /workspace/logs/train_queue.log
}

case "$1" in
small)
    run bielik-1.5b speakleash/Bielik-1.5B-v3.0-Instruct --epochs 2 --rank 32 --lr 2e-4
    run q35-2b Qwen/Qwen3.5-2B --epochs 2 --rank 32 --lr 2e-4 --no-think
    ;;
big)
    run pllum-12b-base CYFRAGOVPL/PLLuM-12B-base-2512 --load-4bit --epochs 2 --rank 32 --batch 2 --grad-acc 8 \
        --template-from CYFRAGOVPL/PLLuM-12B-instruct-2512
    run gemma4-12b-pt google/gemma-4-12B --load-4bit --epochs 2 --rank 32 --batch 2 --grad-acc 8 \
        --template-from google/gemma-4-12B-it
    ;;
esac
echo "QUEUE_DONE $1 $(date +%T)" | tee -a /workspace/logs/train_queue.log
