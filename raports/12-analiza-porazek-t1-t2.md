# 12 — Analiza porażek T1 i T2 na konkretnych zadaniach + tanie poprawki harnessu (nd 27.09, 04:30–05:40)

Sędzia `gpt-6-luna`, zadanie 2024/21 poza mianownikiem (filtr treści sędziego). Dane: finał T1 (`gemma4-qat-t1final__s42/__s43`, `gemma4-qat__nt1final-s44` na 2024+2025; s42 na 2026) i finał T2 (`pllum-v1recipe-full-polqa` + `pllum-kbab-v1`, ta sama konfiguracja, dwa przebiegi). Zrzuty porażek: `/tmp/ana/fail_T1.txt`, `/tmp/ana/fail_T2.txt` (`/tmp/ana/fail_dump.py T1|T2`), taksonomia: `/tmp/ana/taxo.py`. Nowe przebiegi: prefiks `fx-` (`server/fx_run.sh`, ocena `server/fx_judge.sh`).

## Podsumowanie

| | T1 (Gemma-4-12B QAT) | T2 (PLLuM-12B + LoRA + RAG) |
|---|---|---|
| Oczekiwana strata 2024+2025 (119 pkt) | ~35 pkt | ~55 pkt |
| **1. kategoria** | esej (h): 16 pkt (13.4 pp) | źle odczytany obraz (d): 25 pkt (21 pp) |
| **2.** | źle odczytany obraz (d): 10.3 pkt (8.7 pp) | esej (h): 12.5 pkt (10.5 pp) |
| **3.** | brak/zła wiedza (e): 5.7 pkt (4.8 pp) | wiedza (e): 6.5 pkt (5.5 pp) |
| 4. | harness/normalizacja (f): 2.0 pkt (1.7 pp) | **niepełna odpowiedź (b): 5 pkt (4.2 pp); na 2026: 6 pkt (10 pp)** |
| 2026 (60 pkt, 1–2 przebiegi) | c 3, d 3, h 3, e 1 | d 12, h 9.5, b 6, e 3 |
| Naprawialne harnessem/promptem | ~2–4 pkt (f, część c/d w „rozstrzygnij”) | ~4–6 pkt (b, f) |
| **Test** | `--rozstrz-hint` (3 seedy, tylko „rozstrzygnij”): 70.3 → 70.9% na 2024+2025 (+0.8 pp), 83.3 → 84.4% na 2026 | **`--fill-fields`: +2 pkt na zadaniach docelowych (+1.7 pp na 2024+2025), 0 strat** |
| **Decyzja** | **nie przyjęte** (< +2 pp, 2025 na minus); bez zmian w konfiguracji | **PRZYJĘTE do `final_configs.json` (T2 tuned)**, test na sucho przez `exam_run.sh` na H100: OK |

Najważniejsze:
1. **T1 prawie nie ma strat „formalnych”.** Gemma odpowiada na wszystkie części polecenia (0 odpowiedzi z niewypełnionym wzorem na 3 arkuszach). Traci na treści: rozpoznaniu, co przedstawia mapa/rysunek, i na błędnych szczegółach w uzasadnieniu „rozstrzygnij” przy poprawnym rozstrzygnięciu. To naprawia lepsze widzenie/wiedza, nie harness.
2. **T2 ma wyraźną klasę strat formalnych**: odpowiada jednym zdaniem, gubiąc drugi element wzoru („Wydarzenie 2.:”, „Uzasadnienie:”, „Zasadźca:”) — 8 zadań na 3 arkuszach. Ponowienie z tym samym promptem i dopiskiem nic nie daje (PLLuM powtarza tę samą krótką odpowiedź), **dopiero wymuszenie formatu przez prefill odpowiedzi etykietą pierwszego pola** działa.
3. **Szum T2 na tej samej maszynie (temp. 0) jest duży**: dwa przebiegi funkcjonalnie identyczne (`fx-t2base` i `fx-t2ff`, w którym powtórka nigdy nie została przyjęta) dały 48.7 vs 52.9% (2024+2025) i 51.7 vs 43.3% (2026); 12–17 odpowiedzi na arkusz różni się. Dlatego poprawkę T2 oceniałem tylko na zadaniach docelowych (reszta scalona z tego samego przebiegu bazowego).

