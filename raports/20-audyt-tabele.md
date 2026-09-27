# 20 — Audyt odpowiedzi: pełne tabele (generowane: `python eval/audit.py --out raports/20-audyt-tabele.md`)

## A. Wyniki grup (średnia z seedów, sędzia luna)

| grupa | opis | rola | 2024+2025 | 2026 | seedy |
|---|---|---|---|---|---|
| T1-final | T1 finał: Gemma-4-12B QAT t1final | final | 70.3% | 83.3% | 2024×3, 2025×3, 2026×2 |
| T1-rozstrz-hint | T1 --rozstrz-hint (3 seedy) | near | 70.9% | 84.4% | 2024×3, 2025×3, 2026×3 |
| T1-img1120 | T1 --image-min-tokens 1120 (2 seedy) | near | 73.5% | 80.0% | 2024×2, 2025×2, 2026×2 |
| T1-essay-refine-kb | T1 --essay-refine-kb v1 (tylko esej) | near | 73.1% | 81.7% | 2024×2, 2025×2, 2026×1 |
| T1-essay-refine-kb3 | T1 --essay-refine-kb v3 (tylko esej) | near | 75.2% | 80.0% | 2024×2, 2025×2, 2026×1 |
| T2-final | T2 finał: PLLuM+LoRA+RAG --fill-fields --ocr + caption 0.8B | final | 56.7% | 52.5% | 2024×2, 2025×2, 2026×2 |
| T2-fill-fields | T2 poprzedni finał (--fill-fields, bez pomocy obrazowej) | ref | 48.3% | 50.0% | 2024×2, 2025×2, 2026×2 |
| T2-ocr-only | T2 --fill-fields --ocr (bez caption) | near | 51.3% | 48.3% | 2024×2, 2025×2, 2026×2 |
| T2-caption-only | T2 --fill-fields + caption (bez OCR) | near | 57.1% | 46.7% | 2024×2, 2025×2, 2026×2 |
| T2-old | T2 finał z 01:00 (bez --fill-fields; 3 przebiegi tej samej konfiguracji) | ref | 52.4% | 47.8% | 2024×3, 2025×3, 2026×3 |
| T2-nt2ocr | T2 --ocr, pełny przebieg (raport 10) | near | 49.6% | — | 2024×1, 2025×1 |
| T2-hyde | T2 --rag hyde | near | 51.3% | — | 2024×1, 2025×1 |
| T2-kbk2 | T2 --kb-rag-k 2 | near | 53.8% | — | 2024×1, 2025×1 |
| T2-kbk3 | T2 --kb-rag-k 3 | near | 56.3% | — | 2024×1, 2025×1 |
| T3-final | T3 finał: Qwen3.5-4B IQ2_M-PL-E4K-MIX + esej structured | final | 42.9% | 45.0% | 2024×2, 2025×2, 2026×1 |
| T3-prev-iq3xxs | T3 poprzedni: UD-IQ3_XXS 1.95 GB + limit 5000 (esej stary) | near | 44.3% | 42.5% | 2024×3, 2025×3, 2026×2 |
| T3-e4k | T3 IQ3_XXS-PL-E4K 1.87 GB (esej stary) | near | 42.0% | 50.0% | 2024×1, 2025×1, 2026×1 |
| T1-final@T1-essay-refine-kb | T1-final (seedy sparowane z T1-essay-refine-kb) | ref | 71.0% | 83.3% | 2024×2, 2025×2, 2026×1 |
| T1-final@T1-essay-refine-kb3 | T1-final (seedy sparowane z T1-essay-refine-kb3) | ref | 71.0% | 83.3% | 2024×2, 2025×2, 2026×1 |

## B. Finały — strata wg: typ zadania (pkt; 2024+2025 = 119 pkt, 2026 = 60 pkt)

| kategoria | max 24+25 | T1-final 24+25 | T2-final 24+25 | T3-final 24+25 | T1-final 2026 | T2-final 2026 | T3-final 2026 |
|---|---|---|---|---|---|---|---|
| closed_choice | 6 | 0.7 | 1.0 | 2.5 | 0 | 3.0 | 1.0 |
| closed_tf | 8 | 2.0 | 4.0 | 1.0 | 0 | 2.0 | 2.0 |
| closed_match | 6 | 2.3 | 2.0 | 5.5 | 0 | 2.0 | 2.0 |
| podaj | 24 | 4.7 | 3.5 | 12.5 | 0.5 | 2.5 | 4.0 |
| rozstrz | 28 | 6.0 | 18.0 | 12.5 | 5.5 | 9.5 | 9.0 |
| wyjasnij | 17 | 3.7 | 6.0 | 5.5 | 1.0 | 3.5 | 0 |
| essay | 30 | 16.0 | 17.0 | 28.5 | 3.0 | 6.0 | 15.0 |
| **razem** |  | 35.3 | 51.5 | 68.0 | 10.0 | 28.5 | 33.0 |

