# 18 — T3 mniejszy: przycięty słownik + drobniejszy MIX (Qwen3.5-4B)

Stan: nd 27.09.2026, 07:35 CEST. Cel: zejść z Qwen3.5-4B poniżej 1.75 GB (IQ2_M-PL-E4K-MIX) przy wyniku ≥ ~40%.
`server/final_configs.json` nie był zmieniany.

## Wynik w skrócie

- **Przycięcie słownika działa i jest bezstratne**: 248 320 → 126 579 tokenów (token_embd wiązany z głowicą wyjściową, Q4_K = 1440 B/wiersz) oszczędza **181.6 MB** na każdym pliku, bez ponownej kwantyzacji (wiersze token_embd wycięte z gotowego GGUF).
  Tokenizacja identyczna na tekście odłożonym, wizja i myślenie działają, dekodowanie zachłanne daje identyczne 600 tokenów w 5/6 promptów (szósty rozjeżdża się na remisie logitów), PPL bez zmian.
- **Drobniejszy MIX**: `ssm_out` Q5_K → Q4_K (**S4K**) nie zmienia PPL (−31.5 MB). Dalsze cięcia: `attn_gate` IQ3_XXS → IQ2_S (G2) +0.3–0.8% PPL; `ffn_down` IQ3_S → IQ3_XXS (D3) i `ssm_out` IQ4_XS gorsze przy podobnym rozmiarze.
- **Kandydat: `Qwen3.5-4B-IQ2_M-PL-E4K-MIX-S4K-V124K.gguf` — 1 532 889 600 B** (−213 MB względem MIX, −416 MB względem stockowego UD-IQ3_XXS): trzy seedy (42/43/44): 2024 42.4 / 27.1 / 42.4%, 2025 48.3 / 45.0 / 41.7%, **średnio 41.2% na 2024+2025 i 42.8% na 2026** (MIX, obecny finał: 42.9% / 45.0% z dwóch seedów — remis w granicach szumu).
- Odrzucone: MIX-S4KG2-V124K (1 517 160 960 B, `attn_gate` IQ2_S) — 33.7% na 2024+2025 mimo PPL +0.3–0.8% (pętle myślenia). SIQ4/D3/S4KD3 odpadły na PPL albo były zdominowane.

## 1. Fakty o modelu (sprawdzone gguf-py)

- `tokenizer.ggml.model = gpt2` (BPE bajtowy), pre `qwen35`, 248 320 wpisów: 248 044 zwykłe + 26 dodanych (248044–248069: `<|endoftext|>`, `<|im_start|>`, `<|im_end|>`, `<|vision_*|>`, `<|image_pad|>`, `<tool_call>`, `<think>`, `</think>` …) + wypełnienie do 248 320; 247 587 reguł łączenia.
- **Osadzenia wiązane**: brak `output.weight`, `token_embd.weight` [2560 × 248 320] pełni rolę głowicy wyjściowej. W MIX: Q4_K = 357.6 MB (20% pliku) + ~11 MB metadanych tokenizera.
- Model myśli **po angielsku** (ślady w `debug.jsonl`), odpowiada po polsku — słownik musi pokrywać oba języki.

## 2. Przycięcie słownika (V124K)

Skrypty: `work/vt/` lokalnie (`count.py`, `cats.py`, `select.py`, `trim.py`, `cmp_tok.py`, `greedy_cmp.py`), na maszynach `~/models/custom/qwen35-4b/work/vt/` (L40S, H100).

