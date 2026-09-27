# 03 — Benchmarki: wyniki modeli bazowych

Źródła: strona benchmarku (stan na 22–25.09.2026), slajdy `benchmarks&examples.pdf`, pliki `*.reviews.json`. Metodyka i prompty — raport 02.

Ważne przy czytaniu:
- **Tekst = /55 pkt** (34 zadania, opisy zamiast obrazków), **Obrazy = /60 pkt** (37 zadań, oryginalne strony). Procentów z różnych trybów nie da się wprost porównywać.
- Oceniał AI-sędzia według klucza CKE (nie ma to statusu oficjalnej oceny maturalnej).
- Przebiegi mają różne ustawienia (v0.1 greedy ze wspólnym limitem tokenów vs v0.2 z osobnym budżetem myślenia i samplingiem), więc to **nie jest kontrolowane porównanie** samego rozmiaru modelu.
- Arkusz 2023 jest publiczny — mógł być w danych treningowych modeli.
- „Rozmiar BF16” to surowe wagi 16-bit (parametry × 2 bajty). Limit konkursu to **8 GB na dysku**, więc modele powyżej ~4B trzeba kwantyzować.

---

## 1. Małe modele tekstowe (wersja tekstowa, /55)

| Model | Parametry | BF16 | **Wynik** | Zamknięte /11 | Otwarte /29 | Esej /15 | Ustawienia |
|---|---|---|---|---|---|---|---|
| gemma-3-1b-it | 1.0B | 2.0 GB | 14.5% (8) | 4 | 4 | 0 | v0.1 greedy |
| **Bielik-1.5B-v3.0-Instruct** | 1.6B | 3.2 GB | **27.3%** (15) | 5 | 9 | 1 | v0.1 greedy |
| Qwen3-1.7B | 1.7B | 3.4 GB | 23.6% (13) | 4 | 8 | 1 | v0.2 thinking, T=0.6 |
| SmolLM3-3B | 3.1B | 6.2 GB | 18.2% (10) | 5 | 5 | 0 | v0.2 thinking, T=0.6 |
| Llama-3.2-3B-Instruct | 3.2B | 6.4 GB | 18.2% (10) | 3 | 7 | 0 | v0.2 sampling |
| Phi-4-mini-instruct | 3.8B | 7.7 GB | 18.2% (10) | 5 | 5 | 0 | v0.1 greedy |
| **Qwen3-4B-Instruct-2507** | 4.0B | 8.04 GB (!) | **40.0%** (22) | 7 | 12 | 3 | v0.1 greedy |
| **Bielik-4.5B-v3.0-Instruct** | 4.8B | 9.5 GB (!) | **41.8%** (23) | 6 | 15 | 2 | v0.1 greedy |

(!) — w BF16 przekracza 8 GB, trzeba skwantyzować (np. Q8 ≈ 4–5 GB).

## 2. Małe modele multimodalne (≤ 4B)

| Model | Parametry | **Tekst /55** | **Obrazy /60** | Zamkn. T / O | Otwarte T / O | Esej T / O |
|---|---|---|---|---|---|---|
| Qwen3-VL-2B-Instruct | 2.1B | 10.9% | 15.0% | 3 / 5 | 3 / 4 | 0 / 0 |
| Qwen3-VL-2B-Thinking | 2.1B | 12.7% | 6.7% | 3 / 1 | 4 / 3 | 0 / 0 |
| **gemma-3-4b-it** | 4.3B | **36.4%** | 26.7% | **10** / 4 | 7 / 9 | 3 / 3 |
| PLLuM-4B-instruct-2512 | 4.3B | 30.9% | 21.7% | 5 / 3 | 12 / 9 | 0 / 1 |

Uwagi: Qwen3-VL-2B-Thinking w większości zadań nie zdążył skończyć myślenia (brak odpowiedzi = 0). Gemma 3 4B ma najlepsze zamknięte (10/11), ale słabe otwarte.

## 3. Większe modele multimodalne (8B+) — trzeba kwantyzować do ≤ 8 GB

