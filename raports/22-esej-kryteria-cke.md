# 22 — Esej T1 pod konkretne wymagania CKE (nd 27.09, 07:50–08:40)

Cel: podnieść elementy eseju T1 (Gemma-4-12B QAT, finał) z „powierzchownej” / „zadowalającej” do „bogatej” argumentacji samym harnessem (bez treningu). Sędzia `gpt-6-luna`, eseje 2024 / 2025 / 2026, 5 seedów (42–46), oceniany tylko esej.

## Wynik w skrócie

- **Nie przyjęto** — żaden wariant nie spełnia reguły C z raportu 11 (≥ +1 pkt/esej na ≥ 6 parach, 2026 nie na minusie); najbliżej jest FK z **+0.93**. T1 w `server/final_configs.json` **bez zmian**, więc nie było testu na sucho przez `exam_run.sh`. T3 nie testowany (warunek „jeśli T1 zyska” niespełniony).
- Najlepsza procedura: `--essay-mode rubric --essay-rubric-fixed` (pierwszy esej jak dotąd, potem nowy esej na **ten sam temat** z wymaganiami CKE dla jego elementów). Dwa niezależne przebiegi po 15 par: F **+0.33**, FK (to samo + refine z bazą v1, ale refine przyjęty tylko w 4/15, bo skracał esej) **+0.93 pkt/esej**; razem **+0.63 pkt/esej na 30 parach**, 2026 +10 pkt na 10 parach (nie na minusie). Elementów „bogata” jest więcej (baza 4, F 12, FK 10 na 45), ale błędy merytoryczne rosną **2.3 → 3.6–3.9 na esej**, a odjęcia zjadają dużą część zysku. 2025 (Jagiełło) jest niestabilne: F −4, FK +9 pkt na 5 parach.
- Wersje jednoprzebiegowe (wskazówka w poleceniu przed wyborem tematu) **szkodzą** (−0.7 do −1.2 pkt/esej): Gemma zmienia temat (5–7 z 15 esejów, np. 2024 z Karola Wielkiego na wojny z Turcją, 3 pkt) i zmyśla konkrety, gdy wymagamy „4 faktów na element”.
- Wniosek: ograniczeniem nie jest instrukcja, tylko wiedza 12B. Słabe elementy (społeczno-gospodarczy Karola Wielkiego, ustrojowy i gospodarczy Jagiełły) po wymuszeniu szczegółów dostają zmyślone daty i nazwy („unia krzyżacka 1385”, „Akt Hołdu w Horodle z 1410”, „plan Modrzewie”).

## A. Konkretne wymagania CKE dla eseju (zasady oceniania 2024–2026, tekst identyczny)

Źródło: `assets/cke/{2024,2025,2026}/zasady.txt` (część „Dodatkowe informacje dla egzaminatorów”), to samo co `eval/essay_rubric_cke.txt`. CKE nie podaje liczby faktów ani listy wymaganych faktów dla tematu; przy tematach wypisuje tylko wymagania podstawy programowej (np. dla Piłsudskiego: „ocenia wpływ J. Piłsudskiego, R. Dmowskiego… porównuje ich wizje Polski”).

| Poziom elementu | pkt | Definicja CKE |
|---|---|---|
| bogata | 4 | argumentacja **rzeczowa, pogłębiona**, poparta **trafnie dobraną i szczegółową faktografią** oraz **adekwatną terminologią**; **szeroka**, jako całość **wnikliwa analiza** problemu z tematu |
| zadowalająca | 3 | rzeczowa, **prawidłowa** faktografia i terminologia, **elementy refleksji / głębszego namysłu** |
| powierzchowna | 1 | **uogólnienia**, niewnikająca w istotę rzeczy, mało dokładna, **podstawowa** faktografia, **czasami bez przykładów** |

