# 08 — Analiza wyników według typów zadań i zagadnień

Stan na sob 26.09, 20:00. Tabele generuje `eval/analyze.py` → `raports/08-wyniki-tabele.md`, a dane per zadanie są w `results/item_scores.csv`. Zbiór główny to arkusze CKE 2024 + 2025 (119 pkt; zadanie 2024/21 pominięte, bo sędzia API go nie ocenia). Otwarte i eseje biorę tylko z przebiegów ocenianych przez `gpt-6-luna` (H-E6), a zamknięte (ocena automatyczna) także ze starszych przebiegów.

**Jak liczono zagadnienia:**
- **Epoka** wynika z dat i stuleci w poleceniu, źródłach i kluczu CKE całej grupy zadań (przypisy z latami wydań są wycinane). Grupa bez dat dostaje epokę poprzedniej, bo arkusz CKE jest ułożony chronologicznie.
- **Zakres „Polska / powszechna”** to reguła na słowach kluczowych (np. Rzeczpospolita, Piast, sejm, PRL, zabory).
- Oba podziały są automatyczne. Pojedyncze zadania mogą być przypisane źle, ale rozkład (10 / 10 / 24 / 14 / 20 / 12 pkt na epoki) zgadza się z układem arkusza.

---

## 1. Najważniejsze wnioski

| # | Wniosek | Liczby (2024 + 2025) |
|---|---|---|
| 1 | **Esej to największa strata we wszystkich trackach.** 30 z 119 pkt to esej | T1 50–63%, T2 37–40%, T3 13%, małe modele 0–13% |
| 2 | **Historia Polski jest słabym punktem każdego modelu**, także przy tym samym typie zadania | Gemma: Polska 75% vs powszechna 97%; Qwen3.5-4B: 44% vs 90%; PLLuM + LoRA: 25% vs 63%. „Podaj”, Qwen-4B: 5/16 vs 7/8; „rozstrzygnij”: 8/19 vs 9/9 |
| 3 | **Myślenie podnosi zamknięte** (te same modele, ocena automatyczna) | Gemma +9 pp (dev 2023); Qwen3.5-4B +19 pp (2023), +12 pp (2024), +8 pp (2025). Wyjątek: Qwen3.5-2B z myśleniem 0% (urwane odpowiedzi) |
| 4 | **Spadek `t1final` względem starej konfiguracji T1 dotyczy historii Polski i eseju**, powszechna jest stabilna | Polska 66% vs 75%, esej 50% vs 63%, powszechna 93% vs 97% |
| 5 | **Obrazy nie są problemem dla Qwen3.5-4B**: zadania z obrazem wypadają lepiej niż tekstowe | 59% vs 38%. Tekstowe to częściej pytania o fakty z historii Polski |
| 6 | **HyDE pomaga małym modelom głównie na „podaj”**, a Qwen3.5-4B z myśleniem szkodzi | Bielik-1.5B „podaj”: 29% → 46%; Qwen-4B + HyDE: 48% → 42% |
| 7 | **PLLuM + LoRA (T2) jest słaby w dopasowaniu (`closed_match`) i w „rozstrzygnij”**, ale dobry w prawda/fałsz | match 17%, rozstrzygnij 25–29%, P/F 88% |
| 8 | **Najtrudniejsze zadania** (średnio 0–25% w T1–T3) to głównie „rozstrzygnij” i „podaj” z obrazem w nowożytności i 1914–1945 | 2024: 7, 14.1, 19.2, 25, 11.1, 12.1; 2025: 9.3, 14.1, 5.1, 22 |

Skład danych nie tłumaczy wniosku 2: w zbiorze SFT historia Polski to 55% przykładów, a w kompendium 72% notatek. Luka leży w wiedzy modeli bazowych (Gemma i Qwen trenowano głównie na danych globalnych).

---

## 2. Co z tego wynika dla następnych ruchów

