# 19 — Głosowanie większościowe na zadaniach zamkniętych (nd 27.09, 05:55–)

Pomysł: dla zadań zamkniętych (wybór A–D, P/F, dopasowania „A: x”) zamiast jednej próbki (temp. 1.0 w T1, 0.6 w T3) brać K próbek i głosować per część odpowiedzi (litera / „1: P” / „A: nazwa”), remis → pierwsza próbka; opcjonalnie oszczędnie: 2 próbki i dobór do K tylko przy niezgodzie („bramka zgodności”). T2 (temp. 0) pominięty. `server/final_configs.json` — **bez zmian** (patrz decyzja).

## Podsumowanie

**Decyzja: nie włączamy** (config T1 bez zmian; flaga zostaje jako opcja). Efekt jest realny i dodatni na wszystkich arkuszach, ale po dołożeniu realnych próbek wynosi ~**+1.0 pp** (ścisły `grade.py`) / **+0.75 pp** (łagodny, bliżej sędziego AI) — poniżej progu +1.5 pp — a czas T1 rośnie ~3× (mock 324 → 996 s), co przy wyniku „na ekranie w czasie slotu” jest realnym ryzykiem.

| | Wynik |
|---|---|
| **Symulacja T1, pula końcowa** (12–14 niezależnych próbek/zadanie na 2024 i 2025 — stare przebiegi + próbki z przebiegów z flagą) | 2024+2025: K=3 **+0.60 pp**, K=5 **+1.09 pp** [95% CI +0.20…+2.06], adaptacyjnie 2→5 **+1.02 pp** (śr. 3.2 próbki). Łagodnie: K=5 +0.80, 2→5 +0.75 pp. 2026: +0.65 pkt / 60 = +1.1 pp |
| Symulacja T1, pula wstępna (6–9 próbek) | K=5 +1.51 pp (łagodnie +1.05) — zawyżona przez małą pulę; zmalała po dołożeniu próbek |
| **Symulacja T3** (finał IQ2_M-PL-E4K-MIX: tylko 3 próbki/zadanie; proxy UD-IQ3_XXS: 9) | MIX K=3: +0.56 pp (łagodnie +0.83), CI szerokie [−1.4, +2.5]; IQ3_XXS K=5 **+1.11 pp** (łagodnie +1.24), 2026 +1.6 pp — poniżej progu → T3 bez kroku 2 |
| **Przebiegi rzeczywiste T1** (L40S, seed 47, pierwsza próbka vs głos, sparowane) | 2024 zamknięte **4 → 7 pkt**, 2025 **9 → 10**, 2026 (adaptacyjnie) **8 → 10** (z kluczem rdzeniowym) → +4 pkt = +3.4 pp na 2024+2025; zgodne co do znaku, ale seed 47 miał pechową pierwszą próbkę (2024: 4/8 vs średnia puli 5.3) |
| **Koszt czasu** | pełne arkusze K=5: tokeny 153k / 177k (zwykle ~60–90k), zamknięte stają się ścieżką krytyczną (maks. 1.8–1.9 tys. s vs 1.0–1.25 tys. s reszty, L40S współdzielony). Test na sucho `exam_run.sh` mock T1 z `--vote-closed 5 --vote-adaptive` (L40S): **996 s vs 324 s**, tokeny 143k vs 54k (zamknięte 90k vs 22k; najdłuższe zamknięte 870 vs 242 s); część z równoległego T3 innego agenta. 37 odpowiedzi, 0 błędów, głos nie zmienił żadnej odpowiedzi na mocku |
| **Bramka po logprobach** | §4 — litera odpowiedzi po myśleniu ma p ≈ 1 (trafna) / 0.73 (błędna) na n = 2; bez kalibracji → niewdrożona; zamiast niej bramka zgodności 2 próbek |
| **Kod** | `harness/run_exam.py --vote-closed K [--vote-adaptive]` (domyślnie wyłączone; zsynchronizowane na H100 i L40S), `eval/vote_sim.py` (symulacja, `--lenient`, `-v`), `eval/vote_real.py` (analiza przebiegów z flagą) |

## 1. Metoda (offline, zero GPU, zero sędziego) — `eval/vote_sim.py`