- Tabela A (0–12): 12 = 3 × bogata; 11 = 2 bogate + zadowalająca; 10 = bogata + 2 zadowalające; 9 = 3 × zadowalająca albo 2 bogate + powierzchowna; … Element zrealizowany tylko częściowo funkcjonalnie ciągnie całość do niższego wiersza tabeli.
- **Funkcjonalność**: trzeba zająć stanowisko wobec tezy i przekonująco je uzasadnić wiedzą z **trzech elementów/obszarów wskazanych w temacie**. Fakty, postacie i procesy muszą być adekwatne do tematu **i do zajętego stanowiska**; „bezrefleksyjne referowanie wszystkiego, co pamięta” bez odniesienia do tezy = niefunkcjonalne (0).
- **Błędy merytoryczne** (odejmowane od A, bez punktów ujemnych): 1–2 → −1, 3–5 → −2, > 5 → −3. Rodzaje: **chronologia** (złe umiejscowienie w czasie), **terminologia**, **związki przyczynowo-skutkowe** (złe przyczyny/skutki).
- **B (0–3)**: ≥ 300 słów; spójność wstęp – rozwinięcie – zakończenie; każdy akapit wynika z poprzedniego; zaburzenia m.in. wnioski niewynikające z wywodu, wątki poboczne, „zazębianie” wątków, skróty myślowe, niefunkcjonalne dygresje, brak wskaźników zespolenia.

Sędzia (`eval/judge_openai.py`, `SYSTEM_ESSAY`): dostaje pełny tekst powyżej, tematy i liczbę słów; ocenia tylko pierwszy wybrany temat, każdy element osobno (bogata/zadowalająca/powierzchowna/brak), liczy odrębne błędy i stosuje odjęcia; powtórzenia fragmentów traktuje jako zaburzenie spójności. W praktyce luna nagradza konkretne, **poprawne** nazwy i daty z wyjaśnionym skutkiem, a karze uogólnienia („wspierał rozwój miast i handlu”) i każdy błędny szczegół — także zbyt kategoryczne twierdzenia i przypisanie zjawiska innej epoce („folwark za Jagiełły”).

Z tego wymagania, które wpisałem do promptu: każdy z trzech elementów w osobnym akapicie, w kolejności z tematu; w każdym 2–3 (wersja pierwsza: 4) pewne fakty z datą i nazwą własną, wyjaśnione (co, dlaczego, skutek); co najmniej jeden związek przyczyna → skutek; zdanie oceny wiążące argument z tezą; przy tezie wartościującej („najbardziej”, „najwybitniejszy”, „przede wszystkim”, „niesłusznie”) porównanie z alternatywą albo kontrargument; pokrycie całego okresu (ramy czasowe z tematu, całe panowanie, przyczyny – przebieg – skutki); wstęp z kontekstem i stanowiskiem, zakończenie bez nowych faktów; 450–600 wyrazów; wyraźnie: błąd jest gorszy niż brak szczegółu.

## B. Co zaimplementowano (`harness/run_exam.py`, wszystko za flagami; domyślnie bez zmian)

| Flaga | Działanie |
|---|---|
| `--essay-mode rubric` | Do polecenia eseju dopisywane `RUBRIC_HINT`: wymagania najwyższego poziomu CKE jak wyżej + **elementy każdego tematu wyciągnięte z treści** (`essay_aspects`: „Temat 1: militarny, ustrojowy, społeczno-gospodarczy”; „Temat 3: wydarzenia z trzech wybranych państw bloku komunistycznego (każde to osobny element…)”) + ramy czasowe z tezy (np. „temat 2: 1871–1914”). Po odpowiedzi `rubric_clean`: usuwa wstępne komentarze („Ponieważ nie załączyłeś tekstów…”, „Wybrałem temat nr 1. Temat: … Rozwiązanie:”), separatory `***` i przepisany temat w nagłówku; zostawia „Temat nr N”. |
| `--essay-rubric-plan` | z `rubric`: najpierw jawny plan (stanowisko, ramy czasowe, na element: fakty; przyczyna → skutek; ocena), potem esej według planu (2 wywołania z myśleniem). |
| `--essay-rubric-fixed` | z `rubric`: pierwszy esej **bez** wskazówek (wybór tematu jak dotąd), potem nowy esej na ten sam temat z `RUBRIC_HINT` tylko dla tego tematu; przyjmowany przy tym samym temacie, ≥ 300 wyrazach i nieuciętym wyjściu (15/15 przyjętych). Działa z `--essay-from` (pary na tych samych esejach i tematach) i z `--essay-refine-kb`. |

