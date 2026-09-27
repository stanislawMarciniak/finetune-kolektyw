# 08 — Wyniki według typu zadania i zagadnienia (tabele generowane)

Wygenerowane przez `eval/analyze.py`. Komórka = procent punktów (zdobyte/maksymalne). Otwarte i eseje: tylko przebiegi oceniane przez `gpt-6-luna`. Zamknięte: ocena automatyczna, więc także stare przebiegi. Zadanie 2024/21 (odrzucone przez filtr treści sędziego) pominięte.

## Skład arkuszy 2024 + 2025 (punkty)

- **typ:** closed_choice 6, closed_match 6, closed_tf 8, essay 30, open: inne 6, open: podaj 24, open: rozstrzygnij 28, open: wyjaśnij/uzasadnij 12
- **epoka:** 1 starożytność 10, 2 średniowiecze 10, 3 nowożytność 24, 4 XIX w. (1815–1914) 14, 5 1914–1945 20, 6 po 1945 12, essay 30
- **zakres:** Polska 59, essay 30, powszechna 31

## A. Arkusze 2024 + 2025, przebiegi oceniane lunką

### Typ zadania

| przebieg | closed_choice | closed_match | closed_tf | essay | open: inne | open: podaj | open: rozstrzygnij | open: wyjaśnij/uzasadnij | razem |
|---|---|---|---|---|---|---|---|---|---|
| T1 Gemma-4-12B QAT, stara konfiguracja (myślenie) | 83% (5/6) | 83% (5/6) | 50% (4/8) | 63% (19/30) | 100% (5/5) | 88% (21/24) | 89% (25/28) | 67% (8/12) | **77% (92/119)** |
| T1 Gemma-4-12B QAT, t1final (myślenie) | 83% (5/6) | 67% (4/6) | 50% (4/8) | 50% (15/30) | 100% (5/5) | 79% (19/24) | 79% (22/28) | 67% (8/12) | **69% (82/119)** |
| T2 PLLuM-12B-base + LoRA | 50% (3/6) | 17% (1/6) | 88% (7/8) | 37% (11/30) | 40% (2/5) | 33% (8/24) | 29% (8/28) | 42% (5/12) | **38% (45/119)** |
| T2 PLLuM-12B-base + LoRA, poprawka eseju | 50% (3/6) | 17% (1/6) | 88% (7/8) | 40% (12/30) | 60% (3/5) | 33% (8/24) | 25% (7/28) | 33% (4/12) | **38% (45/119)** |
| T2 PLLuM-12B-base + LoRA + HyDE | 67% (4/6) | 17% (1/6) | 88% (7/8) | 40% (12/30) | 20% (1/5) | 33% (8/24) | 25% (7/28) | 25% (3/12) | **36% (43/119)** |
| T3 Qwen3.5-4B Q4 myślenie | 100% (3/3) | 100% (1/1) | 75% (3/4) | 13% (2/15) | 100% (3/3) | 50% (6/12) | 50% (7/14) | 57% (4/7) | **49% (29/59)** |
| T3 Qwen3.5-4B Q4 myślenie + powtórka | 67% (4/6) | 50% (3/6) | 75% (6/8) | 13% (4/30) | 100% (5/5) | 50% (12/24) | 61% (17/28) | 50% (6/12) | **48% (57/119)** |
| T3 Qwen3.5-4B Q4 myślenie + HyDE | 67% (2/3) | 0% (0/1) | 50% (2/4) | 7% (1/15) | 100% (3/3) | 58% (7/12) | 57% (8/14) | 29% (2/7) | **42% (25/59)** |
| Qwen3.5-2B Q4 | 33% (2/6) | 0% (0/6) | 50% (4/8) | 0% (0/30) | 60% (3/5) | 12% (3/24) | 29% (8/28) | 8% (1/12) | **18% (21/119)** |
| Qwen3.5-2B Q4 + HyDE (podaj) | 50% (3/6) | 0% (0/6) | 75% (6/8) | 3% (1/30) | 80% (4/5) | 21% (5/24) | 21% (6/28) | 25% (3/12) | **24% (28/119)** |
| Qwen3.5-2B Q4 + LoRA | 67% (4/6) | 0% (0/6) | 75% (6/8) | 7% (2/30) | 40% (2/5) | 17% (4/24) | 25% (7/28) | 17% (2/12) | **23% (27/119)** |
| Bielik-1.5B Q8 | 50% (3/6) | 0% (0/6) | 38% (3/8) | 7% (2/30) | 20% (1/5) | 29% (7/24) | 18% (5/28) | 8% (1/12) | **18% (22/119)** |
| Bielik-1.5B Q8 + HyDE | 50% (3/6) | 17% (1/6) | 38% (3/8) | 10% (3/30) | 60% (3/5) | 46% (11/24) | 18% (5/28) | 25% (3/12) | **27% (32/119)** |
| Bielik-1.5B Q4 + LoRA | 50% (3/6) | 50% (3/6) | 38% (3/8) | 13% (4/30) | 33% (2/6) | 21% (5/24) | 7% (2/28) | 17% (2/12) | **20% (24/120)** |

