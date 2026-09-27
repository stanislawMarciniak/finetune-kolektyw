# 20 — Audyt odpowiedzi finałów i wariantów bliskich najlepszym (nd 27.09, 06:00–07:00)

Sędzia `gpt-6-luna`, oceny wyłącznie istniejące (koszt sędziego **$0**, GPU nieużywany). 2024/21 poza mianownikiem. Wynik główny = 2024 + 2025 (119 pkt), potwierdzenie = 2026 (60 pkt). Strata = max − średnia z seedów. Buduje na raporcie 12: jego ręczne kategorie błędów (T1, T2) są w skrypcie jako priorytet, reszta z heurystyk na komentarzu sędziego, `debug.jsonl` i odpowiedzi.

- **Skrypt:** `eval/audit.py` (grupy przebiegów: `eval/audit_groups.json`, etykiety epok i rodzajów obrazów: `eval/audit_labels.json`). Pełne tabele: `raports/20-audyt-tabele.md`.
- Nowy wariant bez edycji plików: `python eval/audit.py --add 'T1-vote=T1:T1-final:test2024_v2=runA,runB;test2025_v2=runA' --only T1-vote`; zrzut jednego zadania we wszystkich grupach: `--item test2024_v2/25`.
- Uwaga do danych: `gemma4-qat__nt1img1120-s44` na H100 jest pusty (seed przerwany), więc 1120 ma 2 seedy. Brak zadań z epoki po 1989 w arkuszach 2024–2026.

## Grupy i wyniki (średnia z seedów)

| Grupa | Przebiegi | 2024+2025 | 2026 |
|---|---|---|---|
| **T1 finał** (Gemma QAT t1final) | s42, s43, nt1final-s44; 2026: s42 + fx-t1base-s43 | 70.3% | 83.3% |
| T1 `--rozstrz-hint` | fx-t1rh-s42/43/44 | 70.9% | 84.4% |
| T1 `--image-min-tokens 1120` | nt1img1120-s42/43 | 73.5% | 80.0% |
| T1 `--essay-refine-kb` z bazą v1 / z bazą v3 (dwa warianty, nie dwa seedy: każda liczba to średnia s42+s43, na 2026 jeden seed; poza esejem odpowiedzi skopiowane z finału, więc porównanie z finałem sparowanym = 71.0% / 83.3%) | nt1ref(kb3)-t1final s42/43 | 73.1 / 75.2% | 81.7 / 80.0% |
| **T2 finał** (`--fill-fields --ocr` + caption Qwen 0.8B) | img-t2ocrcap-a/b | 56.7% | 52.5% |
| T2 poprzedni finał (fill-fields, bez pomocy obrazowej) | img-t2base-a/b | 48.3% | 50.0% |
| T2 tylko OCR / tylko caption | img-t2ocr-a/b, img-t2cap-a/b | 51.3 / 57.1% | 48.3 / 46.7% |
| T2 finał z 01:00 (bez fill-fields) | polqa, kbab-v1, fx-t2base | 52.4% | 47.8% |
| T2 HyDE / kb-rag-k 2 / k 3 / OCR (pełne przebiegi) | nt2hyde, nt2k2, nt2k3, nt2ocr | 51.3 / 53.8 / 56.3 / 49.6% | — |
| **T3 finał** (IQ2_M-PL-E4K-MIX + esej structured) | struct2-s42/s43; 2026: s42 | 42.9% | 45.0% |
| T3 poprzedni UD-IQ3_XXS + limit 5000 | nt3rb-s42, nt3rbE3-s43, stock bf5k-s42; 2026: E3-s43, E3fix-s42 | 44.3% | 42.5% |
| T3 IQ3_XXS-PL-E4K | cq-…-e4k__final-s42 | 42.0% | 50.0% |

## Podsumowanie — 5 wzorców

