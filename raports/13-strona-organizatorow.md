# 13 — Strona organizatorów: ocenianie, formaty, przebieg finału (stan: nd 27.09, 05:05)

Źródła pobrane tylko do odczytu (GET, bez rejestracji, bez wysyłania): `https://warsawmodeltrainers.dev/` (`/`, `/matura.html`, `/submissions.html`, `/submissions.mjs`, `/submission-validation.mjs`, `/submission-config.mjs`, `/exams/mock-manifest.json`, `/exams/history-2023-mock-v1.zip`, `/rules`), przewodnik `https://matura-json-guide.ania-olchowik.chatgpt.site/` oraz publiczne widoki Supabase (`https://sbbneffipmmqduwuvxog.supabase.co/rest/v1/...`, klucz publiczny z kodu strony). Surowe kopie: `/tmp/wmt/`; kluczowe pliki w repo: `assets/wmt_site/`.

## TL;DR — co zmienia nasze plany

1. **Termin jest odwrotny, niż zakładaliśmy.** O 11:00 kończy się praca, a nie oddawanie. Arkusz finałowy odblokowuje się dopiero po 11:00 (`final_unlocked: false` o 04:57). Zespół potwierdza w formularzu, że przestał pracować, podaje link do repozytorium i dopiero wtedy dostaje paczkę (link ważny 5 minut).
2. **Dostarczenie odpowiedzi = paczka ZIP + wgranie `answers.json`,** tak samo jak w mocku. Nie ma interaktywnego klienta. Nasz harness pasuje bez przeróbek: `exam.json` z `items` → `answers.json` = `{exam_id, answers:[{id, answer}]}`.
3. **Link do repozytorium jest wymagany, zanim dostaniemy pytania**: „Your code, prompts, settings, and harness must be committed before you access the test questions.” **Nasze lokalne repo nie ma ani jednego commita i nie ma zdalnego repozytorium.** To teraz najpilniejsza sprawa.
4. **Ocena jest punktowa (częściowa), nie zero-jedynkowa:** wyniki mają postać np. 53/60 i 47/60. Oceniają organizatorzy, „AI-graded”, według klucza CKE, po pobraniu plików. Zielone i czerwone pola „live exam” to stary prototyp (pula geograficzna), który jest schowany (`REG_ONLY = true`).
5. **Limit rozmiaru:** strona główna podaje „weights up to 8 GB on disk”, regulamin i FAQ „up to 12B parameters”. Wartości 8.8 GB nie ma nigdzie. Wszystkie nasze artefakty mieszczą się poniżej 8·10⁹ B (czyli także poniżej 8 GiB).
6. **Kategorie finału** odpowiadają naszym trackom: „Best exam score” (T1), „Biggest improvement (requires base model answers)” (T2), „Smallest model passing 35%” (T3). Zasada dla T3: „**the largest model you use determines your size**”.
7. **Konkurencja na mocku 2023:** najlepszy wynik to 88.33% (LockedIn, Gemma), potem 78.33% (100dniDoMatury, Bielik-11B; ArtificialTeam, Bielik INT8). Nasz T1 na mocku miał 78.3% według naszego sędziego (luna), ale **nie wgraliśmy go**. W T3 zespół fabryka.ai ma 36.67% na Bielik-1.5B Q4_K_M (0.97 GB), czyli mniej niż nasze 1.95 GB.

## 1. Ocenianie

