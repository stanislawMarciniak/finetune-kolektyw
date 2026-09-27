# 20 — Audyt odpowiedzi finałów (v2: finały zamrożone, nd 27.09 ~09:40; v1 z 06:00–07:00)

Sędzia `gpt-6-luna`, tylko istniejące oceny (koszt sędziego **$0**, bez GPU, bez zmian w `final_configs.json` i `harness/`). Zbiór główny = 2024 + 2025 (119 pkt, 2024/21 poza mianownikiem), potwierdzenie = 2026 (60 pkt). Strata = max − średnia z seedów. „Przed” = stan z audytu v1 (07:00).

- **Skrypt:** `eval/audit.py`, grupy w `eval/audit_groups.json`, pełne tabele w `raports/20-audyt-tabele.md` (sekcja H: przed vs finał wg typu, epoki i błędu; sekcja I: statystyki esejów).
- **Nowe w skrypcie:**
  - Przebiegi scalone (`--only-ids` + `--merge-from`) biorą oceny zadań spoza `only_ids` z przebiegu źródłowego. Porównanie idzie więc tylko po zmienionych zadaniach, a oceny skopiowane przez `judge_reuse` nie wchodzą do wyniku.
  - Filtry `przebieg|essay` i `przebieg|noessay` pozwalają złożyć finał T1 z przebiegów `fx-t1rh` (zadania krótkie) i `ek22F` (esej).
  - Pole `before` w grupie włącza sekcję H.
- Przez tę zmianę liczby T1 różnią się nieco od raportów 12 i 22 (np. 2026 `fx-t1base-s43`). W v1 zadania spoza zakresu scalenia miały oceny skopiowane, teraz mają oceny ze źródła.

## Zmiana zdolności modeli (TL;DR)

| Track | Przed (07:00) → finał | 24+25 | 2026 | Strata 24+25 / 2026 (pkt) | Co się zmieniło |
|---|---|---|---|---|---|
| **T1** | t1final → + `--rozstrz-hint` + esej `rubric --essay-rubric-fixed` | 70.6 → **71.5%** | 80.5 → **84.1%** | 34.9 → 33.9 / 11.7 → 9.5 | lepsza identyfikacja źródeł w „rozstrzygnij”, esej bogatszy, ale z większą liczbą błędów |
| **T2** | bez zmian od 07:00 (względem stanu z 01:00: + `--fill-fields --ocr` + caption) | 52.4 → **56.7%** | 47.8 → **52.5%** | 56.7 → 51.5 / 31.3 → 28.5 | zyski tylko na zadaniach z obrazem i na polach „Etykieta:” |
| **T3** | IQ2_M-PL-E4K-MIX 1.75 GB → **…-S4K-V124K 1.53 GB** | 42.9 → **41.2%** | 45.8 → **42.8%** | 68.0 → 70.0 / 32.5 → 34.3 | −0.22 GB kosztem ~2 pkt, czyli w szumie seedów (V124K: 45.4 / 36.1 / 42.1% na 24+25) |

1. **T1 zyskał realnie ~1 pkt na 24+25 i ~2 pkt na 2026, w dwóch miejscach.**
   - „Rozstrzygnij”: strata 6.0 → 5.0 pkt (24+25) i 5.5 → 4.3 pkt (2026). Poprawiły się dokładnie zadania z identyfikacją źródła: 2026/19.1 (0 → 1), 2024/5.1 i 2024/1 (+0.67), 2026/17 (+0.67). Błąd „źle odczytany obraz” spadł z 10.0 do 8.3 pkt, a „tekst źródła” na 2026 z 3.0 do 1.3 pkt.
   - Esej, na tych samych 15 parach (5 seedów × 3 arkusze): 8.07 → 8.40 pkt/esej (+0.33).
     - Kryterium A przed odjęciem rośnie o +1.07 pkt. Elementy „bogata” rosną z 4 do 12 na 45, a strata „aspekty” spada z 12.2 do 10.6 pkt (24+25) i z 4.6 do 3.0 pkt (2026).
     - Liczba błędów rośnie z 2.27 do 3.87 na esej, a odjęcie z 1.27 do 2.07 pkt. Strata „esej A: błędy” rośnie z 3.2 do 5.0 pkt (24+25). Dłuższe eseje (~459 zamiast 359 słów) przynoszą więcej faktów, a więc i więcej pomyłek. Odjęcie zjada ~3/4 zysku z A.
     - Po arkuszach: 2024 +0.8, 2025 −0.8, 2026 +1.0 pkt/esej. Na 24+25 wychodzi zero, cały zysk jest na 2026.
