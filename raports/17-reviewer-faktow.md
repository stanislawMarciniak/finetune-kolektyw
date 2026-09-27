# 17 — Recenzent faktów w harnessie (nd 27.09, 05:25–07:00)

Pomysł użytkownika: po odpowiedzi model sprawdza zdanie po zdaniu fakty (daty, nazwy, kto co zrobił, przyczyny i skutki), dla błędnych zdań daje zdanie poprawione, a harness podmienia **tylko te zdania**. Cel: błędy merytoryczne, za które CKE odejmuje punkty (esej: 1–2 błędy −1, 3–5 −2, > 5 −3; otwarte: błąd = 0). Sędzia `gpt-6-luna`; pary na **tych samych** odpowiedziach (`--answer-from` + `--merge-from`), więc różnice to wyłącznie efekt recenzenta.

## Podsumowanie

| | Wynik |
|---|---|
| **Krok 0: OCR w T2 tuned** | `exam_run.sh exams/ocr_dry T2 tuned 8820` na H100: `answers.json OK: test2025_v2 6 odpowiedzi`, 0 błędów. Tekst OCR wstawiony w 12, 16.1, 21.2; `--fill-fields` zadziałał w 16.1, 19, 20, 23. Serwer zatrzymany. Tesseract `pol`, `eng`, `osd` na **obu** maszynach. `--ocr` zostaje w konfiguracji. |
| **T1 eseje** (Gemma, najlepszy wariant D: z myśleniem + notatki) | 15 par: zmienione 4 eseje, **wszystkie 5 podmian merytorycznie poprawne**; sędzia (średnia z 3–4 ocen): **+4.0 pkt na 15 esejach = +0.27 pkt/esej** (na 7 esejach konfiguracji t1final +0.57). Próg z raportu 11 (typ C): ≥ +1 pkt/esej na ≥ 6 parach → **niespełniony**. Koszt czasu: 80–450 s na esej, 3/15 urwane na 8000 tokenach. |
| **T1 eseje bez myślenia** (C) | 5 par t1final: 1 podmiana (poprawna: unia horodelska 1417 → 1413), **0 pkt** (sędzia: 2 → 1 błąd, ale 1–2 błędy to nadal −1). +8–22 s na arkusz. |
| **T1 otwarte** (B, bez myślenia) | 151 zadań (2 seedy 2024+2025 + 2026 s42): zmienione 6; z podmian 2 dobre, 2 złe, 4 obojętne; sędzia **−1 pkt**. |
| **T3** (Qwen3.5-4B IQ3_XXS) | eseje: recenzent nie zgłosił **żadnego** zdania w 6 esejach (B i C). Otwarte: 36 podmian w 22 zadaniach, ~4 dobre / ~17 złe / ~12 puste lub obojętne; sędzia **−1 pkt** (−2 / +1). |
| **T2** | nie testowane (opcjonalne; PLLuM-base przy temp. 0 jako własny recenzent — po wynikach T3 bez sensu). |
| **Decyzja** | **nie przyjęto w żadnym tracku**; `server/final_configs.json` bez zmian (poza `--ocr` w T2 tuned, dodanym wcześniej na prośbę użytkownika). Flagi zostają w harnessie jako opcja (domyślnie wyłączone). |
| **Koszt sędziego** | ≈ **0.30 $** wg cennika `judge_openai.py` (53 oceny; reszta skopiowana), limit 2.00 $. GPU: tylko H100, własne porty 8820, 8830, 8831 — wszystkie zatrzymane. |

Wniosek: mechanizm działa zgodnie z zamysłem (podmienia pojedyncze zdania, nie psuje struktury), a z pytaniem kontrolnym A/B Gemma **prawie nie wprowadza fałszywych poprawek w esejach**. Ale **pułap zysku jest niski**: sędzia odejmuje za błędy średnio ~1.2 pkt na esej T1 (1, 2, 1, 2, 0 na 5 esejach finału), recenzent łapie ~1 z ~2–4 błędów, a zejście z 2 błędów do 1 nic nie daje (ten sam próg −1). Jedyny duży zysk (+3) przyszedł z eseju, w którym poprawka usunęła rażący błąd („podbój Węgrów” przez Karola Wielkiego), co sędzia ocenił też w aspekcie merytorycznym.

