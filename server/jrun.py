"""Wykonuje polecenie powłoki na maszynie Forgehand przez terminal JupyterLab (gdy SSH nie działa).

    .venv/bin/python server/jrun.py 'nvidia-smi; tail /workspace/logs/train_queue.log' [--timeout 120]
Sesja: FH_SESSION (domyślnie 01a0dd91). Ciasteczka są trzymane w /tmp/fh_jupyter.json.
"""

import argparse
import json
import os
import subprocess
import time
import uuid
from pathlib import Path

import requests
import websocket

SESSION = os.environ.get("FH_SESSION", "01a0dd91")
STATE = Path("/tmp/fh_jupyter.json")


def login():
    url = subprocess.run(["fh", "session", "jupyter", SESSION], capture_output=True, text=True, timeout=90).stdout.split()[-1]
    s = requests.Session()
    r = s.get(url, timeout=60)
    base = r.url.split("/lab")[0]
    STATE.write_text(json.dumps({"base": base, "cookies": s.cookies.get_dict()}))
    return base, s


def session():
    if STATE.exists():
        st = json.loads(STATE.read_text())
        s = requests.Session()
        s.cookies.update(st["cookies"])
        if s.get(st["base"] + "/api/status", timeout=30).status_code == 200:
            return st["base"], s
    return login()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("cmd")
    p.add_argument("--timeout", type=float, default=120)
    a = p.parse_args()
    base, s = session()
    xsrf = s.cookies.get("_xsrf", "")
    term = s.post(base + "/api/terminals", headers={"X-XSRFToken": xsrf}, timeout=30).json()["name"]
    cookie = "; ".join(f"{k}={v}" for k, v in s.cookies.get_dict().items())
    ws = websocket.create_connection(base.replace("https", "wss") + f"/terminals/websocket/{term}",
                                     header=[f"Cookie: {cookie}"], timeout=a.timeout)
    mark = uuid.uuid4().hex[:8]
    # znaczniki sklejane w powłoce, żeby echo samego polecenia ich nie zawierało
    ws.send(json.dumps(["stdin", f"echo S''TART_{mark}; ( {a.cmd} ) 2>&1; echo E''ND_{mark}\n"]))
    buf, t0 = "", time.time()
    while time.time() - t0 < a.timeout and f"END_{mark}" not in buf:
        msg = json.loads(ws.recv())
        if msg[0] == "stdout":
            buf += msg[1]
    ws.close()
    s.delete(base + f"/api/terminals/{term}", headers={"X-XSRFToken": xsrf}, timeout=30)
    print(buf.split(f"START_{mark}")[-1].split(f"END_{mark}")[0].replace("\r", "").strip("\n"))


if __name__ == "__main__":
    main()
