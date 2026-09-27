"""T3 Q2: własny IQ2_M-PL-E4K (imatrix PL) z --reasoning-budget 5000 i --essay-mode structured, na jednym H100 (Modal).

    modal volume put matura-models Qwen3.5-4B-IQ2_M-PL-E4K.gguf custom/qwen35-4b/Qwen3.5-4B-IQ2_M-PL-E4K.gguf
    python overnight/modal_q2.py snapshot
    modal run --detach overnight/modal_q2.py::main
    modal volume get matura-results q2/ /tmp/q2_out/
"""

import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAP = Path("/tmp/q2m2_snap")
REPO = "unsloth/Qwen3.5-4B-GGUF"
MODEL = "/models/custom/qwen35-4b/Qwen3.5-4B-IQ2_M-PL-E4K-MIX.gguf"
MMPROJ = f"/models/{REPO}/mmproj-F16.gguf"
LLAMA = shutil.which("llama-server") or "/app/llama-server"
RBM = "\n\nNa podstawie powyższych rozważań podaję ostateczną odpowiedź.\n"
T3 = ("--parallel 8 --rag none --vision --think rozstrz,open,podaj,closed --temperature 0.6 --top-p 0.95 --top-k 20 "
      "--max-tokens 8000 --kb-essay data/kb/kompendium.jsonl").split()
BASE = "--essay-topic-detect --essay-extend 2 --essay-min-words 300".split()
STRUCT = "--essay-mode structured".split()
# (serwer, zbiór, przebieg, argumenty)
RUNS = [(i, ds, "q35-4b-q2-iq2mpl-e4k-mix__struct2-s43", T3 + STRUCT + ["--seed", "43"])
        for i, ds in enumerate(["test2024_v2", "test2025_v2"])]


def snapshot():
    if SNAP.exists():
        shutil.rmtree(SNAP)
    for d in ["harness", "exams/test2024_v2", "exams/test2025_v2", "exams/test2026_v2", "exams/essays3_v2"]:
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

app = modal.App("matura-t3-q2mix43")
models_vol = modal.Volume.from_name("matura-models", create_if_missing=True)
results_vol = modal.Volume.from_name("matura-results", create_if_missing=True)
base_image = (
    modal.Image.from_registry("ghcr.io/ggml-org/llama.cpp:server-cuda", add_python="3.11")
    .entrypoint([])
    .pip_install("openai>=1.40", "huggingface_hub>=0.34", "hf_xet", "requests", "tantivy")
)
image = base_image.add_local_dir(SNAP, "/repo") if SNAP.exists() else base_image


def start_server(port):
    import requests
    cmd = [LLAMA, "-m", MODEL, "--mmproj", MMPROJ, "--host", "127.0.0.1", "--port", str(port),
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


def save(dest, ds, run, log_path):
    d = dest / "runs" / ds / run
    d.mkdir(parents=True, exist_ok=True)
    src = Path("/repo/runs") / ds / run
    if src.exists():
        for f in src.iterdir():
            shutil.copy2(f, d / f.name)
    shutil.copy2(log_path, d / "harness.log")


@app.function(image=image, gpu="H100", volumes={"/models": models_vol, "/results": results_vol}, timeout=70 * 60, cpu=8)
def exam():
    import traceback
    dest = Path("/results/q2mix43")
    summary = []
    try:
        servers = [start_server(8081 + i) for i in range(3)]
        print("servers up", flush=True)
        procs = []
        for srv, ds, run, args in RUNS:
            cmd = [sys.executable, "harness/run_exam.py", "--exam", f"exams/{ds}", "--out", f"/repo/runs/{ds}/{run}",
                   "--base-url", f"http://127.0.0.1:{8081 + srv}/v1", "--name", run, *args]
            lp = f"/tmp/harness_{ds}_{run}.log"
            procs.append((ds, run, subprocess.Popen(cmd, cwd="/repo", stdout=open(lp, "w"), stderr=subprocess.STDOUT), lp))
        saved = set()
        deadline = time.time() + 62 * 60
        while time.time() < deadline:
            for ds, run, p, lp in procs:  # zapis każdego przebiegu zaraz po końcu (wyniki częściowe przy timeoucie)
                if p.poll() is not None and (ds, run) not in saved:
                    save(dest, ds, run, lp)
                    saved.add((ds, run))
                    results_vol.commit()
                    print("saved", ds, run, p.returncode, flush=True)
            if len(saved) == len(procs):
                break
            time.sleep(15)
        for ds, run, p, lp in procs:
            if p.poll() is None:
                p.kill()
            summary.append({"dataset": ds, "run": run, "rc": p.returncode, "tail": open(lp, errors="replace").read()[-800:]})
        for i, (proc, cmd) in enumerate(servers):
            proc.kill()
            shutil.copy2(f"/tmp/server_{8081 + i}.log", dest / f"server_{i}.log")
    except BaseException:
        summary.append({"traceback": traceback.format_exc()})
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    results_vol.commit()
    return summary


@app.local_entrypoint()
def main():
    for s in exam.remote():
        print(json.dumps(s, ensure_ascii=False)[:1500])
