"""Pobiera arkusze, zasady oceniania i informatory z historii ze strony CKE.

Wynik: data/cke/raw/<formula>/<plik>.pdf oraz data/cke/raw/manifest.jsonl.
Do repo trafia tylko ten skrypt (PDF-y zawierają materiały osób trzecich).
"""

import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "cke" / "raw"
BASE = "https://cke.gov.pl"

START_PAGES = {
    "f2023": [
        "/egzamin-maturalny/egzamin-maturalny-w-formule-2023/arkusze/",
        "/egzamin-maturalny/egzamin-maturalny-w-formule-2023/arkusze/2023-2/",
        "/egzamin-maturalny/egzamin-maturalny-w-formule-2023/arkusze/2024-2/",
        "/egzamin-maturalny/egzamin-maturalny-w-formule-2023/arkusze/2025-2/",
        "/egzamin-maturalny/egzamin-maturalny-w-formule-2023/arkusze/2026-2/",
        "/egzamin-maturalny/egzamin-maturalny-w-formule-2023/informatory/",
    ],
    "f2015": ["/egzamin-maturalny/egzamin-maturalny-w-formule-2015/arkusze/"],
    "stara": ["/egzamin-maturalny/egzamin-w-starej-formule/arkusze/"],
}

HISTORY = re.compile(r"(histori|/MHI|MHIP|MHI-|_hist|historia)", re.I)
ART = re.compile(r"(Historia_sztuki|Historia_muzyki|MHS|MHM|sztuk|muzyk)", re.I)
session = requests.Session()
session.headers["User-Agent"] = "Mozilla/5.0 (matura-hackathon research crawler)"


def get(url, **kw):
    for attempt in range(4):
        try:
            r = session.get(url, timeout=60, **kw)
            if r.status_code == 200:
                return r
            if r.status_code == 404:
                return None
        except requests.RequestException as e:
            print("retry", url, e, flush=True)
        time.sleep(2 * (attempt + 1))
    return None


def links(url):
    r = get(url)
    if r is None:
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    return [urljoin(url, a["href"]) for a in soup.find_all("a", href=True)]


def classify(url):
    name = urlparse(url).path.lower()
    if "zasady" in name or "klucz" in name or "odpowiedzi" in name or "schemat" in name:
        return "zasady"
    if "informator" in name or "aneks" in name:
        return "informator"
    if "karta" in name:
        return "karta"
    if "transkryp" in name or "nagran" in name:
        return "inne"
    return "arkusz"


def year_of(url):
    m = re.search(r"/(20[0-2]\d)/", url) or re.search(r"(20[0-2]\d)", url)
    return int(m.group(1)) if m else None


def crawl(formula, starts, max_pages=400):
    seen_pages, pdfs = set(), set()
    queue = [urljoin(BASE, s) for s in starts]
    prefixes = [urlparse(urljoin(BASE, s)).path for s in starts]
    while queue and len(seen_pages) < max_pages:
        page = queue.pop(0)
        if page in seen_pages:
            continue
        seen_pages.add(page)
        for href in links(page):
            path = urlparse(href).path
            if path.lower().endswith(".pdf"):
                if HISTORY.search(path):
                    pdfs.add(href.replace("http://", "https://"))
            elif any(path.startswith(p) for p in prefixes) and "cke.gov.pl" in href and "#" not in href:
                if href not in seen_pages and "wp-json" not in href:
                    queue.append(href)
        time.sleep(0.2)
    print(f"[{formula}] pages={len(seen_pages)} pdfs={len(pdfs)}", flush=True)
    return sorted(pdfs)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = OUT / "manifest.jsonl"
    done = set()
    if manifest.exists():
        done = {json.loads(l)["url"] for l in manifest.open()}
    with manifest.open("a") as mf:
        for formula, starts in START_PAGES.items():
            for url in crawl(formula, starts):
                if url in done:
                    continue
                sub = "art" if ART.search(url) else formula
                dest = OUT / sub / Path(urlparse(url).path).name
                dest.parent.mkdir(parents=True, exist_ok=True)
                if not dest.exists():
                    r = get(url)
                    if r is None:
                        print("FAIL", url, flush=True)
                        continue
                    dest.write_bytes(r.content)
                rec = {"url": url, "formula": sub, "year": year_of(url), "kind": classify(url),
                       "path": str(dest.relative_to(ROOT)), "bytes": dest.stat().st_size}
                mf.write(json.dumps(rec, ensure_ascii=False) + "\n")
                mf.flush()
                print("ok", rec["formula"], rec["year"], rec["kind"], dest.name, flush=True)
                time.sleep(0.2)
    print("DONE", flush=True)


if __name__ == "__main__":
    sys.exit(main())