## B. Finały — strata wg: epoka (pkt; 2024+2025 = 119 pkt, 2026 = 60 pkt)

| kategoria | max 24+25 | T1-final 24+25 | T2-final 24+25 | T3-final 24+25 | T1-final 2026 | T2-final 2026 | T3-final 2026 |
|---|---|---|---|---|---|---|---|
| staro | 10 | 1.0 | 3.5 | 0 | 0 | 3.0 | 0 |
| sred | 14 | 3.3 | 5.5 | 8.5 | 1.0 | 2.5 | 4.0 |
| nowo | 17 | 3.7 | 4.0 | 11.0 | 1.0 | 4.5 | 4.0 |
| xix | 17 | 3.3 | 5.5 | 5.5 | 2.0 | 3.5 | 4.0 |
| 1914-39 | 17 | 4.0 | 9.5 | 7.5 | 2.0 | 4.5 | 4.0 |
| iiws | 4 | 0.7 | 1.0 | 2.0 | 0 | 0 | 0 |
| 1945-89 | 10 | 3.3 | 5.5 | 5.0 | 1.0 | 4.5 | 2.0 |
| 1914-39 (esej) | 15 | 0 | 0 | 14.0 | 0 | 0 | 0 |
| 1945-89 (esej) | 15 | 0 | 0 | 14.5 | 0 | 0 | 0 |
| sred (esej) | 30 | 16.0 | 17.0 | 0 | 0 | 6.0 | 0 |
| xix (esej) | 0 | 0 | 0 | 0 | 3.0 | 0 | 15.0 |
| **razem** |  | 35.3 | 51.5 | 68.0 | 10.0 | 28.5 | 33.0 |

## B. Finały — strata wg: rodzaj błędu (pkt; 2024+2025 = 119 pkt, 2026 = 60 pkt)

| kategoria | T1-final 24+25 | T2-final 24+25 | T3-final 24+25 | T1-final 2026 | T2-final 2026 | T3-final 2026 |
|---|---|---|---|---|---|---|
| wiedza/fakt | 5.3 | 7.5 | 17.0 | 1.0 | 4.0 | 8.0 |
| źle odczytany obraz | 10.0 | 15.0 | 6.5 | 3.0 | 7.5 | 4.0 |
| źle odczytany tekst źródła | 0.7 | 4.0 | 6.0 | 3.0 | 3.5 | 2.0 |
| polecenie/format | 0 | 1.0 | 2.0 | 0 | 1.0 | 0 |
| odpowiedź niepełna | 0 | 1.0 | 0 | 0 | 1.0 | 0 |
| rozumowanie/logika | 0 | 6.0 | 4.0 | 0 | 5.5 | 2.0 |
| harness (fallback/urwanie/błąd) | 1.3 | 0 | 3.0 | 0 | 0 | 2.0 |
| sędzia/grader za surowy (tylko ewaluacja) | 2.0 | 0 | 1.0 | 0 | 0 | 0 |
| esej A: aspekty (powierzchowne/brak) | 12.3 | 13.0 | 18.4 | 3.0 | 5.0 | 12.0 |
| esej A: błędy merytoryczne | 3.3 | 4.0 | 5.8 | 0 | 1.0 | 0 |
| esej B: spójność/długość | 0.3 | 0 | 4.3 | 0 | 0 | 3.0 |
| **razem** | 35.3 | 51.5 | 68.0 | 10.0 | 28.5 | 33.0 |

## B. Finały — strata wg: obraz (pkt; 2024+2025 = 119 pkt, 2026 = 60 pkt)

