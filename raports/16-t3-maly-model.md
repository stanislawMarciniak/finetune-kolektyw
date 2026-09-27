# 16 — T3 z modelem < 0.97 GB (odpowiedź na fabryka.ai)

Stan: nd 27.09.2026, 06:40 CEST. Cel: rozwiązanie T3, w którym **każdy** plik modelu jest < 0.97 GB (najlepiej ≤ 0.9 GB), z wynikiem ≥ 35% i zapasem. `server/final_configs.json` **nie był zmieniany**.

## Wynik w skrócie

- **Nie ma kandydata < 0.97 GB bliskiego 35%.** Najlepszy mały wariant (nasz Qwen3.5-2B-IQ3_XXS-PL-E4K-MIX, 935 MB) ma 16.9% / 20.0% na 2024 / 2025. Bielik-1.5B (goły) 8.5% / 26.7%. Qwen3.5-2B UD-IQ2_M 5.1% / 10.0%. Do progu brakuje ≥ 15 pp, więc zgodnie z regułą (kontynuować tylko od ≥ 35% na 2024+2025) nie było potwierdzeń na 2026, drugiego seeda ani treningu Bielika.
- **Zagrożenie ze strony fabryka.ai jest niskie.** Ich model (SlayerLab `bielik-1.5b-v3-matura-history-sft2`, publiczny) ma u nas **13.3–16.7% na czystym arkuszu 2026**. Na 2024/2025 ma 19–30%, choć był trenowany na zadaniach z tych arkuszy. Ich własna karta modelu podaje 19/60 (31.7%) na CKE maj 2026. 36.67% na mocku to arkusz 2023, a na zadaniach z CKE 2023 zbudowany jest ich ewaluator.
- **Rekomendacja: T3 bez zmian** — UD-IQ3_XXS 1.95 GB, ~44% (albo wariant 4B, który wybierze koordynator na podstawie raportu 10c). Nie ma gotowego bloku konfiguracji dla modelu < 0.97 GB, bo żaden nie jest realnym kandydatem.
- Koszt: sędzia luna ≈ **$1.22** (limit $2.50), Modal **$0**.

## 1. Zagrożenie: fabryka.ai / SlayerLab `bielik-1.5b-v3-matura-history-sft2`

Model jest publiczny na HF (Apache-2.0). To pełne SFT Bielik-1.5B-v3.0-Instruct: 3 epoki, lr 1e-5, 17 min na L40S, 4 144 przykładów. Dane: 2 714 syntetycznych zadań, 300 esejów wzorcowych (×2), 800 zadań uzupełniających i **82 zadania z arkuszy CKE maj 2024 i 2025 (×2)**; 66% promptów ma 0–2 fragmenty plwiki. Pliki GGUF (imatrix PL):

| Plik | Bajty | Uwagi z karty |
|---|---|---|
| `sft2-Q4_K_M.gguf` | 972 797 184 | zgłoszony przez fabryka.ai |
| `sft2-IQ4_XS.gguf` | **868 041 888** | „registered candidate”, PPL ≈ Q8_0 |
| `sft2-Q3_K_M.gguf` | 782 735 520 | u nich odpada |
| `sft2-IQ3_M.gguf` | 728 017 056 | u nich odpada |
| `sft2-IQ3_XXS.gguf` | 632 585 376 | — |

Z karty modelu. Ich ewaluator: 34 zadania zaadaptowane z **CKE maj 2023** (czyli z arkusza mocka) + 34 zadania z Wikipedii; sędzia gemini-3.1-flash-lite.
- IQ4_XS z ich harnessem: 23/55 (41.8%) na „past exam” (2023), **19/60 (31.7%) na CKE maj 2026**.
- Sami piszą, że na arkuszu 2026 każdy wariant 1.5B, łącznie z gołą bazą, ląduje na 19–21/60 („right at the 35% line”), a zysk z SFT widać tylko na arkuszu ewaluatora.
- Harness v5: BM25 plwiki (2 × 700 znaków) dla krótkich zadań i esejów, normalizacja zamkniętych, próg 380 słów w eseju, DRY sampling.

Nasz pomiar: sędzia luna, tylko tekst, temp 0, jeden przebieg. Arkusze 2024 i 2025 są dla tego modelu **skażone** (były w jego danych treningowych).