Skrypty: `server/ek22_run.sh` … `ek22_run5.sh` (warianty), `server/ek22_judge.sh` (ściąga `ek22*` z obu maszyn, kopiuje oceny identycznych odpowiedzi, ocenia eseje luną). Pierwsza wersja `rubric_clean` ucinała wstęp zapisany w linii nagłówka („Temat nr 1 Wiek VIII…”) — poprawione; eseje z pierwszej fali (R) odtworzone z pola `raw` przed oceną (`/tmp/ek22/reclean.py`).

## C. Wyniki (15 par: 3 arkusze × 5 seedów; baza = eseje finału T1 tych samych seedów)

Baza: s42/s43 `gemma4-qat-t1final`, s44 `gemma4-qat__nt1final-s44`; 2026 s43/s44 i wszystkie s45/s46 — nowe eseje bazowe (`ek22B-*`, obecny T1 tuned harness). Warianty:
- **R** — `rubric`, wersja pierwsza (4 fakty na element, „wybierz temat, o którym znasz najwięcej pewnych faktów”), 1 wywołanie;
- **RP** — R + `--essay-rubric-plan` (tylko s42–44);
- **S** — `rubric`, wersja obecna (2–3 pewne, wyjaśnione fakty; bez sugestii wyboru tematu);
- **SK** — S + `--essay-refine-kb data/kb/kb_all_notes.jsonl --essay-refine-think` (baza v1, drugie przejście z raportu 10);
- **F** — `rubric --essay-rubric-fixed --essay-from <baza>` (ten sam temat co baza, esej pisany od nowa);
- **FK** — F + refine z bazą v1 (jak SK).

| Wariant | esejów | śr. pkt | Δ vs baza (pary) | pary ≥ +1 / ≤ −1 | 2026 Σ Δ | b / z / p (suma) | śr. błędów | śr. B | śr. wyrazów | zmiana tematu vs baza |
|---|---|---|---|---|---|---|---|---|---|---|
| baza | 15 | 8.07 | +0.00 | 0 / 0 | +0 | 4 / 21 / 20 | 2.3 | 2.93 | 359 | 0 |
| F | 15 | 8.40 | +0.33 | 8 / 4 | +5 | 12 / 15 / 18 | 3.9 | 3.00 | 459 | 0 |
| FK | 15 | 9.00 | +0.93 | 10 / 3 | +5 | 10 / 22 / 13 | 3.6 | 3.00 | 481 | 0 |
| SK | 15 | 8.53 | +0.47 | 8 / 6 | -4 | 8 / 22 / 15 | 3.0 | 2.87 | 498 | 6 |
| S | 15 | 7.40 | -0.67 | 6 / 6 | -9 | 6 / 16 / 23 | 3.5 | 3.00 | 456 | 5 |
| R | 15 | 7.20 | -0.87 | 5 / 8 | -8 | 5 / 19 / 21 | 4.1 | 2.93 | 481 | 7 |
| RP | 9 | 6.67 | -1.22 | 2 / 6 | -4 | 3 / 11 / 13 | 5.6 | 2.67 | 497 | 3 |

Poziomy elementów: b = bogata, z = zadowalająca, p = powierzchowna (w kolejności elementów tematu); e = liczba błędów wg sędziego; B = spójność; pogrubione = suma pkt (0–15), w nawiasie Δ wobec bazy tego samego seeda.

