# Egzamin (nd 27.09) — procedura

Maszyna egzaminacyjna: Nebius H100 `matura-h100` (`ssh -i ~/.ssh/id_rsa kolektyw@89.169.126.236`). Zapas: L40S `matura-l40s` (89.169.112.149) — ten sam kod i komplet artefaktów wszystkich trzech tracków (modele, LoRA T2, indeks PolQA, bazy wiedzy); te same polecenia `exam_run.sh` działają na obu.
Konfiguracje modeli i harnessu: `server/final_configs.json` (decyzje G4, raport 09 i 05). Kopia LoRA T2 (GGUF + adapter PEFT) na laptopie: `data/final_artifacts/`.

**Finały (stan 27.09 ~09:00, `final_configs.json`):**
- **T1** Gemma-4-12B-it QAT q4_0 + mmproj; harness tuned: myślenie, temp. 1.0, `--rozstrz-hint --essay-mode rubric --essay-rubric-fixed` (esej pisany drugi raz na ten sam temat z wymaganiami CKE, raport 22; powrót: `_comment_T1_old2`).
- **T2** PLLuM-12B-base Q4_K_M + LoRA + RAG, `--fill-fields --ocr` + serwer opisów obrazów Qwen3.5-0.8B (port +50, **z `GGML_CUDA_DISABLE_GRAPHS=1` tylko dla tego procesu**); razem 8.72 GB.
- **T3** Qwen3.5-4B IQ2_M-PL-E4K-MIX-S4K-V124K (1.53 GB) + mmproj, esej `--essay-mode structured`, `--think-retry --match-retry`; cały track z `GGML_CUDA_DISABLE_GRAPHS=1` (raport 21).

Test na sucho (27.09 08:42, H100, `exam_run.sh` jak w kroku 2.4 na `exams/test2026_v2` — 39 zadań; T1/T2/T3 tuned + T2 base naraz, potem T1 base + T3 base; czas z ładowaniem serwerów): **T1 tuned 533 s** (esej rubric-fixed przyjęty, 102 s), **T2 tuned 168 s** (opisy obrazów 27/27 w 48 s), **T3 tuned 577 s**, T2 base 386 s (goła baza, wszystkie odpowiedzi do limitu 2048 tokenów), T3 base 59 s, T1 base 238 s; 0 restartów serwerów, `check_answers.py` OK dla wszystkich. Sędzia (1 seed, kontrola): T1 tuned 78.3%, T2 tuned 41.7% — różnica wobec 84.4 / 52.5% to prawie wyłącznie esej (8 vs 12 i 3 vs 9 pkt; referencje miały jedną próbkę eseju), reszta ±1 pkt. md5: `run_exam.py` e78935fe…, `final_configs.json` fc3ef87c…, `exam_run.sh` b34a278e….

**Harmonogram (raport 13):** nd **11:00 = koniec pracy** (nie termin oddania). Arkusz finałowy odblokowuje się dopiero po 11:00, po podaniu TEAM_KEY, linku HTTPS do zacommitowanego repo i potwierdzeniu, że przestaliśmy pracować. Od 10:45 na ekranie kolejność wystąpień; problemy techniczne zgłaszać do 11:15; wynik pokazują na ekranie w czasie naszego slotu → **wgrywać jak najszybciej**.

## 0. Repozytorium i TEAM_KEY (przed 11:00, najlepiej od razu)

1. Commit i push repo (dane i wagi są w `.gitignore`; `SOURCE.md` ma wymagane zdanie „Made during the Warsaw Model Trainers hackathon…”): `git add -A && git commit -m "..." && git push`. Repo publiczne albo prywatne z dostępem do odczytu dla organizatorów i jury.
2. Link HTTPS do repo (bez tokenów i parametrów, np. `https://github.com/<org>/<repo>`) i TEAM_KEY mieć pod ręką.
3. Po pushu już nic nie zmieniamy w żadnym projekcie (kod, prompty, konfiguracje).

## 1. Przed egzaminem (do 10:00)