| Przebieg | Plik [B] | 2024 | 2025 | 2026 (czysty) |
|---|---|---|---|---|
| `slayer-sft2-iq4xs__bare` (goły prompt, `--bare`) | 868 041 888 | 20.3% | 30.0% | **13.3%** |
| `slayer-sft2-iq4xs__t2h` (nasz harness T2: BM25 PolQA top-3 + 1 notatka KB, `--kb-essay`, OCR tesseract) | 868 041 888 | 18.6% | 26.7% | **16.7%** |
| `bielik-1.5b-q4km__t2h` (goła baza Bielik-1.5B-v3.0-Instruct, nasz Q4_K_M bez imatrix, harness jak wyżej) | 972 797 600 | 8.5% | 26.7% | — |

Pełnego pipeline'u fabryki nie odtwarzaliśmy (opisy obrazów Qwen3.5-0.8B + tłumaczenie BiDi + ich RAG plwiki). Zadania z obrazami to kilka punktów na arkusz, nie 20 pp. Goły Bielik-1.5B Q8_0 miał na mocku u organizatorów 18.33%, co zgadza się z naszymi 8–27%.

**Ocena:** na świeżym arkuszu fabryka.ai powinna wylądować w okolicach 15–30%. Przekroczenie 35% jest możliwe tylko wtedy, gdy finał jest bardzo podobny do arkusza 2023 albo sędzia organizatorów jest wyraźnie łagodniejszy od luny. Tego drugiego nie wiemy (H-N14 — nie wgraliśmy mocka).

## 2. Nasza mała ścieżka (każdy plik < 0.97 GB)

Wspólne ustawienia dla Qwen3.5-2B: serwer jak finał T3 (`-ub 4096 -b 4096 -c 131072 -np 8 --reasoning-format deepseek --reasoning-budget 5000` + `reasoning_budget_message`), mmproj Qwen3.5-2B F16 (668 227 264 B — mniejszy od każdego pliku modelu). Harness T3: `--parallel 8 --rag none --vision --think rozstrz,open,podaj,closed --temperature 0.6 --top-p 0.95 --top-k 20 --max-tokens 8000 --kb-essay data/kb/kompendium.jsonl --essay-mode structured`. Seed 42.

| Model | Plik [B] | 2024 | 2025 | powtórki bez myślenia (24/25) | Przebieg |
|---|---|---|---|---|---|
| Qwen3.5-2B UD-IQ3_XXS (stock unsloth) | 931 823 872 | 6.8% | 21.7% | 18 / 18 | `q35-2b-iq3xxs__t3s-s42` |
| **Qwen3.5-2B-IQ3_XXS-PL-E4K-MIX** (nasz) | 935 453 952 | **16.9%** | 20.0% | 15 / 7 | `q35-2b-iq3xxs-pl-e4k-mix__t3s-s42` |
| Qwen3.5-2B-IQ3_XXS-PL-E4K (nasz) | **866 346 240** | 6.8% | 10.0% | 15 / 10 | `q35-2b-iq3xxs-pl-e4k__t3s-s42` |
| Qwen3.5-2B UD-IQ2_M (stock) | 859 857 152 | 5.1% | 10.0% | 28 / 25 | `q35-2b-iq2m__t3s-s42` (L40S) |
| Bielik-1.5B-v3.0-Instruct Q4_K_M (harness T2 + RAG + OCR) | 972 797 600 | 8.5% | 26.7% | — | `bielik-1.5b-q4km__t2h` (L40S) |
| _dla skali: Qwen3.5-2B Q4_K_M, stara konfiguracja T3 (1.28 GB)_ | 1 280 835 840 | 22.0% | 13.3% | 14 / — | `q35-2b-q4__t3cfg` |

