# 10b — Własne kwantyzacje Qwen3.5-4B dla T3 (imatrix PL)

Stan: nd 27.09.2026, ~04:55 CEST. Cel: mniejszy plik niż obecny finał T3 (Q3_K_M, 2.29 GB) przy wyniku ≥ 35%.

## Wynik w skrócie

- Zbudowane dwa warianty, oba z przepisem UD-IQ3_XXS unsloth skopiowanym 1:1 (typ każdego tensora), różnią się od stocku tylko imatrixem i typem osadzeń:
  - `Qwen3.5-4B-IQ3_XXS-PL.gguf` — **1 949 047 904 B** (token_embd Q5_K, jak stock);
  - `Qwen3.5-4B-IQ3_XXS-PL-E4K.gguf` — **1 869 585 504 B** (token_embd Q4_K; −79.5 MB względem stocku UD-IQ3_XXS, −424 MB względem Q3_K_M).
- Perplexity (szybki test): oba warianty lepsze od stocku UD-IQ3_XXS na tekście historycznym PL (−2.4% / −1.7%) i na śladach rozumowania (−1.7% / −1.8%). Obniżenie osadzeń do Q4_K kosztuje ~0.7% PPL na tekście PL, na rozumowaniu nic.
- **Egzamin (seed 42, 2024+2025, sędzia luna)**: stock UD-IQ3_XXS 46.2%, IQ3_XXS-PL 44.5%, **IQ3_XXS-PL-E4K 43.7%** (40.7% / 46.7%). Różnice względem stocku mieszczą się w szumie (dwa stocki z tymi samymi flagami: 46.2% i 42.9%). Imatrix PL poprawia PPL, ale nie wynik; zysk E4K to wyłącznie −79.5 MB przy zachowanym marginesie ~9 pp nad progiem.

## Przepis

1. Źródło: `unsloth/Qwen3.5-4B-GGUF` → `Qwen3.5-4B-BF16.gguf` (bez konwersji z HF; lista 426 tensorów identyczna ze stockiem, bez MTP i wizji).
2. Przepis UD: typy per tensor odczytane z `Qwen3.5-4B-UD-IQ3_XXS.gguf` (gguf-py) → plik `--tensor-type-file` z 248 regułami `^blk\.N\.nazwa$=typ`. Kontrola: dry-run z imatrixem unsloth daje dokładnie rozmiar stocku.
   - Stock UD-IQ3_XXS: FFN i attn_qkv/gate IQ3_XXS, ffn_down w 5 warstwach IQ4_XS, attn_q/k w 5 z 8 warstw uwagi IQ2_S, attn_v/attn_output IQ3_S, ssm_out Q6_K, ssm_alpha/beta F16, token_embd Q5_K (0.437 GB = 22% pliku).
3. Korpus kalibracyjny (~370k tokenów, 181 bloków × 2048):
   - 56 śladów rozumowania wygenerowanych przez **BF16** Qwen3.5-4B na syntetycznych zadaniach E5 (prompt systemowy i treść zadania jak w harnessie, myślenie włączone; zapis w szablonie czatu Qwen z `<think>`); ciekawostka: nawet BF16 przy limicie 3000 tokenów urywał myślenie w ~70% zadań — pętle nie są wyłącznie efektem kwantyzacji;
   - ~650 KB tekstu PL: kompendium + kompendium_extra, oś czasu, postacie, pojęcia, zadania E5 z wzorcowymi odpowiedziami.
   - Wykluczone: arkusze 2024/2025/2026, a także `probe60_v2` (zawiera zadania z arkusza 2024).
   - Odłożone do perplexity: 10% dokumentów kompendium + 1/12 osi czasu, postaci i pojęć (`ppl_pl.txt`), 9 śladów rozumowania (`ppl_reason.txt`).
