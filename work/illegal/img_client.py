"""Wysyła tylko zadania z obrazami (równolegle, krótkie odpowiedzi) do llama-server; wypisuje błędy."""
import base64, json, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

url, par = sys.argv[1], int(sys.argv[2])
exams = sys.argv[3:]
jobs = []
for ex in exams:
    ex, _, lim = ex.partition(":")
    items = [i for i in json.load(open(Path(ex) / "exam.json"))["items"] if i.get("images")]
    for it in items[: int(lim) if lim else None]:
        parts = [{"type": "image_url", "image_url": {"url": "data:image/png;base64," +
                  base64.b64encode((Path(ex) / im["path"]).read_bytes()).decode()}} for im in it["images"]]
        parts.append({"type": "text", "text": it.get("source_text", "") + "\n\n" + it["question"]})
        jobs.append((f"{Path(ex).name}/{it['id']}", parts))


def one(job):
    name, parts = job
    body = json.dumps({"messages": [{"role": "user", "content": parts}], "max_tokens": 24, "temperature": 0.6,
                       "chat_template_kwargs": {"enable_thinking": False}}).encode()
    t = time.time()
    try:
        r = urllib.request.urlopen(urllib.request.Request(url + "/chat/completions", body, {"Content-Type": "application/json"}), timeout=300)
        u = json.load(r)["usage"]
        return f"OK {name} prompt={u['prompt_tokens']} {time.time() - t:.1f}s"
    except Exception as e:
        return f"ERR {name} {type(e).__name__}: {str(e)[:80]} {time.time() - t:.1f}s"


t0 = time.time()
with ThreadPoolExecutor(par) as ex:
    res = list(ex.map(one, jobs))
err = [r for r in res if r.startswith("ERR")]
print("\n".join(err[:5]))
print(f"requests={len(res)} errors={len(err)} time={time.time() - t0:.1f}s")