2. **T2: bez zmian od audytu v1.** Całą poprawę dnia dały pomoce obrazowe i `--fill-fields`.
   - Strata na zadaniach z obrazem: 34.0 → 26.5 pkt (24+25) i 19.0 → 18.5 pkt (2026). Względem samego `--fill-fields` to +10 pkt na 24+25, CI [+5, +16].
   - Strata na zadaniach bez obrazu stoi w miejscu (8.7 → 8.0).
   - Kurczą się: „podaj” (8.3 → 3.5), wiedza (10.3 → 7.5), „odpowiedź niepełna” (3.0 → 1.0).
   - Nie kurczy się „rozstrzygnij” (19.0 → 18.0 / 9.0 → 9.5). Rośnie „rozumowanie” na 2026 (2.7 → 5.5): caption daje opis, ale PLLuM bez myślenia źle łączy go z tezą.
3. **T3: model mniejszy, ale nie słabszy w granicach szumu. Sam słownik jednak niesie zdolność do zamkniętych.**
   - Zamknięte: MIX 55.0% (22/40), V124K 53.3% (32/60), T40K **32.5%** (13/40, raport 18 §6).
   - Przycięcie słownika do 40k tokenów niszczy dopasowania i P/F (−2.5 i −1.5 pkt), mimo że T40K miał już `--think-retry --match-retry`. Przy 124k tokenów tego efektu nie ma.
   - W V124K rośnie strata „wiedza/fakt” (17.0 → 21.3 pkt na 24+25), a spada „tekst źródła” (6.0 → 3.7) i „polecenie/format” (2.0 → 0.3).
   - Esej nadal ~1/15 pkt (0.5 → 1.2).
   - Przebiegi V124K są bez flag retry. Te flagi dają w pomiarze na MIX +0.5 pkt na 24+25 i 0 na 2026 (sparowane, zmienione zadania), zgodnie z raportem 21 (~+0.2 pkt/arkusz).
4. **Największa strata nie do odzyskania obecnymi modelami:**
   - esej: T1 15.6 pkt na 24+25 (połowa za „aspekty”), T2 17.0, T3 27.3 z 30;
   - identyfikacja obrazu i źródła w „rozstrzygnij”: 9 zadań trudnych dla wszystkich finałów, ~3 pkt na arkusz, 7 z 9 to „rozstrzygnij”.

## T1 — przed vs finał (strata w pkt; 24+25 / 2026)

Finał T1:
- zadania krótkie: `fx-t1rh-s42/43/44` (scalone na t1final, porównanie tylko po zadaniach docelowych);
- esej: `ek22F-s42…s46`, pary z esejami bazowymi tych samych seedów (t1final / nt1final-s44 / `ek22B-*`).

| Wymiar | Przed | Finał | Δ |
|---|---|---|---|
| rozstrzygnij | 6.0 / 5.5 | 5.0 / 4.3 | **−1.0 / −1.2** |
| esej | 15.6 / 5.2 | 15.6 / 4.2 | 0 / **−1.0** |
| podaj, wyjaśnij, zamknięte | 13.3 / 1.0 | 13.3 / 1.0 | 0 (poza zakresem zmian) |
| — źle odczytany obraz | 10.0 / 2.5 | 8.3 / 2.7 | **−1.7** / +0.2 |
| — tekst źródła | 0.7 / 3.0 | 0.7 / 1.3 | 0 / **−1.7** |
| — esej A: aspekty | 12.2 / 4.6 | 10.6 / 3.0 | **−1.6 / −1.6** |
| — esej A: błędy merytoryczne | 3.2 / 0.6 | 5.0 / 1.2 | **+1.8 / +0.6** |
| — harness (fallback) | 1.3 / 0 | 2.3 / 0.3 | +1.0 / +0.3 (rozproszone po 0.33, szum) |
| **razem** | 34.9 / 11.7 | 33.9 / 9.5 | **−1.0 / −2.2** |

Epoki: po zmianach żadna epoka nie traci więcej niż 4.3 pkt. Starożytność spadła do 0.3 pkt (2024/1 i 2024/2 z `--rozstrz-hint`), reszta ±0.7.