- `matura.html`: „Mock results — AI-graded against the official May 2023 history marking guide”, „Final — AI-graded against the final exam marking guide”.
- README paczki mock: „It does not judge correctness on upload. **Organizers download the original answers and grade against the CKE rubric.**” Przy wgraniu: „A successful upload means received, not graded.”
- Formularz: „We check the file format immediately. Organizers grade your answers later.”
- **Granulacja: punkty częściowe.** Publiczne RPC `mh_public_mock_results` zwraca tylko sumy (`score`, `max_points`, `percentage`), bez szczegółów per zadanie. Nie wiadomo, jakim modelem oceniają. Test organizatorów na arkuszu syntetycznym „history-synthetic-c-v2” (Gemma 3 4B BF16) dał 29/60 = 48.33%.
- „Green means correct, red means wrong” dotyczy prototypu „live exam” (`mh_public_runs`, `mh_exam_questions`, `mh_public_answers`). Są tam 14 pytań geograficznych `GEO-*` (typy `numeric`, `single`, `tflist`, zestaw `probny`) i przebiegi „Dry Run Team” oraz „Tarasiuk Lab” z 25–26.09. Kod rejestracji wspominał „exam script… comes on Saturday”, ale opublikowana instrukcja to paczka ZIP i wgranie pliku: „The submission service receives answers only.”
- **Format odpowiedzi zamkniętych** (README): „For choices/matching/true-false, follow the item's `answer_format`. Those examples show syntax, NOT solutions.” W mocku występują wzory: `A` (wybór), `1: P\n2: F\n3: P` (P/F), `1: A\n2: A` (kilka wyborów), `A: 1\nB: 1` (dopasowanie). Esej to jeden tekst z numerem tematu, co najmniej 300 słów (przewodnik: „Include the chosen topic number and at least 300 words”). Każda odpowiedź musi być napisem, po polsku, bez śladów rozumowania i logów czatu. Odpowiedź pusta `""` jest dozwolona.
- Sędzia AI raczej zrozumie „A: USA” jako „Stany Zjednoczone” (nasz `grade.py` jest surowszy, patrz raport 10c), ale numer zamiast imienia władcy to 0 pkt.

## 2. Przebieg finału i dostarczenie

Z `submissions.html?exam=final` i `submissions.mjs`:

1. Formularz „Get final exam questions”: TEAM_KEY, **link HTTPS do repozytorium** (walidacja `^https://host/ścieżka`, bez tokenów i parametrów) oraz zaznaczenie „Our team has stopped working on all projects. Our code is committed… We will not change any project after receiving the questions.” Serwer zapisuje czas („We record the server time when you get access”).
2. `POST functions/v1/final-exam` zwraca `download_url` i `manifest` (`exam_id`, `item_ids`). Na stronie: „Download link valid for 5 minutes; use this button again to renew it.” Paczka zawiera `exam.json`, `images/` i `answers-template.json` („Use the answers template supplied in your exam package”).
3. Uruchamiamy gotowe modele i harness („you may run your finished models and harnesses and submit answers. You must not train, edit, or improve this project or any other project”).
4. Wgranie pliku (`mh_submit_final_project`): nazwa projektu, lista modeli (nazwa/link + kwantyzacja, każdy model osobno, do 20), **kategorie** (jedna do trzech), `answers.json`. W kategorii improvement dochodzi plik odpowiedzi modelu bazowego i wybór „most capable base model”. Najwyżej 3 projekty na zespół, każda kategoria tylko raz: „The same project result counts in all its selected categories.”
5. **Nie ma limitu czasu na pytanie ani na arkusz** ani w kodzie, ani w tekście strony. Regulamin: „Sunday 11:00 — stop… Report technical problems by 11:15”, „Exam and presentation on Sunday, from 11:00 on stage… order shown on screen from 10:45”, „Your model's score on the final exam sheet appears on screen”. Wynik ma więc być gotowy przed naszym wystąpieniem, bo organizatorzy muszą zdążyć ocenić → **wgrywać jak najszybciej**.
- **Internet:** paczkę pobiera i wgrywa się przez przeglądarkę. README pozwala liczyć gdziekolwiek („Run on your laptop, AWS, Modal, or another environment”). Zakaz dotyczy harnessu: „No internet during the exam — RAG on a local knowledge base only”, „may not call a closed API… or a second model beyond the limit”. Nasz układ (H100 przez SSH, bez kluczy, `HF_HUB_OFFLINE=1`) nie łamie tych zasad.
- Walidacja pliku (`submission-validation.mjs`): na najwyższym poziomie tylko `exam_id` i `answers`; `exam_id` równy manifestowi; każdy wpis ma dokładnie `{id, answer}`, oba jako napisy; każde ID z manifestu dokładnie raz, bez nieznanych; odpowiedź ≤ 100 000 znaków; plik ≤ 1 MiB; puste odpowiedzi są tylko ostrzeżeniem.

