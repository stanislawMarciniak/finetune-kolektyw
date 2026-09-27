# 10c — Własne Q2 dla T3 i ustrukturyzowany esej

Stan: nd 27.09.2026, 05:15 CEST. Cel: plik mniejszy niż IQ3_XXS-PL-E4K (1.87 GB) z wynikiem ≥ 35%, oraz lepszy esej dla małych kwantyzacji.

## Wynik w skrócie

- Zbudowane trzy warianty Q2 z naszym imatrixem PL (przepis UD-IQ2_M unsloth 1:1): IQ2_M-PL 1 759 997 024 B, IQ2_M-PL-E4K 1 680 534 624 B, **IQ2_M-PL-E4K-MIX 1 745 906 784 B** (E4K + ffn_down i attn_qkv w IQ3_XXS).
- **IQ2_M-PL-E4K-MIX przechodzi próg: 42.4% (2024) / 40.0% (2025) → średnio 41.2%, 2026: 45.0%** (seed 42, esej structured). To o 124 MB mniej niż IQ3_XXS-PL-E4K (1.87 GB) i o 203 MB mniej niż obecny finał UD-IQ3_XXS (1.95 GB). Czysty IQ2_M-PL-E4K odpada (34.5% / 36.7%) — tak jak stock UD-IQ2_M (34.5% / 33.6%).
- Zysk MIX to **mniej pętli myślenia** (powtórki bez myślenia 2/0/3 na arkusz zamiast 8/10/7 dla E4K) i lepsze zamknięte/otwarte, **nie esej** (esej MIX: 1/1/0 pkt).
- `--essay-mode structured` (nowy tryb harnessu, domyślnie wyłączony): eseje 336–510 wyrazów z nagłówkiem, bez pętli (IQ2 na starej ścieżce pisał 1245–1705 wyrazów). Zysk tylko **+0.5 pkt na esej** (IQ3_XXS 1.17 → 1.67 / 15, n = 6 → 9; IQ2 0.5 → 1.0, n = 6); UD-IQ3_XXS na tych samych odpowiedziach poza esejem: 42.9 → 44.5% (2024+2025), 2026 bez zmian (41.7%). Sufit to wiedza modelu: 5–10 błędów merytorycznych w prawie każdym eseju.
- Ryzyko MIX: jeden seed, najsłabszy arkusz 40.0% (5 pp nad progiem). Drugi seed (2024+2025, s43, `overnight/modal_q2mix43.py`) został przerwany bez wyników: Modal zwrócił `ConflictError: workspace … is disabled` (workspace Modal wyłączony, prawdopodobnie limit środków) — Modal jest niedostępny; powtórzyć na H100 (MIX jest w `~/models/custom/qwen35-4b/`, ~30 min na arkusz).

## 1. Własne kwantyzacje Q2 (imatrix PL)

Przepis: typy tensorów odczytane gguf-py ze stockowego `Qwen3.5-4B-UD-IQ2_M.gguf` (`work/tt_UD-IQ2_M.txt`, 248 reguł: FFN i attn_qkv głównie IQ2_S, ffn_down w 9 warstwach IQ3_S, attn_v/output IQ3_S, ssm_out Q5_K, ssm_alpha/beta Q8_0, token_embd Q5_K) + nasz `imatrix-pl.gguf` (ten sam co w raporcie 10b). Budowa `work/q2_build.sh` na CPU L40S (~3 min na plik). IQ2_M-PL ma rozmiar stocku co do 64 B (metadane) — przepis odtworzony 1:1.

