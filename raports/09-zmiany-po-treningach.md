# 09 — Zmiany po treningach: obecne rozwiązania vs nowe (paczki v2, sędzia gpt-6-luna)

Generowane przez `python eval/analyze.py --registry eval/runs_registry_v2.json`. Paczki v2 mają znaczniki `[Obraz: …]` jak oficjalny exam.json; sędzia `gpt-6-luna` dla wszystkich przebiegów; zadanie 2024/21 (filtr treści sędziego) poza mianownikiem. Wynik główny = 2024 + 2025 (119 pkt), potwierdzenie = 2026.

## Podsumowanie: jak nowe rozwiązania zmieniają obecne (nd 01:00)

| Track | Obecne (sob 20:00) | Nowe | Zmiana |
|---|---|---|---|
| **T1** | Gemma-4-12B QAT, `t1final`: 71.0% (2 seedy), 83.3% na 2026 | bez zmian | żaden z wariantów nie pomógł: stary prompt 72.3% (szum), kompendium w eseju 68.9%, RAG PolQA + baza 68.1%, temperatura 0.6 71.4% |
| **T2** | PLLuM-12B-base + LoRA v1 (1.8 tys. przykładów): 41.2%, 26.7% na 2026; goła baza 0% | **ta sama baza + LoRA na ~12 tys. przykładów (przepis v1) + RAG PolQA top-3 i 1 notatka z bazy wiedzy: 52.9%, 41.7% na 2026** | **+11.7 pp (2024+2025), +15.0 pp (2026)**; przyrost względem gołej bazy +52.9 / +41.7 pp. Rozmiar bez zmian: 7.71 GB |
| **T3** | Qwen3.5-4B Q4_K_M, 2.74 GB: 48.7 / 50.4% | **Qwen3.5-4B Q3_K_M, 2.29 GB, temperatura 0.6: 48.7 / 51.3%, 48.3% na 2026** | **rozmiar −0.45 GB (−16%) przy tym samym wyniku**; przy temperaturze 1.0 Q3_K_M miał duży rozrzut (38.7–48.7%) |

**Co nie zadziałało** (szczegóły w raporcie 07): dane z rozumowaniem dla T2 (H-N15), dane v2 z kontekstem RAFT (H-N26), LoRA z maską myślenia dla T3 — bramka wykryła skrócenie myślenia o 77% (H-N22), Gemma-4 pt jako baza T2 (niestabilna w llama.cpp; H-N2), routing do Bielika (H-N23), wybór tematu eseju (H-H8), niższe kwantyzacje (IQ3_XXS 36%, IQ2_M 21%, Q3_K_S 36%).

**Dane i koszt nocy (szacunki):** 10 243 nowych zadań E5 (odrzucone 15%; typy, epoki i zakres zgodne z limitami) + baza wiedzy (oś czasu 2817, postacie 940, pojęcia 627, kompendium +106); API: E5 ~6.6 $, E6 ~3.8 $, sędzia ~3 $ (szacunki `common.py`/`judge_openai.py`). GPU: Nebius H100 ~7.5 h (~29 $), L40S ~6 h (~10 $), Modal 5 treningów (~8 $), Forgehand (przedpłacone). Statystyki danych poniżej (sekcja E) dotyczą zbioru, na którym trenował zwycięzca T2 (`data/sft/v2plain`, bez kontekstu RAG).


## A. Wyniki łączne (test2024_v2 + test2025_v2; potwierdzenie: test2026_v2)

| track | przebieg | rozmiar [GB] | wynik główny | przyrost vs baza | potwierdzenie | stan |
|---|---|---|---|---|---|---|
| T1 | T1 Gemma QAT t1final s42 | 6.98 | 72.3% |  | 83.3% | pełny |
| T1 | T1 Gemma QAT t1final s43 | 6.98 | 69.7% |  | — | pełny |
| T1 | T1 Gemma QAT stary prompt s42 | 6.98 | 73.1% |  | — | pełny |
| T1 | T1 Gemma QAT stary prompt s43 | 6.98 | 71.4% |  | — | pełny |
| T2 | T2 PLLuM-12B-base goły | 7.48 | 0.0% |  | — | pełny |
| T2 | T2 PLLuM-12B-base + LoRA v1 | 7.71 | 41.2% | +41.2 pp | 26.7% | pełny |
| T2 | T2 Gemma-4-12B pt goła | 7.5 | 0.0% |  | — | pełny |
| T2 | T2 Gemma-4-12B pt + LoRA v1 (scalona) | 7.5 | 0.8% | +0.8 pp | — | pełny |
| T3 | T3 Qwen3.5-4B Q4_K_M | 2.74 | 48.7% |  | — | pełny |
| T3 | T3 Qwen3.5-4B IQ3_XXS | 1.95 | 36.1% |  | — | pełny |
| T3 | T3 Qwen3.5-4B IQ2_M | 1.76 | 21.0% |  | — | pełny |
| T3 | T3 Qwen3.5-2B Q4_K_M | 1.28 | 17.6% |  | — | pełny |
| T3 | T3 Qwen3.5-2B Q4_K_M + HyDE | 1.28 | 21.8% |  | — | pełny |
| T3 | Bielik-4.5B-v3-Instruct Q4_K_M | 2.9 | 31.1% |  | — | pełny |
| T3 | Bielik-4.5B-v3-Instruct Q3_K_M | 2.3 | 7.6% |  | — | pełny |
| T1 | T1 Gemma QAT t1final + kompendium (esej) s42 | 6.98 | 69.7% |  | — | pełny |
| T1 | T1 Gemma QAT t1final + kompendium (esej) s43 | 6.98 | 68.1% |  | — | pełny |
| T2 | T2 PLLuM + LoRA v1 + kompendium (esej) | 7.71 | 37.8% | +37.8 pp | — | pełny |
| T2 | T2 PLLuM + LoRA v1 + kompendium hybryda | 7.71 | 34.5% | +34.5 pp | — | pełny |
| T2 | T2 PLLuM + LoRA v2 think | 7.71 | 37.8% | +37.8 pp | — | pełny |
| T2 | T2 PLLuM + LoRA v2 think + kompendium | 7.71 | 37.8% | +37.8 pp | — | pełny |
| T2 | T2 PLLuM + LoRA v2 answer | 7.71 | 38.7% | +38.7 pp | — | pełny |
| T2 | T2 PLLuM + LoRA v2 answer + kompendium | 7.71 | 38.7% | +38.7 pp | — | pełny |
| T2 | T2 Gemma pt + LoRA v1, tylko tekst (diagnostyka) | 7.38 | — |  | — | niepełny |
| T3 | T3 Qwen3.5-4B IQ4_XS | 2.48 | 41.2% |  | — | pełny |
| T3 | T3 Qwen3.5-4B Q3_K_M | 2.29 | 48.7% |  | 48.3% | pełny |
| T3 | T3 Qwen3.5-4B IQ3_XXS + RAG z bazy wiedzy (hybryda) | 1.95 | 33.6% |  | — | pełny |
| T3 | T3 Qwen3.5-4B IQ3_XXS, myślenie tylko rozstrzygnij/otwarte | 1.95 | 31.1% |  | — | pełny |
| T2 | T2 PLLuM + LoRA v2 answer + RAG z bazy wiedzy | 7.71 | 33.6% | +33.6 pp | — | pełny |
| T2 | T2 PLLuM + LoRA v2 answer + RAG PolQA + baza | 7.71 | 42.0% | +42.0 pp | 38.3% | pełny |
| T3 | T3 Qwen3.5-4B Q3_K_M s43 | 2.29 | 38.7% |  | — | pełny |
| T3 | T3 Qwen3.5-4B Q3_K_S | 2.11 | 36.1% |  | 35.0% | pełny |
| T2 | T2 PLLuM + LoRA v2 pełne dane, 2 epoki | 7.71 | 40.0% | +40.0 pp | — | pełny |
| T2 | T2 PLLuM + LoRA v2 pełne dane, 2 epoki + RAG z bazy | 7.71 | 43.7% | +43.7 pp | — | pełny |
| T2 | T2 PLLuM + LoRA przepis v1 na pełnych danych (2 epoki) | 7.71 | 40.3% | +40.3 pp | 40.0% | pełny |
| T2 | T2 PLLuM + LoRA przepis v1 pełne dane + RAG PolQA + baza | 7.71 | 52.9% | +52.9 pp | 41.7% | pełny |
| T2 | T2 PLLuM + LoRA v2 pełne dane 2 ep. + RAG PolQA + baza | 7.71 | 44.5% | +44.5 pp | — | pełny |
| T2 | T2 PLLuM + LoRA v2 answer + RAG PolQA + baza, bramka BM25 >= 12 | 7.71 | 42.9% | +42.9 pp | — | pełny |
| T3 | T3 Qwen3.5-4B Q4_K_M s43 | 2.74 | 50.4% |  | — | pełny |
| T3 | T3 Qwen3.5-4B Q3_K_M s44 | 2.29 | 42.0% |  | — | pełny |
| T3 | T3 Qwen3.5-4B Q3_K_M temp 0.6 s42 | 2.29 | 48.7% |  | 48.3% | pełny |
| T3 | T3 Qwen3.5-4B Q3_K_M temp 0.6 s43 | 2.29 | 51.3% |  | — | pełny |
| T3 | T3 Qwen3.5-4B Q3_K_M + RAG PolQA + baza | 2.29 | 42.9% |  | — | pełny |
| T1 | T1 Gemma QAT t1final + RAG PolQA + baza s42 | 6.98 | 68.1% |  | — | pełny |
| T1 | T1 Gemma QAT t1final temp 0.6 s42 | 6.98 | 71.4% |  | — | pełny |

## B. Wyniki według kategorii

### Typ zadania