## 1. Taksonomia porażek

Kategorie: (a) niezgodność z poleceniem, (b) odpowiedź niepełna (1 z 2 elementów, brak uzasadnienia), (c) źle odczytany tekst źródła, (d) źle odczytany obraz, (e) brak/zła wiedza, (f) harness (normalizacja zamkniętych, fallback, format), (g) sędzia/klucz, (h) esej. Strata = max − średnia punktów z przebiegów; przypisanie do jednej dominującej kategorii na zadanie (ręcznie, na podstawie odpowiedzi i komentarza sędziego).

### T1 — strata oczekiwana (2024+2025: 3 seedy; 2026: 1 seed)

| Kategoria | 2024+2025 pkt | pp (/119) | 2026 pkt (/60) | Naprawialne? |
|---|---|---|---|---|
| h esej | 16.0 | 13.4 | 3.0 | częściowo (refine KB +0.7/esej, raport 10; poniżej progu) |
| d obraz | 10.3 | 8.7 | 3.0 | trudno: 2024/25 i 2025/14.1 błędne w każdym seedzie; OCR nie pomaga przy rysunkach |
| e wiedza | 5.7 | 4.8 | 1.0 | nie harnessem (RAG/KB w T1 szkodził, raport 10) |
| f harness | 2.0 | 1.7 | 0 | **tak** (normalizacja dopasowań, fallback) |
| c tekst | 0.7 | 0.6 | 3.0 | może prompt (identyfikacja po szczegółach) |
| a, g | 0.7 | 0.6 | 0 | — |

Wg typu zadania (2024+2025): esej 16.0, rozstrzygnij 6.0 (+6.0 na 2026!), podaj 4.7, wyjaśnij 3.7, zamknięte 5.0.

**Wzór „rozstrzygnij”**: w T1 na 2026 wszystkie 6 straconych „rozstrzygnij” miało **poprawne rozstrzygnięcie** w 5 przypadkach, a punkt odebrał błędny szczegół w uzasadnieniu (zła identyfikacja jednego źródła). Na 2024+2025 to samo w 2024/14.1 (3/3 seedy), 2024/23.2, 2025/7.1, 2025/22 (s43), 2024/7 (s44).

**Fallback myślenia** (myślenie urwane na limicie → odpowiedź bez myślenia): 9 zadań na 6 arkuszo-przebiegów (1.5/arkusz), wynik 36% vs 71% bez fallbacku → ~0.6 pkt/arkusz (~1 pp). Limit myślenia serwera pomógł T3 (IQ3), ale zaszkodził Q3_K_M (raport 10) — nie testowane dla Gemmy.

### T2 — strata oczekiwana (2 przebiegi tej samej konfiguracji)

| Kategoria | 2024+2025 pkt | pp (/119) | 2026 pkt (/60) | Naprawialne? |
|---|---|---|---|---|
| d obraz | 25.0 | 21.0 | 12.0 | nie w T2 (PLLuM bez wizji, limit 8.8 GB; OCR/HyDE tylko +3–5 pp na obrazach, traci gdzie indziej) |
| h esej | 12.5 | 10.5 | 9.5 | szum (esej 2026: 3 vs 8 pkt w dwóch przebiegach tej samej konfiguracji) |
| e wiedza | 6.5 | 5.5 | 3.0 | — |
| **b niepełna** | 5.0 | 4.2 | **6.0** | **tak — `--fill-fields`** (część) |
| c tekst | 3.5 | 2.9 | 1.0 | — |
| f format | 2.0 | 1.7 | 1.0 | tak (numery zamiast nazw w dopasowaniach; „P” zamiast dwóch ocen) — nie zrobione |

Wg typu (2024+2025): rozstrzygnij 19.0 (+9 na 2026), esej 12.5, podaj 8.0, wyjaśnij 6.5, zamknięte 7.0.

## 2. Przykłady

