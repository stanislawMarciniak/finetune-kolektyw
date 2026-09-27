# 10c — Walidacja T1: szum, kontaminacja, sędzia (nd 27.09, 04:05–05:15)

Pytanie: czy wynik T1 (Gemma-4-12B-it QAT q4_0 + mmproj, myślenie, temp. 1.0, bez RAG; 72.3 / 69.7% na 2024+2025, 83.3% na 2026) jest zawyżony i czy ~2 pp wystarcza do zmiany konfiguracji (np. `--image-min-tokens 1120`). Sędzia `gpt-6-luna` jak w raportach 09–10, 2024/21 poza mianownikiem (119 pkt na 2024+2025).

## TL;DR

1. **Wynik nie jest zawyżony w wykrywalny sposób.** Nie ma śladu kontaminacji:
   - arkusz 2024 sprzed granicy wiedzy nie wypada lepiej niż 2025/2026 po niej;
   - sonda pamięci nie odtwarza tekstów CKE;
   - odpowiedzi po permutacji nie powtarzają starego klucza;
   - na 70 zadaniach E5, których nigdy nie było w sieci, T1 ma 78.6%, tyle samo co na CKE bez esejów.

   Sędzia luna daje dokładnie tyle samo co `gpt-6-sol` (73.5% vs 73.5% na 298 pkt). Grader zamkniętych jest raczej **za surowy** niż łagodny.
2. **2 pp to szum.** Szum jednego przebiegu na 2024+2025 wynosi ~2.8 pp (SD), a na jednym arkuszu ~4 pp. Do rozstrzygnięcia 2 pp trzeba by ~16 seedów na wariant, a i to nie usuwa niepewności z doboru zadań (±5–6 pp).
3. **`--image-min-tokens 1120`: nie wdrażać.** Cały zysk (+3.2 pp na 2024+2025) pochodzi z esejów, które nie mają obrazów, więc tokeny obrazu nie mogą go powodować. Na zadaniach z obrazami jest tylko +0.9 pp (~0.5 pkt), na 2026 −3.3 pp (80.0 / 80.0 vs 83.3), a łącznie na trzech arkuszach −0.3 pp.
4. **Realistyczna prognoza T1 na nowym arkuszu (jeden seed, ~60 pkt):** ~**74%** (~44 pkt). Przedział 80%: 64–84%, przedział 95%: 60–88%. Wariancję dominuje trudność arkusza (SD ~5 pp) i szum seeda (~4 pp), a nie konfiguracja.
5. **Koszt API: 1.35 $** (sol 1.29 $ + luna 0.06 $ za E5) z limitu 2 $.

## 1. Statystyka: szum i porównania wariantów

Przebiegi T1 na 2024+2025 (sędzia luna; stary grader zamkniętych):

| Wariant | seedy | wyniki | średnia | bez esejów |
|---|---|---|---|---|
| **finał** `t1final` | 3 | 72.3 / 69.7 / 68.9 (s44, nowy) | **70.3** | 78.3 |
| `--image-min-tokens 1120` | 2 (s44 bez wyniku) | 74.8 / 72.3 | 73.5 | 77.5 |
| legacy prompt | 2 | 73.1 / 71.4 | 72.3 | 77.5 |
| t1kb | 2 | 69.7 / 68.1 | 68.9 | 75.8 |
| temp. 0.6 | 1 | 71.4 | 71.4 | 71.9 |
| polqa RAG | 1 | 68.1 | 68.1 | 77.5 |
| img 560 | 1 | 66.4 | 66.4 | 74.2 |