| kategoria | max 24+25 | T1-final 24+25 | T2-final 24+25 | T3-final 24+25 | T1-final 2026 | T2-final 2026 | T3-final 2026 |
|---|---|---|---|---|---|---|---|
| art | 9 | 1.0 | 3.0 | 5.0 | 0 | 0 | 0 |
| artefact | 5 | 1.3 | 4.0 | 2.0 | 2.0 | 6.0 | 6.0 |
| brak obrazu | 61 | 22.3 | 25.0 | 44.0 | 5.0 | 10.0 | 20.0 |
| cartoon | 12 | 3.7 | 6.5 | 4.0 | 1.0 | 6.0 | 1.0 |
| chart | 1 | 0.7 | 0 | 1.0 | 0 | 0 | 0 |
| map | 12 | 4.0 | 5.0 | 6.5 | 1.0 | 5.0 | 3.0 |
| photo | 11 | 1.7 | 3.0 | 1.5 | 0 | 0 | 0 |
| poster | 4 | 0.3 | 2.5 | 1.5 | 0 | 0.5 | 1.0 |
| press | 4 | 0.3 | 2.5 | 2.5 | 1.0 | 1.0 | 2.0 |
| **razem** |  | 35.3 | 51.5 | 68.0 | 10.0 | 28.5 | 33.0 |

## B. Finały — strata wg: rodzaj źródła (pkt; 2024+2025 = 119 pkt, 2026 = 60 pkt)

| kategoria | max 24+25 | T1-final 24+25 | T2-final 24+25 | T3-final 24+25 | T1-final 2026 | T2-final 2026 | T3-final 2026 |
|---|---|---|---|---|---|---|---|
| bez źródła | 32 | 17.0 | 17.0 | 30.5 | 3.0 | 6.0 | 15.0 |
| obraz | 27 | 7.3 | 14.0 | 12.5 | 1.0 | 7.0 | 3.0 |
| tekst | 29 | 5.3 | 8.0 | 13.5 | 2.0 | 4.0 | 5.0 |
| tekst+obraz | 31 | 5.7 | 12.5 | 11.5 | 4.0 | 11.5 | 10.0 |
| **razem** |  | 35.3 | 51.5 | 68.0 | 10.0 | 28.5 | 33.0 |

## C. Typ × epoka — strata finałów razem (pkt, 3 arkusze, suma T1+T2+T3)

| typ \ epoka | staro | sred | nowo | xix | 1914-39 | iiws | 1945-89 | razem |
|---|---|---|---|---|---|---|---|---|
| closed_choice | 1.0 | 0.5 | 3.7 | 2.0 | 1.0 | 0 | 0 | 8.2 |
| closed_tf | 1.0 | 0 | 2.0 | 3.0 | 5.0 | 0 | 0 | 11.0 |
| closed_match | 0 | 6.3 | 7.5 | 0 | 0 | 0 | 0 | 13.8 |
| podaj | 0.3 | 4.0 | 6.5 | 2.0 | 10.3 | 1.0 | 3.5 | 27.7 |
| rozstrz | 5.2 | 12.5 | 7.5 | 16.3 | 10.5 | 2.7 | 5.8 | 60.5 |
| wyjasnij | 0 | 1.5 | 1.0 | 0.5 | 4.7 | 0 | 12.0 | 19.7 |
| essay | 0 | 39.0 | 0 | 18.0 | 14.0 | 0 | 14.5 | 85.5 |
| **razem** | 7.5 | 63.8 | 28.2 | 41.8 | 45.5 | 3.7 | 35.8 | 226.3 |

## D. T1-final: rodzaj błędu × typ zadania (pkt, 3 arkusze)