- Próbki: wszystkie przebiegi w `runs/<zbiór>/*/debug.jsonl` o tej samej konfiguracji zadań zamkniętych: T1 = Gemma QAT, temp. 1.0, myślenie na zamkniętych, bez RAG i starego promptu (t1final s42/s43/s44, t1kb s42/s43 — kompendium dotyczy tylko eseju, val-orig s45/s46, fx-t1*; osobno pula „+img1120”). T3 = Qwen3.5-4B temp. 0.6, pule per kwant. Pominięte rekordy `merged_from` (skopiowane z innego przebiegu) i duplikaty po treści rozumowania — zostają tylko niezależne losowania.
- Ocena jak `eval/grade.py` (dokładne zasady CKE; nierozpoznana część = zła). Wariant `--lenient`: w dopasowaniach nazw akceptuje formy fleksyjne i aliasy („zakon franciszkanów”, „USA”) — ścisły `grade.py` ich nie uznaje, a sędzia AI organizatorów najpewniej tak; ten wariant zmniejsza pozorny zysk z głosowania „na formie” (2025/4, 11.1).
- Symulacja: 4000 losowań K próbek bez zwracania (pierwsza = wynik bez głosowania, ta sama pierwsza próbka w obu ramionach → różnica sparowana). „90%” w tabeli = rozrzut zysku dla jednego egzaminu (kombinacje seedów); „95% CI” niżej = bootstrap po zadaniach (warstwy = arkusze) oczekiwanego zysku.
- Zadania zamknięte: 2024 — 6 zadań / 8 pkt (z 59), 2025 — 9 / 12 (z 60), 2026 — 9 / 10 (z 60). Łącznie 20 z 119 pkt na 2024+2025 → +1 pkt = +0.84 pp.

## 2. Tabela symulacji (ścisły `grade.py`; zysk w pkt arkusza)

| pula | arkusz | próbek/zad. | zadań/pkt | jednomyślne | K=3 | K=5 | 2→5 adapt. (śr. próbek) |
|---|---|---|---|---|---|---|---|
| **T1 pula końcowa** (+ próbki z przebiegów z flagą) | 2024 | 12–14 | 6/8 | 1/6 | 5.28 → 5.48 (**+0.20**) | 5.29 → 5.76 (**+0.47**) | +0.46 (3.6) |
| **T1 pula końcowa** | 2025 | 11–14 | 9/12 | 4/9 | 9.28 → 9.80 (**+0.52**) | 9.26 → 10.08 (**+0.82**) | +0.75 (2.9) |
| **T1 pula końcowa** | 2026 | 3–8 | 9/10 | 7/9 | 9.15 → 9.41 (+0.27) | 9.17 → 9.82 (**+0.65**) | +0.64 (2.5) |
| T1 Gemma QAT (pula wstępna, niżej) | 2024 | 7–9 | 6/8 | 1/6 | 4.91 → 5.05 (**+0.14**) | 4.91 → 5.55 (**+0.64**) | +0.59 (3.5) |
| T1 Gemma QAT | 2025 | 6–9 | 9/12 | 4/9 | 9.08 → 9.76 (**+0.68**) | 9.07 → 10.23 (**+1.16**) | +1.08 (3.1) |
| T1 Gemma QAT | 2026 | 1–3 | 9/10 | 8/9 | +0.33 (tylko 6.1 ma 3 próbki) | — | — |
| T1 +img1120 | 2024 | 9–11 | 6/8 | 1/6 | +0.28 | +0.82 | +0.78 (3.5) |
| T1 +img1120 | 2025 | 8–11 | 9/12 | 4/9 | +0.53 | +0.84 | +0.77 (3.0) |
| T1 +img1120 | 2026 | 3–5 | 9/10 | 7/9 | 9.27 → 10.00 (**+0.73**) | +0.73 | +0.74 (2.3) |
| T3 IQ2_M-PL-E4K(-MIX) (finał) | 2024 | 3 | 6/8 | 3/6 | 4.68 → 5.00 (+0.32) | — | — |
| T3 IQ2_M-PL-E4K(-MIX) | 2025 | 3 | 9/12 | 2/9 | 5.35 → 5.68 (+0.33) | — | — |
| T3 IQ3_XXS | 2024 | 9 | 6/8 | 0/6 | 4.00 → 4.37 (+0.37) | +0.43 | +0.40 (3.8) |
| T3 IQ3_XXS | 2025 | 9 | 9/12 | 1/9 | 5.92 → 6.51 (+0.60) | +0.91 | +0.96 (3.8) |
| T3 IQ3_XXS | 2026 | 4–5 | 9/10 | 2/9 | 5.54 → 6.06 (+0.52) | +0.96 | +0.97 (3.2) |
| T3 Q3_K_M | 2024 | 3 | 6/8 | 2/6 | +0.33 | — | — |
| T3 Q3_K_M | 2025 | 3 | 9/12 | 2/9 | +0.68 | — | — |

