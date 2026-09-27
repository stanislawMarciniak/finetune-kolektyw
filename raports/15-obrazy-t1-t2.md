# 15 — Obrazy w T1 i T2 bez OCR: precyzja mmproj, kafelki, pomocniczy VLM (nd 27.09, 05:15–06:50)

Sędzia `gpt-6-luna`, zadanie 2024/21 poza mianownikiem. Testy tylko na zadaniach z obrazami (2024: 29 zadań / 33 pkt, 2025: 21 / 25 pkt, 2026: 25 / 30 pkt); reszta arkusza scalona z przebiegów bazowych (`--only-ids` + `--merge-from`), więc jest identyczna z konstrukcji. Przebiegi: prefiks `img-` (`server/img_run.sh`), ocena `server/img_judge.sh`, porównanie `eval/img_compare.py`.

## Podsumowanie

| | Wynik | Decyzja |
|---|---|---|
| **T1: mmproj wyższej precyzji** | nie ma czego podnosić: `mmproj-gemma-4-12b-it-qat-q4_0.gguf` mimo nazwy **nie jest kwantyzowany** (`general.file_type` = BF16; tensory 2× BF16 34 MB + 9× F32 141 MB). Identyczny rozmiar jak `unsloth/gemma-4-12b-it-GGUF/mmproj-BF16.gguf` (175.1 MB); `mmproj-F32` (209 MB) to tylko bezstratne rozszerzenie BF16 → F32. | bez testu, bez zmian |
| **T1: kafelki `--image-tiles`** (obraz + 2–4 nachodzące, powiększone fragmenty) | pkt na zadaniach z obrazami (2 seedy): 2024 23.0 → 24.5, 2025 21.5 → 21.0, 2026 25.0 → 24.0; = **+0.8 pp** na 2024+2025, **−1.7 pp** na 2026. Trudne obrazy bez zmian: 2024/14.1 (mapa 1809) i 2024/25 (Jaruzelski) nadal 0 w obu seedach. Serwer Gemmy pada częściej (3–5× więcej obrazów w zapytaniu), przebieg ~2× dłuższy. | **remis → nie przyjęte** (flaga zostaje w harnessie, domyślnie wyłączona) |
| **T2: opisy obrazów z pomocniczego VLM** (Qwen3.5-0.8B Q8_0 + mmproj F16, 1.02 GB) na konfiguracji z `--ocr` | pkt na zadaniach z obrazami (śr. z 2 przebiegów): 2024 **13.5 → 16.5**, 2025 **11.5 → 15.0**, 2026 **9.0 → 11.5**; = **+5.5 pp** na 2024+2025 (119 pkt), **+4.2 pp** na 2026; ten sam znak w 6/6 parach przebiegów | **PRZYJĘTE** (`caption_server` w T2 tuned), test na sucho OK |
| T1 wnioski od konkurencji | LockedIn (88.33% na mocku) podaje tylko „Gema1 [quancik]” (wcześniej Gemma-4-12B-it Q4_K_XL: 45/60); sofa so good: Gemma 3 12B + „mmproj F16”; nikt nie podaje pomocniczego modelu do obrazów w torze wyniku. Nic do przeniesienia poza tym, że wszyscy używają niekwantyzowanego mmproj — tak jak my. | — |
| T2 KB obrazów (retrieval po podobieństwie obrazu) | pominięte (czas) | — |

**Rozmiary po zmianie:** T1 bez zmian (7.15 GB). **T2: 7.48 (baza) + 0.23 (LoRA) + 0.81 (Qwen3.5-0.8B Q8_0) + 0.20 (mmproj F16) = 8.72 GB** — baza < 8 GB, całość < 8.8 GB (reguła drużyny). **Ryzyko:** strona mówi „weights up to 8 GB on disk”; jeśli organizatorzy liczą wszystkie pliki razem, T2 przekracza 8 GB (żaden VLM z projektorem nie mieści się w 0.29 GB zapasu do 8 GB). Powrót: usunąć klucz `caption_server` z `final_configs.json`.

## 1. T1 — precyzja enkodera obrazu

Sprawdzone repozytoria HF: `google/gemma-4-12B-it-qat-q4_0-gguf` (tylko nasz mmproj, 175 115 616 B), `unsloth/gemma-4-12b-it-GGUF` (`mmproj-BF16` 175 115 840 B, `mmproj-F16` 175 115 840 B, `mmproj-F32` 209 522 240 B); `ggml-org`, `bartowski`, `lmstudio-community` — brak repo pod sprawdzonymi nazwami. Odczyt `gguf.GGUFReader` naszego pliku: `general.file_type = 32` (BF16), 11 tensorów: F32 140.7 MB, BF16 34.4 MB. **Hipoteza „kwantyzowany enkoder psuje odczyt karykatur/map” odpada** — enkoder już ma pełną precyzję treningową. F32 dałby te same wagi (BF16 ⊂ F32), więc nie testowałem.