1. **Częstości tokenów** (tokenizer HF `Qwen/Qwen3.5-4B`): 595 M znaków PL — baza wiedzy (kb v1–v3, kompendium, oś czasu, postacie, pojęcia, e7), `data/sft` (E5, eseje, v2/v2full/v2plain), paczki `exams/*`, **wszystkie `runs/*/debug.jsonl` i `answers.json`** (63 MB faktycznych wyjść modeli, w tym angielskie rozumowanie), 250 MB PolQA passages, ~120k artykułów Wikipedii PL — oraz 155 M znaków EN (wikitext-103 train). Widziane: 108 616 tokenów.
2. **Zbiór bazowy** `K_seen_a60k` = widziane ∪ tokeny łacińskie/ASCII/interpunkcja/greka o id < 60 000 (niskie id BPE ≈ częste) = 123 748; `trim.py` dokłada wszystkie tokeny nie-normalne (typ ≠ 1: specjalne, dodane, wypełnienie), 256 tokenów bajtowych i **domknięcie reguł łączenia** (obie części każdej reguły tworzącej zachowany token, rekurencyjnie: +2 535). Wynik: **126 579 tokenów, 126 047 reguł** (reguła zostaje, gdy obie części i wynik są zachowane; kolejność = ranga zachowana).
   Dzięki domknięciu tekst, którego oryginalna tokenizacja używa tylko zachowanych tokenów, tokenizuje się identycznie; reszta spada na krótsze tokeny/bajty (bez `<unk>`).
3. **Przebudowa GGUF** gguf-py: wszystkie metadane skopiowane, podmienione `tokens`/`token_type`/`merges`, przemapowane `eos_token_id`/`padding_token_id`; `token_embd.weight` = wybrane wiersze Q4_K (bajtowo, bez rekwantyzacji); pozostałe tensory bez zmian. ~45 s na plik.

Pokrycie (odsetek tokenów tekstu, które trafiają na token usunięty):

| Zbiór | tokeny | tekst PL odłożony (PolQA za 2.5 GB + arkusz 2026) | EN wikitext-103 test | wyjścia MIX s43 (spoza korpusu) |
|---|---|---|---|---|
| tylko skrypt (łac./ASCII/wspólne) | 161 214 | 0.002% | 0.002% | 0 |
| widziane | 108 616 | 0.007% | 0.009% | 0.012% |
| **widziane + łac. id < 60k (V124K)** | 123 748 (+domknięcie → 126 579) | **0.007%** | **0.006%** | **0.001%** |
| widziane ≥ 2 + łac. id < 40k | 103 636 | 0.020% | 0.011% | 0.014% |

(Bez korpusu EN wariant „widziane” gubił 2.1% tokenów wikitext — stąd dodany wikitext i łacińskie id < 60k.)

### Walidacja (MIX vs MIX-V124K)

| Test | Wynik |
|---|---|
| Tokenizacja llama-server `/tokenize` (598 tekstów: 400 PolQA odłożone, 185 pól arkusza 2026, EN, szablon czatu z `<think>`, `<|vision_start|><|image_pad|>`, `<tool_call>`) | wszystkie teksty z tokenami zachowanymi: **identyczne sekwencje** (396/396 PolQA, 185/185, EN 9/9, specjalne 2/2); 4 fragmenty PolQA z rzadkimi tokenami: +4 tokeny łącznie; detokenizacja = oryginał we wszystkich 598 (także cyrylica/CJK/arabski) |
| llama-server z `--mmproj mmproj-F16.gguf` | startuje; obraz 2024/1-0 rozpoznany („egipski relief”), myślenie w `reasoning_content`, odpowiedź bez `<think>` |
| Dekodowanie zachłanne (GPU, 6 promptów × 600 tokenów, rozumowanie + odpowiedź) | **5/6 identyczne co do znaku**; 1 rozjazd po 374 znakach („Describe” vs „Summarize” — remis logitów, inny kształt macierzy wyjściowej) |
| PPL CPU (4 × 2048), tekst PL / ślady rozumowania | MIX 6.198 / 1.8465 → MIX-V124K **6.154 / 1.8444** (lekki spadek: masa usuniętych tokenów renormalizowana) |
| Egzamin (esej structured, s42) | brak błędów/pustych, powtórki bez myślenia 2/1/1 (MIX: 2/0/3 i 1/3/–) |

