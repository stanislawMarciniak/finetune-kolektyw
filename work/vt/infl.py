import json, sys, urllib.request, collections
ports = sys.argv[2:]
def tok(port, text):
    req = urllib.request.Request(f"http://127.0.0.1:{port}/tokenize", json.dumps({"content": text, "add_special": False}).encode(), {"Content-Type": "application/json"})
    return len(json.load(urllib.request.urlopen(req))["tokens"])
S = collections.defaultdict(lambda: [0] * (len(ports) + 1))
for l in open(sys.argv[1]):
    d = json.loads(l); s = S[d["src"]]; s[0] += len(d["text"])
    for k, p in enumerate(ports): s[k + 1] += tok(p, d["text"])
for src, s in S.items():
    base = s[1]
    print(src, "chars", s[0], " ".join(f"p{p}: {1000*s[k+1]/s[0]:.1f} tok/kchar ({100*(s[k+1]/base-1):+.2f}%)" for k, p in enumerate(ports)))
