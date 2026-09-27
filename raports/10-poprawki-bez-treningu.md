# 10 — Poprawki bez treningu: harness, flagi serwera, OCR, baza wiedzy (nd 27.09, 02:10–04:15)

Sędzia `gpt-6-luna` jak w raporcie 09; zadanie 2024/21 poza mianownikiem. Wynik główny = 2024 + 2025 (119 pkt), potwierdzenie = 2026. Nowe przebiegi mają w nazwie `__nt` (`runs/<zbiór>/<przebieg>/`, oceny `results/grades/<zbiór>/<przebieg>.{auto,judge}.json`). Szum między seedami ~2–3 pp. Termin skrócono do 04:15, więc większość wariantów ma **jeden seed** — traktuj je jako wskazówkę, nie dowód.

## Podsumowanie

| Track | Obecny finał (przed) | Najlepsza zmiana bez treningu | Decyzja |
|---|---|---|---|
| **T3** | Qwen3.5-4B Q3_K_M **2.29 GB**, temp. 0.6: 50.0% (2 seedy), 48.3% na 2026 | **UD-IQ3_XXS 1.95 GB** + limit myślenia serwera 5000 tokenów + nagłówek eseju z treści + dopisywanie akapitów < 300 wyrazów: **43.3%** (42.9 / 43.7, 2 seedy), **42.5%** na 2026 (41.7 / 43.3); było 36.1% | **ZMIANA w `final_configs.json`: rozmiar −0.34 GB (−15%)**, margines nad 35% ~7–8 pp |
| **T1** | Gemma-4-12B QAT t1final: 71.0% (72.3 / 69.7), 83.3% na 2026 | `--image-min-tokens 1120`: 73.5% (74.8 / 72.3); refine eseju z bazą: +0.7 pkt / esej | bez zmian (+2.5 pp < 3 pp; zysk głównie z eseju; na 2026 80.0% vs 83.3%, 2 seedy) |
| **T2** | PLLuM + LoRA + RAG: 52.9%, 41.7% na 2026 | HyDE / kb-rag-k 2–3 / OCR: bez eseju wszystkie 53.9% vs 52.8% | bez zmian (szum; OCR/HyDE +3–5 pp tylko na obrazach) |

Najważniejsze obserwacje:
1. **Pętle myślenia małych kwantyzacji to realny, naprawialny problem**: limit 5000 tokenów z komunikatem zamykającym zbija powtórki bez myślenia z ~45–55 do ~4 na 2 arkusze i daje +4–5 pp przy tej samej temperaturze (IQ3_XXS 38.7 → 42.9%, IQ2_M 29.4 → 34.5%). Q3_K_S na 2026: 35.0 → 48.3%. **Ale Q3_K_M (mało pętli) traci** (50.0 → 45.4%) — limit ucina też dobre długie myślenie.
2. **Dopisywanie akapitów pomaga tylko esejom < 300 wyrazów** (4 → 7 pkt na 5 esejach); przy dłuższych dopisane akapity wnoszą błędy (13 → 7). Stąd próg 300.
3. **Nagłówek tematu z treści**: 7/7 znanych błędnych nagłówków wykrytych i poprawionych, 0 fałszywych poprawek na 96 esejach.
4. **Eseje dominują szum**: w T2 (temp. 0!) esej 2025 zmienia się o 6 pkt między przebiegami bez zmiany promptu eseju; w T1 esej odpowiada za większość różnic między wariantami.

**Koszt sędziego:** ~2.7 $ z limitu 4.5 $ (ok. 20 przebiegów × arkusz + ~60 par esejów); `eval/judge_reuse.py` skopiował ~700 ocen identycznych odpowiedzi (głównie pary esejów i T2).

## A. Co zaimplementowano (harness/run_exam.py, wszystko za flagami; `--bare` bez zmian)

