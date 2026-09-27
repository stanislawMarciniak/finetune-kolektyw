# 23 — Podpowiedzi z wyszukiwania podobnych obrazów (nd 27.09, 07:50–08:50)

Pomysł: lokalny korpus obrazów z podpisami (Wikimedia Commons + dawne arkusze CKE), enkoder obrazu, dla każdego obrazu z egzaminu top-k najbliższych i ich podpisy w treści zadania jako `[Podobny obraz w bazie: <podpis>; podobieństwo 0.87]`. Kryterium go/no-go: ręczna ocena trafności top-3 na obrazach z `test2024_v2`, `test2025_v2`, `test2026_v2` (97 miejsc na obraz, 61 różnych obrazów).

## Podsumowanie

| | Wynik |
|---|---|
| **Decyzja** | **NIE przyjęte** (no-go na etapie oceny offline; przebiegów T1/T3 i sędziego nie uruchamiałem, koszt sędziego $0). `final_configs.json` bez zmian. |
| Trafne dokładne dopasowania | **3 z 61 obrazów**: moneta 2026/14 („3 ruble-20 złotych 1835”, sim 0.97), banknot 2025/12 (talar Księstwa Warszawskiego 1810, 0.90; napis i tak czytelny), rycina 2024/8 (Sejm za Zygmunta III, 1622, 0.91) |
| Częściowo trafne (typ/epoka) | ~7 (znaczki plebiscytu górnośląskiego 2024/19, wazy greckie 2025/1, rzymski most/akwedukt 2025/3, winiety prasy II RP 2026/19) |
| **Mylące** (konkretne, błędne wydarzenie) | **~7**: 2024/14.1 (mapa 1809 → „Najazd Mongołów”, „Wojna polsko-rosyjska 1654–1667”, DINOv2: mapa granic II RP z arkusza 2023), 2024/5.1 (wyprawy wikingów → wojna trzydziestoletnia), 2024/2 (królestwa hellenistyczne → „Bliski Wschód w VI w. p.n.e.”, sim 0.95), 2025/7 (mapa 1466 → Polska Chrobrego), 2025/10 (medal tylżycki → medale Władysława IV), 2025/14.1 (mapa powstania styczniowego → wojna trzydziestoletnia), 2026/12 (plan Chocimia → „plany bitew powstania listopadowego”) |
| Zadania trudne z raportu 20 | 0 pomocnych, 4 mylące (2024/14.1, 2024/5.1, 2025/14.1, 2026/12.2); karykatury (2024/25, 2026/15, 2026/20, 2026/24), „Szpilki”, plakaty — bez żadnego trafienia |
| Próg podobieństwa | nie rozdziela trafnych od mylących: trafne 0.90–0.97, mylące 0.88–0.95, szum do 0.93 |

**Dlaczego nie działa:** (1) mapy i plany CKE są przerysowane we własnym stylu wydawnictw szkolnych — enkodery dopasowują styl (każda szara mapa CKE ma 0.94–0.96 do każdej innej), nie treść; (2) duża część źródeł z XX w. (karykatury, okładki, plakaty PRL, Herblock) jest chroniona prawem autorskim i nie ma jej na Commons; (3) podpisy obrazów z arkuszy CKE (tekst strony obok obrazu) często opisują inne zadanie. Tam, gdzie jest dokładne trafienie (moneta, banknot), obraz zwykle ma czytelny napis, który T1 i T3 czytają same, a T2 dostaje z OCR i opisu VLM.

## 1. Enkoder

Tylko wieża obrazu (wyszukiwanie obraz→obraz; tekstowa wieża niepotrzebna), zapis fp16 `safetensors` + procesor w katalogu indeksu, ładowanie wyłącznie z lokalnej ścieżki (`HF_HUB_OFFLINE=1`).

| Enkoder | Plik | Rozmiar | Mieści się w |
|---|---|---|---|
| `facebook/dinov2-small` (22 M par., wymiar 384) | `encoder/model.safetensors` | **44 136 744 B** (44 MB) | T1, T2 (zapas 0.08 GB → 8.766 GB), T3 |
| `google/siglip2-base-patch16-224`, wieża obrazu (93 M, wymiar 768) | `encoder/model.safetensors` | **185 793 128 B** (186 MB) | T1, T3; **nie T2** |