| przebieg | closed_choice | closed_match | closed_tf | essay | open: inne | open: podaj | open: rozstrzygnij | open: wyjaśnij/uzasadnij | razem |
|---|---|---|---|---|---|---|---|---|---|
| T1 Gemma QAT t1final s42 | 83% (5/6) | 100% (6/6) | 75% (6/8) | 50% (15/30) | 100% (5/5) | 79% (19/24) | 79% (22/28) | 67% (8/12) | **72% (86/119)** |
| T1 Gemma QAT t1final s43 | 83% (5/6) | 67% (4/6) | 75% (6/8) | 47% (14/30) | 100% (5/5) | 83% (20/24) | 71% (20/28) | 75% (9/12) | **70% (83/119)** |
| T1 Gemma QAT stary prompt s42 | 100% (6/6) | 67% (4/6) | 62% (5/8) | 50% (15/30) | 100% (5/5) | 79% (19/24) | 79% (22/28) | 92% (11/12) | **73% (87/119)** |
| T1 Gemma QAT stary prompt s43 | 83% (5/6) | 83% (5/6) | 75% (6/8) | 63% (19/30) | 100% (5/5) | 71% (17/24) | 71% (20/28) | 67% (8/12) | **71% (85/119)** |
| T2 PLLuM-12B-base goły | 0% (0/6) | 0% (0/6) | 0% (0/8) | 0% (0/30) | 0% (0/5) | 0% (0/24) | 0% (0/28) | 0% (0/12) | **0% (0/119)** |
| T2 PLLuM-12B-base + LoRA v1 | 67% (4/6) | 0% (0/6) | 88% (7/8) | 53% (16/30) | 60% (3/5) | 38% (9/24) | 29% (8/28) | 17% (2/12) | **41% (49/119)** |
| T2 Gemma-4-12B pt goła | 0% (0/6) | 0% (0/6) | 0% (0/8) | 0% (0/30) | 0% (0/6) | 0% (0/24) | 0% (0/28) | 0% (0/12) | **0% (0/120)** |
| T2 Gemma-4-12B pt + LoRA v1 (scalona) | 0% (0/6) | 0% (0/6) | 0% (0/8) | 0% (0/30) | 0% (0/6) | 4% (1/24) | 0% (0/28) | 0% (0/12) | **1% (1/120)** |
| T3 Qwen3.5-4B Q4_K_M | 33% (2/6) | 83% (5/6) | 75% (6/8) | 17% (5/30) | 100% (5/5) | 50% (12/24) | 50% (14/28) | 75% (9/12) | **49% (58/119)** |
| T3 Qwen3.5-4B IQ3_XXS | 50% (3/6) | 0% (0/6) | 75% (6/8) | 7% (2/30) | 80% (4/5) | 42% (10/24) | 39% (11/28) | 58% (7/12) | **36% (43/119)** |
| T3 Qwen3.5-4B IQ2_M | 67% (4/6) | 0% (0/6) | 12% (1/8) | 0% (0/30) | 80% (4/5) | 33% (8/24) | 21% (6/28) | 17% (2/12) | **21% (25/119)** |
| T3 Qwen3.5-2B Q4_K_M | 67% (4/6) | 0% (0/6) | 62% (5/8) | 0% (0/30) | 60% (3/5) | 17% (4/24) | 14% (4/28) | 8% (1/12) | **18% (21/119)** |
| T3 Qwen3.5-2B Q4_K_M + HyDE | 67% (4/6) | 0% (0/6) | 50% (4/8) | 7% (2/30) | 60% (3/5) | 21% (5/24) | 21% (6/28) | 17% (2/12) | **22% (26/119)** |
| Bielik-4.5B-v3-Instruct Q4_K_M | 50% (3/6) | 33% (2/6) | 50% (4/8) | 27% (8/30) | 60% (3/5) | 29% (7/24) | 18% (5/28) | 42% (5/12) | **31% (37/119)** |
| Bielik-4.5B-v3-Instruct Q3_K_M | 50% (3/6) | 0% (0/6) | 38% (3/8) | 0% (0/30) | 40% (2/5) | 4% (1/24) | 0% (0/28) | 0% (0/12) | **8% (9/119)** |
| T1 Gemma QAT t1final + kompendium (esej) s42 | 67% (4/6) | 100% (6/6) | 50% (4/8) | 47% (14/30) | 100% (5/5) | 83% (20/24) | 75% (21/28) | 75% (9/12) | **70% (83/119)** |
| T1 Gemma QAT t1final + kompendium (esej) s43 | 67% (4/6) | 50% (3/6) | 62% (5/8) | 50% (15/30) | 100% (5/5) | 67% (16/24) | 86% (24/28) | 75% (9/12) | **68% (81/119)** |
| T2 PLLuM + LoRA v1 + kompendium (esej) | 50% (3/6) | 17% (1/6) | 88% (7/8) | 43% (13/30) | 40% (2/5) | 33% (8/24) | 21% (6/28) | 42% (5/12) | **38% (45/119)** |
| T2 PLLuM + LoRA v1 + kompendium hybryda | 67% (4/6) | 17% (1/6) | 88% (7/8) | 20% (6/30) | 40% (2/5) | 42% (10/24) | 25% (7/28) | 33% (4/12) | **34% (41/119)** |
| T2 PLLuM + LoRA v2 think | 50% (3/6) | 83% (5/6) | 50% (4/8) | 37% (11/30) | 0% (0/5) | 46% (11/24) | 25% (7/28) | 33% (4/12) | **38% (45/119)** |
| T2 PLLuM + LoRA v2 think + kompendium | 50% (3/6) | 83% (5/6) | 50% (4/8) | 40% (12/30) | 20% (1/5) | 42% (10/24) | 29% (8/28) | 17% (2/12) | **38% (45/119)** |
| T2 PLLuM + LoRA v2 answer | 67% (4/6) | 67% (4/6) | 75% (6/8) | 37% (11/30) | 40% (2/5) | 38% (9/24) | 18% (5/28) | 42% (5/12) | **39% (46/119)** |
| T2 PLLuM + LoRA v2 answer + kompendium | 67% (4/6) | 67% (4/6) | 88% (7/8) | 43% (13/30) | 60% (3/5) | 25% (6/24) | 18% (5/28) | 33% (4/12) | **39% (46/119)** |
| T2 Gemma pt + LoRA v1, tylko tekst (diagnostyka) | 67% (2/3) | 0% (0/1) | 75% (3/4) | 20% (3/15) | 67% (2/3) | 33% (4/12) | 29% (4/14) | 14% (1/7) | **32% (19/59)** |
| T3 Qwen3.5-4B IQ4_XS | 50% (3/6) | 50% (3/6) | 100% (8/8) | 0% (0/30) | 80% (4/5) | 46% (11/24) | 50% (14/28) | 50% (6/12) | **41% (49/119)** |
| T3 Qwen3.5-4B Q3_K_M | 50% (3/6) | 33% (2/6) | 25% (2/8) | 27% (8/30) | 60% (3/5) | 58% (14/24) | 64% (18/28) | 67% (8/12) | **49% (58/119)** |
| T3 Qwen3.5-4B IQ3_XXS + RAG z bazy wiedzy (hybryda) | 50% (3/6) | 0% (0/6) | 75% (6/8) | 0% (0/30) | 60% (3/5) | 46% (11/24) | 43% (12/28) | 42% (5/12) | **34% (40/119)** |
| T3 Qwen3.5-4B IQ3_XXS, myślenie tylko rozstrzygnij/otwarte | 50% (3/6) | 0% (0/6) | 50% (4/8) | 3% (1/30) | 100% (5/5) | 29% (7/24) | 43% (12/28) | 42% (5/12) | **31% (37/119)** |
| T2 PLLuM + LoRA v2 answer + RAG z bazy wiedzy | 67% (4/6) | 67% (4/6) | 75% (6/8) | 10% (3/30) | 60% (3/5) | 38% (9/24) | 25% (7/28) | 33% (4/12) | **34% (40/119)** |
| T2 PLLuM + LoRA v2 answer + RAG PolQA + baza | 67% (4/6) | 67% (4/6) | 75% (6/8) | 27% (8/30) | 80% (4/5) | 33% (8/24) | 36% (10/28) | 50% (6/12) | **42% (50/119)** |
| T3 Qwen3.5-4B Q3_K_M s43 | 50% (3/6) | 50% (3/6) | 50% (4/8) | 13% (4/30) | 100% (5/5) | 50% (12/24) | 43% (12/28) | 25% (3/12) | **39% (46/119)** |
| T3 Qwen3.5-4B Q3_K_S | 33% (2/6) | 0% (0/6) | 62% (5/8) | 20% (6/30) | 80% (4/5) | 42% (10/24) | 46% (13/28) | 25% (3/12) | **36% (43/119)** |
| T2 PLLuM + LoRA v2 pełne dane, 2 epoki | 67% (4/6) | 67% (4/6) | 75% (6/8) | 23% (7/30) | 67% (4/6) | 46% (11/24) | 25% (7/28) | 42% (5/12) | **40% (48/120)** |
| T2 PLLuM + LoRA v2 pełne dane, 2 epoki + RAG z bazy | 67% (4/6) | 67% (4/6) | 75% (6/8) | 33% (10/30) | 80% (4/5) | 50% (12/24) | 29% (8/28) | 33% (4/12) | **44% (52/119)** |
| T2 PLLuM + LoRA przepis v1 na pełnych danych (2 epoki) | 83% (5/6) | 50% (3/6) | 50% (4/8) | 27% (8/30) | 80% (4/5) | 62% (15/24) | 21% (6/28) | 25% (3/12) | **40% (48/119)** |
| T2 PLLuM + LoRA przepis v1 pełne dane + RAG PolQA + baza | 83% (5/6) | 67% (4/6) | 50% (4/8) | 53% (16/30) | 80% (4/5) | 62% (15/24) | 32% (9/28) | 50% (6/12) | **53% (63/119)** |
| T2 PLLuM + LoRA v2 pełne dane 2 ep. + RAG PolQA + baza | 67% (4/6) | 67% (4/6) | 75% (6/8) | 40% (12/30) | 60% (3/5) | 50% (12/24) | 29% (8/28) | 33% (4/12) | **45% (53/119)** |
| T2 PLLuM + LoRA v2 answer + RAG PolQA + baza, bramka BM25 >= 12 | 67% (4/6) | 67% (4/6) | 75% (6/8) | 47% (14/30) | 40% (2/5) | 25% (6/24) | 29% (8/28) | 58% (7/12) | **43% (51/119)** |
| T3 Qwen3.5-4B Q4_K_M s43 | 50% (3/6) | 50% (3/6) | 75% (6/8) | 10% (3/30) | 100% (5/5) | 50% (12/24) | 64% (18/28) | 83% (10/12) | **50% (60/119)** |
| T3 Qwen3.5-4B Q3_K_M s44 | 67% (4/6) | 17% (1/6) | 62% (5/8) | 7% (2/30) | 100% (5/5) | 54% (13/24) | 46% (13/28) | 58% (7/12) | **42% (50/119)** |
| T3 Qwen3.5-4B Q3_K_M temp 0.6 s42 | 67% (4/6) | 0% (0/6) | 50% (4/8) | 7% (2/30) | 100% (5/5) | 58% (14/24) | 71% (20/28) | 75% (9/12) | **49% (58/119)** |
| T3 Qwen3.5-4B Q3_K_M temp 0.6 s43 | 67% (4/6) | 67% (4/6) | 88% (7/8) | 20% (6/30) | 80% (4/5) | 58% (14/24) | 54% (15/28) | 58% (7/12) | **51% (61/119)** |
| T3 Qwen3.5-4B Q3_K_M + RAG PolQA + baza | 50% (3/6) | 50% (3/6) | 88% (7/8) | 10% (3/30) | 80% (4/5) | 54% (13/24) | 50% (14/28) | 33% (4/12) | **43% (51/119)** |
| T1 Gemma QAT t1final + RAG PolQA + baza s42 | 83% (5/6) | 83% (5/6) | 62% (5/8) | 40% (12/30) | 100% (5/5) | 88% (21/24) | 71% (20/28) | 67% (8/12) | **68% (81/119)** |
| T1 Gemma QAT t1final temp 0.6 s42 | 67% (4/6) | 50% (3/6) | 50% (4/8) | 70% (21/30) | 100% (5/5) | 79% (19/24) | 75% (21/28) | 67% (8/12) | **71% (85/119)** |

