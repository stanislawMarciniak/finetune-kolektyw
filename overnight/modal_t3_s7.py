"""T3: drugi seed (s7) dla UD-IQ3_XXS i UD-IQ2_M z --reasoning-budget 5000, na jednym L40S (Modal).

    python overnight/modal_t3_s7.py snapshot          # zamrożenie kodu i paczek do /tmp/t3s7_snap
    modal run --detach overnight/modal_t3_s7.py::main # prefetch (CPU) + egzamin (L40S)
    modal volume get matura-results t3s7/ /tmp/t3s7_out/
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAP = Path("/tmp/t3s7_snap")
REPO = "unsloth/Qwen3.5-4B-GGUF"
QUANTS = {"udiq3xxs": "Qwen3.5-4B-UD-IQ3_XXS.gguf", "udiq2m": "Qwen3.5-4B-UD-IQ2_M.gguf"}
MMPROJ = "mmproj-F16.gguf"
DATASETS = ["test2024_v2", "test2025_v2"]
LLAMA = shutil.which("llama-server") or "/app/llama-server"
RBM = "\n\nNa podstawie powyższych rozważań podaję ostateczną odpowiedź.\n"
HARNESS = ("--parallel 8 --rag none --vision --think rozstrz,open,podaj,closed --temperature 0.6 --top-p 0.95 --top-k 20 "
           "--max-tokens 8000 --kb-essay data/kb/kompendium.jsonl --seed 7 --essay-topic-detect --essay-extend 2").split()


def snapshot():
    if SNAP.exists():
        shutil.rmtree(SNAP)
    for d in ["harness", "exams/test2024_v2", "exams/test2025_v2"]:
        shutil.copytree(ROOT / d, SNAP / d, ignore=shutil.ignore_patterns("__pycache__"))
    (SNAP / "eval").mkdir(parents=True)
    for f in (ROOT / "eval").glob("*.py"):
        shutil.copy2(f, SNAP / "eval" / f.name)
    (SNAP / "data/kb").mkdir(parents=True)
    shutil.copy2(ROOT / "data/kb/kompendium.jsonl", SNAP / "data/kb/kompendium.jsonl")
    md5 = hashlib.md5((SNAP / "harness/run_exam.py").read_bytes()).hexdigest()
    (SNAP / "SNAPSHOT.json").write_text(json.dumps({"run_exam_md5": md5, "time": time.strftime("%F %T")}))
    print("snapshot", SNAP, "run_exam.py md5", md5)


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "snapshot":
    snapshot()
    sys.exit(0)

import modal  # noqa: E402

app = modal.App("matura-t3-s7")
models_vol = modal.Volume.from_name("matura-models", create_if_missing=True)
results_vol = modal.Volume.from_name("matura-results", create_if_missing=True)

base_image = (
    modal.Image.from_registry("ghcr.io/ggml-org/llama.cpp:server-cuda", add_python="3.11")
    .entrypoint([])
    .pip_install("openai>=1.40", "huggingface_hub>=0.34", "hf_xet", "requests", "tantivy")
)
image = base_image.add_local_dir(SNAP, "/repo") if SNAP.exists() else base_image


def hf_secret():
    env = {}
    if not (ROOT / ".env").exists():
        return modal.Secret.from_dict({})
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith("HF_TOKEN="):
            env["HF_TOKEN"] = line.split("=", 1)[1].strip().strip('"')
    return modal.Secret.from_dict(env)


@app.function(image=base_image, volumes={"/models": models_vol}, timeout=1800, cpu=2, secrets=[hf_secret()])
def prefetch():
    from huggingface_hub import hf_hub_download
    os.environ["HF_XET_HIGH_PERFORMANCE"] = "1"
    out = {}
    for f in [*QUANTS.values(), MMPROJ]:
        dest = Path("/models") / REPO / f
        if not dest.exists():
            t0 = time.time()
            hf_hub_download(REPO, f, local_dir=str(Path("/models") / REPO))
            print(f"downloaded {f} in {time.time() - t0:.0f}s", flush=True)
        out[f] = dest.stat().st_size
    models_vol.commit()
    return out


def start_server(model, port):
    import requests
    cmd = [LLAMA, "-m", str(model), "--mmproj", f"/models/{REPO}/{MMPROJ}", "--host", "127.0.0.1", "--port", str(port),
           "-ngl", "999", "--kv-unified", "--jinja", "-ub", "4096", "-b", "4096", "-c", "98304", "-np", "8",
           "--reasoning-format", "deepseek", "--reasoning-budget", "5000", "--reasoning-budget-message", RBM]
    log = open(f"/tmp/server_{port}.log", "w")
    proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
    t0 = time.time()
    while time.time() - t0 < 600:
        if proc.poll() is not None:
            raise RuntimeError(f"server {port} died: " + open(f"/tmp/server_{port}.log").read()[-3000:])
        try:
            if requests.get(f"http://127.0.0.1:{port}/health", timeout=2).status_code == 200:
                return proc, cmd
        except requests.RequestException:
            pass
        time.sleep(2)
    raise RuntimeError(f"server {port} timeout")


@app.function(image=image, gpu="L40S", volumes={"/models": models_vol, "/results": results_vol}, timeout=75 * 60, cpu=8)
def exam():
    import traceback
    try:
        return _exam()
    except BaseException:
        tb = traceback.format_exc()
        print(tb, flush=True)
        for f in sorted(Path("/tmp").glob("harness_*.log")):
            print("==", f, f.read_text(errors="replace")[-2000:], flush=True)
        return [{"traceback": tb}]


def _exam():
    help_txt = subprocess.run([LLAMA, "--help"], capture_output=True, text=True).stdout
    assert "--reasoning-budget-message" in help_txt, "llama-server without --reasoning-budget-message"
    version = subprocess.run([LLAMA, "--version"], capture_output=True, text=True)
    version = (version.stdout + version.stderr).strip()[-300:]
    print(version, flush=True)
    servers = {}
    for i, (q, f) in enumerate(QUANTS.items()):
        servers[q] = (8081 + i, *start_server(f"/models/{REPO}/{f}", 8081 + i))
    print("servers up", flush=True)
    procs = []
    for q, (port, _, _) in servers.items():
        for ds in DATASETS:
            run = f"q35-4b-{q}__bf5k-modal-s7"
            out = f"/repo/runs/{ds}/{run}"
            cmd = [sys.executable, "harness/run_exam.py", "--exam", f"exams/{ds}", "--out", out,
                   "--base-url", f"http://127.0.0.1:{port}/v1", "--name", run, *HARNESS]
            log = open(f"/tmp/harness_{q}_{ds}.log", "w")
            procs.append((q, ds, run, subprocess.Popen(cmd, cwd="/repo", stdout=log, stderr=subprocess.STDOUT), time.time()))
    deadline = time.time() + 65 * 60
    t_start = time.time()
    while any(p.poll() is None for *_, p, _ in procs) and time.time() < deadline:
        time.sleep(15)
        el = time.time() - t_start
        if int(el) % 120 < 15:
            done = {f"{q}/{ds}": (sum(1 for _ in open(f"/repo/runs/{ds}/{run}/debug.jsonl")) if Path(f"/repo/runs/{ds}/{run}/debug.jsonl").exists() else 0, p.poll())
                    for q, ds, run, p, _ in procs}
            print(f"{el:.0f}s", done, flush=True)
    if time.time() - t_start < 60:
        for f in sorted(Path("/tmp").glob("harness_*.log")):
            print("== early exit", f, f.read_text(errors="replace")[-2000:], flush=True)
    summary = []
    dest = Path("/results/t3s7")
    for q, ds, run, p, t0 in procs:
        if p.poll() is None:
            p.kill()
        d = dest / "runs" / ds / run
        d.mkdir(parents=True, exist_ok=True)
        src = Path("/repo/runs") / ds / run
        if src.exists():
            for f in src.iterdir():
                shutil.copy2(f, d / f.name)
        shutil.copy2(f"/tmp/harness_{q}_{ds}.log", d / "harness.log")
        summary.append({"quant": q, "dataset": ds, "run": run, "returncode": p.returncode,
                        "log_tail": open(f"/tmp/harness_{q}_{ds}.log", errors="replace").read()[-1500:]})
    for q, (port, proc, cmd) in servers.items():
        alive = proc.poll() is None
        proc.kill()
        shutil.copy2(f"/tmp/server_{port}.log", dest / f"server_{q}.log")
        summary.append({"quant": q, "server_cmd": cmd, "server_alive_at_end": alive})
    (dest / "summary.json").write_text(json.dumps({"llama_version": version, "snapshot": json.loads(Path("/repo/SNAPSHOT.json").read_text()),
                                                   "runs": summary}, ensure_ascii=False, indent=1))
    results_vol.commit()
    return summary


@app.local_entrypoint()
def main():
    print(prefetch.remote())
    for s in exam.remote():
        print(json.dumps(s, ensure_ascii=False)[:2000])


@app.function(image=image, cpu=1)
def probe():
    import glob
    r = subprocess.run([sys.executable, "harness/run_exam.py", "--exam", "exams/test2024_v2", "--out", "/repo/runs/test2024_v2/x",
                        "--base-url", "http://127.0.0.1:9/v1", "--only-ids", "1", *HARNESS], cwd="/repo", capture_output=True, text=True, timeout=60)
    return {"exe": sys.executable, "llama": LLAMA, "rc": r.returncode, "out": (r.stdout + r.stderr)[-3000:]}


@app.local_entrypoint()
def check():
    print(probe.remote())