| błąd \ typ | closed_choice | closed_tf | closed_match | podaj | rozstrz | wyjasnij | essay | razem |
|---|---|---|---|---|---|---|---|---|
| wiedza/fakt | 0.7 | 0 | 1.0 | 2.0 | 2.7 | 0 | 0 | 6.3 |
| źle odczytany obraz | 0 | 1.7 | 0 | 1.8 | 4.8 | 4.7 | 0 | 13.0 |
| źle odczytany tekst źródła | 0 | 0.3 | 0 | 0 | 3.3 | 0 | 0 | 3.7 |
| harness (fallback/urwanie/błąd) | 0 | 0 | 0 | 1.0 | 0.3 | 0 | 0 | 1.3 |
| sędzia/grader za surowy (tylko ewaluacja) | 0 | 0 | 1.3 | 0.3 | 0.3 | 0 | 0 | 2.0 |
| esej A: aspekty (powierzchowne/brak) | 0 | 0 | 0 | 0 | 0 | 0 | 15.3 | 15.3 |
| esej A: błędy merytoryczne | 0 | 0 | 0 | 0 | 0 | 0 | 3.3 | 3.3 |
| esej B: spójność/długość | 0 | 0 | 0 | 0 | 0 | 0 | 0.3 | 0.3 |

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
| wiedza/fakt | 3.5 | 3.0 | 3.5 | 14.5 | 0.5 | 0 | 0 | 25.0 |
| źle odczytany obraz | 0 | 0 | 1.0 | 0 | 7.5 | 2.0 | 0 | 10.5 |
| źle odczytany tekst źródła | 0 | 0 | 0 | 1.0 | 6.5 | 0.5 | 0 | 8.0 |
| polecenie/format | 0 | 0 | 2.0 | 0 | 0 | 0 | 0 | 2.0 |
| rozumowanie/logika | 0 | 0 | 0 | 0 | 4.5 | 1.5 | 0 | 6.0 |
| harness (fallback/urwanie/błąd) | 0 | 0 | 0 | 1.0 | 2.5 | 1.5 | 0 | 5.0 |
| sędzia/grader za surowy (tylko ewaluacja) | 0 | 0 | 1.0 | 0 | 0 | 0 | 0 | 1.0 |
| esej A: aspekty (powierzchowne/brak) | 0 | 0 | 0 | 0 | 0 | 0 | 30.4 | 30.4 |
| esej A: błędy merytoryczne | 0 | 0 | 0 | 0 | 0 | 0 | 5.8 | 5.8 |
| esej B: spójność/długość | 0 | 0 | 0 | 0 | 0 | 0 | 7.3 | 7.3 |

## E. Zadania trudne dla wszystkich finałów (średnio ≤ 34% punktów w każdym)

| zadanie | typ | epoka | obraz | max | T1-final śr. pkt (błąd) | T2-final śr. pkt (błąd) | T3-final śr. pkt (błąd) |
|---|---|---|---|---|---|---|---|
| 2024/5.1 | rozstrz | sred | map | 1 | 0.33 (obraz) | 0 (obraz) | 0 (obraz) |
| 2024/7 | rozstrz | sred | brak obrazu | 1 | 0 (wiedza) | 0 (wiedza) | 0 (tekst) |
| 2024/11.1 | closed_match | nowo | art | 1 | 0.33 (wiedza) | 0 (wiedza) | 0 (wiedza) |
| 2024/14.1 | rozstrz | xix | map | 1 | 0 (obraz) | 0 (obraz) | 0 (obraz) |
| 2024/19.2 | podaj | 1914-39 | artefact | 1 | 0.33 (obraz) | 0 (wiedza) | 0 (wiedza) |
| 2025/14.1 | rozstrz | xix | map | 1 | 0 (obraz) | 0 (obraz) | 0 (obraz) |
| 2025/22 | rozstrz | iiws | brak obrazu | 1 | 0.33 (wiedza) | 0 (wiedza) | 0 (wiedza) |
| 2026/12.2 | rozstrz | nowo | map | 1 | 0 (obraz) | 0 (tekst) | 0 (obraz) |
| 2026/18.2 | rozstrz | 1914-39 | artefact | 1 | 0 (tekst) | 0 (obraz) | 0 (obraz) |
| 2026/19.1 | rozstrz | 1914-39 | press | 1 | 0 (tekst) | 0 (tekst) | 0 (tekst) |

## F. Rozbieżności między finałami (różnica ≥ 67 pp udziału punktów)