### Epoka

| przebieg | 1 starożytność | 2 średniowiecze | 3 nowożytność | 4 XIX w. (1815–1914) | 5 1914–1945 | 6 po 1945 | essay | razem |
|---|---|---|---|---|---|---|---|---|
| T1 Gemma QAT t1final s42 | 80% (8/10) | 90% (9/10) | 75% (18/24) | 86% (12/14) | 79% (15/19) | 75% (9/12) | 50% (15/30) | **72% (86/119)** |
| T1 Gemma QAT t1final s43 | 90% (9/10) | 70% (7/10) | 79% (19/24) | 79% (11/14) | 79% (15/19) | 67% (8/12) | 47% (14/30) | **70% (83/119)** |
| T1 Gemma QAT stary prompt s42 | 100% (10/10) | 70% (7/10) | 75% (18/24) | 79% (11/14) | 79% (15/19) | 92% (11/12) | 50% (15/30) | **73% (87/119)** |
| T1 Gemma QAT stary prompt s43 | 90% (9/10) | 70% (7/10) | 75% (18/24) | 79% (11/14) | 63% (12/19) | 75% (9/12) | 63% (19/30) | **71% (85/119)** |
| T2 PLLuM-12B-base goły | 0% (0/10) | 0% (0/10) | 0% (0/24) | 0% (0/14) | 0% (0/19) | 0% (0/12) | 0% (0/30) | **0% (0/119)** |
| T2 PLLuM-12B-base + LoRA v1 | 30% (3/10) | 20% (2/10) | 33% (8/24) | 64% (9/14) | 32% (6/19) | 42% (5/12) | 53% (16/30) | **41% (49/119)** |
| T2 Gemma-4-12B pt goła | 0% (0/10) | 0% (0/10) | 0% (0/24) | 0% (0/14) | 0% (0/20) | 0% (0/12) | 0% (0/30) | **0% (0/120)** |
| T2 Gemma-4-12B pt + LoRA v1 (scalona) | 10% (1/10) | 0% (0/10) | 0% (0/24) | 0% (0/14) | 0% (0/20) | 0% (0/12) | 0% (0/30) | **1% (1/120)** |
| T3 Qwen3.5-4B Q4_K_M | 70% (7/10) | 60% (6/10) | 46% (11/24) | 79% (11/14) | 53% (10/19) | 67% (8/12) | 17% (5/30) | **49% (58/119)** |
| T3 Qwen3.5-4B IQ3_XXS | 40% (4/10) | 30% (3/10) | 38% (9/24) | 57% (8/14) | 53% (10/19) | 58% (7/12) | 7% (2/30) | **36% (43/119)** |
| T3 Qwen3.5-4B IQ2_M | 30% (3/10) | 20% (2/10) | 29% (7/24) | 29% (4/14) | 21% (4/19) | 42% (5/12) | 0% (0/30) | **21% (25/119)** |
| T3 Qwen3.5-2B Q4_K_M | 30% (3/10) | 20% (2/10) | 25% (6/24) | 29% (4/14) | 16% (3/19) | 25% (3/12) | 0% (0/30) | **18% (21/119)** |
| T3 Qwen3.5-2B Q4_K_M + HyDE | 30% (3/10) | 20% (2/10) | 21% (5/24) | 36% (5/14) | 26% (5/19) | 33% (4/12) | 7% (2/30) | **22% (26/119)** |
| Bielik-4.5B-v3-Instruct Q4_K_M | 30% (3/10) | 50% (5/10) | 21% (5/24) | 50% (7/14) | 37% (7/19) | 17% (2/12) | 27% (8/30) | **31% (37/119)** |
| Bielik-4.5B-v3-Instruct Q3_K_M | 10% (1/10) | 0% (0/10) | 8% (2/24) | 29% (4/14) | 5% (1/19) | 8% (1/12) | 0% (0/30) | **8% (9/119)** |
| T1 Gemma QAT t1final + kompendium (esej) s42 | 100% (10/10) | 90% (9/10) | 75% (18/24) | 79% (11/14) | 68% (13/19) | 67% (8/12) | 47% (14/30) | **70% (83/119)** |
| T1 Gemma QAT t1final + kompendium (esej) s43 | 90% (9/10) | 80% (8/10) | 58% (14/24) | 93% (13/14) | 68% (13/19) | 75% (9/12) | 50% (15/30) | **68% (81/119)** |
| T2 PLLuM + LoRA v1 + kompendium (esej) | 40% (4/10) | 20% (2/10) | 25% (6/24) | 57% (8/14) | 42% (8/19) | 33% (4/12) | 43% (13/30) | **38% (45/119)** |
| T2 PLLuM + LoRA v1 + kompendium hybryda | 40% (4/10) | 30% (3/10) | 33% (8/24) | 57% (8/14) | 42% (8/19) | 33% (4/12) | 20% (6/30) | **34% (41/119)** |
| T2 PLLuM + LoRA v2 think | 50% (5/10) | 50% (5/10) | 46% (11/24) | 43% (6/14) | 32% (6/19) | 8% (1/12) | 37% (11/30) | **38% (45/119)** |
| T2 PLLuM + LoRA v2 think + kompendium | 70% (7/10) | 30% (3/10) | 46% (11/24) | 36% (5/14) | 32% (6/19) | 8% (1/12) | 40% (12/30) | **38% (45/119)** |
| T2 PLLuM + LoRA v2 answer | 30% (3/10) | 40% (4/10) | 46% (11/24) | 57% (8/14) | 26% (5/19) | 33% (4/12) | 37% (11/30) | **39% (46/119)** |
| T2 PLLuM + LoRA v2 answer + kompendium | 40% (4/10) | 30% (3/10) | 42% (10/24) | 50% (7/14) | 26% (5/19) | 33% (4/12) | 43% (13/30) | **39% (46/119)** |
| T2 Gemma pt + LoRA v1, tylko tekst (diagnostyka) | 20% (1/5) | 0% (0/5) | 17% (2/12) | 83% (5/6) | 57% (4/7) | 44% (4/9) | 20% (3/15) | **32% (19/59)** |
| T3 Qwen3.5-4B IQ4_XS | 60% (6/10) | 40% (4/10) | 38% (9/24) | 86% (12/14) | 42% (8/19) | 83% (10/12) | 0% (0/30) | **41% (49/119)** |
| T3 Qwen3.5-4B Q3_K_M | 90% (9/10) | 40% (4/10) | 46% (11/24) | 71% (10/14) | 42% (8/19) | 67% (8/12) | 27% (8/30) | **49% (58/119)** |
| T3 Qwen3.5-4B IQ3_XXS + RAG z bazy wiedzy (hybryda) | 70% (7/10) | 30% (3/10) | 33% (8/24) | 64% (9/14) | 37% (7/19) | 50% (6/12) | 0% (0/30) | **34% (40/119)** |
| T3 Qwen3.5-4B IQ3_XXS, myślenie tylko rozstrzygnij/otwarte | 50% (5/10) | 30% (3/10) | 33% (8/24) | 50% (7/14) | 37% (7/19) | 50% (6/12) | 3% (1/30) | **31% (37/119)** |
| T2 PLLuM + LoRA v2 answer + RAG z bazy wiedzy | 50% (5/10) | 40% (4/10) | 50% (12/24) | 50% (7/14) | 32% (6/19) | 25% (3/12) | 10% (3/30) | **34% (40/119)** |
| T2 PLLuM + LoRA v2 answer + RAG PolQA + baza | 70% (7/10) | 40% (4/10) | 54% (13/24) | 43% (6/14) | 37% (7/19) | 42% (5/12) | 27% (8/30) | **42% (50/119)** |
| T3 Qwen3.5-4B Q3_K_M s43 | 80% (8/10) | 20% (2/10) | 38% (9/24) | 79% (11/14) | 32% (6/19) | 50% (6/12) | 13% (4/30) | **39% (46/119)** |
| T3 Qwen3.5-4B Q3_K_S | 50% (5/10) | 30% (3/10) | 38% (9/24) | 64% (9/14) | 26% (5/19) | 50% (6/12) | 20% (6/30) | **36% (43/119)** |
| T2 PLLuM + LoRA v2 pełne dane, 2 epoki | 40% (4/10) | 50% (5/10) | 46% (11/24) | 57% (8/14) | 40% (8/20) | 42% (5/12) | 23% (7/30) | **40% (48/120)** |
| T2 PLLuM + LoRA v2 pełne dane, 2 epoki + RAG z bazy | 70% (7/10) | 40% (4/10) | 50% (12/24) | 57% (8/14) | 37% (7/19) | 33% (4/12) | 33% (10/30) | **44% (52/119)** |
| T2 PLLuM + LoRA przepis v1 na pełnych danych (2 epoki) | 30% (3/10) | 50% (5/10) | 50% (12/24) | 57% (8/14) | 26% (5/19) | 58% (7/12) | 27% (8/30) | **40% (48/119)** |
| T2 PLLuM + LoRA przepis v1 pełne dane + RAG PolQA + baza | 60% (6/10) | 40% (4/10) | 71% (17/24) | 57% (8/14) | 32% (6/19) | 50% (6/12) | 53% (16/30) | **53% (63/119)** |
| T2 PLLuM + LoRA v2 pełne dane 2 ep. + RAG PolQA + baza | 60% (6/10) | 40% (4/10) | 46% (11/24) | 57% (8/14) | 37% (7/19) | 42% (5/12) | 40% (12/30) | **45% (53/119)** |
| T2 PLLuM + LoRA v2 answer + RAG PolQA + baza, bramka BM25 >= 12 | 40% (4/10) | 40% (4/10) | 42% (10/24) | 43% (6/14) | 47% (9/19) | 33% (4/12) | 47% (14/30) | **43% (51/119)** |
| T3 Qwen3.5-4B Q4_K_M s43 | 80% (8/10) | 50% (5/10) | 50% (12/24) | 79% (11/14) | 47% (9/19) | 100% (12/12) | 10% (3/30) | **50% (60/119)** |
| T3 Qwen3.5-4B Q3_K_M s44 | 70% (7/10) | 50% (5/10) | 46% (11/24) | 71% (10/14) | 42% (8/19) | 58% (7/12) | 7% (2/30) | **42% (50/119)** |
| T3 Qwen3.5-4B Q3_K_M temp 0.6 s42 | 70% (7/10) | 50% (5/10) | 58% (14/24) | 71% (10/14) | 53% (10/19) | 83% (10/12) | 7% (2/30) | **49% (58/119)** |
| T3 Qwen3.5-4B Q3_K_M temp 0.6 s43 | 70% (7/10) | 70% (7/10) | 50% (12/24) | 86% (12/14) | 47% (9/19) | 67% (8/12) | 20% (6/30) | **51% (61/119)** |
| T3 Qwen3.5-4B Q3_K_M + RAG PolQA + baza | 50% (5/10) | 50% (5/10) | 58% (14/24) | 79% (11/14) | 32% (6/19) | 58% (7/12) | 10% (3/30) | **43% (51/119)** |
| T1 Gemma QAT t1final + RAG PolQA + baza s42 | 80% (8/10) | 70% (7/10) | 83% (20/24) | 86% (12/14) | 68% (13/19) | 75% (9/12) | 40% (12/30) | **68% (81/119)** |
| T1 Gemma QAT t1final temp 0.6 s42 | 100% (10/10) | 60% (6/10) | 67% (16/24) | 86% (12/14) | 63% (12/19) | 67% (8/12) | 70% (21/30) | **71% (85/119)** |

