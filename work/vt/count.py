"""Token frequency of the Qwen3.5 tokenizer over our PL/EN corpus -> counts.npy (len 248320)."""
import glob, json, sys, os
import numpy as np
from tokenizers import Tokenizer

tok = Tokenizer.from_file("work/vt/qwen35/tokenizer.json")
counts = np.zeros(248320, dtype=np.int64)
nchars = 0


def feed(texts):
    global nchars
    texts = [t for t in texts if t]
    if not texts:
        return
    ids = [i for enc in tok.encode_batch(texts, add_special_tokens=False) for i in enc.ids]
    counts[:] += np.bincount(np.asarray(ids, dtype=np.int64), minlength=248320)
    nchars += sum(map(len, texts))


def strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from strings(v)


def jsonl_files(paths, limit_bytes=None):
    for p in paths:
        buf, done = [], 0
        with open(p, encoding="utf-8", errors="replace") as f:
            for line in f:
                done += len(line)
                try:
                    buf.extend(strings(json.loads(line)))
                except Exception:
                    buf.append(line)
                if len(buf) >= 4000:
                    feed(buf); buf = []
                if limit_bytes and done > limit_bytes:
                    break
        feed(buf)
        print(p, nchars, file=sys.stderr, flush=True)


small = []
for pat in ["data/kb/*.jsonl", "data/sft/*.jsonl", "data/sft/*/*.jsonl", "exams/*/exam.json", "runs/*/*/debug.jsonl",
            "runs/*/*/answers.json", "data/kb/e7/*.jsonl"]:
    small += sorted(glob.glob(pat))
small = [p for p in small if os.path.getsize(p) < 400e6]
jsonl_files(small)
for p in glob.glob("exams/*/exam.json"):
    pass
jsonl_files(["data/kb/polqa/data/passages.jsonl"], limit_bytes=float(sys.argv[1]) * 1e6 if len(sys.argv) > 1 else 400e6)

import pyarrow.parquet as pq
pf = pq.ParquetFile(sorted(glob.glob("data/kb/wikipedia/20231101.pl/*.parquet"))[3])
for i, b in enumerate(pf.iter_batches(batch_size=2000, columns=["text"])):
    feed(b.column(0).to_pylist())
    if i >= 60:
        break
print("wiki", nchars, file=sys.stderr)
np.save("work/vt/counts.npy", counts)
print("chars", nchars, "distinct", int((counts > 0).sum()))
