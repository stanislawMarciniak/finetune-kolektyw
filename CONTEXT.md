# CONTEXT — dla nowego agenta (stan: nd 27.09.2026, 09:00)

Zespół Kolektyw, hackathon **Warsaw Model Trainers**: lokalne modele rozwiązują maturę z historii (poziom rozszerzony). **Egzamin: nd 27.09 — o 11:00 koniec pracy, dopiero potem pytania** (TEAM_KEY + link HTTPS do zacommitowanego repo + potwierdzenie → paczka ZIP). Repo musi być wypchnięte przed 11:00. Na tym etapie nie trenujemy już nic — zostało uruchomić egzamin według `server/RUNBOOK.md` i wgrać wyniki. Szczegóły strony organizatorów: `raports/13-strona-organizatorow.md`.

## 1. Zasady konkursu (najważniejsze)

- Trzy projekty = trzy kategorie formularza finału (każda kategoria raz na zespół):
  - **T1** → „Best exam score”;
  - **T2** → „Biggest improvement” — wymaga też wgrania odpowiedzi gołej bazy (`T2-base`) w tym samym harnessie;
  - **T3** → „Smallest model passing 35%”; liczy się rozmiar **największego modelu** w rozwiązaniu.
- Limit (wg drużyny): model bazowy < 8 GB, łącznie z nakładkami (LoRA, mmproj) < 8.8 GB; strona: „weights up to 8 GB on disk” / „up to 12B parameters” (RAG się nie liczy). Podczas egzaminu **bez internetu i bez zamkniętych API** (klucze usunąć z maszyn przed pobraniem paczki).
- Wejście: paczka ZIP (`exam.json`, `images/`, `answers-template.json`; link ważny 5 min, odnawialny); wyjście: `answers.json` sprawdzony `harness/check_answers.py` i wgrany na `https://warsawmodeltrainers.dev/submissions.html?exam=final` z `TEAM_KEY`. Ocena punktowa przez sędziego AI organizatorów wg klucza CKE; wynik pokazują na ekranie w czasie naszego slotu (kolejka od 10:45, problemy techniczne do 11:15).
- Szczegóły: `raports/01-konkurs-cel-i-zasady.md`, `assets/presentations/rules&faq.pdf`.

## 2. Finalne rozwiązania (decyzja G4)

Konfiguracje serwera i harnessu: **`server/final_configs.json`** (czyta je `server/exam_run.sh`).

| Track | Model | Wynik (sędzia luna; 2024+2025 / 2026) |
|---|---|---|
| T1 | Gemma-4-12B-it QAT q4_0 + mmproj, myślenie, temp. 1.0, `--rozstrz-hint --essay-mode rubric --essay-rubric-fixed` (raporty 12, 20, 22) | 70.9%; 84.4% (3 seedy z `--rozstrz-hint`; esej rubric szac. +0.5 pp) |
| T2 | PLLuM-12B-base-2512 Q4_K_M + LoRA `pllum-v1recipe-full` + RAG (BM25 PolQA top-3 + 1 notatka z bazy wiedzy) + `--fill-fields --ocr` + serwer opisów obrazów Qwen3.5-0.8B Q8_0 + mmproj (razem 8.72 GB, raport 15; serwer opisów z `GGML_CUDA_DISABLE_GRAPHS=1`) | **56.7%; 52.5%** (2 seedy, raport 20; goła baza: 0%) |
| T3 | Qwen3.5-4B **IQ2_M-PL-E4K-MIX-S4K-V124K (1.53 GB, własna kwantyzacja z imatrix PL + przycięty słownik, raport 18)** + mmproj, myślenie oprócz eseju z limitem 5000 tokenów, temp. 0.6, esej `--essay-mode structured`, `--think-retry --match-retry`, `GGML_CUDA_DISABLE_GRAPHS=1` (raport 21) | 41.2% (3 seedy: 45.4 / 36.1 / 42.1); 42.8% (2026, 3 seedy) |

- LoRA T2: trening na Modal (H100), 2 epoki, rank 32, lr 1e-4, dane `data/sft/v2plain/train_answer.jsonl` (10 479 przykładów, bez kontekstu RAG), szablon czatu z PLLuM-instruct. Job w `overnight/modal_train.py`.
- T3 bez LoRA: LoRA z `--mask-think` niszczyła myślenie (bramka `eval/think_gate.py` → FAIL).
- Pełne uzasadnienie i porównania: `raports/09-zmiany-po-treningach.md` (przed/po, typy, epoki, zakres, obrazy, koszty), decyzje w `raports/05-plan-dzialania.md`, hipotezy i wyniki w `raports/07-hipotezy.md` (otwarta tylko H-N14 — kalibracja na próbnym zgłoszeniu).

## 3. Maszyny