1. **Kontekst z wiedzą o historii Polski jest najcelniejszą dźwignią wiedzy.** SFT nie dodaje wiedzy (H-T1), a myślenie jej nie tworzy. Model może ją dostać tylko z kontekstu (RAG), więc baza wiedzy powinna celować w historię Polski: oś czasu, postacie, pojęcia (§4).
2. **Esej:** kontekst faktów (kompendium: +5.6 pp na 12 tematach dla Qwen-4B), plan przed pisaniem i wybór tematu, który model zna (H-H8). Zysk z eseju działa na wszystkie tracki.
3. **Myślenie zostaje wszędzie, gdzie model je ma** (T1, T3). Dla T2 opłaca się **nauczyć bazę myśleć** (§3).
4. **T2:** do rundy 2 SFT dodać zadania typu dopasowanie i „rozstrzygnij” z uzasadnieniem (rozumowanie w danych, §3).

---

## 3. Pytanie 1: dataset z myśleniem zamiast pozbywania się myślenia

**Tak, ale nie dla każdego tracku tak samo.** Myślenie daje Gemmie ~+25 pp (56% → ~80% w starych pomiarach) i +8–19 pp na zamkniętych dla Qwen-4B. Nie wyłączamy go. Wyłączyliśmy je tylko w eseju T3, bo tam urywało się przy limicie i esej i tak powstawał awaryjnie.

| Track | Czy trenować na rozumowaniu | Dlaczego |
|---|---|---|
| **T2** (Gemma-4-12B pt / PLLuM-12B-base) | **tak, priorytet** | bazy nie myślą wcale, więc to największy potencjalny przyrost; przyrost liczy się względem gołej bazy |
| **T3** (Qwen3.5-4B) | ostrożnie, jako eksperyment | model już myśli natywnie. Krótkie, skupione rozumowania mogą ograniczyć urwania (6–14 na arkusz), ale mogą też zepsuć natywne myślenie (H-N16) |
| **T1** (Gemma-4-12B-it) | nie | myśli dobrze; LoRA na 80% modelu to ryzyko bez wyraźnego zysku |

**Jak zrobić dane:**
- **Uzasadnienie z kluczem** (styl STaR): nauczyciel dostaje zadanie, źródła i poprawną odpowiedź z klucza CKE. Pisze krótkie rozumowanie (150–400 słów), które do niej prowadzi: co mówi źródło, jaki fakt jest potrzebny, jak wykluczyć inne opcje. API nie zwraca ukrytego rozumowania modelu, więc prosimy o jawne uzasadnienie.
- **Esej:** „myślenie” to plan (teza, 3 elementy, 2–3 fakty na element) przed wypracowaniem.
- **Format:** Qwen — `<think>…</think>` (natywny); Gemma pt — kanał myśli Gemmy (`<|channel>thought … <channel|>`), żeby `llama.cpp` oddzielał rozumowanie od odpowiedzi; PLLuM — `<think>…</think>` (harness już je wycina).
- **Zadania z obrazami** (115 z CKE): API ich nie widzi. Uzasadnienia może pisać Gemma-4-12B-it z obrazem na H100 (lokalnie, bez kosztu API), a w tych danych klucz jest znany.

**Koszt przy 30.31 $ w API:**
- `gpt-6-luna` kosztowała dotąd ~0.0002 $ za zapytanie (5402 zapytań za 1.07 $). Przy dłuższych odpowiedziach szacunek to ~0.001 $, czyli **~2 $ za 1787 uzasadnień**.
- `gpt-6-sol` kosztuje ~0.011 $ za zapytanie, czyli ~20 $ za to samo. Za drogo przy pozostałych potrzebach.
- Propozycja: luna pisze wszystko, a sol albo Claude sprawdza próbkę ~50 (czy rozumowanie jest poprawne i nie tylko dopasowane do klucza). Zostaje ~25 $ na sędziego, kompendium i bazę wiedzy.

---