1. **Esej to największa pojedyncza strata we wszystkich trackach, i to głównie „aspekty powierzchowne”, a nie błędy faktów.** Strata na eseju (2024+2025): T1 16.0 z 35.3 pkt, T2 17.0 z 51.5, T3 28.5 z 68.0. Z tego kryterium A „aspekty” to T1 12.3, T2 13.0, T3 18.4 pkt; błędy merytoryczne (odjęcia) tylko 3.3 / 4.0 / 5.8. T3 dostaje za esej 0–2/15 pkt (2026: 0).
2. **„Rozstrzygnij” z identyfikacją źródła to największa strata poza esejem.** Wynosi T1 6.0 + 5.5 (2026), T2 18.0 + 9.5, T3 12.5 + 9.0 pkt. Typowy przebieg: rozstrzygnięcie jest dobre, ale jedno ze źródeł (mapa, znaczek, winieta gazety, drugi tekst) zidentyfikowane błędnie, więc 0 pkt. 8 z 10 zadań trudnych dla wszystkich tracków to „rozstrzygnij” (tabela niżej).
3. **Obraz: T2 zyskał najwięcej, ale obrazy nadal kosztują najwięcej.** Źle odczytany obraz: T1 10.0 / 3.0, T2 15.0 / 7.5, T3 6.5 / 4.0 pkt (2024+2025 / 2026). Najtrudniejsze są mapy i plany (2024/14.1, 2025/14.1, 2026/12.2, 2024/5.1), znaczki i monety (2026/13, 2026/18.x) oraz rysunki satyryczne. Pomoc obrazowa T2 (OCR + caption) daje **+10 pkt na 2024+2025 (+8.4 pp), bootstrap po zadaniach 95% CI [+5, +16] pkt, i +1.5 pkt na 2026** wobec wersji bez pomocy. To jedyna zmiana w tym audycie, która jest wyraźnie ponad szumem.
4. **T3 przegrywa na gołych faktach, T1 i T2 nie.** Wiedza/fakt: T3 17.0 + 8.0 pkt, T1 5.3 + 1.0, T2 7.5 + 4.0. Najwięcej traci na „podaj” (14.5 pkt na 3 arkuszach), np. data godziny „W”, konfederacja warszawska, prymas Wyszyński („Karol Wojtyła”). W 10 zadaniach T1 i T2 mają ≥ 67% punktów, a T3 ≤ 34%.
5. **Straty formalne i harnessu są już małe, a nasz grader nie jest za surowy.** Odpowiedź niepełna: T2 1 + 1 pkt (było 5 + 6 przed `--fill-fields`, raport 12), T1 0. Harness (fallback bez myślenia): T1 1.3 pkt, T3 3.0 + 2.0. Za surowa auto-ocena zamkniętych (synonimy: „Zakon Franciszkanów”, „Benedyktynowie/Jezuita”, „USA”): T1 2.0, T3 1.0 pkt na 2024+2025. To zaniża nasze wyniki, więc wynik u organizatorów może być o ~0.5–1 pkt/arkusz wyższy, nie niższy.

**Epoki:** T1 nie ma wyraźnie słabej epoki (1–4 pkt na epokę). T2 traci najwięcej w latach 1914–39 (9.5 + 4.5 pkt), ale to błędy obrazu i rozumowania, nie wiedzy. T3 traci najwięcej w nowożytności (11.0 pkt) i średniowieczu (8.5 pkt), głównie na faktach (zakony, dopasowania władców, nazwy dokumentów). Wszystkie modele wybierają najczęściej temat średniowieczny w eseju (Karol Wielki, Jagiełło).

## Straty finałów wg typu i rodzaju błędu (pkt; 2024+2025 / 2026)