Przycięte warianty innych plików (ta sama lista tokenów, jakość = oryginał): `Qwen3.5-4B-IQ3_XXS-PL-E4K-V124K.gguf` 1 688 025 600 B (oryginał 1.87 GB: 42.1% / 50.0%), `Qwen3.5-4B-UD-IQ3_XXS-V124K.gguf` 1 728 530 912 B (stock UD-IQ3_XXS, obecny finał: 43.3–44.5% / 41.7%; tu Q5_K = 1760 B/wiersz, −220 MB). Bez własnych przebiegów egzaminu.

## 3. Drobniejszy MIX (na bazie IQ2_M-PL-E4K-MIX, imatrix PL, token_embd Q4_K, potem V124K)

Budowa: `llama-quantize --imatrix imatrix-pl.gguf --tensor-type-file tt_mix_<v>.txt --token-embedding-type q4_k BF16 … IQ2_M` (L40S i H100 CPU), potem `trim.py`. PPL CPU, 4 × 2048 (jak raport 10c).

| Plik (V124K) | Zmiana względem MIX | Bajty | PPL tekst PL | PPL rozumowanie | Egzamin |
|---|---|---|---|---|---|
| MIX-V124K | — | 1 564 346 880 | 6.154 | 1.8444 | tak |
| **MIX-S4K-V124K** | `ssm_out` (24×) Q5_K → Q4_K | **1 532 889 600** | **6.146** | **1.8458** | tak |
| MIX-SIQ4-V124K | `ssm_out` Q5_K → IQ4_XS | 1 525 025 280 | 6.174 (+0.3%) | 1.8544 (+0.5%) | nie |
| MIX-D3-V124K | `ffn_down` 9 × IQ3_S → IQ3_XXS | 1 554 393 600 | 6.208 (+0.9%) | 1.8539 (+0.5%) | nie (większy i gorszy niż S4K) |
| MIX-S4KD3-V124K | S4K + D3 | 1 522 936 320 | 6.231 (+1.3%) | 1.8564 (+0.6%) | nie (zdominowany przez S4KG2) |
| **MIX-S4KG2-V124K** | S4K + `attn_gate` (24×) IQ3_XXS → IQ2_S | **1 517 160 960** | 6.206 (+0.8%) | 1.8493 (+0.3%) | tak |
| (MIX, bez przycięcia) | | 1 745 906 784 | 6.198 | 1.8465 | |
| (IQ2_M-PL-E4K, bez MIX) | | 1 680 534 624 | 6.690 | 1.9443 | 34.5% / 36.7% |

## 4. Egzaminy

Serwer jak finał T3 (`-ub 4096 -b 4096 --reasoning-format deepseek --reasoning-budget 5000` + komunikat, mmproj-F16, build llama.cpp 2145525 z maszyn), jeden serwer na 3 arkusze: `-np 24 -c 294912` (8 slotów i 98 304 kontekstu na arkusz, `--kv-unified`). Harness: T3 z `final_configs.json` z `--essay-mode structured` zamiast `--essay-topic-detect/--essay-extend/--essay-min-words` (jak MIX w 10c): `--parallel 8 --rag none --vision --think rozstrz,open,podaj,closed --temperature 0.6 --top-p 0.95 --top-k 20 --max-tokens 8000 --kb-essay data/kb/kompendium.jsonl --essay-mode structured`. Sędzia gpt-6-luna. Skrypty `work/vt/vt_exam.sh`, `work/vt/vt_judge.sh`.

