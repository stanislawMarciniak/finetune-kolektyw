# Forgehand (Labqoat) L40S session

Third GPU, separate from the two Nebius machines. **Free for other jobs** — ask before starting anything, and run
**only ONE llama-server with images (`--mmproj`) at a time** (see RAM rule below).

- Account: `fh whoami` → team `baseline`, workspace `matura` (image `forgehand/base:cuda`).
- Class `gpu-l40s-small`: 1× L40S 48 GB, **4 vCPU, 30 GB usable RAM**, 1.861 $/h, prepaid (~185 $ left on 27.09 06:00).
- **Team limit: 1 GPU session at a time.** Session started 27.09 05:52: `01a0e0fa` (full id `01a0e0fa-49cf-727b-ba3f-d23045e616dc`).
  Left RUNNING on purpose (prepaid). Stop only if broken: `fh session stop 01a0e0fa`.

## Connect

```
fh session ls                                   # state + IP (IP changes with every new session)
ssh root@18.212.193.136                         # laptop key ~/.ssh/id_rsa is registered (fh ssh-key ls)
fh session ssh 01a0e0fa -- 'nvidia-smi'         # same thing via the CLI
```

- After `fh session start matura --class gpu-l40s-small --wait` port 22 refuses connections for ~2–3 min — retry in a loop.
- Nebius → Forgehand directly (no laptop bandwidth): start an agent on the laptop (`eval $(ssh-agent -s); ssh-add ~/.ssh/id_rsa`),
  then `ssh -A kolektyw@89.169.112.149 'scp FILE root@<fh-ip>:/scratch/...'` (1.75 GB in ~90 s).
- Tunnel a server to the laptop: `ssh -N -L 8331:localhost:8331 root@<fh-ip>`.

## Disks

| Path | What | Persists after `session stop`? |
|---|---|---|
| `/scratch` | local NVMe, 229 GB — **work here** (models, repo, logs, builds) | **no** (fresh every session) |
| `/workspace` | network mount (`127.0.0.1:/`), old repo/logs/runs from Saturday, old llama.cpp build | yes |
| `/` | overlay 200 GB; `/opt/conda` etc. come from the image | **no** (conda installs are lost) |

`/workspace` crashed twice on Saturday under RAM pressure — do not serve models from it or write heavy output there;
copy results off to the laptop (`rsync root@<ip>:/scratch/repo/runs/... runs/...`).

## What is installed (session 01a0e0fa)

- Driver 595.91, CUDA runtime/cuBLAS 12.8 as pip wheels in `/opt/conda/lib/python3.11/site-packages/nvidia/*`.
- llama.cpp:
  - `/scratch/llama-81bc6b8/` — copy of the Saturday build (`/workspace/llama.cpp`, commit 81bc6b8, sm_89). Supports `--reasoning-budget`
    and `--reasoning-budget-message`. The binary has RPATH to `/workspace/llama.cpp/build/bin`, so set `LD_LIBRARY_PATH` (below).
  - **`/scratch/llama.cpp-2145525/build/bin/llama-server` — same commit as Nebius H100/L40S (recommended for new jobs)**; smoke-tested
    with MIX + mmproj + reasoning budget. Persistent copy of the whole `bin/` in `/workspace/llama.cpp-2145525-bin/` (+ build script).
    Built with `/scratch/build_2145525.sh` (CUDA 12.8 toolkit from conda `nvidia/label/cuda-12.8.1` into `/opt/conda`, `-j 3`, ~25 min);
    the final link needs `cmake -B build -DCMAKE_EXE_LINKER_FLAGS="-Wl,-rpath-link,/opt/conda/lib -L/opt/conda/lib"` and a rebuild.
    Nebius binaries do **not** run here (they need glibc 2.39 + CUDA 13; this image is Ubuntu 22.04, glibc 2.35).