Rozrzut dla jednego egzaminu (kombinacje seedów, 90%): zwykle −1…+2 lub −1…+3 pkt na arkusz — głosowanie może w pojedynczym przebiegu stracić punkt, ale średnio zyskuje wszędzie.

**Suma 2024+2025 (119 pkt), bootstrap po zadaniach:**

| pula | K=3 | K=5 | 2→5 adapt. |
|---|---|---|---|
| T1 (ścisły) | +0.69 pp [+0.01, +1.42] | **+1.51 pp [+0.18, +2.91]** | +1.40 pp [+0.16, +2.74] |
| T1 (łagodny) | +0.46 pp [−0.06, +0.99] | +1.05 pp [+0.00, +2.10] | +0.96 pp [−0.03, +1.93] |
| T1 +img1120 (ścisły / łagodny) | +0.68 / +0.47 | +1.39 / +1.03 | +1.30 / +0.95 |
| T3 MIX (ścisły / łagodny) | +0.54 / +0.82 pp | — | — |
| T3 IQ3_XXS (ścisły / łagodny) | +0.81 / +0.85 | +1.13 / +1.24 | +1.14 / +1.23 |

Wniosek: efekt jest **realny, ale mały** — to 1–2 pkt na 119, bo zamknięte to tylko 17% arkusza, a większość z nich model i tak rozwiązuje stabilnie (jednomyślne albo stabilnie złe: T3 2025/5.1 0/9, 2024/11.1 0/9). K=3 daje mniej niż połowę efektu K=5 (przy 3 próbkach per część łatwo o remis → pierwsza próbka). Bramka zgodności (2→5) zachowuje ~93% zysku K=5 przy ~3.3 zamiast 5 próbek.

## 3. Przebiegi rzeczywiste (T1, L40S, własny serwer z konfiguracją finałową)

Najpierw próba na H100 (współdzielony serwer finałowy :8830) — kolejka innych agentów (23 procesy harnessu na 2 serwerach po 8 slotów), po 12 min bez odpowiedzi → przerwane (tylko moje procesy). Potem własny llama-server T1 (dokładnie `final_configs` T1 server) na L40S :8871, harness T1 final + `--seed 47`: 2024 i 2025 pełne arkusze `--vote-closed 5`, 2026 tylko zamknięte `--vote-closed 5 --vote-adaptive`. Wyniki w `runs/test202x_v2/gemma4-qat__vote5-s47` i `gemma4-qat__vote5a-s47-closed` (`python eval/vote_real.py <katalog>`).

| arkusz | pierwsza próbka | głos | zmiany |
|---|---|---|---|
| 2024 (K=5) | 4 / 8 | **7 / 8** | 10: B,B,A,A,A → A (+1); 14.2: B,D,C,C,C → C (+1); 19.1: F F P + 4× F P P → F P P (+1); 11.1: Karol IX/Małgorzata 3× — głos nie pomógł |
| 2025 (K=5) | 9 / 12 | **10 / 12** | 4: „Zakon franciszkański…” + 4× „Franciszkanie, Benedyktyni, Jezuici” → +2; 11.1: „Stany Zjednoczone” vs 3× „USA” → „USA” (−1 tylko w ścisłym `grade.py`; sędzia AI uzna oba) |
| 2026 (adaptacyjnie, tylko zamknięte) | 8 / 10 | 9 / 10 (klucz dokładny), **10 / 10** (klucz rdzeniowy) | 7/9 zadań skończyło się na 2 zgodnych próbkach; 19.2: P F + 3× F P → F P (+1); 6.1: Kapetingowie / Anjoujczycy / Annijowowie / Anjou / Annażowie — przy kluczu dokładnym remis → pierwsza (zła), po zmianie na rdzenie 5 liter „anjou” ma 2 głosy → dobrze |