### Epoka (z dat w poleceniu i źródłach grupy; esej osobno)

| przebieg | 1 starożytność | 2 średniowiecze | 3 nowożytność | 4 XIX w. (1815–1914) | 5 1914–1945 | 6 po 1945 | essay | razem |
|---|---|---|---|---|---|---|---|---|
| T1 Gemma-4-12B QAT, stara konfiguracja (myślenie) | 100% (10/10) | 80% (8/10) | 83% (20/24) | 79% (11/14) | 79% (15/19) | 75% (9/12) | 63% (19/30) | **77% (92/119)** |
| T1 Gemma-4-12B QAT, t1final (myślenie) | 100% (10/10) | 80% (8/10) | 75% (18/24) | 71% (10/14) | 63% (12/19) | 75% (9/12) | 50% (15/30) | **69% (82/119)** |
| T2 PLLuM-12B-base + LoRA | 40% (4/10) | 20% (2/10) | 29% (7/24) | 64% (9/14) | 42% (8/19) | 33% (4/12) | 37% (11/30) | **38% (45/119)** |
| T2 PLLuM-12B-base + LoRA, poprawka eseju | 20% (2/10) | 20% (2/10) | 29% (7/24) | 64% (9/14) | 42% (8/19) | 42% (5/12) | 40% (12/30) | **38% (45/119)** |
| T2 PLLuM-12B-base + LoRA + HyDE | 40% (4/10) | 20% (2/10) | 42% (10/24) | 50% (7/14) | 26% (5/19) | 25% (3/12) | 40% (12/30) | **36% (43/119)** |
| T3 Qwen3.5-4B Q4 myślenie | 60% (3/5) | 80% (4/5) | 58% (7/12) | 83% (5/6) | 57% (4/7) | 44% (4/9) | 13% (2/15) | **49% (29/59)** |
| T3 Qwen3.5-4B Q4 myślenie + powtórka | 80% (8/10) | 50% (5/10) | 42% (10/24) | 79% (11/14) | 58% (11/19) | 67% (8/12) | 13% (4/30) | **48% (57/119)** |
| T3 Qwen3.5-4B Q4 myślenie + HyDE | 40% (2/5) | 40% (2/5) | 58% (7/12) | 83% (5/6) | 43% (3/7) | 56% (5/9) | 7% (1/15) | **42% (25/59)** |
| Qwen3.5-2B Q4 | 20% (2/10) | 10% (1/10) | 21% (5/24) | 43% (6/14) | 21% (4/19) | 25% (3/12) | 0% (0/30) | **18% (21/119)** |
| Qwen3.5-2B Q4 + HyDE (podaj) | 40% (4/10) | 30% (3/10) | 21% (5/24) | 43% (6/14) | 26% (5/19) | 33% (4/12) | 3% (1/30) | **24% (28/119)** |
| Qwen3.5-2B Q4 + LoRA | 10% (1/10) | 30% (3/10) | 21% (5/24) | 43% (6/14) | 37% (7/19) | 25% (3/12) | 7% (2/30) | **23% (27/119)** |
| Bielik-1.5B Q8 | 30% (3/10) | 0% (0/10) | 25% (6/24) | 43% (6/14) | 16% (3/19) | 17% (2/12) | 7% (2/30) | **18% (22/119)** |
| Bielik-1.5B Q8 + HyDE | 40% (4/10) | 0% (0/10) | 33% (8/24) | 57% (8/14) | 32% (6/19) | 25% (3/12) | 10% (3/30) | **27% (32/119)** |
| Bielik-1.5B Q4 + LoRA | 30% (3/10) | 20% (2/10) | 21% (5/24) | 36% (5/14) | 10% (2/20) | 25% (3/12) | 13% (4/30) | **20% (24/120)** |