### Historia Polski vs powszechna

| przebieg | Polska | essay | powszechna | razem |
|---|---|---|---|---|
| T1 Gemma QAT t1final s42 | 76% (45/59) | 50% (15/30) | 87% (26/30) | **72% (86/119)** |
| T1 Gemma QAT t1final s43 | 68% (40/59) | 47% (14/30) | 97% (29/30) | **70% (83/119)** |
| T1 Gemma QAT stary prompt s42 | 73% (43/59) | 50% (15/30) | 97% (29/30) | **73% (87/119)** |
| T1 Gemma QAT stary prompt s43 | 63% (37/59) | 63% (19/30) | 97% (29/30) | **71% (85/119)** |
| T2 PLLuM-12B-base goły | 0% (0/59) | 0% (0/30) | 0% (0/30) | **0% (0/119)** |
| T2 PLLuM-12B-base + LoRA v1 | 29% (17/59) | 53% (16/30) | 53% (16/30) | **41% (49/119)** |
| T2 Gemma-4-12B pt goła | 0% (0/59) | 0% (0/30) | 0% (0/31) | **0% (0/120)** |
| T2 Gemma-4-12B pt + LoRA v1 (scalona) | 2% (1/59) | 0% (0/30) | 0% (0/31) | **1% (1/120)** |
| T3 Qwen3.5-4B Q4_K_M | 49% (29/59) | 17% (5/30) | 80% (24/30) | **49% (58/119)** |
| T3 Qwen3.5-4B IQ3_XXS | 34% (20/59) | 7% (2/30) | 70% (21/30) | **36% (43/119)** |
| T3 Qwen3.5-4B IQ2_M | 19% (11/59) | 0% (0/30) | 47% (14/30) | **21% (25/119)** |
| T3 Qwen3.5-2B Q4_K_M | 19% (11/59) | 0% (0/30) | 33% (10/30) | **18% (21/119)** |
| T3 Qwen3.5-2B Q4_K_M + HyDE | 24% (14/59) | 7% (2/30) | 33% (10/30) | **22% (26/119)** |
| Bielik-4.5B-v3-Instruct Q4_K_M | 31% (18/59) | 27% (8/30) | 37% (11/30) | **31% (37/119)** |
| Bielik-4.5B-v3-Instruct Q3_K_M | 12% (7/59) | 0% (0/30) | 7% (2/30) | **8% (9/119)** |
| T1 Gemma QAT t1final + kompendium (esej) s42 | 69% (41/59) | 47% (14/30) | 93% (28/30) | **70% (83/119)** |
| T1 Gemma QAT t1final + kompendium (esej) s43 | 64% (38/59) | 50% (15/30) | 93% (28/30) | **68% (81/119)** |
| T2 PLLuM + LoRA v1 + kompendium (esej) | 24% (14/59) | 43% (13/30) | 60% (18/30) | **38% (45/119)** |
| T2 PLLuM + LoRA v1 + kompendium hybryda | 31% (18/59) | 20% (6/30) | 57% (17/30) | **34% (41/119)** |
| T2 PLLuM + LoRA v2 think | 34% (20/59) | 37% (11/30) | 47% (14/30) | **38% (45/119)** |
| T2 PLLuM + LoRA v2 think + kompendium | 34% (20/59) | 40% (12/30) | 43% (13/30) | **38% (45/119)** |
| T2 PLLuM + LoRA v2 answer | 37% (22/59) | 37% (11/30) | 43% (13/30) | **39% (46/119)** |
| T2 PLLuM + LoRA v2 answer + kompendium | 37% (22/59) | 43% (13/30) | 37% (11/30) | **39% (46/119)** |
| T2 Gemma pt + LoRA v1, tylko tekst (diagnostyka) | 32% (10/31) | 20% (3/15) | 46% (6/13) | **32% (19/59)** |
| T3 Qwen3.5-4B IQ4_XS | 49% (29/59) | 0% (0/30) | 67% (20/30) | **41% (49/119)** |
| T3 Qwen3.5-4B Q3_K_M | 47% (28/59) | 27% (8/30) | 73% (22/30) | **49% (58/119)** |
| T3 Qwen3.5-4B IQ3_XXS + RAG z bazy wiedzy (hybryda) | 36% (21/59) | 0% (0/30) | 63% (19/30) | **34% (40/119)** |
| T3 Qwen3.5-4B IQ3_XXS, myślenie tylko rozstrzygnij/otwarte | 32% (19/59) | 3% (1/30) | 57% (17/30) | **31% (37/119)** |
| T2 PLLuM + LoRA v2 answer + RAG z bazy wiedzy | 41% (24/59) | 10% (3/30) | 43% (13/30) | **34% (40/119)** |
| T2 PLLuM + LoRA v2 answer + RAG PolQA + baza | 46% (27/59) | 27% (8/30) | 50% (15/30) | **42% (50/119)** |
| T3 Qwen3.5-4B Q3_K_M s43 | 39% (23/59) | 13% (4/30) | 63% (19/30) | **39% (46/119)** |
| T3 Qwen3.5-4B Q3_K_S | 36% (21/59) | 20% (6/30) | 53% (16/30) | **36% (43/119)** |
| T2 PLLuM + LoRA v2 pełne dane, 2 epoki | 41% (24/59) | 23% (7/30) | 55% (17/31) | **40% (48/120)** |
| T2 PLLuM + LoRA v2 pełne dane, 2 epoki + RAG z bazy | 46% (27/59) | 33% (10/30) | 50% (15/30) | **44% (52/119)** |
| T2 PLLuM + LoRA przepis v1 na pełnych danych (2 epoki) | 44% (26/59) | 27% (8/30) | 47% (14/30) | **40% (48/119)** |
| T2 PLLuM + LoRA przepis v1 pełne dane + RAG PolQA + baza | 54% (32/59) | 53% (16/30) | 50% (15/30) | **53% (63/119)** |
| T2 PLLuM + LoRA v2 pełne dane 2 ep. + RAG PolQA + baza | 42% (25/59) | 40% (12/30) | 53% (16/30) | **45% (53/119)** |
| T2 PLLuM + LoRA v2 answer + RAG PolQA + baza, bramka BM25 >= 12 | 39% (23/59) | 47% (14/30) | 47% (14/30) | **43% (51/119)** |
| T3 Qwen3.5-4B Q4_K_M s43 | 54% (32/59) | 10% (3/30) | 83% (25/30) | **50% (60/119)** |
| T3 Qwen3.5-4B Q3_K_M s44 | 47% (28/59) | 7% (2/30) | 67% (20/30) | **42% (50/119)** |
| T3 Qwen3.5-4B Q3_K_M temp 0.6 s42 | 54% (32/59) | 7% (2/30) | 80% (24/30) | **49% (58/119)** |
| T3 Qwen3.5-4B Q3_K_M temp 0.6 s43 | 53% (31/59) | 20% (6/30) | 80% (24/30) | **51% (61/119)** |
| T3 Qwen3.5-4B Q3_K_M + RAG PolQA + baza | 51% (30/59) | 10% (3/30) | 60% (18/30) | **43% (51/119)** |
| T1 Gemma QAT t1final + RAG PolQA + baza s42 | 71% (42/59) | 40% (12/30) | 90% (27/30) | **68% (81/119)** |
| T1 Gemma QAT t1final temp 0.6 s42 | 63% (37/59) | 70% (21/30) | 90% (27/30) | **71% (85/119)** |