| Plik | Bajty | PPL tekst PL | PPL ślady rozumowania |
|---|---|---|---|
| stock UD-IQ2_M | 1 759 997 088 | 6.899 ± 0.269 | 1.9410 ± 0.039 |
| `Qwen3.5-4B-IQ2_M-PL.gguf` | 1 759 997 024 | 6.647 (−3.7%) | 1.9302 (−0.6%) |
| **`Qwen3.5-4B-IQ2_M-PL-E4K.gguf`** (token_embd Q4_K) | **1 680 534 624** | 6.690 (−3.0%) | 1.9443 (+0.2%) |
| `Qwen3.5-4B-IQ2_M-PL-E4K-MIX.gguf` (E4K + ffn_down i attn_qkv IQ2_S → IQ3_XXS, 47 tensorów) | 1 745 906 784 | **6.198 (−10.2%)** | **1.8465 (−4.9%)** |
| (stock UD-IQ3_XXS, dla skali) | 1 949 047 968 | 5.736 | 1.8015 |

PPL: CPU, 4 × 2048 tokenów, zbiory odłożone z raportu 10b (`work/ppl_q2.sh`). Imatrix PL daje przy 2 bitach nieco więcej niż przy IQ3_XXS (−3.7% vs −2.4% na tekście PL), ale na śladach rozumowania nic. MIX zamyka ~45% luki PPL między UD-IQ2_M a UD-IQ3_XXS kosztem +65 MB względem E4K (nadal < stock UD-IQ2_M).

Pliki: `~/models/custom/qwen35-4b/` na L40S i H100 (sumy `q2.sha256`, README uzupełnione); na wolumenie Modal `matura-models` pod `custom/qwen35-4b/` (E4K, MIX).

## 2. `--essay-mode structured` (harness)

Nowe flagi w `harness/run_exam.py` (domyślnie wyłączone; bez nich i z `--bare` zachowanie bez zmian):

| Flaga | Działanie |
|---|---|
| `--essay-mode structured` | esej krok po kroku zamiast jednego wywołania + poprawek |
| `--essay-kb PATH` | notatki dla trybu structured (domyślnie `--kb-essay`, czyli v1 `data/kb/kompendium.jsonl`) |
| `--essay-pick model\|kb\|mix` | wybór tematu: samoocena modelu (`CHOOSE_PROMPT`, domyślnie), pokrycie bazy wiedzy (suma BM25 3 najlepszych notatek zgodnych z nazwami własnymi tezy) albo oba |
| `--essay-plan-think` | plan z myśleniem (nie testowane — limit czasu) |

Przebieg (bez myślenia, każde wywołanie krótkie z twardym limitem tokenów — małe kwantyzacje nie mają jak się zapętlić):
1. wybór tematu; aspekty z polecenia (także „aspekt X, Y i Z”; przy „trzech wybranych władców/państw/wydarzeń” elementy wskazuje plan);
2. plan: `TEZA:` + 2 argumenty na aspekt, z 3 notatkami kompendium dla tezy; **stanowisko zawsze „zgadzam się”** — w wersji 1 model w planie pisał „klęska nie była nieunikniona”, a w akapitach „była nieunikniona” (sędzia: „sprzeczność stanowiska”);
3. akapit na aspekt (130–160 wyrazów w poleceniu, w praktyce 90–130; ≤ 190 po przycięciu do pełnego zdania), 2 notatki na aspekt wybierane tylko z puli pasującej do tezy i planu (notatka spoza tematu szkodziła w A/B T2), zaczyna od „Po pierwsze, / Po drugie, / Po trzecie,”; usuwane powtórzone zdania;
4. wstęp (50–70 wyrazów, stanowisko) i zakończenie („Podsumowując,”, 40–60);
5. złożenie z nagłówkiem „Temat nr N”; gdy < 420 wyrazów — jeden dodatkowy akapit; twardy limit 650 wyrazów. W wersji 1 były dwa dodatkowe akapity — to w nich pojawiały się zmyślenia („1870 legionistów w 10. DP”), więc v2 dopuszcza jeden.

Wynik: 336–474 wyrazów, zawsze z nagłówkiem, bez pętli. ~7 krótkich wywołań, ~4 min na esej przy 8 slotach.

## 3. Porównanie ścieżek eseju (sędzia luna, CKE)

