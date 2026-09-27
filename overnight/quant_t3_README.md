# Qwen3.5-4B — własne kwantyzacje T3 (imatrix PL)

Stan: 27.09.2026 ~04:55 CEST. Pliki gotowe; E4K i E3K sprawdzone w finalnej konfiguracji T3.

## Pliki

| Plik | Bajty | sha256 (początek) | Opis |
|---|---|---|---|
| `Qwen3.5-4B-IQ3_XXS-PL.gguf` | 1 949 047 904 | 3294f1c3 | przepis UD-IQ3_XXS unsloth 1:1 + nasz imatrix, token_embd Q5_K |
| `Qwen3.5-4B-IQ3_XXS-PL-E4K.gguf` | 1 869 585 504 | 1d026af7 | jw., ale token_embd Q4_K (z imatrix dla token_embd) |
| `Qwen3.5-4B-IQ3_XXS-PL-E3K.gguf` | 1 785 156 704 | fdfb3283 | jw., token_embd Q3_K |
| `Qwen3.5-4B-IQ2_M-PL.gguf` * | 1 759 997 024 | 9009979a | przepis UD-IQ2_M 1:1 + imatrix PL, token_embd Q5_K |
| `Qwen3.5-4B-IQ2_M-PL-E4K-MIX.gguf` * | 1 745 906 784 | 1d4eaec7 | UD-IQ2_M + imatrix PL, token_embd Q4_K, ffn_down i attn_qkv IQ2_S→IQ3_XXS (47 tensorów, `work/tt_UD-IQ2_M-mix.txt`) |
| `Qwen3.5-4B-IQ2_M-PL-E4K.gguf` * | 1 680 534 624 | b74ef5c4 | UD-IQ2_M + imatrix PL, token_embd Q4_K |

\* pliki IQ2_M zbudował inny agent (`work/q2_build.sh`, sumy w `q2.sha256`); bez wyników egzaminu. PPL (CPU, 4 × 2048, tekst PL / rozumowanie): stock UD-IQ2_M 6.899 / 1.9410; IQ2_M-PL 6.647 / 1.9302; IQ2_M-PL-E4K 6.690 / 1.9443; IQ2_M-PL-E4K-MIX 6.198 / 1.8465 (dla porównania stock UD-IQ3_XXS 5.736 / 1.8015). Stock UD-IQ2_M z limitem myślenia miał na egzaminie 34.5% (39.0 / 30.0).
| stock `UD-IQ3_XXS` (dla porównania) | 1 949 047 968 | — | `~/models/unsloth/Qwen3.5-4B-GGUF/` |
| stock `Q3_K_M` (obecny finał T3) | 2 293 388 448 | — | jw. |

mmproj bez zmian: `~/models/unsloth/Qwen3.5-4B-GGUF/mmproj-F16.gguf` (672 423 616 B). Lista tensorów identyczna ze stockiem (426, bez MTP).

## Przepis

1. Źródło: `unsloth/Qwen3.5-4B-GGUF/Qwen3.5-4B-BF16.gguf` (+ `imatrix_unsloth.gguf_file` do kontroli).
2. Typy per tensor skopiowane ze stockowego UD-IQ3_XXS (`tt_UD-IQ3_XXS.txt`, 248 reguł `^nazwa$=typ` dla `--tensor-type-file`; dry-run z imatrix unsloth daje bajt w bajt rozmiar stocku). Różnice względem stocku: tylko imatrix i (w E4K) typ token_embd.
3. Korpus kalibracyjny `work/calib.txt` (1.27 MB, 181 bloków × 2048 ≈ 370k tokenów):
   - 56 śladów rozumowania Qwen3.5-4B **BF16** (wygenerowanych na syntetycznych zadaniach E5, prompt jak w harnessie, szablon czatu Qwen z `<think>`);
   - ~650 KB tekstu PL: kompendium + kompendium_extra, oś czasu, postacie, pojęcia, zadania E5 z odpowiedziami.
   - Bez arkuszy 2024/2025/2026 (probe60 odrzucony — zawiera zadania z 2024).
4. imatrix: `llama-imatrix-tiedout` (llama-imatrix z łatką: przy `--process-output` zbiera też `token_embd.weight`, bo osadzenia są wiązane = głowica wyjściowa; źródło llama.cpp przywrócone, binarka osobno), `-c 2048 --parse-special --process-output`. Wynik `imatrix-pl.gguf`.
5. `llama-quantize --imatrix imatrix-pl.gguf --tensor-type-file tt_UD-IQ3_XXS.txt --token-embedding-type {q5_k|q4_k} BF16 out IQ3_XXS`.

Skrypty (repo lokalne): `overnight/quant_calib_gen.py`, `quant_calib_build.py`, `quant_t3_pipeline.sh`, `quant_t3_exam.sh`, `quant_t3_launch.sh`, `quant_t3_judge.sh`.

## Perplexity (szybki test, CPU, 4 × 2048 tokenów, zbiory odłożone)

| Model | PPL tekst hist. PL | PPL ślady rozumowania |
|---|---|---|
| stock UD-IQ3_XXS | 5.736 ± 0.218 | 1.8015 ± 0.035 |
| **IQ3_XXS-PL** | **5.597** (−2.4%) | 1.7716 (−1.7%) |
| **IQ3_XXS-PL-E4K** | 5.638 (−1.7%) | **1.7690** (−1.8%) |
| stock Q3_K_M | 5.107 ± 0.191 | 1.6991 ± 0.030 |

