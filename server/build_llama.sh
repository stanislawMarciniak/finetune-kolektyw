#!/usr/bin/env bash
# llama.cpp z CUDA na maszynie bez nvcc: toolkit z condy, kompilacja tylko dla sm_89 (L40S).
set -x
/opt/conda/bin/conda install -y -c "nvidia/label/cuda-12.8.1" cuda-nvcc cuda-cudart-dev libcublas-dev cuda-cccl cuda-profiler-api
export CUDA_HOME=/opt/conda PATH=/opt/conda/bin:$PATH
cd /workspace/llama.cpp && rm -rf build
cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=89 -DLLAMA_CURL=OFF \
  -DCUDAToolkit_ROOT=/opt/conda -DCMAKE_CUDA_COMPILER=/opt/conda/bin/nvcc
cmake --build build --config Release -j 4 --target llama-server llama-quantize llama-export-lora
ls -la build/bin/
echo BUILD_DONE
