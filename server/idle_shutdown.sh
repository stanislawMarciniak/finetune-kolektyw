#!/usr/bin/env bash
# Strażnik kosztów na maszynach Nebius: gdy przez IDLE_MIN minut nie działa żaden harness, trening ani konwersja,
# wyłącza system (maszyna przechodzi w STOPPED i przestaje naliczać GPU). Sam llama-server bez zadań to bezczynność.
IDLE_MIN=${IDLE_MIN:-30}
idle=0
while true; do
  if pgrep -f "run_exam.py|sft_lora.py|sft_peft.py|convert_hf_to_gguf|convert_lora_to_gguf|llama-quantize|llama-export-lora|judge_openai|hf_hub_download" > /dev/null; then
    idle=0
  else
    idle=$((idle + 1))
  fi
  if [ "$idle" -ge "$IDLE_MIN" ]; then
    echo "$(date) idle ${IDLE_MIN} min -> shutdown"
    sudo shutdown -h now
  fi
  sleep 60
done