1. Start maszyn, jeśli strażnik je wyłączył: `nebius compute instance start --id computeinstance-e00j2pxfys1stnqd3z` (H100) i `--id computeinstance-e00ttdn3vwkvxy53g9` (L40S); SSH po ~1.5 min.
2. Zatrzymać wszystko, co nie jest egzaminem: `pkill -f "[q]ueue.sh"; pkill -f "[g]rade_loop.sh"; pkill -f "[i]dle_shutdown.sh"`.
3. **Usunąć klucze API z obu maszyn** (zakaz zewnętrznych API w czasie egzaminu; musi być zrobione **przed pobraniem paczki po 11:00**): `rm -f ~/.fh_key ~/repo/.env ~/.cache/huggingface/token`. Sprawdzić: `ls ~/.fh_key ~/repo/.env 2>&1` → „No such file”.
4. Zsynchronizować kod z laptopa (ten sam stan co w commicie): `tar czf - --exclude=__pycache__ harness server train/templates data/kb/kompendium.jsonl data/kb/kb_all_notes.jsonl | ssh ... 'cd ~/repo && tar xzf -'`, potem porównać `md5sum harness/*.py server/final_configs.json server/exam_run.sh` z laptopem.
5. Test na sucho na mocku, bez sieci dla harnessu (`HF_HUB_OFFLINE=1` ustawia skrypt):
   `bash server/exam_run.sh assets/mock-2023 T3 tuned` → `runs/final/T3-tuned/answers.json` (37 odpowiedzi).

## 2. Egzamin (po 11:00)

1. 11:00 — wszyscy przestają pracować. Klucze usunięte z maszyn (krok 1.3), repo wypchnięte (krok 0).
2. `https://warsawmodeltrainers.dev/submissions.html?exam=final` → TEAM_KEY + link HTTPS do repo + zaznaczyć potwierdzenie zakończenia pracy → „Get final exam questions” → pobrać ZIP (link ważny 5 min; ten sam przycisk go odnawia). Paczka: `exam.json`, `images/`, `answers-template.json`.
3. Przesłać na H100 i rozpakować tak, żeby `exam.json` leżał obok `images/`:
   `scp -i ~/.ssh/id_rsa <paczka>.zip kolektyw@89.169.126.236:~/repo/exams/` i na maszynie `mkdir -p ~/repo/exams/final && cd ~/repo/exams/final && unzip ../<paczka>.zip` (jeśli ZIP ma podkatalog, przenieść jego zawartość do `exams/final/`).
4. Uruchomić:

```bash
cd ~/repo
# wszystkie trzy tracki mieszczą się naraz na H100; każdy na osobnym porcie
bash server/exam_run.sh exams/final T1 tuned 8401 &
bash server/exam_run.sh exams/final T2 tuned 8402 &
bash server/exam_run.sh exams/final T3 tuned 8403 &
bash server/exam_run.sh exams/final T2 base 8412 &   # wymagany: baseline do kategorii improvement
wait
# pozostałe przebiegi „base” (tanie; wgrywać tylko, jeśli organizatorzy zażądają)
bash server/exam_run.sh exams/final T1 base 8411 &
bash server/exam_run.sh exams/final T3 base 8413 &
wait
ls runs/final/*/answers.json
```

5. **Walidacja każdego pliku przed wgraniem** (te same reguły co strona: klucze, `exam_id` z manifestu, komplet ID, typy, ≤ 100 000 znaków, ≤ 1 MiB):

```bash
for f in runs/final/*/answers.json; do echo "$f"; python3 harness/check_answers.py "$f" exams/final/answers-template.json; done
```

6. Wgrać przez stronę zgłoszeń (formularz projektu: nazwa, modele, kategorie, `answers.json`) — kolejność: **T1, T3, potem T2** (T1 i T3 gotowe wcześniej, wynik ma zdążyć na nasz slot). Mapowanie i pola formularza — sekcja „Zgłoszenia” niżej.

- Serwery mają nadzorcę (restart po awarii CUDA), a harness ponawia zapytania przy błędach połączenia.
- Czas: pobranie i przesłanie ~2 min; pierwsza fala (T1/T2/T3 tuned + T2 base naraz) ~10 min przy arkuszu wielkości 2026 (T2 tuned gotowy po ~3 min, T1 ~9 min, T3 ~10 min), druga fala (T1/T3 base) ~1–3 min.
- Problemy techniczne zgłaszać organizatorom do 11:15 (Telegram `t.me/warsawmodeltrainers`).
- Jeśli H100 nie wstanie: te same polecenia na L40S (48 GB; tracki uruchamiać po kolei, nie naraz).
- **T2 tuned uruchamia dwa serwery**: PLLuM na podanym porcie i pomocniczy VLM opisów obrazów (Qwen3.5-0.8B, klucz `caption_server`) na porcie **+50** (8402 → 8452); oba zatrzymuje sam. Serwer opisów startuje z `GGML_CUDA_DISABLE_GRAPHS=1` (ten sam błąd mmproj Qwen3.5 co w T3, raport 21); PLLuM i T1 z grafami. W logu harnessu: „opisy obrazów: N/N w … s”. **Jeśli serwer opisów nie wstanie** (albo brak plików), `exam_run.sh` wypisuje „UWAGA: serwer opisów obrazów nie wstał” i T2 idzie dalej z samym `--ocr` — to nadal lepsze niż brak pomocy przy obrazach (raport 15: OCR+opisy > OCR > nic). Pojedyncze nieudane opisy → zadanie bez opisu, egzamin się nie zatrzymuje. Ręczne wyłączenie opisów: usunąć `caption_server` z `final_configs.json` (`--ocr` zostaje).
- Oczekiwane wyniki (luna, 2024+2025 / 2026): T1 ~71% / 84% (`--rozstrz-hint` 70.9 / 84.4%, esej rubric szac. +0.5 pp), T2 ~57% / 52% (OCR + opisy, raport 20; goły PLLuM 0%), T3 ~41% / 43% przy 1.53 GB (IQ2_M-PL-E4K-MIX-S4K-V124K, raport 18; 3 seedy 45.4 / 36.1 / 42.1%).

