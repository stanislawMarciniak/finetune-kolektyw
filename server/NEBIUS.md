# Nebius H100 VM (matura-h100)

- Instance id: `computeinstance-e00j2pxfys1stnqd3z` (project `project-e00vktr4pr003rw2ex8avm`, eu-north1)
- Boot disk: `matura-h100-boot` (managed, 300 GiB network_ssd, deleted together with the instance)
- Public IP: `89.169.126.236` (static allocation, survives stop/start)
- User: `kolektyw` (passwordless sudo)
- SSH: `ssh -i ~/.ssh/id_rsa kolektyw@89.169.126.236`
- Platform/preset: `gpu-h100-sxm` / `1gpu-16vcpu-200gb`, on-demand, 1x H100 80GB HBM3, 16 vCPU, 196 GB RAM
- Image: `ubuntu24.04-cuda13.0` (driver 580.173, CUDA 13.0 toolkit at `/usr/local/cuda`, Python 3.12)
- Price: ~3.85 $/h while RUNNING (budget 123 $ => ~30 h). Stopped VM still bills the disk + IP (small).

## Paths on the VM
- llama.cpp (CUDA, sm_90): `~/llama.cpp/build/bin/{llama-server,llama-quantize,llama-export-lora,llama-cli}`
- venvs (uv, Python 3.12):
  - `~/venv-unsloth`: unsloth 2026.9.11, torch 2.12.1+cu130, transformers 5.5.0, gguf-py (editable)
  - `~/venv-hf`: torch 2.14.0+cu130, transformers 5.17.0, peft 0.21, trl 1.14, accelerate 1.15, datasets 5.0.1, bitsandbytes 0.50.2, gguf-py (editable)
- GGUF models: `~/models/google/gemma-4-12B-it-qat-q4_0-gguf/{gemma-4-12b-it-qat-q4_0.gguf,mmproj-gemma-4-12b-it-qat-q4_0.gguf}`,
  `~/models/mradermacher/PLLuM-12B-base-2512-GGUF/PLLuM-12B-base-2512.Q4_K_M.gguf`
- HF cache (`~/.cache/huggingface/hub`): google/gemma-4-12B (full safetensors), google/gemma-4-12B-it (config/tokenizer only),
  CYFRAGOVPL/PLLuM-12B-base-2512 (full). HF token in `~/.cache/huggingface/token`.
- Repo: `~/repo` (harness, eval, train, server, exams, assets/mock-2023, data/sft/{train,val}.jsonl, data/kb/polqa_index)
- Setup logs/scripts: `~/build_llama.{sh,log}`, `~/setup_venvs.{sh,log}`, `~/download_models.{py,log}`

## Serve (smoke-tested, ~158 tok/s, ~9.4 GB VRAM)
```
M=~/models/google/gemma-4-12B-it-qat-q4_0-gguf
~/llama.cpp/build/bin/llama-server -m $M/gemma-4-12b-it-qat-q4_0.gguf --mmproj $M/mmproj-gemma-4-12b-it-qat-q4_0.gguf -ngl 999 -c 16384 --jinja --port 8090
```
Tunnel from laptop: `ssh -i ~/.ssh/id_rsa -N -L 8090:localhost:8090 kolektyw@89.169.126.236`

## Lifecycle (run locally; CLI at ~/.nebius/bin/nebius, profile kolektyw)
```
nebius compute instance stop   --id computeinstance-e00j2pxfys1stnqd3z
nebius compute instance start  --id computeinstance-e00j2pxfys1stnqd3z
nebius compute instance get    --id computeinstance-e00j2pxfys1stnqd3z
nebius compute instance delete --id computeinstance-e00j2pxfys1stnqd3z   # also deletes the managed boot disk
```

## Gotchas
- Gemma-4 `-it` via `--jinja` thinks by default: 300 max_tokens gave empty `content` (all in `reasoning_content`, ~700 tokens total).
  Use a larger `max_tokens` or pass `"chat_template_kwargs": {"enable_thinking": false}` for direct answers.
- Latest torch from PyPI is cu130 -> needs driver >= 580; that's why the `ubuntu24.04-cuda13.0` image was used
  (`ubuntu24.04-cuda12` has driver 570, `ubuntu22.04-cuda12` has 550).
- Boot disk (network_ssd 300 GiB) writes only ~150 MB/s; large downloads/installs in parallel are IO-bound.
- llama.cpp build prints `UI: download dist.tar.gz ... failed` (web UI bundle); harmless for the API.
- Create -> SSH took ~81 s (instance RUNNING after ~45 s).