| Flaga | Co robi |
|---|---|
| `--essay-extend N` (+ `--essay-min-words 350`) | Za krótki esej: zamiast przepisywania całości („do około 450 wyrazów” — Qwen znów pisał ~250) model dopisuje 1–2 akapity rozwinięcia z nowymi faktami (ze wskazaniem aspektów tematu); akapity wstawiane przed zakończeniem; do N rund. Odrzuca dopiski < 40 wyrazów i „przepisania całości”. |
| `--essay-topic-detect` | Numer tematu z treści eseju: słowa charakterystyczne tylko dla jednego z trzech tematów (`eval/rag_precompute.terms`), wynik tylko przy wyraźnej przewadze (≥ 3 i ≥ 2× drugi + 1); inaczej stare pytanie modelu o cyfrę. Nagłówek napisany przez model zostaje, chyba że treść bardzo wyraźnie wskazuje inny temat (≥ 10 i ≥ 3× drugi) — wtedy cyfra jest poprawiana. |
| `--essay-refine-kb PATH` (+ `--essay-refine-k 6`, `--essay-refine-think`) | Drugie przejście eseju: pierwszy esej bez bazy (model sam wybiera temat), potem notatki dla tezy wybranego tematu i dla każdego aspektu (zapytanie = nazwy własne tezy + słownik aspektu, np. społeczno-gospodarczy → „przywilej szlachta chłopi miasta handel…”), filtr notatek bez wspólnych nazw własnych z tezą/esejem (np. „Dżoser” trafiany przez „dynastii”). Poprawka przyjmowana tylko przy tym samym temacie, nie krótsza i nieurwana. |
| `--ocr` (+ `--ocr-cache`) | Tesseract 5 (pol+eng, zainstalowany przez apt na **obu** maszynach), dwa tryby: `--psm 3` (bloki tekstu) i `--psm 11` (rozproszone napisy map); filtr śmieci (linie z ≥ 60% „dobrych” słów, min. 3 słowa); tekst wstawiany pod znacznikiem obrazu jako `[Tekst odczytany z obrazu (OCR, może zawierać błędy): …]` i trafia do zapytania RAG. Pamięć podręczna po sha1 obrazu (`~/.cache/matura_ocr`), `OMP_THREAD_LIMIT=1`. |
| `--rag-clean-query` | Usuwa `[Obraz: …png]` i adresy z zapytania RAG (źródło śmieciowych trafień typu „Adam7”). |
| `--only-ids`, `--merge-from DIR` | Tylko wybrane zadania; reszta kopiowana z innego przebiegu (tanie powtórki, np. same eseje albo same zadania z obrazami). |
| `--essay-from DIR` | Pierwsza wersja eseju brana z istniejącego przebiegu — pary przed/po na **tych samych** esejach (esej ma ogromny rozrzut między próbkami). |

Nowe narzędzia: `eval/judge_reuse.py` (kopiuje oceny identycznych odpowiedzi z już ocenionych przebiegów — sędzia ocenia tylko to, co się zmieniło), `server/nt_*.sh` (skrypty eksperymentów), `server/nt_judge.sh` (ściągnięcie + ocena).

### Walidacja wykrywania tematu (wszystkie eseje w `runs/*`, 96 esejów)

- 79 esejów: nagłówek zgodny z wykryciem; **7: nagłówek błędny, wykrycie poprawne** (wszystkie wstawione przez stare pytanie o cyfrę), np. `q35-4b-q3ks__t3cfg` 2025: esej o Jagielle z nagłówkiem „Temat nr 3” (wynik sędziego 0), `pllum-12b-base-sft__v2` 2026: esej o klęsce 1939 z „Temat nr 1”, `q35-4b-iq2m__t3cfg` 2024: esej o Piłsudskim z „Temat nr 2”. Wszystkie 7 zostałyby poprawione (`fixed`).
- 6 esejów: wynik niejasny → stare pytanie modelu (bez zmian zachowania).

## T3 — Qwen3.5-4B, najmniejszy plik ≥ 35%

### Limit myślenia (serwer: `--reasoning-budget 5000 --reasoning-budget-message "\n\nNa podstawie powyższych rozważań podaję ostateczną odpowiedź.\n"`)

Po 5000 tokenach myślenia serwer wstawia komunikat i zamyka myślenie; model odpowiada z zachowanym rozumowaniem (finish = stop) zamiast urwania na 8000 i powtórki bez myślenia.