## 3. Terminy

| Kiedy | Co |
|---|---|
| do 11:00 | koniec pracy; kod zacommitowany (i wypchnięty) |
| od 10:45 | na ekranie kolejność wystąpień |
| po 11:00 | `final_unlocked` → potwierdzenie gotowości → paczka (link na 5 min) |
| do 11:15 | zgłaszanie problemów technicznych |
| od 11:00 | egzamin i prezentacje na scenie; wynik na ekranie, 2–3 min prezentacji + 1–2 min pytań |
| 13:00–13:45 | obrady jury; 14:00 wyniki |

Punktacja w regulaminie: 40% wynik finału, 40% przyrost względem bazy, 20% prezentacja. Formularz finału dzieli jednak na trzy kategorie. **To niespójność — pytanie do organizatorów.**

## 4. Limity rozmiaru

- Strona główna: „Pick any open model with downloadable weights up to 8 GB on disk — quantized is fine”. Rejestracja: „Base model (weights up to 8 GB on disk)”. Regulamin i FAQ: „any model with downloadable open weights, **up to 12B parameters**”, „A RAG knowledge base doesn't count towards the limit”. Dyskwalifikacja za „a model over the limit”.
- Jednostka GB nie jest zdefiniowana (10⁹ czy 2³⁰). Nie wiadomo też, czy liczą się mmproj i LoRA. Przy naszych rozmiarach nie ma to znaczenia (tabela niżej).
- T3: „For smallest model, **the largest model you use** determines your size” — liczy się największy model w rozwiązaniu, a nie suma.

Dokładne rozmiary (`ls -l`, identyczne na H100 i L40S):

| Track | Plik | Bajty |
|---|---|---|
| T1 | `gemma-4-12b-it-qat-q4_0.gguf` | 6 975 879 296 |
| T1 | `mmproj-gemma-4-12b-it-qat-q4_0.gguf` | 175 115 616 |
| **T1 razem** | | **7 150 994 912** (7.15 GB / 6.66 GiB) |
| T2 | `PLLuM-12B-base-2512.Q4_K_M.gguf` | 7 477 204 064 |
| T2 | `train/pllum-v1recipe-full/lora.gguf` | 228 104 192 |
| **T2 razem** | | **7 705 308 256** (7.71 GB / 7.18 GiB) |
| T3 | `Qwen3.5-4B-UD-IQ3_XXS.gguf` (największy) | **1 949 047 968** (1.95 GB / 1.82 GiB) |
| T3 | `mmproj-F16.gguf` | 672 423 616 |
| T3 razem | | 2 621 471 584 (2.62 GB) |
| RAG (nie liczy się) | `~/repo/data/kb` | 4 712 556 049 (H100) |

Wszystko jest poniżej 8·10⁹ B. Ryzyko „12B parameters”: PLLuM-12B (baza Mistral-Nemo) i Gemma-4-12B mają realnie ~12.2B parametrów. Inne zespoły też używają modeli „12B” (Gemma-4-12B, Gemma 3 12B) i przechodzą. Warto jednak zapytać.

## 5. Schemat pytań

- Oficjalny `exam.json` (mock i zapowiedziany finał, „separate pack and exam ID”): `exam_id`, `title`, `source_exam_id`, `source_url`, `input_format: "separate-text-and-images-v1"`, `language`, `max_points`, `instructions`, `items[]`. Każdy item ma: `id` (napis), `group`, `max_points`, `question`, `source_text` (ze znacznikami `[Obraz: images/Z01.png]`), `images[] = {path, source_page, sha256}` i `answer_format`. **Nasza kopia `assets/mock-2023/exam.json` jest bajtowo identyczna z plikiem ze strony (`cmp`).** To dokładnie format, który czyta `run_exam.py`.
- `pytania-FORMAT.json` („questions” albo goła lista) to format panelu organizatora dla prototypu live exam (`id`, `set`, `type`, `question`, `options`, `points`, `topic`, `ord`), a nie paczki finałowej. Dla bezpieczeństwa harness przyjmuje teraz i ten format (sekcja 7).
- Odpowiedź: `{"exam_id": ..., "answers": [{"id": "2.1", "answer": "..."}]}`. Kolejność dowolna.