Eseje 2024/2025/2026 (paczka `essays3_v2` — trzy tematy do wyboru, jak na arkuszu), seedy 42 i 43; dla IQ3_XXS także esej z pełnych arkuszy.

| Model | Ścieżka | n | średnio pkt / 15 | wyrazy | Przebiegi |
|---|---|---|---|---|---|
| UD-IQ3_XXS | obecna (topic-detect + extend 2, min 300) | 6 | 1.17 | 341–633 | `q35-4b-essay-iq3xxs-base-s42/43` |
| UD-IQ3_XXS | structured v1 (2 dodatkowe akapity, stanowisko modelu) | 6 | 1.00 | 402–456 | `q35-4b-essay-iq3xxs-STRUCT-s42/43` |
| UD-IQ3_XXS | **structured v2** | 9 | **1.67** | 336–456 | `q35-4b-essay-iq3xxs-struct2-s42/43` (essays3 + arkusze) |
| IQ2_M-PL-E4K | obecna | 6 | 0.50 | 328–**1705** (3 z 6 > 1200, pętle) | `q35-4b-essay-iq2mpl-e4k-base-s42/43` |
| IQ2_M-PL-E4K | **structured v2** | 6 | **1.00** | 394–474 | `q35-4b-essay-iq2mpl-e4k-struct2-s42/43` |

Wnioski:
- Structured v2 usuwa problem długości (IQ2: 1245–1705 → ~400–470 wyrazów) i stale daje nagłówek; spójność rośnie z 0 do 1. Zysk punktowy jest mały: +0.5 pkt na esej (IQ3_XXS 1.17 → 1.67, IQ2 0.5 → 1.0), w granicach szumu przy n = 6–9.
- Sufit wyznacza wiedza modelu 4B, nie forma: w prawie każdym eseju sędzia liczy 5–10 błędów merytorycznych (maksymalne −3), a aspekty są „powierzchowne”. Notatki kompendium (218 notatek, po jednej na zagadnienie) są za rzadkie, żeby pokryć trzy aspekty konkretnymi faktami; model dopowiada resztę z pamięci — z błędami.
- Oczekiwane +5 pkt za esej jest nierealne dla Qwen3.5-4B w 2–3 bitach; realne +0.5–1 pkt ≈ +1–1.5 pp na arkusz.

### Przykłady przed/po (UD-IQ3_XXS, te same odpowiedzi poza esejem)

| | Przed: `q35-4b-iq3xxs__nt3rb-s42` | Po: `q35-4b-essay-iq3xxs-struct2-s42` |
|---|---|---|
| 2024, wyrazy / nagłówek | 250 / „Temat 3: …” (Piłsudski) | 405 / „Temat nr 1” (Karol Wielki) |
| 2024, punkty | **0** (A 0, 8 błędów, spójność 0 — < 300 słów) | **2** (A 1, 4 błędy, spójność 1) |
| 2024, sędzia | „Wątek dyplomatyczny i ustrojowy podjęto powierzchownie, a argumentacja militarna jest niefunkcjonalna; … Podana liczba słów wynosi 250, więc praca nie spełnia minimum 300 słów i otrzymuje 0 pkt za spójność.” | „W każdym z trzech aspektów argumentacja jest powierzchowna … błędne twierdzenia o niepodzielności państwa po śmierci Karola … powtarzanie tych samych zdań istotnie zaburza spójność.” |
| 2025, wyrazy / nagłówek | 293 / „Temat nr 1” (Jagiełło; zaczyna „Oto wypowiedź na temat…”, „Tytuł: …”) | 381 / „Temat nr 3” (rok 1956) |
| 2025, punkty | **2** (A 2, 1 błąd, spójność 0 — 293 słowa) | **2** (A 1, 6 błędów, spójność 1) |
| 2025, sędzia | „… błędnie wskazano synów Jagiełły jako Stefana II i Kazimierza. Praca liczy 293 słowa, czyli mniej niż wymagane 300, dlatego w kryterium spójności przyznano 0 pkt.” | „Argument dotyczący Polski jest rzeczowy, ale wywód o Węgrzech pozostaje powierzchowny, a wskazane Włochy nie były państwem bloku komunistycznego …” |
| 2026 (s43), punkty | 1 (`q35-4b-iq3xxs__nt3rbE3-s43`, 423 wyr.) | 1 (451 wyr., „Temat nr 3”, 4 błędy) |

