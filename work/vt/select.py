"""Build keep-id lists.  python select.py
  keep_script.txt : all ascii/latin/common(+greek) tokens + corpus-seen tokens
  keep_corpus{N}.txt : tokens seen >= N times in the corpus + ascii/latin single 'words' up to rank cutoff
"""
import json, sys
import numpy as np
sys.path.insert(0, "work/vt")
from cats import cls, vocab

counts = np.load("work/vt/counts.npy")
id2s = {i: s for s, i in vocab.items()}
c = {i: cls(s) for i, s in id2s.items()}
seen = set(np.flatnonzero(counts > 0).tolist())
lat = {i for i, k in c.items() if k in ("ascii", "latin", "common", "GREEK")}


def dump(name, ids):
    ids = sorted(ids)
    open(f"work/vt/{name}.txt", "w").write("\n".join(map(str, ids)) + "\n")
    print(name, len(ids))


dump("keep_script", lat | seen)
dump("keep_seen1", seen)
dump("keep_seen2", set(np.flatnonzero(counts > 1).tolist()))
# seen + ASCII tokens with low id (BPE ids ~ merge order ~ frequency in Qwen's training data)
for cut in (40000, 80000):
    dump(f"keep_seen_a{cut // 1000}k", seen | {i for i in lat if i < cut})