### Obraz

| przebieg | bez obrazu | z obrazem | razem |
|---|---|---|---|
| T1 Gemma QAT t1final s42 | 67% (41/61) | 78% (45/58) | **72% (86/119)** |
| T1 Gemma QAT t1final s43 | 64% (39/61) | 76% (44/58) | **70% (83/119)** |
| T1 Gemma QAT stary prompt s42 | 64% (39/61) | 83% (48/58) | **73% (87/119)** |
| T1 Gemma QAT stary prompt s43 | 69% (42/61) | 74% (43/58) | **71% (85/119)** |
| T2 PLLuM-12B-base goły | 0% (0/61) | 0% (0/58) | **0% (0/119)** |
| T2 PLLuM-12B-base + LoRA v1 | 48% (29/61) | 34% (20/58) | **41% (49/119)** |
| T2 Gemma-4-12B pt goła | 0% (0/61) | 0% (0/59) | **0% (0/120)** |
| T2 Gemma-4-12B pt + LoRA v1 (scalona) | 2% (1/61) | 0% (0/59) | **1% (1/120)** |
| T3 Qwen3.5-4B Q4_K_M | 39% (24/61) | 59% (34/58) | **49% (58/119)** |
| T3 Qwen3.5-4B IQ3_XXS | 21% (13/61) | 52% (30/58) | **36% (43/119)** |
| T3 Qwen3.5-4B IQ2_M | 8% (5/61) | 34% (20/58) | **21% (25/119)** |
| T3 Qwen3.5-2B Q4_K_M | 15% (9/61) | 21% (12/58) | **18% (21/119)** |
| T3 Qwen3.5-2B Q4_K_M + HyDE | 20% (12/61) | 24% (14/58) | **22% (26/119)** |
| Bielik-4.5B-v3-Instruct Q4_K_M | 36% (22/61) | 26% (15/58) | **31% (37/119)** |
| Bielik-4.5B-v3-Instruct Q3_K_M | 3% (2/61) | 12% (7/58) | **8% (9/119)** |
| T1 Gemma QAT t1final + kompendium (esej) s42 | 64% (39/61) | 76% (44/58) | **70% (83/119)** |
| T1 Gemma QAT t1final + kompendium (esej) s43 | 64% (39/61) | 72% (42/58) | **68% (81/119)** |
| T2 PLLuM + LoRA v1 + kompendium (esej) | 41% (25/61) | 34% (20/58) | **38% (45/119)** |
| T2 PLLuM + LoRA v1 + kompendium hybryda | 34% (21/61) | 34% (20/58) | **34% (41/119)** |
| T2 PLLuM + LoRA v2 think | 43% (26/61) | 33% (19/58) | **38% (45/119)** |
| T2 PLLuM + LoRA v2 think + kompendium | 44% (27/61) | 31% (18/58) | **38% (45/119)** |
| T2 PLLuM + LoRA v2 answer | 41% (25/61) | 36% (21/58) | **39% (46/119)** |
| T2 PLLuM + LoRA v2 answer + kompendium | 44% (27/61) | 33% (19/58) | **39% (46/119)** |
| T2 Gemma pt + LoRA v1, tylko tekst (diagnostyka) | 38% (10/26) | 27% (9/33) | **32% (19/59)** |
| T3 Qwen3.5-4B IQ4_XS | 31% (19/61) | 52% (30/58) | **41% (49/119)** |
| T3 Qwen3.5-4B Q3_K_M | 41% (25/61) | 57% (33/58) | **49% (58/119)** |
| T3 Qwen3.5-4B IQ3_XXS + RAG z bazy wiedzy (hybryda) | 26% (16/61) | 41% (24/58) | **34% (40/119)** |
| T3 Qwen3.5-4B IQ3_XXS, myślenie tylko rozstrzygnij/otwarte | 21% (13/61) | 41% (24/58) | **31% (37/119)** |
| T2 PLLuM + LoRA v2 answer + RAG z bazy wiedzy | 31% (19/61) | 36% (21/58) | **34% (40/119)** |
| T2 PLLuM + LoRA v2 answer + RAG PolQA + baza | 43% (26/61) | 41% (24/58) | **42% (50/119)** |
| T3 Qwen3.5-4B Q3_K_M s43 | 34% (21/61) | 43% (25/58) | **39% (46/119)** |
| T3 Qwen3.5-4B Q3_K_S | 28% (17/61) | 45% (26/58) | **36% (43/119)** |
| T2 PLLuM + LoRA v2 pełne dane, 2 epoki | 46% (28/61) | 34% (20/59) | **40% (48/120)** |
| T2 PLLuM + LoRA v2 pełne dane, 2 epoki + RAG z bazy | 52% (32/61) | 34% (20/58) | **44% (52/119)** |
| T2 PLLuM + LoRA przepis v1 na pełnych danych (2 epoki) | 43% (26/61) | 38% (22/58) | **40% (48/119)** |
| T2 PLLuM + LoRA przepis v1 pełne dane + RAG PolQA + baza | 64% (39/61) | 41% (24/58) | **53% (63/119)** |
| T2 PLLuM + LoRA v2 pełne dane 2 ep. + RAG PolQA + baza | 52% (32/61) | 36% (21/58) | **45% (53/119)** |
| T2 PLLuM + LoRA v2 answer + RAG PolQA + baza, bramka BM25 >= 12 | 48% (29/61) | 38% (22/58) | **43% (51/119)** |
| T3 Qwen3.5-4B Q4_K_M s43 | 36% (22/61) | 66% (38/58) | **50% (60/119)** |
| T3 Qwen3.5-4B Q3_K_M s44 | 33% (20/61) | 52% (30/58) | **42% (50/119)** |
| T3 Qwen3.5-4B Q3_K_M temp 0.6 s42 | 31% (19/61) | 67% (39/58) | **49% (58/119)** |
| T3 Qwen3.5-4B Q3_K_M temp 0.6 s43 | 41% (25/61) | 62% (36/58) | **51% (61/119)** |
| T3 Qwen3.5-4B Q3_K_M + RAG PolQA + baza | 34% (21/61) | 52% (30/58) | **43% (51/119)** |
| T1 Gemma QAT t1final + RAG PolQA + baza s42 | 61% (37/61) | 76% (44/58) | **68% (81/119)** |
| T1 Gemma QAT t1final temp 0.6 s42 | 74% (45/61) | 69% (40/58) | **71% (85/119)** |

## C. Porównania przed / po (różnica w punktach procentowych)

### T1: stary prompt vs t1final (s42): T1 Gemma QAT stary prompt s42 → T1 Gemma QAT t1final s42

| kategoria | przed | po | różnica |
|---|---|---|---|
| closed_choice | 100% | 83% | -17 pp |
| closed_match | 67% | 100% | +33 pp |
| closed_tf | 62% | 75% | +12 pp |
| essay | 50% | 50% | +0 pp |
| open: inne | 100% | 100% | +0 pp |
| open: podaj | 79% | 79% | +0 pp |
| open: rozstrzygnij | 79% | 79% | +0 pp |
| open: wyjaśnij/uzasadnij | 92% | 67% | -25 pp |
| 1 starożytność | 100% | 80% | -20 pp |
| 2 średniowiecze | 70% | 90% | +20 pp |
| 3 nowożytność | 75% | 75% | +0 pp |
| 4 XIX w. (1815–1914) | 79% | 86% | +7 pp |
| 5 1914–1945 | 79% | 79% | +0 pp |
| 6 po 1945 | 92% | 75% | -17 pp |
| essay | 50% | 50% | +0 pp |
| Polska | 73% | 76% | +3 pp |
| essay | 50% | 50% | +0 pp |
| powszechna | 97% | 87% | -10 pp |

Zadania lepsze: 8, gorsze: 8.

### T1: t1final vs t1final + kompendium (s42): T1 Gemma QAT t1final s42 → T1 Gemma QAT t1final + kompendium (esej) s42

| kategoria | przed | po | różnica |
|---|---|---|---|
| closed_choice | 83% | 67% | -17 pp |
| closed_match | 100% | 100% | +0 pp |
| closed_tf | 75% | 50% | -25 pp |
| essay | 50% | 47% | -3 pp |
| open: inne | 100% | 100% | +0 pp |
| open: podaj | 79% | 83% | +4 pp |
| open: rozstrzygnij | 79% | 75% | -4 pp |
| open: wyjaśnij/uzasadnij | 67% | 75% | +8 pp |
| 1 starożytność | 80% | 100% | +20 pp |
| 2 średniowiecze | 90% | 90% | +0 pp |
| 3 nowożytność | 75% | 75% | +0 pp |
| 4 XIX w. (1815–1914) | 86% | 79% | -7 pp |
| 5 1914–1945 | 79% | 68% | -11 pp |
| 6 po 1945 | 75% | 67% | -8 pp |
| essay | 50% | 47% | -3 pp |
| Polska | 76% | 69% | -7 pp |
| essay | 50% | 47% | -3 pp |
| powszechna | 87% | 93% | +7 pp |

