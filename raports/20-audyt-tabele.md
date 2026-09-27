# 20 — Audyt odpowiedzi: pełne tabele (wygenerowane `python3 eval/audit.py --out raports/20-audyt-tabele.md`, stan finałów z nd 27.09 ~10:10: T3 = S4K-T64K; sekcja H = poprzedni stan vs finał, I = statystyki esejów)

## A. Wyniki grup (średnia z seedów, sędzia luna)

| grupa | opis | rola | 2024+2025 | 2026 | seedy |
|---|---|---|---|---|---|
| T1-final | T1 finał: Gemma-4-12B QAT + --rozstrz-hint + esej --essay-mode rubric --essay-rubric-fixed (krótkie: fx-t1rh 3 seedy; esej: ek22F, 5 seedów/arkusz) | final | 71.5% | 84.1% | 2024×8, 2025×8, 2026×8 |
| T1-before | T1 stan z audytu 07:00: t1final (3 seedy) + eseje bazowe tych samych 5 seedów co ek22 | ref | 70.6% | 80.5% | 2024×8, 2025×8, 2026×7 |
| T1-rozstrz-hint | składnik finału: --rozstrz-hint (tylko zadania krótkie) | near | 79.4% | 88.1% | 2024×3, 2025×3, 2026×3 |
| T1-t1final | t1final bez eseju | ref | 78.3% | 85.6% | 2024×3, 2025×3, 2026×2 |
| T1-essay-rubric | składnik finału: esej rubric-fixed (ek22F), tylko esej | near | 48.0% | 72.0% | 2024×5, 2025×5, 2026×5 |
| T1-essay-base | eseje bazowe (te same seedy i tematy) | ref | 48.0% | 65.3% | 2024×5, 2025×5, 2026×5 |
| T1-essay-rubric-kb | odrzucone: rubric-fixed + --essay-refine-kb v1 (ek22FK), tylko esej | rejected | 54.0% | 72.0% | 2024×5, 2025×5, 2026×5 |
| T1-img1120 | T1 --image-min-tokens 1120 (2 seedy) | rejected | 73.5% | 80.0% | 2024×2, 2025×2, 2026×2 |
| T1-essay-refine-kb | T1 --essay-refine-kb v1 (tylko esej) | rejected | 73.1% | 81.7% | 2024×2, 2025×2, 2026×1 |
| T1-essay-refine-kb3 | T1 --essay-refine-kb v3 (tylko esej) | rejected | 75.2% | 80.0% | 2024×2, 2025×2, 2026×1 |
| T1-t1final-full | t1final pełne przebiegi (3 seedy) | ref | 70.3% | 84.2% | 2024×3, 2025×3, 2026×2 |
| T1-tiles | odrzucone: --image-tiles (2 seedy, tylko zadania z obrazem) | rejected | 71.8% | 81.7% | 2024×2, 2025×2, 2026×2 |
| T2-final | T2 finał: PLLuM+LoRA+RAG --fill-fields --ocr + caption 0.8B | final | 56.7% | 52.5% | 2024×2, 2025×2, 2026×2 |
| T2-fill-fields | T2 poprzedni finał (--fill-fields, bez pomocy obrazowej) | ref | 48.3% | 50.0% | 2024×2, 2025×2, 2026×2 |
| T2-ocr-only | T2 --fill-fields --ocr (bez caption) | rejected | 51.3% | 48.3% | 2024×2, 2025×2, 2026×2 |
| T2-caption-only | T2 --fill-fields + caption (bez OCR) | rejected | 57.1% | 46.7% | 2024×2, 2025×2, 2026×2 |
| T2-old | T2 finał z 01:00 (bez --fill-fields; 3 przebiegi tej samej konfiguracji) | ref | 52.4% | 47.8% | 2024×3, 2025×3, 2026×3 |
| T2-nt2ocr | T2 --ocr, pełny przebieg (raport 10) | rejected | 49.6% | — | 2024×1, 2025×1 |
| T2-hyde | T2 --rag hyde | rejected | 51.3% | — | 2024×1, 2025×1 |
| T2-kbk2 | T2 --kb-rag-k 2 | rejected | 53.8% | — | 2024×1, 2025×1 |
| T2-kbk3 | T2 --kb-rag-k 3 | rejected | 56.3% | — | 2024×1, 2025×1 |
| T3-final | T3 finał: Qwen3.5-4B IQ2_M-PL-E4K-MIX-S4K-T64K 1.44 GB + esej structured + --think-retry --match-retry (2 seedy) | final | 41.6% | 45.0% | 2024×2, 2025×2, 2026×2 |
| T3-V124K | T3 finał z 09:40: …-S4K-V124K 1.53 GB (3 seedy, bez retry) | ref | 41.2% | 42.8% | 2024×3, 2025×3, 2026×3 |
| T3-MIX | T3 stan z audytu 07:00: IQ2_M-PL-E4K-MIX 1.75 GB | ref | 42.9% | 45.8% | 2024×2, 2025×2, 2026×2 |
| T3-retry | składnik finału: --think-retry --match-retry (na MIX, scalone, seedy sparowane) | near | 43.3% | 45.0% | 2024×2, 2025×1, 2026×1 |
| T3-T40K | odrzucone: słownik przycięty do 40k (1.40 GB), z retry | rejected | 36.1% | 45.0% | 2024×2, 2025×2, 2026×2 |
| T3-prev-iq3xxs | T3 poprzedni: UD-IQ3_XXS 1.95 GB + limit 5000 (esej stary) | rejected | 44.3% | 42.5% | 2024×3, 2025×3, 2026×2 |
| T3-e4k | T3 IQ3_XXS-PL-E4K 1.87 GB (esej stary) | rejected | 42.0% | 50.0% | 2024×1, 2025×1, 2026×1 |
| T1-t1final-full@T1-essay-refine-kb | T1-t1final-full (seedy sparowane z T1-essay-refine-kb) | ref | 71.0% | 83.3% | 2024×2, 2025×2, 2026×1 |
| T1-t1final-full@T1-essay-refine-kb3 | T1-t1final-full (seedy sparowane z T1-essay-refine-kb3) | ref | 71.0% | 83.3% | 2024×2, 2025×2, 2026×1 |
| T1-t1final-full@T1-tiles | T1-t1final-full (seedy sparowane z T1-tiles) | ref | 71.0% | 84.2% | 2024×2, 2025×2, 2026×2 |
| T3-MIX@T3-retry | T3-MIX (seedy sparowane z T3-retry) | ref | 42.9% | 45.0% | 2024×2, 2025×1, 2026×1 |
| T3-V124K@T3-T40K | T3-V124K (seedy sparowane z T3-T40K) | ref | 40.8% | 42.5% | 2024×2, 2025×2, 2026×2 |

## B. Finały — strata wg: typ zadania (pkt; 2024+2025 = 119 pkt, 2026 = 60 pkt)

| kategoria | max 24+25 | T1-final 24+25 | T2-final 24+25 | T3-final 24+25 | T1-final 2026 | T2-final 2026 | T3-final 2026 |
|---|---|---|---|---|---|---|---|
| closed_choice | 6 | 0.7 | 1.0 | 1.5 | 0 | 3.0 | 0.5 |
| closed_tf | 8 | 2.0 | 4.0 | 1.5 | 0 | 2.0 | 1.0 |
| closed_match | 6 | 2.3 | 2.0 | 5.0 | 0 | 2.0 | 1.5 |
| podaj | 24 | 4.7 | 3.5 | 14.0 | 0 | 2.5 | 4.0 |
| rozstrz | 28 | 5.0 | 18.0 | 14.0 | 4.3 | 9.5 | 9.5 |
| wyjasnij | 17 | 3.7 | 6.0 | 5.5 | 1.0 | 3.5 | 2.5 |
| essay | 30 | 15.6 | 17.0 | 28.0 | 4.2 | 6.0 | 14.0 |
| **razem** |  | 33.9 | 51.5 | 69.5 | 9.5 | 28.5 | 33.0 |