## 3. Po egzaminie

Zatrzymać maszyny: `nebius compute instance stop --id ...` (obie) i `fh session stop <sesja>`.

## Zgłoszenia (projekt → kategoria, pola formularza)

Najwyżej 3 projekty na zespół, każda kategoria tylko raz. W „Models used” każdy model osobno, z kwantyzacją.

| Projekt | Kategoria | `answers.json` | Models used |
|---|---|---|---|
| T1 | „Best exam score” | `runs/final/T1-tuned/answers.json` | `google/gemma-4-12B-it-qat-q4_0-gguf` — Q4_0 (QAT) + mmproj Q4_0 |
| T2 | „Biggest improvement” | `runs/final/T2-tuned/answers.json` + **base model answers: `runs/final/T2-base/answers.json`**; „most capable base model”: PLLuM-12B-base-2512 Q4_K_M | `CYFRAGOVPL/PLLuM-12B-base-2512` (GGUF `mradermacher/PLLuM-12B-base-2512-GGUF`) — Q4_K_M + LoRA F16 `pllum-v1recipe-full`; **drugi model (opisy obrazów):** `unsloth/Qwen3.5-0.8B-GGUF` — Q8_0 + mmproj F16 |
| T3 | „Smallest model passing 35%” (liczy się **największy** model w rozwiązaniu) | `runs/final/T3-tuned/answers.json` | `Qwen/Qwen3.5-4B` — własna kwantyzacja IQ2_M-PL-E4K-MIX-S4K-V124K (GGUF z BF16 `unsloth/Qwen3.5-4B-GGUF`, imatrix PL, przepis UD-IQ2_M + ffn_down/attn_qkv IQ3_XXS + ssm_out Q4_K, słownik przycięty do 126 579 tokenów) + mmproj F16 (`unsloth/Qwen3.5-4B-GGUF`) |

## Rozmiary (do formularza)

Limit (wg drużyny): model bazowy < 8 GB, łącznie z dodatkowymi modelami/nakładkami (LoRA, mmproj) < 8.8 GB. Strona: „weights up to 8 GB on disk” / „up to 12B parameters”; baza wiedzy RAG się nie liczy. T1 i T3 mieszczą się w 8 GB łącznie; **T2 od raportu 15 ma 8.72 GB łącznie** (baza 7.48 GB < 8 GB, reszta to LoRA i pomocniczy VLM do opisów obrazów) — mieści się w regule drużyny < 8.8 GB, ale nie w 8 GB, gdyby organizatorzy liczyli wszystkie pliki razem (powrót: usunąć `caption_server` z `final_configs.json`).

| Track | Model (plik) | Rozmiar |
|---|---|---|
| T1 | `gemma-4-12b-it-qat-q4_0.gguf` + `mmproj-gemma-4-12b-it-qat-q4_0.gguf` | 6.98 GB + 0.18 GB = 7.15 GB |
| T2 | `PLLuM-12B-base-2512.Q4_K_M.gguf` + LoRA `train/pllum-v1recipe-full/lora.gguf`; RAG: indeks PolQA (BM25) + `data/kb/kb_all_notes.jsonl` (dane, nie model) | 7.48 GB + 0.23 GB = 7.71 GB (≤ 8 GB) |
| T2 (pomocniczy, raport 15) | `models/unsloth/Qwen3.5-0.8B-GGUF/Qwen3.5-0.8B-Q8_0.gguf` + `mmproj-F16.gguf` (opisy obrazów dla PLLuM; `caption_server` w `final_configs.json`, port = port T2 + 50) | 0.81 GB + 0.20 GB = 1.02 GB (811 843 840 + 204 987 232 B) → **T2 razem 8 722 139 328 B = 8.72 GB** (PLLuM 7 477 204 064 + LoRA 228 104 192 + Qwen 811 843 840 + mmproj 204 987 232) |
| T3 | `Qwen3.5-4B-IQ2_M-PL-E4K-MIX-S4K-V124K.gguf` (największy plik; `~/models/custom/qwen35-4b/`, sha256 2f2a141a…) + `mmproj-F16.gguf` 0.67 GB | **1.53 GB** (1 532 889 600 B) |

