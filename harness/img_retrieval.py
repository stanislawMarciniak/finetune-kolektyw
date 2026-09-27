"""Wyszukiwanie podobnych obrazów w lokalnym korpusie z podpisami (raport 23).

Indeks (katalog): encoder/ (wagi HF, fp16, tylko wieża obrazu), emb.npy (N×D fp16, znormalizowane), meta.jsonl
(podpisy, kolejność = wiersze emb), config.json. Działa bez sieci (ładowanie wyłącznie z lokalnego katalogu).

  python harness/img_retrieval.py build --encoder facebook/dinov2-small --corpus DIR [DIR...] --out data/imgret/idx_dino
  python harness/img_retrieval.py query --index data/imgret/idx_dino -k 3 obraz.png [...]
"""
import argparse, json, os, re, sys
from pathlib import Path

import numpy as np

HEAD = "[Podobny obraz w bazie"


def _load_encoder(src, device):
    if Path(src).is_dir():
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    import torch
    from transformers import AutoConfig, AutoImageProcessor, AutoModel
    cfg = AutoConfig.from_pretrained(src)
    dtype = torch.float16 if device.startswith("cuda") else torch.float32
    if "siglip" in cfg.model_type:
        from transformers import SiglipVisionModel, Siglip2VisionModel
        cls = Siglip2VisionModel if cfg.model_type.startswith("siglip2") else SiglipVisionModel
        model = cls.from_pretrained(src, torch_dtype=dtype)
    else:
        model = AutoModel.from_pretrained(src, torch_dtype=dtype)
    proc = AutoImageProcessor.from_pretrained(src)
    return model.to(device).eval(), proc, dtype


class Encoder:
    def __init__(self, src, device=None):
        import torch
        self.torch = torch
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model, self.proc, self.dtype = _load_encoder(src, self.device)

    def embed(self, images, bs=64):
        from PIL import Image
        out = []
        for i in range(0, len(images), bs):
            ims = []
            for x in images[i:i + bs]:
                try:
                    im = x if isinstance(x, Image.Image) else Image.open(x)
                    ims.append(im.convert("RGB"))
                except Exception:
                    ims.append(Image.new("RGB", (224, 224)))
            px = self.proc(images=ims, return_tensors="pt")["pixel_values"].to(self.device, self.dtype)
            with self.torch.no_grad():
                o = self.model(pixel_values=px)
                v = o.pooler_output if getattr(o, "pooler_output", None) is not None else o.last_hidden_state[:, 0]
            v = self.torch.nn.functional.normalize(v.float(), dim=-1)
            out.append(v.cpu().numpy())
        return np.concatenate(out) if out else np.zeros((0, 1), np.float32)


def fmt_caption(r, n=220):
    name = r.get("name", "")
    parts = [name]
    on = r.get("objname", "")
    if on and on.lower() not in name.lower():
        parts.append(on)
    d = r.get("desc", "")
    if d and d.lower()[:40] not in name.lower():
        parts.append(d[:n])
    if r.get("date") and r["date"] not in " ".join(parts):
        parts.append(r["date"])
    cat = r.get("cat", "")
    if cat and not cat.startswith("cke/"):
        parts.append(f"kategoria Commons: {cat}")
    return re.sub(r"\s+", " ", "; ".join(p for p in parts if p)).strip()


class Index:
    def __init__(self, path, device="cpu"):
        p = Path(path)
        self.emb = np.load(p / "emb.npy").astype(np.float32)
        self.meta = [json.loads(l) for l in (p / "meta.jsonl").open()]
        self.enc = Encoder(str(p / "encoder"), device)

    def search(self, images, k=3, min_sim=0.0):
        q = self.enc.embed(images)
        sims = q @ self.emb.T
        res = []
        for row in sims:
            idx = np.argsort(-row)[: k * 4]
            hits, seen = [], set()
            for j in idx:
                if row[j] < min_sim or len(hits) >= k:
                    break
                c = fmt_caption(self.meta[j])
                if c in seen:
                    continue
                seen.add(c)
                hits.append({"sim": float(row[j]), "caption": c, "id": self.meta[j].get("title", "")})
            res.append(hits)
        return res


def hint_block(hits):
    return "\n".join(f"{HEAD}: {h['caption']}; podobieństwo {h['sim']:.2f}]" for h in hits)


def build(a):
    import torch
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    enc = Encoder(a.encoder, "cuda" if torch.cuda.is_available() else "cpu")
    metas, paths = [], []
    for d in a.corpus:
        d = Path(d).expanduser()
        for l in (d / "meta.jsonl").open():
            r = json.loads(l)
            f = d / r["file"]
            if f.exists():
                r["file"] = str(f)
                metas.append(r); paths.append(f)
    print("obrazów:", len(paths), flush=True)
    embs = []
    for i in range(0, len(paths), 2048):
        embs.append(enc.embed(paths[i:i + 2048], bs=128))
        print(i + len(embs[-1]), flush=True)
    emb = np.concatenate(embs).astype(np.float16)
    np.save(out / "emb.npy", emb)
    with (out / "meta.jsonl").open("w") as f:
        for r in metas:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    enc.model.half().save_pretrained(out / "encoder", safe_serialization=True)
    enc.proc.save_pretrained(out / "encoder")
    json.dump({"encoder": a.encoder, "n": len(metas), "dim": int(emb.shape[1])}, (out / "config.json").open("w"))
    print("zapisano", out, emb.shape, flush=True)


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    b = sp.add_parser("build"); b.add_argument("--encoder", required=True); b.add_argument("--corpus", nargs="+", required=True)
    b.add_argument("--out", required=True)
    q = sp.add_parser("query"); q.add_argument("--index", required=True); q.add_argument("-k", type=int, default=3)
    q.add_argument("--min-sim", type=float, default=0.0); q.add_argument("images", nargs="+")
    a = ap.parse_args()
    if a.cmd == "build":
        build(a)
    else:
        idx = Index(a.index)
        for p, hits in zip(a.images, idx.search(a.images, a.k, a.min_sim)):
            print(p); print(hint_block(hits))


if __name__ == "__main__":
    main()