Zadania lepsze: 7, gorsze: 9.

### T2: LoRA v1 vs LoRA v2 think: T2 PLLuM-12B-base + LoRA v1 → T2 PLLuM + LoRA v2 think

| kategoria | przed | po | różnica |
|---|---|---|---|
| closed_choice | 67% | 50% | -17 pp |
| closed_match | 0% | 83% | +83 pp |
| closed_tf | 88% | 50% | -38 pp |
| essay | 53% | 37% | -17 pp |
| open: inne | 60% | 0% | -60 pp |
| open: podaj | 38% | 46% | +8 pp |
| open: rozstrzygnij | 29% | 25% | -4 pp |
| open: wyjaśnij/uzasadnij | 17% | 33% | +17 pp |
| 1 starożytność | 30% | 50% | +20 pp |
| 2 średniowiecze | 20% | 50% | +30 pp |
| 3 nowożytność | 33% | 46% | +12 pp |
| 4 XIX w. (1815–1914) | 64% | 43% | -21 pp |
| 5 1914–1945 | 32% | 32% | +0 pp |
| 6 po 1945 | 42% | 8% | -33 pp |
| essay | 53% | 37% | -17 pp |
| Polska | 29% | 34% | +5 pp |
| essay | 53% | 37% | -17 pp |
| powszechna | 53% | 47% | -7 pp |

Zadania lepsze: 15, gorsze: 16.

### T2: LoRA v2 answer vs v2 think: T2 PLLuM + LoRA v2 answer → T2 PLLuM + LoRA v2 think

| kategoria | przed | po | różnica |
|---|---|---|---|
| closed_choice | 67% | 50% | -17 pp |
| closed_match | 67% | 83% | +17 pp |
| closed_tf | 75% | 50% | -25 pp |
| essay | 37% | 37% | +0 pp |
| open: inne | 40% | 0% | -40 pp |
| open: podaj | 38% | 46% | +8 pp |
| open: rozstrzygnij | 18% | 25% | +7 pp |
| open: wyjaśnij/uzasadnij | 42% | 33% | -8 pp |
| 1 starożytność | 30% | 50% | +20 pp |
| 2 średniowiecze | 40% | 50% | +10 pp |
| 3 nowożytność | 46% | 46% | +0 pp |
| 4 XIX w. (1815–1914) | 57% | 43% | -14 pp |
| 5 1914–1945 | 26% | 32% | +5 pp |
| 6 po 1945 | 33% | 8% | -25 pp |
| essay | 37% | 37% | +0 pp |
| Polska | 37% | 34% | -3 pp |
| essay | 37% | 37% | +0 pp |
| powszechna | 43% | 47% | +3 pp |

Zadania lepsze: 15, gorsze: 14.

### T3: Q4_K_M vs IQ3_XXS: T3 Qwen3.5-4B Q4_K_M → T3 Qwen3.5-4B IQ3_XXS

| kategoria | przed | po | różnica |
|---|---|---|---|
| closed_choice | 33% | 50% | +17 pp |
| closed_match | 83% | 0% | -83 pp |
| closed_tf | 75% | 75% | +0 pp |
| essay | 17% | 7% | -10 pp |
| open: inne | 100% | 80% | -20 pp |
| open: podaj | 50% | 42% | -8 pp |
| open: rozstrzygnij | 50% | 39% | -11 pp |
| open: wyjaśnij/uzasadnij | 75% | 58% | -17 pp |
| 1 starożytność | 70% | 40% | -30 pp |
| 2 średniowiecze | 60% | 30% | -30 pp |
| 3 nowożytność | 46% | 38% | -8 pp |
| 4 XIX w. (1815–1914) | 79% | 57% | -21 pp |
| 5 1914–1945 | 53% | 53% | +0 pp |
| 6 po 1945 | 67% | 58% | -8 pp |
| essay | 17% | 7% | -10 pp |
| Polska | 49% | 34% | -15 pp |
| essay | 17% | 7% | -10 pp |
| powszechna | 80% | 70% | -10 pp |

Zadania lepsze: 7, gorsze: 20.

### T2: LoRA v1 vs przepis v1 na pełnych danych: T2 PLLuM-12B-base + LoRA v1 → T2 PLLuM + LoRA przepis v1 na pełnych danych (2 epoki)

| kategoria | przed | po | różnica |
|---|---|---|---|
| closed_choice | 67% | 83% | +17 pp |
| closed_match | 0% | 50% | +50 pp |
| closed_tf | 88% | 50% | -38 pp |
| essay | 53% | 27% | -27 pp |
| open: inne | 60% | 80% | +20 pp |
| open: podaj | 38% | 62% | +25 pp |
| open: rozstrzygnij | 29% | 21% | -7 pp |
| open: wyjaśnij/uzasadnij | 17% | 25% | +8 pp |
| 1 starożytność | 30% | 30% | +0 pp |
| 2 średniowiecze | 20% | 50% | +30 pp |
| 3 nowożytność | 33% | 50% | +17 pp |
| 4 XIX w. (1815–1914) | 64% | 57% | -7 pp |
| 5 1914–1945 | 32% | 26% | -5 pp |
| 6 po 1945 | 42% | 58% | +17 pp |
| essay | 53% | 27% | -27 pp |
| Polska | 29% | 44% | +15 pp |
| essay | 53% | 27% | -27 pp |
| powszechna | 53% | 47% | -7 pp |

Zadania lepsze: 14, gorsze: 10.

### T2: LoRA v1 vs v2 pełne dane 2 epoki: T2 PLLuM-12B-base + LoRA v1 → T2 PLLuM + LoRA v2 pełne dane, 2 epoki

| kategoria | przed | po | różnica |
|---|---|---|---|
| closed_choice | 67% | 67% | +0 pp |
| closed_match | 0% | 67% | +67 pp |
| closed_tf | 88% | 75% | -12 pp |
| essay | 53% | 23% | -30 pp |
| open: inne | 60% | 67% | +7 pp |
| open: podaj | 38% | 46% | +8 pp |
| open: rozstrzygnij | 29% | 25% | -4 pp |
| open: wyjaśnij/uzasadnij | 17% | 42% | +25 pp |
| 1 starożytność | 30% | 40% | +10 pp |
| 2 średniowiecze | 20% | 50% | +30 pp |
| 3 nowożytność | 33% | 46% | +12 pp |
| 4 XIX w. (1815–1914) | 64% | 57% | -7 pp |
| 5 1914–1945 | 32% | 40% | +8 pp |
| 6 po 1945 | 42% | 42% | +0 pp |
| essay | 53% | 23% | -30 pp |
| Polska | 29% | 41% | +12 pp |
| essay | 53% | 23% | -30 pp |
| powszechna | 53% | 55% | +2 pp |

Zadania lepsze: 12, gorsze: 9.

### T2: LoRA v1 vs przepis v1 pełne dane + RAG PolQA: T2 PLLuM-12B-base + LoRA v1 → T2 PLLuM + LoRA przepis v1 pełne dane + RAG PolQA + baza

| kategoria | przed | po | różnica |
|---|---|---|---|
| closed_choice | 67% | 83% | +17 pp |
| closed_match | 0% | 67% | +67 pp |
| closed_tf | 88% | 50% | -38 pp |
| essay | 53% | 53% | +0 pp |
| open: inne | 60% | 80% | +20 pp |
| open: podaj | 38% | 62% | +25 pp |
| open: rozstrzygnij | 29% | 32% | +4 pp |
| open: wyjaśnij/uzasadnij | 17% | 50% | +33 pp |
| 1 starożytność | 30% | 60% | +30 pp |
| 2 średniowiecze | 20% | 40% | +20 pp |
| 3 nowożytność | 33% | 71% | +37 pp |
| 4 XIX w. (1815–1914) | 64% | 57% | -7 pp |
| 5 1914–1945 | 32% | 32% | +0 pp |
| 6 po 1945 | 42% | 50% | +8 pp |
| essay | 53% | 53% | +0 pp |
| Polska | 29% | 54% | +25 pp |
| essay | 53% | 53% | +0 pp |
| powszechna | 53% | 50% | -3 pp |

Zadania lepsze: 20, gorsze: 8.

### T3: Q3_K_M vs Q3_K_M + RAG PolQA + baza: T3 Qwen3.5-4B Q3_K_M → T3 Qwen3.5-4B Q3_K_M + RAG PolQA + baza

| kategoria | przed | po | różnica |
|---|---|---|---|
| closed_choice | 50% | 50% | +0 pp |
| closed_match | 33% | 50% | +17 pp |
| closed_tf | 25% | 88% | +62 pp |
| essay | 27% | 10% | -17 pp |
| open: inne | 60% | 80% | +20 pp |
| open: podaj | 58% | 54% | -4 pp |
| open: rozstrzygnij | 64% | 50% | -14 pp |
| open: wyjaśnij/uzasadnij | 67% | 33% | -33 pp |
| 1 starożytność | 90% | 50% | -40 pp |
| 2 średniowiecze | 40% | 50% | +10 pp |
| 3 nowożytność | 46% | 58% | +12 pp |
| 4 XIX w. (1815–1914) | 71% | 79% | +7 pp |
| 5 1914–1945 | 42% | 32% | -11 pp |
| 6 po 1945 | 67% | 58% | -8 pp |
| essay | 27% | 10% | -17 pp |
| Polska | 47% | 51% | +3 pp |
| essay | 27% | 10% | -17 pp |
| powszechna | 73% | 60% | -13 pp |

Zadania lepsze: 16, gorsze: 18.

### T1: t1final vs t1final + RAG PolQA + baza (s42): T1 Gemma QAT t1final s42 → T1 Gemma QAT t1final + RAG PolQA + baza s42

