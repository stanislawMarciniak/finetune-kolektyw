"""Vocabulary trimming of a (quantized) GGUF: keep a token subset, remap ids, slice token_embd/output rows.

  python trim.py SRC.gguf KEEP_IDS.txt OUT.gguf

KEEP_IDS.txt: old token ids (one per line) forming the base set. Added automatically: every non-normal token
(control/user-defined/unused), all single-byte tokens, and the BPE-merge closure (both parts of every merge that
produces a kept token), so any text whose original tokenization uses only kept tokens tokenizes identically.
"""
import sys
import numpy as np
sys.path.insert(0, "/home/kolektyw/llama.cpp/gguf-py")
import gguf
from gguf import GGUFValueType as VT

src, keep_path, out = sys.argv[1:4]
r = gguf.GGUFReader(src)
f = r.fields
tokens = f["tokenizer.ggml.tokens"].contents()
ttype = f["tokenizer.ggml.token_type"].contents()
merges = f["tokenizer.ggml.merges"].contents()
n = len(tokens)
tid = {t: i for i, t in enumerate(tokens)}

keep = np.zeros(n, bool)
for line in open(keep_path):
    if line.strip():
        keep[int(line)] = True
for i, (t, ty) in enumerate(zip(tokens, ttype)):
    if ty != 1 or len(t) == 1:
        keep[i] = True
base_n = int(keep.sum())

by_result = {}
for m in merges:
    a, b = m.split(" ", 1)
    by_result.setdefault(a + b, []).append((a, b))
stack = [tokens[i] for i in np.flatnonzero(keep)]
while stack:
    t = stack.pop()
    for a, b in by_result.get(t, ()):
        for p in (a, b):
            j = tid[p]
            if not keep[j]:
                keep[j] = True
                stack.append(p)
old_ids = np.flatnonzero(keep)
remap = {int(o): k for k, o in enumerate(old_ids)}
kept_set = {tokens[i] for i in old_ids}
new_merges = []
for m in merges:
    a, b = m.split(" ", 1)
    if a in kept_set and b in kept_set and a + b in kept_set:
        new_merges.append(m)
print(f"vocab {n} -> {len(old_ids)} (base {base_n}, closure +{len(old_ids) - base_n}); merges {len(merges)} -> {len(new_merges)}")

w = gguf.GGUFWriter(out, arch=f["general.architecture"].contents())
for field in f.values():
    name = field.name
    if name == "general.architecture" or name.startswith("GGUF."):
        continue
    vt = field.types[0]
    sub = field.types[-1] if vt == VT.ARRAY else None
    val = field.contents()
    if name == "tokenizer.ggml.tokens":
        val = [tokens[i] for i in old_ids]
    elif name == "tokenizer.ggml.token_type":
        val = [ttype[i] for i in old_ids]
    elif name == "tokenizer.ggml.merges":
        val = new_merges
    elif name.startswith("tokenizer.ggml.") and name.endswith("_token_id"):
        val = remap[int(val)]
    w.add_key_value(name, val, vt, sub_type=sub)

tensors = []
for t in r.tensors:
    data = t.data
    if t.name in ("token_embd.weight", "output.weight"):
        assert data.shape[0] == n, (t.name, data.shape)
        data = np.ascontiguousarray(data[old_ids])
    tensors.append((t, data))
    w.add_tensor_info(t.name, data.shape, data.dtype, data.nbytes, t.tensor_type)
w.write_header_to_file()
w.write_kv_data_to_file()
w.write_ti_data_to_file()
for t, data in tensors:
    w.write_tensor_data(data, tensor_endianess=r.endianess)
w.close()
np.savetxt(out + ".oldids.txt", old_ids, fmt="%d")
print("written", out)