| Arkusz / seed | baza | F | FK | SK | S | R | RP |
|---|---|---|---|---|---|---|---|
| 2024 / 42 | T1 zpz e2 B3 **9** | T1 bpb e3 B3 **10** (+1) | T1 zpb e3 B3 **9** (+0) | T1 bzb e3 B3 **12** (+3) | T2 ppp e6 B3 **3** (-6) | T1 bpb e4 B3 **7** (-2) | T1 bzb e3 B3 **12** (+3) |
| 2024 / 43 | T1 zpb e4 B3 **9** | T1 bpb e6 B3 **9** (+0) | T1 bpz e4 B3 **9** (+0) | T2 pzp e5 B2 **5** (-4) | T1 zpz e2 B3 **9** (+0) | T2 zpp e2 B3 **7** (-2) | T1 zpb e7 B3 **8** (-1) |
| 2024 / 44 | T1 zpb e3 B3 **9** | T1 bpb e4 B3 **10** (+1) | T1 zpz e6 B3 **7** (-2) | T1 bpz e5 B3 **9** (+0) | T1 bpb e5 B3 **10** (+1) | T1 bpb e4 B3 **10** (+1) | T2 ppp e5 B2 **3** (-6) |
| 2024 / 45 | T1 zpb e2 B3 **10** | T1 bzb e3 B3 **12** (+2) | T1 bpb e2 B3 **11** (+1) | T3 zbp e3 B3 **9** (-1) | T2 zpz e3 B3 **8** (-2) | T2 ppp e7 B3 **3** (-7) | — |
| 2024 / 46 | T1 zpb e2 B3 **10** | T1 bpb e3 B3 **10** (+0) | T1 bpb e2 B3 **11** (+1) | T1 bpb e5 B3 **9** (-1) | T1 bpb e4 B3 **10** (+0) | T2 zzz e1 B3 **11** (+1) | — |
| 2025 / 42 | T1 zpp e2 B2 **6** | T1 ppp e7 B3 **3** (-3) | T1 zpp e6 B3 **4** (-2) | T1 zzp e3 B2 **7** (+1) | T1 ppp e7 B3 **3** (-3) | T1 ppp e8 B3 **3** (-3) | T1 ppp e8 B3 **3** (-3) |
| 2025 / 43 | T1 zpp e3 B3 **5** | T1 ppp e6 B3 **3** (-2) | T1 zzp e5 B3 **8** (+3) | T1 zpp e6 B3 **4** (-1) | T1 zpp e4 B3 **5** (+0) | T1 zpp e6 B3 **5** (+0) | T1 zpp e8 B2 **4** (-1) |
| 2025 / 44 | T1 ppp e3 B3 **4** | T1 zpp e6 B3 **5** (+1) | T1 zpp e7 B3 **5** (+1) | T1 zzp e2 B3 **9** (+5) | T1 zpp e4 B3 **5** (+1) | T1 zpp e5 B3 **6** (+2) | T1 zpp e8 B3 **5** (+1) |
| 2025 / 45 | T1 zpp e5 B3 **5** | T1 ppp e7 B3 **3** (-2) | T1 zzp e2 B3 **9** (+4) | T3 zzz e3 B3 **10** (+5) | T3 zzz e2 B3 **11** (+6) | T1 zpp e4 B3 **5** (+0) | — |
| 2025 / 46 | T1 zpp e4 B3 **5** | T1 bpp e3 B3 **7** (+2) | T1 zzp e3 B3 **8** (+3) | T1 zzp e1 B3 **9** (+4) | T1 zzp e6 B3 **7** (+2) | T2 zzz e2 B2 **10** (+5) | — |
| 2026 / 42 | T2 zzz e0 B3 **12** | T2 zzz e1 B3 **11** (-1) | T2 bbz e1 B3 **13** (+1) | T3 zzp e3 B3 **8** (-4) | T2 bbz e1 B3 **13** (+1) | T3 zzz e2 B3 **11** (-1) | T3 zzz e3 B3 **10** (-2) |
| 2026 / 43 | T3 zzp e1 B3 **9** | T3 zzz e3 B3 **10** (+1) | T3 zbz e4 B3 **11** (+2) | T3 zbz e1 B3 **12** (+3) | T3 zzp e0 B3 **10** (+1) | T3 zpz e3 B3 **8** (-1) | T3 zpz e4 B2 **7** (-2) |
| 2026 / 44 | T1 zpz e3 B3 **8** | T1 zpz e4 B3 **8** (+0) | T1 zpz e6 B3 **7** (-1) | T3 zbp e2 B3 **9** (+1) | T3 ppp e4 B3 **4** (-4) | T3 zbp e2 B3 **10** (+2) | T3 pzz e4 B3 **8** (+0) |
| 2026 / 45 | T2 zzp e0 B3 **10** | T2 zbz e0 B3 **14** (+4) | T2 zzz e0 B3 **12** (+2) | T3 ppp e2 B3 **5** (-5) | T3 zzp e3 B3 **8** (-2) | T3 zpp e5 B3 **5** (-5) | — |
| 2026 / 46 | T3 zzp e0 B3 **10** | T3 zzz e2 B3 **11** (+1) | T3 zbz e3 B3 **11** (+1) | T3 zzz e1 B3 **11** (+1) | T3 ppp e2 B3 **5** (-5) | T3 zzp e6 B3 **7** (-3) | — |

