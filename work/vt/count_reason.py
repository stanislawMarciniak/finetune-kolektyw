import glob, json, numpy as np
from tokenizers import Tokenizer
tok = Tokenizer.from_file("work/vt/qwen35/tokenizer.json")
c = np.zeros(248320, np.int64); n = 0; buf = []
for f in glob.glob("runs/*/*/debug.jsonl"):
    if "q35-4b-vt-" in f: continue
    for l in open(f):
        try: d = json.loads(l)
        except Exception: continue
        r = d.get("reasoning")
        if r: buf.append(r)
    if len(buf) > 3000:
        ids = [i for e in tok.encode_batch(buf, add_special_tokens=False) for i in e.ids]
        c += np.bincount(np.asarray(ids, np.int64), minlength=248320); n += sum(map(len, buf)); buf = []
if buf:
    ids = [i for e in tok.encode_batch(buf, add_special_tokens=False) for i in e.ids]
    c += np.bincount(np.asarray(ids, np.int64), minlength=248320); n += sum(map(len, buf))
np.save("work/vt/counts_reason.npy", c); print("reason chars", n, "distinct", (c > 0).sum())