## 1. Co zbudowano (`harness/run_exam.py`, wszystko za flagami; `--bare` bez zmian)

| Flaga | Co robi |
|---|---|
| `--factcheck essay,podaj,rozstrz,open` | Po odpowiedzi (po poprawkach eseju, przed normalizacją zamkniętych): podział na zdania (`fc_units`: skróty „r.”, „w.”, „np.”, inicjały, „1410 r. Jagiełło” nie dzielą zdania; pomijane: nagłówek „Temat nr N”, etykiety pól „Uzasadnienie:”, **cała linia „Rozstrzygnięcie:”** — zamiana Tak/Nie to zmiana odpowiedzi, nie faktu; zdania < 4 wyrazów). **Jedno wywołanie** na odpowiedź: ponumerowane zdania, prompt „surowy egzaminator-historyk… zgłoś tylko, gdy jesteś pewien”, wynik w liniach `[n] BŁĄD:` / `[n] POPRAWKA:` („jeśli nie znasz poprawnej wartości, usuń błędny szczegół”). Dla otwartych w prompcie treść zadania i źródła (+ obrazy przy `--vision`): „twierdzenia zgodne ze źródłami są poprawne”. |
| (filtr kształtu) | Podmiana tylko, gdy poprawka ≠ oryginał, ≥ 50% wyrazów oryginału zostaje, wydłużenie ≤ 12 wyrazów (esej) / 8 (otwarte), nie krótsza niż połowa, bez dodatkowych zdań. |
| (pytanie kontrolne, domyślne; `--factcheck-no-confirm` wyłącza) | Osobne wywołanie: „Które z dwóch zdań jest zgodne z faktami? A/B/X” w losowej (deterministycznej) kolejności; podmiana tylko, gdy model wybierze poprawkę. |
| `--factcheck-kb PATH` | Notatki BM25 **per zdanie**: zapytanie = 6 najrzadszych słów zdania (nazwy, daty) + nazwy własne tezy tematu (esej); do 2 notatek na zdanie, razem ≤ 10 (esej) / 4 (otwarte), z datą z pola `subtopic` („Unia horodelska (1413)”). Prompt: „jeśli notatka dotyczy tego samego faktu i podaje inną datę/nazwę, zaufaj notatkom”. |
| `--factcheck-think` | Recenzent i pytanie kontrolne z myśleniem (8000 / 1500 tokenów). |
| `--factcheck-max N` | Maks. podmian na odpowiedź (domyślnie 6). |
| `--answer-from DIR` | Odpowiedzi z `debug.jsonl` innego przebiegu **bez generowania** (wszystkie typy, nie tylko esej) — tylko recenzent. Do tanich par przed/po. |

Log w `debug.jsonl` → `factcheck`: liczba zdań, notatki, surowa odpowiedź recenzenta, każda zgłoszona zmiana (`old`, `new`, `why`, `pick`, `ok` = True / False / `"shape"`), `applied`. Błąd recenzenta nigdy nie zatrzymuje egzaminu (try/except → odpowiedź bez zmian). Naprawiony w trakcie błąd: dzielenie przez zero przy „zdaniu” bez liter wywracało cały arkusz (T3 2026 s43, powtórzony).

Uboczna zmiana: `NoteRetriever.search` zwraca też `sub` (pole `subtopic`); prompty innych funkcji używają tylko `title`/`text`, więc nic się nie zmienia.

Skrypty: `server/fc_run.sh <port> <wariant> <przebieg bazowy> "<zbiory>" <argumenty>` (`KINDS=essay` ogranicza typy), `server/fc_judge.sh <budżet> [filtr]`, analiza `/tmp/fc_ana.py`. Paczka testowa `exams/ocr_dry` (2025: 12, 16.1, 19, 20, 21.2, 23 z obrazami).