Obserwacje:
- **Zmiana tematu** to główna strata wersji jednoprzebiegowych: baza w 2024 i 2025 zawsze bierze temat 1; z wskazówką R/S/SK przechodzą na temat 2 (wojny z Turcją) albo 3 w 5–7 z 15 esejów i tam zwykle wypadają gorzej (2024/s42 S: 3 pkt). F usuwa to z definicji (0 zmian).
- **Bogata rośnie tylko przy stałym temacie**: F ma 12 elementów „bogata” (baza 4), zwłaszcza 2024 (Karol Wielki: polityczny i kulturowy — missi dominici, Admonitio generalis 789, Alkuin, minuskuła karolińska) i 2026 s45 (bogata + 2 zadowalające, 0 błędów, 14 pkt).
- **Błędy rosną z każdą wersją, która żąda więcej konkretów**: 2.3 (baza) → 3.5 (S) → 3.9 (F) → 4.1 (R) → 5.6 (RP). Na Jagielle (2025) F traci 3 razy po 2–3 pkt przy 6–7 błędach; słabego elementu (ustrojowy, społeczno-gospodarczy) wskazówka nie naprawia — dalej „powierzchowna”, tylko z błędami.
- Plan jawny (RP) szkodzi najbardziej: plan utrwala zmyślone fakty, a esej je rozwija (2025: 8 błędów we wszystkich 3 seedach).
- Refine z bazą v1 (SK vs S) obniża błędy 3.5 → 3.0 i daje ~+1.1 pkt/esej, czyli podobnie jak w raporcie 10 (+0.77) — to refine, nie wymagania CKE, niesie zysk SK. W FK refine prawie nie działa (przyjęty 4/15: esej po rubric ma ~480 wyrazów, a poprawka wychodzi krótsza i jest odrzucana), więc FK to w 11/15 esejach po prostu druga próbka F. Różnica F vs FK (+0.33 vs +0.93) to zatem głównie szum próbkowania i sędziego — dlatego uczciwa ocena procedury to średnia z obu: +0.63 pkt/esej.
- B praktycznie bez zmian (2.9–3.0); `rubric_clean` usuwa komentarze typu „Ponieważ nie załączyłeś tekstów…”, ale sędzia i tak rzadko za nie karał.

## D. Przykłady