| zadanie | typ | epoka | obraz | udział pkt | rozwiązuje | nie rozwiązuje (błąd) |
|---|---|---|---|---|---|---|
| 2024/1 | rozstrz | staro | photo | T1=33% T2=0% T3=100% | T3-final | T1-final: obraz; T2-final: obraz |
| 2024/8.1 | podaj | nowo | art | T1=67% T2=100% T3=0% | T2-final | T3-final: wiedza |
| 2024/9 | rozstrz | nowo | art | T1=100% T2=0% T3=50% | T1-final | T2-final: rozumowanie |
| 2024/10 | closed_choice | nowo | chart | T1=33% T2=100% T3=0% | T2-final | T1-final: wiedza; T3-final: wiedza |
| 2024/11.2 | wyjasnij | nowo | art | T1=100% T2=100% T3=0% | T1-final, T2-final | T3-final: rozumowanie |
| 2024/14.2 | closed_choice | xix | map | T1=100% T2=100% T3=0% | T1-final, T2-final | T3-final: wiedza |
| 2024/18 | rozstrz | 1914-39 | poster | T1=100% T2=0% T3=100% | T1-final, T3-final | T2-final: rozumowanie |
| 2024/19.1 | closed_tf | 1914-39 | artefact | T1=67% T2=0% T3=100% | T3-final | T2-final: obraz |
| 2024/22.1 | podaj | iiws | brak obrazu | T1=100% T2=100% T3=0% | T1-final, T2-final | T3-final: wiedza |
| 2024/23.1 | podaj | 1945-89 | poster | T1=100% T2=50% T3=0% | T1-final | T3-final: wiedza |
| 2024/24 | rozstrz | 1945-89 | map | T1=100% T2=0% T3=50% | T1-final | T2-final: obraz |
| 2025/2 | rozstrz | staro | brak obrazu | T1=100% T2=0% T3=100% | T1-final, T3-final | T2-final: niepelna |
| 2025/4 | closed_match | sred | brak obrazu | T1=50% T2=100% T3=0% | T2-final | T3-final: sedzia |
| 2025/7.1 | rozstrz | sred | map | T1=67% T2=100% T3=0% | T2-final | T3-final: tekst |
| 2025/9.2 | podaj | nowo | brak obrazu | T1=100% T2=100% T3=0% | T1-final, T2-final | T3-final: wiedza |
| 2025/9.3 | podaj | nowo | brak obrazu | T1=0% T2=100% T3=0% | T2-final | T1-final: wiedza; T3-final: wiedza |
| 2025/10 | closed_tf | nowo | artefact | T1=100% T2=0% T3=0% | T1-final | T2-final: obraz; T3-final: wiedza |
| 2025/11.1 | closed_match | nowo | brak obrazu | T1=83% T2=100% T3=25% | T1-final, T2-final | T3-final: wiedza |
| 2025/11.2 | rozstrz | nowo | brak obrazu | T1=100% T2=0% T3=50% | T1-final | T2-final: rozumowanie |
| 2025/15.2 | rozstrz | xix | brak obrazu | T1=100% T2=0% T3=100% | T1-final, T3-final | T2-final: tekst |
| 2025/16.2 | rozstrz | xix | press | T1=100% T2=0% T3=100% | T1-final, T3-final | T2-final: rozumowanie |
| 2025/17.2 | closed_choice | 1914-39 | cartoon | T1=100% T2=0% T3=100% | T1-final, T3-final | T2-final: wiedza |
| 2025/19 | podaj | 1914-39 | brak obrazu | T1=33% T2=100% T3=0% | T2-final | T1-final: wiedza; T3-final: wiedza |
| 2025/21.2 | rozstrz | 1914-39 | press | T1=100% T2=50% T3=0% | T1-final | T3-final: rozumowanie |
| 2026/2 | closed_tf | staro | brak obrazu | T1=100% T2=0% T3=100% | T1-final, T3-final | T2-final: polecenie |
| 2026/3.1 | rozstrz | staro | map | T1=100% T2=0% T3=100% | T1-final, T3-final | T2-final: rozumowanie |
| 2026/3.2 | closed_choice | staro | map | T1=100% T2=0% T3=100% | T1-final, T3-final | T2-final: wiedza |
| 2026/4.1 | rozstrz | sred | map | T1=100% T2=0% T3=0% | T1-final | T2-final: obraz; T3-final: obraz |
| 2026/5.1 | podaj | sred | brak obrazu | T1=100% T2=0% T3=100% | T1-final, T3-final | T2-final: niepelna |
| 2026/6.1 | closed_match | sred | brak obrazu | T1=100% T2=100% T3=0% | T1-final, T2-final | T3-final: wiedza |
| 2026/6.2 | rozstrz | sred | brak obrazu | T1=0% T2=100% T3=0% | T2-final | T1-final: wiedza; T3-final: harness |
| 2026/7 | podaj | sred | map | T1=100% T2=100% T3=0% | T1-final, T2-final | T3-final: wiedza |
| 2026/8 | rozstrz | nowo | brak obrazu | T1=100% T2=100% T3=0% | T1-final, T2-final | T3-final: harness |
| 2026/10.1 | closed_choice | nowo | brak obrazu | T1=100% T2=0% T3=0% | T1-final | T2-final: tekst; T3-final: wiedza |
| 2026/13 | closed_match | nowo | artefact | T1=100% T2=0% T3=50% | T1-final | T2-final: obraz |
| 2026/14.1 | podaj | xix | artefact | T1=50% T2=100% T3=0% | T2-final | T3-final: wiedza |
| 2026/14.3 | closed_tf | xix | artefact | T1=100% T2=0% T3=0% | T1-final | T2-final: wiedza; T3-final: wiedza |
| 2026/15.2 | closed_choice | xix | cartoon | T1=100% T2=0% T3=100% | T1-final, T3-final | T2-final: obraz |
| 2026/17 | rozstrz | xix | brak obrazu | T1=0% T2=100% T3=0% | T2-final | T1-final: tekst; T3-final: rozumowanie |
| 2026/18.1 | podaj | 1914-39 | artefact | T1=100% T2=0% T3=0% | T1-final | T2-final: wiedza; T3-final: wiedza |
| 2026/19.2 | closed_tf | 1914-39 | press | T1=100% T2=100% T3=0% | T1-final, T2-final | T3-final: wiedza |
| 2026/20 | rozstrz | 1914-39 | cartoon | T1=100% T2=25% T3=100% | T1-final, T3-final | T2-final: rozumowanie |
| 2026/22 | rozstrz | 1945-89 | brak obrazu | T1=100% T2=0% T3=100% | T1-final, T3-final | T2-final: wiedza |
| 2026/23.2 | podaj | 1945-89 | cartoon | T1=100% T2=100% T3=0% | T1-final, T2-final | T3-final: wiedza |
| 2026/24 | wyjasnij | 1945-89 | cartoon | T1=67% T2=0% T3=100% | T3-final | T2-final: rozumowanie |
| 2026/25 | rozstrz | 1945-89 | poster | T1=100% T2=50% T3=0% | T1-final | T3-final: rozumowanie |