- Własne kwantyzacje 2B: imatrix na tym samym korpusie PL + śladach rozumowania co w raporcie 10b (`llama-imatrix-tiedout`, więc z wpisem dla token_embd) i przepis UD-IQ3_XXS unsloth 1:1 (150 reguł). `-PL-E4K` ma osadzenia Q4_K (osadzenia to 350 MB = 37% pliku 2B), a `-PL-E4K-MIX` dodatkowo ffn_down i attn_qkv w IQ4_XS zamiast IQ3_XXS (37 tensorów). Imatrix PL i MIX zmniejszają liczbę pętli myślenia, ale nie ratują wiedzy.
- Odpowiedzi 2B w 3 bitach to zepsuta polszczyzna i zmyślenia („Rozstrzydnie”, „Augustyn Roussea”, „Konstancjanie”). To nie błąd harnessu. Eseje 0/15 we wszystkich wariantach.
- **Niezrobione (świadomie):** RAG dla 2B (przebieg `t3srag` został przerwany, patrz niżej; historycznie 2B Q4 z RAG miał 20–25%), 2B bez myślenia, Qwen3.5-0.8B, LoRA/SFT Bielika-1.5B. Nasze wcześniejsze SFT Bielika-1.5B pogorszyło wynik (13–27%), a pełne SFT SlayerLab daje u nas 13–17% na 2026. Przy luce ≥ 15 pp żadna z tych dróg nie dawała realnej szansy przed 11:00.
- Qwen3.5-4B nie mieści się w 0.97 GB nawet w IQ1 (same osadzenia 4B to ~0.44 GB w Q5_K).

## 3. Rekomendacja

- **T3 zostaje przy Qwen3.5-4B** (UD-IQ3_XXS 1 949 047 968 B albo mniejszy wariant 4B z raportu 10b/10c według decyzji koordynatora). Model < 0.97 GB z wynikiem 17–27% oznaczałby pewną utratę kategorii.
- Jeśli fabryka.ai przejdzie 35% w finale, wygra T3 plikiem 0.97 GB (albo 0.87 GB). Nasza odpowiedź na to to wyłącznie mniejszy plik 4B (1.75–1.87 GB), nie model < 1 GB.

## 4. Przebieg pracy i incydenty

- L40S (05:20–05:55): Bielik, SlayerLab i Qwen3.5-2B IQ2_M skończone. Maszynę przeciążyły serwery innego agenta (m.in. llama-server na CPU `-ngl 0`, przebiegi `q35-4b-vt-mix-v124k`): 4 GB wolnej RAM, load 24 na 16 rdzeni, generowanie spadło do 0.2 tok/s. **O 03:54:02 UTC wszystkie moje przebiegi harnessu na L40S zostały zakończone sygnałem („Terminated”) przez proces, którego nie uruchamiałem** (Qwen3.5-2B IQ3_XXS z RAG i bez, oba warianty PL). Zatrzymałem wtedy tylko własne serwery (porty 8811, 8812, 8815, 8816) i przeniosłem przebiegi 2B na H100.
- H100 (05:57–06:33): trzy moje serwery (8821–8823) obok Gemmy T1 i serwera 4B innych agentów. Zatrzymane przez skrypt po zakończeniu. Cudzych procesów nie ruszałem.

## Pliki

- Skrypty: `server/t3s_small.sh` (fazy `q2b`, `custom`, `slayer`, `bielik`, `q2b26`), `overnight/t3s_judge.sh` (pobranie, `to_results`, `grade`, `judge_reuse`, luna; `HOST=` wybiera maszynę).
- Modele (nie do finału): L40S `~/models/custom/qwen35-2b/` (imatrix-pl-2b.gguf, trzy GGUF, tt_*.txt, build.sh) — kopia na H100 w tej samej ścieżce; L40S `~/models/SlayerLab/…/sft2-IQ4_XS.gguf`, `~/models/speakleash/Bielik-1.5B-v3.0-Instruct-GGUF/` (fp16 + Q4_K_M), `~/models/unsloth/Qwen3.5-2B-GGUF/` (UD-IQ3_XXS, UD-IQ2_M, BF16), `~/models/unsloth/Qwen3.5-0.8B-GGUF/`; H100 `~/models/unsloth/Qwen3.5-2B-GGUF/Qwen3.5-2B-UD-IQ3_XXS.gguf`. Można je usunąć (H100 ma 78% dysku zajęte).
- Przebiegi: `runs/test202[456]_v2/{slayer-sft2-iq4xs__*,bielik-1.5b-q4km__t2h,q35-2b-iq*__t3s-s42}` (lokalnie + oceny w `results/grades/`).

## Koszty

- Sędzia gpt-6-luna ≈ $1.22: Bielik $0.16, SlayerLab $0.43, 2B IQ2_M ≈ $0.15, 2B IQ3_XXS ×3 $0.48.
- Modal: $0. Forgehand GPU: nieużywany.