1. **Plus (F, 2026 s45, temat 2 — rewolucja przemysłowa; 10 → 14 pkt).** Baza, aspekt gospodarczy: „ten sam proces doprowadził do ogromnego skwantyfikowanego rozwarstwienia majątkowego. Kapitał koncentrował się w rękach wąskiej grupy właścicieli fabryk…” (sędzia: „argumentacja pozostaje dość ogólna … aspekt kulturowy powierzchownie, bez konkretnych przykładów”). F, aspekt społeczny: „…gwałtowną urbanizacją i powstaniem przeludnionych, niehigienicznych slumsów w miastach takich jak Manchester. Praca dzieci w kopalniach i fabrykach … Jednakże te dramatyczne warunki stały się bezpośrednią przyczyną powstania ruchów robotniczych oraz przełomowych reform ustawodawczych, takich jak Factory Act z 1833 roku … W konsekwencji…” (sędzia: „uzasadnia stanowisko konkretnymi przykładami … nie stwierdzono jednoznacznych błędów”; b w aspekcie gospodarczym).
2. **Minus (R, 2025 s42, Jagiełło; 6 → 3 pkt, 8 błędów).** „Kluczowym wydarzeniem było zawarcie unii krzyżackiej w 1385 roku…”, „Kluczowym dokumentem był Akt Hołdu w Horodle z 1410 roku…”, „…kampanie przeciwko Zakonowi Livoński”. Sędzia: „argumentacja w każdym aspekcie pozostaje powierzchowna, a część przykładów jest błędna … określenie unii z 1385 r. jako krzyżackiej, datowanie unii horodelskiej na 1410 r. oraz przypisanie Jagielle rozwoju folwarku”. Żądanie „4 faktów na element” wytwarza fakty, których model nie zna.

## E. Koszty, czas, maszyny

- Sędzia: **$0.88** z limitu $1.50 (≈ $0.0095 za esej; 92 eseje łącznie z nowymi bazami). Eseje z kopiowanymi zadaniami: pozostałe zadania dostają oceny przez `judge_reuse` (bez kosztu).
- GPU: własne serwery Gemmy na H100 (port 8577) i L40S (port 8578), zatrzymane po przebiegach. H100 był równolegle obciążony próbami egzaminu innych agentów (T1/T2/T3 `exam_run`), więc przebiegi tam 2–3× wolniejsze (~10–16 tok/s na slot).
- Czas zadania eseju: baza 20–70 s (H100 bez obciążenia); `--essay-rubric-fixed` = 2 pełne eseje z myśleniem: 90–420 s na obciążonym H100, FK 230–400 s na L40S (8 równoległych esejów). Na egzaminie esej idzie równolegle z innymi zadaniami, więc przebieg T1 wydłużyłby się o ~2–5 min.
- Harness zsynchronizowany na obie maszyny (tylko nowe flagi; lokalna wersja zawiera też zmiany innych agentów, np. `add_img_hints`, niczego nie cofałem). Na L40S nadpisałem `runs/test2026_v2/gemma4-qat-t1final__s42` lokalną kopią (potrzebna jako `--essay-from`; ten sam przebieg ściągnięty wcześniej).

## F. Rekomendacja

- T1 zostaje bez zmian (reguła C niespełniona). Jeśli koordynator mimo to chce grać na esej, jedyna procedura dodatnia na wszystkich trzech arkuszach łącznie i bez straty na 2026 to `--essay-mode rubric --essay-rubric-fixed` (+0.63 pkt/esej na 30 parach ≈ +0.5 pp wyniku na arkusz; szum sędziego ±1–3 pkt/esej; +2–5 min przebiegu). Wtedy dopisać tylko te dwie flagi na końcu T1 tuned harness (po `--rozstrz-hint`), bez `--essay-refine-kb` (w FK prawie nie działał), i zrobić test na sucho przez `exam_run.sh`.
- Dalsza droga to wiedza, nie instrukcja: notatki bazy v1 **per element przed pisaniem** (a nie tylko refine po), albo wymaganie konkretów tylko w elementach, dla których są notatki. Wersja „4 fakty na element” i jawny plan — nie używać.
