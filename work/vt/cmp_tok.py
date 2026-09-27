"""Compare tokenization of two llama-servers on held-out texts.  python cmp_tok.py heldout.jsonl PORT_ORIG PORT_NEW [oldids.txt]"""
import json, sys, urllib.request

path, po, pn = sys.argv[1:4]
oldids = [int(x) for x in open(sys.argv[4])] if len(sys.argv) > 4 else None
kept = set(oldids) if oldids else None


def tok(port, text):
    req = urllib.request.Request(f"http://127.0.0.1:{port}/tokenize", json.dumps(
        {"content": text, "add_special": False, "parse_special": True, "with_pieces": True}).encode(),
        {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req))["tokens"]


def detok(port, ids):
    req = urllib.request.Request(f"http://127.0.0.1:{port}/detokenize", json.dumps({"tokens": ids}).encode(),
                                 {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req))["content"]


stats = {}
for line in open(path):
    d = json.loads(line)
    src, text = d["src"], d["text"]
    a, b = tok(po, text), tok(pn, text)
    s = stats.setdefault(src, dict(n=0, same=0, all_kept=0, all_kept_same=0, tok_o=0, tok_n=0, rt_ok=0))
    s["n"] += 1
    s["tok_o"] += len(a); s["tok_n"] += len(b)
    same = [x["piece"] for x in a] == [x["piece"] for x in b]
    s["same"] += same
    if kept is not None and all(x["id"] in kept for x in a):
        s["all_kept"] += 1
        s["all_kept_same"] += same
        if not same:
            print("MISMATCH (all kept)", src, repr(text[:80]))
    s["rt_ok"] += detok(pn, [x["id"] for x in b]) == detok(po, [x["id"] for x in a])
for k, s in stats.items():
    print(k, s)