| Typ (max 24+25) | T1 | T2 | T3 |
|---|---|---|---|
| zamknięte: wybór (6) | 0.7 / 0 | 1.0 / 3.0 | 2.5 / 1.0 |
| zamknięte: P/F (8) | 2.0 / 0 | 4.0 / 2.0 | 1.0 / 2.0 |
| zamknięte: dopasowanie (6) | 2.3 / 0 | 2.0 / 2.0 | 5.5 / 2.0 |
| podaj (24) | 4.7 / 0.5 | 3.5 / 2.5 | **12.5** / 4.0 |
| rozstrzygnij (28) | 6.0 / **5.5** | **18.0** / **9.5** | **12.5** / **9.0** |
| wyjaśnij/uzasadnij (17) | 3.7 / 1.0 | 6.0 / 3.5 | 5.5 / 0 |
| esej (30) | **16.0** / 3.0 | **17.0** / 6.0 | **28.5** / **15.0** |
| **razem** | 35.3 / 10.0 | 51.5 / 28.5 | 68.0 / 33.0 |

| Rodzaj błędu | T1 | T2 | T3 |
|---|---|---|---|
| wiedza/fakt | 5.3 / 1.0 | 7.5 / 4.0 | **17.0 / 8.0** |
| źle odczytany obraz | **10.0** / 3.0 | **15.0 / 7.5** | 6.5 / 4.0 |
| źle odczytany tekst źródła | 0.7 / 3.0 | 4.0 / 3.5 | 6.0 / 2.0 |
| rozumowanie/logika | 0 / 0 | 6.0 / 5.5 | 4.0 / 2.0 |
| polecenie/format | 0 / 0 | 1.0 / 1.0 | 2.0 / 0 |
| odpowiedź niepełna | 0 / 0 | 1.0 / 1.0 | 0 / 0 |
| harness (fallback) | 1.3 / 0 | 0 / 0 | 3.0 / 2.0 |
| grader za surowy (tylko ewaluacja) | 2.0 / 0 | 0 / 0 | 1.0 / 0 |
| esej A aspekty / A błędy / B spójność | 12.3 / 3.3 / 0.3 (24+25) | 13.0 / 4.0 / 0 | 18.4 / 5.8 / 4.3 |

Typ × epoka (suma strat trzech finałów, 3 arkusze): „rozstrzygnij” traci najwięcej w XIX w. (16.3 pkt) i średniowieczu (12.5 pkt), „podaj” w latach 1914–39 (10.3 pkt), „wyjaśnij” w latach 1945–89 (12.0 pkt, rysunki satyryczne 2024/25 i 2026/24). Pełne tabele (także rodzaj obrazu i źródła): `raports/20-audyt-tabele.md`, sekcje B–D.

## Zadania trudne dla wszystkich tracków (każdy finał ≤ 34% punktów)

| Zadanie | Typ, epoka | T1 / T2 / T3 (śr. pkt) | Dlaczego |
|---|---|---|---|
| 2024/14.1 | rozstrz, XIX, mapa | 0 / 0 / 0 | mapa wojny 1809 czytana jako 1812 albo wojna polsko-bolszewicka |
| 2025/14.1 | rozstrz, XIX, mapa + herby | 0 / 0 / 0 | który herb z powstania styczniowego — obraz |
| 2026/12.2 | rozstrz, nowożytność, plan bitwy | 0 / 0 / 0 | T1: „Nie”, Wiedeń dobrze, plan = „Kamieniec 1675” zamiast Chocimia |
| 2024/5.1 | rozstrz, średniowiecze, mapa | 0.33 / 0 / 0 | wyprawy Wikingów czytane jako krucjaty |
| 2026/18.2 | rozstrz, 1914–39, znaczek | 0 / 0 / 0 | znaczek (Wersal) dobrze, tekst z Poczdamu przypisany Wersalowi |
| 2026/19.1 | rozstrz, 1914–39, winieta gazety | 0 / 0 / 0 | złe datowanie źródła 2. (maj 1926) — tu `--rozstrz-hint` dał T1 3/3 |
| 2024/7 | rozstrz, średniowiecze, tekst | 0 / 0 / 0 | chronologia: Krzywousty (1109) vs Bolesław Śmiały; T1 datuje na XIII–XIV w. |
| 2025/22 | rozstrz, II wojna, tekst | 0.33 / 0 / 0 | Armia Andersa vs kościuszkowcy — T1 myli z „Armią Berlinga”/„PSZ na Zachodzie” |
| 2024/11.1 | dopasowanie, nowożytność | 0.33 / 0 / 0 | Karol IX / Henryk IV — T1 s43 „Małgorzata”, s44 „Henryk III” |
| 2024/19.2 | podaj, 1914–39, znaczek | 0.33 / 0 / 0 | Litwa Środkowa → Żeligowski (T1 s43 „Kościuszko”, s44 „Piłsudski”) |