## G. Warianty bliskie najlepszym vs odniesienie (Δ pkt = średnia wariantu − średnia odniesienia, te same zadania)

### T1-rozstrz-hint vs T1-final — T1 --rozstrz-hint (3 seedy)

- Δ 2024+2025: **+0.67 pkt (+0.6 pp)**
  (w tym esej -0.33 pkt; bez eseju +1.00); 2024: +1.00; 2025: -0.33; 2026: +0.67
- zadania lepsze / gorsze: 6 / 7 (suma +3.67 / -2.33 pkt)
- bootstrap po zadaniach (2024+2025, tylko szum zadań, bez szumu seedów): 95% CI [-1.7, +3.3] pkt
- wg type: rozstrz: +2.17, podaj: -0.50, essay: -0.33
- wg epoch: staro: +1.00, 1914-39: +0.67, esej: -0.33, sred: +0.33, xix: -0.33
- wg img: True: +2.00, False: -0.67
- największe zmiany: 2026/19.1 +1.00, 2024/5.1 +0.67, 2024/1 +0.67, 2026/17 +0.67, 2025/7.1 +0.33, 2026/14.1 -0.50, 2024/26 -0.33, 2025/15.2 -0.33, 2025/5.2 -0.33, 2026/4.1 -0.33

### T1-img1120 vs T1-final — T1 --image-min-tokens 1120 (2 seedy)

- Δ 2024+2025: **+3.83 pkt (+3.2 pp)**
  (w tym esej +4.50 pkt; bez eseju -0.67); 2024: +3.00; 2025: +0.83; 2026: -2.00
- zadania lepsze / gorsze: 18 / 19 (suma +13.00 / -11.17 pkt)
- bootstrap po zadaniach (2024+2025, tylko szum zadań, bez szumu seedów): 95% CI [-4.0, +12.5] pkt
- wg type: rozstrz: +2.00, closed_tf: -1.50, essay: +1.50, podaj: -0.83, wyjasnij: +0.67, closed_choice: +0.17, closed_match: -0.17
- wg epoch: 1945-89: +2.33, esej: +1.50, nowo: -1.33, 1914-39: -1.00, xix: +0.83, iiws: -0.33, sred: -0.17
- wg img: True: +1.00, False: +0.83
- największe zmiany: 2024/26 +2.50, 2025/25 +2.00, 2024/25 +1.50, 2026/17 +1.00, 2025/4 +1.00, 2026/26 -3.00, 2024/15.2 -0.67, 2024/8.1 -0.67, 2025/5.1 -0.67, 2025/7.1 -0.67

