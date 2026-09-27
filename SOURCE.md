# SOURCE — Kolektyw, Warsaw Model Trainers (matura z historii, poziom rozszerzony)

Made during the Warsaw Model Trainers hackathon, Kolektyw3, 25–27.09.2026.

Repo zawiera kod, konfiguracje, raporty i bazę wiedzy używaną przez harness w czasie egzaminu. Wagi modeli, dane chronione (arkusze i zasady CKE, materiały organizatorów, zrzuty Wikipedii, indeks PolQA) i wygenerowane zbiory treningowe są w `.gitignore`; skrypty pozwalają je odtworzyć.

## Rozwiązania

Źródło prawdy: `server/final_configs.json` (argumenty `llama-server` i `harness/run_exam.py` dla każdego tracku, wariant `tuned` i `base`; uruchamia `server/exam_run.sh`).

| Track | Model (HF) | Pliki wag | Co zrobiliśmy |
|---|---|---|---|
| T1 najlepszy wynik | `google/gemma-4-12B-it-qat-q4_0-gguf` | `gemma-4-12b-it-qat-q4_0.gguf` + `mmproj-gemma-4-12b-it-qat-q4_0.gguf` (7.15 GB) | bez treningu; harness: prompt organizatorów, typ z `answer_format`, normalizacja zamkniętych, myślenie per typ, obrazy, powtórka bez myślenia przy urwaniu, kontrola eseju (≥ 300 wyrazów, numer tematu); wskazówka do „rozstrzygnij” (`--rozstrz-hint`, identyfikacja każdego źródła); esej wg kryteriów CKE (`--essay-mode rubric --essay-rubric-fixed`: esej pisany drugi raz na ten sam temat z wymaganiami najwyższego poziomu dla elementów tematu, raport 22); temp. 1.0 |
| T2 największy postęp | `CYFRAGOVPL/PLLuM-12B-base-2512` (GGUF: `mradermacher/PLLuM-12B-base-2512-GGUF`) | `PLLuM-12B-base-2512.Q4_K_M.gguf` + LoRA `lora.gguf` (7.71 GB); pomocniczy VLM do opisów obrazów `unsloth/Qwen3.5-0.8B-GGUF` `Qwen3.5-0.8B-Q8_0.gguf` + `mmproj-F16.gguf` (1.02 GB) → razem 8.72 GB | baza bez dostrojenia instrukcyjnego (goła: 0%); LoRA SFT `pllum-v1recipe-full` na 10,5 tys. przykładów w formacie harnessu (zadania CKE spoza zbiorów testowych, 10 tys. zadań syntetycznych z weryfikacją, eseje ≥ 12/15), szablon czatu z PLLuM-instruct; harness + RAG: BM25 po PolQA (top-3) i 1 notatka z `data/kb/kb_all_notes.jsonl`, kompendium do eseju, `--fill-fields`, OCR (`--ocr`, tesseract) i opisy obrazów z Qwen3.5-0.8B wstawiane obok znacznika `[Obraz: …]` (`--caption-url`, PLLuM nie ma wizji; raport 15); temp. 0 |
| T3 najmniejszy ≥ 35% | `Qwen/Qwen3.5-4B` (mmproj z `unsloth/Qwen3.5-4B-GGUF`) | **`Qwen3.5-4B-IQ2_M-PL-E4K-MIX-S4K-V124K.gguf` (1.53 GB, własna kwantyzacja: polska imatrix, token_embd Q4_K, ffn_down i attn_qkv IQ3_XXS, ssm_out Q4_K, reszta IQ2 wg przepisu unsloth; słownik przycięty z 248 320 do 126 579 tokenów)** + `mmproj-F16.gguf` | bez LoRA (niszczyła myślenie); drabina kwantyzacji; myślenie dla zadań krótkich z limitem 5000 tokenów; esej strukturalny (`--essay-mode structured`: plan z kompendium, akapit na aspekt, 336–650 słów); ponowienia z myśleniem przy urwaniu i dla dopasowań (`--think-retry --match-retry`); llama-server z `GGML_CUDA_DISABLE_GRAPHS=1` (awarie mmproj na H100, raport 21); temp. 0.6 |