Razem ~10 pkt na 3 arkusze, czyli ~3 pkt/arkusz nie do zdobycia żadnym obecnym trackiem. 6 z 10 to identyfikacja obrazu albo źródła w „rozstrzygnij”.

## Gdzie tracki się różnią (46 zadań z różnicą ≥ 67 pp; pełna lista w tabelach, sekcja F)

- **T2 rozwiązuje, T1 nie (fakty z RAG PolQA):** 2025/9.3 (T1 3/3 „Wojny religijne we Francji”, klucz: noc św. Bartłomieja), 2025/19 (T2 2/2 po `--fill-fields`; T1 zmyśla prezydentów: „Paderewski 1929”, „Kasprzycki”), 2026/6.2, 2026/17 (T1: „zabór rosyjski” mimo „c.k.”). RAG zasila tu konkretną nazwę albo datę. W T1 RAG globalnie szkodził (raport 10), więc to argument za RAG tylko dla „podaj”, ale bez danych na T1.
- **T1 i T3 rozwiązują, T2 nie (rozumowanie):** 2024/18, 2025/2, 2025/15.2, 2025/16.2, 2026/3.1, 2026/22, 2026/20. PLLuM bez myślenia podaje dobre rozstrzygnięcie ze złym argumentem (2026/20: „w 1939 r. Niemcy zaatakowały Polskę”) albo złe rozstrzygnięcie. To ograniczenie modelu bez myślenia, harness tego nie naprawi.
- **T1 i T2 rozwiązują, T3 nie (10 zadań, głównie fakty):** 2024/22.1, 2025/9.2, 2025/11.1, 2026/7, 2026/23.2, 2026/6.1, 2026/19.2, 2024/14.2, 2024/11.2. Do tego T3 fallback bez myślenia: 2026/8, 2026/6.2.
- **T3 lepszy od T1:** 2024/1 (relief B: T3 2/2, T1 1/3), 2024/19.1, 2026/24. To pojedyncze przypadki, bez wzoru.

## Warianty bliskie najlepszym — werdykty

Δ = wariant − odniesienie na tych samych zadaniach (scalone przebiegi mają Δ = 0 poza zadaniami docelowymi). Bootstrap po zadaniach nie uwzględnia szumu seedów, więc zaniża niepewność.