| Kwantyzacja (plik) | przed: T3 cfg temp 1.0, s42 | przed: stock temp 0.6, s42 | **po: limit 5000, temp 0.6, s42** | powtórki bez myślenia (przed → po) | 2026 |
|---|---|---|---|---|---|
| Q3_K_M 2.29 GB (obecny finał) | 48.7% | 48.7 / 51.3% (s42/s43) | 45.4% (gorzej) | 25 → 0 | 48.3% (finał) |
| Q3_K_S 2.11 GB | 36.1% | 37.8% | **42.0%** | 52 / 55 → **4** | 35.0% → **48.3%** (limit + poprawki eseju, s42) |
| UD-IQ3_XXS 1.95 GB | 36.1% | 38.7% | **42.9%** (s43 z poprawkami eseju: 43.7%) | 44 / 49 → **4** | **41.7%** (limit + poprawki eseju, s43; 1 powtórka) |
| UD-IQ2_M 1.76 GB | 21.0% | 29.4% | **34.5%** | 57 / 63 → 22 | — |

- Q3_K_S: czysty efekt limitu 37.8 → 42.0% (+4.2 pp).
- Czysty efekt limitu (IQ3_XXS, ta sama temp. 0.6): **38.7 → 42.9% (+4.2 pp)**, bilans zadań +15 / −10 pkt, głównie „rozstrzygnij” (+6 pkt). Temperatura 1.0 → 0.6 daje osobno +2.6 pp.
- **Q3_K_M z limitem jest gorszy** (45.4% vs 50.0% średnio): ma mało pętli, a limit 5000 ucina też myślenie, które kończyłoby się między 5000 a 8000 tokenów. Limit pomaga tylko kwantyzacjom, które się zapętlają — **nie zmieniać finału dla Q3_K_M**.
- IQ2_M: limit daje +5.1 pp (29.4 → 34.5%), łącznie z temperaturą +13.5 pp, ale nadal < 35%; eseje po ~1750 wyrazów (pętle w eseju bez myślenia), 3% za esej. Wariant z `--presence-penalty 1.0` + poprawki eseju (`q35-4b-iq2m__nt3rbppE3-s42`): znowu **34.5%** — powtórki 22 → 6, eseje 1750 → ~370 wyrazów (esej 3 → 10%), ale zamknięte 45 → 30%. IQ2_M odpada; UD-IQ2_XXS nie pobierany.

Rozbicie IQ3_XXS (przed → po): zamknięte 45.0 → 50.0%, otwarte 46.4 → 56.5%, obrazy 51.7 → 56.9%, bez obrazów 35.5 → 51.6%, Polska 33.9 → 50.8%, esej 6.7 → 6.7%.

Przykłady (IQ3_XXS, `q35-4b-iq3xxs__t3cfg` → `q35-4b-iq3xxs__nt3rb-s42`; „fallback” = myślenie urwane na 8000 tokenach i powtórka bez myślenia):

| Zadanie | Przed (fallback) | Po (limit 5000) |
|---|---|---|
| 2025/24.2 (podaj, 1 pkt) | 0: „Krajem, w którym w 1989 roku doszło do krwawego obalenia dyktatury komunistycznej, jest Rzeczpospolota Północna Irakia? Nie, to błędne. To Rzeczpospol…” (27 tys. znaków myślenia wyrzucone) | 1: „Rumunia” (komunikat limitu w myśleniu, finish = stop) |
| 2024/22.1 (data godziny „W”) | 0: „…datą dzienną … jest 23 lipca 1944 roku” | 1: „1.8.1944” |
| 2024/15.1 | 0: „powstanie listopadowe (1830–1831), znane również jako wojsko-wojewódzka (lub powstanie styczniowe…)” | 1: „Powstanie listopadowe.” |
| 2025/16.2 (rewolucja 1905) | 0: „Tak, rewolucja … zakończyła się obaleniem monarchii” | 1: „Nie. … Rewolucja rosyjska z 9 stycznia 1905 roku” (myślenie 26 tys. → 6.7 tys. znaków) |
| 2025/11.1 (dopasowanie) | 0: „A: 1787 B: 1787 C: 1698” (śmieci bez myślenia) | 1: „A: Stany Zjednoczone Ameryki B: … C: Rzeczpospolita Obojga Narodów” |