## 2. Warianty i przebiegi

Bazy: T1 `gemma4-qat-t1final__s42` (2024, 2025, 2026) i `__s43` (2024, 2025); T3 `q35-4b-iq3xxs__nt3rbE3-s43` (2024–2026), `__nt3rbE3fix-s42` (2026), `__nt3rb-s42` (2024, 2025; ten sam serwer, bez poprawek eseju). Dodatkowe eseje T1 do par (wariant D): `gemma4-qat__nt1final-s44`, `-legacy__s42/s43`, `-t1kb__s42/s43` (2024, 2025).

| Wariant | Typy | Myślenie | Notatki | Status |
|---|---|---|---|---|
| A | eseje + otwarte | tak | per zdanie, pełne zdanie | **przerwany** po 25 min: H100 współdzielone z 5 innymi serwerami → 13 tok/s na slot; Qwen dochodził do limitu 5000 tokenów w 53/55 wywołaniach. Nie do użycia na egzaminie. |
| B | eseje + otwarte | nie | per zdanie, pełne zdanie (słabe trafienia: „Zniesienie monarchii w Rumunii” przy Jagielle) | T1 5 arkuszy, T3 6 arkuszy |
| C | eseje | nie | **najrzadsze słowa + temat, z datą z `subtopic`** | T1 5 esejów, T3 6 esejów |
| D | eseje | tak | jak C | T1 15 esejów |

## 3. T1 — Gemma-4-12B QAT

### Eseje (pary na tych samych esejach; sędzia 3× na zmienionych, średnia; oryginał liczony razem z pierwotną oceną)

| Esej | przed | C (bez myślenia) | D (myślenie) | Co zmieniono |
|---|---|---|---|---|
| 2024 t1final s42 | 9 | 9 (bez zmian) | 9 (bez zmian) | „BRAK BŁĘDÓW” (sędzia: 2 błędy — „system lenny”, „Pax Karolina”; interpretacyjne) |
| **2024 t1final s43** | **9.25** (9, 11, 9, 8) | 9 (podmiana odrzucona w A/B) | **12.33** (11, 13, 13) | „Langebanków i Węgrów” → „Saksonów i Longobardów” |
| 2025 t1final s42 | 6.25 (6, 6, 7, 6) | 6.33 (6, 7, 6) | 6.33 (= C) | unia horodelska 1417 → **1413**; sędzia 2 → 1 błąd, potrącenie nadal −1 |
| 2025 t1final s43 | 5 | 5 | 5 | zgłoszone „Jagiełło z dynastii Piastów” — odrzucone w A/B (słusznie) |
| 2026 t1final s42 | 12 | 12 | 12 | „BRAK BŁĘDÓW” |
| 2025 t1kb s42 | 9 (9, 9, 9, 9) | — | 9 (9, 9, 9) | usunięte „odzyskanie Pomorza Gdańskiego” po Grunwaldzie; 2 → 1 błąd, potrącenie bez zmian |
| 2025 nt1final s44 | 4.75 (4, 4, 6, 5) | — | 5.67 (4, 9, 4) | usunięty „Stefan Batory” z listy Jagiellonów (szum sędziego ±3) |
| pozostałe 8 (legacy, t1kb, s44 2024) | — | — | bez zmian | 3 urwane na 8000 tokenach (447 s), 5 bez zgłoszeń lub odrzucone |
| **Suma** | | **+0.1 pkt / 5 esejów** | **+4.0 pkt / 15 esejów (+0.27/esej)**; na 7 esejach t1final **+4.0 (+0.57/esej)** | |

Trafność zmian w esejach (D + C, ręcznie): **5 podmian, 5 poprawnych, 0 fałszywych**. Pytanie kontrolne odrzuciło 4 zgłoszenia: 2 błędne poprawki (Jagiełło „z dynastii Piastów”; chrystianizacja Litwy 1387 → 1386 — 1387 jest dobrze) i 2 poprawne (2024 s43 w C, „system folwarczny” u Karola Wielkiego w s44). **Recall niski**: na 5 esejach t1final sędzia liczy 11 błędów, recenzent poprawił 2.

