"""Korpus obrazów z Wikimedia Commons do wyszukiwania po podobieństwie obrazu (raport 23).

BFS po kategoriach (głębokość, limity plików/podkategorii na kategorię), metadane przez API (jedno zapytanie naraz),
miniatury 330 px (standardowy rozmiar, cache CDN) pobierane równolegle. Wynik: OUT/imgs/<n>.jpg + OUT/meta.jsonl
({"id", "file", "title", "desc", "date", "cat"}). Wznawialne: pomija pliki już zapisane w meta.jsonl.

  python data_gen/img_commons.py --out ~/imgret/commons --max-files 40000
"""
import argparse, html, json, re, sys, threading, time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

UA = "KolektywMaturaHackathon/0.2 (https://warsawmodeltrainers.dev; kolektyw.hackathon@gmail.com) requests"
API = "https://commons.wikimedia.org/w/api.php"

SEEDS = [
    # Polska: epoki, powstania, państwo
    "History of Poland", "Maps of the history of Poland", "Old maps of Poland", "Partitions of Poland",
    "Duchy of Warsaw", "Congress Poland", "Kościuszko Uprising", "November Uprising", "January Uprising",
    "Polish Legions in Italy", "Constitution of 3 May 1791", "Bar Confederation", "Deluge (history)",
    "Polish–Lithuanian Commonwealth", "Piast dynasty", "Jagiellonian dynasty", "Kings of Poland",
    "Second Polish Republic", "Polish–Soviet War", "Polish Legions in World War I", "Greater Poland uprising (1918–1919)",
    "Silesian Uprisings", "Invasion of Poland", "Warsaw Uprising", "Polish Underground State", "Home Army",
    "Polish Armed Forces in the West", "Katyn massacre", "Polish People's Republic", "Solidarity (Polish trade union)",
    "Polish October", "Poznań 1956 protests", "Martial law in Poland", "Round Table Agreement", "Polish 1970 protests",
    "Polish 1980 strikes",
    # sztuka, plakaty, karykatury, pieniądze, znaczki
    "Paintings by Jan Matejko", "Paintings by Artur Grottger", "Paintings by Juliusz Kossak",
    "Paintings by Wojciech Kossak", "Paintings by Józef Brandt", "Paintings by Piotr Michałowski",
    "Paintings by Marcello Bacciarelli", "Paintings by Bernardo Bellotto", "History paintings",
    "Socialist realist paintings", "Polish posters", "Propaganda posters of Poland", "Political posters of Poland",
    "World War II posters", "World War I posters", "Soviet propaganda posters", "Nazi propaganda posters",
    "Political cartoons", "Caricatures", "Punch (magazine) cartoons", "Satirical cartoons", "Cartoons by Thomas Nast",
    "Coins of Poland", "Banknotes of Poland", "Stamps of Poland", "Medieval coins", "Ancient Greek coins",
    "Roman Republican coins", "Seals of Poland", "Coats of arms of Poland", "Polish heraldry",
    # architektura
    "Romanesque architecture in Poland", "Gothic architecture in Poland", "Renaissance architecture in Poland",
    "Baroque architecture in Poland", "Neoclassical architecture in Poland", "Wawel", "Socialist realist architecture",
    "Ancient Greek architecture", "Ancient Roman architecture", "Gothic cathedrals in France",
    # świat
    "Maps of the Napoleonic Wars", "Maps of World War I", "Maps of World War II", "Maps of the Cold War",
    "Maps of the Roman Empire", "Maps of ancient Greece", "Maps of ancient Egypt", "Maps of Mesopotamia",
    "Maps of the Crusades", "Maps of the Viking Age", "Maps of the Holy Roman Empire", "Maps of the Middle Ages",
    "Maps of the Age of Discovery", "Maps of the Ottoman Empire", "Maps of Russian Empire", "Maps of the Soviet Union",
    "Maps of the Thirty Years' War", "Maps of the history of Europe", "Maps of the history of Lithuania",
    "Maps of the Teutonic Order", "Teutonic Order", "Ancient Egyptian reliefs", "Assyrian reliefs", "Ancient Greek pottery",
    "Bayeux Tapestry", "Illuminated manuscripts of Poland", "French Revolution", "Napoleonic Wars",
    "American Revolutionary War", "Industrial Revolution", "Paris Peace Conference, 1919", "Yalta Conference",
    "Potsdam Conference", "Berlin Wall", "Holocaust", "Historical photographs of Warsaw", "Reformation",
    "Protestant Reformation", "Printing press", "Renaissance paintings", "Paintings by Jacques-Louis David",
]

TAG = re.compile(r"<[^>]+>")
SKIP_MIME = ("application/", "audio/", "video/")


def clean(s, n=400):
    s = html.unescape(TAG.sub(" ", s or ""))
    return re.sub(r"\s+", " ", s).strip()[:n]