| Model | Parametry | BF16 | Q8 | Q4 | **Tekst /55** | **Obrazy /60** | Esej (obrazy) |
|---|---|---|---|---|---|---|---|
| InternVL3.5-8B | 8.5B | 17.1 GB | 8.5 GB | 4.3 GB | — | 36.7% | 1/15 |
| **Qwen3.5-9B** | 9.7B | 19.3 GB | 9.7 GB | 4.8 GB | — | **60.0%** | 8/15 |
| LLaVA-Bielik-11B-v2.6 | 11.6B | 23.2 GB | 11.6 GB | 5.8 GB | **52.7%** | 23.3% | 0/15 |
| **gemma-4-12B-it** | 12.0B | 23.9 GB | 12.0 GB | 6.0 GB | — | **76.7%** | **12/15** |
| LLaVA-PLLuM-12B | 12.7B | 25.4 GB | 12.7 GB | 6.4 GB | 34.5% | 23.3% | 0/15 |
| Ministral-3-14B-Instruct-2512 | 14.0B | 27.9 GB | 14.0 GB | 7.0 GB | **60.0%** | 48.3% | 3/15 |

Rozmiary Q8/Q4 to idealne szacunki z prezentacji (same wagi). Realny plik GGUF Q4_K_M jest ~20% większy (np. Gemma 4 12B ≈ 7–7.5 GB, Ministral 14B ≈ 8+ GB — za dużo, potrzebny Q3). Po kwantyzacji trzeba **ponownie zmierzyć wynik**.

Szczegóły trzech najlepszych:
- **Gemma 4 12B (obrazy)**: 46/60 — zamknięte 10/11, otwarte 24/34, esej 12/15; na wspólnym zbiorze 34 zadań 44/55 (80%). Tryb myślenia, T=1.0.
- **Qwen3.5-9B (obrazy)**: 36/60 — zamknięte 5/11, otwarte 23/34, esej 8/15; 34/55 na wspólnym zbiorze. 3 zadania bez odpowiedzi końcowej (limit myślenia).
- **Ministral 14B (tekst)**: 33/55 — otwarte 25/29 (najlepsze), ale zamknięte 5/11 i esej 3/15.

## 4. Punkt odniesienia

**GPT Astra** (gpt-6-astra, agent referencyjny, bez limitu rozmiaru): **60/60** (obrazy) i **55/55** (tekst). Pokazuje, że arkusz jest w pełni rozwiązywalny, a sędzia potrafi przyznać maksimum.

## 5. Trudność zadań (średni % punktów w 25 przebiegach małych i średnich modeli)

Najłatwiejsze (warto nie tracić): 1 — neolit (88%), 11.1 — nadużycie liberum veto (80%), 11.2 — zniesienie liberum veto (76%), 13.2 — datowanie bitwy (72%), 4.2 — plan Elbląga (68%), 6 — dwie opinie o Łokietku (64%).

Najtrudniejsze (tu jest największy zapas):

| Zadanie | Pkt | Śr. wynik | Temat |
|---|---|---|---|
| 20 | 1 | 0% | Saara i Nadrenia (traktat wersalski) |
| 8 | 2 | 0% | rycina reformacyjna (tylko obrazy) |
| 24 | 1 | 4% | dwie kampanie propagandowe PRL |
| 13.1 | 1 | 8% | identyfikacja planu bitwy |
| **26** | **15** | **11.7%** | **esej** |
| 5.2 | 1 | 16% | roszczenia Edwarda III do Francji (genealogia) |
| 22 | 1 | 16% | sojusze po obu stronach żelaznej kurtyny |
| 9.3, 25.1, 25.2 | 1 | 20% | Wazowie/Jagiellonowie; Breżniew; Jaruzelski i stan wojenny |
| 9.1, 12 | 1 | 24% | unia personalna Wazów; trzy stany czy trzy władze |
| 18 | 3 | 25% | karykatura „Duch roku ’76” |
| 19 | 2 | 26% | P/F o okresie międzywojennym |

**Esej to 15 z 55 pkt (27%)**, a małe modele biorą w nim średnio ~12%. Poza Gemmą 4 12B (12/15) i Qwen3.5-9B (8/15) żaden model nie przekroczył 3/15. Typowe błędy: kilka tematów naraz, władcy spoza epoki, zmyślone daty, < 300 słów, pętle powtórzeń. To najtańszy do poprawienia obszar (fine-tuning na dobrych esejach + szablon eseju w harnessie).

Druga grupa do poprawy to **historia XX wieku i PRL** (zadania 20–25) — wszystkie modele wypadają tu słabo.

## 6. Koszt inferencji (Modal, 1 pełny egzamin)

