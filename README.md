# Kolektyw — lokalne modele na maturze z historii (poziom rozszerzony)

Made during the Warsaw Model Trainers hackathon, Kolektyw3, 25–27.09.2026.

Trzy rozwiązania (tracki) konkursu Warsaw Model Trainers: lokalny model językowy (llama.cpp, bez internetu i bez zewnętrznych API) rozwiązuje arkusz matury CKE z historii (formuła 2023, poziom rozszerzony) podany jako `exam.json` + `images/` i zwraca `answers.json`. Repo zawiera harness egzaminacyjny, konfiguracje, skrypty danych, treningu, kwantyzacji i ewaluacji, raporty z eksperymentów oraz bazę wiedzy używaną w czasie egzaminu. Wagi modeli, materiały CKE i organizatorów oraz duże zbiory pochodne są poza repo (`.gitignore`); poniżej są linki i skrypty, które je odtwarzają.

## Wyniki

Ocena: nasz sędzia LLM (`gpt-6-luna`) według zasad oceniania CKE, zamknięte automatycznie (`eval/grade.py`). Zbiór główny = arkusze maj 2024 + maj 2025 (119 pkt; zadanie 2024/21 poza mianownikiem, bo odrzuca je filtr treści sędziego), kontrolny = maj 2026 (60 pkt). Szum między seedami to ~2–3 pp. Liczby z `raports/20-audyt-odpowiedzi.md` i `raports/18-t3-mniejszy.md`.

| Track (kategoria) | Rozwiązanie | Rozmiar wag | 2024+2025 | 2026 |
|---|---|---|---|---|
| **T1** — Best exam score | Gemma-4-12B-it QAT q4_0 + mmproj, myślenie, harness z `--rozstrz-hint` i esejem wg kryteriów CKE | 7.15 GB | **71.5%** | **84.1%** |
| **T2** — Biggest improvement | PLLuM-12B-base-2512 Q4_K_M + nasza LoRA + RAG (BM25) + OCR + opisy obrazów z Qwen3.5-0.8B | 8.72 GB łącznie (baza 7.48 GB) | **56.7%** (goła baza: 0%) | **52.5%** (goła baza: 0%) |
| **T3** — Smallest model passing 35% | nasza kwantyzacja Qwen3.5-4B IQ2_M-PL-E4K-MIX-S4K-V124K (imatrix PL, przycięty słownik) + mmproj | **1.53 GB** (największy plik) | **41.2%** (3 seedy: 45.4 / 36.1 / 42.1) | **42.8%** (3 seedy) |

Źródło prawdy dla wszystkich flag: [`server/final_configs.json`](server/final_configs.json) (argumenty `llama-server` i `harness/run_exam.py` dla każdego tracku, wariant `tuned` i `base`); uruchamia je [`server/exam_run.sh`](server/exam_run.sh), procedura egzaminu w [`server/RUNBOOK.md`](server/RUNBOOK.md).

Limit rozmiaru (interpretacja drużyny): model bazowy < 8 GB, łącznie z nakładkami i modelami pomocniczymi < 8.8 GB; strona organizatorów podaje „weights up to 8 GB on disk”. GB = 10⁹ B. Baza wiedzy RAG się nie liczy.

---

## T1 — Gemma-4-12B-it QAT (najlepszy wynik)