Czas: CPU ~4 s na załadowanie + zapytanie (1 obraz); budowa indeksu 29 tys. obrazów na H100 — ok. 1–1.5 min na enkoder. Oba enkodery dają podobną (złą) jakość; SigLIP2 lepiej trafia w typ obiektu (monety, znaczki, wazy), DINOv2 mocniej łapie styl (mapy CKE).

## 2. Korpus

| Źródło | Obrazy | Uwagi |
|---|---|---|
| Wikimedia Commons | **27 565** (miniatury 330 px, ~1.4 GB) | BFS od 110 kategorii (historia Polski wg epok, powstania, mapy historyczne Polski/Europy/starożytności, Matejko, Grottger, Kossakowie, Brandt, plakaty, karykatury, monety, banknoty, znaczki, architektura, rewolucje, konferencje), głębokość 2, ≤ 200 plików i ≤ 40 podkategorii na kategorię. Podpis = nazwa pliku + ObjectName + opis (pl, jeśli jest) + data + kategoria. Kategorie startowe ogólne, nie dobierane pod zadania testowe. |
| Dawne arkusze CKE (`data/cke/extracted`, formuły 2015, 2023, stara, historia sztuki) | **1 630** | **bez 2405/2505/2605 i Informatorów EM2024–26** (zbiory testowe). Podpis = tekst strony 140 pt nad i 70 pt pod obrazem (pymupdf). |
| **Razem w indeksie** | **29 193** (SigLIP2) / 29 410 (DINOv2) | różnica: pliki dopisane między budowami |

Crawl: Commons ogranicza pojedyncze IP (HTTP 429 z `retry-after`, także na API) i wymaga User-Agenta z kontaktem (bez niego API zwraca stronę błędu). Jedno IP ≈ 4–8 obrazów/s → rozdzielone na 3 IP (H100, L40S, laptop; `--shard i/3`), ~35 min.

## 3. Przykłady (SigLIP2, top-3; pełne listy: `results/imgret/ev_sig_v1.jsonl`, `ev_dino_v1.jsonl`)

| Zadanie (obraz) | Top-1 … top-3 (sim) | Ocena |
|---|---|---|
| 2026/14 moneta Królestwa Polskiego („3 ruble, 81 części czystego złota”) | 3 ruble-20 złotych 1835 SPB, *Coins of Congress Poland (1815–1864)* (0.97); to samo 1836 (0.93), 1838 (0.92) | **trafne** (dokładny obiekt i data) |
| 2024/8 ilustracja z epoki | *Polish Sejm under the reign of Sigismund III Vasa*, 1622 (0.91); to samo, inna kopia (0.87); przygotowania do koronacji Augusta III (0.86) | **trafne** (ale pytanie 8.1 dotyczy nazwy dokumentu — Nihil novi — podpis tego nie daje) |
| 2025/12 banknot | 1 talar 1810 Sobolewski, *Banknotes of the Grand Duchy of Warsaw (1810)* (0.90); 1 talar 1810 Małachowski (0.89) | trafne, ale nadmiarowe (napis na banknocie jest czytelny) |
| 2024/14.1 mapa działań wojennych (1809) | CKE: „Mapa. Najazd Mongołów” (0.88); belgijski sektor NATO w RFN (0.88); *Wojna polsko-rosyjska 1654–1667* (0.88). DINOv2: mapa „Kształtowanie się granic II RP” z arkusza 2023 (0.96) | **mylące** — DINOv2 wzmacnia dokładnie ten błąd, który modele już robią („wojna polsko-bolszewicka”) |
| 2024/2 mapa państw starożytnych (królestwa hellenistyczne) | *Oriente Médio no século VI a.C.* (0.95); *Median Empire … 6th century BC* (0.95); *Diadochs kingdoms* (0.94) | **mylące** przy najwyższym podobieństwie (tylko trzecie trafne) |
| 2025/14.1 mapa jednego z powstań (styczniowe) | wojna trzydziestoletnia, faza duńska (0.91), czesko-palatynacka (0.89), kampania wiosenna 1813 (0.89). DINOv2 #2: *Карта-схема … «Польское восстание 1863 года»* (0.94), ale #1: CKE, tekst konstytucji (0.95) | mylące (SigLIP2) / trafne tylko na 2. miejscu (DINOv2) |
| 2026/12.2 plan bitwy (Chocim 1673) | CKE: „Plany bitew z okresu powstania listopadowego” (0.88) ×2; CKE wojna o dziedzictwo Gustawa Wazy (0.88) | **mylące** |
| 2024/25 rysunek z epoki (Jaruzelski) | karykatura Franciszka Józefa, Karagöz 1908 (0.72); karykatura libańska (0.71); karykatura z hiperinflacji 1923 (0.71) | szum (brak obrazu w korpusie) |