Początek eseju po (2024): „Temat nr 1 / W epoce średniowiecza, w czasach powolnego zaniku rzymskiego imperium i powstawania nowych królestów, Karol Wielki w latach 768–814 odniósł niezwykły sukces. … / Po pierwsze, państwo Karola Wielkiego stanowiło szczyt koordynacji władzy …”.

## 4. Pełne arkusze

Serwer jak finał T3 (`-c 98304 -np 8 -ub 4096`, mmproj-F16, `--reasoning-budget 5000` + komunikat), harness T3 (`--think rozstrz,open,podaj,closed --temperature 0.6 --top-k 20 --max-tokens 8000 --kb-essay data/kb/kompendium.jsonl`) + `--essay-mode structured`, seed 42. Q2 na Modal (H100, llama.cpp `server-cuda`, trzy serwery — po jednym na arkusz). IQ3_XXS: esej structured podmieniony w istniejących przebiegach (`--only-ids` + `--merge-from`, reszta odpowiedzi identyczna, oceny skopiowane `judge_reuse`).

| Model (plik, bajty) | Esej | 2024 | 2025 | średnia | 2026 | powtórki bez myślenia (24/25/26) | esej pkt (24/25/26) | Przebieg |
|---|---|---|---|---|---|---|---|---|
| **IQ2_M-PL-E4K-MIX** (1 745 906 784) | structured | 42.4% | 40.0% | **41.2%** | **45.0%** | 2 / 0 / 3 | 1 / 1 / 0 | `q35-4b-q2-iq2mpl-e4k-mix__struct2-s42` |
| IQ2_M-PL-E4K (1 680 534 624) | structured | 33.9% | 35.0% | 34.5% | 36.7% | 8 / 10 / 7 | 1 / 0 / 0 | `q35-4b-q2-iq2mpl-e4k__struct2-s42` |
| stock UD-IQ2_M (1 759 997 088), dla porównania | obecna | 39.0% | 30.0% | 34.5% | — | 22 łącznie | 1 / 0 | `q35-4b-iq2m__nt3rb-s42` (raport 10) |
| stock UD-IQ2_M, seed 7 | obecna | — | — | 33.6% | — | 16 łącznie | 0 / 0 | `q35-4b-udiq2m__bf5k-modal-s7` |
| UD-IQ3_XXS (1 949 047 968) | **structured** (podmiana eseju) | 42.4% | 46.7% | **44.5%** | 41.7% (s43) | 4 łącznie | 2 / 2 / 1 | `q35-4b-essay-iq3xxs-struct2-s42` (24, 25), `-s43` (26) |
| UD-IQ3_XXS, te same odpowiedzi | obecna | 39.0% | 46.7% | 42.9% | 41.7% (s43) | 4 łącznie | 0 / 2 / 1 | `q35-4b-iq3xxs__nt3rb-s42`, `q35-4b-iq3xxs__nt3rbE3-s43` |

MIX vs E4K przy tym samym imatrixie i tej samej ścieżce eseju: +6.7 pp (2024+2025) i +8.3 pp (2026) za 65 MB — dwa najbardziej wrażliwe typy tensorów (ffn_down, attn_qkv warstw DeltaNet) w IQ3_XXS zamiast IQ2_S. Rozbicie MIX: zamknięte 50.0%, otwarte 53.6%, obrazy 55.2%, Polska 37.3%, świat 83.3%.

## 5. Rekomendacja i ryzyko