4. imatrix na BF16 (`-c 2048 --parse-special --process-output`). Osadzenia są wiązane (token_embd = głowica wyjściowa), a stockowy `llama-imatrix` zbiera dane tylko dla `output.weight`; jednolinijkowa łatka w narzędziu (osobna binarka `llama-imatrix-tiedout`, źródło llama.cpp przywrócone, `llama-server` nietknięty) dodaje `token_embd.weight`. Dzięki temu Q4_K osadzeń jest kwantyzowane z wagami ważności (imatrix unsloth nie ma wpisu dla token_embd).
5. `llama-quantize --imatrix imatrix-pl.gguf --tensor-type-file tt_UD-IQ3_XXS.txt --token-embedding-type {q5_k|q4_k} … IQ3_XXS`.

## Perplexity (CPU, 4 × 2048 tokenów na zbiór; GPU był zajęty)

| Model | Rozmiar [B] | PPL tekst hist. PL | PPL ślady rozumowania |
|---|---|---|---|
| stock UD-IQ3_XXS | 1 949 047 968 | 5.736 ± 0.218 | 1.8015 ± 0.035 |
| IQ3_XXS-PL | 1 949 047 904 | **5.597** | 1.7716 |
| IQ3_XXS-PL-E4K | 1 869 585 504 | 5.638 | **1.7690** |
| stock Q3_K_M (finał T3) | 2 293 388 448 | 5.107 ± 0.191 | 1.6991 ± 0.030 |

Nasz imatrix zamyka ok. 22% (tekst PL) i 29% (rozumowanie) luki PPL między stockowym UD-IQ3_XXS a Q3_K_M. Poprawa jest widoczna w każdym z 4 bloków osobno, ale mieści się w przedziałach ± — traktować jako sanity check. KL-dywergencji względem BF16 nie policzono (brak VRAM).

## Egzamin

Sparowany A/B (seed 42, 2024+2025, identyczne flagi jak `server/nt_t3_wave1.sh`: `-c 98304 -np 8 -ub 4096`, mmproj-F16, `--reasoning-budget 5000` + komunikat; harness T3 temp 0.6, `--max-tokens 8000`, `--kb-essay`):
- `q35-4b-cq-stock-iq3xxs__bf5k-s42`, `q35-4b-cq-iq3xxs-pl__bf5k-s42`, `q35-4b-cq-iq3xxs-pl-e4k__bf5k-s42`.

`quant_t3_launch.sh` na L40S czeka na wolny VRAM (≥ 26 GB → wszystkie trzy; ≥ 17.5 GB → stock + PL, potem E4K) i nie startuje po 06:30 CEST. Ocena: `overnight/quant_t3_judge.sh 1.5` (pobiera przebiegi, `to_results`, `grade`, sędzia luna z limitem $1.50). Przebiegi ruszyły po zwolnieniu VRAM (E4K 03:21, stock 03:25, PL 03:27; ~28 min na arkusz) i skończyły się 03:57.

| Model | Rozmiar [B] | 2024 | 2025 | średnia |
|---|---|---|---|---|
| stock UD-IQ3_XXS (`q35-4b-cq-stock-iq3xxs__bf5k-s42`, L40S) | 1 949 047 968 | 42.4% | 50.0% | 46.2% |
| IQ3_XXS-PL (`q35-4b-cq-iq3xxs-pl__bf5k-s42`) | 1 949 047 904 | 40.7% | 48.3% | 44.5% |
| **IQ3_XXS-PL-E4K** (`q35-4b-cq-iq3xxs-pl-e4k__bf5k-s42`) | **1 869 585 504** | 40.7% | 46.7% | **43.7%** |
| stock UD-IQ3_XXS, drugi agent (`q35-4b-iq3xxs__nt3rb-s42`, H100, te same flagi) | 1 949 047 968 | 39.0% | 46.7% | 42.9% |

Sędzia gpt-6-luna, koszt ocen tych przebiegów ≈ $0.46. Jeden seed (42); dwa przebiegi stocku z identycznymi flagami różnią się o 3.3 pp, więc różnice PL/E4K vs stock (−1.7 / −2.5 pp) to remis w granicach szumu — imatrix PL poprawił PPL, ale nie wynik egzaminu. Wszystkie warianty z limitem myślenia są 8–11 pp nad progiem 35% (bez limitu stock IQ3_XXS miał ~36%).

## Potwierdzenie w finalnej konfiguracji T3 (04:00–04:50)