### Historia Polski vs powszechna

| przebieg | Polska | essay | powszechna | razem |
|---|---|---|---|---|
| T1 Gemma-4-12B QAT, stara konfiguracja (myślenie) | 75% (44/59) | 63% (19/30) | 97% (29/30) | **77% (92/119)** |
| T1 Gemma-4-12B QAT, t1final (myślenie) | 66% (39/59) | 50% (15/30) | 93% (28/30) | **69% (82/119)** |
| T2 PLLuM-12B-base + LoRA | 25% (15/59) | 37% (11/30) | 63% (19/30) | **38% (45/119)** |
| T2 PLLuM-12B-base + LoRA, poprawka eseju | 27% (16/59) | 40% (12/30) | 57% (17/30) | **38% (45/119)** |
| T2 PLLuM-12B-base + LoRA + HyDE | 31% (18/59) | 40% (12/30) | 43% (13/30) | **36% (43/119)** |
| T3 Qwen3.5-4B Q4 myślenie | 48% (15/31) | 13% (2/15) | 92% (12/13) | **49% (29/59)** |
| T3 Qwen3.5-4B Q4 myślenie + powtórka | 44% (26/59) | 13% (4/30) | 90% (27/30) | **48% (57/119)** |
| T3 Qwen3.5-4B Q4 myślenie + HyDE | 45% (14/31) | 7% (1/15) | 77% (10/13) | **42% (25/59)** |
| Qwen3.5-2B Q4 | 22% (13/59) | 0% (0/30) | 27% (8/30) | **18% (21/119)** |
| Qwen3.5-2B Q4 + HyDE (podaj) | 27% (16/59) | 3% (1/30) | 37% (11/30) | **24% (28/119)** |
| Qwen3.5-2B Q4 + LoRA | 25% (15/59) | 7% (2/30) | 33% (10/30) | **23% (27/119)** |
| Bielik-1.5B Q8 | 17% (10/59) | 7% (2/30) | 33% (10/30) | **18% (22/119)** |
| Bielik-1.5B Q8 + HyDE | 32% (19/59) | 10% (3/30) | 33% (10/30) | **27% (32/119)** |
| Bielik-1.5B Q4 + LoRA | 22% (13/59) | 13% (4/30) | 23% (7/31) | **20% (24/120)** |

### Zadanie z obrazem (True) vs bez (False)

| przebieg | bez obrazu | z obrazem | razem |
|---|---|---|---|
| T1 Gemma-4-12B QAT, stara konfiguracja (myślenie) | 77% (47/61) | 78% (45/58) | **77% (92/119)** |
| T1 Gemma-4-12B QAT, t1final (myślenie) | 66% (40/61) | 72% (42/58) | **69% (82/119)** |
| T2 PLLuM-12B-base + LoRA | 39% (24/61) | 36% (21/58) | **38% (45/119)** |
| T2 PLLuM-12B-base + LoRA, poprawka eseju | 43% (26/61) | 33% (19/58) | **38% (45/119)** |
| T2 PLLuM-12B-base + LoRA + HyDE | 41% (25/61) | 31% (18/58) | **36% (43/119)** |
| T3 Qwen3.5-4B Q4 myślenie | 31% (8/26) | 64% (21/33) | **49% (29/59)** |
| T3 Qwen3.5-4B Q4 myślenie + powtórka | 38% (23/61) | 59% (34/58) | **48% (57/119)** |
| T3 Qwen3.5-4B Q4 myślenie + HyDE | 27% (7/26) | 55% (18/33) | **42% (25/59)** |
| Qwen3.5-2B Q4 | 16% (10/61) | 19% (11/58) | **18% (21/119)** |
| Qwen3.5-2B Q4 + HyDE (podaj) | 25% (15/61) | 22% (13/58) | **24% (28/119)** |
| Qwen3.5-2B Q4 + LoRA | 15% (9/61) | 31% (18/58) | **23% (27/119)** |
| Bielik-1.5B Q8 | 13% (8/61) | 24% (14/58) | **18% (22/119)** |
| Bielik-1.5B Q8 + HyDE | 26% (16/61) | 28% (16/58) | **27% (32/119)** |
| Bielik-1.5B Q4 + LoRA | 21% (13/61) | 19% (11/59) | **20% (24/120)** |