| Zadanie | Track | Kat. | Odpowiedź | Klucz / komentarz sędziego |
|---|---|---|---|---|
| 2024/14.1 (rozkaz Napoleona a mapa 1809) | T1, 0/3 seedy | d | „Nie … mapa: wojna polsko-bolszewicka” / „powstanie listopadowe” | rozstrzygnięcie dobre, mapa to 1809 (Raszyn) → 0 |
| 2024/25 (Jaruzelski zamiata „Solidarność”) | T1, 0/3 | d | „faszyzm, Mussolini” / „III Rzesza” / „wpływy religijne” | 0/3 w każdym seedzie; OCR nic nie daje |
| 2026/17 (dwa zabory) | T1 | c | „Nie … źródło 1. to zabór rosyjski” | „instytucje c.k. → zabór austriacki” → 0 mimo dobrego rozstrzygnięcia |
| 2025/4 (nazwy zakonów) | T1 s44 | f | „Zakon Franciszkanów / Zakon Benedyktynów / Zakon Jezuitów” | auto-ocena: 0/2 (klucz „franciszkanie…”); s43: literówka „Franciszanie” → 1/2 |
| 2025/11.1 | T1 s44 | f | „A: USA” | auto-ocena: WRONG (klucz „Stany Zjednoczone”) |
| 2025/19 (dwa wydarzenia) | T2 | b | „Zabójstwo prezydenta Gabriela Narutowicza w grudniu 1922 r.” (jedno) | 1/2 „podano jedno poprawne wydarzenie” |
| 2024/13 (wydarzenie + uzasadnienie) | T2 | b | „Rycina przedstawia ścięcie Karola I … w 1649 r.” | 0 „brak wymaganego uzasadnienia” |
| 2026/5.1 (wystawca i zasadźca) | T2 | b | „Komes Jan.” | 0 „nie podano imienia zasadźcy” |
| 2024/11.1, 2025/5.1 (dopasowania władców) | T2 | f | „A: 1 B: 2” | numery zamiast imion władców → 0 |
| 2026/26 (esej) | T2 | h | ta sama konfiguracja: 3 vs 8 pkt | szum batchowania przy temp. 0 |

## 3. Poprawki — ranking

| # | Poprawka | Track | Zakres (pkt w grze) | Oczekiwany zysk | Status |
|---|---|---|---|---|---|
| 1 | **`--fill-fields`**: brakuje pól wzoru → powtórka z wzorem i prefillem etykiety pierwszego pola; przyjęta tylko, gdy wszystkie pola wypełnione | T2 | 8 zadań, ~7 pkt / 3 arkusze | +1–2 pkt/arkusz | **przetestowane, przyjęte** |
| 2 | `--rozstrz-hint`: wskazówka „ustal źródła po szczegółach, nie dopisuj niepewnych identyfikacji” | T1 | rozstrzygnij: 6 pkt/2 arkusze + 6 pkt na 2026 | zmierzone: +0.5–1 pkt/arkusz (w szumie) | przetestowane, nie przyjęte (opcja dla koordynatora) |
| 3 | Normalizacja zamkniętych dopasowań: „Zakon Franciszkanów” → „franciszkanie”, „USA” → „Stany Zjednoczone”, literówki (odległość edycji ≤ 1) | T1/T2 | ~2 pkt/3 seedy T1 | ~0.5 pkt/arkusz — **tylko jeśli organizatorzy oceniają zamknięte dopasowaniem napisów** | nie zrobione |
| 4 | Dopasowania z numerami (T2): odpowiedź „A: 1” przy wzorze „A: nazwa” → podstawić nazwę z numerowanej listy źródła albo powtórka z prefillem | T2 | 2 pkt / 2 arkusze | ~0.5–1 pkt/arkusz | nie zrobione |
| 5 | `--reasoning-budget` dla Gemmy (zamiast fallbacku bez myślenia) | T1 | ~1.5 zadania/arkusz, 36% vs 71% | ~0.5 pkt/arkusz; ryzyko ucięcia dobrego myślenia (jak Q3_K_M) | nie zrobione |
| 6 | „Rozstrzygnij” T1: drugie przejście weryfikujące uzasadnienie (czy każda identyfikacja źródła zgadza się ze szczegółami) | T1 | jak #2 | niepewny; 2× czas | nie zrobione |
| 7 | T2 zamknięte P/F: odpowiedź „P” przy dwóch stwierdzeniach (2026/2) → powtórka z prefillem „1:” | T2 | 1 pkt | mały | nie zrobione |
| 8 | Esej T2: wybór tematu / głosowanie z kilku esejów (szum 3–8 pkt) | T2 | ~10 pkt | duży, ale wymaga oceny bez sędziego | nie zrobione |