## B. Finały — strata wg: epoka (pkt; 2024+2025 = 119 pkt, 2026 = 60 pkt)

| kategoria | max 24+25 | T1-final 24+25 | T2-final 24+25 | T3-final 24+25 | T1-final 2026 | T2-final 2026 | T3-final 2026 |
|---|---|---|---|---|---|---|---|
| staro | 10 | 0.3 | 3.5 | 3.0 | 0 | 3.0 | 1.0 |
| sred | 14 | 2.7 | 5.5 | 8.5 | 1.3 | 2.5 | 3.5 |
| nowo | 17 | 3.7 | 4.0 | 10.5 | 1.0 | 4.5 | 2.5 |
| xix | 17 | 3.7 | 5.5 | 5.0 | 1.0 | 3.5 | 3.5 |
| 1914-39 | 17 | 4.0 | 9.5 | 9.5 | 1.0 | 4.5 | 4.0 |
| iiws | 4 | 0.7 | 1.0 | 2.0 | 0 | 0 | 0.5 |
| 1945-89 | 10 | 3.3 | 5.5 | 3.0 | 1.0 | 4.5 | 4.0 |
| 1914-39 (esej) | 15 | 0 | 0 | 14.0 | 0 | 0 | 0 |
| sred (esej) | 30 | 15.6 | 17.0 | 0 | 0 | 6.0 | 0 |
| xix (esej) | 15 | 0 | 0 | 14.0 | 4.2 | 0 | 0 |
| iiws (esej) | 0 | 0 | 0 | 0 | 0 | 0 | 14.0 |
| **razem** |  | 33.9 | 51.5 | 69.5 | 9.5 | 28.5 | 33.0 |

## B. Finały — strata wg: rodzaj błędu (pkt; 2024+2025 = 119 pkt, 2026 = 60 pkt)

| kategoria | T1-final 24+25 | T2-final 24+25 | T3-final 24+25 | T1-final 2026 | T2-final 2026 | T3-final 2026 |
|---|---|---|---|---|---|---|
| wiedza/fakt | 4.7 | 7.5 | 19.0 | 1.0 | 4.0 | 7.5 |
| źle odczytany obraz | 8.3 | 15.0 | 9.0 | 2.7 | 7.5 | 6.5 |
| źle odczytany tekst źródła | 0.7 | 4.0 | 4.0 | 1.3 | 3.5 | 4.0 |
| polecenie/format | 0 | 1.0 | 0 | 0 | 1.0 | 0 |
| odpowiedź niepełna | 0 | 1.0 | 2.5 | 0 | 1.0 | 0 |
| rozumowanie/logika | 0.7 | 6.0 | 5.0 | 0 | 5.5 | 1.0 |
| harness (fallback/urwanie/błąd) | 2.3 | 0 | 1.0 | 0.3 | 0 | 0 |
| sędzia/grader za surowy (tylko ewaluacja) | 1.7 | 0 | 1.0 | 0 | 0 | 0 |
| esej A: aspekty (powierzchowne/brak) | 10.6 | 13.0 | 18.3 | 3.0 | 5.0 | 9.2 |
| esej A: błędy merytoryczne | 5.0 | 4.0 | 5.8 | 1.2 | 1.0 | 2.9 |
| esej B: spójność/długość | 0 | 0 | 3.9 | 0 | 0 | 1.9 |
| **razem** | 33.9 | 51.5 | 69.5 | 9.5 | 28.5 | 33.0 |

## B. Finały — strata wg: obraz (pkt; 2024+2025 = 119 pkt, 2026 = 60 pkt)

| kategoria | max 24+25 | T1-final 24+25 | T2-final 24+25 | T3-final 24+25 | T1-final 2026 | T2-final 2026 | T3-final 2026 |
|---|---|---|---|---|---|---|---|
| art | 9 | 1.0 | 3.0 | 5.5 | 0 | 0 | 0 |
| artefact | 5 | 1.3 | 4.0 | 2.5 | 1.7 | 6.0 | 3.0 |
| brak obrazu | 61 | 22.6 | 25.0 | 43.5 | 5.5 | 10.0 | 20.0 |
| cartoon | 12 | 3.7 | 6.5 | 4.0 | 1.0 | 6.0 | 5.0 |
| chart | 1 | 0.7 | 0 | 0.5 | 0 | 0 | 0 |
| map | 12 | 3.0 | 5.0 | 5.5 | 1.3 | 5.0 | 3.5 |
| photo | 11 | 1.0 | 3.0 | 4.5 | 0 | 0 | 0 |
| poster | 4 | 0.3 | 2.5 | 1.0 | 0 | 0.5 | 0 |
| press | 4 | 0.3 | 2.5 | 2.5 | 0 | 1.0 | 1.5 |
| **razem** |  | 33.9 | 51.5 | 69.5 | 9.5 | 28.5 | 33.0 |

## B. Finały — strata wg: rodzaj źródła (pkt; 2024+2025 = 119 pkt, 2026 = 60 pkt)

| kategoria | max 24+25 | T1-final 24+25 | T2-final 24+25 | T3-final 24+25 | T1-final 2026 | T2-final 2026 | T3-final 2026 |
|---|---|---|---|---|---|---|---|
| bez źródła | 32 | 16.6 | 17.0 | 30.0 | 4.2 | 6.0 | 14.5 |
| obraz | 27 | 7.3 | 14.0 | 10.5 | 1.0 | 7.0 | 3.0 |
| tekst | 29 | 6.0 | 8.0 | 13.5 | 1.3 | 4.0 | 5.5 |
| tekst+obraz | 31 | 4.0 | 12.5 | 15.5 | 3.0 | 11.5 | 10.0 |
| **razem** |  | 33.9 | 51.5 | 69.5 | 9.5 | 28.5 | 33.0 |

## C. Typ × epoka — strata finałów razem (pkt, 3 arkusze, suma T1+T2+T3)

| typ \ epoka | staro | sred | nowo | xix | 1914-39 | iiws | 1945-89 | razem |
|---|---|---|---|---|---|---|---|---|
| closed_choice | 1.0 | 0.5 | 3.2 | 1.0 | 1.0 | 0 | 0 | 6.7 |
| closed_tf | 1.0 | 0 | 1.0 | 2.5 | 6.0 | 0 | 0 | 10.5 |
| closed_match | 0 | 6.3 | 6.0 | 0 | 0 | 0.5 | 0 | 12.8 |
| podaj | 1.8 | 4.0 | 6.5 | 1.5 | 10.8 | 1.0 | 3.0 | 28.7 |
| rozstrz | 7.0 | 11.2 | 8.0 | 16.2 | 10.0 | 2.7 | 5.3 | 60.3 |
| wyjasnij | 0 | 2.0 | 1.5 | 1.0 | 4.7 | 0 | 13.0 | 22.2 |
| essay | 0 | 38.6 | 0 | 18.2 | 14.0 | 14.0 | 0 | 84.8 |
| **razem** | 10.8 | 62.6 | 26.2 | 40.4 | 46.5 | 18.2 | 21.3 | 226.0 |

## D. T1-final: rodzaj błędu × typ zadania (pkt, 3 arkusze)