| Wariant | Δ 2024+2025 | bez eseju | 2026 | Gdzie zysk | Werdykt |
|---|---|---|---|---|---|
| T1 `--rozstrz-hint` (3 seedy) | +0.67 pkt (+0.6 pp), CI [−1.7, +3.3] | **+1.0** | +0.67 | rozstrz z obrazem: +2.2 pkt; zyski dokładnie na identyfikacji źródła (2026/19.1 +1.0, 2024/5.1 +0.67, 2024/1 +0.67, 2026/17 +0.67); straty rozproszone po 0.33 (szum sędziego na kopiowanych odpowiedziach) | **mały, ale systematyczny** (mechanizm + 2 z 3 arkuszy na plus); poniżej progu reguły A |
| T1 `--image-min-tokens 1120` (2 seedy) | +3.83 pkt (+3.2 pp), CI [−4.0, +12.5] | **−0.67** | −2.0 (esej −3) | +4.5 pkt z eseju; 18 zadań lepszych / 19 gorszych; tylko 2024/25 (rysunek) wyraźnie + | **szum** (cały zysk z eseju, na którego tokeny obrazu nie działają) — odrzucenie słuszne |
| T1 `--essay-refine-kb` v1 (seedy sparowane) | +2.5 pkt (+1.25/esej, 4 pary) | 0 | −1.0 | tylko esej | realny, ale mały i niestabilny (raport 10: +0.77/esej na 13 parach); 2026 na minus |
| T1 `--essay-refine-kb` v3 (seedy sparowane) | +5.0 pkt (+2.5/esej, 4 pary) | 0 | −2.0 | tylko esej | j.w.; v3 szkodziła esejom T2, więc bez niej |
| T2 tylko OCR vs finał | **−6.5 pkt (−5.5 pp)**, CI [−12, −2] | −6.5 | −2.5 | — | finał słuszny; to caption niesie zysk |
| T2 tylko caption vs finał | +0.5 pkt, CI [−5, +5.5] | +0.5 | **−3.5** | 2024 +2.5, 2025 −2.0 | remis; OCR + caption stabilniejsze (plus na wszystkich 3 arkuszach wobec wersji bez pomocy) |
| T2 bez pomocy obrazowej vs finał | **−10 pkt (−8.4 pp)**, CI [−16, −5] | −10 | −1.5 | 18 zadań z obrazem gorszych, 3 lepsze | **potwierdza finał** |
| T2 HyDE / k2 / k3 / OCR (vs 3 przebiegi finału z 01:00) | −1.3 / +1.7 / +4.7 / −3.3 pkt | **+1.67 we wszystkich czterech** | — | różnice wyłącznie z eseju (±3–5 pkt) | **szum** (identyczne +1.67 bez eseju = ten sam artefakt batchowania) |
| T3 poprzedni UD-IQ3_XXS vs finał MIX | +1.67 pkt (+1.4 pp), CI [−7, +10] | +0.17 | −1.5 | 32 zadania lepsze / 31 gorsze | **remis**; MIX jest o 0.2 GB mniejszy, więc zostaje |
| T3 E4K vs finał MIX | −1.0 pkt | −0.5 | +3.0 | 22 / 21 zadań | remis (1 seed) |
| (kontrola) T3 RAG PolQA / RAG bazy wiedzy, starsze konfiguracje | −7.0 / −3.0 pkt | −2 / −1 | — | „podaj” −1 / +1 | RAG nie pomaga T3 nawet na faktach |

## Przykłady

| Zadanie | Track | Klucz | Odpowiedź | Werdykt sędziego | Błąd |
|---|---|---|---|---|---|
| 2026/12.2 | T1 s42 | Nie: Wiedeń vs plan Chocimia | „Nie … Źródło 2. przedstawia plan oblężenia Kamieńca Podolskiego (1675)” | 0: „rozstrzygnięcie poprawne … źródło 2. błędnie zidentyfikowano” | obraz |
| 2025/22 | T1 s43 | Nie: Anders vs 1. DP Kościuszki | „Nie … Armii Polskiej w ZSRR, później znanej jako Armia Berlinga … kościuszkowców … Wojsk Polskich na Zachodzie” | 0: „rozstrzygnięcie poprawne, ale uzasadnienie błędnie utożsamia…” | wiedza (w uzasadnieniu) |
| 2024/7 | T1, 3/3 seedy | A (Henryk V, 1109) | „Fragment A … Henryk V czeski a Bolesław Wstydliwy, XIII w.” | 0: „błędnie datuje wydarzenia obu fragmentów” | wiedza (chronologia) |
| 2025/9.3 | T1, 3/3 | noc św. Bartłomieja | „Wojny religijne we Francji.” | 0: „zbyt ogólna” (T2 z RAG: 1) | wiedza |
| 2026/18.2 | T1, 2/2 | Nie: Wersal vs Poczdam | „Tak … napis »80. rocznica podpisania traktatu wersalskiego« … źródło 2. opisuje przekazanie…” | 0: „źródło 2. przedstawia postanowienia konferencji poczdamskiej” | tekst źródła |
| 2026/23.2 | T3 | Wyszyński | „Kardiniał Karol Wojtyła” | 0 | wiedza |
| 2025/4 | T3 s43 / s42 | franciszkanie, benedyktyni, jezuici | s43: „A: 1 / B: 2 / C: 3”; s42: „Franciszkanie / Benedyktynowie / Jezuita” | auto: 0 i 0 | s43 polecenie/format; s42 **grader za surowy** (egzaminator dałby 2) |
| 2026/13 | T2, oba | 1 → C, 2 → A | „Znaczek A … napis »1776«” / „A … »GETTYSBURG« … wojna o niepodległość” | 0: „oba wskazania błędne” | obraz (OCR/caption czyta napis, model źle łączy) |
| 2026/20 | T2 a | lata 30. + 2 argumenty | „lata 30. … w 1939 r. Niemcy zaatakowały Polskę” | 0 (przebieg b: 1/2) | rozumowanie |
| 2024/19.2 | T1 | Żeligowski | s42 „Józef Żeligowski” (1, łagodnie), s43 „Tadeusz Kościuszko”, s44 „Józef Piłsudski” | 1 / 0 / 0 | obraz + wiedza (Litwa Środkowa na znaczku) |