| Maszyna | Adres | Rola |
|---|---|---|
| Nebius H100 `matura-h100` | `ssh -i ~/.ssh/id_rsa kolektyw@89.169.126.236`, instancja `computeinstance-e00j2pxfys1stnqd3z` | egzamin (wszystkie trzy tracki naraz) |
| Nebius L40S `matura-l40s` | `kolektyw@89.169.112.149`, instancja `computeinstance-e00ttdn3vwkvxy53g9` | zapas; ma komplet artefaktów wszystkich tracków |

- Tenant `tenant-e00j4265yye6dtbee1`. Start: `nebius compute instance start --id <instancja>` (SSH po ~1.5 min). Szczegóły: `server/NEBIUS.md`.
- Na maszynach: kod w `~/repo`, modele w `~/models/<repo HF>/`, LoRA w `~/train/`, llama.cpp w `~/llama.cpp`. Python: `~/venv-unsloth` (H100) albo `~/venv-eval` (L40S) — `server/lib_eval.sh` wybiera sam.
- **Strażnik `server/idle_shutdown.sh`** wyłącza maszynę po 45 min bez harnessu/treningu. Po restarcie maszyny trzeba go uruchomić ręcznie (nie startuje sam). W nocy maszyny powinny się wyłączyć.
- **Na obu maszynach są jeszcze klucze** (`~/.fh_key`, `~/repo/.env`) — do usunięcia przed egzaminem (RUNBOOK krok 3).
- Forgehand L40S (`ssh root@18.212.193.136`, sesja `01a0e0fa`, 30 GB RAM — tylko jeden serwer z mmproj naraz): zapas/eksperymenty, opis w `server/FORGEHAND.md`. Modal — wyczerpany.
- Test na sucho finałów (27.09 08:42, H100, `exam_run.sh` na `test2026_v2`, 4 tracki naraz): T1 tuned 533 s, T2 tuned 168 s, T3 tuned 577 s, T2 base 386 s, T3 base 59 s; bez restartów, `check_answers.py` OK (szczegóły w RUNBOOK).

## 4. Mapa repozytorium

- `harness/run_exam.py` — program egzaminacyjny `exam.json` → `answers.json` + `debug.jsonl` + `meta.json`. Prompt organizatorów, typ zadania z `answer_format`, myślenie per typ (`--think`), RAG (`--rag bm25`, `--kb-rag`, `--kb-essay`), obrazy (`--vision`), naprawa eseju (≥ 300 wyrazów, numer tematu), powtórka bez myślenia przy urwaniu, ponawianie przy błędach połączenia, `--bare` dla wariantu base. Flagi opt-in (domyślnie wyłączone; w finale tylko te z `final_configs.json`): `--fill-fields`, `--ocr`, `--caption-url`, `--rozstrz-hint`, `--match-names-hint`, `--image-tiles`, `--factcheck*`, `--vote-closed/--vote-adaptive`, `--essay-mode structured|rubric`, `--essay-rubric-fixed/-plan`, `--essay-refine-kb`, `--think-retry`, `--match-retry`, `--answer-from/--only-ids/--merge-from/--essay-from`, `--img-retrieval` (`harness/img_retrieval.py`). `harness/check_answers.py` — walidacja `answers.json` jak na stronie. `harness/topics.py` (Polska/świat), `harness/make_exam_pack.py --v2` (paczki w formacie finału ze znacznikami `[Obraz: ...]`).
- `server/` — `exam_run.sh <exam> <T1|T2|T3> <tuned|base> [port]`, `final_configs.json`, `RUNBOOK.md`, `lib_eval.sh` (`serve` z nadzorcą restartującym llama-server po awarii CUDA, `stop`, `run`), `queue.sh`, `grade_loop.sh`, `idle_shutdown.sh`, `pull.sh` (zrzut wyników z maszyn + regeneracja raportu 09), `fetch_runs.sh`, skrypty eksperymentów (`phase*`, `t2_*`, `t3_*`, `t1_*`, `exp_*`).
- `train/` — `build_sft_v2.py` (zbiór wierny harnessowi: RAFT, HyDE, warianty answer/think, manifest + STATS), `build_sft.py` (v1), `sft_lora.py` (Unsloth; `--mask-think`, `--template-from`), `sft_peft.py` (czysty PEFT/TRL), `templates/`.
- `data_gen/` — generatory danych przez API (E1 arkusze CKE, E3 syntetyczne, E4 eseje, **E5 `e5_bulk.py`** 10 tys. zadań z weryfikacją, **E6 `e6_kb.py`** baza wiedzy), `common.py` (limity kosztów), `taxonomy.json`, `cost_log.jsonl`.
- `eval/` — `grade.py` (zamknięte), `judge_openai.py` (sędzia LLM wg zasad CKE; odrzucenia filtra treści → `filtered`, poza mianownikiem), `analyze.py --registry eval/runs_registry_v2.json` (raport 09), `report.py`, `retrieval_bench.py`, `think_gate.py`, `build_exam.py`, `data/` (zbiory testowe, `scope_labels.json`).
- `overnight/` — Modal (`modal_train.py`, `modal_convert.py`), skrypty lokalne (crawl CKE, ekstrakcja PDF).
- `raports/` — 01 zasady, 02 ewaluacja, 03 benchmarki, 04 zasoby/koszty, 05 plan i decyzje, 06 datasety, 07 hipotezy, 08 analiza wyników (+ `08-wyniki-tabele.md`, `08b-wyszukiwanie.md`), 09 przed/po; 10–13 poprawki nocne, kwantyzacje T3, walidacja T1, strona organizatorów; 14–23 poranne eksperymenty (match-names, obrazy T1/T2, mały T3, reviewer faktów, głosowanie, audyt odpowiedzi `eval/audit.py`, illegal instruction i ponowienia T3, esej wg kryteriów CKE, wyszukiwanie obrazów).
- `SOURCE.md` — opis rozwiązań i odtwarzania do zgłoszenia.