## B. T1 na wszystkich arkuszach (2024, 2025, 2026, mock 2023)

### Typ zadania

| przebieg | closed_choice | closed_match | closed_tf | essay | open: inne | open: podaj | open: rozstrzygnij | open: wyjaśnij/uzasadnij | razem |
|---|---|---|---|---|---|---|---|---|---|
| T1 Gemma-4-12B QAT, stara konfiguracja (myślenie) | 85% (11/13) | 70% (7/10) | 72% (13/18) | 67% (40/60) | 81% (13/16) | 86% (37/43) | 79% (42/53) | 77% (20/26) | **77% (183/239)** |
| T1 Gemma-4-12B QAT, t1final (myślenie) | 85% (11/13) | 70% (7/10) | 72% (13/18) | 53% (32/60) | 81% (13/16) | 86% (37/43) | 72% (38/53) | 81% (21/26) | **72% (172/239)** |

### Epoka

| przebieg | 1 starożytność | 2 średniowiecze | 3 nowożytność | 4 XIX w. (1815–1914) | 5 1914–1945 | 6 po 1945 | ? nieokreślona | essay | razem |
|---|---|---|---|---|---|---|---|---|---|
| T1 Gemma-4-12B QAT, stara konfiguracja (myślenie) | 100% (20/20) | 86% (19/22) | 77% (36/47) | 78% (21/27) | 74% (26/35) | 74% (20/27) | 100% (1/1) | 67% (40/60) | **77% (183/239)** |
| T1 Gemma-4-12B QAT, t1final (myślenie) | 95% (19/20) | 82% (18/22) | 74% (35/47) | 78% (21/27) | 71% (25/35) | 78% (21/27) | 100% (1/1) | 53% (32/60) | **72% (172/239)** |

## C. Zamknięte (ocena automatyczna), 2024 + 2025 — także stare przebiegi i gołe bazy

### Zamknięte według typu

| przebieg | closed_choice | closed_match | closed_tf | razem |
|---|---|---|---|---|
| Gemma-4-12B QAT myślenie (Modal) | 83% (5/6) | 83% (5/6) | 50% (4/8) | **70% (14/20)** |
| Bielik-11B-v3 Q5 | 100% (6/6) | 67% (4/6) | 75% (6/8) | **80% (16/20)** |
| Bielik-PL-11B Q5 | 100% (6/6) | 50% (2/4) | 75% (6/8) | **78% (14/18)** |
| Qwen3.5-9B Q5 | 83% (5/6) | 83% (5/6) | 75% (6/8) | **80% (16/20)** |
| Qwen3.5-4B Q4 bez myślenia | 67% (4/6) | 33% (2/6) | 38% (3/8) | **45% (9/20)** |
| Qwen3.5-4B Q4 myślenie (Modal) | 50% (3/6) | 67% (4/6) | 50% (4/8) | **55% (11/20)** |
| Qwen3.5-2B Q4 (Modal) | 50% (3/6) | 33% (2/6) | 50% (4/8) | **45% (9/20)** |
| Bielik-1.5B Q8 (Modal) | 50% (3/6) | 17% (1/6) | 62% (5/8) | **45% (9/20)** |
| Bielik-11B-Base (goły) | 83% (5/6) | 50% (2/4) | 50% (4/8) | **61% (11/18)** |
| Bielik-4.5B-Base (goły) | 40% (2/5) | 50% (2/4) | 38% (3/8) | **41% (7/17)** |
| Gemma-4-12B pt (goły) | 67% (4/6) | 50% (2/4) | 88% (7/8) | **72% (13/18)** |
| T1 Gemma-4-12B QAT, stara konfiguracja (myślenie) | 83% (5/6) | 83% (5/6) | 50% (4/8) | **70% (14/20)** |
| T1 Gemma-4-12B QAT, t1final (myślenie) | 83% (5/6) | 67% (4/6) | 50% (4/8) | **65% (13/20)** |
| T2 PLLuM-12B-base + LoRA | 50% (3/6) | 17% (1/6) | 88% (7/8) | **55% (11/20)** |
| T2 PLLuM-12B-base + LoRA, poprawka eseju | 50% (3/6) | 17% (1/6) | 88% (7/8) | **55% (11/20)** |
| T2 PLLuM-12B-base + LoRA + HyDE | 67% (4/6) | 17% (1/6) | 88% (7/8) | **60% (12/20)** |
| T3 Qwen3.5-4B Q4 myślenie | 100% (3/3) | 100% (1/1) | 75% (3/4) | **88% (7/8)** |
| T3 Qwen3.5-4B Q4 myślenie + powtórka | 67% (4/6) | 50% (3/6) | 75% (6/8) | **65% (13/20)** |
| T3 Qwen3.5-4B Q4 myślenie + HyDE | 67% (2/3) | 0% (0/1) | 50% (2/4) | **50% (4/8)** |
| Qwen3.5-2B Q4 | 33% (2/6) | 0% (0/6) | 50% (4/8) | **30% (6/20)** |
| Qwen3.5-2B Q4 + HyDE (podaj) | 50% (3/6) | 0% (0/6) | 75% (6/8) | **45% (9/20)** |
| Qwen3.5-2B Q4 + LoRA | 67% (4/6) | 0% (0/6) | 75% (6/8) | **50% (10/20)** |
| Bielik-1.5B Q8 | 50% (3/6) | 0% (0/6) | 38% (3/8) | **30% (6/20)** |
| Bielik-1.5B Q8 + HyDE | 50% (3/6) | 17% (1/6) | 38% (3/8) | **35% (7/20)** |
| Bielik-1.5B Q4 + LoRA | 50% (3/6) | 50% (3/6) | 38% (3/8) | **45% (9/20)** |