Na 2024+2025 IQ3_XXS zyskał 15 zadań z fallbackiem (0 → 1 pkt w 13 z nich). Część zysku to temperatura 0.6 zamiast 1.0 (+2.6 pp); czysty efekt limitu przy tej samej temperaturze: +4.2 pp (niżej).

### Esej T3: dopisywanie akapitów i nagłówek (pary na tych samych esejach)

15 esejów z istniejących przebiegów (Q3_K_M t06 s42/s43, IQ3_XXS, Q3_K_S, IQ2_M; 2024–2026) + `--essay-topic-detect --essay-extend 2` (próg 350): **24 → 22 pkt** łącznie. Wyraźny wzór:

| Esej przed poprawką | par | przed → po |
|---|---|---|
| < 300 wyrazów (spójność = 0) | 5 | **4 → 7** |
| ≥ 300 wyrazów | 4 | 13 → 7 |
| z błędnym nagłówkiem (poprawiony `fixed`) | 3 | 0 → 1, 0 → 1, 0 → 3 |

- Przykład plusa: Q3_K_M 2025 s42 — 266 wyrazów, 2 pkt („nie spełnia wymogu minimum 300 słów”) → dopisane 151 wyrazów, 417, **4 pkt**.
- Przykład minusa: Q3_K_M 2025 s43 — 309 wyrazów, 5 pkt → 465 wyrazów, 1 pkt: dopisane akapity wprowadziły nowe błędy („błędna data bitwy pod Grunwaldem”) i powtórzenia.
- Q3_K_S 2025: esej o Jagielle z nagłówkiem „Temat nr 3” (0 pkt) → nagłówek poprawiony na 1, 279 → 508 wyrazów, 1 pkt.
- Wersja z drugim przejściem z bazą v3 (ER) nie pomogła (Q3_K_S 2024 6 → 3).
- **Wniosek: dopisywanie tylko poniżej 300 wyrazów** (`--essay-min-words 300`) + nagłówek z treści. Tak uruchomione są przebiegi `nt3rbE3`.

## T2 — PLLuM-12B-base + LoRA v1recipe-full + RAG

Warianty harnessu na finałowym serwerze (temp. 0, jeden przebieg na wariant): `pllum-v1r__nt2hyde` (`--rag hyde`), `__nt2k2` / `__nt2k3` (`--kb-rag-k 2/3`), `__nt2ocr` (`--ocr`). Odrzucone przed końcem z braku czasu GPU: `ref`, `clean` (`--rag-clean-query`), `essay` (eseje PLLuM mają już 470+ wyrazów i nagłówek — poprawki nic by nie zmieniły). Bazy v2/v3 testuje osobny worker (`pllum-kbab-*`).

**Szum T2 mimo temp. 0:** `pllum-kbab-v1` (ta sama konfiguracja co finał, osobny worker) ma 55.5% / 50.0% (2026) wobec 52.9% / 41.7% finału — batchowanie w llama.cpp zmienia odpowiedzi, więc różnice T2 < ~3 pp to też szum.

| Przebieg | 2024+2025 | bez eseju | obrazy | esej (2 eseje) |
|---|---|---|---|---|
| finał `pllum-v1recipe-full-polqa` | 52.9% | 52.8% | 41.4% | 53.3% |
| ta sama konfiguracja, inny przebieg (`pllum-kbab-v1`) | 55.5% | 52.8% | 43.1% | 63.3% |
| `--rag hyde` | 51.3% | 53.9% | **46.6%** | 43.3% |
| `--kb-rag-k 2` | 53.8% | 53.9% | 43.1% | 53.3% |
| `--kb-rag-k 3` | 56.3% | 53.9% | 44.8% | 63.3% |
| `--ocr` | 49.6% | 53.9% | 44.8% | 36.7% |