- **Szum jednego przebiegu (119 pkt):** SD z sum wariancji zadań między seedami tej samej konfiguracji = **2.8 pp** (z wyników całkowitych 1.6 pp, ale przy df = 5 to słaby estymator). Na jednym arkuszu (60 pkt) szum wynosi **~4 pp**: finał na 2025 dał 71.7 / 73.3 / 63.3%, na 2024 72.9 / 66.1 / 74.6%.
- **Źródła wariancji:** eseje 30% (dwa zadania!), otwarte 48%, zamknięte 22%. Największe wariancje zadań: 2024/26 (esej), 2024/25 (rysunek Jaruzelskiego, 0 albo 3 pkt), 2025/25 (esej).
- **Nowy seed s44 finału (68.9%) jest niżej niż średnia dwóch pierwszych (71.0%).** Część to grader: 3 pkt na 2025 odrzucone za „Zakon Benedyktynów”, „USA” (sekcja 3c). Przy uczciwym dopasowaniu s44 ma 71.4%, a średnia finału 71.1%.

Sparowany bootstrap (zadania losowane w obrębie arkusza, esej zawsze jeden na arkusz; seedy losowane w obrębie wariantu; 5000 prób), różnica względem finału (3 seedy) na 2024+2025:

| Wariant | Δ (pp) | 95% CI | P(lepszy) | Δ bez esejów |
|---|---|---|---|---|
| 1120 | +3.2 | [−3.2, +9.2] | 0.85 | −0.8 |
| legacy | +2.0 | [−3.3, +7.3] | 0.76 | −0.8 |
| t1kb | −1.4 | [−7.2, +4.3] | 0.31 | −2.4 |
| temp. 0.6 | +1.1 | [−4.4, +6.2] | 0.65 | **−6.4** |
| img 560 | −3.9 | [−9.1, +1.1] | 0.06 | −4.1 |

- Na 2026 1120 dało **−3.3 pp** (80.0 / 80.0 vs 83.3, 1 seed finału). Na wszystkich trzech arkuszach (tylko przebiegi z kompletem) wychodzi **−0.3 pp**, CI [−5.1, +4.4].
- Wszystkie „dodatnie” warianty są dodatnie wyłącznie dzięki esejom. Bez esejów żaden nie bije finału.

### Reguła decyzyjna

- Minimalna wykrywalna różnica przy samym szumie seedów (2σ, σ ≈ 2.8 pp na 2024+2025): n = 2 seedy na wariant → 5.6 pp, n = 3 → 4.6 pp, n = 5 → 3.5 pp, n = 10 → 2.5 pp. **Do wykrycia 2 pp trzeba ~16 seedów na wariant.**
- Nawet przy nieskończonej liczbie seedów zostaje niepewność doboru zadań: ±5–6 pp na 77 zadaniach. Zmiana musi mieć mechanizm, który działa na konkretne zadania, a nie tylko wygrywać średnio.
- **Zmieniać konfigurację tylko, gdy:**
  1. Δ ≥ 3 pp przy ≥ 3 seedach na wariant (2024+2025);
  2. ten sam znak na 2026;
  3. Δ > 0 także bez esejów; zmiany eseju oceniać w parach (`--essay-from`), bo esej to 30% wariancji przy dwóch zadaniach;
  4. zysk leży na typach zadań, których zmiana dotyczy (mechanizm);
  5. brak nowego ryzyka operacyjnego.

  W innym wypadku zostajemy przy przetestowanym finale: przy równym oczekiwanym zysku wygrywa niższe ryzyko.

## 2. Źródła zawyżenia

### 2a. Kontaminacja — granica wiedzy

- Karta modelu Gemma 4: **granica danych pretreningu styczeń 2025**. Premiera rodziny 31.03/2.04.2026, wariant 12B 3.06.2026 (dane posttreningowe nieujawnione).
- Arkusz 2024 (maj 2024, klucz lipiec 2024) jest **przed** granicą, a mock 2023 tym bardziej. Arkusze 2025 i 2026 są **po** niej. Arkusz 2026 (maj 2026) teoretycznie mógłby trafić do posttreningu 12B, ale to mało prawdopodobne.
- **Test naturalny: wynik według arkusza** (średnia z 11 przebiegów T1): 2024 **69.8%**, 2025 **71.5%**. Finał: 2024 71.2%, 2025 69.4%, 2026 83.3% (1120: 80.0 / 80.0), mock 2023 78.3% (luna, 1 przebieg). Zamknięte: 2024 63.6%, 2025 77.3%, 2026 10/10. **Arkusz sprzed granicy nie wypada lepiej** — brak sygnału kontaminacji.