**Model:** [`google/gemma-4-12B-it-qat-q4_0-gguf`](https://huggingface.co/google/gemma-4-12B-it-qat-q4_0-gguf), bez treningu.

| Plik | Bajty |
|---|---|
| `gemma-4-12b-it-qat-q4_0.gguf` | 6 975 879 296 |
| `mmproj-gemma-4-12b-it-qat-q4_0.gguf` (enkoder obrazu; mimo nazwy BF16, raport 15) | 175 115 616 |
| **razem** | **7 150 994 912 (7.15 GB)** |

Co zrobiliśmy (tylko harness): prompt organizatorów, typ zadania z `answer_format`, normalizacja odpowiedzi zamkniętych, myślenie dla wszystkich typów, obrazy przez mmproj, powtórka bez myślenia przy urwanym myśleniu, kontrola eseju (≥ 300 wyrazów, numer tematu). Do tego dwie flagi przyjęte rano 27.09:
- `--rozstrz-hint` — w zadaniach „Rozstrzygnij…” wskazówka, by identyfikować każde źródło po szczegółach i nie dopisywać niepewnych faktów (raporty 12, 20);
- `--essay-mode rubric --essay-rubric-fixed` — esej pisany drugi raz na ten sam temat, z wymaganiami najwyższego poziomu CKE dla każdego elementu tematu (raport 22).

```bash
# llama-server (tuned i base identyczne); exam_run.sh dokłada --host/--port -ngl 999 --kv-unified --jinja
llama-server -m ~/models/google/gemma-4-12B-it-qat-q4_0-gguf/gemma-4-12b-it-qat-q4_0.gguf \
  --mmproj ~/models/google/gemma-4-12B-it-qat-q4_0-gguf/mmproj-gemma-4-12b-it-qat-q4_0.gguf \
  -ub 4096 -b 4096 -c 131072 -np 8 --reasoning-format deepseek
# harness tuned
python harness/run_exam.py --exam <katalog> --out <wynik> --base-url http://127.0.0.1:<port>/v1 \
  --parallel 8 --rag none --vision --think essay,rozstrz,open,podaj,closed \
  --temperature 1.0 --top-p 0.95 --top-k 64 --rozstrz-hint --essay-mode rubric --essay-rubric-fixed
# harness base
... --bare --parallel 8 --vision --think essay,rozstrz,open,podaj,closed --temperature 1.0 --top-p 0.95 --top-k 64
```

## T2 — PLLuM-12B-base + LoRA (największy przyrost)

**Model bazowy:** [`CYFRAGOVPL/PLLuM-12B-base-2512`](https://huggingface.co/CYFRAGOVPL/PLLuM-12B-base-2512) (pretrenowany, bez dostrojenia instrukcyjnego; oparty na Mistral-Nemo-Base-2407), GGUF z [`mradermacher/PLLuM-12B-base-2512-GGUF`](https://huggingface.co/mradermacher/PLLuM-12B-base-2512-GGUF). Wariant `base` = ta sama baza bez LoRA i bez pomocy harnessu (`--bare`): **0%** — goła baza nie trzyma formatu odpowiedzi.

**Model pomocniczy (opisy obrazów, bo PLLuM nie ma wizji):** [`unsloth/Qwen3.5-0.8B-GGUF`](https://huggingface.co/unsloth/Qwen3.5-0.8B-GGUF) (z [`Qwen/Qwen3.5-0.8B`](https://huggingface.co/Qwen/Qwen3.5-0.8B)).

| Plik | Bajty |
|---|---|
| `PLLuM-12B-base-2512.Q4_K_M.gguf` | 7 477 204 064 |
| `lora.gguf` — nasza LoRA `pllum-v1recipe-full` (F16) | 228 104 192 |
| `Qwen3.5-0.8B-Q8_0.gguf` | 811 843 840 |
| `mmproj-F16.gguf` (Qwen3.5-0.8B) | 204 987 232 |
| **razem** | **8 722 139 328 (8.72 GB)**; sam PLLuM + LoRA: 7.71 GB |

**LoRA `pllum-v1recipe-full`** (SFT, Unsloth, `train/sft_lora.py`, job w `overnight/modal_train.py`, Modal H100):
- dane: `data/sft/v2plain/train_answer.jsonl` + `val_answer.jsonl` — **10 479 przykładów** (10 165 train / 314 val) w dokładnym formacie promptu harnessu, bez kontekstu RAG: 10 064 zadania syntetyczne z weryfikacją na ślepo (E3/E5), 297 esejów ocenionych ≥ 12/15, 118 prawdziwych zadań CKE spoza zbiorów testowych (E1), 500 przykładów HyDE i 150 dopytań o numer tematu eseju; odrzucone: 883 prawie-duplikaty, 23 zbyt podobne do zbiorów ewaluacyjnych (`data/sft/v2plain/STATS.md`);
- hiperparametry: 2 epoki, rank 32, alpha 32, dropout 0, lr 1e-4, batch 4 × grad-acc 4, max 4096 tokenów, moduły q/k/v/o/gate/up/down, baza w bf16 (bez 4-bit);
- szablon czatu z [`CYFRAGOVPL/PLLuM-12B-instruct-2512`](https://huggingface.co/CYFRAGOVPL/PLLuM-12B-instruct-2512) (`--template-from`; baza go nie ma) — kopia w repo: `data/final_artifacts/pllum-v1recipe-full-adapter/chat_template.jinja` (identyczna bajtowo z plikiem z HF);
- konwersja: `llama.cpp/convert_lora_to_gguf.py <adapter> --base-model-id CYFRAGOVPL/PLLuM-12B-base-2512 --outtype f16`;
- w repo: `adapter_config.json`, `chat_template.jinja`, `README.md` adaptera (`data/final_artifacts/pllum-v1recipe-full-adapter/`); same wagi LoRA (GGUF i safetensors) są poza repo.

**Harness T2:** temp. 0, bez myślenia; RAG BM25: 3 fragmenty z PolQA (7 mln pasaży polskiej Wikipedii) + 1 notatka z naszej bazy `data/kb/kb_all_notes.jsonl` dla typów podaj/rozstrzygnij/otwarte; kompendium (`data/kb/kompendium.jsonl`) przy eseju; `--fill-fields` (gdy brakuje pól wzoru „Etykieta:”, powtórka z wymuszonym formatem, raport 12); `--ocr` (tesseract pol+eng na obrazach) i opisy obrazów z Qwen3.5-0.8B wstawiane obok znacznika `[Obraz: …]` (`--caption-url`, raport 15: +5.5 pp).

```bash
# PLLuM + LoRA
llama-server -m ~/models/mradermacher/PLLuM-12B-base-2512-GGUF/PLLuM-12B-base-2512.Q4_K_M.gguf \
  --lora ~/train/pllum-v1recipe-full/lora.gguf --chat-template-file ~/train/pllum-12b-base/chat_template.jinja -c 65536 -np 8
# serwer opisów obrazów (port T2 + 50), z GGML_CUDA_DISABLE_GRAPHS=1
GGML_CUDA_DISABLE_GRAPHS=1 llama-server -m ~/models/unsloth/Qwen3.5-0.8B-GGUF/Qwen3.5-0.8B-Q8_0.gguf \
  --mmproj ~/models/unsloth/Qwen3.5-0.8B-GGUF/mmproj-F16.gguf -c 32768 -np 8
# harness tuned (exam_run.sh dopisuje --caption-url http://127.0.0.1:<port+50>/v1)
python harness/run_exam.py ... --parallel 8 --no-think-kwargs --temperature 0.0 --top-p 1.0 --top-k 1 \
  --kb-essay data/kb/kompendium.jsonl --rag bm25 --rag-types podaj,rozstrz,open --rag-k 3 \
  --kb-rag data/kb/kb_all_notes.jsonl --kb-rag-k 1 --fill-fields --ocr
# base: serwer bez --lora i bez szablonu, harness:
... --bare --parallel 8 --no-think-kwargs --temperature 0.0 --top-p 1.0 --top-k 1
```

Indeks BM25 (`data/kb/polqa_index`, tantivy, ~4.4 GB, z polem słów obciętych do 6 znaków na polską fleksję) buduje `overnight/local/build_kb.py`; harness szuka go domyślnie w tym miejscu.

## T3 — Qwen3.5-4B, własna kwantyzacja 1.53 GB (najmniejszy ≥ 35%)

**Model:** [`Qwen/Qwen3.5-4B`](https://huggingface.co/Qwen/Qwen3.5-4B); punkt wyjścia do kwantyzacji `Qwen3.5-4B-BF16.gguf` i `mmproj-F16.gguf` z [`unsloth/Qwen3.5-4B-GGUF`](https://huggingface.co/unsloth/Qwen3.5-4B-GGUF). Bez LoRA (LoRA z maską myślenia skracała myślenie o 77%, bramka `eval/think_gate.py`).

| Plik | Bajty | sha256 |
|---|---|---|
| **`Qwen3.5-4B-IQ2_M-PL-E4K-MIX-S4K-V124K.gguf`** (nasz, największy plik rozwiązania) | **1 532 889 600** | `2f2a141a41190092e97a8feeb6a54eccb8721a6851de3b5b8e7ea8057083b1f6` |
| `mmproj-F16.gguf` (bez zmian, z unsloth) | 672 423 616 | — |

Jeśli organizatorzy liczą sumę plików, T3 ma 2.21 GB; liczony „największy plik” to model (1.53 GB).

Jak powstał plik (raporty 10b, 10c, 18):
1. **Polski imatrix** (`imatrix-pl.gguf`) liczony na BF16 z korpusu ~370 tys. tokenów: 56 śladów rozumowania samego Qwen3.5-4B BF16 na naszych zadaniach syntetycznych E5 (w szablonie czatu z `<think>`) + ~650 KB tekstu z naszej bazy wiedzy (kompendium, oś czasu, postacie, pojęcia, zadania E5 z odpowiedziami); bez arkuszy 2024–2026. `llama-imatrix` z jednolinijkową łatką, która przy `--process-output` zbiera też `token_embd.weight` (osadzenia są wiązane z głowicą wyjściową).
2. **Przepis typów tensorów:** unsloth UD-IQ2_M odczytany 1:1 z `Qwen3.5-4B-UD-IQ2_M.gguf` (gguf-py), a potem zmiany: `token_embd` Q4_K (**E4K**), `ffn_down` i `attn_qkv` z IQ2_S na IQ3_XXS — 47 tensorów (**MIX**), `ssm_out` Q5_K → Q4_K (**S4K**). `llama-quantize` z typem bazowym IQ2_M.
3. **Przycięty słownik (V124K):** 248 320 → 126 579 tokenów. Zachowane są: każdy token widziany w korpusie 595 mln znaków PL (baza wiedzy, dane SFT, arkusze, wyjścia naszych modeli z angielskim rozumowaniem, PolQA, ~120 tys. artykułów Wikipedii) i 155 mln znaków EN (wikitext-103), tokeny łacińskie/ASCII/greckie o id < 60 000, wszystkie tokeny specjalne i bajtowe oraz domknięcie reguł BPE. Wiersze `token_embd` wycięte bajtowo z gotowego GGUF, bez ponownej kwantyzacji (−181.6 MB). Tokenizacja identyczna na tekście odłożonym, PPL bez zmian (`work/vt/`).

Harness T3: temp. 0.6, myślenie dla zadań krótkich (bez eseju) z limitem serwera 5000 tokenów i komunikatem domykającym; esej `--essay-mode structured` (plan z kompendium, akapit na aspekt, 336–650 słów; raport 10c); `--think-retry` (urwane myślenie → jedna powtórka z myśleniem, potem bez) i `--match-retry` (dopasowania z cyframi zamiast nazw; raport 21). Cały track z `GGML_CUDA_DISABLE_GRAPHS=1` (awarie `clip_encode` mmproj Qwen3.5 na H100 przy grafach CUDA, raport 21).

```bash
GGML_CUDA_DISABLE_GRAPHS=1 llama-server -m ~/models/custom/qwen35-4b/Qwen3.5-4B-IQ2_M-PL-E4K-MIX-S4K-V124K.gguf \
  --mmproj ~/models/unsloth/Qwen3.5-4B-GGUF/mmproj-F16.gguf -ub 4096 -b 4096 -c 98304 -np 8 \
  --reasoning-format deepseek --reasoning-budget 5000 \
  --reasoning-budget-message $'\n\nNa podstawie powyższych rozważań podaję ostateczną odpowiedź.\n'
# harness tuned
python harness/run_exam.py ... --parallel 8 --rag none --vision --think rozstrz,open,podaj,closed \
  --temperature 0.6 --top-p 0.95 --top-k 20 --max-tokens 8000 --kb-essay data/kb/kompendium.jsonl \
  --essay-mode structured --think-retry --match-retry
# base: serwer bez --reasoning-budget*, harness:
... --bare --parallel 8 --vision --temperature 1.0 --top-p 0.95 --top-k 20
```

---

## Harness (`harness/run_exam.py`)

Wejście: katalog z `exam.json` (format organizatorów `separate-text-and-images-v1`: `items[]` z `id`, `question`, `source_text` ze znacznikami `[Obraz: images/X.png]`, `images[]`, `answer_format`, `max_points`) i `images/`. Wyjście: `answers.json` (do wgrania) + `debug.jsonl` (pełne prompty, rozumowanie, powtórki) + `meta.json`. Komunikacja z `llama-server` przez API zgodne z OpenAI.

Przebieg dla każdego zadania:
1. **Typ zadania z `answer_format`:** zamknięte `closed_tf` (P/F), `closed_choice` (litera), `closed_match` (przyporządkowanie), `closed_multi`; otwarte `podaj`, `rozstrz` (rozstrzygnij + uzasadnij), `open` (wyjaśnij, porównaj…); `essay`.
2. **Prompt:** prompt systemowy organizatorów, „Zadanie N (p pkt)”, źródła, dopisek o formacie przy zamkniętych; opcjonalnie obrazy PNG (`--vision`), tekst z OCR (`--ocr`), opisy z pomocniczego VLM (`--caption-url`), kontekst RAG (`--rag bm25`, `--kb-rag`), kompendium przy eseju (`--kb-essay`), wskazówki (`--rozstrz-hint`).
3. **Myślenie per typ** (`--think`, przez `chat_template_kwargs.enable_thinking`; `--no-think-kwargs` dla modeli bez przełącznika).
4. **Naprawy:** normalizacja zamkniętych do wzoru, powtórka bez myślenia przy urwaniu (albo najpierw z myśleniem: `--think-retry`), uzupełnianie pól wzoru (`--fill-fields`), esej: ≥ 300 wyrazów i nagłówek „Temat nr N”, tryby `structured` / `rubric`; ponawianie przy błędach połączenia z serwerem.
5. `--bare` = wariant base: goły model, bez dopisku o formacie, powtórek, poprawek eseju i normalizacji.

Wszystkie flagi eksperymentalne są opt-in (domyślnie wyłączone); w finale działają tylko te z `final_configs.json`. Pełna lista: `python harness/run_exam.py --help`.

Inne pliki: `harness/check_answers.py` (walidacja `answers.json` jak na stronie zgłoszeń: klucze, `exam_id`, komplet ID, typy, ≤ 100 000 znaków, ≤ 1 MiB), `harness/topics.py` (Polska / świat), `harness/make_exam_pack.py --v2` (nasze zbiory → paczki w formacie finału), `harness/to_results.py` (przebieg → format oceniania).

## Dane i bazy wiedzy

| Zbiór | Do czego | Jak powstał | W repo? |
|---|---|---|---|
| **Kompendium** `data/kb/kompendium.jsonl` (218 notatek) | esej T2 i T3 (`--kb-essay`), RAG T2, imatrix T3 | E2 `data_gen/e2_kb.py`: taksonomia działów podstawy programowej → notatka 300–500 słów na podtemat, model `gpt-6-sol` | **tak** |
| **Notatki RAG** `data/kb/kb_all_notes.jsonl` (4 708) | RAG T2 (`--kb-rag`, top-1) | kompendium 218 + kompendium_extra 106 + oś czasu 2 817 + postacie 940 + pojęcia 627 (E6 `data_gen/e6_kb.py`, `gpt-6-luna`), złożone przez `train/build_sft_v2.py` (`load_kb`) | **tak** |
| **PolQA** — korpus 7 mln pasaży polskiej Wikipedii (III 2022) | RAG T2 (BM25 top-3), częstości tokenów T3 | [`ipipan/polqa`](https://huggingface.co/datasets/ipipan/polqa), indeks: `overnight/local/build_kb.py` | nie (4.4 GB, skrypt) |
| **Wikipedia PL** `20231101.pl` | częstości tokenów (przycinanie słownika T3) | [`wikimedia/wikipedia`](https://huggingface.co/datasets/wikimedia/wikipedia), pobiera `overnight/local/build_kb.py` | nie |
| **wikitext-103** (`wikitext-103-raw-v1`) | częstości tokenów EN (T3) | [`Salesforce/wikitext`](https://huggingface.co/datasets/Salesforce/wikitext) | nie |
| **Dane SFT LoRA T2** `data/sft/v2plain/` (10 479) | trening LoRA T2 | E1 `e1_real.py` (zadania CKE formuły 2015, stara matura, informator → format egzaminu, `gpt-6-luna`), E3 `e3_synthetic.py` (wiązki zadań, `gpt-6-sol`, weryfikacja na ślepo `gpt-6-luna`), E4 `e4_essays.py` (eseje `gpt-6-sol`, ocena CKE ≥ 12/15), **E5 `e5_bulk.py`** (10 243 zadania `gpt-6-luna` z weryfikacją na ślepo i filtrami przecieków, 15% odrzuconych), potem `train/build_sft_v2.py --no-raft --out-dir data/sft/v2plain`; specyfikacja `data_gen/SPEC.md` | nie (skrypty; zawierają wyciągi z arkuszy CKE) |
| **Korpus kalibracyjny imatrix T3** (~370 tys. tokenów) + zbiory PPL | kwantyzacja T3 | `overnight/quant_calib_gen.py` (ślady BF16) + `overnight/quant_calib_build.py` | nie (skrypty) |
| **Lista tokenów V124K** `work/vt/K_seen_a60k.txt` | przycinanie słownika T3 | `work/vt/count.py` → `select.py` / `cats.py` | **tak** |
| **Arkusze CKE** matura z historii, formuła 2023 (maj 2023–2026) + zasady oceniania | tylko ewaluacja (2024, 2025 główne; 2026 kontrolny; 2023 dev); nigdy w treningu, bazie wiedzy ani imatrix | [cke.gov.pl — arkusze formuły 2023](https://cke.gov.pl/egzamin-maturalny/egzamin-maturalny-w-formule-2023/arkusze/); `overnight/local/cke_crawl.py` + `pdf_extract.py` → `eval/build_exam.py <rok>` → `harness/make_exam_pack.py --v2` | nie (materiały CKE) |
| Starsze arkusze CKE (formuła 2015, stara matura), informator | trening (E1: 233 zadania, w LoRA 118 po filtrach) | jw. (`cke_crawl.py`) | nie |
| Mock 2023 i benchmark organizatorów | test na sucho, kalibracja sędziego | strona organizatorów | nie |

Filtry kontaminacji: zadania syntetyczne porównywane z zadaniami testowymi (n-gramy + filtry nazw z kluczy), przykłady z arkuszy 2023–2026 wykluczone z treningu (`data_gen/SPEC.md`, `train/build_sft.py`).

## Licencje

Sprawdzone 27.09.2026 w kartach modeli/datasetów na Hugging Face (pole `license`) i na GitHubie.

| Składnik | Licencja | Źródło |
|---|---|---|
| Gemma 4 12B it QAT (T1) | **Apache 2.0** (Gemma 4 nie ma już osobnych „Gemma Terms of Use”) | [karta modelu](https://huggingface.co/google/gemma-4-12B-it-qat-q4_0-gguf), [licencja Gemma 4](https://ai.google.dev/gemma/docs/gemma_4_license) |
| PLLuM-12B-base-2512 i PLLuM-12B-instruct-2512 (szablon czatu) (T2) | **Apache 2.0** (baza Mistral-Nemo-Base-2407, też Apache 2.0) | [karta base](https://huggingface.co/CYFRAGOVPL/PLLuM-12B-base-2512), [karta instruct](https://huggingface.co/CYFRAGOVPL/PLLuM-12B-instruct-2512) |
| GGUF PLLuM (mradermacher) | Apache 2.0 | [karta](https://huggingface.co/mradermacher/PLLuM-12B-base-2512-GGUF) |
| Qwen3.5-4B (T3) i Qwen3.5-0.8B (T2, opisy obrazów), GGUF unsloth | **Apache 2.0** | [Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B/blob/main/LICENSE), [Qwen3.5-0.8B](https://huggingface.co/Qwen/Qwen3.5-0.8B/blob/main/LICENSE), [unsloth 4B](https://huggingface.co/unsloth/Qwen3.5-4B-GGUF), [unsloth 0.8B](https://huggingface.co/unsloth/Qwen3.5-0.8B-GGUF) |
| Nasze pochodne wagi: LoRA `pllum-v1recipe-full`, kwantyzacja `…-MIX-S4K-V124K.gguf`, `imatrix-pl.gguf` | licencja modelu bazowego: Apache 2.0 | — |
| llama.cpp (serwer, kwantyzacja, gguf-py, konwersja LoRA) | MIT | [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) |
| Unsloth, PEFT, TRL (trening) | Apache 2.0 | [unsloth](https://github.com/unslothai/unsloth), [peft](https://github.com/huggingface/peft), [trl](https://github.com/huggingface/trl) |
| Tesseract + `tessdata` (OCR w T2) | Apache 2.0 | [tesseract](https://github.com/tesseract-ocr/tesseract), [tessdata_best](https://github.com/tesseract-ocr/tessdata_best) |
| tantivy-py (BM25) | MIT | [tantivy-py](https://github.com/quickwit-oss/tantivy-py) |
| PolQA (`ipipan/polqa`) | **CC BY-SA 4.0** | [karta](https://huggingface.co/datasets/ipipan/polqa) |
| Wikipedia PL (`wikimedia/wikipedia`) | CC BY-SA 3.0 + GFDL | [karta](https://huggingface.co/datasets/wikimedia/wikipedia) |
| wikitext-103 (`Salesforce/wikitext`) | CC BY-SA 3.0 + GFDL | [karta](https://huggingface.co/datasets/Salesforce/wikitext) |
| Arkusze i zasady oceniania CKE | **niepewne** — oficjalne, publicznie udostępniane materiały CKE, ale bez wskazanej otwartej licencji i z utworami osób trzecich (ilustracje, fragmenty tekstów). Używamy ich tylko do ewaluacji (2023–2026) i jako źródła zadań treningowych ze starszych formuł; nie redystrybuujemy PDF-ów ani wyekstrahowanych tekstów (tylko skrypty pobierające). | [cke.gov.pl](https://cke.gov.pl/) |
| Materiały organizatorów (mock 2023, benchmark) | **niepewne** — licencja niepodana; poza repo | strona konkursu |
| Nasze dane syntetyczne (kompendium, notatki, zadania E1–E6) | **niepewne** — repo nie ma pliku licencji; tekst wygenerowany przez `gpt-6-sol` / `gpt-6-luna` (API Forgehand udostępnione na hackathonie), warunków tego API nie weryfikowaliśmy. Regulamin konkursu dopuszcza dane syntetyczne z dowolnego LLM. | — |

Kod w repo: bez osobnej licencji (regulamin: „code: any license”).

---

## Setup / Odtworzenie pipeline'u

Kroki od zera do `answers.json`. Oznaczenia: **[GPU]** potrzebna karta NVIDIA, **[API]** potrzebny klucz do zewnętrznego LLM (tylko budowanie danych i ocena, nigdy egzamin), **[brak w repo]** krok, którego skryptu lub pliku nie ma w repozytorium.

### 1. Wymagania

| | Użyte przez nas |
|---|---|
| GPU egzaminacyjne | Nebius **H100 80 GB** (sm_90) — wszystkie tracki naraz (T1, T2 z serwerem opisów, T3 tuned + T2 base); zapas Nebius **L40S 48 GB** (sm_89) — te same polecenia, tracki po kolei |
| VRAM na track | nie mierzyliśmy dokładnie przy finałowych flagach; znane punkty: serwer T3 ~7.9 GB (L40S), pierwsza fala egzaminu (T1, T2 + serwer opisów, T3, T2 base) mieści się naraz w 80 GB, każdy track osobno w 48 GB. T1 i T2 mają duże konteksty (`-c 131072` / `65536` na 8 slotów), więc potrzebują wyraźnie więcej niż same wagi. |
| System | Ubuntu 24.04 (obraz Nebius `ubuntu24.04-cuda13.0`), sterownik 580, CUDA 13.0; Forgehand: Ubuntu 22.04 + CUDA 12.8 też działał |
| Python | 3.12 na maszynach (uv venv), 3.10+ działa; trening na Modal: 3.11 |
| Narzędzia | `git`, `cmake`, `build-essential`, `tesseract-ocr tesseract-ocr-pol` (T2 `--ocr`) |
| Trening LoRA | Modal H100 80 GB (baza 12B w bf16, bez 4-bit) |

```bash
sudo apt-get install -y git cmake build-essential ccache python3-dev tesseract-ocr tesseract-ocr-pol
git clone https://github.com/stanislawMarciniak/finetune-kolektyw ~/repo   # exam_run.sh zakłada ~/repo
cd ~/repo
python3 -m venv ~/venv-eval && ~/venv-eval/bin/pip install -r requirements.txt
export PY=~/venv-eval/bin/python   # server/lib_eval.sh bierze $PY (domyślnie ~/venv-unsloth, potem ~/venv-eval)
```

### 2. llama.cpp (commit `2145525`)

Wszystkie wyniki i egzamin: llama.cpp **`2145525a4081d66ff1a87cf43ef809f95a85ac0c`** (26.09.2026). Potrzebne `--reasoning-budget` i `--reasoning-budget-message` (T3); starsze buildy mogą ich nie mieć. `exam_run.sh` szuka binarki w `~/llama.cpp/build/bin/llama-server`.

```bash
git clone https://github.com/ggml-org/llama.cpp ~/llama.cpp
cd ~/llama.cpp && git checkout 2145525a4081d66ff1a87cf43ef809f95a85ac0c
cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=90 -DLLAMA_CURL=OFF   # 89 dla L40S
cmake --build build --config Release -j "$(nproc)" \
  --target llama-server llama-quantize llama-imatrix llama-perplexity
pip install -e ~/llama.cpp/gguf-py   # gguf-py dla work/vt/trim.py (w venv z kroku 1)
```

### 3. Modele z Hugging Face

Układ katalogów oczekiwany przez `final_configs.json`: `~/models/<repo HF>/<plik>` (`exam_run.sh` zamienia `models/` na `~/models/`, `train/` na `~/train/`).

```bash
cd ~ && pip install -U huggingface_hub hf_xet    # polecenie `hf` (starsze: huggingface-cli download ...)
hf download google/gemma-4-12B-it-qat-q4_0-gguf gemma-4-12b-it-qat-q4_0.gguf mmproj-gemma-4-12b-it-qat-q4_0.gguf \
  --local-dir ~/models/google/gemma-4-12B-it-qat-q4_0-gguf
hf download mradermacher/PLLuM-12B-base-2512-GGUF PLLuM-12B-base-2512.Q4_K_M.gguf \
  --local-dir ~/models/mradermacher/PLLuM-12B-base-2512-GGUF
hf download unsloth/Qwen3.5-0.8B-GGUF Qwen3.5-0.8B-Q8_0.gguf mmproj-F16.gguf \
  --local-dir ~/models/unsloth/Qwen3.5-0.8B-GGUF
hf download unsloth/Qwen3.5-4B-GGUF mmproj-F16.gguf Qwen3.5-4B-BF16.gguf Qwen3.5-4B-UD-IQ2_M.gguf \
  --local-dir ~/models/unsloth/Qwen3.5-4B-GGUF          # BF16 i UD-IQ2_M tylko do odtworzenia kwantyzacji T3
# szablon czatu T2 (ten sam co w PLLuM-12B-instruct-2512)
mkdir -p ~/train/pllum-12b-base && cp ~/repo/data/final_artifacts/pllum-v1recipe-full-adapter/chat_template.jinja ~/train/pllum-12b-base/
```

Kontrola rozmiarów: gemma 6 975 879 296 B, mmproj gemma 175 115 616 B, PLLuM 7 477 204 064 B, Qwen3.5-0.8B-Q8_0 811 843 840 B, mmproj 0.8B 204 987 232 B, mmproj 4B 672 423 616 B.

Nasze artefakty (LoRA T2, GGUF T3) **nie są opublikowane na HF** — trzeba je odtworzyć (krok 4) albo dostać kopię od zespołu. Docelowe miejsca: `~/train/pllum-v1recipe-full/lora.gguf` i `~/models/custom/qwen35-4b/Qwen3.5-4B-IQ2_M-PL-E4K-MIX-S4K-V124K.gguf`.

### 4. Artefakty własne

#### 4a. Arkusze CKE i zbiory ewaluacyjne

```bash
cd ~/repo
python overnight/local/cke_crawl.py          # PDF-y CKE → data/cke/raw/ + manifest.jsonl
python overnight/local/pdf_extract.py        # tekst, rendery stron, wycinki obrazów → data/cke/extracted/
# ewaluacja: eval/build_exam.py oczekuje assets/cke/<rok>/{arkusz,zasady}.pdf (skopiować z data/cke/raw/)
for y in 2024 2025 2026; do python eval/build_exam.py $y; done              # → eval/data/test<rok>_split.jsonl
python harness/make_exam_pack.py --v2 test2024_split test2025_split test2026_split   # → exams/test<rok>_v2/
```

#### 4b. Baza wiedzy, RAG i dane SFT **[API]**

Generatory w `data_gen/` wołają API zgodne z OpenAI (u nas Forgehand, modele `gpt-6-sol` / `gpt-6-luna`); klucz w `.env` jako `FORGEHAND_API_KEY` (nigdy w repo), adres endpointu w `data_gen/common.py`. Każdy etap ma limit kosztu i wznawia się po ID (koszty m.in. E5 ~$6.6, E6 ~$3.8; log w `data_gen/cost_log.jsonl`). Inne API wymaga podmiany `BASE_URL` i nazw modeli.

```bash
set -a; . ./.env; set +a
python -m data_gen.e1_real          # prawdziwe zadania CKE (formuła 2015, stara matura, informator) → data/sft/real_cke.jsonl
python -m data_gen.e2_kb            # taksonomia + kompendium → data_gen/taxonomy.json, data/kb/kompendium.jsonl
python -m data_gen.e3_synthetic     # wiązki zadań z weryfikacją → data/sft/synthetic_items.jsonl
python -m data_gen.e4_essays        # eseje ≥ 12/15 → data/sft/essays.jsonl
python -m data_gen.e5_bulk --n 10000 --tag bulk   # 10 243 zadania → data/sft/e5_items.jsonl (flagi: --help)
python -m data_gen.e6_kb            # oś czasu, postacie, pojęcia, kompendium_extra → data/kb/
python overnight/local/build_kb.py  # PolQA + indeks BM25 data/kb/polqa_index (+ Wikipedia PL do data/kb/wikipedia)
python train/build_sft_v2.py --no-raft --out-dir data/sft/v2plain   # dane LoRA T2 + data/kb/kb_all_notes.jsonl
```

Dane i notatki są generowane przez LLM z próbkowaniem, więc powtórka da podobny, ale nie identyczny zbiór. Dokładne pliki użyte w finale: `data/kb/*.jsonl` w repo; `data/sft/v2plain/` tylko lokalnie u zespołu.

#### 4c. LoRA T2 **[GPU]**

Oryginalnie na Modal (`modal run --detach overnight/modal_train.py --jobs pllum-v1recipe-full`, H100, obraz z `unsloth` i llama.cpp; potrzebny sekret Modal `hf-token`). To samo lokalnie:

```bash
pip install unsloth unsloth_zoo "transformers>=4.57" "trl>=0.24" "peft>=0.17" datasets accelerate bitsandbytes
python train/sft_lora.py --model CYFRAGOVPL/PLLuM-12B-base-2512 --template-from CYFRAGOVPL/PLLuM-12B-instruct-2512 \
  --epochs 2 --rank 32 --lr 1e-4 --batch 4 --grad-acc 4 \
  --train data/sft/v2plain/train_answer.jsonl --val data/sft/v2plain/val_answer.jsonl --out ~/train/pllum-v1recipe-full
python ~/llama.cpp/convert_lora_to_gguf.py ~/train/pllum-v1recipe-full/adapter \
  --base-model-id CYFRAGOVPL/PLLuM-12B-base-2512 --outtype f16 --outfile ~/train/pllum-v1recipe-full/lora.gguf
# oczekiwany rozmiar lora.gguf: 228 104 192 B
```

#### 4d. Kwantyzacja T3 **[GPU do imatrix]**

Skrypty: `overnight/quant_calib_gen.py`, `overnight/quant_calib_build.py`, `overnight/quant_t3_pipeline.sh` (imatrix + warianty IQ3_XXS), `work/vt/fine_build.sh` (warianty MIX + przycięcie), `work/vt/trim.py`. Dwóch rzeczy **nie ma w repo**: łatki `llama-imatrix-tiedout` (jedna linia w llama-imatrix: przy `--process-output` zbierać też `token_embd.weight`; bez niej osadzenia Q4_K są kwantyzowane bez wag ważności) i plików typów tensorów `tt_*.txt` — poniżej odtworzenie według opisu z raportów 10c i 18.

```bash
W=~/models/custom/qwen35-4b/work; mkdir -p $W; B=~/llama.cpp/build/bin; S=~/models/unsloth/Qwen3.5-4B-GGUF
# 1) korpus kalibracyjny: ślady rozumowania BF16 na zadaniach E5 (serwer BF16 na porcie 8090) + baza wiedzy
$B/llama-server -m $S/Qwen3.5-4B-BF16.gguf -ngl 999 -c 32768 -np 16 --jinja --reasoning-format deepseek --port 8090 &
python overnight/quant_calib_gen.py --items data/sft/e5_items.jsonl --out $W/traces.jsonl --base-url http://127.0.0.1:8090/v1 --n 380
cp data/kb/{kompendium,kompendium_extra,timeline,persons,terms}.jsonl data/sft/e5_items.jsonl $W/
python overnight/quant_calib_build.py $W        # → calib.txt, ppl_pl.txt, ppl_reason.txt
# 2) imatrix (u nas łatana binarka llama-imatrix-tiedout; zwykła llama-imatrix działa bez wpisu dla token_embd)
$B/llama-imatrix -m $S/Qwen3.5-4B-BF16.gguf -f $W/calib.txt -o $W/imatrix-pl.gguf -ngl 999 -c 2048 -b 2048 -ub 2048 \
  --parse-special --process-output
```

```python
# 3) tt_mix_s4k.txt: typy tensorów stockowego UD-IQ2_M + zmiany MIX (ffn_down/attn_qkv IQ2_S→IQ3_XXS) i S4K (ssm_out Q5_K→Q4_K)
import os, re, gguf
r = gguf.GGUFReader(os.path.expanduser("~/models/unsloth/Qwen3.5-4B-GGUF/Qwen3.5-4B-UD-IQ2_M.gguf"))
with open(os.path.expanduser("~/models/custom/qwen35-4b/work/tt_mix_s4k.txt"), "w") as f:
    for t in r.tensors:
        ty = t.tensor_type.name.lower()
        if not t.name.startswith("blk.") or ty in ("f32", "f16", "bf16"):
            continue
        kind = t.name.split(".")[2]
        if kind in ("ffn_down", "attn_qkv") and ty == "iq2_s":
            ty = "iq3_xxs"
        if kind == "ssm_out" and ty == "q5_k":
            ty = "q4_k"
        f.write(f"^{re.escape(t.name)}$={ty}\n")
```

```bash
# 4) kwantyzacja + przycięcie słownika (lista tokenów w repo)
$B/llama-quantize --imatrix $W/imatrix-pl.gguf --tensor-type-file $W/tt_mix_s4k.txt --token-embedding-type q4_k \
  $S/Qwen3.5-4B-BF16.gguf $W/Qwen3.5-4B-IQ2_M-PL-E4K-MIX-S4K.gguf IQ2_M 8
python work/vt/trim.py $W/Qwen3.5-4B-IQ2_M-PL-E4K-MIX-S4K.gguf work/vt/K_seen_a60k.txt \
  ~/models/custom/qwen35-4b/Qwen3.5-4B-IQ2_M-PL-E4K-MIX-S4K-V124K.gguf
# kontrola: 126 579 tokenów; nasz plik ma 1 532 889 600 B i sha256 2f2a141a…b1f6
sha256sum ~/models/custom/qwen35-4b/Qwen3.5-4B-IQ2_M-PL-E4K-MIX-S4K-V124K.gguf
```

Imatrix zależy od śladów rozumowania z próbkowaniem, więc odtworzony plik będzie miał ten sam rozmiar, ale inny sha256. Listę tokenów można też przeliczyć (`work/vt/count.py` → `work/vt/select.py`), ale korpus częstości zawiera nasze przebiegi `runs/` spoza repo — dlatego gotowa lista jest w repo.

### 5. Egzamin (tak jak w finale)

Paczka od organizatorów (ZIP): `exam.json`, `images/`, `answers-template.json` — rozpakować tak, żeby `exam.json` leżał obok `images/`, np. `~/repo/exams/final/`. Skrypt `server/exam_run.sh <katalog> <T1|T2|T3> <tuned|base> [port]` czyta `final_configs.json`, zdejmuje klucze API ze środowiska (`unset FORGEHAND_API_KEY OPENAI_API_KEY HF_TOKEN`), ustawia `HF_HUB_OFFLINE=1`, dla T3 ustawia `GGML_CUDA_DISABLE_GRAPHS=1` (dla T2 tylko w procesie serwera opisów), startuje `llama-server` z nadzorcą (restart po awarii CUDA), uruchamia harness i zatrzymuje serwery. Wynik: `runs/final/<track>-<wariant>/answers.json` + `debug.jsonl` + `meta.json`.

```bash
cd ~/repo
# pierwsza fala naraz na H100 (na L40S po kolei)
bash server/exam_run.sh exams/final T1 tuned 8401 &
bash server/exam_run.sh exams/final T2 tuned 8402 &   # + serwer opisów obrazów na 8452
bash server/exam_run.sh exams/final T3 tuned 8403 &
bash server/exam_run.sh exams/final T2 base 8412 &    # baseline wymagany w kategorii improvement
wait
bash server/exam_run.sh exams/final T1 base 8411 &
bash server/exam_run.sh exams/final T3 base 8413 &
wait
# walidacja (te same reguły co strona zgłoszeń)
for f in runs/final/*/answers.json; do echo "$f"; python3 harness/check_answers.py "$f" exams/final/answers-template.json; done
```

Czas na H100 (test na sucho 27.09, arkusz 2026 = 39 zadań, z ładowaniem serwerów, tracki naraz jak wyżej): **T1 tuned 533 s, T2 tuned 168 s, T3 tuned 577 s, T1 base 238 s, T2 base 386 s, T3 base 59 s**; 0 restartów serwerów, `check_answers.py` OK. Szybki test instalacji: `bash server/exam_run.sh assets/mock-2023 T3 tuned` (mock 2023 ze strony organizatorów, 37 odpowiedzi).

### 6. Ewaluacja (opcjonalnie) **[API]**

```bash
python harness/to_results.py runs/test2024_v2/<przebieg>      # przebieg → results/<zbiór>/<przebieg>.jsonl
python eval/grade.py results/                                  # zamknięte automatycznie wg tabel punktów CKE
export OPENAI_API_KEY=...                                      # albo inny klucz + --key-env / --base-url (JUDGE_BASE_URL)
python eval/judge_openai.py grade --model gpt-6-luna --essay-model gpt-6-luna --budget 1.0   # otwarte i eseje wg zasad CKE
python eval/analyze.py --registry eval/runs_registry_v2.json   # tabele jak w raporcie 09
```

U nas sędzia `gpt-6-luna` przez API Forgehand (`--key-env FORGEHAND_API_KEY --base-url <endpoint>`), pętla na maszynie: `server/grade_loop.sh`, zbiorcze przebiegi: `server/lib_eval.sh` (`serve` / `run` / `stop`). Kalibracja sędziego: `python eval/judge_openai.py calib` (oceny sędziego benchmarku organizatorów); porównanie z mocniejszym `gpt-6-sol` i powtarzalność: raport 11. Audyt odpowiedzi finałów: `eval/audit.py` (raport 20).

---

## Co nie zadziałało

| Pomysł | Wynik | Raport |
|---|---|---|
| RAG (PolQA + baza) i kompendium w eseju dla T1 | 68.1% / 68.9% vs 71.0% bez | 09, 11 |
| LoRA dla T3 z maską myślenia | myślenie krótsze o 77%, bramka FAIL | 07 (H-N22), 09 |
| Dane z rozumowaniem / z kontekstem RAFT dla T2 | 40–44.5% vs 52.9% przepisu bez kontekstu | 07 (H-N15, H-N26), 09 |
| Gemma-4-12B pt jako baza T2 | śmieci po LoRA, niezgodny szablon i słownik | 07 (H-N2) |
| Kafelki obrazów T1 (`--image-tiles`) | +0.8 pp / −1.7 pp, remis | 15 |
| `--match-names-hint` | ujemny we wszystkich trackach | 14 |
| Recenzent faktów (T1, T3) | eseje +0.27 pkt, otwarte −1 pkt | 17 |
| Głosowanie w zamkniętych T1 | +1.0 pp za ~3× dłuższy czas; nie włączone | 19 |
| Wyszukiwanie podobnych obrazów | 3/61 trafień, ~7 mylących | 23 |
| Modele < 1 GB na T3 (Qwen3.5-2B, Bielik-1.5B) | ≤ 20% | 16 |
| Czyste IQ2_M dla T3 (stock i z imatrix PL) | 33.6–34.5%, poniżej progu | 10c |
| `attn_gate` IQ2_S (S4KG2) i słownik 40k tokenów dla T3 | 33.7% i 36.2%; PPL tego nie wykrywa | 18 |

## Mapa repozytorium

- `harness/` — program egzaminacyjny i walidacja (opis wyżej).
- `server/` — `exam_run.sh`, `final_configs.json`, `RUNBOOK.md`, `lib_eval.sh`, kolejki i skrypty eksperymentów.
- `train/` — `build_sft_v2.py`, `build_sft.py` (v1), `sft_lora.py` (Unsloth; `--mask-think`, `--template-from`), `sft_peft.py` (czysty PEFT/TRL), `templates/`.
- `data_gen/` — generatory E1–E7, `SPEC.md`, `common.py` (limity kosztów), `taxonomy.json`.
- `eval/` — `grade.py`, `judge_openai.py`, `analyze.py`, `report.py`, `audit.py`, `retrieval_bench.py`, `think_gate.py`, `build_exam.py`.
- `overnight/` — Modal (`modal_train.py`, `modal_convert.py`, `modal_q2*.py`), kwantyzacje T3 (`quant_*`), `local/` (crawl CKE, ekstrakcja PDF, indeks PolQA).
- `work/vt/` — przycinanie słownika T3; `work/illegal/` — odtworzenie awarii CUDA (raport 21).
- `raports/` — 01–08 zasady, ewaluacja, zasoby, plan, dane, hipotezy, analiza; 09 przed/po treningach; 10–13 poprawki nocne, kwantyzacje T3, walidacja, strona organizatorów; 14–23 poranne eksperymenty.
- `SOURCE.md` — plik wymagany przez regulamin (zdanie o hackathonie).