- **Bez eseju wszystkie warianty dają 53.9% vs 52.8% (+1 pkt)** — szum. Całe różnice wyniku łącznego to esej 2025: OCR go nie dotyka (esej bez obrazu), a i tak spadł 8 → 2 pkt przez niedeterminizm batchowania. → **T2 bez zmian.**
- HyDE i OCR pomagają na obrazach (+5.2 / +3.4 pp), ale tracą gdzie indziej.
- Przykład OCR (plus): 2025/12 — OCR: „Kassowy-Billct Xięstwa Warszawskiego…”; przed: „Tak. … Źródło 2. przedstawia banknot Banku Polskiego” (0), po: „Nie. … źródło 2. przedstawia bilet kasowy Księstwa Warszawskiego z 1810 r.” (1).
- Przykład OCR (plus): 2025/21.2 — OCR: „PISMO CENTRALNEGO OKRĘGV PRZEMYSŁOWEGO”; po: „czasopismo związane z Centralnym Okręgiem Przemysłowym … rządy sanacji” (0 → 1).
- Przykład OCR (minus): 2024/9 — OCR łacińskiego napisu to śmieci („CVNX POLO PAPE MERISNI…”), odpowiedź prawie ta sama, 1 → 0 (sędzia).
- HyDE plusy: 2024/2, 2024/4, 2024/5.2, 2024/12.3, 2024/13 (wszystkie z obrazami); minus: esej 2025 8 → 4.

## T1 — Gemma-4-12B QAT

### Tokeny obrazu (`--image-min-tokens`, serwer)

| Przebieg | 2024+2025 | obrazy | bez obrazów | esej | zamknięte |
|---|---|---|---|---|---|
| t1final (s42 / s43, średnia) — **obecny finał** | **71.0%** (72.3 / 69.7) | 76.7% | 82.3% | 48.3% | 80.0% |
| `--image-min-tokens 560 --image-max-tokens 1120`, s42 | 66.4% | 72.4% | 77.4% | 43.3% | 70.0% |
| `--image-min-tokens 1120 --image-max-tokens 1120`, s42 / s43 | **73.5%** (74.8 / 72.3) | 78.4% | 75.8% | 61.7% | 72.5% |

- Przy 1120 tokenach prompt z obrazem rośnie ~2× (2024/25: 571 → 1311 tokenów; 2024/14.1: 879 → 1685). Zysk +2.5 pp (2 seedy) jest **poniżej progu 3 pp**, a +4 z ~+3 pkt to eseje (szum próbkowania eseju); zadania z obrazami +1.7 pp, bez obrazów −6.5 pp (szum). Bilans zadań bez esejów: +5.5 / −6.5 pkt.
- **2024/25** (Jaruzelski zamiata „Solidarność” pod dywan; 0/3 we wszystkich 8 dotychczasowych przebiegach Gemmy): s42 — „satyra na III Rzeszę i ZSRR, marionetka przypominająca Himmlera” (0); **s43 — „opresyjny charakter władzy komunistycznej w Polsce w latach 80. … relacja z ruchem »Solidarność« … marionetka sterowana przez ZSRR” (3/3)**. Więcej tokenów obrazu czasem wystarcza, ale nie stabilnie.
- 2024/14.1 (mapa wojny 1809): nadal „kampania 1812”, 0/1 w obu seedach.
- Stałe zyski: 2024/1 (relief, 0,0 → 1,1), 2024/5.1, 2025/3.1; stałe straty: 2025/5.1 (zamknięte, bez obrazu — szum).
- **Decyzja: bez zmiany finału** (+2.5 pp < 3 pp). 560 tokenów odrzucone (66.4%, s42). Jeśli koordynator chce zaryzykować — to jedyny wariant T1 z dodatnim wynikiem na obu seedach 2024 (78.0 / 74.6 vs 72.9 / 66.1), ale 2025 s43 zwykły.

#### Dogrywka 1120 (04:00–04:30): reguła „średnia wyższa na 2024+2025, nie niższa na 2026, bez awarii”