- Environment for llama-server (the conda toolkit is gone after a new session; the pip CUDA 12.8 wheels are in the image):
  ```
  N=/opt/conda/lib/python3.11/site-packages/nvidia
  LB=/scratch/llama.cpp-2145525/build/bin        # new session: LB=/workspace/llama.cpp-2145525-bin (or copy it to /scratch first)
  export LD_LIBRARY_PATH=$LB:$N/cuda_runtime/lib:$N/cublas/lib
  ```
  `server/fh_mix_s43.sh` defaults to `LB=/scratch/llama-81bc6b8` (the build the 2026 s43 result was measured on); override with `LB=...`.
- Python for the harness: `/scratch/.venv/bin/python` (first in PATH; has `openai`; `harness/run_exam.py --help` OK). `/opt/conda/bin/python`
  has torch 2.9.1+cu128 but no `openai`.
- `tesseract` 4 + `tesseract-ocr-pol` (apt; for T2 `--ocr`).
- Models (sha256 verified against Nebius `q2.sha256` / Nebius copy):
  - `/scratch/models/custom/qwen35-4b/Qwen3.5-4B-IQ2_M-PL-E4K-MIX.gguf` (T3 final, 1 745 906 784 B) + `q2.sha256`
  - `/scratch/models/unsloth/Qwen3.5-4B-GGUF/mmproj-F16.gguf` (from HF, sha256 = Nebius copy)
  - persistent backup of both: `/workspace/models/{custom/qwen35-4b,unsloth/Qwen3.5-4B-GGUF}/` — after a new session
    `cp -r /workspace/models/* /scratch/models/` instead of re-transferring.
- Repo (code as on the laptop 27.09 ~06:00): `/scratch/repo/{harness,server,eval,data/kb/*.jsonl,exams/test202{4,5,6}_v2}`.
  No `.env`, no API keys on the machine — judge from the laptop.

## Running T3 (example)

`server/fh_mix_s43.sh [exam...]` — T3 tuned from `final_configs.json` (MIX + mmproj, `-c 98304 -np 8 -ub 4096`, reasoning budget 5000
+ message, `--essay-mode structured`) with `--seed 43`; uses `server/lib_eval.sh` (`serve`/`run`/`stop`) with `BIN`, `PY`, `L=/scratch/logs`.
```
ssh root@<ip> 'cd /scratch/repo && nohup setsid bash server/fh_mix_s43.sh test2026_v2 > /scratch/logs/fh_mix_s43.log 2>&1 < /dev/null &'
```
One T3 server: ~7.9 GB VRAM, ~77 tok/s per slot with 8 slots; RAM after load ~7 GB used + page cache.
test2026_v2 (39 items) took 5.5 min wall. Result `runs/test2026_v2/q35-4b-q2-iq2mpl-e4k-mix__struct2-s43-2026-fh` (build 81bc6b8):
**46.7%** (luna; closed 9/10, open 19/35, essay 0/15; s42 was 45.0%).

Judge on the laptop (no keys on the machine):
```
rsync -az root@<ip>:/scratch/repo/runs/test2026_v2/<run>/ runs/test2026_v2/<run>/
.venv/bin/python harness/to_results.py runs/test2026_v2/<run> && .venv/bin/python eval/grade.py results/
(set -a; . ./.env; set +a; .venv/bin/python eval/judge_openai.py grade --model gpt-6-luna --essay-model gpt-6-luna \
  --key-env FORGEHAND_API_KEY --base-url https://app.forgehand.app/api/v1/teams/01a0da5f-05f4-700d-a554-4c8f829182f1/llm/v1 \
  --budget 0.3 --only "test2026_v2/<run>")
.venv/bin/python eval/report.py | grep <run>
```

## RAM rule

32 GB class (30 GB visible). Saturday: two Qwen servers with `--mmproj` at once → `/workspace` mount crashed twice. So:
**one llama-server with images at a time**; a second text-only small server is OK only if `free -g` shows > 10 GB available.

Also: `pkill -f "--port 8332"` inside `ssh root@... '...'` kills your own ssh shell (the pattern matches its command line) —
use `server/lib_eval.sh stop` or a `[-]-port` pattern in a separate ssh call.