## 2. T1 — kafelki (`--image-tiles`)

Mechanizm (`harness/run_exam.py`, `image_parts`): dla obrazu o dłuższym boku ≥ 700 px po pełnym obrazie idzie tekst „Powiększone fragmenty obrazu k (lewa górna, …)” i 4 fragmenty 2×2 (nakładka 20%; przy proporcjach ≥ 1.8 albo krótszym boku < 500 px — 2 połowy wzdłuż dłuższego boku), fragmenty < 640×640 px powiększane (LANCZOS, ≤ 2.5×); do polecenia dopisek `TILES_NOTE` („to ten sam obraz, nie osobne źródła”). Każdy fragment dostaje własny budżet tokenów obrazu → ok. 2× większa rozdzielczość liniowa (inaczej niż `--image-min-tokens 1120`, który tylko podnosi budżet jednego obrazu). Domyślnie wyłączone; ignorowane przy `--bare`.

Przebiegi: `img-t1tiles-s42/s43` (H100, port 8811), baza: `gemma4-qat-t1final__s42/__s43` (2026: `t1final__s42` + `fx-t1base-s43`).

| Arkusz (pkt obrazów) | baza (s42 / s43) | kafelki (s42 / s43) | Δ średnio | arkusz %: baza → kafelki |
|---|---|---|---|---|
| 2024 (33) | 25 / 21 | 24 / 25 | +1.5 | 72.9 / 66.1 → 71.2 / 71.2 |
| 2025 (25) | 20 / 23 | 21 / 21 | −0.5 | 71.7 / 73.3 → 71.7 / 70.0 |
| 2026 (30) | 25 / 25 | 25 / 23 | −1.0 | 83.3 / 83.3 → 83.3 / 80.0 |
| **2024+2025 (119)** | | | **+1.0 pkt = +0.8 pp** | |

- Zyski: **2024/10** (podział dochodów z diagramu → sejm egzekucyjny: „B” → „A”, 0 → 1 w obu seedach), 2024/1 (reliefy, 0/0 → 1/1), 2024/5.1 (mapa), 2025/3.1, 2025/7.1 (mapa 1466).
- Straty: **2025/21.2** (1/1 → 0/0: z kafelkami „Oba źródła (1 i 2)” — port w Gdyni przypisany sanacji; bez kafelków „Źródło 1. … logo C.O.P.”), 2024/11.1, 2024/19.1 (portrety), 2026/18.1.
- **2024/14.1** (mapa 1809) — w obu wariantach „Nie … mapa: wojna polsko-bolszewicka / 1812”; sędzia: „mapa przedstawia wojnę z 1809 r.” → 0. Wyższa rozdzielczość nie pomaga: Gemma czyta napisy, ale nie wiąże mapy z kampanią 1809 — to brak wiedzy/rozumowania, nie ostrości. Tak samo 2024/25 (karykatura) i 2025/14.1 (herb).
- Reguła z raportu 11: typ B/D (więcej obrazów w zapytaniu, większe ryzyko awarii CUDA) wymaga ≥ +4 pp i tego samego znaku na 3 arkuszach — jest +0.8 / −1.7 pp → **remis, zostaje obecna konfiguracja**.
- Operacyjnie: w czasie testu serwer Gemmy padł 6 razy („CUDA error: an illegal instruction”, nadzorca go wskrzeszał) na ~150 zadań; 2026 zajęło 22–25 min przy 6 przebiegach równolegle (dodatkowo H100 był dzielony z przebiegami innych agentów).

## 3. T2 — opisy obrazów pomocniczym VLM (`--caption-url`)

**Stan przed:** PLLuM-12B nie ma wizji; T2 widział tylko znacznik `[Obraz: images/25-0.png]` (+ od 05:33 tekst OCR z tesseracta, `--ocr`, dodany przez koordynatora). To główna strata T2 (raport 12: 25 pkt na 2024+2025).