Jeśli T3 zmieni plik modelu: poprawić wiersz T3 w obu tabelach, `server/final_configs.json` i linię „T3 — plik modelu” w `SOURCE.md`.

## Zmiany rano 27.09 (07:30–09:00)

- **T1 (07:30)** `--rozstrz-hint` (raporty 12, 20; 70.9 / 84.4%). **T1 (08:40)** `--essay-mode rubric --essay-rubric-fixed` (raport 22, decyzja użytkownika mimo niespełnionej reguły C: +0.63 pkt/esej na 30 parach, 2026 nie na minusie; esej = 2 pełne przebiegi z myśleniem). Powroty: `_comment_T1_old2`, `_comment_T1_old`.
- **T3 (08:00)** `--think-retry --match-retry` (raport 21-ponowienia); `exam_run.sh` ustawia dla T3 `GGML_CUDA_DISABLE_GRAPHS=1` (raport 21, awarie clip_encode pod pełnym obciążeniem 4/7 → 0/4).
- **T2 (09:00)** serwer opisów obrazów także z `GGML_CUDA_DISABLE_GRAPHS=1` (tylko ten proces; prefiks przy `serve` w `exam_run.sh`).
- Harness zunifikowany (jedna wersja `run_exam.py` ze wszystkimi flagami opt-in, domyślnie wyłączonymi); md5 w akapicie „Test na sucho” na górze.

## Zmiana z raportu 10c (27.09 ~05:45)

- **T3** przełączony z UD-IQ3_XXS (1.95 GB) na własny **`Qwen3.5-4B-IQ2_M-PL-E4K-MIX.gguf` (1 745 906 784 B)**; serwer bez zmian poza `-m` (limit myślenia 5000 + komunikat zostają); harness tuned: `--essay-mode structured` zamiast `--essay-topic-detect --essay-extend 2 --essay-min-words 300`. Wynik: 2024+2025 41.2% (s42) / 44.5% (s43), średnio 42.9%; 2026 45.0% (s42). Powrót do UD-IQ3_XXS: `_comment_T3_old2` w `final_configs.json`. **Ryzyko**: najsłabszy arkusz 40.0% (oba seedy 2025) — margines ~5 pp.
- **T3 (07:30)** przełączony na **`Qwen3.5-4B-IQ2_M-PL-E4K-MIX-S4K-V124K.gguf` (1 532 889 600 B)**: MIX z przyciętym słownikiem i ssm_out Q4_K (raport 18); 3 seedy 2024+2025 45.4 / 36.1 / 42.1% (śr. 41.2%), 2026 śr. 42.8%. Powrót do MIX: `_comment_T3_mix_old`.
- T3 base: ten sam plik co tuned, goły harness bez zmian.

## Zmiany z raportu 10 (27.09 nad ranem)

- **T3** przełączony na UD-IQ3_XXS (1.95 GB) + limit myślenia serwera `--reasoning-budget 5000` z komunikatem `reasoning_budget_message` (klucz w `final_configs.json`, `exam_run.sh` przekazuje go jako jeden argument) + harness `--essay-topic-detect --essay-extend 2 --essay-min-words 300`. Wynik: 43.3% (2024+2025, 2 seedy: 42.9 / 43.7), 41.7% (2026, s43); stary Q3_K_M: 50.0% / 48.3%. **Ryzyko**: margines nad 35% ~7–8 pp. Powrót do Q3_K_M: wartości w `_comment_T3_old` w `final_configs.json`.
- T3 base używa tego samego pliku IQ3_XXS (goły harness bez zmian).
- Test na sucho T3 tuned (3 zadania z 2024) przez `exam_run.sh` na H100: OK (finish = stop, bez powtórek, nagłówek eseju z treści).
- Tesseract (`tesseract-ocr-pol`) zainstalowany na obu maszynach (od raportu 15 T2 tuned używa `--ocr`).