- **Kandydat T3 (ryzykowny): `models/custom/qwen35-4b/Qwen3.5-4B-IQ2_M-PL-E4K-MIX.gguf` — 1 745 906 784 B** (sha256 1d4eaec7…; na H100 i L40S) + `models/unsloth/Qwen3.5-4B-GGUF/mmproj-F16.gguf`.
  - serwer: jak finał T3 (`-ub 4096 -b 4096 -c 98304 -np 8 --reasoning-format deepseek --reasoning-budget 5000` + `reasoning_budget_message`), tylko inna ścieżka `-m`;
  - harness: `--parallel 8 --rag none --vision --think rozstrz,open,podaj,closed --temperature 0.6 --top-p 0.95 --top-k 20 --max-tokens 8000 --kb-essay data/kb/kompendium.jsonl --essay-mode structured` (w trybie structured flagi `--essay-topic-detect/--essay-extend` nie działają).
- Ryzyko: **średnio-wysokie**. Jeden seed; najsłabszy arkusz 40.0% (+5 pp nad progiem) przy szumie seedów 2–3 pp (do 3.3 pp między dwoma stockami IQ3_XXS). Kwantyzacje IQ2 bez MIX leżą na progu (33.6–34.5%). Egzamin Q2 szedł na Modal z aktualnym llama.cpp `server-cuda` (tam też jest `--reasoning-budget-message`) — przed zmianą finału test na sucho z buildem H100.
- Warunek przełączenia: drugi seed `q35-4b-q2-iq2mpl-e4k-mix__struct2-s43` (2024+2025; przerwany, do uruchomienia: `modal run --detach overnight/modal_q2mix43.py::main` po `python overnight/modal_q2mix43.py snapshot` z harnessem z `/tmp/q2_snap`) ze średnią ≥ ~38%. Jeśli wyjdzie niżej — zostać przy IQ3_XXS-PL-E4K (1.87 GB, 43.7%) albo stocku UD-IQ3_XXS (1.95 GB).
- Esej structured dla obecnego finału UD-IQ3_XXS: +1.6 pp na 2024+2025 (0+2 → 2+2 pkt), 2026 bez zmian; mały, ale bez strat i bez pętli — do decyzji koordynatora (`server/final_configs.json` nie zmieniany).
- Nie zrobione: `--essay-plan-think`, `--essay-pick kb/mix` na egzaminie (w dev tylko wybór modelu), drugi seed E4K, KLD.

## Koszty i przebiegi

- Sędzia gpt-6-luna: ≈ **$0.79** (eseje dev $0.31 za 33 eseje ≈ $0.009/esej; pełne arkusze Q2 $0.48; oceny pozostałych odpowiedzi IQ3_XXS skopiowane `judge_reuse`). Drugi seed MIX (przerwany) dodałby ≈ $0.16.
- Modal: 4 zadania H100 po ~15–20 min (trzy serwery na GPU).
- Przebiegi: pełne `q35-4b-q2-iq2mpl-e4k-mix__struct2-s42`, `q35-4b-q2-iq2mpl-e4k__struct2-s42` (2024/2025/2026; wolumen Modal `matura-results` `q2mix/`, `q2/`, lokalnie `runs/`), przerwany bez wyników `q35-4b-q2-iq2mpl-e4k-mix__struct2-s43`; eseje `q35-4b-essay-iq3xxs-{base,STRUCT,struct2}-s42/43`, `q35-4b-essay-iq2mpl-e4k-{base,struct2}-s42/43` (essays3_v2; IQ3_XXS na H100 i lokalnie, IQ2 z Modal `q2e/`). Na H100 zostały też niesędziowane eseje `essays12_rag` (base/STRUCT v1).

Pliki: `harness/run_exam.py` (tryb structured), `server/q2e_essay_dev.sh`, `overnight/modal_q2.py`, `overnight/modal_q2e.py`, `overnight/modal_q2mix.py`; na L40S `~/models/custom/qwen35-4b/work/q2_build.sh`, `ppl_q2.sh`, `tt_UD-IQ2_M*.txt`, logi `quant_*.log`, `cpu_ppl_*IQ2_M*.log`.