class Crawler:
    def __init__(self, a):
        self.a, self.out = a, Path(a.out).expanduser()
        (self.out / "imgs").mkdir(parents=True, exist_ok=True)
        self.s = requests.Session()
        self.s.headers["User-Agent"] = UA
        self.meta_f = self.out / "meta.jsonl"
        self.seen = set()
        self.n = 0
        if self.meta_f.exists():
            for l in self.meta_f.open():
                r = json.loads(l)
                self.seen.add(r["title"])
                self.n = max(self.n, r["id"] + 1)
        self.lock = threading.Lock()
        self.fails = 0

    def api(self, **p):
        p.update(action="query", format="json", formatversion=2, maxlag=5)
        for t in range(6):
            try:
                r = self.s.get(API, params=p, timeout=30)
                if r.status_code == 429 or "maxlag" in r.text[:200]:
                    time.sleep(float(r.headers.get("retry-after", 5)) + 3 * t); continue
                return r.json()
            except Exception as e:
                print("api err", e, file=sys.stderr); time.sleep(3 * (t + 1))
        return {}

    def members(self, cat):
        """(pliki z metadanymi, podkategorie) jednej kategorii, z limitami."""
        files, cont = [], {}
        d = self.api(list="categorymembers", cmtitle="Category:" + cat, cmtype="subcat", cmlimit=self.a.subs_per_cat)
        subs = [m["title"].split(":", 1)[1] for m in d.get("query", {}).get("categorymembers", [])]
        while len(files) < self.a.per_cat:
            d = self.api(generator="categorymembers", gcmtitle="Category:" + cat, gcmtype="file", gcmlimit=50,
                         prop="imageinfo", iiprop="url|mime|extmetadata", iiurlwidth=330,
                         iiextmetadatafilter="ImageDescription|ObjectName|DateTimeOriginal",
                         iiextmetadatalanguage="pl", **cont)
            for pg in d.get("query", {}).get("pages", []):
                if pg.get("ns") == 14:
                    subs.append(pg["title"].split(":", 1)[1])
                elif pg.get("ns") == 6 and pg.get("imageinfo"):
                    files.append(pg)
            if "continue" not in d:
                break
            cont = {k: v for k, v in d["continue"].items() if k != "continue"}
            cont["continue"] = d["continue"].get("continue", "")
        return files, subs

    def download(self, rec, url):
        path = self.out / "imgs" / f"{rec['id']}.jpg"
        for t in range(4):
            try:
                r = self.s.get(url, timeout=30)
                if r.status_code == 429:
                    time.sleep(float(r.headers.get("retry-after", 10)) + 2 * t); continue
                if r.status_code != 200 or len(r.content) < 2000:
                    break
                path.write_bytes(r.content)
                with self.lock:
                    self.meta_f.open("a").write(json.dumps(rec, ensure_ascii=False) + "\n")
                return
            except Exception:
                time.sleep(3)
        with self.lock:
            self.fails += 1

    def cat_worker(self, q, done_cats, pool, t0):
        while self.n < self.a.max_files and time.time() - t0 < self.a.max_minutes * 60:
            with self.lock:
                if not q:
                    if self.active == 0:
                        return
                    item = None
                else:
                    item = q.popleft()
                    if item[0] in done_cats:
                        continue
                    done_cats.add(item[0])
                    self.active += 1
            if item is None:
                time.sleep(1); continue
            cat, depth = item
            try:
                files, subs = self.members(cat)
            except Exception as e:
                print("cat err", cat, e, file=sys.stderr); files, subs = [], []
            for pg in files:
                ii = pg["imageinfo"][0]
                with self.lock:
                    if pg["title"] in self.seen or ii.get("mime", "").startswith(SKIP_MIME) or not ii.get("thumburl"):
                        continue
                    self.seen.add(pg["title"])
                    rid = self.n; self.n += 1
                em = ii.get("extmetadata", {})
                g = lambda k: clean((em.get(k) or {}).get("value", ""))
                rec = {"id": rid, "title": pg["title"], "file": f"imgs/{rid}.jpg",
                       "name": re.sub(r"\.\w{3,4}$", "", pg["title"].split(":", 1)[1]).replace("_", " "),
                       "objname": g("ObjectName")[:150], "desc": g("ImageDescription"),
                       "date": g("DateTimeOriginal")[:40], "cat": cat}
                pool.submit(self.download, rec, ii["thumburl"])
            with self.lock:
                if depth < self.a.depth:
                    q.extend((s, depth + 1) for s in subs)
                self.active -= 1
            print(f"{time.time() - t0:6.0f}s cat={cat[:50]!r} d={depth} files={len(files)} subs={len(subs)} "
                  f"total_id={self.n} fails={self.fails} q={len(q)} dlq={pool._work_queue.qsize()}", flush=True)
            while pool._work_queue.qsize() > 600:
                time.sleep(0.5)

    def run(self):
        i, m = map(int, self.a.shard.split("/"))
        q = deque((s, 0) for j, s in enumerate(SEEDS) if j % m == i)
        done_cats, self.active = set(), 0
        pool = ThreadPoolExecutor(self.a.workers)
        t0 = time.time()
        cats = [threading.Thread(target=self.cat_worker, args=(q, done_cats, pool, t0)) for _ in range(self.a.api_workers)]
        for t in cats:
            t.start()
        for t in cats:
            t.join()
        pool.shutdown(wait=True)
        print("DONE", self.n, "fails", self.fails, flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-files", type=int, default=40000)
    ap.add_argument("--max-minutes", type=float, default=45)
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument("--per-cat", type=int, default=250)
    ap.add_argument("--subs-per-cat", type=int, default=40)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--api-workers", type=int, default=3)
    ap.add_argument("--shard", default="0/1", help="i/m: tylko co m-ta kategoria startowa (kilka maszyn = kilka IP)")
    Crawler(ap.parse_args()).run()