Konfiguracja jak w `server/final_configs.json` (T3 tuned) z podmienionym plikiem modelu: `-c 98304 -np 8 -ub 4096 --reasoning-budget 5000` + komunikat, harness `--parallel 8 … --essay-topic-detect --essay-extend 2 --essay-min-words 300`. Skrypt `overnight/quant_t3_final.sh`. Seed 43 pominięty (priorytet czasu).

Nowy wariant **`Qwen3.5-4B-IQ3_XXS-PL-E3K.gguf` — 1 785 156 704 B** (token_embd Q3_K, sha256 fdfb3283…; −84.4 MB względem E4K, −163.9 MB względem stocku UD-IQ3_XXS).
PPL (GPU, 4 × 2048): E3K 5.767 (tekst PL) / 1.8015 (rozumowanie) vs E4K 5.625 / 1.7673 → +2.5% / +1.9%, czyli poziom stocku UD-IQ3_XXS; próg odrzucenia (+10%) daleko.

| Przebieg (finalna konfiguracja) | Rozmiar [B] | 2024 | 2025 | średnia 24+25 | 2026 | eseje (24/25/26, z 15) |
|---|---|---|---|---|---|---|
| stock UD-IQ3_XXS (dane koordynatora, 2 seedy) | 1 949 047 968 | 42.9% | 43.7% | 43.3% | 41.7% | — |
| `q35-4b-cq-iq3xxs-pl-e4k__final-s42` | 1 869 585 504 | 42.4% | 41.7% | 42.1% | 50.0% | 1 / 0 / 2 |
| `q35-4b-cq-iq3xxs-pl-e3k__final-s42` | 1 785 156 704 | 44.1% | 45.0% | 44.6% | **33.3%** | 0 / 4 / 1 |

Sędzia gpt-6-luna; koszt tej rundy ≈ $0.47 (limit $0.80). E3K 2026: bez błędów połączenia i pustych odpowiedzi; esej 397 wyrazów z nagłówkiem tematu (1/15 pkt); zad. 17 urwane i zastąpione odpowiedzią bez myślenia (818 wyrazów). Jeden seed na wariant — różnice między E3K, E4K i stockiem (±2 pp) to szum; wszystkie są wyraźnie nad 35%.

## Rekomendacja i ryzyko

- **E3K odrzucony**: 44.6% na 2024+2025, ale **33.3% na 2026** (poniżej progu 35%, a przyjęty próg przełączenia to 38%). Obniżenie osadzeń do Q3_K widać dopiero na trzecim arkuszu — PPL (+2%) tego nie zapowiadało.
- **Finał T3 bez zmian**: stockowy UD-IQ3_XXS (1 949 047 968 B; 43.3% na 2024+2025 przy 2 seedach, 41.7% na 2026). `server/final_configs.json` nie był zmieniany.
- **Mniejsza opcja zapasowa: E4K** (`~/models/custom/qwen35-4b/Qwen3.5-4B-IQ3_XXS-PL-E4K.gguf`, 1 869 585 504 B; −79.5 MB): 42.4 / 41.7 / 50.0% w finalnej konfiguracji (seed 42). Przełączenie tylko decyzją koordynatora; ryzyko średnie (jeden seed, margines ~7 pp na najsłabszym arkuszu).
- Warunek konieczny dla wszystkich wariantów IQ3_XXS: `--reasoning-budget 5000` + komunikat. Pliki IQ2_M-PL innego agenta (1.68–1.76 GB) nie mają wyników egzaminu; stock UD-IQ2_M miał 34.5%.

## Pliki

- L40S i H100: `~/models/custom/qwen35-4b/` (GGUF PL, PL-E4K, PL-E3K, IQ2_M-PL* innego agenta, `imatrix-pl.gguf`, `tt_UD-IQ3_XXS.txt`, README.md, READY); na L40S także `work/` (korpus, ślady, logi).
- Repo lokalne: `overnight/quant_calib_gen.py`, `quant_calib_build.py`, `quant_t3_pipeline.sh`, `quant_t3_exam.sh`, `quant_t3_launch.sh`, `quant_t3_judge.sh`, `quant_t3_final.sh`, `quant_t3_README.md`.