Po tym przebiegu klucz głosu w `vote_closed` zmieniony na rdzenie 5-literowe słów (odmiany i warianty zapisu głosują razem). Czas: pełny arkusz K=5 na współdzielonym L40S (3 moje przebiegi naraz na 8 slotach) 2386 / 2265 s, tokeny 153k / 177k; zamknięte to 2–4× więcej tokenów niż zwykle i najdłuższe zadania arkusza (2024/11.1: 30.7k tok, 2025/5.1: 50.1k tok w 5 próbkach).

Test na sucho przez `server/exam_run.sh assets/mock-2023 T1 tuned 8872` (L40S, config z `--rozstrz-hint --vote-closed 5 --vote-adaptive`): OK, 37 odpowiedzi, 0 błędów, **996 s** (bazowy test na sucho T1 na L40S z 26.09: 324 s; część różnicy z równoległego testu T3 innego agenta — GPU 94%). Wynik przeniesiony do `runs/vote19/T1-tuned-dry` na L40S, oryginalny `runs/final/T1-tuned` przywrócony.

## 4. Bramka po prawdopodobieństwie odpowiedzi (logprobs)

Sonda (`logprobs=True, top_logprobs=5` na własnym serwerze T1, 2024/10 — zadanie, w którym Gemma dzieli głosy B 4/7, A 2/7, D 1/7; klucz A). llama-server zwraca logproby także dla tokenów myślenia (trzeba brać końcówkę). Dwie próbki (sonda przerwana — kolejka GPU):

| seed | końcówka myślenia | `<channel|>` | litera odpowiedzi | trafna |
|---|---|---|---|---|
| 900 | „The answer is A.” (A: 0.996) | 0.999 | **A: 1.000** | tak |
| 901 | „… seems to be B.” (B: 0.9998) | 0.561 | **B: 0.725** | nie |

Wniosek wstępny: decyzja zapada w myśleniu (litera w myśleniu ma p ≈ 1 w obu), ale końcowy token bywa mniej pewny przy złej odpowiedzi. Na n = 2 nie da się skalibrować progu P, a kalibracja wymagałaby dziesiątek próbek z logprobami (nie ma ich w starych przebiegach) — **bramka `--vote-gate P` nie wdrożona**. Zamiast niej `--vote-adaptive` (bramka zgodności): 2 próbki, przy zgodzie koniec, przy niezgodzie dobór do K — nie wymaga kalibracji; symulacja: ~93% zysku K=5 przy ~3.3 próbki; w realnym przebiegu 2026 7/9 zadań skończyło się na 2 próbkach.

## 5. Decyzja

- **T1: nie włączać.** Po powiększeniu puli oczekiwany zysk ~+1.0 pp (ścisły) / +0.75 pp (łagodny) — poniżej progu +1.5 pp z zadania i w granicach szumu seeda (σ ≈ 1.5–2 pp, raport 11). Efekt nie może zaszkodzić innym zadaniom (reguła A z raportu 11 dopuszcza „dowolny zysk”), ale kosztuje **~3× dłuższy T1** (na egzaminie szac. 10–15 min → 30+ min), a wynik musi pojawić się na ekranie w czasie naszego slotu. Status quo wygrywa. `final_configs.json`: T1 bez zmian (przez chwilę 07:35–07:40 flaga była dopisana i zsynchronizowana, cofnięte na laptopie i obu maszynach); opis opcji w `_comment_T1_vote`.
- **T3: nie włączać** (symulacja +0.6–1.2 pp, CI dla finałowego MIX szerokie; T3 i tak jest najdłuższy).
- **Jeśli zespół chce zaryzykować czas dla ~1 pp w T1:** dopisać `--vote-closed 5 --vote-adaptive` do T1 tuned harness (kod jest na obu maszynach, przetestowany na 3 arkuszach + mock przez `exam_run.sh`). Tańszy wariant `--vote-closed 3` daje wg symulacji tylko +0.6 pp.
- Możliwe usprawnienie (niezrobione): w trybie adaptacyjnym druga próbka startuje dopiero po pierwszej, a przy niezgodzie 3 kolejne dopiero po drugiej — 3 rundy myślenia szeregowo; start 2 próbek równolegle skróciłby ogon.
- Koszt: sędzia 0 $ (zamknięte oceniane automatycznie); GPU: własny serwer Gemma na L40S ~75 min (zatrzymany), krótko kolejka na H100.
