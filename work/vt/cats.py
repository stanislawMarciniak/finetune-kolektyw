import json, unicodedata, collections
t = json.load(open("work/vt/qwen35/tokenizer.json"))
vocab = t["model"]["vocab"]
bs = list(range(ord("!"), ord("~") + 1)) + list(range(ord("¡"), ord("¬") + 1)) + list(range(ord("®"), ord("ÿ") + 1))
cs = bs[:]; n = 0
for b in range(256):
    if b not in bs:
        bs.append(b); cs.append(256 + n); n += 1
u2b = {chr(c): b for b, c in zip(bs, cs)}


def script(ch):
    if ch.isascii():
        return "ascii"
    name = unicodedata.name(ch, "")
    cat = unicodedata.category(ch)
    if name.startswith("LATIN"):
        return "latin"
    if cat[0] in "PSZN" and not name.startswith(("CJK", "FULLWIDTH", "IDEOGRAPHIC")):
        return "common"
    return name.split(" ")[0] if name else "?"


def cls(s):
    b = bytes(u2b[c] for c in s)
    try:
        txt = b.decode("utf-8")
    except UnicodeDecodeError:
        return "partial"
    sc = {script(c) for c in txt}
    sc.discard("common") if len(sc) > 1 else None
    if sc <= {"ascii"}:
        return "ascii"
    if sc <= {"ascii", "latin", "common"}:
        return "latin"
    if sc <= {"ascii", "common"} or sc == {"common"}:
        return "common"
    return "/".join(sorted(sc - {"ascii", "latin", "common"}))[:30]


if __name__ == "__main__":
    c = collections.Counter(cls(s) for s in vocab)
    for k, v in c.most_common(25):
        print(k, v)