| Model (plik, bajty) | seed | 2024 | 2025 | śr. 24+25 | 2026 | powtórki bez myślenia (24/25/26) | Przebieg |
|---|---|---|---|---|---|---|---|
| **MIX-S4K-V124K** (1 532 889 600) | 42 | 42.4% | 48.3% | **45.4%** | 45.0% | 3 / 1 / 3 | `q35-4b-vt-mix-s4k-v124k__struct2-s42` |
| | 43 | 27.1% | 45.0% | 36.1% | 40.0% | 3 / 1 / 4 | `…-s43` |
| | 44 | 42.4% | 41.7% | 42.1% | 43.3% | 2 / 1 / 1 | `…-s44` (H100) |
| | **średnio** | 37.3% | 45.0% | **41.2%** | **42.8%** | | |
| MIX-V124K (1 564 346 880) | 42 | 35.6% | 41.7% | 38.6% | 43.3% | 2 / 1 / 1 | `q35-4b-vt-mix-v124k__struct2-s42` |
| | 43 | 40.7% | 40.0% | 40.4% | — | 4 / 1 / – | `…-s43` |
| MIX-S4KG2-V124K (1 517 160 960) | 42 | 37.3% | 30.0% | **33.7%** ✗ | 40.0% | 5 / 6 / 6 | `q35-4b-vt-mix-s4kg2-v124k__struct2-s42` (H100) |
| (MIX, bez przycięcia, 1 745 906 784; raport 10c / drugi agent) | 42 | 42.4% | 40.0% | 41.2% | 45.0% | 2 / 0 / 3 | `q35-4b-q2-iq2mpl-e4k-mix__struct2-s42` |
| | 43 | 49.2% | 40.0% | 44.6% | 46.7% | 1 / 3 / – | `…-s43`, `…-s43-2026-fh` |

Obserwacje:
- **Przycięcie jest neutralne**, różnice to szum próbkowania: dekodowanie zachłanne MIX vs MIX-V124K identyczne na 5/6 promptach tekstowych (600 tokenów) i **3/3 promptach z obrazami z arkusza 2024** (400 tokenów, identyczna liczba tokenów promptu), a przegrane zadania to zwykłe błędy wiedzy („Juliusz Cezar” zamiast Oktawiana, „Habsburgowie”/„Bonaparte” zamiast Hohenzollernów) — bez artefaktów tokenizacji (0 znaków zastępczych/CJK w wyjściach).
  Mimo to średnia przyciętej rodziny jest niższa niż MIX (24+25: MIX 42.9% z 2 seedów vs V124K 39.5% i S4K-V124K 41.2%) — przy rozrzucie arkusza 2024 w tej rodzinie **27.1–49.2%** to ~1 odchylenie standardowe, nie dowód.
- **Rozrzut pojedynczego arkusza jest duży** dla 2-bitowego 4B: 17 arkuszy rodziny MIX (MIX, MIX-V124K, MIX-S4K-V124K) daje średnio ~42% przy odchyleniu ~5 pp; 1 z 17 (S4K s43, 2024: 27.1%) spadł poniżej 35%.
- **PPL nie wyłapuje szkód w rozumowaniu**: S4KG2 (`attn_gate` → IQ2_S) ma PPL +0.3–0.8%, ale 2× więcej powtórek bez myślenia (pętle, jak czysty E4K) i 33.7% na 24+25. Ekranowanie PPL wystarcza do odrzucenia, nie do akceptacji.

## 5. Rekomendacja

- **Najlepszy kandydat: `Qwen3.5-4B-IQ2_M-PL-E4K-MIX-S4K-V124K.gguf` — 1 532 889 600 B**, sha256 `2f2a141a41190092e97a8feeb6a54eccb8721a6851de3b5b8e7ea8057083b1f6`, na L40S i H100 (sumy zgodne). Spełnia kryteria (≥ 40% na 24+25, ≥ 38% na 2026): **41.2% / 42.8%** (3 seedy). −213 MB względem obecnego finału MIX (1 745 906 784 B), −416 MB względem stockowego UD-IQ3_XXS.
  - podmiana w `final_configs.json` T3 tylko ścieżki `-m`: `-m models/custom/qwen35-4b/Qwen3.5-4B-IQ2_M-PL-E4K-MIX-S4K-V124K.gguf` (mmproj, flagi serwera i harness z `--essay-mode structured` bez zmian — tak był mierzony).
  - Wszystkie przebiegi szły na buildzie llama.cpp z maszyn (2145525), `--reasoning-budget-message` działa.