| Przebieg | 2024 | 2025 | 2024+2025 | 2026 |
|---|---|---|---|---|
| finał s42 | 72.9 | 71.7 | 72.3 | **83.3** |
| finał s43 | 66.1 | 73.3 | 69.7 | – |
| finał s44 (nowy, `gemma4-qat__nt1final-s44`) | 74.6 | 63.3 | 68.9 | – |
| **średnia finału** | | | **70.3** (3 seedy) | **83.3** (1 seed) |
| 1120 s42 | 78.0 | 71.7 | 74.8 | 80.0 |
| 1120 s43 | 74.6 | 70.0 | 72.3 | 80.0 |
| **średnia 1120** | | | **73.5** (2 seedy) | **80.0** |

- Seed 44 dla 1120 przerwany (cięcie zakresu). Awarie: 0 restartów supervisora na obu serwerach (8571 = 1120, 8572 = stock), 0 błędów w przebiegach.
- 2026: bez eseju 1120 ma 39 / 39 z 45 wobec 38 finału (+2.2 pp); cała strata to esej (12 → 9 / 9 z 15), na który tokeny obrazu nie działają. 60 pkt w arkuszu, więc −3.3 pp = 2 pkt.
- Łącznie 3 arkusze bez esejów (134 pkt, średnie po seedach): finał 80.3%, 1120 80.6% (+0.2 pp; bootstrap po zadaniach i seedach 95% CI −6.2…+6.9). Zadania z obrazem +1.1 pp (2024 +5.6, 2025 −5.3, 2026 +1.7), bez obrazu −1.4 pp. Nie spełnia ani kryterium A z raportu 11 (+2 pp na celu, reszta ≥ −1 pp), ani B (≥ +4 pp, ten sam znak na 3 arkuszach). Mniejszy rozrzut 1120 to głównie 2 seedy vs 3 (rozstęp rośnie z liczbą seedów); rozrzut finału pochodzi z zadań bez eseju (2024: 11.4 pp, esej stały 9/9/9).
- **Decyzja: NIE przyjęto** — 2026 niższe (80.0 < 83.3). T1 w `final_configs.json` bez zmian (`--image-min-tokens` domyślne).

### Drugie przejście eseju z bazą wiedzy (`--essay-refine-kb`, pary na tych samych esejach)

Eseje z 6 istniejących przebiegów T1 (t1final, stary prompt, t1kb × 2 seedy; 2024, 2025 + 2026 dla t1final s42) poprawione przez Gemmę z myśleniem; oceniany tylko esej (reszta skopiowana).

| Baza | par | suma przed → po (pkt) | średnio na esej | poprawka przyjęta |
|---|---|---|---|---|
| `kb_all_notes.jsonl` (v1) | 13 | 104 → 114 | **+0.77** | 11/13 |
| `kb_all_notes_v3.jsonl` | 13 | 104 → 113 | **+0.69** | 11/13 |

- Największe zyski: 2024 t1kb s42 5 → 10 (v1 i v3; sędzia przed: „pominięto rolę Dmowskiego… przypisanie Piłsudskiemu wpływu na uznanie Polski”, po: „nie stwierdzam jednoznacznych błędów merytorycznych”), 2025 t1final s43 5 → 9 / 10 (usunięte „osłabianie władzy absolutnej” i „handel zbożem w czasach Jagiełły”), 2024 t1final s43 9 → 12 (v3).
- Straty: 2026 t1final s42 12 → 11 (v1) / 10 (v3), 2024 t1kb s43 7 → 5 (v3), 2025 legacy s42 8 → 6 (v3).
- Gemma dopisuje tylko ~40–60 wyrazów; sędzia wciąż pisze „aspekt społeczno-gospodarczy ogólnikowy” — refine nie usuwa głównej słabości.
- Efekt na wynik: 2 eseje × ~0.7 pkt ≈ **+1.2 pp** na 2024+2025 — poniżej progu 3 pp, a na 2026 gorzej → **nie wchodzi do finału**.

### OCR na 97 obrazach 2024–2026

57/97 obrazów daje tekst po filtrze. Dobre: legendy map (2024/14.1 „polskich / austriackich / rosyjskich … Tylża Królewiec Grodno”, 2025/7.1 „granice państwa zakonnego / nabytki Polski w 1466 r.”), nagłówki gazet (2025/16.1 „ROBOTNIK / ORGAN POLSKIEJ PARTYI SOCYALISTYCZNEJ”, 2026/19.1 „Warszawa, PIĄTEK 14 Maja 1926 r.”), drzewa genealogiczne (2024/11.1). Bez tekstu: rysunki satyryczne — **2024/25 (Jaruzelski i „Solidarność”) nic nie daje**, więc OCR nie naprawi tego zadania.