Nadal nie do zdobycia:
- mapy: 2024/14.1, 2025/14.1, 2026/12.2;
- znaczki: 2026/14.2 i 2026/18.2 (źródło tekstowe przypisane złemu traktatowi);
- chronologia: 2024/7, 2025/22.

## T2 — przed vs finał (strata w pkt; 24+25 / 2026)

„Przed” to finał z 01:00 (3 przebiegi bez `--fill-fields`). Od audytu v1 T2 się nie zmienił.

| Wymiar | Przed (01:00) | Sam `--fill-fields` | Finał | Δ finał − 01:00 |
|---|---|---|---|---|
| zadania z obrazem | 34.0 / 19.0 | 36.5 / 20.0 | 26.5 / 18.5 | **−7.5** / −0.5 |
| zadania bez obrazu (bez eseju) | 8.7 / 4.0 | 8.0 / 4.0 | 8.0 / 4.0 | −0.7 / 0 |
| podaj | 8.3 / 4.0 | | 3.5 / 2.5 | **−4.8 / −1.5** |
| rozstrzygnij | 19.0 / 9.0 | | 18.0 / 9.5 | −1.0 / +0.5 |
| wyjaśnij | 8.3 / 3.0 | | 6.0 / 3.5 | −2.3 / +0.5 |
| esej (2 vs 3 próbki; pomoce go nie dotyczą) | 14.0 / 8.3 | | 17.0 / 6.0 | szum ±3 |
| — wiedza/fakt | 10.3 / 6.0 | | 7.5 / 4.0 | **−2.8 / −2.0** |
| — odpowiedź niepełna | 3.0 / 1.0 | | 1.0 / 1.0 | **−2.0** / 0 |
| — źle odczytany obraz | 15.3 / 8.7 | | 15.0 / 7.5 | −0.3 / −1.2 |
| — rozumowanie | 7.7 / 2.7 | | 6.0 / 5.5 | −1.7 / **+2.8** |
| **razem** | 56.7 / 31.3 | | 51.5 / 28.5 | **−5.2 / −2.8** |

Zadania, które caption i OCR „naprawiły” (0 → 1): 2024/4, 2025/12, 2025/16.1, 2025/3.1, 2025/23, 2026/1, 2026/7. W heurystyce część z nich była oznaczona jako „wiedza”, bo przed pomocą model zgadywał fakt zamiast odczytać obraz.

Nie do zdobycia bez modelu z myśleniem: „rozstrzygnij” (18 pkt na 24+25, prawie połowa strat poza esejem) i rozumowanie na 2026. Tutaj pomoc obrazowa jest już wykorzystana.

## T3 — przed vs finał (strata w pkt; 24+25 / 2026)

| Wymiar | MIX 1.75 GB (2 seedy) | V124K 1.53 GB (3 seedy) | Δ |
|---|---|---|---|
| zamknięte (P/F + dopasowanie + wybór) | 9.0 / 3.5 | 9.3 / 3.7 | +0.3 / +0.2 (P/F +2.0, dopasowanie −1.5) |
| podaj | 12.5 / 4.0 | 14.0 / 4.7 | +1.5 / +0.7 |
| rozstrzygnij | 12.5 / 9.5 | 14.0 / 10.0 | +1.5 / +0.5 |
| esej | 28.5 / 15.0 | 27.3 / 14.0 | −1.2 / −1.0 |
| — wiedza/fakt | 17.0 / 7.5 | 21.3 / 7.7 | **+4.3** / +0.2 |
| — tekst źródła | 6.0 / 2.5 | 3.7 / 3.3 | **−2.3** / +0.8 |
| — polecenie/format | 2.0 / 0 | 0.3 / 0 | −1.7 |
| — rozumowanie | 4.0 / 2.0 | 6.0 / 3.3 | +2.0 / +1.3 |
| — harness (fallback) | 3.0 / 1.5 | 3.0 / 2.7 | 0 / +1.2 (przebiegi bez `--think-retry`) |
| **razem** | 68.0 / 32.5 | 70.0 / 34.3 | **+2.0 / +1.8** (≈ 1.7 / 3 pp, w szumie) |