T3 — plik modelu (jedyna rzecz, która może się jeszcze zmienić; aktualizować razem z `final_configs.json`): `Qwen3.5-4B-IQ2_M-PL-E4K-MIX-S4K-V124K.gguf` (własna kwantyzacja z przyciętym słownikiem, `~/models/custom/qwen35-4b/`, raporty 10c i 18), 1 532 889 600 B, sha256 2f2a141a….

Wagi i artefakty poza repo: na maszynach egzaminacyjnych `~/models/<repo HF>/` (modele bazowe z HF) i `~/train/pllum-v1recipe-full/lora.gguf` (LoRA T2); kopia LoRA T2 (GGUF + adapter PEFT) lokalnie w `data/final_artifacts/` — w repo tylko `adapter_config.json`, `chat_template.jinja` i `README.md` adaptera. Indeks BM25 PolQA (`data/kb/polqa_index`, 4.4 GB) buduje `overnight/local/build_kb.py`.

Baza wiedzy w repo (tekst wygenerowany przez nas, `data_gen/e2_kb.py`, `e6_kb.py`): `data/kb/kompendium.jsonl` (T2, T3: esej), `data/kb/kb_all_notes.jsonl` (T2: RAG).

## Najważniejsze pliki

- `harness/run_exam.py` — program egzaminacyjny `exam.json` → `answers.json`; `harness/check_answers.py` (walidacja jak na stronie zgłoszeń), `harness/topics.py` (Polska / świat), `harness/make_exam_pack.py` (paczki w formacie finału).
- `train/build_sft_v2.py`, `train/sft_lora.py` (Unsloth; `--mask-think` dla modeli myślących), `train/sft_peft.py` (bez Unsloth), `train/templates/`; trening na Modal: `overnight/modal_train.py`.
- `data_gen/` — generatory danych (E1–E7; `e5_bulk.py` zadania z weryfikacją na ślepo i filtrami przecieków, `e6_kb.py` baza wiedzy).
- `eval/` — ocena zamkniętych (`grade.py`), sędzia LLM wg zasad CKE (`judge_openai.py`), raporty (`analyze.py`, `report.py`), benchmark wyszukiwania (`retrieval_bench.py`), bramka ochrony myślenia (`think_gate.py`).
- `server/` — skrypty maszyn (kolejki, ewaluacje, egzamin: `exam_run.sh`, `final_configs.json`, `RUNBOOK.md`).
- `raports/` — 01–08: zasady, ewaluacja, zasoby, plan, dane, hipotezy (07), analiza wyników (08); 09 — porównanie przed/po; 10–13 — poprawki nocne, kwantyzacje T3, walidacja, strona organizatorów; 14–23 — poranne eksperymenty (obrazy T2, mniejszy T3 z przyciętym słownikiem, głosowanie, audyt odpowiedzi, stabilność CUDA, esej wg kryteriów CKE, wyszukiwanie obrazów).
- `work/vt/` — przycinanie słownika Qwen3.5 dla T3 (skrypty i listy zachowanych tokenów); `work/illegal/` — odtworzenie awarii CUDA (raport 21).

## Odtworzenie (skrót)

1. Arkusze CKE: `overnight/local/cke_crawl.py` + `pdf_extract.py`; zbiory ewaluacyjne: `eval/build_exam.py <rok>`, paczki: `harness/make_exam_pack.py --v2 test2024_split ...`.
2. Dane SFT: `data_gen/e1_real.py` … `e6_kb.py` (API zgodne z OpenAI), potem `train/build_sft_v2.py`.
3. Trening: `train/sft_lora.py --model CYFRAGOVPL/PLLuM-12B-base-2512 --template-from CYFRAGOVPL/PLLuM-12B-instruct-2512 ...`; konwersja LoRA: `llama.cpp/convert_lora_to_gguf.py`.
4. Egzamin: modele z HF do `~/models/<repo HF>/`, potem `bash server/exam_run.sh <katalog z exam.json> <T1|T2|T3> <tuned|base>`.
5. Ewaluacja: `server/lib_eval.sh` + `harness/run_exam.py`, ocena: `server/fetch_runs.sh` / `server/grade_loop.sh`, raport: `eval/analyze.py --registry eval/runs_registry_v2.json`.