- Ryzyko: **średnie**. Jakość ≈ MIX (przycięcie dowodowo neutralne, `ssm_out` Q4_K neutralne w PPL), ale rodzina MIX ma duży rozrzut pojedynczego arkusza (~5 pp; 1 z 17 arkuszy < 35%: 27.1%). Ten sam rozrzut dotyczy obecnego finału MIX — plik mniejszy nie dokłada ryzyka w granicach pomiaru.
- Bezpieczniejsze, ale większe opcje z tym samym przycięciem (jakość = oryginał, bez własnych egzaminów): `Qwen3.5-4B-IQ3_XXS-PL-E4K-V124K.gguf` 1 688 025 600 B (oryg. 42.1% / 50.0%, 1 seed) i `Qwen3.5-4B-UD-IQ3_XXS-V124K.gguf` 1 728 530 912 B (stock UD-IQ3_XXS: 43.3–44.5% / 41.7%) — oba mniejsze niż obecny MIX; na razie tylko na L40S.
- Nie robić: dalszych cięć IQ3_XXS → IQ2 (S4KG2 pokazuje, że PPL tego nie wyłapie).

## Pliki i koszty

Na **L40S i H100** w `~/models/custom/qwen35-4b/` (sumy `vt124k.sha256`, README uzupełnione):

| Plik | Bajty | sha256 |
|---|---|---|
| `Qwen3.5-4B-IQ2_M-PL-E4K-MIX-S4K-V124K.gguf` | 1 532 889 600 | 2f2a141a41190092e97a8feeb6a54eccb8721a6851de3b5b8e7ea8057083b1f6 |
| `Qwen3.5-4B-IQ2_M-PL-E4K-MIX-S4KG2-V124K.gguf` | 1 517 160 960 | 016deb66fba344f7e48850503926bb4fc4771c39b2ad49ac803415c517725d69 |
| `Qwen3.5-4B-IQ2_M-PL-E4K-MIX-V124K.gguf` | 1 564 346 880 | 1c83459dfe4632bde40c41d3fbaf287f57d8cf947b5f7042612a4f740bbd9bda |
| `Qwen3.5-4B-IQ3_XXS-PL-E4K-V124K.gguf` (tylko L40S) | 1 688 025 600 | 48ae44540defdd0c8d37294e14700cb90dcd05ee7df3319c692d03c4e83fcd93 |
| `Qwen3.5-4B-UD-IQ3_XXS-V124K.gguf` (tylko L40S) | 1 728 530 912 | 6f35ef3db28288fb85e3005917805a9e4bfd6bffacf25794a8fbfbe5ee9d2645 |

Pozostałe (SIQ4, D3, S4KD3) tylko na H100. mmproj bez zmian: `models/unsloth/Qwen3.5-4B-GGUF/mmproj-F16.gguf` (672 423 616 B, mniejszy od modelu).
Lista zachowanych starych id obok każdego pliku (`*.gguf.oldids.txt`). Na H100 dobudowany `llama-perplexity` (tylko nowy cel, reszta binarek bez zmian) i kopia BF16 w `work/vt/` (8.4 GB, do usunięcia po egzaminie).

Koszt sędziego gpt-6-luna: ≈ **$1.32** (8 przebiegów × 3 arkusze + 1 × 2 arkusze; limit $1.50). Modal nieużywany.

## 6. Dalsze cięcie słownika według częstości (27.09, 08:35–09:25)