### 2a'. Sonda pamięci (surowe `/completion`, zachłanne, 96 tokenów)

273 teksty: źródła, polecenia i rozwiązania CKE 2023–2026 (pierwsza połowa tekstu → porównanie kontynuacji z oryginałem). Kontrole: 80 tekstów źródłowych i 80 odpowiedzi E5 (wygenerowane przez lunę, nigdy w sieci) oraz 3 teksty „na pewno znane” (Pan Tadeusz, hymn, preambuła Konstytucji 1997).

- **Surowe `/completion` bez szablonu** (jak w zadaniu): Gemma-4-it wpada w pętle powtórzeń końcówki promptu we wszystkich grupach, również w tekstach znanych. ROUGE-L 0.01–0.15, prefiks dosłowny ~0 słów. Sonda jest w tej postaci **nieczuła**, bo nie odtwarza nawet drugiego wersu Pana Tadeusza.
- **Wariant z szablonem czatu i prefillem** („Kontynuuj dosłownie…”, pierwsza połowa jako początek odpowiedzi modelu):

| Grupa | n | ROUGE-L | najdłuższy wspólny ciąg (słowa) |
|---|---|---|---|
| CKE źródła 2023 / 2024 / 2025 / 2026 | 22 / 15 / 14 / 19 | 0.14 / **0.07** / 0.08 / 0.11 | 2.1 / 1.3 / 1.4 / 1.4 |
| CKE rozwiązania 2023 / 2024 / 2025 / 2026 | 6 / 10 / 5 / 6 | 0.12 / **0.10** / 0.16 / 0.24 | 1.7 / 1.5 / 2.6 / 4.5 |
| kontrola E5 źródła / odpowiedzi | 80 / 80 | 0.10 / 0.11 | 1.6 / 1.8 |
| teksty znane | 3 | 0.10 | 1.3 |

- Teksty CKE są na poziomie kontroli, a 2024 wręcz poniżej. Dwa jedyne dłuższe dopasowania (2026/4.1: 18 słów, 2023/3: 10 słów) to **kopiowanie wcześniejszego zdania z tego samego promptu**, nie pamięć.
- Wniosek: skwantyzowana 12B słabo pamięta dosłownie polskie teksty w ogóle (nawet kanon), więc dosłowna pamięć kluczy CKE jest nieprawdopodobna. Sonda ma niską czułość, więc to argument słabszy od testów 2a i 2b.

### 2b. Test permutacji (zamknięte 2024 + 2025, 15 zadań / 20 pkt)

- Zbudowano 4 różne permutacje na arkusz (`exams/test202{4,5}_v2_perm{1..4}`, klucze `eval/data/test202{4,5}_v2_perm{k}.jsonl`, skrypt `/tmp/val/perm.py`):
  - wybór: przetasowane opcje A–D;
  - P/F: przestawione stwierdzenia;
  - dopasowanie: zamienione etykiety fragmentów A/B/C w źródle (2025/4: etykiety w tabeli).
- Przebiegi: T1 finał na własnym serwerze (port 8391), 1 seed na permutację (s42–s45). Kontrola: te same zadania bez permutacji (s45, s46) plus zamknięte z przebiegów finału s42–s44.
- Ocena: `grade.py` plus uczciwe dopasowanie odmian dla dopasowań (sekcja 3c), identyczne dla oryginału i permutacji.

| | oryginał (5 przebiegów) | permutacja (4 przebiegi) | Δ |
|---|---|---|---|
| razem (20 pkt) | 78.0% | 65.0% | **−13.0 pp**, 95% CI [−27, −2] |
| 2024 — przed granicą wiedzy | 65.0% | 53.1% | −11.9 pp |
| 2025 — po granicy wiedzy | 86.7% | 72.9% | −13.8 pp |
| wybór / dopasowanie / P-F | 83 / 73 / 78% | 63 / 67 / 66% | |