## 6. Konkurencja (mock 2023, 45 ocenionych zgłoszeń, stan 04:57)

Najlepsze zgłoszenie każdego zespołu (rozwiązanie, nie baseline):

| Zespół | Projekt | Modele / kwantyzacja | Wynik |
|---|---|---|---|
| LockedIn | Gema1 | „Gema1 [quancik]” (wcześniej Gemma-4-12B-it Q4_K_XL: 45/60) | **53/60 = 88.33%** (baseline 45/60) |
| 100dniDoMatury | v5-tourne(.1) | speakleash/Bielik-11B-v2 [BF16] (w BF16 to ~22 GB, ponad limit 8 GB — pewnie opis niedokładny) | 47/60 = 78.33% |
| ArtificialTeam | BASE DROP | bielik INT8 | 47/60 = 78.33% |
| Sam (Altman) | wqie53 | Gemma-4 Q6_K | 43/60 = 71.67% |
| sofa so good | Gemma 3 12B Q4_K_S + essay rules | Gemma 3 12B Q4_K_S + mmproj F16 | 42/60 = 70.00% |
| Ania (organizator, test) | istniejące odpowiedzi Qwen | — | 33/60 = 55.00% |
| Sara | Bielik 4.5B Q8_0 + RAFT LoRA + Qwen3-VL-2B | Bielik-4.5B Q8_0 | 26/60 = 43.33% (baseline 30%) |
| Sara | Gemma 3 4B IQ4_XS | **2.26 GB** + mmproj F16 | 25/60 = 41.67% |
| fabryka.ai | MAW: Bielik-1.5B sft2 + RAG + OCR + Qwen3.5-0.8B | **Bielik-1.5B Q4_K_M 972 797 184 B**; Qwen3.5-0.8B Q5_K_M 795 MB | **22/60 = 36.67%** (baseline Bielik-1.5B Q8_0: 18.33%) |
| sofa so good | Qwen3.5-4B UD-IQ3_XXS + Qwen3.5-2B | Qwen3.5-4B UD-IQ3_XXS | 24/60 = 40.00% (baseline 16.67%) |
| Tarasiuk Lab | Qwen2.5-7B-AWQ | AWQ | 12/60 = 20.00% |

Wnioski:
- **T1:** nasz T1 miał na mocku 78.3% według luny (`runs/mock-2023/gemma4-qat-t1final`), czyli poziom 2.–3. miejsca. Lider ma 88.33%. Mock 2023 jest publiczny i część zespołów mogła się do niego dopasować, a my nie znamy ich wyników na świeżych arkuszach. **Nie mamy żadnego zgłoszenia na mocku, więc nie wiemy, jak sędzia organizatorów ocenia nasze odpowiedzi (H-N14).**
- **T3:** fabryka.ai (największy model 0.97 GB, 36.67% na mocku) jest mniejsza od nas (1.95 GB) i przechodzi próg 35% z marginesem ~1.7 pp. Sara (Gemma 3 4B, 2.26 GB, 41.67%) i sofa so good (ten sam Qwen3.5-4B UD-IQ3_XXS, 40%) mają rozmiar podobny do naszego. Jeśli fabryka.ai utrzyma ≥ 35% w finale, wygra T3. Jeśli spadnie poniżej, liczymy się my. Zależy też, czy „rozmiar” to GB czy liczba parametrów (1.5B < 4B tak czy inaczej).
- **T2 (improvement):** Sara +13.3 pp, fabryka +18.3 pp, sofa so good +23.3 pp, LockedIn +13.3 pp. Nasz T2: goła baza 0% → ~42–53%, więc duża przewaga.

## 7. Porównanie z naszym pipeline'em i poprawki