| błąd \ typ | closed_choice | closed_tf | closed_match | podaj | rozstrz | wyjasnij | essay | razem |
|---|---|---|---|---|---|---|---|---|
| wiedza/fakt | 0.7 | 0 | 1.0 | 2.0 | 2.0 | 0 | 0 | 5.7 |
| źle odczytany obraz | 0 | 1.7 | 0 | 1.3 | 3.3 | 4.7 | 0 | 11.0 |
| źle odczytany tekst źródła | 0 | 0.3 | 0 | 0 | 1.7 | 0 | 0 | 2.0 |
| rozumowanie/logika | 0 | 0 | 0 | 0 | 0.7 | 0 | 0 | 0.7 |
| harness (fallback/urwanie/błąd) | 0 | 0 | 0 | 1.0 | 1.7 | 0 | 0 | 2.7 |
| sędzia/grader za surowy (tylko ewaluacja) | 0 | 0 | 1.3 | 0.3 | 0 | 0 | 0 | 1.7 |
| esej A: aspekty (powierzchowne/brak) | 0 | 0 | 0 | 0 | 0 | 0 | 13.6 | 13.6 |
| esej A: błędy merytoryczne | 0 | 0 | 0 | 0 | 0 | 0 | 6.2 | 6.2 |

## D. T2-final: rodzaj błędu × typ zadania (pkt, 3 arkusze)

| błąd \ typ | closed_choice | closed_tf | closed_match | podaj | rozstrz | wyjasnij | essay | razem |
|---|---|---|---|---|---|---|---|---|
| wiedza/fakt | 2.0 | 1.0 | 1.0 | 4.5 | 3.0 | 0 | 0 | 11.5 |
| źle odczytany obraz | 1.0 | 3.0 | 2.0 | 0 | 10.0 | 6.5 | 0 | 22.5 |
| źle odczytany tekst źródła | 1.0 | 1.0 | 0 | 0.5 | 5.0 | 0 | 0 | 7.5 |
| polecenie/format | 0 | 1.0 | 1.0 | 0 | 0 | 0 | 0 | 2.0 |
| odpowiedź niepełna | 0 | 0 | 0 | 1.0 | 1.0 | 0 | 0 | 2.0 |
| rozumowanie/logika | 0 | 0 | 0 | 0 | 8.5 | 3.0 | 0 | 11.5 |
| esej A: aspekty (powierzchowne/brak) | 0 | 0 | 0 | 0 | 0 | 0 | 18.0 | 18.0 |
| esej A: błędy merytoryczne | 0 | 0 | 0 | 0 | 0 | 0 | 5.0 | 5.0 |

## D. T3-final: rodzaj błędu × typ zadania (pkt, 3 arkusze)

| błąd \ typ | closed_choice | closed_tf | closed_match | podaj | rozstrz | wyjasnij | essay | razem |
|---|---|---|---|---|---|---|---|---|
| wiedza/fakt | 2.0 | 2.5 | 5.5 | 14.5 | 1.5 | 0.5 | 0 | 26.5 |
| źle odczytany obraz | 0 | 0 | 0 | 1.0 | 10.0 | 4.5 | 0 | 15.5 |
| źle odczytany tekst źródła | 0 | 0 | 0 | 0.5 | 7.5 | 0 | 0 | 8.0 |
| odpowiedź niepełna | 0 | 0 | 0 | 1.5 | 0 | 1.0 | 0 | 2.5 |
| rozumowanie/logika | 0 | 0 | 0 | 0 | 4.0 | 2.0 | 0 | 6.0 |
| harness (fallback/urwanie/błąd) | 0 | 0 | 0 | 0.5 | 0.5 | 0 | 0 | 1.0 |
| sędzia/grader za surowy (tylko ewaluacja) | 0 | 0 | 1.0 | 0 | 0 | 0 | 0 | 1.0 |
| esej A: aspekty (powierzchowne/brak) | 0 | 0 | 0 | 0 | 0 | 0 | 27.5 | 27.5 |
| esej A: błędy merytoryczne | 0 | 0 | 0 | 0 | 0 | 0 | 8.7 | 8.7 |
| esej B: spójność/długość | 0 | 0 | 0 | 0 | 0 | 0 | 5.8 | 5.8 |

## E. Zadania trudne dla wszystkich finałów (średnio ≤ 34% punktów w każdym)

| zadanie | typ | epoka | obraz | max | T1-final śr. pkt (błąd) | T2-final śr. pkt (błąd) | T3-final śr. pkt (błąd) |
|---|---|---|---|---|---|---|---|
| 2024/7 | rozstrz | sred | brak obrazu | 1 | 0 (harness) | 0 (wiedza) | 0 (wiedza) |
| 2024/11.1 | closed_match | nowo | art | 1 | 0.33 (wiedza) | 0 (wiedza) | 0 (wiedza) |
| 2024/14.1 | rozstrz | xix | map | 1 | 0 (obraz) | 0 (obraz) | 0 (obraz) |
| 2024/19.2 | podaj | 1914-39 | artefact | 1 | 0.33 (obraz) | 0 (wiedza) | 0 (wiedza) |
| 2025/14.1 | rozstrz | xix | map | 1 | 0 (harness) | 0 (obraz) | 0 (obraz) |
| 2025/22 | rozstrz | iiws | brak obrazu | 1 | 0.33 (wiedza) | 0 (wiedza) | 0 (tekst) |
| 2026/12.2 | rozstrz | nowo | map | 1 | 0 (obraz) | 0 (tekst) | 0 (obraz) |

## F. Rozbieżności między finałami (różnica ≥ 67 pp udziału punktów)