### Otwarte (B, bez myślenia; 151 zadań na 5 arkuszach)

- 514 zdań, 55 zgłoszeń, 15 odrzuconych filtrem kształtu, 32 w pytaniu A/B, **8 podmian w 7 zadaniach** (1 to esej 2024 s43 z B: „Longobardów i innych ludów”, sędzia 9 → 12).
- Ręcznie: **2 dobre** (Ruryowiczów → Rurykowiczów; wspomniany esej), **2 złe** (2024/7: „Bolesław Wstydliwy” → „Władysław II Jagiełło, XIV w.” — oba błędne, właściwie Krzywousty; 2024/24: usunięte prawdziwe „wystąpienie Węgier z Układu Warszawskiego”), 4 obojętne (np. „powołania Senatu” → „wolnych wyborów do Senatu”).
- Sędzia na zmienionych otwartych: **−1 pkt** (2025/18 s43: 3 → 2 po dopisaniu „w 1871 roku” — raczej szum); reszta bez zmian.

## 4. T3 — Qwen3.5-4B UD-IQ3_XXS

- **Eseje (B, C): 0 zgłoszeń w 6 esejach** — Qwen zawsze odpowiada „BRAK BŁĘDÓW” (1 raz urwane). Eseje T3 dostają ~1/15 pkt, więc błędy nie są ich główną słabością.
- **Otwarte (B)**: 1027 zdań, 203 zgłoszenia, 101 odrzuconych filtrem kształtu (często „poprawka” = to samo zdanie), 66 w pytaniu A/B, **36 podmian w 22 zadaniach**. Ręcznie (33 pierwsze): ~4 dobre (2026/13 „rok 1863 odnosi się do samej bitwy”, 2026/11 „eksportera surowców”, 2026/24, 2025/21.2), **~17 złych** (np. 2025/18: „1871: Utworzenie Cesarstwa Niemieckiego” → „Rok 1871 to nie utworzenie Cesarstwa Niemieckiego”; 2025/12: banknot „emitowany przez Xyst (kościół) w Warszawie”; PPS „1894 → 1892” przy „Robotniku”), ~12 pustych/obojętnych.
- Sędzia: **−1 pkt** (2025/12 s43 1 → 0, 2026/20 s43 1 → 0, 2026/24 s42 2 → 3). Mały model „poprawia” dobre fakty na złe — dokładnie ryzyko z założeń.

## 5. Przykłady

| # | Zdanie oryginalne | Werdykt recenzenta | Podmiana | Efekt u sędziego |
|---|---|---|---|---|
| 1 | T1 2024 s43 (esej): „Poprzez liczne podboje (m.in. Saksonów, Langebanków i Węgrów) oraz unifikację struktur władzy, stworzył potężne państwo…” | „błędna nazwa ludu (Langebanków zamiast Longobardów) oraz błędne wskazanie podbitego ludu (Węgrzy nie byli podbici przez Karola Wielkiego)”; A/B: poprawka | „…(m.in. Saksonów i Longobardów)…” | 9.25 → **12.33** (3 oceny; sędzia przed: „błędy obejmują m.in. podbój Węgrów, błędną nazwę Longobardów”) |
| 2 | T1 2025 s42 (esej): „Kluczowym momentem było zawarcie unii horodelskiej (1417)…” | „błędna data unii horodelskiej” (notatka „Unia horodelska (1413)” — dopiero po poprawce wyszukiwania; w B recenzent zgłosił zdanie, ale „poprawka” była identyczna) | „…(1413)…” | błędy 2 → 1, **punkty bez zmian** (6.25 → 6.33): próg CKE 1–2 błędy = −1 |
| 3 | T1 2024/7 s42 (rozstrzygnij): „…konflikt między Henrykiem V czeskim a Bolesławem Wstydliwym… w XIII wieku” | „postacie z różnych epok” | B: „…a Władysławem II Jagiełłą… w XIV wieku” (błąd → inny błąd; w wariancie z myśleniem A/B tę samą propozycję z Łokietkiem odrzucił) | 0 → 0 |
| 4 | T3 2025/18 s43 (otwarte): „1871: Utworzenie Cesarstwa Niemieckiego (unification).” | „Rok 1871 to nie utworzenie Cesarstwa Niemieckiego.” | to samo zdanie (fałsz) | bez zmiany punktów, ale fałszywa poprawka przeszła i filtr kształtu, i A/B |