| kategoria | przed | po | różnica |
|---|---|---|---|
| closed_choice | 83% | 83% | +0 pp |
| closed_match | 100% | 83% | -17 pp |
| closed_tf | 75% | 62% | -12 pp |
| essay | 50% | 40% | -10 pp |
| open: inne | 100% | 100% | +0 pp |
| open: podaj | 79% | 88% | +8 pp |
| open: rozstrzygnij | 79% | 71% | -7 pp |
| open: wyjaśnij/uzasadnij | 67% | 67% | +0 pp |
| 1 starożytność | 80% | 80% | +0 pp |
| 2 średniowiecze | 90% | 70% | -20 pp |
| 3 nowożytność | 75% | 83% | +8 pp |
| 4 XIX w. (1815–1914) | 86% | 86% | +0 pp |
| 5 1914–1945 | 79% | 68% | -11 pp |
| 6 po 1945 | 75% | 75% | +0 pp |
| essay | 50% | 40% | -10 pp |
| Polska | 76% | 71% | -5 pp |
| essay | 50% | 40% | -10 pp |
| powszechna | 87% | 90% | +3 pp |

Zadania lepsze: 7, gorsze: 11.

### T3: Q3_K_M temp 1.0 vs 0.6 (s42): T3 Qwen3.5-4B Q3_K_M → T3 Qwen3.5-4B Q3_K_M temp 0.6 s42

| kategoria | przed | po | różnica |
|---|---|---|---|
| closed_choice | 50% | 67% | +17 pp |
| closed_match | 33% | 0% | -33 pp |
| closed_tf | 25% | 50% | +25 pp |
| essay | 27% | 7% | -20 pp |
| open: inne | 60% | 100% | +40 pp |
| open: podaj | 58% | 58% | +0 pp |
| open: rozstrzygnij | 64% | 71% | +7 pp |
| open: wyjaśnij/uzasadnij | 67% | 75% | +8 pp |
| 1 starożytność | 90% | 70% | -20 pp |
| 2 średniowiecze | 40% | 50% | +10 pp |
| 3 nowożytność | 46% | 58% | +12 pp |
| 4 XIX w. (1815–1914) | 71% | 71% | +0 pp |
| 5 1914–1945 | 42% | 53% | +11 pp |
| 6 po 1945 | 67% | 83% | +17 pp |
| essay | 27% | 7% | -20 pp |
| Polska | 47% | 54% | +7 pp |
| essay | 27% | 7% | -20 pp |
| powszechna | 73% | 80% | +7 pp |

Zadania lepsze: 14, gorsze: 10.

### T1: t1final temp 1.0 vs 0.6 (s42): T1 Gemma QAT t1final s42 → T1 Gemma QAT t1final temp 0.6 s42

| kategoria | przed | po | różnica |
|---|---|---|---|
| closed_choice | 83% | 67% | -17 pp |
| closed_match | 100% | 50% | -50 pp |
| closed_tf | 75% | 50% | -25 pp |
| essay | 50% | 70% | +20 pp |
| open: inne | 100% | 100% | +0 pp |
| open: podaj | 79% | 79% | +0 pp |
| open: rozstrzygnij | 79% | 75% | -4 pp |
| open: wyjaśnij/uzasadnij | 67% | 67% | +0 pp |
| 1 starożytność | 80% | 100% | +20 pp |
| 2 średniowiecze | 90% | 60% | -30 pp |
| 3 nowożytność | 75% | 67% | -8 pp |
| 4 XIX w. (1815–1914) | 86% | 86% | +0 pp |
| 5 1914–1945 | 79% | 63% | -16 pp |
| 6 po 1945 | 75% | 67% | -8 pp |
| essay | 50% | 70% | +20 pp |
| Polska | 76% | 63% | -14 pp |
| essay | 50% | 70% | +20 pp |
| powszechna | 87% | 90% | +3 pp |

Zadania lepsze: 5, gorsze: 9.

## D. Myślenie, powtórki i koszt czasu (z debug.jsonl)