| zadanie | typ | epoka | obraz | udział pkt | rozwiązuje | nie rozwiązuje (błąd) |
|---|---|---|---|---|---|---|
| 2024/1 | rozstrz | staro | photo | T1=100% T2=0% T3=0% | T1-final | T2-final: obraz; T3-final: obraz |
| 2024/5.1 | rozstrz | sred | map | T1=100% T2=0% T3=0% | T1-final | T2-final: obraz; T3-final: obraz |
| 2024/8.1 | podaj | nowo | art | T1=67% T2=100% T3=0% | T2-final | T3-final: wiedza |
| 2024/9 | rozstrz | nowo | art | T1=100% T2=0% T3=50% | T1-final | T2-final: rozumowanie |
| 2024/11.2 | wyjasnij | nowo | art | T1=100% T2=100% T3=0% | T1-final, T2-final | T3-final: rozumowanie |
| 2024/12.1 | podaj | nowo | photo | T1=33% T2=100% T3=0% | T2-final | T1-final: obraz; T3-final: wiedza |
| 2024/17.1 | wyjasnij | xix | cartoon | T1=100% T2=100% T3=0% | T1-final, T2-final | T3-final: rozumowanie |
| 2024/18 | rozstrz | 1914-39 | poster | T1=100% T2=0% T3=100% | T1-final, T3-final | T2-final: rozumowanie |
| 2024/22.1 | podaj | iiws | brak obrazu | T1=100% T2=100% T3=0% | T1-final, T2-final | T3-final: wiedza |
| 2024/23.2 | rozstrz | 1945-89 | poster | T1=67% T2=0% T3=100% | T3-final | T2-final: obraz |
| 2024/24 | rozstrz | 1945-89 | map | T1=100% T2=0% T3=50% | T1-final | T2-final: obraz |
| 2025/2 | rozstrz | staro | brak obrazu | T1=100% T2=0% T3=100% | T1-final, T3-final | T2-final: niepelna |
| 2025/4 | closed_match | sred | brak obrazu | T1=50% T2=100% T3=0% | T2-final | T3-final: sedzia |
| 2025/7.1 | rozstrz | sred | map | T1=100% T2=100% T3=0% | T1-final, T2-final | T3-final: rozumowanie |
| 2025/9.2 | podaj | nowo | brak obrazu | T1=100% T2=100% T3=0% | T1-final, T2-final | T3-final: wiedza |
| 2025/9.3 | podaj | nowo | brak obrazu | T1=0% T2=100% T3=0% | T2-final | T1-final: wiedza; T3-final: wiedza |
| 2025/10 | closed_tf | nowo | artefact | T1=100% T2=0% T3=100% | T1-final, T3-final | T2-final: obraz |
| 2025/11.2 | rozstrz | nowo | brak obrazu | T1=100% T2=0% T3=0% | T1-final | T2-final: rozumowanie; T3-final: tekst |
| 2025/15.2 | rozstrz | xix | brak obrazu | T1=67% T2=0% T3=100% | T3-final | T2-final: tekst |
| 2025/16.2 | rozstrz | xix | press | T1=100% T2=0% T3=100% | T1-final, T3-final | T2-final: rozumowanie |
| 2025/17.2 | closed_choice | 1914-39 | cartoon | T1=100% T2=0% T3=100% | T1-final, T3-final | T2-final: wiedza |
| 2025/19 | podaj | 1914-39 | brak obrazu | T1=33% T2=100% T3=0% | T2-final | T1-final: wiedza; T3-final: wiedza |
| 2025/21.2 | rozstrz | 1914-39 | press | T1=100% T2=50% T3=0% | T1-final | T3-final: wiedza |
| 2025/23 | podaj | 1945-89 | art | T1=100% T2=100% T3=0% | T1-final, T2-final | T3-final: niepelna |
| 2026/2 | closed_tf | staro | brak obrazu | T1=100% T2=0% T3=100% | T1-final, T3-final | T2-final: polecenie |
| 2026/3.1 | rozstrz | staro | map | T1=100% T2=0% T3=50% | T1-final | T2-final: rozumowanie |
| 2026/3.2 | closed_choice | staro | map | T1=100% T2=0% T3=100% | T1-final, T3-final | T2-final: wiedza |
| 2026/5.1 | podaj | sred | brak obrazu | T1=100% T2=0% T3=100% | T1-final, T3-final | T2-final: niepelna |
| 2026/6.1 | closed_match | sred | brak obrazu | T1=100% T2=100% T3=0% | T1-final, T2-final | T3-final: wiedza |
| 2026/6.2 | rozstrz | sred | brak obrazu | T1=0% T2=100% T3=0% | T2-final | T1-final: wiedza; T3-final: tekst |
| 2026/10.1 | closed_choice | nowo | brak obrazu | T1=100% T2=0% T3=50% | T1-final | T2-final: tekst |
| 2026/13 | closed_match | nowo | artefact | T1=100% T2=0% T3=100% | T1-final, T3-final | T2-final: obraz |
| 2026/14.3 | closed_tf | xix | artefact | T1=100% T2=0% T3=50% | T1-final | T2-final: wiedza |
| 2026/15.2 | closed_choice | xix | cartoon | T1=100% T2=0% T3=100% | T1-final, T3-final | T2-final: obraz |
| 2026/17 | rozstrz | xix | brak obrazu | T1=67% T2=100% T3=0% | T2-final | T3-final: tekst |
| 2026/18.1 | podaj | 1914-39 | artefact | T1=100% T2=0% T3=0% | T1-final | T2-final: wiedza; T3-final: wiedza |
| 2026/19.1 | rozstrz | 1914-39 | press | T1=100% T2=0% T3=0% | T1-final | T2-final: tekst; T3-final: tekst |
| 2026/20 | rozstrz | 1914-39 | cartoon | T1=100% T2=25% T3=50% | T1-final | T2-final: rozumowanie |
| 2026/22 | rozstrz | 1945-89 | brak obrazu | T1=100% T2=0% T3=50% | T1-final | T2-final: wiedza |
| 2026/23.2 | podaj | 1945-89 | cartoon | T1=100% T2=100% T3=0% | T1-final, T2-final | T3-final: wiedza |

## I. Eseje — statystyki ocen (wszystkie próbki grupy, 3 arkusze)

| grupa | esejów | śr. pkt /15 | śr. A przed odjęciem /12 | śr. błędów | śr. odjęcie | śr. B /3 | elementy b / z / p / brak |
|---|---|---|---|---|---|---|---|
| T1-final | 15 | 8.40 | 7.47 | 3.87 | 2.07 | 3.00 | 12 / 15 / 18 / 0 |
| T1-before | 15 | 8.07 | 6.40 | 2.27 | 1.27 | 2.93 | 4 / 21 / 20 / 0 |
| T1-essay-rubric | 15 | 8.40 | 7.47 | 3.87 | 2.07 | 3.00 | 12 / 15 / 18 / 0 |
| T1-essay-base | 15 | 8.07 | 6.40 | 2.27 | 1.27 | 2.93 | 4 / 21 / 20 / 0 |
| T1-essay-rubric-kb | 15 | 9.00 | 7.87 | 3.60 | 1.87 | 3.00 | 10 / 22 / 13 / 0 |
| T1-img1120 | 6 | 9.17 | 7.50 | 2.50 | 1.33 | 3.00 | 3 / 9 / 6 / 0 |
| T1-essay-refine-kb | 5 | 9.00 | 7.20 | 1.60 | 1.00 | 2.80 | 2 / 7 / 6 / 0 |
| T1-essay-refine-kb3 | 5 | 9.80 | 7.80 | 1.40 | 0.80 | 2.80 | 4 / 6 / 5 / 0 |
| T1-t1final-full | 8 | 8.25 | 6.62 | 2.12 | 1.25 | 2.88 | 2 / 12 / 10 / 0 |
| T1-tiles | 6 | 8.83 | 7.00 | 1.83 | 1.00 | 2.83 | 1 / 11 / 6 / 0 |
| T2-final | 6 | 7.33 | 6.00 | 3.33 | 1.67 | 3.00 | 0 / 10 / 8 / 0 |
| T2-fill-fields | 6 | 7.33 | 6.00 | 3.33 | 1.67 | 3.00 | 0 / 10 / 8 / 0 |
| T2-ocr-only | 6 | 7.33 | 6.00 | 3.33 | 1.67 | 3.00 | 0 / 10 / 8 / 0 |
| T2-caption-only | 6 | 7.33 | 6.00 | 3.33 | 1.67 | 3.00 | 0 / 10 / 8 / 0 |
| T2-old | 9 | 7.56 | 6.33 | 3.00 | 1.67 | 2.89 | 1 / 14 / 12 / 0 |
| T2-nt2ocr | 2 | 5.50 | 5.00 | 3.50 | 2.00 | 2.50 | 0 / 3 / 1 / 2 |
| T2-hyde | 2 | 6.50 | 5.50 | 4.00 | 2.00 | 3.00 | 0 / 3 / 2 / 1 |
| T2-kbk2 | 2 | 8.00 | 7.00 | 3.50 | 2.00 | 3.00 | 0 / 4 / 2 / 0 |
| T2-kbk3 | 2 | 9.50 | 7.00 | 1.00 | 0.50 | 3.00 | 0 / 4 / 2 / 0 |
| T3-final | 6 | 1.00 | 2.50 | 8.67 | 3.00 | 1.00 | 0 / 0 / 15 / 3 |
| T3-V124K | 9 | 1.22 | 2.44 | 6.89 | 2.67 | 0.89 | 0 / 0 / 22 / 5 |
| T3-MIX | 6 | 0.50 | 2.00 | 7.33 | 2.50 | 0.50 | 0 / 0 / 12 / 6 |
| T3-retry | 4 | 0.50 | 1.75 | 7.25 | 2.25 | 0.50 | 0 / 0 / 7 / 5 |
| T3-T40K | 6 | 0.83 | 2.50 | 7.67 | 3.00 | 0.83 | 0 / 0 / 15 / 3 |
| T3-prev-iq3xxs | 8 | 1.38 | 2.75 | 5.75 | 2.62 | 0.88 | 0 / 1 / 20 / 3 |
| T3-e4k | 3 | 1.00 | 2.67 | 5.00 | 2.33 | 0.67 | 0 / 0 / 8 / 1 |
| T1-t1final-full@T1-essay-refine-kb | 5 | 8.20 | 6.60 | 2.20 | 1.20 | 2.80 | 1 / 8 / 6 / 0 |
| T1-t1final-full@T1-essay-refine-kb3 | 5 | 8.20 | 6.60 | 2.20 | 1.20 | 2.80 | 1 / 8 / 6 / 0 |
| T1-t1final-full@T1-tiles | 6 | 8.83 | 7.00 | 1.83 | 1.00 | 2.83 | 1 / 11 / 6 / 0 |
| T3-MIX@T3-retry | 4 | 0.50 | 1.75 | 7.25 | 2.25 | 0.50 | 0 / 0 / 7 / 5 |
| T3-V124K@T3-T40K | 6 | 1.17 | 2.33 | 6.00 | 2.67 | 0.83 | 0 / 0 / 14 / 4 |

