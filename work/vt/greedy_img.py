"""Greedy identity check with exam images.  python greedy_img.py PORT_A PORT_B"""
import base64, glob, json, sys, urllib.request

pa, pb = sys.argv[1:3]
imgs = ["exams/test2024_v2/images/1-0.png", "exams/test2024_v2/images/10-0.png", "exams/test2024_v2/images/18-0.png"]
imgs = [p for p in imgs if glob.glob(p)] or sorted(glob.glob("exams/test2024_v2/images/*"))[:3]


def gen(port, img):
    b64 = base64.b64encode(open(img, "rb").read()).decode()
    body = {"messages": [{"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
        {"type": "text", "text": "Opisz, co przedstawia ten obraz i z jakiej epoki pochodzi."}]}],
        "max_tokens": 400, "temperature": 0, "top_k": 1, "seed": 1}
    r = json.load(urllib.request.urlopen(urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/chat/completions", json.dumps(body).encode(), {"Content-Type": "application/json"}), timeout=600))
    m = r["choices"][0]["message"]
    return (m.get("reasoning_content") or "") + "\n<<>>\n" + (m.get("content") or ""), r["usage"]


for img in imgs:
    a, ua = gen(pa, img)
    b, ub = gen(pb, img)
    k = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    print(f"{'IDENTICAL' if a == b else 'DIFF@char ' + str(k)} prompt_tokens {ua['prompt_tokens']}/{ub['prompt_tokens']} | {img}")
    print("   A:", repr(a[max(0, k - 40):k + 100]))
    if a != b:
        print("   B:", repr(b[max(0, k - 40):k + 100]))