- **Spadek jest taki sam na arkuszu, którego model nie mógł widzieć (2025).** To nie pamięć, tylko wrażliwość na układ zadania (i mała próba).
- **Tylko 3 z 25 błędnych odpowiedzi po permutacji to „echo” starego klucza** (np. 2025/10 dwa razy „1: F 2: P”), czyli mniej więcej tyle, ile daje przypadek. Reszta to błędy merytoryczne:
  - 2024/14.2 cztery razy „Zajączek” (model czyta mapę 1809 jako powstanie listopadowe — ten sam błąd co w 14.1);
  - 2025/7.2 „Jan Olbracht” jako król w 1466.
- **Zastrzeżenie:** permutacja dopasowań daje nienaturalny układ (Fragment B przed A), a model czasem przypisuje po kolejności. Część spadku to trudniejszy układ, nie „prawdziwa” słabość.
- Na świeżym arkuszu w naturalnym układzie (2026) zamknięte wyszły 10/10, więc nie korygujemy wyniku w dół z tego powodu. Warto jednak wiedzieć, że zamknięte są kruche.

### 2c. Czysty zbiór E5 (70 zadań, 70 pkt: 30 zamkniętych, 40 otwartych; 46 średnich, 18 łatwych, 6 trudnych)

`exams/e5clean70`, klucze `eval/data/e5clean70.jsonl` (zamknięte automatycznie, otwarte luna), przebieg `gemma4-qat__val-e5-s42` (T1 finał, s42):

| | wynik |
|---|---|
| **razem** | **55/70 = 78.6%** |
| zamknięte (wybór / P-F / dopasowanie) | 27/30 (8/10, 10/10, 9/10) |
| otwarte | 28/40 = 70% |
| łatwe / średnie / trudne | 17/18, 35/46, 3/6 |

- Na zadaniach, których **na pewno nie było w sieci**, T1 ma tyle samo co na arkuszach CKE bez esejów (78.3% na 2024+2025). Brak śladu zawyżenia przez pamięć.
- Zastrzeżenia: E5 jest łatwiejsze (same zadania 1-punktowe, bez obrazów i esejów), a generował je ten sam model, który ocenia (luna), więc to kontrola „brak luki”, a nie estymator wyniku na arkuszu.

### 2d. Mock organizatorów (maj 2023)

Klucz = `dev2023_img` (te same ID). Przebieg `runs/mock-2023/gemma4-qat-t1final` (test na sucho): **78.3%** (47/60; zamknięte 9/11, esej 11/15; luna). Arkusz sprzed granicy wiedzy, więc potencjalnie „widziany”, ale wynik jest w tym samym przedziale co świeży 2026. Oficjalnej oceny sędziego organizatorów dla tego zgłoszenia nie mamy.

## 3. Audyt sędziego

### 3a. luna vs `gpt-6-sol` (otwarte + eseje, 5 przebiegów finału: 2024 s42/s43, 2025 s42/s43, 2026 s42)

| Przebieg | luna | sol | luna − sol |
|---|---|---|---|
| 2024 s42 | 72.9% | 72.9% | 0.0 |
| 2024 s43 | 66.1% | 64.4% | +1.7 |
| 2025 s42 | 71.7% | 75.0% | −3.3 |
| 2025 s43 | 73.3% | 71.7% | +1.7 |
| 2026 s42 | 83.3% | 83.3% | 0.0 |
| **razem (298 pkt)** | **73.5%** | **73.5%** | **0.00 pp** |

- Oceny różnią się w 10 ze 155 pozycji, 5 razy wyżej luna i 5 razy wyżej sol.
- Według typów (luna/sol/maks.): rozstrzygnij 51/53/71, podaj 47/46/56, wyjaśnij 22/22/30, inne 16/16/16, eseje 41/40/75.
- **Luna nie jest łagodniejsza.** Szum sędziego to ±1 pkt na pozycję, na arkusz ~±2 pp (SD).
- Kalibracja z raportu 02 (dev2023, 4 słabe modele, bez esejów): luna 61 vs oficjalny sędzia 59 pkt, sol również 61. Nasz lokalny proces może być ~1–3% względnie łagodniejszy od sędziego benchmarku.