## H. Poprzedni stan vs obecny finał — strata (pkt), wg typu, epoki i błędu

### T1-final (przed: T1-before)

Wg: typ zadania

| kategoria | przed 24+25 | finał 24+25 | Δ | przed 2026 | finał 2026 | Δ |
|---|---|---|---|---|---|---|
| closed_choice | 0.7 | 0.7 | +0.0 | 0 | 0 | +0.0 |
| closed_tf | 2.0 | 2.0 | +0.0 | 0 | 0 | +0.0 |
| closed_match | 2.3 | 2.3 | +0.0 | 0 | 0 | +0.0 |
| podaj | 4.7 | 4.7 | +0.0 | 0 | 0 | +0.0 |
| rozstrz | 6.0 | 5.0 | -1.0 | 5.5 | 4.3 | -1.2 |
| wyjasnij | 3.7 | 3.7 | +0.0 | 1.0 | 1.0 | +0.0 |
| essay | 15.6 | 15.6 | +0.0 | 5.2 | 4.2 | -1.0 |
| **razem** | 34.9 | 33.9 | -1.0 | 11.7 | 9.5 | -2.2 |

Wg: epoka

| kategoria | przed 24+25 | finał 24+25 | Δ | przed 2026 | finał 2026 | Δ |
|---|---|---|---|---|---|---|
| staro | 1.0 | 0.3 | -0.7 | 0 | 0 | +0.0 |
| sred | 3.3 | 2.7 | -0.7 | 1.0 | 1.3 | +0.3 |
| nowo | 3.7 | 3.7 | +0.0 | 1.0 | 1.0 | +0.0 |
| xix | 3.3 | 3.7 | +0.3 | 1.5 | 1.0 | -0.5 |
| 1914-39 | 4.0 | 4.0 | +0.0 | 2.0 | 1.0 | -1.0 |
| iiws | 0.7 | 0.7 | +0.0 | 0 | 0 | +0.0 |
| 1945-89 | 3.3 | 3.3 | +0.0 | 1.0 | 1.0 | +0.0 |
| sred (esej) | 15.6 | 15.6 | +0.0 | 0 | 0 | +0.0 |
| xix (esej) | 0 | 0 | +0.0 | 5.2 | 4.2 | -1.0 |
| **razem** | 34.9 | 33.9 | -1.0 | 11.7 | 9.5 | -2.2 |

Wg: rodzaj błędu

| kategoria | przed 24+25 | finał 24+25 | Δ | przed 2026 | finał 2026 | Δ |
|---|---|---|---|---|---|---|
| wiedza/fakt | 5.3 | 4.7 | -0.7 | 1.0 | 1.0 | +0.0 |
| źle odczytany obraz | 10.0 | 8.3 | -1.7 | 2.5 | 2.7 | +0.2 |
| źle odczytany tekst źródła | 0.7 | 0.7 | +0.0 | 3.0 | 1.3 | -1.7 |
| rozumowanie/logika | 0 | 0.7 | +0.7 | 0 | 0 | +0.0 |
| harness (fallback/urwanie/błąd) | 1.3 | 2.3 | +1.0 | 0 | 0.3 | +0.3 |
| sędzia/grader za surowy (tylko ewaluacja) | 2.0 | 1.7 | -0.3 | 0 | 0 | +0.0 |
| esej A: aspekty (powierzchowne/brak) | 12.2 | 10.6 | -1.6 | 4.6 | 3.0 | -1.6 |
| esej A: błędy merytoryczne | 3.2 | 5.0 | +1.8 | 0.6 | 1.2 | +0.6 |
| esej B: spójność/długość | 0.2 | 0 | -0.2 | 0 | 0 | +0.0 |
| **razem** | 34.9 | 33.9 | -1.0 | 11.7 | 9.5 | -2.2 |

### T2-final (przed: T2-old)

Wg: typ zadania

| kategoria | przed 24+25 | finał 24+25 | Δ | przed 2026 | finał 2026 | Δ |
|---|---|---|---|---|---|---|
| closed_choice | 1.0 | 1.0 | +0.0 | 3.0 | 3.0 | +0.0 |
| closed_tf | 4.0 | 4.0 | +0.0 | 2.0 | 2.0 | +0.0 |
| closed_match | 2.0 | 2.0 | +0.0 | 2.0 | 2.0 | +0.0 |
| podaj | 8.3 | 3.5 | -4.8 | 4.0 | 2.5 | -1.5 |
| rozstrz | 19.0 | 18.0 | -1.0 | 9.0 | 9.5 | +0.5 |
| wyjasnij | 8.3 | 6.0 | -2.3 | 3.0 | 3.5 | +0.5 |
| essay | 14.0 | 17.0 | +3.0 | 8.3 | 6.0 | -2.3 |
| **razem** | 56.7 | 51.5 | -5.2 | 31.3 | 28.5 | -2.8 |

Wg: epoka

| kategoria | przed 24+25 | finał 24+25 | Δ | przed 2026 | finał 2026 | Δ |
|---|---|---|---|---|---|---|
| staro | 4.0 | 3.5 | -0.5 | 4.0 | 3.0 | -1.0 |
| sred | 6.7 | 5.5 | -1.2 | 3.0 | 2.5 | -0.5 |
| nowo | 4.3 | 4.0 | -0.3 | 4.0 | 4.5 | +0.5 |
| xix | 8.0 | 5.5 | -2.5 | 3.0 | 3.5 | +0.5 |
| 1914-39 | 11.7 | 9.5 | -2.2 | 4.0 | 4.5 | +0.5 |
| iiws | 1.3 | 1.0 | -0.3 | 0 | 0 | +0.0 |
| 1945-89 | 6.7 | 5.5 | -1.2 | 5.0 | 4.5 | -0.5 |
| sred (esej) | 14.0 | 17.0 | +3.0 | 8.3 | 6.0 | -2.3 |
| **razem** | 56.7 | 51.5 | -5.2 | 31.3 | 28.5 | -2.8 |

Wg: rodzaj błędu

| kategoria | przed 24+25 | finał 24+25 | Δ | przed 2026 | finał 2026 | Δ |
|---|---|---|---|---|---|---|
| wiedza/fakt | 10.3 | 7.5 | -2.8 | 6.0 | 4.0 | -2.0 |
| źle odczytany obraz | 15.3 | 15.0 | -0.3 | 8.7 | 7.5 | -1.2 |
| źle odczytany tekst źródła | 4.3 | 4.0 | -0.3 | 3.7 | 3.5 | -0.2 |
| polecenie/format | 2.0 | 1.0 | -1.0 | 1.0 | 1.0 | +0.0 |
| odpowiedź niepełna | 3.0 | 1.0 | -2.0 | 1.0 | 1.0 | +0.0 |
| rozumowanie/logika | 7.7 | 6.0 | -1.7 | 2.7 | 5.5 | +2.8 |
| esej A: aspekty (powierzchowne/brak) | 10.7 | 13.0 | +2.3 | 6.3 | 5.0 | -1.3 |
| esej A: błędy merytoryczne | 3.3 | 4.0 | +0.7 | 1.7 | 1.0 | -0.7 |
| esej B: spójność/długość | 0 | 0 | +0.0 | 0.3 | 0 | -0.3 |
| **razem** | 56.7 | 51.5 | -5.2 | 31.3 | 28.5 | -2.8 |

### T3-final (przed: T3-V124K)

Wg: typ zadania