## D. Wpływ myślenia na zamknięte (te same modele, ocena automatyczna)

| zbiór | model | bez myślenia | z myśleniem |
|---|---|---|---|
| dev2023_text | Gemma-4-12B QAT | 55% (6/11) | 64% (7/11) |
| dev2023_text | Qwen3.5-4B Q4 | 45% (5/11) | 64% (7/11) |
| dev2023_text | Qwen3.5-2B Q4 | 55% (6/11) | 0% (0/11) |
| test2024_split | Qwen3.5-4B Q4 | 38% (3/8) | 50% (4/8) |
| test2025_split | Qwen3.5-4B Q4 | 50% (6/12) | 58% (7/12) |

## E. Najtrudniejsze zadania 2024 + 2025 (średni odsetek punktów w przebiegach T1–T3 ocenianych lunką)

| zbiór | zadanie | typ | epoka | obraz | średnio |
|---|---|---|---|---|---|
| 2024 | 14.1 | open: rozstrzygnij | 3 nowożytność | tak | 0% |
| 2024 | 19.2 | open: podaj | 5 1914–1945 | tak | 0% |
| 2024 | 25 | open: wyjaśnij/uzasadnij | 6 po 1945 | tak | 0% |
| 2024 | 7 | open: rozstrzygnij | 2 średniowiecze | nie | 0% |
| 2025 | 14.1 | open: rozstrzygnij | 4 XIX w. (1815–1914) | tak | 0% |
| 2025 | 9.3 | open: podaj | 3 nowożytność | nie | 0% |
| 2024 | 11.1 | closed_match | 3 nowożytność | tak | 25% |
| 2024 | 12.1 | open: podaj | 3 nowożytność | tak | 25% |
| 2024 | 19.1 | closed_tf | 5 1914–1945 | tak | 25% |
| 2024 | 8.1 | open: podaj | 3 nowożytność | tak | 25% |
| 2025 | 21.1 | open: podaj | 5 1914–1945 | tak | 25% |
| 2025 | 22 | open: rozstrzygnij | 5 1914–1945 | nie | 25% |
| 2025 | 5.1 | closed_match | 2 średniowiecze | nie | 25% |
| 2025 | 7.1 | open: rozstrzygnij | 3 nowożytność | tak | 25% |
| 2025 | 25 | essay | essay | nie | 30% |
| 2025 | 19 | open: podaj | 5 1914–1945 | nie | 38% |
| 2024 | 10 | closed_choice | 3 nowożytność | tak | 50% |
| 2024 | 11.2 | open: wyjaśnij/uzasadnij | 3 nowożytność | tak | 50% |
| 2024 | 12.2 | open: podaj | 3 nowożytność | tak | 50% |
| 2024 | 12.3 | open: rozstrzygnij | 3 nowożytność | tak | 50% |

Przebiegi do średniej: gemma4-12b-qat__s42L, gemma4-qat-t1final, pllum-12b-base-sft__fix, q35-4b-q4-think-fb__none. Pełne dane per zadanie: `results/item_scores.csv`.
