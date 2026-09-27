#!/usr/bin/env bash
# Przygotowanie maszyny Forgehand (L40S): llama.cpp z CUDA + biblioteki do treningu LoRA.
# Log: /workspace/logs/setup.log
set -x
mkdir -p /workspace/logs /workspace/models /workspace/data /workspace/runs /scratch/hf
export HF_HOME=/scratch/hf
cd /workspace
if [ ! -x /workspace/llama.cpp/build/bin/llama-server ]; then
  git clone --depth 1 https://github.com/ggml-org/llama.cpp /workspace/llama.cpp
  cd /workspace/llama.cpp
  cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=89 -DLLAMA_CURL=OFF
  cmake --build build --config Release -j 4 --target llama-server llama-quantize llama-cli llama-export-lora
  pip install -r requirements/requirements-convert_hf_to_gguf.txt
  cd /workspace
fi
pip install -U "transformers>=4.57" "trl>=0.24" "peft>=0.17" "datasets" "accelerate" "bitsandbytes" "openai" "huggingface_hub" "hf_xet" "liger-kernel" 2>&1 | tail -5
pip install -U unsloth unsloth_zoo 2>&1 | tail -5
python -c "import torch, transformers, trl, peft; print('torch', torch.__version__, torch.cuda.is_available(), 'transformers', transformers.__version__, 'trl', trl.__version__, 'peft', peft.__version__)"
python -c "import unsloth; print('unsloth ok')" || echo "unsloth import failed"
echo SETUP_DONE