Pytanie: ile słownika da się jeszcze usunąć ponad V124K (która zachowała każdy token widziany w korpusie)? Arytmetyka: w S4K-V124K token_embd = 126 579 × 1440 B ≈ 182 MB; każde 10k wierszy Q4_K ≈ 14.4 MB, więc zejście do 40k daje ≈ −125 MB, a teoretyczny sufit (cały token_embd) ≈ −182 MB.

Ranking: `score = f_PL + f_myślenie + 0.25·f_EN`. f_PL to częstości z korpusu PL z §2 (595 M znaków). f_myślenie to nowe częstości z pól `reasoning` wszystkich `runs/*/debug.jsonl` oprócz przebiegów `q35-4b-vt-*` (38 M znaków; te przebiegi są zbiorem odłożonym). f_EN to wikitext. Brano top-N zwykłych tokenów, do tego tokeny specjalne/bajtowe/myślenia/wizji i domknięcie BPE (`work/vt/K_top64k.txt`, `K_top40k.txt`). Wiersze wycięto z pełnego pliku S4K (ten sam `trim.py`).

| Wariant | tokeny | Bajty | vs S4K-V124K | inflacja: PolQA odłożone / arkusz 2026* / myślenie EN (odłożone) | PPL tekst PL / rozumowanie | zachłanne 9 promptów (6 tekst + 3 obraz) |
|---|---|---|---|---|---|---|
| S4K-V124K (finał T3) | 126 579 | 1 532 889 600 | — | 332.7 / 354.6 / 316.8 tok/1k znaków | 6.146 / 1.8458 | — |
| **S4K-T64K** | 63 990 | **1 440 305 600** | −92.6 MB | +0.23% / +0.02% / +0.02% | 6.117 (−0.5%) / 1.8422 (−0.2%) | 6/9 identyczne (tekst 4/6, obraz 2/3) |
| **S4K-T40K** | 39 980 | **1 404 879 328** | −128.0 MB | +1.24% / +0.12% / +0.10% | 6.092 (−0.9%) / 1.8530 (+0.4%) | 4/9 identyczne (tekst 3/6, obraz 1/3) |

\* Arkusz 2026 był w korpusie częstości, więc uczciwą miarą dla polskiego jest PolQA odłożone.
Część rozjazdów przy zachłannym dekodowaniu to remisy logitów (V124K vs MIX też miał 1/9). W T40K widać też prawdziwy efekt słownika: „Preußen” → „Preussen”, bo token „ß” został usunięty.
PPL na tekście, który tokenizuje się inaczej, nie jest ściśle porównywalna, bo zmienia się liczba tokenów. Obie wartości mieszczą się w 1%.

Egzamin: tylko najmniejszy wariant spełniający kryteria ekranu (T40K). Harness T3 z aktualnego `final_configs.json` (z `--think-retry --match-retry`), 3 arkusze na jednym serwerze `-np 24 -c 294912`. Seed 42 na Nebius L40S (build 2145525). Seed 43 na Forgehand L40S (build 2145525, `--cache-ram 4096`, harness zsynchronizowany z laptopa). **Brak restartów nadzorcy i awarii CUDA** na obu serwerach, 0 błędów.

| S4K-T40K (1 404 879 328 B) | 2024 | 2025 | śr. 24+25 | 2026 | zamknięte 24+25 | Przebieg |
|---|---|---|---|---|---|---|
| seed 42 (Nebius) | 39.0% | 30.0% | 34.5% | 51.7% | 6/20 | `q35-4b-vt-mix-s4k-t40k__struct2-s42` |
| seed 43 (Forgehand) | 35.6% | 40.0% | 37.8% | 38.3% | 7/20 | `…-s43` |
| **średnio** | 37.3% | 35.0% | **36.2%** ✗ | 45.0% | 32.5% | |
| (S4K-V124K, 3 seedy, bez retry) | 37.3% | 45.0% | 41.2% | 42.8% | 32/60 = 53% | §4 |