## 4. Wyniki testów

### T2 `--fill-fields` (H100, `fx-t2base` = finał T2 na tej samej maszynie)

Wykrycie wzoru: końcowe linie polecenia kończące się „:” albo „•”; pole liczone jako wypełnione, gdy po etykiecie jest treść. W finałowych odpowiedziach T2 wyzwala się na 8 zadaniach, w T1 na **0** (Gemma zawsze wypełnia wzór — flaga nie dotyczy T1).

| Wariant powtórki | przyjęte | pkt na 8 zadaniach docelowych |
|---|---|---|
| baza (`fx-t2base`, oba stare przebiegi finału) | — | 4 |
| wieloturowa „Twoja odpowiedź jest niepełna…” (`fx-t2ff`) | 0/7 (PLLuM powtarza to samo) | 4 |
| jednoturowa z wzorem w poleceniu (`fx-t2ff2`) | 2/7, obie nadal błędne | 4 |
| **jednoturowa + prefill etykiety pierwszego pola** (`fx-t2ff3/ff4`) | 5–6/7 | **6** |

- **2025/19**: 1 → **2**: „Wydarzenie 1.: … Narutowicz … zginął w zamachu 16 grudnia 1922 r. / Wydarzenie 2.: 12 maja 1926 r. Józef Piłsudski przejął władzę w wyniku przewrotu majowego” (= klucz).
- **2024/13**: 0 → **1**: „Wydarzenie: ścięcie Karola I. / Uzasadnienie: Rycina przedstawia egzekucję monarchy.”
- 2025/20 (1 → 1, „• nazistowski • komunistyczny”), 2025/23 (0 → 0, „barok” zamiast socrealizmu), 2026/5.1 (prefill zostawił puste „Wystawca:” — po zaostrzeniu warunku „wszystkie pola wypełnione” powtórka odrzucona; 0 pkt w obu wersjach), 2026/13, 2026/20 bez zmian.
- **Bilans: +2 pkt / 0 strat** na 2024+2025 (+1.7 pp), 0 na 2026. Pozostałe zadania identyczne z konstrukcji (`--only-ids` + `--merge-from fx-t2base`).
- Reguła z raportu 11, typ A: jasny mechanizm, zmiana może dotknąć tylko zadań z niewypełnionym wzorem, zysk dokładnie tam → **przyjęte**. T2 = zysk nad gołym modelem, `--bare` bez zmian, więc poprawka zwiększa tylko wynik strojonego wariantu.
- Koszt czasu: 1 dodatkowe krótkie wywołanie na ~2–3 zadania/arkusz (~2 s).

### T1 `--rozstrz-hint` (H100, tylko 14 „rozstrzygnij” na arkusz, reszta scalona z t1final; 2 seedy)

Baza: t1final s42/s43/s44 (2024, 2025), s42 + nowy `fx-t1base-s43` (2026). Hint: `fx-t1rh-s42/s43/s44` (3 seedy; trzeci dorzucony, bo po 2 seedach wynik był niejednoznaczny). Punkty na 14 „rozstrzygnij” (14–15 pkt na arkusz):

| Arkusz | baza (seedy) | średnia | hint (seedy) | średnia | Δ pkt | Δ pp arkusza |
|---|---|---|---|---|---|---|
| 2024 | 11 / 8 / 11 | 10.0 | 11 / 11 / 12 | 11.33 | **+1.33** | +2.2 |
| 2025 | 11 / 12 / 13 | 12.0 | 11 / 12 / 12 | 11.67 | −0.33 | −0.6 |
| 2026 | 9 / 10 | 9.5 | 12 / 10 / 10 | 10.67 | **+1.17** | +1.9 |
| **2024+2025** | | 22.0 | | 23.0 | +1.0 | **+0.8 pp** |