| # | Niezgodność / ryzyko | Stan | Poprawka |
|---|---|---|---|
| 1 | Brak commita i zdalnego repozytorium, a link HTTPS jest wymagany przed pobraniem pytań | **PILNE, niezrobione** | Przed 11:00: `git add` (dane w `.gitignore`), commit, push na GitHub (public albo private z dostępem dla organizatorów i jury), `SOURCE.md` ze zdaniem wymaganym przez regulamin |
| 2 | Brak TEAM_KEY / rejestracji zespołu (lineup miał być do sob. 16:00); nie ma nas w tabeli mocka | **PILNE** | Ustalić, kto w zespole ma TEAM_KEY; od razu wgrać mock T1 (`runs/mock-2023/gemma4-qat-t1final/answers.json`) dla kalibracji |
| 3 | CONTEXT/RUNBOOK: „oddanie do 11:00” | błąd założeń | Przepisać harmonogram (sekcja 8) |
| 4 | Wzór dopasowania „A: 1”, gdy polecenie wymaga nazw (2024/11.1, 2025/4, 5.1, 11.1, 2026/6.1, 21) — model czasem wpisuje numery; `normalize_closed` dodatkowo redukował „A: Karol IX (1560–1574)” do „A: 1560” | **zrobione** | `run_exam.py --match-names-hint`: wskazówka w treści zadania i brak redukcji do liczby dla takich zadań. Warunek `match_wants_names`: dopasowanie, wzór z cyfrą i polecenie bez słów „numer/cyfr/liczb/oznacz/liter”. Mock 2.2 („wpisz numer fragmentu”) nie łapie się, więc zachowanie bez zmian |
| 5 | Pytania mogłyby przyjść jako `questions` albo goła lista | **zrobione** (zabezpieczenie) | `load_exam()` w `run_exam.py`: `items` bez zmian; `questions`/lista → `items` (`points` → `max_points`, domyślne `source_text`/`images`/`answer_format`, `exam_id` z nazwy katalogu, ostrzeżenie na stderr) |
| 6 | Walidacja zgodna ze stroną przed wgraniem | **zrobione** | `harness/check_answers.py <answers.json> <answers-template.json lub exam.json>` — te same reguły co `submission-validation.mjs` (klucze, exam_id, komplet ID, typy, 100 000 znaków, 1 MiB) |
| 7 | `exam_id` bierzemy z `exam.json`, strona porównuje z manifestem | OK | `check_answers.py` z `answers-template.json` z paczki to wychwyci |
| 8 | Wariant `--bare` nie normalizuje zamkniętych | świadome | Baseline potrzebny tylko w improvement (T2); nie zmieniać |
| 9 | Przebiegi base dla T1 i T3 | do decyzji | Formularz wymaga baseline tylko w improvement. Regulamin wymienia jednak dyskwalifikację za „no untouched-model (benchmark) submission for the model that sits the exam”. Puszczać base równolegle (tanio), ale wgrywać tylko w projekcie T2; zapytać organizatorów |
| 10 | Format odpowiedzi zamkniętych | OK | `normalize_closed` daje dokładnie składnię `answer_format` (`A`, `1: P`, `1: A`, `A: x`) |
| 11 | Obrazy | OK | `path` względem katalogu `exam.json`; `--vision` wysyła PNG |

Test poprawek: `python -m py_compile harness/run_exam.py` OK; `load_exam` na `assets/mock-2023` (37 items), na syntetycznym `{"questions": [...]}` i na gołej liście OK; `match_wants_names` łapie tylko zadania z nazwami (lista wyżej), na mocku nic; `normalize_closed(..., names=True)` zachowuje „Karol IX (1560–1574)”; `check_answers.py` na `runs/mock-2023/gemma4-qat-t1final/answers.json` → OK. Domyślne zachowanie harnessu (bez flagi) jest bez zmian.