| przebieg | zbiór | z myśleniem | mediana znaków myślenia | puste myślenie | powtórki | urwane | tokeny wyjścia | czas [s] |
|---|---|---|---|---|---|---|---|---|
| T1 Gemma QAT t1final s42 | test2024_v2 | 40/40 | 3526 | 0 | 0 | 0 | 58058 | 1822 |
| T1 Gemma QAT t1final s42 | test2025_v2 | 38/38 | 2699 | 0 | 2 | 0 | 64480 | 1933 |
| T1 Gemma QAT t1final s43 | test2024_v2 | 40/40 | 3258 | 0 | 1 | 0 | 79782 | 2365 |
| T1 Gemma QAT t1final s43 | test2025_v2 | 38/38 | 2669 | 0 | 2 | 0 | 68197 | 2160 |
| T1 Gemma QAT stary prompt s42 | test2024_v2 | 40/40 | 3451 | 0 | 2 | 0 | 83363 | 2139 |
| T1 Gemma QAT stary prompt s42 | test2025_v2 | 38/38 | 2922 | 0 | 2 | 0 | 68911 | 2061 |
| T1 Gemma QAT stary prompt s43 | test2024_v2 | 40/40 | 3288 | 0 | 2 | 0 | 77628 | 2517 |
| T1 Gemma QAT stary prompt s43 | test2025_v2 | 38/38 | 2743 | 0 | 1 | 0 | 63391 | 2239 |
| T2 PLLuM-12B-base goły | test2024_v2 | 0/40 | 0 | 0 | 0 | 40 | 83968 | 1891 |
| T2 PLLuM-12B-base goły | test2025_v2 | 0/38 | 0 | 0 | 0 | 38 | 79872 | 1841 |
| T2 PLLuM-12B-base + LoRA v1 | test2024_v2 | 0/40 | 0 | 0 | 0 | 0 | 2303 | 150 |
| T2 PLLuM-12B-base + LoRA v1 | test2025_v2 | 0/38 | 0 | 0 | 0 | 0 | 3307 | 165 |
| T2 Gemma-4-12B pt goła | test2024_v2 | 0/40 | 0 | 0 | 0 | 20 | 40960 | 1314 |
| T2 Gemma-4-12B pt goła | test2025_v2 | 0/38 | 0 | 0 | 0 | 20 | 40960 | 1312 |
| T2 Gemma-4-12B pt + LoRA v1 (scalona) | test2024_v2 | 0/40 | 0 | 0 | 0 | 20 | 40962 | 1682 |
| T2 Gemma-4-12B pt + LoRA v1 (scalona) | test2025_v2 | 0/38 | 0 | 0 | 0 | 20 | 40960 | 1682 |
| T3 Qwen3.5-4B Q4_K_M | test2024_v2 | 39/40 | 9330 | 0 | 8 | 1 | 164409 | 4146 |
| T3 Qwen3.5-4B Q4_K_M | test2025_v2 | 37/38 | 11682 | 0 | 11 | 0 | 166751 | 4183 |
| T3 Qwen3.5-4B IQ3_XXS | test2024_v2 | 39/40 | 23668 | 0 | 22 | 5 | 243571 | 5540 |
| T3 Qwen3.5-4B IQ3_XXS | test2025_v2 | 37/38 | 22908 | 0 | 22 | 2 | 230904 | 5375 |
| T3 Qwen3.5-4B IQ2_M | test2024_v2 | 39/40 | 24827 | 0 | 32 | 5 | 299804 | 5223 |
| T3 Qwen3.5-4B IQ2_M | test2025_v2 | 37/38 | 22912 | 0 | 25 | 3 | 248744 | 4654 |
| T3 Qwen3.5-2B Q4_K_M | test2024_v2 | 39/40 | 15155 | 0 | 14 | 1 | 185874 | 3332 |
| T3 Qwen3.5-2B Q4_K_M | test2025_v2 | 37/38 | 15651 | 0 | 13 | 0 | 174793 | 3150 |
| T3 Qwen3.5-2B Q4_K_M + HyDE | test2024_v2 | 39/40 | 10175 | 0 | 9 | 0 | 168694 | 1653 |
| T3 Qwen3.5-2B Q4_K_M + HyDE | test2025_v2 | 37/38 | 18019 | 0 | 17 | 1 | 206584 | 1890 |
| Bielik-4.5B-v3-Instruct Q4_K_M | test2024_v2 | 0/40 | 0 | 0 | 0 | 0 | 6969 | 168 |
| Bielik-4.5B-v3-Instruct Q4_K_M | test2025_v2 | 0/38 | 0 | 0 | 0 | 1 | 6951 | 168 |
| Bielik-4.5B-v3-Instruct Q3_K_M | test2024_v2 | 0/40 | 0 | 0 | 0 | 14 | 42640 | 685 |
| Bielik-4.5B-v3-Instruct Q3_K_M | test2025_v2 | 0/38 | 0 | 0 | 0 | 5 | 14767 | 301 |
| T1 Gemma QAT t1final + kompendium (esej) s42 | test2024_v2 | 40/40 | 3507 | 0 | 3 | 0 | 81081 | 2374 |
| T1 Gemma QAT t1final + kompendium (esej) s42 | test2025_v2 | 38/38 | 3011 | 0 | 4 | 0 | 87285 | 2435 |
| T1 Gemma QAT t1final + kompendium (esej) s43 | test2024_v2 | 40/40 | 3059 | 0 | 1 | 0 | 63485 | 1991 |
| T1 Gemma QAT t1final + kompendium (esej) s43 | test2025_v2 | 38/38 | 3136 | 0 | 4 | 0 | 82942 | 2294 |
| T2 PLLuM + LoRA v1 + kompendium (esej) | test2024_v2 | 0/40 | 0 | 0 | 0 | 0 | 4274 | 123 |
| T2 PLLuM + LoRA v1 + kompendium (esej) | test2025_v2 | 0/38 | 0 | 0 | 0 | 0 | 2018 | 94 |
| T2 PLLuM + LoRA v1 + kompendium hybryda | test2024_v2 | 0/40 | 0 | 0 | 0 | 0 | 2300 | 99 |
| T2 PLLuM + LoRA v1 + kompendium hybryda | test2025_v2 | 0/38 | 0 | 0 | 0 | 0 | 2340 | 100 |
| T2 PLLuM + LoRA v2 think | test2024_v2 | 0/40 | 0 | 0 | 0 | 0 | 3977 | 190 |
| T2 PLLuM + LoRA v2 think | test2025_v2 | 0/38 | 0 | 0 | 0 | 0 | 2671 | 135 |
| T2 PLLuM + LoRA v2 think + kompendium | test2024_v2 | 0/40 | 0 | 0 | 0 | 0 | 3370 | 230 |
| T2 PLLuM + LoRA v2 think + kompendium | test2025_v2 | 0/38 | 0 | 0 | 0 | 0 | 2732 | 196 |
| T2 PLLuM + LoRA v2 answer | test2024_v2 | 0/40 | 0 | 0 | 0 | 0 | 2457 | 136 |
| T2 PLLuM + LoRA v2 answer | test2025_v2 | 0/38 | 0 | 0 | 0 | 0 | 2305 | 132 |
| T2 PLLuM + LoRA v2 answer + kompendium | test2024_v2 | 0/40 | 0 | 0 | 0 | 0 | 2548 | 161 |
| T2 PLLuM + LoRA v2 answer + kompendium | test2025_v2 | 0/38 | 0 | 0 | 0 | 0 | 2380 | 157 |
| T2 Gemma pt + LoRA v1, tylko tekst (diagnostyka) | test2024_v2 | 0/40 | 0 | 0 | 0 | 0 | 2530 | 92 |
| T3 Qwen3.5-4B IQ4_XS | test2024_v2 | 39/40 | 11393 | 0 | 11 | 0 | 178165 | 4253 |
| T3 Qwen3.5-4B IQ4_XS | test2025_v2 | 37/38 | 14724 | 0 | 9 | 1 | 167918 | 4083 |
| T3 Qwen3.5-4B Q3_K_M | test2024_v2 | 39/40 | 10219 | 0 | 15 | 1 | 184588 | 4373 |
| T3 Qwen3.5-4B Q3_K_M | test2025_v2 | 37/38 | 12808 | 0 | 11 | 0 | 165939 | 4040 |
| T3 Qwen3.5-4B IQ3_XXS + RAG z bazy wiedzy (hybryda) | test2024_v2 | 39/40 | 24072 | 0 | 27 | 2 | 275154 | 3420 |
| T3 Qwen3.5-4B IQ3_XXS + RAG z bazy wiedzy (hybryda) | test2025_v2 | 37/38 | 22951 | 0 | 18 | 2 | 234370 | 3373 |
| T3 Qwen3.5-4B IQ3_XXS, myślenie tylko rozstrzygnij/otwarte | test2024_v2 | 21/40 | 25045 | 0 | 13 | 4 | 142432 | 1982 |
| T3 Qwen3.5-4B IQ3_XXS, myślenie tylko rozstrzygnij/otwarte | test2025_v2 | 18/38 | 21270 | 0 | 8 | 3 | 122913 | 2118 |
| T2 PLLuM + LoRA v2 answer + RAG z bazy wiedzy | test2024_v2 | 0/40 | 0 | 0 | 0 | 1 | 5432 | 415 |
| T2 PLLuM + LoRA v2 answer + RAG z bazy wiedzy | test2025_v2 | 0/38 | 0 | 0 | 0 | 0 | 2414 | 343 |
| T2 PLLuM + LoRA v2 answer + RAG PolQA + baza | test2024_v2 | 0/40 | 0 | 0 | 0 | 0 | 2441 | 389 |
| T2 PLLuM + LoRA v2 answer + RAG PolQA + baza | test2025_v2 | 0/38 | 0 | 0 | 0 | 0 | 2297 | 335 |
| T3 Qwen3.5-4B Q3_K_M s43 | test2024_v2 | 39/40 | 20999 | 0 | 17 | 2 | 224324 | 4923 |
| T3 Qwen3.5-4B Q3_K_M s43 | test2025_v2 | 37/38 | 16453 | 0 | 14 | 0 | 184730 | 4191 |
| T3 Qwen3.5-4B Q3_K_S | test2024_v2 | 39/40 | 23438 | 0 | 27 | 0 | 263304 | 5226 |
| T3 Qwen3.5-4B Q3_K_S | test2025_v2 | 37/38 | 23854 | 0 | 25 | 2 | 244980 | 5027 |
| T2 PLLuM + LoRA v2 pełne dane, 2 epoki | test2024_v2 | 0/40 | 0 | 0 | 0 | 0 | 2664 | 146 |
| T2 PLLuM + LoRA v2 pełne dane, 2 epoki | test2025_v2 | 0/38 | 0 | 0 | 0 | 0 | 2449 | 140 |
| T2 PLLuM + LoRA v2 pełne dane, 2 epoki + RAG z bazy | test2024_v2 | 0/40 | 0 | 0 | 0 | 0 | 2492 | 194 |
| T2 PLLuM + LoRA v2 pełne dane, 2 epoki + RAG z bazy | test2025_v2 | 0/38 | 0 | 0 | 0 | 0 | 2410 | 188 |
| T2 PLLuM + LoRA przepis v1 na pełnych danych (2 epoki) | test2024_v2 | 0/40 | 0 | 0 | 0 | 0 | 2630 | 569 |
| T2 PLLuM + LoRA przepis v1 na pełnych danych (2 epoki) | test2025_v2 | 0/38 | 0 | 0 | 0 | 0 | 2330 | 518 |
| T2 PLLuM + LoRA przepis v1 pełne dane + RAG PolQA + baza | test2024_v2 | 0/40 | 0 | 0 | 0 | 0 | 2439 | 580 |
| T2 PLLuM + LoRA przepis v1 pełne dane + RAG PolQA + baza | test2025_v2 | 0/38 | 0 | 0 | 0 | 0 | 2461 | 549 |
| T2 PLLuM + LoRA v2 pełne dane 2 ep. + RAG PolQA + baza | test2024_v2 | 0/40 | 0 | 0 | 0 | 0 | 2591 | 193 |
| T2 PLLuM + LoRA v2 pełne dane 2 ep. + RAG PolQA + baza | test2025_v2 | 0/38 | 0 | 0 | 0 | 0 | 2471 | 186 |
| T2 PLLuM + LoRA v2 answer + RAG PolQA + baza, bramka BM25 >= 12 | test2024_v2 | 0/40 | 0 | 0 | 0 | 0 | 2391 | 485 |
| T2 PLLuM + LoRA v2 answer + RAG PolQA + baza, bramka BM25 >= 12 | test2025_v2 | 0/38 | 0 | 0 | 0 | 0 | 2509 | 486 |
| T3 Qwen3.5-4B Q4_K_M s43 | test2024_v2 | 39/40 | 18631 | 0 | 12 | 0 | 202698 | 4783 |
| T3 Qwen3.5-4B Q4_K_M s43 | test2025_v2 | 37/38 | 15981 | 0 | 7 | 1 | 182874 | 4520 |
| T3 Qwen3.5-4B Q3_K_M s44 | test2024_v2 | 39/40 | 15525 | 0 | 16 | 0 | 188894 | 6270 |
| T3 Qwen3.5-4B Q3_K_M s44 | test2025_v2 | 37/38 | 18635 | 0 | 12 | 0 | 192885 | 6125 |
| T3 Qwen3.5-4B Q3_K_M temp 0.6 s42 | test2024_v2 | 39/40 | 7755 | 0 | 12 | 0 | 160287 | 4059 |
| T3 Qwen3.5-4B Q3_K_M temp 0.6 s42 | test2025_v2 | 37/38 | 15570 | 0 | 15 | 0 | 181111 | 4484 |
| T3 Qwen3.5-4B Q3_K_M temp 0.6 s43 | test2024_v2 | 39/40 | 8378 | 0 | 10 | 0 | 155430 | 5755 |
| T3 Qwen3.5-4B Q3_K_M temp 0.6 s43 | test2025_v2 | 37/38 | 17442 | 0 | 13 | 0 | 181251 | 5913 |
| T3 Qwen3.5-4B Q3_K_M + RAG PolQA + baza | test2024_v2 | 39/40 | 8259 | 0 | 12 | 1 | 170946 | 7174 |
| T3 Qwen3.5-4B Q3_K_M + RAG PolQA + baza | test2025_v2 | 37/38 | 14258 | 0 | 12 | 0 | 185820 | 7683 |
| T1 Gemma QAT t1final + RAG PolQA + baza s42 | test2024_v2 | 40/40 | 3156 | 0 | 0 | 0 | 60617 | 3002 |
| T1 Gemma QAT t1final + RAG PolQA + baza s42 | test2025_v2 | 38/38 | 2939 | 0 | 3 | 0 | 68765 | 3267 |
| T1 Gemma QAT t1final temp 0.6 s42 | test2024_v2 | 40/40 | 3211 | 0 | 3 | 0 | 63882 | 1664 |
| T1 Gemma QAT t1final temp 0.6 s42 | test2025_v2 | 38/38 | 2668 | 0 | 2 | 0 | 72060 | 1796 |

## E. Dane SFT v2 (10479 przykładów)

- **origin:** synthetic 10064, essay 297, real 118
- **task:** solve 9829, hyde 500, topic_number 150
- **kind:** rozstrz 2007, open 1806, podaj 1615, closed_match 1231, closed_tf 1008, closed_choice 990, essay 827, hyde 500, closed_multi 495
- **epoch:** nowożytność 2598, 1914–1945 1495, XIX w. 1408, średniowiecze 1142, starożytność 1001, po 1945 904, 3 nowożytność 432, 5 1914–1945 397, 2 średniowiecze 277, ? nieokreślona 266, 4 XIX w. (1815–1914) 225, 6 po 1945 217, 1 starożytność 117
- **scope:** Polska 6670, powszechna 3809
- **rag_mode:** none 10479
- **has_rationale:** True 7951, False 2528