## 6. Czas

- **C (eseje, bez myślenia)**: 8–22 s na esej (1–2 krótkie wywołania) — pomijalne (+~0.3 min/arkusz).
- **D (eseje, myślenie)**: 80–450 s na esej (1.4–8 tys. tokenów), 3/15 urwane na 8000 → esej jest i tak najdłuższym zadaniem, więc **+1.5–7.5 min na arkusz** na H100 dzielonym przez 3 tracki.
- **B (otwarte + eseje, bez myślenia)**: ~50 tokenów/zadanie, ale każde zadanie z obrazem wysyła obrazy drugi raz; przy 5 arkuszach naraz na zatłoczonym H100 17 min na arkusz (przebieg bazowy 3–10 min). Realnie +2–4 min/arkusz.

## 7. Decyzja

- **T1: nie przyjęto.** Eseje: +0.27 pkt/esej (D, 15 par; +0.57 na 7 esejach finałowej konfiguracji), próg typu C z raportu 11 to ≥ +1 pkt/esej na ≥ 6 parach; na seedzie 42 zysk 0 (remis), na s43 +3 z jednego eseju. D kosztuje do 7.5 min na arkusz i bywa urwany. C (tani) daje 0. Otwarte: −1 pkt, 2 złe podmiany na 8. Remis → zostaje obecna konfiguracja.
- **T3: nie przyjęto.** Eseje bez efektu, otwarte −1 pkt przy ~50% złych podmian.
- **T2:** nietestowane.
- **Pułap zgodny z audytem (raport 20):** w eseju T1 na 2024+2025 odjęcia za błędy merytoryczne to tylko **3.3 pkt** strat, a „aspekty powierzchowne” 12.3 pkt (T3: 5.8 vs 18.4). Recenzent faktów może więc odzyskać co najwyżej ~0.8 pkt na esej, a z progiem CKE (1–2 błędy = −1) realnie mniej. Nawet idealny recenzent nie spełni progu ≥ +1 pkt/esej; większą stratę niesie płytkość aspektów, na którą recenzent faktów nie działa.
- `server/final_configs.json`: **bez zmian** z tego raportu. Jeśli koordynator chce zaryzykować w T1 (tylko eseje, zero fałszywych podmian na 5): `--factcheck essay --factcheck-kb data/kb/kb_all_notes.jsonl` (C, +~20 s) — spodziewany zysk ~0; z `--factcheck-think` (D) ~+0.3–0.6 pkt/arkusz za kilka minut czasu. Nie testowane przez `exam_run.sh`.

## Uwaga dla innych agentów: `judge_reuse.py` kopiuje oceny z przebiegów sędziego sol

`eval/judge_reuse.py` bierze ocenę identycznej odpowiedzi z **dowolnego** przebiegu tego samego zbioru — także z `…__sol` (sędzia `gpt-6-sol`) i powtórek. Przy `--merge-from` niezmienione zadania dostały więc czasem oceny sol zamiast luny: T1 2025 s42 wyszło 43 → 45 pkt bez żadnej zmiany odpowiedzi (2025/3.1 i 7.1 0 → 1 — to dokładnie rozbieżności luna/sol z raportu 11). W tym raporcie porównywane są wyłącznie zadania zmienione przez recenzenta, a niezmienione mają ocenę bazy. Porównując przebiegi `--merge-from` całymi arkuszami, wyklucz `__sol` z puli `known` w `judge_reuse.py` albo porównuj tylko zmienione zadania.