## 4. Decyzja

Reguła (raport 11): przyjmujemy tylko, jeśli zadania docelowe zyskują w 2 seedach, a reszta się nie zmienia. Już ocena offline pokazuje, że podpowiedź byłaby częściej myląca niż pomocna (3 trafne vs ~7 mylących na 61 obrazów, 0 pomocnych vs 4 mylące na zadaniach trudnych), a progu podobieństwa, który by je rozdzielał, nie ma. Maksymalny zysk z 3 trafnych (finały: 2024/8.1 T1 67% / T2 100%, 2026/14.1 T1 50% / T2 100%) to ≤ 1–2 pkt na 3 arkusze, głównie dla T3, wobec realnego ryzyka strat na mapach w „rozstrzygnij”. Przebiegi T1/T3 z sędzią zmierzyłyby tylko szum — **pominięte**. Nic nie kopiowałem na maszyny do konfiguracji egzaminu; `final_configs.json` bez zmian.

Co mogłoby zadziałać (niesprawdzone, po egzaminie): tylko Commons bez obrazów CKE (usuwa dopasowania stylu z przypadkowymi podpisami) + próg ≥ 0.95 + wyłącznie dla obiektów typu moneta/banknot/znaczek/obraz olejny (nie mapy i plany) — przy obecnych danych zostaje 1 trafne (2026/14) i 1 mylące (2024/2).

## 5. Pliki

- `data_gen/img_commons.py` — crawler Commons (BFS po kategoriach, API + miniatury 330 px, `--shard i/m`, obsługa `retry-after`, wznawialny).
- `data_gen/img_cke.py` — obrazy z dawnych arkuszy CKE z podpisem z tekstu strony (wyklucza 2024–2026).
- `harness/img_retrieval.py` — `build` (enkoder → `emb.npy` fp16 + `meta.jsonl` + `encoder/`) i `query`; klasa `Index` używana przez harness.
- `harness/run_exam.py` — **opcjonalne, domyślnie wyłączone** flagi `--img-retrieval PATH --img-retrieval-k 3 --img-retrieval-min-sim X --img-retrieval-device cpu`: top-k podpisów pod znacznikiem `[Obraz: ...]` (funkcja `add_img_hints`), w `debug.jsonl` pod `ocr` z kluczem `<ścieżka>#podobne`, trafiają też do zapytania RAG; błąd (brak indeksu/torcha) → komunikat i egzamin idzie dalej; ignorowane przy `--bare`. Sprawdzone na H100 (`venv-unsloth`, CPU, bez sieci). Edycje innych agentów zachowane; `py_compile` OK. **Nie synchronizowałem `run_exam.py` na maszyny.**
- `eval/img_retrieval_eval.py` — top-k dla wszystkich obrazów z paczek testowych.
- Wyniki (lokalnie, `results/` i `data/` są w `.gitignore`): `results/imgret/ev_sig_v1.jsonl`, `results/imgret/ev_dino_v1.jsonl` (oraz wstępne `ev_sig.jsonl`, `ev_dino.jsonl` na korpusie 4.6 tys.).
- Dane (poza repo): korpus i indeksy na H100 w `~/imgret/` (`commons*`, `cke`, `idx_sig_v1` 232 MB, `idx_dino_v1` 76 MB); lokalnie `data/imgret/cke`, `data/imgret/commons_lap`; na L40S `~/imgret/commons_l40s`. Do usunięcia po hackathonie.

## Koszt

Sędzia: $0. GPU: H100 — tylko budowa indeksów w `venv-unsloth` (~3 min razem z oceną, bez serwerów i portów); L40S — tylko crawl (CPU/sieć). Żadnych procesów innych agentów nie ruszałem; moje crawlery zakończone na wszystkich trzech maszynach.