### 3b. Ręczna kontrola rozbieżności z kluczem CKE

| Zadanie | luna | sol | Moja ocena wg klucza |
|---|---|---|---|
| 2025/3.1 „Akwedukt.” (funkcja budowli) | 0 | 1 | **sol** — klucz dosłownie: „funkcja wodociągu [akweduktu] / transport wody” |
| 2025/7.1 (ta sama wojna — tak) | 0 | 1 | raczej **sol** — rozstrzygnięcie i odwołanie do obu źródeł są; nieścisłość „skutki” vs „przyczyna” |
| 2025/18 s42 (rysunek 1919) | 2 | 3 | **luna** — błędne szczegóły (Marianna z mieczem, Germania podpisuje) |
| 2025/18 s43 | 3 | 2 | **sol** — podobne błędy („proklamacja cesarstwa”); luna niekonsekwentna między s42 i s43 |
| 2025/19 s43 (Wojciechowski †1933, Mościcki 1939) | 1 | 0 | **sol** — Wojciechowski zmarł w 1953; rezygnacja Mościckiego to konstytucja kwietniowa, nie marcowa |
| 2026/14.1 „Konstytucja KP (sierpniowa 1815)” | 1 | 0 | remis/luna — nazwa poprawna, dopisek błędny |
| 2026/14.2 (moneta 1835 podana jako 1855) | 0 | 1 | remis |
| eseje 2024 s43, 2025 s42/s43 | ±1 pkt | | szum |

Bilans: w ~4 przypadkach bliżej klucza jest sol, w ~2 luna. Błędy luny idą w obie strony (raz za surowo, raz za łagodnie), więc nie ma systematycznego zawyżenia.

### 3c. Grader zamkniętych (`eval/grade.py` + `normalize_closed`)

- **Nie jest łagodny.** Przejrzano 372 odpowiedzi zamknięte wszystkich przebiegów Gemmy:
  - `normalize_closed` zostawia jedną literę (ostatnią), a `parse_choice` wymaga dokładnie jednego kandydata;
  - wszystkie odpowiedzi finału mają dokładną składnię `answer_format`;
  - brak odpowiedzi z kilkoma literami przyjętych jako poprawne. Jedyny „hedge” to „A: USA (lub Stany Zjednoczone)” — oba poprawne.
- **Jest za surowy przy dopasowaniach z nazwami:** porównuje dosłowny napis klucza, więc „Zakon Benedyktynów” ≠ „benedyktyni”, a „USA” ≠ „Stany Zjednoczone”. W przebiegach finału/1120 odebrało to 3 pkt w `nt1final-s44` (2025/4 i 11.1) i 1 pkt w `nt1img1120-s43`. Sędzia organizatorów (LLM) to uzna, więc nasze liczby są tu **zaniżone**, nie zawyżone.
  - Propozycja dla koordynatora: w `grade.py` porównywać rdzenie wyrazów i aliasy (np. `fair_match` w `/tmp/val/perm_ana.py`) — nie zmieniałem, bo plik jest współdzielony.
- **Ryzyko na egzaminie:** przy `answer_format` „A: 1 / B: 1” i pytaniu o nazwy (2024/11.1) model w 2 z 6 przebiegów odpowiada numerami („A: 4 B: 5”) zamiast imion — 0 pkt. Poprawka w harnessie mogłaby przypominać o nazwach, gdy polecenie ich wymaga. Nie wdrażałem.

## 4. Realistyczna prognoza T1 na nowym arkuszu (jeden seed, ~60 pkt)