### T1-essay-refine-kb vs T1-final@T1-essay-refine-kb — T1 --essay-refine-kb v1 (tylko esej)

- Δ 2024+2025: **+2.50 pkt (+2.1 pp)**
  (w tym esej +2.50 pkt; bez eseju +0.00); 2024: +0.50; 2025: +2.00; 2026: -1.00
- zadania lepsze / gorsze: 2 / 1 (suma +2.50 / -1.00 pkt)
- bootstrap po zadaniach (2024+2025, tylko szum zadań, bez szumu seedów): 95% CI [+0.0, +7.0] pkt
- wg type: essay: +1.50
- wg epoch: esej: +1.50
- wg img: False: +1.50
- największe zmiany: 2025/25 +2.00, 2024/26 +0.50, 2026/26 -1.00

### T1-essay-refine-kb3 vs T1-final@T1-essay-refine-kb3 — T1 --essay-refine-kb v3 (tylko esej)

- Δ 2024+2025: **+5.00 pkt (+4.2 pp)**
  (w tym esej +5.00 pkt; bez eseju +0.00); 2024: +2.50; 2025: +2.50; 2026: -2.00
- zadania lepsze / gorsze: 2 / 1 (suma +5.00 / -2.00 pkt)
- bootstrap po zadaniach (2024+2025, tylko szum zadań, bez szumu seedów): 95% CI [+0.0, +12.5] pkt
- wg type: essay: +3.00
- wg epoch: esej: +3.00
- wg img: False: +3.00
- największe zmiany: 2025/25 +2.50, 2024/26 +2.50, 2026/26 -2.00

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

### T3-prev-iq3xxs vs T3-final — T3 poprzedni: UD-IQ3_XXS 1.95 GB + limit 5000 (esej stary)

- Δ 2024+2025: **+1.67 pkt (+1.4 pp)**
  (w tym esej +1.50 pkt; bez eseju +0.17); 2024: -2.67; 2025: +4.33; 2026: -1.50
- zadania lepsze / gorsze: 32 / 31 (suma +18.83 / -18.67 pkt)
- bootstrap po zadaniach (2024+2025, tylko szum zadań, bez szumu seedów): 95% CI [-7.2, +9.7] pkt
- wg type: podaj: -4.50, rozstrz: +3.83, essay: +2.50, wyjasnij: -2.17, closed_match: +0.67, closed_choice: -0.50, closed_tf: +0.33
- wg epoch: staro: -3.17, esej: +2.50, xix: -1.33, nowo: +1.33, sred: +1.00, 1914-39: -0.67, 1945-89: +0.50
- wg img: False: +4.50, True: -4.33
- największe zmiany: 2025/25 +1.50, 2026/8 +1.00, 2026/26 +1.00, 2025/7.1 +1.00, 2024/23.1 +1.00, 2026/24 -2.00, 2024/12.2 -1.00, 2024/17.2 -1.00, 2024/19.1 -1.00, 2024/3.2 -1.00

### T3-e4k vs T3-final — T3 IQ3_XXS-PL-E4K 1.87 GB (esej stary)

- Δ 2024+2025: **-1.00 pkt (-0.8 pp)**
  (w tym esej -0.50 pkt; bez eseju -0.50); 2024: -2.00; 2025: +1.00; 2026: +3.00
- zadania lepsze / gorsze: 22 / 21 (suma +19.50 / -17.50 pkt)
- bootstrap po zadaniach (2024+2025, tylko szum zadań, bez szumu seedów): 95% CI [-11.0, +8.0] pkt
- wg type: podaj: -1.50, wyjasnij: +1.50, closed_choice: +1.50, essay: +1.50, closed_tf: -1.00, rozstrz: -0.50, closed_match: +0.50
- wg epoch: staro: -5.00, nowo: +4.00, 1914-39: -2.50, 1945-89: +2.00, xix: +1.50, esej: +1.50, sred: +0.50
- wg img: False: +4.00, True: -2.00
- największe zmiany: 2026/26 +2.00, 2025/11.1 +1.50, 2024/25 +1.50, 2026/8 +1.00, 2026/7 +1.00, 2024/19.1 -2.00, 2024/1 -1.00, 2024/12.2 -1.00, 2024/3.1 -1.00, 2024/3.2 -1.00