## 6. Drugi seed i decyzja (27.09 05:15–05:45)

Drugi seed na **naszym** L40S (llama.cpp build 2145525, ten sam co na H100 — zamyka też wątpliwość „inny build na Modal”): dwa serwery MIX (porty 8661/8662, flagi jak finał T3), harness T3 + `--essay-mode structured --seed 43`, skrypt `server/q2_mix_s43.sh` na L40S (~12 min na arkusz). Przebieg `q35-4b-q2-iq2mpl-e4k-mix__struct2-s43`.

| Seed | 2024 | 2025 | średnia | 2026 | powtórki bez myślenia (24/25) | esej pkt (24/25) |
|---|---|---|---|---|---|---|
| s42 (Modal, llama.cpp `server-cuda`) | 42.4% | 40.0% | 41.2% | 45.0% | 2 / 0 | 1 / 1 |
| **s43 (L40S, build 2145525)** | **49.2%** | **40.0%** | **44.5%** | — | 1 / 3 | 2 / 1 |
| **średnia 2 seedów** | 45.8% | 40.0% | **42.9%** | 45.0% | | |

Reguła: s43 ≥ 38% **i** średnia s42+s43 ≥ 40% → **spełniona (44.5% i 42.9%)** → T3 przełączony.

Zmiany:
- `server/final_configs.json`: T3 tuned i base `-m models/custom/qwen35-4b/Qwen3.5-4B-IQ2_M-PL-E4K-MIX.gguf` (`exam_run.sh` zamienia `models/` na `~/models/`); tuned harness: `--essay-mode structured` zamiast `--essay-topic-detect --essay-extend 2 --essay-min-words 300`; reszta (limit myślenia 5000 + `reasoning_budget_message`, temp. 0.6, `--kb-essay`) bez zmian. Poprzedni T3 (UD-IQ3_XXS) w `_comment_T3_old2`.
- sha256 MIX zgodne na H100 i L40S: `1d4eaec76a59d638b36f5b11411edf5bdbab6b40633c17d3b04cbc692cd38845`, 1 745 906 784 B.
- `server/RUNBOOK.md` (wiersze T3 w tabelach zgłoszeń i rozmiarów, oczekiwane wyniki, sekcja zmian), linia „T3 — plik modelu” w `SOURCE.md`, tabela wyników w `CONTEXT.md`. Uwaga: wiersz T3 w tabeli rozwiązań na górze `SOURCE.md` nadal opisuje UD-IQ3_XXS — do poprawienia przez koordynatora.
- Test na sucho `server/exam_run.sh … T3 tuned`: L40S — mini-paczka z mocka 2023 (esej 26, zadania 1 i 2.1), port 8672: 3 odpowiedzi, 0 błędów, 0 powtórek, esej 488 wyrazów „Temat nr 1”, 3 akapity structured, serwer załadował plik MIX; H100 — pełny mock 2023, port 8671 (GPU dzielony z Gemmą): 37 odpowiedzi, 0 błędów, 2 powtórki bez myślenia, 13.9 min, `answers.json OK`, esej structured z nagłówkiem.

Koszty tej rundy: sędzia $0.148 (63 oceny) → łącznie sędzia ≈ **$0.94**. **Modal (z `modal billing report --for today`)**: moje zadania `matura-t3-q2` $1.41, `matura-t3-q2mix` $0.98, `matura-t3-q2e` $0.48, `matura-t3-q2mix43` $0.29 = **$3.17**, z czego H100 $2.80 ≈ 42.6 min H100 ($3.95/h), reszta CPU/pamięć. `modal billing summary`: w tym okresie $30.45 zużycia, $30 kredytów wyczerpane, $0.38 ponad kredyt — stąd `workspace … is disabled` przy s43 na Modal. Modal nie jest już używany.