| Model | GPU | Tekst $ | Obrazy $ |
|---|---|---|---|
| Gemma 3 1B / Bielik 1.5B / Llama 3.2 3B | L4 | 0.08–0.18 | — |
| Qwen3 4B / Bielik 4.5B / PLLuM 4B / Gemma 3 4B | L4 | 0.15–0.21 | 0.16–0.18 |
| Qwen3-VL-2B-Thinking | L4 | 2.37 | 2.89 |
| LLaVA-Bielik 11B / LLaVA-PLLuM 12B / Ministral 14B | A100 | 0.64–1.06 | 0.76–0.84 |
| InternVL 8B / Gemma 4 12B / Qwen3.5 9B | A100 | — | 2.33 / 4.56 / 4.88 |

Modele z myśleniem są 5–20× droższe i wolniejsze (Gemma 4 12B: ~73 GPU-min na arkusz przy 14 tok/s w transformers BF16). Na scenie jest „kilka minut” na cały egzamin, więc potrzebny jest szybki serwer (vLLM / llama.cpp na mocnym GPU, równoległe zapytania, rozsądny budżet myślenia).

## 7. Szacunki fine-tuningu (ze strony; 6 mln przetworzonych tokenów = 2 mln × 3 epoki, A100 80GB ≈ 2.5 $/h, LoRA/QLoRA)

| Model | Czas | Koszt |
|---|---|---|
| Gemma 3 1B | 0.3–1.3 h | 1–4 $ |
| Bielik 1.5B / Qwen3 1.7B | 0.5–2.3 h | 1–6 $ |
| Qwen3 4B / Gemma 3 4B / Bielik 4.5B / PLLuM 4B | 1.3–6 h | 3–15 $ |
| InternVL 8B / Qwen3.5 9B | 2.7–12 h | 7–30 $ |
| Gemma 4 12B / LLaVA-* 11–12B | 3.7–16 h | 9–40 $ |
| Ministral 14B | 4.7–18.7 h | 12–47 $ |

To zgrubne szacunki bez pomiarów. Zalecenie autorki: zacząć od modeli 1–4.5B z LoRA/QLoRA, przed wydaniem pieniędzy zmierzyć 50–100 kroków. Na H100 czasy są ~2× krótsze.

## 8. Nowsze modele, których benchmark nie obejmuje

Sprawdzone na Hugging Face 26.09.2026 — trzeba je zmierzyć samodzielnie (plan w raporcie 05):

| Model | Rozmiar GGUF | Dlaczego ważny |
|---|---|---|
| Gemma-4-12B-it **QAT q4_0** (oficjalny, Google) | 6.98 GB + mmproj 0.18 GB | kwantyzacja trenowana przez Google — prawdopodobnie jakość bliska BF16 (76.7% w benchmarku) |
| Qwen3.5-0.8B / 2B / 4B (+ wersje `-Base`) | Q4_K_M: 0.53 / 1.28 / 2.74 GB | nowa generacja małych modeli, 201 języków, natywne widzenie — kandydaci do T3 |
| Bielik-11B-v3.0-Instruct, Bielik-PL-11B-v3.0-Instruct, Bielik-Minitron-7B-v3.0 | Q5_K_M 7.91 GB / — / Q8_0 7.95 GB | nowsze polskie modele (benchmark testował tylko Bielik v3 1.5B/4.5B i LLaVA-Bielik v2.6) |
| PLLuM-12B-instruct-2512 / PLLuM-4B-instruct-2512 (tekst) | Q4_K_M ~7.3 GB / — | polskie modele z grudnia 2025 |
| Wersje `-Base`: Gemma-4-12B, Qwen3.5-9B, PLLuM-12B-2512, Bielik-11B-v3 | — | kandydaci do wariantu T2-B1 |

Nie mieszczą się w 8 GB nawet w 2 bitach: Gemma-4-31B, Gemma-4-26B-A4B, Qwen3.6-27B, Qwen3.5/3.6-35B-A3B.

## 9. Co z tego wynika dla trzech tracków