## Co jeszcze można zrobić przed 11:00 bez treningu (priorytet)

Punkty w grze na ~3 arkusze (jak 2024–2026); „oczekiwany zysk” to wartość zmierzona, nie optymistyczna. Nie edytowałem `final_configs.json` ani harnessu.

| # | Działanie | Track | W grze (3 arkusze) | Oczekiwany zysk | Ryzyko / koszt | Rekomendacja |
|---|---|---|---|---|---|---|
| 1 | **Włączyć `--rozstrz-hint`** (flaga już jest, testowana na H100 w `fx-t1rh`) | T1 | rozstrzygnij: T1 traci ~6 pkt/arkusz na 2024 i ~5.5 na 2026 | **+1.5 pkt / 3 arkusze** (+0.5/arkusz; zmierzone na 3 seedach, zyski dokładnie na identyfikacji źródła, 2 z 3 arkuszy na plus) | zmienia tylko prompt „rozstrzygnij”, 0 dodatkowego czasu; formalnie poniżej reguły A (+0.8 pp < 2 pp) | **tak, jeśli koordynator akceptuje zmianę w szumie** — to jedyny wariant T1 z mechanistycznie spójnym zyskiem |
| 2 | Awaryjnie: jeśli serwer caption padnie na egzaminie, **zostawić `--ocr`** zamiast wracać do wersji bez pomocy | T2 | ~25 pkt zadań z obrazem na arkusz | OCR-only vs bez pomocy: +3 pkt na 2024+2025 (−1 na 2026) | żadne (tylko instrukcja w RUNBOOK) | **tak** — dopisać do RUNBOOK |
| 3 | Powtórka bez podpowiedzi przy **dopasowaniu odpowiedzianym cyframi** („A: 1 / B: 2”, gdy wzór chce nazw): jedna powtórka z prefillem „A:”, przyjęta tylko, gdy nazwy nie są cyframi | T3 (T2 historycznie) | ~2 pkt / 3 arkusze (2025/4 s43; T2 wcześniej 2024/11.1, 2025/5.1) | ~+0.5 pkt / 3 arkusze (nazwy bywają potem złe — raport 14) | typ A (dotyka tylko takich odpowiedzi); wymaga zmiany harnessu i testu na sucho ~15 min | opcjonalnie, niski priorytet |
| 4 | T3: przy fallbacku (myślenie urwane) powtórka **z myśleniem i innym seedem** zamiast odpowiedzi bez myślenia | T3 | harness 5 pkt / 3 arkusze (2026/8, 2026/6.2, 2025/21.2…) | ~+1–2 pkt / 3 arkusze (odpowiedzi po fallbacku są wyraźnie gorsze; w T1: 36% vs 71%, raport 12) | +1–2 min na arkusz; zmiana harnessu i test na GPU | opcjonalnie, jeśli jest ktoś z wolnym GPU przed 09:30 |
| 5 | T1 `--essay-refine-kb` z bazą **v1** (nie v3) | T1 | esej: T1 traci 6–8/15 pkt, w tym ~5 za „aspekty” | +0.7 pkt/esej (13 par, raport 10) ≈ **+2 pkt / 3 arkusze**, ale 2026 na minus w obu wersjach | reguła C niespełniona (< +1/esej); +1 wywołanie eseju (~1–2 min) | raczej nie; tylko jeśli koordynator chce grać na esej |
| — | Notatki bazy wiedzy „pod słabe epoki” | T2 | — | brak: słabe miejsca T2 (1914–39) to obraz i rozumowanie, nie wiedza; baza v2/v3 szkodziła esejom T2 | — | **nie** |
| — | RAG dla T3 (nawet tylko „podaj”) | T3 | fakty 25 pkt / 3 arkusze | zmierzone: PolQA −5.9 pp, baza wiedzy −2.5 pp; „podaj” −1 / +1 | — | **nie** |
| — | Tokeny obrazu 1120 dla T1 | T1 | — | bez eseju −0.67 pkt, 2026 −2 | — | **nie** (potwierdzone) |