**Do synchronizacji na maszyny:** `harness/run_exam.py`, `harness/check_answers.py` (po zakończeniu edycji drugiego workera w `run_exam.py`). Jeśli koordynator zdecyduje, dopisać `--match-names-hint` do `harness` w `server/final_configs.json` dla T1 tuned i T3 tuned. T2 lepiej nie ruszać: LoRA była trenowana na treści bez wskazówki, a dopisek zmienia prompt.

## 8. Proponowane zmiany w RUNBOOK (nie wprowadzone)

1. **Nowy krok 0 (przed 11:00):** commit i push repozytorium na GitHub, link HTTPS bez tokenów. Sprawdzić `SOURCE.md`. Przygotować TEAM_KEY.
2. **Krok „Egzamin”** zastąpić sekwencją: (a) o 11:00 wszyscy przestają pracować; (b) `https://warsawmodeltrainers.dev/submissions.html?exam=final` → TEAM_KEY + link do repo + potwierdzenie → „Get final exam questions” → pobrać ZIP w ciągu 5 min (w razie czego odnowić); (c) `scp`/`tar` na H100 do `~/repo/exams/final/` i rozpakować (`exam.json` obok `images/`); (d) `exam_run.sh` jak dotąd; (e) `python3 harness/check_answers.py runs/final/<T>-<var>/answers.json exams/final/answers-template.json`; (f) wgrać trzy projekty.
3. **Mapowanie projektów na kategorie:** T1 → „Best exam score”; T2 → „Biggest improvement” + plik `T2-base/answers.json` jako base model answers (model bazowy: PLLuM-12B-base-2512 Q4_K_M); T3 → „Smallest model passing 35%”. Każda kategoria tylko raz na zespół.
4. **Pola „Models used”** (każdy model osobno, z kwantyzacją):
   - T1: `google/gemma-4-12B-it-qat-q4_0-gguf` — „Q4_0 (QAT), mmproj Q4_0” (7 150 994 912 B);
   - T2: `CYFRAGOVPL/PLLuM-12B-base-2512` (GGUF mradermacher) — „Q4_K_M + LoRA F16 (pllum-v1recipe-full)” (7 705 308 256 B);
   - T3: `unsloth/Qwen3.5-4B-GGUF` — „UD-IQ3_XXS (1 949 047 968 B) + mmproj F16”.
5. **Priorytet czasu:** wynik ma być na ekranie w naszej kolejce, więc najpierw wgrać T1 (i T3), potem resztę. Szacunek: pobranie i przesłanie ~2 min, T1 ~10–15 min, T3 ~10–20 min, T2 ~2 min.
6. W CONTEXT.md poprawić: „oddanie do 11:00” → „stop o 11:00, potem pytania”; „8.8 GB” → „8 GB on disk / 12B parametrów”.

## 9. Pytania do organizatorów (Telegram t.me/warsawmodeltrainers)

1. Do kiedy trzeba wgrać odpowiedzi z finału? Przed naszym wystąpieniem na scenie, czy jest wspólny termin?
2. Czy liczenie na zdalnej maszynie GPU (Nebius, przez SSH, bez internetu w harnessie) jest w porządku w czasie egzaminu? README mówi „Run on your laptop, AWS, Modal…”, regulamin mówi „bring your laptop or a model ready to run on our station”.
3. Punktacja: 40/40/20 z regulaminu czy trzy osobne kategorie z formularza?
4. „Smallest model”: rozmiar w GB na dysku czy w parametrach? Czy liczy się mmproj (encoder obrazu) jako osobny model?
5. Limit 8 GB: 10⁹ czy 2³⁰ B? Czy LoRA liczy się do rozmiaru modelu bazowego? Czy „12B” oznacza nominalną nazwę (PLLuM-12B, Gemma-4-12B ~12.2B)?
6. Czy przebieg base (benchmark) jest wymagany dla każdego projektu, czy tylko w kategorii improvement?
7. Czy wynik baseline 0% (goły model base bez szablonu czatu) jest akceptowany jako „most capable base model that can answer the exam on its own”?
8. Jakim modelem i promptem ocenia sędzia AI i czy daje punkty za zadania zamknięte przy drobnych różnicach zapisu (np. „USA” zamiast „Stany Zjednoczone”)?