Całość (reszta scalona z tych samych seedów bazy): 2024+2025 **70.3 → 70.9%** (73.1 / 70.6 / 68.9 vs 72.3 / 69.7 / 68.9), 2026 83.3 → 84.4%.

- Zyski dokładnie tam, gdzie celował mechanizm (identyfikacja źródła po szczegółach): **2026/19.1** 0/2 → 3/3 („Źródło 1. … data 14 maja 1926 r., »Belweder zdobyty!« … Źródło 2. opisuje wcześniejszy kryzys” — wcześniej źródło 2. datowane na maj 1926), **2026/17** 0/2 → 2/3 („zabór austriacki, na co wskazuje skrót »c.k.«” — wcześniej „zabór rosyjski”), **2024/1** 1/3 → 3/3 (relief B), **2024/5.1** 1/3 → 3/3 (mapa wypraw Wikingów, nie krucjat), 2025/7.1 2/3 → 3/3.
- Straty: 2025/5.2 i 2025/15.2 (3/3 → 2/3), 2026/14.2, 2026/4.1, 2024/15.2, 2025/22 (szum pojedynczych seedów).
- Bez wpływu na trudne obrazy: 2024/14.1 (mapa 1809) i 2025/14.1 (herb) nadal 0 we wszystkich seedach.
- **Decyzja: NIE przyjęte** (reguła A z raportu 11: wymaga ≥ +2 pp przy 2 seedach; jest +0.8 pp na 2024+2025, +1.9 pp na 2026, znak ujemny na 2025). Kandydat do przyjęcia, gdyby koordynator chciał zaryzykować: zmienia tylko prompt „rozstrzygnij”, nie wydłuża czasu, 2 z 3 arkuszy na plus, zyski mechanistycznie spójne — ale różnica mieści się w szumie.

## Zmiany w plikach

- `harness/run_exam.py`: flagi `--fill-fields` (funkcje `answer_template`, `template_filled`, stała `FIELDS_RETRY`; zapis w `debug.jsonl` jako `fields`) i `--rozstrz-hint` (stała `ROZSTRZ_HINT`). Domyślne zachowanie i `--bare` bez zmian; `--essay-mode structured` drugiego workera nietknięty.
- `server/final_configs.json`: **T2 tuned harness + `--fill-fields`**; stara wartość w `_comment_T2_old`. T1 bez zmian.
- `server/fx_run.sh`, `server/fx_judge.sh`, `exams/fx_dry/` (6 zadań 2025 do testu na sucho).
- Test na sucho: `bash server/exam_run.sh exams/fx_dry T2 tuned 8803` na H100 — `answers.json OK: test2025_v2 6 odpowiedzi`, powtórka zadziałała na 19, 20, 23, serwer zatrzymany.

## Koszt

Sędzia `gpt-6-luna`: 184 oceny (reszta ~700 skopiowana przez `judge_reuse`) — **≈ 0.44 $ wg cennika `judge_openai.py`** (T2: 0.14 $, T1: 0.31 $), realnie ok. 40% tego. Limit 1.00 $. GPU: H100 ~30 min (własne porty 8801–8803, zatrzymane); L40S nieużywany.

## Uwagi dla egzaminu

- T2 tuned ma teraz `--fill-fields`: przy zadaniach ze wzorem „Etykieta:” i niepełnej odpowiedzi harness robi jedno dodatkowe krótkie wywołanie z prefillem odpowiedzi. Prefill asystenta działa w llama-server z buildu na H100 (sprawdzone testem na sucho); przy innej wersji serwera w najgorszym razie powtórka zostanie odrzucona i zostaje pierwsza odpowiedź.
- Szum T2 (temp. 0) między przebiegami na tej samej maszynie: ±4–8 pp na arkusz — nie porównywać wariantów T2 pełnymi przebiegami bez scalania niezmienionych zadań.
