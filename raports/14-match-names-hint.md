# 14 — `--match-names-hint`: test na zadaniach, których dotyczy (27.09, 05:05–05:25)

**Wniosek: nie dodajemy flagi do żadnego tracku.** `server/final_configs.json` bez zmian.

## Na które zadania działa

`match_wants_names` (typ `closed_match`, wzór „A: 1”, polecenie bez słów „numer/cyfr/liczb/oznacz/liter”) łapie dokładnie zadania z raportu 13:
- 2024: 11.1;
- 2025: 4, 5.1, 11.1;
- 2026: 6.1, 21.

Wskazówka w prompcie i wyłączenie redukcji do liczby są za `args.match_names_hint and match_wants_names(item)`, więc pozostałych zadań flaga nie zmienia.

## Metoda

- Przebiegi z flagą: `server/mn_run.sh t1|t2|t3` → `fx-t1mn-s42/43`, `fx-t2mn-s42/43`, `fx-t3mn-s42/43`, z `--only-ids` na sześciu zadaniach. Konfiguracje jak w `final_configs.json` tuned (T3: UD-IQ3_XXS, limit rozumowania 5000 + komunikat).
- Punkt odniesienia to istniejące przebiegi bez flagi:
  - T1: `gemma4-qat-t1final__s42/s43`, `gemma4-qat__nt1final-s44`; na 2026 tylko s42. Przebiegi `fx-t1rh` mają te zadania scalone z t1final, więc nie są niezależne.
  - T2: `fx-t2ff`, `fx-t2ff2`, `fx-t2base`, `pllum-v1recipe-full-polqa`, `pllum-kbab-v1`.
  - T3: `q35-4b-iq3xxs__nt3rb-s42`, `__nt3rbE3-s43`, `q35-4b-cq-stock-iq3xxs__bf5k-s42`, `q35-4b-udiq3xxs__bf5k-modal-s7`; na 2026 tylko s43.
- Ocena: łagodne porównanie z kluczem CKE, bo `grade.py` porównuje dosłownie. Liczy się rdzeń nazwy i warianty, np. „Zakon Benedyktynów” = benedyktyni, USA = Stany Zjednoczone, „Anjou”/„Andegawenowie”; numer władcy musi się zgadzać. Punktacja: komplet = max; przy max 2 za jeden błąd 1 pkt. Skrypt: `/tmp/mn_grade.py`. Sędzia luna nieużyty (ocenia tylko pozycje otwarte), koszt $0.

## Wyniki (punkty, średnia na przebieg)

| Zadanie (max) | T1 bez | T1 z | T2 bez | T2 z | T3 bez | T3 z |
|---|---|---|---|---|---|---|
| 2024/11.1 (1) | 0.33 | 0.5 | 0 | 0 | 0 | 0 |
| 2025/4 (2) | 1.67 | 2.0 | 2.0 | 2.0 | 1.5 | 1.0 |
| 2025/5.1 (1) | 0.67 | **0** | 0 | 0 | 0 | 0 |
| 2025/11.1 (2) | 2.0 | 2.0 | 1.8 | 2.0 | 1.0 | 1.0 |
| 2026/6.1 (1) | 1.0 | 0.5 | 1.0 | **0**\* | 1.0 | 0.5 |
| 2026/21 (2) | 2.0 | 2.0 | 2.0 | 2.0 | 1.0 | 1.5 |
| **Suma (9)** | **7.67** | **7.0** | **6.8** | **6.0** | **4.5** | **4.0** |

Suma z dwóch seedów wobec dwukrotności średniej bazy: T1 14 vs 15.3, T2 12 vs 13.6, T3 8 vs 9.0. Żaden track nie zyskuje, więc reguła decyzyjna mówi „nie”.

\* T2 2026/6.1 z flagą: „Rurykowicze / Andegawenowie” bez liter „A:”/„B:”. Treść jest poprawna, ale format zepsuty. Nawet licząc tu 1 pkt, T2 ma 14 vs 13.6, czyli remis w granicach szumu.

## Przykłady

- **T2 2024/11.1** (klucz: A Karol IX, B Henryk IV): bez flagi zawsze „A: 1 / B: 2” — to surowe wyjście modelu, nie skutek obcinania. Z flagą „A: Karol IX / B: Henryk II”. Nazwy się pojawiają, ale punkt nadal jest stracony. Podobnie 2025/5.1: „A: 1 / B: 1” → „A: Przemysł II / B: Henryk V” (klucz: Wacław II, Brzetysław I).
- **T1 2025/5.1**: bez flagi 2 z 3 poprawnie („A: Wacław II / B: Brzetysław I”). Z flagą „A: Władysław II / B: Władysław III” oraz „A: Władysław II / B: Przemysł Ottokar II” — 0 z 2.
- **T3 2025/4** s42: bez flagi „Franciszkaninowie / Benedyktyni / Jezuici” (2 pkt). Z flagą „Premonstratensians / Cistercy / Dominikanie” (0 pkt).

## Obcinanie do liczby

Błąd „A: Karol IX (1560–1574)” → „A: 1560” nie wystąpił w żadnym przebiegu bazowym obecnych konfiguracji finałowych na tych zadaniach. T1 i T3 wpisują same nazwy, a T2 wpisuje cyfry już w surowej odpowiedzi. Liczby typu „A: 1561 / B: 1598” są tylko w starych wariantach T3 (IQ2_M, Q3_K_S, `t3cfg` bez limitu). Poprawka nie ma więc na co wpłynąć w finale. Flaga zostaje w `run_exam.py` jako opcja, domyślnie wyłączona.