| kategoria | przed 24+25 | finał 24+25 | Δ | przed 2026 | finał 2026 | Δ |
|---|---|---|---|---|---|---|
| closed_choice | 2.3 | 1.5 | -0.8 | 0.3 | 0.5 | +0.2 |
| closed_tf | 3.0 | 1.5 | -1.5 | 1.3 | 1.0 | -0.3 |
| closed_match | 4.0 | 5.0 | +1.0 | 2.0 | 1.5 | -0.5 |
| podaj | 14.0 | 14.0 | -0.0 | 4.7 | 4.0 | -0.7 |
| rozstrz | 14.0 | 14.0 | +0.0 | 10.0 | 9.5 | -0.5 |
| wyjasnij | 5.3 | 5.5 | +0.2 | 2.0 | 2.5 | +0.5 |
| essay | 27.3 | 28.0 | +0.7 | 14.0 | 14.0 | +0.0 |
| **razem** | 70.0 | 69.5 | -0.5 | 34.3 | 33.0 | -1.3 |

Wg: epoka

| kategoria | przed 24+25 | finał 24+25 | Δ | przed 2026 | finał 2026 | Δ |
|---|---|---|---|---|---|---|
| staro | 3.3 | 3.0 | -0.3 | 1.3 | 1.0 | -0.3 |
| sred | 9.0 | 8.5 | -0.5 | 3.7 | 3.5 | -0.2 |
| nowo | 10.7 | 10.5 | -0.2 | 2.3 | 2.5 | +0.2 |
| xix | 5.7 | 5.0 | -0.7 | 4.7 | 3.5 | -1.2 |
| 1914-39 | 9.7 | 9.5 | -0.2 | 4.0 | 4.0 | -0.0 |
| iiws | 2.0 | 2.0 | +0.0 | 0.7 | 0.5 | -0.2 |
| 1945-89 | 2.3 | 3.0 | +0.7 | 3.7 | 4.0 | +0.3 |
| 1914-39 (esej) | 14.0 | 14.0 | +0.0 | 0 | 0 | +0.0 |
| 1945-89 (esej) | 13.3 | 0 | -13.3 | 0 | 0 | +0.0 |
| xix (esej) | 0 | 14.0 | +14.0 | 0 | 0 | +0.0 |
| iiws (esej) | 0 | 0 | +0.0 | 14.0 | 14.0 | +0.0 |
| **razem** | 70.0 | 69.5 | -0.5 | 34.3 | 33.0 | -1.3 |

Wg: rodzaj błędu

| kategoria | przed 24+25 | finał 24+25 | Δ | przed 2026 | finał 2026 | Δ |
|---|---|---|---|---|---|---|
| wiedza/fakt | 21.3 | 19.0 | -2.3 | 7.7 | 7.5 | -0.2 |
| źle odczytany obraz | 7.0 | 9.0 | +2.0 | 3.0 | 6.5 | +3.5 |
| źle odczytany tekst źródła | 3.7 | 4.0 | +0.3 | 3.3 | 4.0 | +0.7 |
| polecenie/format | 0.3 | 0 | -0.3 | 0 | 0 | +0.0 |
| odpowiedź niepełna | 0.3 | 2.5 | +2.2 | 0.3 | 0 | -0.3 |
| rozumowanie/logika | 6.0 | 5.0 | -1.0 | 3.3 | 1.0 | -2.3 |
| harness (fallback/urwanie/błąd) | 3.0 | 1.0 | -2.0 | 2.7 | 0 | -2.7 |
| sędzia/grader za surowy (tylko ewaluacja) | 1.0 | 1.0 | +0.0 | 0 | 0 | +0.0 |
| esej A: aspekty (powierzchowne/brak) | 18.3 | 18.3 | -0.0 | 9.2 | 9.2 | -0.1 |
| esej A: błędy merytoryczne | 5.1 | 5.8 | +0.7 | 2.5 | 2.9 | +0.4 |
| esej B: spójność/długość | 3.9 | 3.9 | +0.0 | 2.2 | 1.9 | -0.3 |
| **razem** | 70.0 | 69.5 | -0.5 | 34.3 | 33.0 | -1.3 |

## G. Warianty bliskie najlepszym vs odniesienie (Δ pkt = średnia wariantu − średnia odniesienia, te same zadania)

### T1-rozstrz-hint vs T1-t1final — składnik finału: --rozstrz-hint (tylko zadania krótkie)

- Δ 2024+2025: **+1.00 pkt (+1.1 pp)**
  (w tym esej +0.00 pkt; bez eseju +1.00); 2024: +1.33; 2025: -0.33; 2026: +1.17
- zadania lepsze / gorsze: 5 / 4 (suma +3.33 / -1.17 pkt)
- bootstrap po zadaniach (2024+2025, tylko szum zadań, bez szumu seedów): 95% CI [-1.0, +3.3] pkt
- wg type: rozstrz: +2.17
- wg epoch: 1914-39: +1.00, staro: +0.67, sred: +0.33, xix: +0.17
- wg img: True: +2.17
- największe zmiany: 2026/19.1 +1.00, 2024/5.1 +0.67, 2024/1 +0.67, 2026/17 +0.67, 2025/7.1 +0.33, 2025/15.2 -0.33, 2025/5.2 -0.33, 2026/4.1 -0.33, 2026/14.2 -0.17

### T1-essay-rubric vs T1-essay-base — składnik finału: esej rubric-fixed (ek22F), tylko esej

- Δ 2024+2025: **-0.00 pkt (-0.0 pp)**
  (w tym esej -0.00 pkt; bez eseju +0.00); 2024: +0.80; 2025: -0.80; 2026: +1.00
- zadania lepsze / gorsze: 2 / 1 (suma +1.80 / -0.80 pkt)
- bootstrap po zadaniach (2024+2025, tylko szum zadań, bez szumu seedów): 95% CI [-1.6, +1.6] pkt
- wg type: essay: +1.00
- wg epoch: esej: +1.00
- wg img: False: +1.00
- największe zmiany: 2026/26 +1.00, 2024/26 +0.80, 2025/25 -0.80

### T1-essay-rubric-kb vs T1-essay-base — odrzucone: rubric-fixed + --essay-refine-kb v1 (ek22FK), tylko esej

- Δ 2024+2025: **+1.80 pkt (+6.0 pp)**
  (w tym esej +1.80 pkt; bez eseju +0.00); 2024: +0.00; 2025: +1.80; 2026: +1.00
- zadania lepsze / gorsze: 2 / 0 (suma +2.80 / 0.00 pkt)
- bootstrap po zadaniach (2024+2025, tylko szum zadań, bez szumu seedów): 95% CI [+0.0, +3.6] pkt
- wg type: essay: +2.80
- wg epoch: esej: +2.80
- wg img: False: +2.80
- największe zmiany: 2025/25 +1.80, 2026/26 +1.00

### T1-img1120 vs T1-t1final-full — T1 --image-min-tokens 1120 (2 seedy)

- Δ 2024+2025: **+3.83 pkt (+3.2 pp)**
  (w tym esej +4.50 pkt; bez eseju -0.67); 2024: +3.00; 2025: +0.83; 2026: -2.50
- zadania lepsze / gorsze: 17 / 19 (suma +12.50 / -11.17 pkt)
- bootstrap po zadaniach (2024+2025, tylko szum zadań, bez szumu seedów): 95% CI [-4.0, +12.5] pkt
- wg type: rozstrz: +2.00, closed_tf: -1.50, essay: +1.50, podaj: -1.33, wyjasnij: +0.67, closed_choice: +0.17, closed_match: -0.17
- wg epoch: 1945-89: +2.33, esej: +1.50, nowo: -1.33, 1914-39: -1.00, xix: +0.33, iiws: -0.33, sred: -0.17
- wg img: False: +0.83, True: +0.50
- największe zmiany: 2024/26 +2.50, 2025/25 +2.00, 2024/25 +1.50, 2026/17 +1.00, 2025/4 +1.00, 2026/26 -3.00, 2024/15.2 -0.67, 2024/8.1 -0.67, 2025/5.1 -0.67, 2025/7.1 -0.67