**Mechanizm:** osobny llama-server z Qwen3.5-0.8B Q8_0 + mmproj F16 (jedyny VLM, który mieści się w zapasie 1.09 GB: 0.812 + 0.205 = 1.017 GB; Qwen3.5-2B z projektorem to ≥ 1.44 GB). Przed rozwiązywaniem harness opisuje każdy unikalny obraz raz (równolegle, ~8–30 s na arkusz), po angielsku (0.8B pisze po polsku słabo), promptem `CAPTION_PROMPT`: typ obrazu, **dosłowna transkrypcja napisów z obrazu**, osoby/symbole/przedmioty, dla map: obszar, granice, strzałki, legenda; max 150 słów, bez zgadywania nazw. Kontekst dla VLM = tylko tytuł/podpis źródła (linia przed i 2 po znaczniku). Opis wstawiany do `source_text` pod znacznikiem jako „[Opis obrazu (automatyczny, może zawierać błędy): …]” (jak OCR) i trafia też do zapytania RAG. Błąd VLM → brak opisu, zadanie idzie dalej. `exam_run.sh` uruchamia serwer z klucza `caption_server` na porcie T2 + 50 i dopisuje `--caption-url`.

Warianty promptu: v1 dostawał 700 znaków tekstu źródeł jako kontekst → VLM przepisywał tekst źródła jako „napisy z obrazu” (2024/14.1) i zmyślał; v2 (przyjęty) — tylko tytuł źródła.

### Wyniki — pkt na zadaniach z obrazami (przebiegi a / b; reszta arkusza z `fx-t2ff4`)

| Arkusz (pkt obrazów) | bez OCR, bez opisów | opisy v1 | opisy v2 | **`--ocr` (obecny finał)** | **`--ocr` + opisy v2 (nowy finał)** | Δ vs `--ocr` |
|---|---|---|---|---|---|---|
| 2024 (33) | 11 / 14 / 14* | 17 / 21 | 16 / 14 | 13 / 14 | **16 / 17** | **+3.0** |
| 2025 (25) | 9 / 9 / 10* | 15 / 11 | 14 / 15 | 12 / 11 | **15 / 15** | **+3.5** |
| 2026 (30) | 9 / 11 / 11* | 9 / 7 | 10 / 9 | 9 / 9 | **11 / 12** | **+2.5** |
| arkusz % 2024 / 2025 / 2026 | 50.8 / 47.2 / 50.6 | 61.0 / 53.4 / 46.7 | 54.2 / 55.9 / 49.2 | 51.7 / 50.9 / 48.3 | **56.8 / 56.7 / 52.5** | +5.1 / +5.8 / +4.2 pp |

\* trzeci = `fx-t2ff4` (ten sam kod bez OCR, starszy przebieg). Szum T2 przy temp. 0 między przebiegami: ±1–3 pkt obrazów na arkusz.

- Opisy bez OCR: +8.1 pp (v1) / +6.0 pp (v2) na 2024+2025, ale 2026 −3.9 / −1.4 pp. **Z OCR opisy pomagają na wszystkich trzech arkuszach** (OCR daje dosłowne napisy, VLM — co przedstawia obraz; uzupełniają się).
- Reguła z raportu 11: typ A (jasny mechanizm — model dostaje treść obrazu, której wcześniej nie miał; zmiana dotyka tylko zadań z obrazami) i nawet B (≥ +4 pp przy 2 przebiegach, ten sam znak na 2024, 2025 i 2026) oraz D (nowy model → test na sucho: zrobiony). **Przyjęte.**
- Strony nieprzewidziane: 2024/23.1, 2025/14.1, 2025/21.2, 2026/15.1 — po jednej utracie w jednym z dwóch przebiegów (opis wprowadził w błąd albo szum).
- T2 base (`--bare`) bez zmian → kategoria „Biggest improvement” zyskuje całą różnicę.

### Przykłady (`img-t2ocr-a` → `img-t2ocrcap-a`)

| Zadanie | Opis z VLM (fragment) | Stara odpowiedź (`--ocr`) | Nowa odpowiedź (+ opisy) |
|---|---|---|---|
| **2025/3.1** funkcja budowli z fotografii (1 pkt) | „Photograph … Pont du Gard (Roman aqueduct with 10 arches)” | „Bramę.” → **0** („należało wskazać transport wody”) | „Przenoszenie wody.” → **1** |
| **2024/12.3** barok czy klasycyzm, pomnik nagrobny (1 pkt) | „seated stone statue of a man, likely a king … holding a crown … In front of him lies a defeated figure” | „Klasycyzm … regularny układ kompozycji” → **0** | „Barok … teatralna kompozycja, monarcha jako zwycięzca, a przed nim leży pokonany przeciwnik” → **1** |
| **2025/23** styl obrazu (1 pkt) | „Painting … a group of children and adults carrying pickaxes … rifles, uniforms” | „Barok … dynamika kompozycji” → **0** | „Socrealizm … zbiorowość i praca” → **1** |
| **2024/4** argument: inspiracje greckie i rzymskie (1 pkt) | „church with a green dome and classical columns” | „greckie kolumny z rzymskim łukiem triumfalnym” → **0** | „kolumny … greckie, a kopuła … rzymskie” → **1** |
| **2026/1** tabela: cywilizacje + numery z mapy (2 pkt) | „Label 3 … South Asia … Label 4 … East Asia” | „Cywilizacja egipska / Cywilizacja chińska” (bez numerów) → **1** | „egipska 1 / chińska 4” → **2** |