- Średnie finału według arkusza (luna): 2024 71.2% (3 seedy), 2025 70.3% (3 seedy, średnia starego i uczciwego gradera), 2026 83.3% (1120: 80%), mock 2023 78.3%. **Średnia ~76%, mediana ~75%.**
- Rozrzut: między arkuszami (po odjęciu szumu seeda) SD ≈ 5 pp; seed na jednym arkuszu ≈ 4 pp; sędzia ≈ 1.5–2 pp; niepewność średniej z 4 arkuszy ≈ 3 pp. Łącznie **SD ≈ 7.5 pp**.
- Korekty: sędzia organizatorów może być ~1–2 pp surowszy od luny (kalibracja dev2023); LLM uzna odmiany nazw (+~0.5 pp); klątwa zwycięzcy mała (nowy seed s44 przy uczciwym graderze: 71.4% ≈ średnia).
- **Prognoza: ~74% (≈ 44/60 pkt); przedział 80%: 64–84% (38–50 pkt), 95%: 60–88%.** Wynik 83% z 2026 to raczej górna część rozkładu, a 70% z 2024+2025 dolna-środkowa.

## 5. Rekomendacja: `--image-min-tokens 1120` — NIE wdrażać

| Zbiór | finał | 1120 | Δ |
|---|---|---|---|
| 2024+2025, razem | 70.3% (3 seedy) | 73.5% (2) | +3.2 |
| – zadania z obrazami (58 pkt) | 77.6% | 78.4% | **+0.9** |
| – bez obrazów, bez esejów (31 pkt) | 79.6% | 75.8% | −3.8 |
| – eseje (30 pkt, **bez obrazów**) | 46.7% | 61.7% | +15.0 |
| 2026 | 83.3% (1) | 80.0% (2) | **−3.3** |
| 2024+2025+2026 (przebiegi z kompletem) | 76.0% | 75.7% | −0.3 |

- Mechanizm się nie zgadza: opcja serwera zmienia tylko kodowanie obrazów, a cały zysk jest w esejach bez obrazów, czyli w szumie próbkowania eseju. Tam, gdzie opcja działa (obrazy), jest +0.9 pp, czyli ~0.5 pkt.
- Ryzyko: prompt z obrazem ~2× dłuższy, więcej VRAM i czasu. Znane awarie Gemmy przy `-ub 4096` z obrazami (CONTEXT, pułapki).
- Reguła z sekcji 1 nie jest spełniona (brak zysku bez esejów, przeciwny znak na 2026).
- Trzeci seed 1120 na 2024+2025 (`gemma4-qat__nt1img1120-s44`, worker obok) **nie dał wyniku**: o 04:50 procesy i serwery 8571/8572 już nie istniały, a katalogi przebiegów były puste. Jeden seed więcej na 2024+2025 i tak nie zmieniłby znaku na 2026 ani mechanizmu (zysk w esejach bez obrazów).

## 6. Koszt i pliki

- **API razem 1.35 $** z limitu 2 $: sol 1.29 $ (2024 s42: 0.26 $; pozostałe 4 przebiegi: 1.03 $) + luna 0.06 $ (40 otwartych E5). Oceny luna dla s44 i 2026-1120 wykonał worker obok.
- Oceny sol (osobne nazwy, luna nietknięta): `results/grades/<zbiór>/gemma4-qat-t1final__s4{2,3}__sol.judge.json`.
- Permutacje: `exams/test202{4,5}_v2_perm{1..4}/`, `eval/data/test202{4,5}_v2_perm{1..4}.jsonl`; przebiegi: `runs/test202{4,5}_v2_perm*/gemma4-qat__val-perm*`, kontrole `runs/test202{4,5}_v2/gemma4-qat__val-orig-s4{5,6}`.
- Sonda: `/tmp/val/mem_*.py`, wyniki `/tmp/val/mem_out.jsonl` (surowe), `/tmp/val/m_chat_all.jsonl` (prefill).
- Skrypty: `/tmp/val/vstats.py` (szum + bootstrap), `/tmp/val/perm_ana.py --fair`, `/tmp/val/perm_echo.py`, `/tmp/val/sol_cmp.py`.
- Serwer walidacyjny na H100: port 8391 (zatrzymany po zakończeniu; procesów innych workerów nie ruszałem).
- `server/final_configs.json` bez zmian.