Różnice są systematyczne w każdym bloku, ale mieszczą się w przedziałach ±; to sanity check, nie dowód.

## Egzamin (A/B, seed 42, 2024+2025, identyczne flagi)

Serwer: `-ub 4096 -b 4096 -c 98304 -np 8 --reasoning-format deepseek --mmproj mmproj-F16 --reasoning-budget 5000 --reasoning-budget-message $'\n\nNa podstawie powyższych rozważań podaję ostateczną odpowiedź.\n'`.
Harness: `--parallel 4 --rag none --vision --think rozstrz,open,podaj,closed --temperature 0.6 --top-p 0.95 --top-k 20 --max-tokens 8000 --kb-essay data/kb/kompendium.jsonl --seed 42`.

Przebiegi (w `~/repo/runs/test202{4,5}_v2/` na L40S):
- `q35-4b-cq-stock-iq3xxs__bf5k-s42`
- `q35-4b-cq-iq3xxs-pl__bf5k-s42`
- `q35-4b-cq-iq3xxs-pl-e4k__bf5k-s42`

Start: `work/quant_t3_launch.sh` czeka, aż na L40S zwolni się VRAM (≥ 17.5 GB → stock + PL; +9 GB → E4K); nie startuje po 04:30 UTC. Log: `work/launch.out`, `work/exam_860*.out`, `~/logs/run_q35-4b-cq-*`.
Ocena lokalnie: `overnight/quant_t3_judge.sh 1.5`.

Wyniki (wszystkie przebiegi zakończone 03:57 CEST):

| Model | Rozmiar [B] | 2024 | 2025 | średnia |
|---|---|---|---|---|
| stock UD-IQ3_XXS (`q35-4b-cq-stock-iq3xxs__bf5k-s42`, L40S) | 1 949 047 968 | 42.4% | 50.0% | 46.2% |
| IQ3_XXS-PL (`q35-4b-cq-iq3xxs-pl__bf5k-s42`) | 1 949 047 904 | 40.7% | 48.3% | 44.5% |
| **IQ3_XXS-PL-E4K** (`q35-4b-cq-iq3xxs-pl-e4k__bf5k-s42`) | **1 869 585 504** | 40.7% | 46.7% | **43.7%** |
| stock UD-IQ3_XXS, drugi agent (`q35-4b-iq3xxs__nt3rb-s42`, H100, te same flagi) | 1 949 047 968 | 39.0% | 46.7% | 42.9% |

Sędzia gpt-6-luna, koszt ocen tych przebiegów ≈ $0.46. Jeden seed (42); dwa przebiegi stocku z identycznymi flagami różnią się o 3.3 pp, więc różnice PL/E4K vs stock (−1.7 / −2.5 pp) to remis w granicach szumu — imatrix PL poprawił PPL, ale nie wynik egzaminu. Wszystkie warianty z limitem myślenia są 8–11 pp nad progiem 35% (bez limitu stock IQ3_XXS miał ~36%).

Rekomendacja: najmniejszy sprawdzony plik ≥ 35% to `Qwen3.5-4B-IQ3_XXS-PL-E4K.gguf` (1 869 585 504 B) — **tylko razem z `--reasoning-budget 5000` + komunikatem**.

## Finalna konfiguracja T3 (seed 42, 04:00–04:50)

| Przebieg (finalna konfiguracja) | Rozmiar [B] | 2024 | 2025 | średnia 24+25 | 2026 | eseje (24/25/26, z 15) |
|---|---|---|---|---|---|---|
| stock UD-IQ3_XXS (dane koordynatora, 2 seedy) | 1 949 047 968 | 42.9% | 43.7% | 43.3% | 41.7% | — |
| `q35-4b-cq-iq3xxs-pl-e4k__final-s42` | 1 869 585 504 | 42.4% | 41.7% | 42.1% | 50.0% | 1 / 0 / 2 |
| `q35-4b-cq-iq3xxs-pl-e3k__final-s42` | 1 785 156 704 | 44.1% | 45.0% | 44.6% | **33.3%** | 0 / 4 / 1 |

Sędzia gpt-6-luna; koszt tej rundy ≈ $0.47 (limit $0.80). E3K 2026: bez błędów połączenia i pustych odpowiedzi; esej 397 wyrazów z nagłówkiem tematu (1/15 pkt); zad. 17 urwane i zastąpione odpowiedzią bez myślenia (818 wyrazów). Jeden seed na wariant — różnice między E3K, E4K i stockiem (±2 pp) to szum; wszystkie są wyraźnie nad 35%.

PPL E3K (GPU, 4 × 2048): 5.767 tekst PL / 1.8015 rozumowanie (E4K: 5.625 / 1.7673).

Decyzja: E3K odpada (2026: 33.3% < 35%). Finał T3 zostaje przy stockowym UD-IQ3_XXS; mniejsza opcja zapasowa to **E4K (1 869 585 504 B; 42.4 / 41.7 / 50.0%)** — przełączenie tylko za zgodą koordynatora.
