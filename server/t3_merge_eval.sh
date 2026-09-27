#!/usr/bin/env bash
# T3 (H100): LoRA z maską myślenia scalona w wagi Qwen3.5-4B (konwerter LoRA w llama.cpp nie obsługuje Qwen3.5),
# konwersja do GGUF, kwantyzacja Q4_K_M i Q3_K_M, sonda + bramka ochrony myślenia, a przy PASS pełna ewaluacja T3 v2.
set -u
cd ~/repo
. server/lib_eval.sh
A=$HOME/train/q35-4b-maskthink
OUT=$A/merged
B=$HOME/llama.cpp/build/bin
Q=$HOME/models/unsloth/Qwen3.5-4B-GGUF
if [ ! -f $A/q35-4b-maskthink-Q3_K_M.gguf ]; then
  [ -f $OUT/model.safetensors ] || $HOME/venv-hf/bin/python - <<EOF
import torch
from transformers import AutoModelForImageTextToText
from peft import PeftModel
base = AutoModelForImageTextToText.from_pretrained("Qwen/Qwen3.5-4B", dtype=torch.bfloat16)
m = PeftModel.from_pretrained(base, "$A/adapter").merge_and_unload()
m.save_pretrained("$OUT", safe_serialization=True)
print("merged")
EOF
  # tokenizer i pliki procesora prosto z repo bazy (AutoProcessor wymaga torchvision)
  $HOME/venv-hf/bin/python - <<EOF
from huggingface_hub import snapshot_download
snapshot_download("Qwen/Qwen3.5-4B", local_dir="$OUT", allow_patterns=["tokenizer*", "vocab*", "merges*", "*.jinja",
                  "preprocessor_config.json", "video_preprocessor_config.json", "chat_template*", "special_tokens_map.json"])
EOF
  # transformers nie wczytuje warstwy MTP, więc jej nie zapisuje, a konwerter Qwen3.5 jej wymaga (blk.32):
  # kopiujemy tensory MTP z oryginalnego checkpointu (LoRA ich nie dotyczy)
  $HOME/venv-hf/bin/python - <<EOF
import glob, json
from huggingface_hub import snapshot_download
from safetensors import safe_open
from safetensors.torch import save_file
src = snapshot_download("Qwen/Qwen3.5-4B", allow_patterns=["*.safetensors", "*.json"])
mtp = {}
for f in glob.glob(f"{src}/*.safetensors"):
    with safe_open(f, "pt") as st:
        for k in st.keys():
            if "mtp" in k:
                mtp[k] = st.get_tensor(k)
save_file(mtp, "$OUT/model-mtp.safetensors", metadata={"format": "pt"})
p = "$OUT/config.json"
c = json.load(open(p))
(c.get("text_config") or c)["mtp_num_hidden_layers"] = 1
json.dump(c, open(p, "w"), indent=2)
print("mtp tensors:", len(mtp))
EOF
  $HOME/venv-hf/bin/python $HOME/llama.cpp/convert_hf_to_gguf.py $OUT --outtype bf16 --outfile $A/q35-4b-maskthink-BF16.gguf
  $B/llama-quantize $A/q35-4b-maskthink-BF16.gguf $A/q35-4b-maskthink-Q4_K_M.gguf Q4_K_M
  $B/llama-quantize $A/q35-4b-maskthink-BF16.gguf $A/q35-4b-maskthink-Q3_K_M.gguf Q3_K_M
fi
ls -la $A/*.gguf
SRV="-ub 4096 -b 4096 -c 98304 -np 8 --reasoning-format deepseek"
T3="--rag none --vision --think rozstrz,open,podaj,closed --temperature 1.0 --top-p 0.95 --top-k 20 --max-tokens 8000 --kb-essay data/kb/kompendium.jsonl"
# sonda przed (baza Q4) i po (scalony Q4) na tej samej maszynie
serve 8161 -m $Q/Qwen3.5-4B-Q4_K_M.gguf --mmproj $Q/mmproj-F16.gguf $SRV
serve 8162 -m $A/q35-4b-maskthink-Q4_K_M.gguf --mmproj $Q/mmproj-F16.gguf $SRV
run q35-4b-q4__probe-h100 exams/probe60_v2 8161 --parallel 8 $T3 &
run q35-4b-q4-maskthink__probe exams/probe60_v2 8162 --parallel 8 $T3 &
wait_runs
stop 8161
$PY eval/think_gate.py check runs/probe60_v2/q35-4b-q4__probe-h100 runs/probe60_v2/q35-4b-q4-maskthink__probe | tee $L/think_gate.log
if grep -q GATE_PASS $L/think_gate.log; then
  serve 8163 -m $A/q35-4b-maskthink-Q3_K_M.gguf --mmproj $Q/mmproj-F16.gguf $SRV
  for ds in test2024_v2 test2025_v2; do
    run q35-4b-q4-maskthink__t3cfg exams/$ds 8162 --parallel 4 $T3 &
    run q35-4b-q3km-maskthink__t3cfg exams/$ds 8163 --parallel 4 $T3 &
  done
  wait_runs
  stop 8163
fi
stop 8162
echo T3_MERGE_DONE