### T1-essay-refine-kb vs T1-t1final-full@T1-essay-refine-kb — T1 --essay-refine-kb v1 (tylko esej)

- Δ 2024+2025: **+2.50 pkt (+2.1 pp)**
  (w tym esej +2.50 pkt; bez eseju +0.00); 2024: +0.50; 2025: +2.00; 2026: -1.00
- zadania lepsze / gorsze: 2 / 1 (suma +2.50 / -1.00 pkt)
- bootstrap po zadaniach (2024+2025, tylko szum zadań, bez szumu seedów): 95% CI [+0.0, +7.0] pkt
- wg type: essay: +1.50
- wg epoch: esej: +1.50
- wg img: False: +1.50
- największe zmiany: 2025/25 +2.00, 2024/26 +0.50, 2026/26 -1.00

### T1-essay-refine-kb3 vs T1-t1final-full@T1-essay-refine-kb3 — T1 --essay-refine-kb v3 (tylko esej)

- Δ 2024+2025: **+5.00 pkt (+4.2 pp)**
  (w tym esej +5.00 pkt; bez eseju +0.00); 2024: +2.50; 2025: +2.50; 2026: -2.00
- zadania lepsze / gorsze: 2 / 1 (suma +5.00 / -2.00 pkt)
- bootstrap po zadaniach (2024+2025, tylko szum zadań, bez szumu seedów): 95% CI [+0.0, +12.5] pkt
- wg type: essay: +3.00
- wg epoch: esej: +3.00
- wg img: False: +3.00
- największe zmiany: 2025/25 +2.50, 2024/26 +2.50, 2026/26 -2.00

### T1-tiles vs T1-t1final-full@T1-tiles — odrzucone: --image-tiles (2 seedy, tylko zadania z obrazem)

- Δ 2024+2025: **+1.00 pkt (+0.8 pp)**
  (w tym esej +0.00 pkt; bez eseju +1.00); 2024: +1.50; 2025: -0.50; 2026: -1.50
- zadania lepsze / gorsze: 10 / 11 (suma +6.00 / -6.50 pkt)
- bootstrap po zadaniach (2024+2025, tylko szum zadań, bez szumu seedów): 95% CI [-3.5, +5.5] pkt
- wg type: rozstrz: +1.50, podaj: -1.00, closed_choice: +1.00, closed_match: -1.00, closed_tf: -1.00
- wg epoch: 1914-39: -4.00, staro: +1.00, sred: +1.00, 1945-89: +1.00, xix: +0.50
- wg img: True: -0.50
- największe zmiany: 2024/10 +1.00, 2024/1 +1.00, 2026/24 +0.50, 2026/14.2 +0.50, 2025/7.1 +0.50, 2025/21.2 -1.00, 2026/18.1 -1.00, 2024/11.1 -0.50, 2024/19.1 -0.50, 2024/2 -0.50

### T2-fill-fields vs T2-final — T2 poprzedni finał (--fill-fields, bez pomocy obrazowej)

- Δ 2024+2025: **-10.00 pkt (-8.4 pp)**
  (w tym esej +0.00 pkt; bez eseju -10.00); 2024: -4.00; 2025: -6.00; 2026: -1.50
- zadania lepsze / gorsze: 3 / 18 (suma +1.50 / -13.00 pkt)
- bootstrap po zadaniach (2024+2025, tylko szum zadań, bez szumu seedów): 95% CI [-16.0, -5.0] pkt
- wg type: podaj: -4.50, rozstrz: -4.00, wyjasnij: -3.00
- wg epoch: staro: -3.00, sred: -2.50, xix: -2.50, 1945-89: -2.00, 1914-39: -1.00, nowo: -0.50
- wg img: True: -11.50
- największe zmiany: 2026/20 +0.50, 2026/12.1 +0.50, 2025/3.2 +0.50, 2024/4 -1.00, 2025/12 -1.00, 2025/16.1 -1.00, 2025/18 -1.00, 2025/23 -1.00

### T2-ocr-only vs T2-final — T2 --fill-fields --ocr (bez caption)

- Δ 2024+2025: **-6.50 pkt (-5.5 pp)**
  (w tym esej +0.00 pkt; bez eseju -6.50); 2024: -3.00; 2025: -3.50; 2026: -2.50
- zadania lepsze / gorsze: 4 / 16 (suma +2.00 / -11.00 pkt)
- bootstrap po zadaniach (2024+2025, tylko szum zadań, bez szumu seedów): 95% CI [-12.0, -2.0] pkt
- wg type: rozstrz: -3.00, podaj: -3.00, wyjasnij: -3.00
- wg epoch: staro: -4.50, sred: -1.50, nowo: -1.50, 1914-39: -1.00, 1945-89: -1.00, xix: +0.50
- wg img: True: -9.00
- największe zmiany: 2026/15.1 +0.50, 2025/21.2 +0.50, 2025/14.1 +0.50, 2024/23.1 +0.50, 2024/12.3 -1.00, 2024/4 -1.00, 2025/18 -1.00, 2025/23 -1.00, 2025/3.1 -1.00

### T2-caption-only vs T2-final — T2 --fill-fields + caption (bez OCR)

- Δ 2024+2025: **+0.50 pkt (+0.4 pp)**
  (w tym esej +0.00 pkt; bez eseju +0.50); 2024: +2.50; 2025: -2.00; 2026: -3.50
- zadania lepsze / gorsze: 9 / 13 (suma +5.50 / -8.50 pkt)
- bootstrap po zadaniach (2024+2025, tylko szum zadań, bez szumu seedów): 95% CI [-5.0, +5.5] pkt
- wg type: podaj: -3.50, closed_tf: +0.50
- wg epoch: xix: -1.50, 1914-39: -1.00, 1945-89: -1.00, nowo: +0.50
- wg img: True: -3.00
- największe zmiany: 2024/9 +1.00, 2024/25 +1.00, 2025/8 +0.50, 2025/3.2 +0.50, 2025/14.1 +0.50, 2026/1 -1.50, 2025/18 -1.00, 2025/23 -1.00, 2024/12.1 -0.50, 2024/16.1 -0.50

### T2-nt2ocr vs T2-old — T2 --ocr, pełny przebieg (raport 10)

- Δ 2024+2025: **-3.33 pkt (-2.8 pp)**
  (w tym esej -5.00 pkt; bez eseju +1.67); 2024: +2.00; 2025: -5.33
- zadania lepsze / gorsze: 8 / 5 (suma +5.00 / -8.33 pkt)
- bootstrap po zadaniach (2024+2025, tylko szum zadań, bez szumu seedów): 95% CI [-16.7, +6.0] pkt
- wg type: essay: -5.00, podaj: +1.33, wyjasnij: +0.33
- wg epoch: esej: -5.00, staro: -1.00, xix: +1.00, sred: +0.67, 1914-39: +0.67, 1945-89: +0.67, nowo: -0.67, iiws: +0.33
- wg img: False: -5.33, True: +2.00
- największe zmiany: 2025/21.2 +1.00, 2025/12 +1.00, 2024/5.2 +0.67, 2024/23.1 +0.67, 2024/12.3 +0.67, 2025/25 -5.33, 2024/9 -1.00, 2025/3.2 -1.00, 2025/11.2 -0.67, 2025/18 -0.33

### T2-hyde vs T2-old — T2 --rag hyde

- Δ 2024+2025: **-1.33 pkt (-1.1 pp)**
  (w tym esej -3.00 pkt; bez eseju +1.67); 2024: +4.00; 2025: -5.33