## Zmiany w konfiguracji i plikach

- `server/final_configs.json` — **T3 tuned**: `UD-IQ3_XXS.gguf` + `--reasoning-budget 5000` + nowy klucz `reasoning_budget_message` („\n\nNa podstawie powyższych rozważań podaję ostateczną odpowiedź.\n”); harness + `--essay-topic-detect --essay-extend 2 --essay-min-words 300`. **T3 base**: ten sam plik IQ3_XXS, goły harness bez zmian. Stare wartości T3 w kluczu `_comment_T3_old` (Q3_K_M 2.29 GB, bez limitu, bez poprawek eseju). T1 i T2 bez zmian.
- `server/exam_run.sh` — przekazuje `reasoning_budget_message` jako jeden argument (spacje i nowe linie); bez klucza zachowanie jak wcześniej. Test na sucho T3 tuned przez `exam_run.sh` (3 zadania) na H100: OK.
- `server/RUNBOOK.md`, `CONTEXT.md` — rozmiar T3 1.95 GB, opis zmian.
- Na obu maszynach: zsynchronizowany harness/server, `tesseract-ocr` + `tesseract-ocr-pol`, pliki `UD-IQ3_XXS.gguf` (1.95 GB) i `Q3_K_S.gguf` (H100 dociągnięty), bazy v2/v3.

## Ryzyka

- **T3 IQ3_XXS: 2 seedy na 2024+2025 (42.9 / 43.7%) i dwa na 2026 (41.7 / 43.3%)**; rozrzut seedów T3 bywał duży (Q3_K_M przy temp. 1.0: 38.7–48.7%). Margines nad 35% ~7–8 pp — realne, ale niezerowe ryzyko spadku poniżej progu na nowym arkuszu. Zapas: Q3_K_S 2.11 GB z tym samym limitem: 42.0% (s42), **48.3% na 2026**.
- Limit myślenia jest opcją serwera llama.cpp (build 2145525 na obu maszynach) — przy innej wersji flaga może nie istnieć.
- Harness T3 zależy teraz od `tantivy` (import `rag_precompute` w wykrywaniu tematu) — jest w obu venvach; test na sucho przeszedł.
- IQ2_M (1.76 GB) z limitem: 34.5% — poniżej progu; nie ryzykować bez lepszego wyniku (z `--presence-penalty 1.0` też 34.5%).
- Retriever notatek (`rag_precompute.terms`) pomija linie ze słowami Warszawa/Kraków/Wrocław/Poznań i porównuje 6-znakowe rdzenie (odmienione nazwy własne się nie łączą) — nie naprawiane (nie trywialne bez zmiany wyników T2).

## Drugi seed 2026 dla T3 (dogrywka)

- `q35-4b-iq3xxs__nt3rbE3-s42` (L40S) dał 28.3%, ale **nieważny**: skrypt zatrzymał serwer 8551 po swoich przebiegach s43, gdy ten przebieg jeszcze trwał → 8 × `APIConnectionError` (20, 21, 22, 23.1, 23.2, 24, 25, 26 z esejem), puste odpowiedzi. Błąd infrastruktury, nie modelu.
- Naprawa: te 8 zadań powtórzone na H100 tą samą konfiguracją (IQ3_XXS, limit 5000 + komunikat, poprawki eseju, s42) i scalone (`--only-ids … --merge-from`) → `q35-4b-iq3xxs__nt3rbE3fix-s42`: **43.3%**, 0 błędów.
- **T3 finał na 2026: 41.7% (s43) / 43.3% (s42), średnio 42.5%.**

Skrypt oceny: `server/nt_judge.sh <budżet> [filtr]` (ściąga `__nt*` z obu maszyn, `to_results`, `grade`, `judge_reuse`, sędzia). Analiza: `/tmp/ana/score.py`, `/tmp/ana/cmp.py`, `/tmp/ana/essay_pairs.py`.
