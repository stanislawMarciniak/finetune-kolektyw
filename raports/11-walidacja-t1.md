# 11 — Walidacja wyniku T1 i reguła decyzji o zmianie konfiguracji (nd 27.09, 04:05–04:50)

Pytania: (1) czy 71.0% T1 (Gemma-4-12B QAT `t1final`, sędzia `gpt-6-luna`) jest zawyżone, (2) ile pp i seedów trzeba, żeby zmienić konfigurację. `server/final_configs.json` bez zmian. Skrypty: `/tmp/ana/stats.py` (bootstrap, MDD, winner's curse), `/tmp/ana/solcmp.py` (luna vs sol), oceny sol w `/tmp/soljudge/results/grades/`, powtórka luny w `/tmp/lunajudge/results/grades/` (oryginalne oceny luny nietknięte). Sonda kontaminacji pominięta (decyzja: czas).

## Podsumowanie

| | Wynik |
|---|---|
| **Sędzia luna vs mocniejszy `gpt-6-sol`** (T1 s42, wszystkie otwarte + eseje) | 2024: 37 vs 37 pkt, 2025: 32 vs **36**, 2026: 40 vs 39. **Luna nie jest łagodniejsza** — średnio o ~1 pkt/arkusz *surowsza*; zgodność zadań 86/92 (93%). Dodatkowo 2024 s43: 34 vs 33. |
| **Powtórka luny na tych samych odpowiedziach** (s42 + s43, 2024+2025, 124 pozycje) | zgodność 119/124 (96%); sumy −0.8 pp i +1.7 pp; prawie cały rozrzut to eseje (2024 s43: 9 → 12 pkt). |
| **Ręczny audyt klucza** (16 zadań z Polski/obrazami, luna dała punkty) | 14 ocen w porządku, **2 łagodne na granicy** (~2 pkt ≈ 1.7 pp u surowego egzaminatora CKE). |
| **Zamknięte (`eval/grade.py`)** | dokładne: tabela punktów zgodna z zasadami CKE we wszystkich 24 zadaniach, bez luźnej normalizacji; w T1 s42 wszystkie sparsowane automatycznie. |
| **Mianownik** | arkusze 60 pkt (zgodne z CKE), esej 15 pkt (2024/26, 2025/25, 2026/26); 2024/21 (1 pkt) poza mianownikiem → 119 pkt; wpływ ±0.4 pp. |
| **T1 (2024+2025, 2 seedy)** | **71.0%, 95% CI [63.7, 77.6]** (bootstrap po zadaniach + seedach) |
| **Szum jednego przebiegu** (seed + sędzia, 119 pkt) | σ ≈ 1.5 pp (4 pary seedów, różnice 1.7–2.5 pp; ostrożnie przyjmować 2 pp) |
| **Minimalna wykrywalna różnica** (α = 0.05, moc 80%, tylko szum seedów) | 1 seed/ramię: **6 pp**; 2 seedy: **4.2 pp**; 3 seedy: 3.5 pp; 5 seedów: 2.7 pp |
| **Winner's curse** (7 konfiguracji T1 na 2024+2025) | najlepsza z 7 przy 1–2 seedach jest zawyżona średnio o **+1.5–2.0 pp** |

**Wniosek:** wynik T1 **nie jest zawyżony przez sędziego** (sol daje tyle samo albo więcej). Realne źródła „zawyżenia” to: rozrzut między arkuszami (69.5 / 72.5 / 83.3% — 2026 jest dla Gemmy łatwy), winner's curse ~1–2 pp i ewentualnie surowszy sędzia organizatorów (~1–2 pp). **Realistyczny wynik T1 na egzaminie: ~72%, przedział 80% ≈ 65–79%** (95%: ~62–82%). **~2 pp to nie jest powód do zmiany** — to ok. 1σ szumu dla jednego seeda.

## 1. Audyt sędziego: luna vs sol

`eval/judge_openai.py` nie ma opcji ścieżki wyjścia — uruchomione przez wrapper z podmienionym `RES` na kopię wejść w `/tmp/soljudge/results` (ten sam prompt/zasady, `--model gpt-6-sol --essay-model gpt-6-sol`).

| Arkusz (T1 s42) | pozycji sędziego | luna | sol | różnica | zgodność | wynik % luna → sol |
|---|---|---|---|---|---|---|
| 2024 (59 pkt) | 33 | 37 | 37 | 0 | 33/33 | 72.9 → 72.9 |
| 2025 (60 pkt) | 29 | 32 | 36 | **+4** | 25/29 | 71.7 → **78.3** |
| 2026 (60 pkt) | 30 | 40 | 39 | −1 | 28/30 | 83.3 → 81.7 |
| 2024 s43 (dodatkowo) | 33 | 34 | 33 | −1 | 32/33 | 66.1 → 64.4 |

- **Średni bias (sol − luna): +0.5 pkt/arkusz** (+2 pkt na 4 arkusze-przebiegi; na 2024+2025 s42 +4 pkt = +3.4 pp, na 2024 s43 −1 pkt). Luna nie zawyża; jeśli już, lekko zaniża pojedyncze „rozstrzygnij”.
- Kalibracja z wcześniej (DEV-2023, 104 oceny oficjalnego sędziego benchmarku, słabsze modele): luna 61 vs oficjalne 59 pkt, sol też 61 vs 59 — oba sędziowie ~2 pkt / 104 łagodniejsze od oficjalnego. To jedyny sygnał łagodności: **~−1–2 pp** względem sędziego organizatorów (jeśli używa tego samego co benchmark).

Rozbieżności (wszystkie):

| Zadanie | luna | sol | Odpowiedź Gemmy | Klucz CKE | Komentarz |
|---|---|---|---|---|---|
| 2025/3.1 (funkcja budowli, 1) | 0 | 1 | „Akwedukt.” | „funkcja wodociągu [akweduktu] / transport wody” | klucz sam podaje „akweduktu” — sol ma rację, luna za surowa |
| 2025/7.1 (ta sama wojna, 1) | 0 | 1 | „Tak … Źródło 1 opisuje akt … włączenia ziem pruskich … mapa … tereny nabyte w 1466 r.” | „tak … inkorporacja Prus … wojna trzynastoletnia” | **niestabilne**: luna 0, powtórka luny 1, sol 1 |
| 2025/18 (rysunek 1871/1919, 3) | 2 | 3 | odwet Francji, traktat wersalski, ale „Marianna trzyma miecz” | przesłanie + 2 elementy + kontekst 1919 | luna odjęła za nieścisłe szczegóły opisu |
| 2025/25 (esej, 15) | 6 | 7 | esej o Jagielle, unia horodelska „1417” | — | sol liczy więcej błędów (4), ale wyżej ocenia argumentację |
| 2026/14.2 (moneta i Statut, 1) | 0 | 1 | „Tak … Statut organiczny … moneta w rublach” | „tak … upadek powstania listopadowego” | brak jawnego „powstania listopadowego”; na granicy |
| 2026/26 (esej, 15) | **12** | 10 | rewolucja przemysłowa | — | tu luna łagodniejsza (aspekt kulturowy „ogólnikowy” wg sol) |
| 2024/26 s43 (esej, 15) | **9** | 8 | Karol Wielki, „Langebankowie”, „margralowcy” | — | luna łagodniejsza o 1 |

Luna dała więcej niż sol tylko na **esejach** (2 przypadki, −3 pkt); sol więcej na 4 zadaniach krótkich + 1 eseju (+5 pkt).

## 2. Ręczny audyt ocen luny (16 zadań, pełne punkty, Polska/obrazy, 2024–2025, s42)

Sprawdzone: 2024/4, 5.1, 5.2, 8.2, 9, 11.2, 12.2, 12.3, 19.2, 22.2, 23.1, 23.2, 24; 2025/12, 16.1, 16.2. 14/16 jednoznacznie zgodne z kluczem (np. 2024/24: „Nie … Czechosłowacja 1968 … Węgry 1956, Imre Nagy” = klucz; 2024/23.2: „zniesienie Senatu 27% … pytanie nr 3 67%” = klucz). **Łagodne na granicy:**

- **2024/19.2** (generał Litwy Środkowej): „Nazwisko generała to: **Józef** Żeligowski” — klucz „[Lucjan] Żeligowski”. Luna: „błędne imię nie wpływa na ocenę”. Egzaminator CKE przy błędnym elemencie dodatkowym zwykle daje 0 → **−1 pkt**.
- **2025/16.2** (rewolucja 1905): rozstrzygnięcie i uzasadnienie poprawne, ale „powoływał **Dumę Pałacową**” (Duma Państwowa). Luna: „błędne określenie nie podważa uzasadnienia”. Błąd merytoryczny w uzasadnieniu — u surowego egzaminatora **−1 pkt**.
- Drobne, niekarane: 2024/11.2 „edykt nantejski w latach 1589–1610” (pomieszane daty panowania z edyktem), 2024/5.2 „Cesarstwo Bizancjum” (akceptowalne).

Szacunek: ~2 łagodne oceny na 16 (12%) → na ~40 pełnych ocen luny na 2024+2025 **~3–5 pkt ≈ 2.5–4 pp** w najsurowszym scenariuszu; realnie (sol też je akceptuje, nasz prompt sędziego mówi „nieszkodliwe dodatki nie odbierają punktów”) **~1–2 pp**.

## 3. Zamknięte — `eval/grade.py`

- `score()` odtwarza dokładnie zasady CKE: 2 pkt/3 wskazania → 3→2, 2→1, ≤1→0; 1 pkt/2 wskazania → tylko komplet. Sprawdzone na wszystkich 24 zadaniach zamkniętych 2024–2026 (6 + 9 + 9) — zgodne z `rubric`.
- Parsowanie: litery/P-F/dopasowania po numerach, `norm` tylko NFKC + lowercase + usunięcie markdownu; niejednoznaczne → sędzia (nie dostaje punktu „z automatu”). Spot-check T1 s42 (24 pozycje, np. 2024/20.2 „F P P” vs klucz „F P F” → 1 pkt; 2025/14.2 „F F P” vs „P F P” → 1; 2026/6.1 „Anjou” vs „Andegawenowie / Anjou” → 1): wszystko poprawne.
- Jedyna furtka: `parse_tf` przy braku numeracji bierze ostatnie n liter P/F z całej odpowiedzi — w T1 nieużyta (wszystkie odpowiedzi numerowane). Zamknięte to tylko 20 z 119 pkt — sędzia decyduje o ~83% wyniku.

## 4. Mianownik

- Arkusze: 2024 = 60 pkt / 40 pozycji, 2025 = 60 / 38, 2026 = 60 / 39 — zgodne z maksimum arkusza rozszerzonego CKE (60 pkt). Esej 15 pkt (A 0–12 + B 0–3).
- 2024/21 (1 pkt; odrzucany przez filtr treści sędziego) poza mianownikiem → 119 pkt. Wpływ na wynik T1 (84.5/119 = 71.0%): przy mianowniku 120 i 0 pkt za 2024/21 → 70.4%, przy 1 pkt → 71.3% — **−0.6 / +0.3 pp**, pomijalne.
- Esej to 25% arkusza i główne źródło szumu: T1 dostaje 5–13/15 za esej (t1final: 9, 6 / 9, 5; img1120: 13, 6 / 10, 8).

## 5. Statystyka (2024+2025, 119 pkt)

Bootstrap hierarchiczny: losowanie zadań w warstwach (arkusz × esej/nie-esej; esej zawsze 1 na arkusz), w każdym zadaniu losowy seed; różnice sparowane po zadaniach; 4000 powtórzeń.

| Konfiguracja | seedy | wynik | 95% CI |
|---|---|---|---|
| T1 t1final (finał) | 2 | 71.0% (72.3 / 69.7) | [63.7, 77.6] |
| T1 `--image-min-tokens 1120` | 2 | 73.5% (74.8 / 72.3) | [66.4, 80.4] |
| T3 UD-IQ3_XXS (finał) | 2 | 43.3% (42.9 / 43.7) | [35.0, 51.2] |
| T3 Q3_K_M temp. 0.6 | 2 | 50.0% (48.7 / 51.3) | [41.4, 58.3] |

| Różnica (sparowana) | Δ | 95% CI (zadania + seedy) | SD |
|---|---|---|---|
| img1120 − t1final | +2.5 pp | [−4.8, +10.0] | 3.7 |
| temp. 0.6 − t1final (1 vs 2 seedy) | +0.4 | [−5.8, +6.0] | 3.0 |
| stary prompt − t1final | +1.3 | [−5.3, +8.0] | 3.4 |
| kompendium (t1kb) − t1final | −2.1 | [−8.7, +4.8] | 3.4 |
| RAG PolQA − t1final (1 seed) | −2.9 | [−9.2, +3.3] | 3.2 |
| img560 − t1final (1 seed) | −4.6 | [−10.3, +0.8] | 2.8 |
| T3 IQ3_XXS − Q3_K_M t0.6 | −6.7 | [−16.4, +2.6] | 4.9 |

**Żadna różnica T1 nie jest istotna.** Najbliżej: img560 (−4.6 pp, CI dotyka 0) — odrzucenie było słuszne.

### Szum i minimalna wykrywalna różnica

- Pary seedów tej samej konfiguracji (t1final, legacy, t1kb, img1120): różnice +2.5, +1.7, +1.7, +2.5 pp; 13–15 z 77 zadań zmienia ocenę. σ pojedynczego przebiegu ≈ **1.5 pp** (mała próba; ostrożnie 2 pp). Na pojedynczym arkuszu 60 pkt rozrzut seedów sięga **6.8 pp** (2024: 72.9 vs 66.1).
- Szum sędziego (powtórka luny na tych samych odpowiedziach): **0.8–1.7 pp** na 119 pkt, prawie wyłącznie eseje (±1–3 pkt). Uwaga: `judge_reuse` kopiuje oceny identycznych odpowiedzi, więc σ z par seedów zaniża część szumu sędziego.

| seedy na ramię | SD różnicy (σ = 1.5 / 2.0) | próg 2σ | MDD (α = 0.05, moc 80%) |
|---|---|---|---|
| 1 | 2.1 / 2.8 pp | 4.2 / 5.5 | **6.0 / 7.9** |
| 2 | 1.5 / 2.0 | 3.0 / 3.9 | **4.2 / 5.6** |
| 3 | 1.2 / 1.6 | 2.4 / 3.2 | 3.5 / 4.6 |
| 5 | 1.0 / 1.3 | 1.9 / 2.5 | 2.7 / 3.5 |

To tylko szum powtórzeń na **tych samych** arkuszach. Czy zmiana pomoże na **nowym** arkuszu, zależy jeszcze od zmienności efektu między zadaniami (CI sparowane wyżej: ±7 pp przy 2 seedach) — tego nie zmniejszą seedy, tylko więcej arkuszy (2026 jako trzeci).

### Winner's curse

Na 2024+2025 porównano 7 pełnych konfiguracji T1 (t1final, legacy, t1kb, t1polqa, t06, img1120, img560; średnie 66.4–73.5%) + pary refine esejów. Symulacja przy równych prawdziwych średnich: najlepsza z 7 jest zawyżona o **+2.0 pp** (1 seed) / **+1.5 pp** (2 seedy); z 10 — +2.3 / +1.6 pp. t1final nie był maksimum w tej rundzie (wybrany wcześniej), więc jego obciążenie ≈ 0–1.5 pp; **img1120 (73.5%) byłby wyborem z zawyżeniem ~1.5 pp — czyli jego +2.5 pp to w ~60% efekt selekcji**. 2026 nie był używany do selekcji → bez tego obciążenia (ale 1 seed i łatwiejszy dla Gemmy arkusz).

## 6. Realistyczny wynik T1 na egzaminie

| Składnik | Wpływ |
|---|---|
| Punkt wyjścia: średnia z 3 arkuszy (luna) | 2024 69.5, 2025 72.5, 2026 83.3 → ~74% |
| Korekta luna → sol | +0.5 pkt/arkusz → **~0 do +1 pp** (brak zawyżenia) |
| Łagodne oceny vs surowy egzaminator CKE (audyt ręczny, kalibracja DEV-2023) | **−1 do −2 pp** |
| Winner's curse | **−0 do −1.5 pp** |
| Rozrzut: jeden przebieg na nowym arkuszu 60 pkt (zadania + seed + esej) | SD ≈ 5 pp |

**Środek ~72%, przedział 80% ≈ 65–79%, 95% ≈ 62–82%.** Najsłabszy obserwowany pojedynczy arkusz-przebieg: 66.1% (2024 s43).

Uwaga T3 (poza zakresem, ale wynika z tych samych liczb): IQ3_XXS 43.3%, CI [35.0, 51.2]; na pojedynczym nowym arkuszu SD ~6 pp → **P(< 35%) ≈ 8–10%**. Zapas Q3_K_S (48.3% na 2026) warto mieć pod ręką.

## 7. Reguła decyzji (od teraz)

Status quo wygrywa remis — jest już przetestowany na sucho i znany. Zmieniamy konfigurację/model, gdy:

| Typ zmiany | Wymóg |
|---|---|
| **A. Jasny mechanizm, naprawa konkretnej awarii, mały koszt poza celem** (np. limit myślenia na pętle, poprawka nagłówka eseju, retry przy crashu) | zysk skupiony na zadaniach, których dotyczy mechanizm (mierzalnie: np. powtórki 45 → 4), pozostałe zadania bez straty > 1 pp; **≥ +2 pp przy 2 seedach** albo dowolny zysk, jeśli zmiana nie może dotknąć innych zadań. Przykład spełniający: T3 limit 5000 (+4.2 pp, fallbacki 44–49 → 4). |
| **B. Zmiana globalna bez mechanizmu** (temperatura, prompt, tokeny obrazu, RAG, inny kwant tego samego modelu) | **≥ +4 pp przy ≥ 2 seedach na ramię** (≈ MDD) **i** ten sam znak na 2024, 2025 i 2026; albo ≥ +3 pp przy 3 seedach + ten sam znak na 3 arkuszach. |
| **C. Zysk głównie z eseju** | odjąć esej i ocenić resztę wg A/B; esej sam dla siebie wymaga par na tych samych esejach (`--essay-from`) i ≥ +1 pkt/esej na ≥ 6 parach. |
| **D. Zmiana z ryzykiem operacyjnym** (inny model, więcej VRAM/tokenów, dłuższy czas, nowa flaga serwera) | jak B **plus** test na sucho przez `exam_run.sh` na maszynie egzaminacyjnej. |
| **E. Kryterium tracka (rozmiar T3, próg 35%)** | dopuszczalna strata wyniku, jeśli dolna granica 95% CI zostaje ≥ 35% (obecnie IQ3_XXS: 35.0 — na granicy). |

**Odpowiedź na „czy ~2 pp wystarczy”: nie.** 2 pp to ~1σ przy jednym seedzie; bez mechanizmu wymaga to ok. 5 seedów na ramię, żeby było rozróżnialne od szumu, a i tak nie przenosi się pewnie na nowy arkusz. `--image-min-tokens 1120` (+2.5 pp, 2 seedy, 2025 s43 −3.3 pp, efekt ~60% z selekcji) — **zostaje odrzucony**, chyba że potwierdzenia siostrzanego workera (2026 s42/s43 + trzeci seed 2024+2025) dadzą łącznie ≥ +3 pp na 3 seedach i + na 2026.

## Koszt

- `gpt-6-sol`: ~150 wywołań (T1 s42 na 3 arkuszach + 2024 s43 i część 2025 s43 z przerwanego przebiegu) — ≈ 1.15 $ wg cennika w `judge_openai.py` (5/30 $/M), **realnie ≈ 0.45–0.55 $** (cennik `data_gen/common.py`: 2.04/12.2 $/M).
- `gpt-6-luna` powtórka: 124 wywołania, ≈ 0.02 $ realnie.
- **Razem ≈ 0.5 $** (limit 1.50 $).