## 4. Pytanie 3: większa baza wiedzy, lepszy embedder, podejście hybrydowe

**Diagnoza z wcześniejszych pomiarów (H-H2):** RAG zawodził głównie przez wyszukiwanie, nie przez brak treści. Zapytanie z samego polecenia dawało trafność 28% (top-4), słowa kluczowe od luny 69%, a HyDE od luny 81% (górna granica). Własne HyDE Bielika-1.5B dawało 47%. Lepsza baza pomoże więc tylko razem z lepszym wyszukiwaniem.

| Pomysł | Ocena | Szczegóły |
|---|---|---|
| **Oś czasu historii Polski** (rok – wydarzenie – postacie – skutek, ~1500–2500 wpisów) | **tak, najwyższy priorytet** | krótkie, precyzyjne wpisy z nazwami i datami są idealne dla BM25; celuje w lukę z wniosku 2 i w błędy dat w esejach. Generacja lunką z wymagań CKE ~1 $; weryfikacja próbki |
| **Spis postaci** (~800: daty, funkcja, 3–5 kluczowych faktów) | **tak** | „Podaj imię i przydomek”, „podaj władcę”; wiele najtrudniejszych zadań to identyfikacja osoby lub dokumentu |
| **Pojęcia i nazwy historiograficzne** (~500: „nazwa stosowana w historiografii”) | **tak** | częsty typ polecenia CKE („Podaj stosowaną w historiografii nazwę…”) |
| Dogenerowanie kompendium (~300 notatek) | tak, niższy priorytet | pomaga esejowi; oś czasu i postacie dają więcej faktów na token |
| **Embedder** (dense) | sprawdzić, ale mieści się w limitach | kandydaci: `intfloat/multilingual-e5-small` (~0.12 GB), `sdadas/mmlw-retrieval-roberta-base` (~0.5 GB), `Qwen/Qwen3-Embedding-0.6B` (~0.6 GB w Q8). W T3 embedder musi być mniejszy od głównego modelu (np. IQ3_XXS 1.95 GB — mieści się); w T1/T2 suma z modelem i LoRA < 8.8 GB (Gemma pt 7.38 + mmproj 0.12 + e5-small ≈ 7.6 GB) |
| **Hybryda** BM25 + dense (RRF), opcjonalnie reranker | tak, jeśli dense doda ≥ 10 pp trafności | BM25 łapie nazwy i daty, dense parafrazy; łączenie RRF jest tanie |

**Jak to sprawdzić tanio, zanim cokolwiek pójdzie na GPU:** benchmark trafności wyszukiwania (CPU, `eval/rag_coverage.py` rozszerzony) na zadaniach „podaj / rozstrzygnij” i tematach esejów z 2023–2026. Porównujemy bazy (PolQA, kompendium, oś czasu, postacie), metody wyszukiwania (BM25, dense, hybryda) i zapytania (polecenie, HyDE modelu). Kryterium: trafność top-3. End-to-end na GPU robimy dopiero dla najlepszego wariantu.

---

## 5. Pytanie 2: decyzje o pomysłach z planu

| Pomysł | Decyzja | Hipoteza |
|---|---|---|
| Lepsze kompendium dla eseju | włączone do bazy wiedzy z §4 (po osi czasu i postaciach) | H-N12 |
| Wybór tematu eseju przez samoocenę modelu | **sprawdzić** (12 tematów + potem pełne arkusze) | H-H8 |
| Limit myślenia per typ | **odrzucone** | H-N13 |
| Szybkie zbiory kontrolne z esejów | **tak**, ale każdą zmianę eseju potwierdzamy potem na pełnych arkuszach (czy nie psuje reszty) | reguła w 05 |
| T3 poniżej 1.5 GB | **tak**: Qwen3.5-4B UD-IQ2_XXS (1.52 GB), jeśli IQ2_M utrzyma ≥ 40%, oraz Qwen3.5-2B z myśleniem i HyDE | H-N17, H-N18 |