Wnioski:
- **T40K odpada** (36.2% < 40% na 2024+2025). Spadek dotyczy głównie zadań zamkniętych (32.5% vs 53% w V124K). Wskazuje to na realną szkodę agresywnego cięcia, a nie tylko szum. Przy 2 seedach nie jest to rozstrzygające, ale nie ma podstaw do zmiany finału.
- T64K (−92.6 MB) przeszedł ekran z mniejszym marginesem ryzyka (6/9 zachłannych identycznych, inflacja ≤ 0.23%), ale **nie był egzaminowany** (brak czasu i budżetu sędziego). Jest na L40S, sha256 `dfc99b4924c532838ce4565f99b1d6f0101984c3e6f491bb6358d243f281014e`.
- **Rekomendacja: zostać przy S4K-V124K (1 532 889 600 B).** Plik T40K (sha256 `48d20bcfd1c05b2d24fd11a9b7d1c673b0fe0fdf8ea93c33df403c3b5bebfb49`) jest na obu maszynach Nebius i na Forgehand, ale nie nadaje się do finału.
- Koszt sędziego tej rundy: ≈ $0.45 (limit $0.80).

## 7. Egzamin S4K-T64K (27.09, 09:00–09:30)

Konfiguracja taka sama jak dla T40K w §6: harness T3 z `--think-retry --match-retry`, harness na maszynach bez zmian, 3 arkusze na jednym serwerze `-np 24 -c 294912`, do tego `GGML_CUDA_DISABLE_GRAPHS=1`. Seed 42 szedł na Nebius L40S, seed 43 na Forgehand L40S; sha256 pliku sprawdzone na Forgehand. **0 restartów nadzorcy, 0 błędów CUDA i 0 błędów harnessu.** Czas: 11–13.5 min na arkusz (Nebius) i 14.5–15.5 min (Forgehand), wszystkie arkusze równolegle.

| S4K-T64K (1 440 305 600 B) | 2024 | 2025 | śr. 24+25 | 2026 | zamknięte 24+25 | powtórki bez myślenia (24/25/26) |
|---|---|---|---|---|---|---|
| seed 42 (Nebius) | 40.7% | 45.0% | 42.9% | 51.7% | 12/20 | 1 / 0 / 0 |
| seed 43 (Forgehand) | 42.4% | 38.3% | 40.4% | 38.3% | 12/20 | 1 / 1 / 0 |
| **średnio** | 41.6% | 41.7% | **41.6%** ✓ | **45.0%** ✓ | **60%** ✓ | |
| (S4K-V124K, 3 seedy, bez retry) | 37.3% | 45.0% | 41.2% | 42.8% | 53% | |
| (S4K-T40K, 2 seedy, z retry) | 37.3% | 35.0% | 36.2% ✗ | 45.0% | 32.5% | |

Wniosek: **T64K spełnia regułę decyzji**: ≥ 40% na 2024+2025, ≥ 38% na 2026, a zamknięte nie są gorsze niż w V124K. Plik jest o **92.6 MB mniejszy** od finału (1 440 305 600 vs 1 532 889 600 B). Plik `models/custom/qwen35-4b/Qwen3.5-4B-IQ2_M-PL-E4K-MIX-S4K-T64K.gguf`, sha256 `dfc99b4924c532838ce4565f99b1d6f0101984c3e6f491bb6358d243f281014e`, jest na obu maszynach Nebius i na Forgehand.
Zastrzeżenia:
- Tylko 2 seedy, a najsłabszy arkusz ma 38.3%.
- T64K jechał z `--think-retry --match-retry`, a V124K bez nich, więc porównanie z V124K nie jest czyste.
- Na H100 T64K nie był testowany (zakaz; tam trwa diagnoza awarii CUDA przy obrazach).

Decyzja o przełączeniu należy do użytkownika; `final_configs.json` nie był zmieniany. Koszt sędziego: ≈ $0.45 (limit $0.50).