| Track | Obserwacja z benchmarku |
|---|---|
| **1. Najlepszy wynik** | Gemma 4 12B w Q4 (~7 GB) mieści się w limicie i jako jedyna ma ~77–80% bez treningu, w tym 12/15 z eseju. Qwen3.5-9B (Q5/Q6) to drugi kandydat. Harness (RAG + format odpowiedzi + budżet myślenia) może dołożyć punkty w zadaniach 20–25 i w formatowaniu. Trzeba sprawdzić, ile traci po kwantyzacji i czy zdąży w czasie na scenie. |
| **2. Największy postęp** | Liczy się różnica względem **najlepszego pojedynczego modelu** w pipeline. Checkpoint `-Base` / `-pt` wolno zgłosić jako bazę (H-R2). Najwięcej zapasu mają słabe bazy z dobrym polskim: Bielik 1.5B (27%), Qwen3-1.7B (24%), PLLuM 4B (31%), Gemma 3 4B (36%) oraz gołe `-Base` (PLLuM-12B-base 0%). Esej (~15 pkt, ok. 25% arkusza; H-R9) daje najwięcej punktów. Mocna baza (Gemma 4) ma mały zapas. Embedder, reranker, OCR i enkoder obrazów nie podnoszą bazy (H-R7). |
| **3. Najmniejszy ≥ 35%** | Bez treningu próg 35% przekraczają dopiero modele ~4B (Gemma 3 4B 36.4%, Qwen3-4B 40%, Bielik 4.5B 41.8%). Najbliżej z mniejszych są Bielik 1.5B (27.3%) i Qwen3-1.7B (23.6%) — 35% z 55 to 19.25, czyli trzeba 20 pkt: Bielikowi brakuje 5, Qwenowi 7. Realny cel: model 1–2B w Q4/Q5 (~1–1.5 GB) + fine-tuning (esej, formaty) + RAG. Rozmiar liczony **w GB na dysku** (potwierdzone), a w pipeline liczy się **tylko największy** model. Embedder, reranker, OCR i enkoder obrazów muszą być mniejsze od głównego i zmieścić się z nim w sumie < 8.8 GB (H-R7). Przy modelach 1–4B suma jest daleko pod limitem; `mmproj` mniejszy od LLM nie podnosi rozmiaru w T3 (H-R5). Część zadań finału ma obrazy (H-R9). |

## 10. Nasze wyniki (noc 25/26.09)

Runtime: llama.cpp (GGUF, jak na egzaminie), prompt organizatorów, ustawienia producenta. Zamknięte oceniane automatycznie, otwarte i eseje przez `gpt-5.4-mini` (92% zgodności z oficjalnym sędzią, raport 07 H-E2). Arkusze 2024–2026 są w formacie finału: tekst osobno, obrazy osobno; modele tekstowe dostają sam tekst. Pełna tabela: `results/report.md`.

| Model | GB | DEV-2023 | 2024 | 2025 | 2026 | Track |
|---|---|---|---|---|---|---|
| Gemma-4-12B QAT (myślenie) | 7.16 | 81.7% (obrazy) / 80.0% (tekst) | **81.7%** | **81.7%** | **76.7%** | T1 |
| Bielik-11B-v3 Q5 (tekst) | 7.91 | **87.3%** (tekst) | 63.3% | 60.0% | 65.0% | T1 (zespół) |
| Qwen3.5-9B Q5 (myślenie) | 7.50 | 51.7% (obrazy) / 58.2% | 70.0% | 65.0% | — | T1 |
| PLLuM-12B-instruct Q4 | 7.48 | 50.9% | — | — | — | — |
| Qwen3.5-4B Q4 | 2.74 (+0.67) | 46.7% (obrazy) / 29.1% | 46.7% | 38.3% | — | **T3** |
| Bielik-1.5B Q8 | 1.70 | 29.1% | 26.7% | 28.3% | 18.3% | T3 |
| Qwen3.5-2B Q4 | 1.28 (+0.67) | 18.3% (obrazy) / 25.5% | 20.0% | 25.0% | — | T3 |
| Qwen3.5-0.8B Q4 | 0.53 | 6.7% / 9.1% | — | — | — | T3 |
| Qwen3.5-2B-Base Q4 (goły) | 1.27 | 12.7% | — | — | — | T2 |
| PLLuM-12B-base Q4 (goły) | 7.48 | **0.0%** | — | — | — | **T2** |

„—” = przebieg niewykonany albo jeszcze nieoceniony.

Wnioski:
- **T1:** Gemma-4-12B QAT to stabilne ~80%. Bielik-11B jest mocniejszy na wiedzy tekstowej, a wyrocznia obu modeli daje +3–7 pkt na 60 — cel dla selektora.
- **T3:** Qwen3.5-4B (2.74 GB) już przekracza 35%; celem jest zejście do 2B / 1.5B dzięki harnessowi i SFT (brakuje ~10–15 pp).
- **T2:** PLLuM-12B-base (goły 0%) jest idealną bazą pod postęp; wersja instruct tej rodziny osiąga 51%, a lepszy SFT + harness może dać więcej.
- **Myślenie** pomaga Gemmie o +24 pp i Qwen3.5-4B o +16 pp, ale psuje Qwen3.5-2B (niekończące się rozumowanie).