Opisy 0.8B są niedoskonałe (np. 2024/25: „SOLDA” zamiast „Solidarność”, bez rozpoznania Jaruzelskiego; 2025/3.1: „Poland, near the Vistula”), ale typ obrazu, główny obiekt i napisy wystarczają PLLuM-owi w wielu zadaniach „nazwij styl / funkcję / wskaż na mapie”.

## 4. Zmiany w plikach

- `harness/run_exam.py`: `--image-tiles` (`image_parts`, `png_b64`, `TILES_NOTE`, `TILE_NAMES`), `--caption-url` (`CAPTION_PROMPT`, `caption_image`, `add_captions`, wstępne opisy w `main`; w `debug.jsonl` pod `ocr` z kluczem `<ścieżka>#opis`). Domyślne zachowanie i `--bare` bez zmian; edycje innych agentów zachowane.
- `server/exam_run.sh`: opcjonalny klucz `caption_server` → drugi `serve` na porcie `PORT+50`, `--caption-url`, `stop` obu.
- `server/final_configs.json`: **T2 tuned + `caption_server`** (Qwen3.5-0.8B Q8_0 + mmproj F16); stary stan opisany w `_comment_T2_caption_old`. T1, T3 bez zmian.
- `server/RUNBOOK.md` (rozmiary, „Models used” T2), `SOURCE.md` (wiersz T2).
- `server/img_run.sh`, `server/img_judge.sh`, `eval/img_compare.py`; paczka testu na sucho `exams/img_dry` (na H100: 5 zadań z 2025, 4 z obrazami).
- Modele: `~/models/unsloth/Qwen3.5-0.8B-GGUF/{Qwen3.5-0.8B-Q8_0.gguf, mmproj-F16.gguf}` na **H100 i L40S** (sha256 zgodne: `0ad885ff…`, `56e4c6cf…`).

## 5. Test na sucho

`bash server/exam_run.sh exams/img_dry T2 tuned 8805` na H100: „opisy obrazów: 4/4 w 8 s”, `answers.json OK: test2025_v2 5 odpowiedzi`, oba serwery (8805, 8855) zatrzymane. Powtórka po awarii laptopa (07:25–07:40), już z zabezpieczeniem w `exam_run.sh` (brak plików VLM albo serwer opisów nie wstaje → komunikat „UWAGA: serwer opisów obrazów nie wstał”, T2 idzie dalej z samym `--ocr`; gałąź sprawdzona z nieistniejącymi plikami): `bash server/exam_run.sh exams/img_dry T2 tuned 8806` — **H100: „opisy obrazów: 4/4 w 3 s”, `answers.json OK` 5 odpowiedzi; L40S: to samo (4/4 w 3 s, OK)**; w `debug.jsonl` jednocześnie OCR (3.1), opisy (3.1, 8, 18, 23) i `--fill-fields` (19); serwery 8806/8856 zatrzymane na obu maszynach. Pliki VLM na obu maszynach: 811 843 840 B (sha256 `0ad885ff…7a6c`) i 204 987 232 B (`56e4c6cf…2453`). T2 razem: 7 477 204 064 + 228 104 192 + 811 843 840 + 204 987 232 = **8 722 139 328 B**. Na egzaminie T2 tuned na 8402 → VLM na 8452 (bez kolizji z portami z RUNBOOK). Koszt czasu T2: +10–40 s.

## Koszt

Sędzia luna: 441 ocen (reszta skopiowana przez `judge_reuse`) — **≈ 0.86 $ wg cennika `judge_openai.py`** (T2: 0.50 $, T1: 0.36 $), realnie ok. 40% tego; limit 2.50 $. GPU: H100 — własne porty 8811 (Gemma, kafelki), 8822/8823 (VLM + PLLuM; po zakończeniu te numery zajął agent T3 — to już nie moje serwery), 8805/8855 (test na sucho); wszystkie moje serwery zatrzymane. L40S — tylko pobranie plików modelu.