- zadania lepsze / gorsze: 9 / 7 (suma +7.00 / -8.33 pkt)
- bootstrap po zadaniach (2024+2025, tylko szum zadań, bez szumu seedów): 95% CI [-11.3, +7.3] pkt
- wg type: wyjasnij: +3.33, essay: -3.00, rozstrz: -1.00, podaj: -0.67
- wg epoch: esej: -3.00, 1914-39: +1.67, staro: +1.00, nowo: -0.67, 1945-89: -0.33, sred: -0.33, iiws: +0.33
- wg img: False: -4.33, True: +3.00
- największe zmiany: 2025/18 +1.67, 2024/4 +1.00, 2024/2 +1.00, 2024/13 +1.00, 2024/5.2 +0.67, 2025/25 -3.33, 2024/9 -1.00, 2025/1.1 -1.00, 2025/8 -1.00, 2025/9.3 -1.00

### T2-kbk2 vs T2-old — T2 --kb-rag-k 2

- Δ 2024+2025: **+1.67 pkt (+1.4 pp)**
  (w tym esej +0.00 pkt; bez eseju +1.67); 2024: +1.00; 2025: +0.67
- zadania lepsze / gorsze: 9 / 6 (suma +5.67 / -4.00 pkt)
- bootstrap po zadaniach (2024+2025, tylko szum zadań, bez szumu seedów): 95% CI [-3.7, +7.0] pkt
- wg type: wyjasnij: +1.33, rozstrz: +1.00, closed_match: -1.00, podaj: +0.33
- wg epoch: xix: +1.00, sred: +0.67, 1914-39: +0.67, nowo: -0.67, 1945-89: -0.33, iiws: +0.33
- wg img: True: +1.00, False: +0.67
- największe zmiany: 2025/8 +1.00, 2025/15.2 +1.00, 2024/2 +1.00, 2025/18 +0.67, 2024/12.3 +0.67, 2024/9 -1.00, 2025/11.1 -1.00, 2025/3.2 -1.00, 2024/23.1 -0.33, 2024/5.2 -0.33

### T2-kbk3 vs T2-old — T2 --kb-rag-k 3

- Δ 2024+2025: **+4.67 pkt (+3.9 pp)**
  (w tym esej +3.00 pkt; bez eseju +1.67); 2024: +2.00; 2025: +2.67
- zadania lepsze / gorsze: 9 / 6 (suma +8.67 / -4.00 pkt)
- bootstrap po zadaniach (2024+2025, tylko szum zadań, bez szumu seedów): 95% CI [-2.0, +12.0] pkt
- wg type: essay: +3.00, podaj: +1.33, wyjasnij: +0.33
- wg epoch: esej: +3.00, staro: +1.00, xix: +1.00, sred: +0.67, iiws: -0.67, 1945-89: +0.67, nowo: -0.67, 1914-39: -0.33
- wg img: False: +2.67, True: +2.00
- największe zmiany: 2025/25 +1.67, 2024/26 +1.33, 2025/8 +1.00, 2025/15.2 +1.00, 2024/4 +1.00, 2024/1 -1.00, 2024/9 -1.00, 2024/22.2 -0.67, 2025/11.2 -0.67, 2024/5.2 -0.33

### T3-retry vs T3-MIX@T3-retry — składnik finału: --think-retry --match-retry (na MIX, scalone, seedy sparowane)

- Δ 2024+2025: **+0.50 pkt (+0.4 pp)**
  (w tym esej +0.00 pkt; bez eseju +0.50); 2024: +0.50; 2025: +0.00; 2026: +0.00
- zadania lepsze / gorsze: 2 / 1 (suma +1.50 / -1.00 pkt)
- bootstrap po zadaniach (2024+2025, tylko szum zadań, bez szumu seedów): 95% CI [+0.0, +1.5] pkt
- wg type: rozstrz: +1.00, podaj: -1.00, wyjasnij: +0.50
- wg epoch: nowo: +1.00, xix: -1.00, 1945-89: +0.50
- wg img: False: +1.00, True: -0.50
- największe zmiany: 2026/8 +1.00, 2024/25 +0.50, 2026/16.2 -1.00

### T3-T40K vs T3-V124K@T3-T40K — odrzucone: słownik przycięty do 40k (1.40 GB), z retry

- Δ 2024+2025: **-5.50 pkt (-4.6 pp)**
  (w tym esej -1.00 pkt; bez eseju -4.50); 2024: +1.50; 2025: -7.00; 2026: +1.50
- zadania lepsze / gorsze: 21 / 25 (suma +11.50 / -15.50 pkt)
- bootstrap po zadaniach (2024+2025, tylko szum zadań, bez szumu seedów): 95% CI [-13.0, +2.0] pkt
- wg type: rozstrz: +2.50, closed_match: -2.50, closed_tf: -1.50, essay: -1.00, podaj: -0.50, wyjasnij: -0.50, closed_choice: -0.50
- wg epoch: xix: -3.00, nowo: -1.50, staro: +1.00, sred: -1.00, 1945-89: +1.00, esej: -1.00, 1914-39: +0.50
- wg img: True: -3.50, False: -0.50
- największe zmiany: 2025/5.2 +1.00, 2024/23.1 +1.00, 2026/8 +0.50, 2026/7 +0.50, 2026/25 +0.50, 2025/11.1 -1.50, 2024/5.2 -1.00, 2025/14.2 -1.00, 2025/25 -1.00, 2025/6 -1.00

### T3-prev-iq3xxs vs T3-MIX — T3 poprzedni: UD-IQ3_XXS 1.95 GB + limit 5000 (esej stary)

- Δ 2024+2025: **+1.67 pkt (+1.4 pp)**
  (w tym esej +1.50 pkt; bez eseju +0.17); 2024: -2.67; 2025: +4.33; 2026: -2.00
- zadania lepsze / gorsze: 28 / 29 (suma +16.33 / -16.67 pkt)
- bootstrap po zadaniach (2024+2025, tylko szum zadań, bez szumu seedów): 95% CI [-7.2, +9.7] pkt
- wg type: podaj: -4.50, rozstrz: +4.33, essay: +2.50, wyjasnij: -1.67, closed_choice: -1.00, closed_tf: -0.67, closed_match: +0.67
- wg epoch: staro: -2.67, esej: +2.50, xix: -1.33, 1945-89: +1.00, 1914-39: -0.67, sred: +0.50, nowo: +0.33
- wg img: True: -3.83, False: +3.50
- największe zmiany: 2025/25 +1.50, 2026/26 +1.00, 2025/7.1 +1.00, 2024/23.1 +1.00, 2024/22.1 +1.00, 2026/24 -1.50, 2024/12.2 -1.00, 2024/17.2 -1.00, 2024/19.1 -1.00, 2024/3.2 -1.00

### T3-e4k vs T3-MIX — T3 IQ3_XXS-PL-E4K 1.87 GB (esej stary)

- Δ 2024+2025: **-1.00 pkt (-0.8 pp)**
  (w tym esej -0.50 pkt; bez eseju -0.50); 2024: -2.00; 2025: +1.00; 2026: +2.50
- zadania lepsze / gorsze: 27 / 23 (suma +19.50 / -18.00 pkt)
- bootstrap po zadaniach (2024+2025, tylko szum zadań, bez szumu seedów): 95% CI [-11.0, +8.0] pkt
- wg type: wyjasnij: +2.00, closed_tf: -2.00, podaj: -1.50, essay: +1.50, closed_choice: +1.00, closed_match: +0.50
- wg epoch: staro: -4.50, nowo: +3.00, 1914-39: -2.50, 1945-89: +2.50, xix: +1.50, esej: +1.50
- wg img: False: +3.00, True: -1.50
- największe zmiany: 2026/26 +2.00, 2025/11.1 +1.50, 2024/25 +1.50, 2025/21.2 +1.00, 2025/18 +1.00, 2024/19.1 -2.00, 2024/1 -1.00, 2024/12.2 -1.00, 2024/3.1 -1.00, 2024/3.2 -1.00