Dane (w `.gitignore`, tylko lokalnie i na maszynach; wyjątki w repo: `data/kb/kompendium.jsonl`, `data/kb/kb_all_notes.jsonl` i konfiguracja adaptera LoRA T2): `assets/` (arkusze CKE, mock-2023, benchmark-2023), `exams/` (paczki testowe `test202x_v2`, `probe60_v2`), `data/sft/` (`e5_items.jsonl` 10 243 zadania; `v2`, `v2full`, `v2plain`), `data/kb/` (kompendium, oś czasu 2817, postacie 940, pojęcia 627, `kb_all_notes.jsonl`, indeks `polqa_index` 4.4 GB), `data/final_artifacts/` (kopia LoRA T2: GGUF + adapter PEFT), `runs/`, `results/`.

## 5. Ewaluacja — jak czytać wyniki

- Zbiory testowe: arkusze 2024, 2025 (główne) i 2026 (kontrolny), paczki `exams/test202x_v2`. Zadanie 2024/21 jest odrzucane przez filtr treści sędziego → wykluczone.
- Sędzia: `gpt-6-luna` przez API Forgehand. Stary sędzia był o ~4 pp łagodniejszy — porównuj tylko wyniki „luna”.
- Szum między seedami: ~2–3 pp; różnice poniżej tego traktuj jako remis.
- Klucze API: `.env` na laptopie (`OPENAI_API_KEY`, `HF_TOKEN`, `FORGEHAND_API_KEY`). Nigdy ich nie wypisuj; przekazuj przez stdin.

## 6. Pułapki (nauczone boleśnie)

- `pkill -f`/`pgrep -f` przez SSH zabija własną powłokę — używaj wzorców `"[q]ueue.sh"`.
- zsh na laptopie: `"$h:repo"` to modyfikator `:r` — pisz `"${h}:repo"`.
- Gemma 4 na H100 z `-ub 4096`, wieloma slotami i obrazami potrafi paść („illegal instruction”) — dlatego nadzorca w `lib_eval.sh serve` i ponawianie w harnessie. Dla mmproj Qwen3.5 (T3 i serwer opisów T2) przyczyną są grafy CUDA → `GGML_CUDA_DISABLE_GRAPHS=1` w `exam_run.sh` (raport 21).
- Konwerter LoRA llama.cpp nie obsługuje Qwen3.5 — trzeba scalać przez PEFT i dokopiować tensory MTP (`server/t3_merge_eval.sh`).
- Gemma-4 pt jako baza T2 odrzucona (śmieci po LoRA, niezgodność szablonu i słownika).
- Skrypty z `wait` czekały w nieskończoność na llama-server — używaj `wait_runs` z `lib_eval.sh`.

## 7. Co zostało do zrobienia

1. **Przed 11:00 (pilne):** commit i push repozytorium (dane i wagi w `.gitignore`), link HTTPS bez tokenów; ustalić, kto ma TEAM_KEY — RUNBOOK krok 0.
2. Rano (przed 10:45): H100 zsynchronizowany i przetestowany na sucho (08:42); zostaje: sync Nebius L40S (zapas), test T3 po decyzji o słowniku, zatrzymać zbędne procesy (`idle_shutdown.sh`), **usunąć klucze** — kroki w `server/RUNBOOK.md`.
3. Po 11:00: formularz „Get final exam questions” → paczka → `exam_run.sh` dla T1/T2/T3 tuned + T2 base (polecenia w RUNBOOK), `harness/check_answers.py` na każdym `answers.json`, wgrać trzy projekty (T1, T3, potem T2 z plikiem bazy). Kategorie, pola formularza i rozmiary — na końcu RUNBOOK.
4. Po egzaminie: zatrzymać maszyny (`nebius compute instance stop --id ...`).