- Esej T3, statystyki z sekcji I tabel:
  - średnio 1.2 / 15 pkt;
  - 6.9 błędu na esej;
  - elementy: 0 „bogata”, 22 „powierzchowna”, 5 „brak”.
- V124K wybiera w eseju temat 3 (1914–39, 1945–89, II wojna), a MIX temat średniowieczny. Strata ta sama.
- Nie do zdobycia tym rozmiarem:
  - esej (~14 z 15 pkt na arkusz);
  - fakty w „podaj” (14 pkt na 24+25).

  Raport 16 potwierdza, że żaden model < 0.97 GB nie zbliża się do 35%.

## Eksperymenty odrzucone (klasa błędu, w którą celowały → dlaczego nie pomogły)

| Eksperyment | Celował w | Wynik | Dlaczego nie |
|---|---|---|---|
| Kafelki obrazu T1 `--image-tiles` (raport 15) | źle odczytany obraz | +1.0 pkt na 24+25 (bez eseju), −1.5 na 2026; 11 zadań lepszych / 13 gorszych | większa rozdzielczość nie naprawia interpretacji (mapa 1809 dalej „1812”); zysk w „rozstrzygnij” zjadają błędy w podaj / P/F |
| Recenzent faktów (raport 17) | esej A: błędy, wiedza w otwartych | T1 esej +0.27 pkt/esej, T1 otwarte −1, T3 −1 | błędy to tylko 3.2 pkt z 15.6 straty eseju T1. Progi CKE (1–2 błędy = −1) zjadają poprawki, a recenzent zamienia też dobre zdania na złe |
| Głosowanie zamkniętych (raport 19) | wiedza w zamkniętych | +1.0 pp ściśle / +0.75 łagodnie, czas ~3× | zamknięte to u T1 tylko 5 pkt straty na 24+25; zysk w szumie, a koszt czasu realny |
| Retrieval obrazów (raport 23) | źle odczytany obraz | 3/61 trafień dokładnych, ~7 mylących, 0 pomocnych na zadaniach trudnych | źródła CKE (znaczki, plany bitew) nie występują w bazie, a podobne obrazy podsuwają zły kontekst |
| Esej `--essay-refine-kb` (v1 / v3; na rubric: FK) | esej A: aspekty | stary esej: +1.25 / +2.5 pkt/esej na 24+25, ale −1 / −2 na 2026; na rubric FK +0.6 pkt/esej ponad F (15 par, CI [0, +3.6] pkt) | niestabilne między arkuszami, 2026 na minus w starym trybie. Dodatkowe wywołanie eseju; niespełniona reguła C (≥ +1/esej) |
| Weryfikator T3 (recenzent faktów na T3, raport 17) | wiedza/fakt T3 | eseje: 0 zgłoszeń; otwarte: 36 podmian, ~4 dobre / ~17 złe, −1 pkt | model 4B w 2 bitach nie odróżnia swoich dobrych faktów od złych, więc weryfikacja tylko dokłada szum |
| `--match-names-hint` (raport 14) | polecenie/format w dopasowaniu (cyfry zamiast nazw) | ujemny we wszystkich trackach | podpowiedź zmienia dobre nazwy na złe. W T3 zastąpiona przez `--match-retry` (powtórka tylko przy cyfrach) |
| T3 słownik 40k (raport 18 §6) | rozmiar T3 | zamknięte 32.5% vs 53%; −5.5 pkt na 24+25 mimo retry | przycięcie słownika usuwa tokeny potrzebne w dopasowaniach i P/F |
| T1 `--image-min-tokens 1120` | źle odczytany obraz | bez eseju −0.67 pkt, 2026 −2 | cały „zysk” z eseju, na który tokeny obrazu nie działają |

## Zadania trudne dla wszystkich finałów (każdy ≤ 34% punktów)

W porównaniu z v1: 2024/5.1 i 2026/19.1 wypadły (rozwiązuje je T1 z `--rozstrz-hint`), a doszło 2026/14.2.