Łącznie: realistycznie **+1.5–3 pkt na 3 arkusze dla T1** (#1, opcjonalnie #5) i ~+1–2 pkt dla T3 (#3, #4, wymagają zmian harnessu i testu). T2 zostaje bez zmian, z instrukcją awaryjną #2. Nierozwiązywalne obecnymi modelami: ~3 pkt/arkusz z tabeli zadań trudnych i większość strat eseju T3.

## Ograniczenia

- Rodzaj błędu per przebieg z heurystyk. Ręczne kategorie z raportu 12 mają pierwszeństwo dla T1 i dla zadań T2 bez obrazu (odpowiedzi T2 z obrazem zmieniły się po OCR/caption). Kategorie „rozumowanie” i „tekst” T2/T3 są przybliżone (±2–3 pkt na track).
- Epoka eseju = epoka wybranego tematu (pole `topic` sędziego).
- Warianty z 1 seedem (T2 HyDE/k2/k3/OCR, T3 E4K) i porównania na 2026 z 1–2 seedami są wskazówką, nie dowodem (szum ~2–3 pp, raport 11).

## Do dopisania o 08:30

Nowe eksperymenty (obraz dla T1: `img-t1tiles-*`, recenzent faktów `*__fcB`, głosowanie zamkniętych `gemma4-qat__vote5*`, mniejszy T3 `q35-2b-*__t3s-*`, `q35-4b-vt-mix-*`) są na maszynach, niezsynchronizowane i częściowo nieocenione. Po ściągnięciu i ocenie wystarczy dopisać grupy do `eval/audit_groups.json` (albo `--add`) i uruchomić `python eval/audit.py --out raports/20-audyt-tabele.md`. Nowa grupa z `"vs": "T1-final"` dostaje automatycznie sekcję G (Δ wg typu, epoki i obrazu, bootstrap).

## Rekomendacje 3 i 4 — wykonane (08:15, raport 21)

Obie włączone w T3 tuned: `--think-retry` (powtórka z myśleniem, seed +7, przed fallbackiem bez myślenia) i `--match-retry` (dopasowania z cyframi: najpierw bez redukcji do numeru, potem jedna powtórka bez wskazówki z raportu 14). Na 9 zadaniach z fallbackiem odpowiedzi z myśleniem mają 0.56 pkt/odp., a bez myślenia 0.38, czyli ~+0.2 pkt/arkusz; powtórka udała się w 5 z 7 wyzwoleń. Dopasowanie: w grze tylko 2025/4 (~+0.3 pkt/arkusz). Czas: +2–4 min na arkusz. Sędzia $0.10. Szczegóły: `raports/21-t3-ponowienia.md`.