| Zadanie | Typ, epoka, obraz | T1 / T2 / T3 (śr. pkt) | Dlaczego |
|---|---|---|---|
| 2024/14.1 | rozstrz, XIX, mapa | 0 / 0 / 0 | mapa wojny 1809 czytana jako 1812 albo wojna polsko-bolszewicka |
| 2025/14.1 | rozstrz, XIX, mapa + herby | 0 / 0 / 0 | który herb pochodzi z powstania styczniowego — odczyt obrazu |
| 2026/12.2 | rozstrz, nowożytność, plan bitwy | 0 / 0 / 0 | plan Chocimia rozpoznany jako „Kamieniec 1675” |
| 2026/14.2 | rozstrz, XIX, artefakt | 0.33 / 0 / 0 | identyfikacja przedmiotu |
| 2026/18.2 | rozstrz, 1914–39, znaczek | 0 / 0 / 0.33 | znaczek (Wersal) rozpoznany dobrze, ale tekst z Poczdamu przypisany Wersalowi |
| 2024/7 | rozstrz, średniowiecze, tekst | 0 / 0 / 0 | chronologia: Krzywousty 1109 vs XIII w. |
| 2025/22 | rozstrz, II wojna, tekst | 0.33 / 0 / 0 | Armia Andersa mylona z „Armią Berlinga” |
| 2024/11.1 | dopasowanie, nowożytność | 0.33 / 0 / 0 | Karol IX / Henryk IV |
| 2024/19.2 | podaj, 1914–39, znaczek | 0.33 / 0 / 0 | Litwa Środkowa → Żeligowski |

Rozbieżności między finałami (różnica ≥ 67 pp): 38 zadań, w v1 było 46. Wzorce bez zmian:
- T1 rozwiązuje „rozstrzygnij”, którego nie rozwiązują T2 i T3;
- T2 z RAG trafia pojedyncze fakty „podaj”;
- T3 traci fakty, które T1 i T2 znają.

Pełna lista: tabele, sekcja F.

## Przykłady (bez zmian od v1, poza 2026/19.1)

| Zadanie | Track | Klucz | Odpowiedź | Werdykt | Błąd |
|---|---|---|---|---|---|
| 2026/12.2 | T1 | Nie: Wiedeń vs plan Chocimia | „Źródło 2. przedstawia plan oblężenia Kamieńca Podolskiego (1675)” | 0: „źródło 2. błędnie zidentyfikowano” | obraz |
| 2026/19.1 | T1 | datowanie źródła 2 (maj 1926) | v1: złe datowanie; finał z `--rozstrz-hint`: 3/3 seedy poprawnie | 0 → 1 | tekst źródła (naprawione) |
| 2025/22 | T1 | Anders vs 1. DP Kościuszki | „…Armii Polskiej w ZSRR, później znanej jako Armia Berlinga…” | 0 | wiedza |
| 2024/7 | T1 | A (Henryk V, 1109) | „…Bolesław Wstydliwy, XIII w.” | 0 | wiedza (chronologia) |
| 2026/18.2 | T1 | Nie: Wersal vs Poczdam | „Tak … źródło 2. opisuje przekazanie…” | 0 | tekst źródła |
| 2026/23.2 | T3 | Wyszyński | „Kardiniał Karol Wojtyła” | 0 | wiedza |
| 2025/4 | T3 s42 | franciszkanie, benedyktyni, jezuici | „Franciszkanie / Benedyktynowie / Jezuita” | auto 0 (egzaminator dałby 2) | grader za surowy |
| 2026/13 | T2 | 1 → C, 2 → A | „Znaczek A … napis »1776«” | 0 | obraz (caption czyta napis, model źle łączy) |
| 2026/20 | T2 | lata 30. + 2 argumenty | „…w 1939 r. Niemcy zaatakowały Polskę” | 0 | rozumowanie |

## Ograniczenia

- **Rodzaj błędu:** przypisany z heurystyk (ręczne kategorie z raportu 12 mają pierwszeństwo dla T1 i dla zadań T2 bez obrazu). Kategorie „rozumowanie” i „tekst” dla T2 i T3 mają niepewność ±2–3 pkt na track.
- **Esej:**
  - T1 w finale ma 5 seedów, a „przed” to te same seedy, więc pary są czyste. T2 i T3 mają 2–3 próbki, a esej zmienia się między nimi o ±3 pkt.
  - Epoka eseju = temat wybrany przez model.
- **T3 finał:** przebiegi są bez `--think-retry --match-retry`. Efekt flag zmierzono osobno na MIX (+0.5 pkt na 24+25).
- **Szum:** seedy ~2–3 pp (raport 11). Jedynymi zmianami wyraźnie ponad szumem są pomoc obrazowa T2 i spadek zamkniętych przy T40K.
