# 07 — Założenia i hipotezy do weryfikacji

Lista rzeczy, które przyjmujemy w planie (raport 05), a które trzeba potwierdzić pytaniem do organizatorów albo eksperymentem. Odznaczaj `- [x]` i dopisuj wynik w linii „Wynik”.

**Priorytety:**
- **P0** — blokuje decyzje; wyjaśnić do sob ~12:00,
- **P1** — potrzebne do bramek G2/G3 (sob 17:00 / 23:00),
- **P2** — optymalizacje.

**Rodzaj:** **[O]** pytanie do organizatorów, **[E]** eksperyment, **[M]** obserwacja (leaderboard, przebiegi próbne).

---

## Już potwierdzone

- [x] **H-R0a** Track 3 mierzy **rozmiar w GB na dysku**; przy wielu modelach liczy się tylko największy. *(Twoja informacja)*
- [x] **H-R0b** Pytania otwarte i esej ocenia **LLM-sędzia ze szczegółowymi kryteriami jak w CKE**. *(Twoja informacja)*
- [x] **H-R0c** Obrazy i tekst przychodzą **osobno**; modele tekstowe mogą odpowiedzieć na podstawie samego tekstu. *(Twoja informacja)*
- [x] **H-R0d** Model może działać na maszynie w chmurze; zakaz dotyczy internetu i zewnętrznych API AI. *(FAQ na slajdach)*
- [x] **H-R0e** Baza wiedzy RAG nie wlicza się do limitu; adapter LoRA nie wlicza się do limitu 8 GB. *(FAQ na slajdach)*
- [x] **H-R0f** Wszystkie rozważane modele bazowe (Gemma 4, Qwen3.5, Bielik v3, PLLuM-2512) mają licencję Apache 2.0. *(karty na HF)*
- [x] **H-M0** Gemma-4-12B-it QAT q4_0 (6.98 GB + mmproj 0.18 GB) mieści się w limicie; modele ≥ 26B nie mieszczą się nawet w 2 bitach. *(rozmiary plików na HF)*

---

## A. Zasady i organizacja

- [x] **H-R1 (P0) [O]** Zespół może zgłosić **osobne rozwiązania do różnych tracków** (np. mały model do T3 i duży do T1).
  - Wpływ: scenariusz S1 (trzy linie) albo S2 (jedno rozwiązanie) — drzewo w 05 §2.
  - Wynik: **TAK — trzy osobne rozwiązania** (odpowiedź organizatorów, 26.09 ~01:45). Obowiązuje scenariusz S1.
- [x] **H-R2 (P0) [O]** Jako model bazowy wolno zgłosić **checkpoint pretrenowany (`-Base` / `-pt`)**, a nie tylko `-Instruct`.
  - Wpływ: wariant T2-B1 (największy potencjalny postęp) — 05 §5.
  - Wynik: **TAK** (organizatorzy, 26.09 ~15:30). Checkpoint pretrenowany (`-Base` / `-pt`) wolno zgłosić jako model bazowy. Wariant T2-B1 jest dozwolony; zostaje wybór, która baza daje największy skok (H-M7, H-M8).
- [x] **H-R3 (P0) [O]** Wynik bazowy mierzy się na **gołym modelu bez harnessu**, więc zysk z harnessu wlicza się do postępu.
  - Wpływ: czy RAG / esej sekcyjny / głosowanie podnoszą wynik w T2.
  - Wynik: **TAK — baza bez harnessu** (odpowiedź organizatorów).
- [x] **H-R4 (P1) [O]** Postęp liczony jest jako **różnica w punktach procentowych**, a nie zysk względny.
  - Wpływ: przy zysku względnym opłaca się ekstremalnie słaba baza (nawet mały model).
  - Wynik: **tak — różnica w pp** (organizatorzy).
- [x] **H-R5 (P0) [O]** Plik **mmproj wlicza się** do rozmiaru modelu (T3 i limit 8 GB).
  - Wpływ: Qwen3.5-9B Q6_K + mmproj = 8.38 GB (za dużo → Q5_K_M); w T3 obrazy przez OCR zamiast mmproj.
  - Wynik: **nie — mmproj to osobny plik, który sam musi mieć < 8 GB** (organizatorzy). W T3 liczy się największy plik modelu, a mmproj (0.2–0.9 GB) jest mniejszy od LLM, więc **natywne widzenie Qwen3.5 nie podnosi rozmiaru liczonego w T3**.
  - **Doprecyzowanie (H-R7, 26.09 ~15:30):** brak wpływu na rozmiar w T3 dotyczy tylko miary „największy plik”. Enkoder obrazów wchodzi do sumy **< 8.8 GB** razem z głównym modelem. Qwen3.5-9B Q6_K (7.46 GB) + mmproj (0.92 GB) = 8.38 GB mieści się w kopercie, ale zostawia 0.42 GB na LoRA i resztę. Z widzeniem i zapasem zostaje Q5_K_M (6.58 + 0.92 = 7.50 GB, zapas 1.30 GB).
- [x] **H-R6 (P1) [O]** Adapter LoRA **nie wlicza się także w T3**.
  - Wpływ: w T3 można mocno kwantyzować bazę i trzymać LoRA w BF16 bez scalania.
  - Wynik: **tak** (organizatorzy). Otwiera strategię H-T11.
  - **Korekta (oficjalny komunikat, 26.09 ~14:30):** baza ze swoją kwantyzacją ≤ 8 GB, **po fine-tuningu łącznie ≤ 8.8 GB (8 GB + 10%)**. Techniki „pompujące” model (podnoszenie precyzji, kopie, głosowanie) są niedozwolone. Adapter LoRA **wlicza się** więc w tolerancję 10%.
  - Wpływ na nasz plan: **mały.**
    - T1: Gemma QAT 6.98 GB + mmproj 0.18 GB + LoRA + modele pomocnicze < 8.8 GB (zostaje 1.64 GB; H-R7).
    - T2: PLLuM-12B-base 7.48 GB / Gemma-4-12B pt 7.38 GB + mmproj + LoRA + modele pomocnicze < 8.8 GB (zostaje 1.32 GB / ~1.24 GB).
    - T3: LoRA ≤ 10% bazy (np. ≤ 0.27 GB dla Qwen3.5-4B Q4). Zwykła LoRA r=16–64 (20–150 MB) się mieści; strategię H-T11 ograniczamy do adaptera ≤ 10%. Suma i tak jest daleko pod 8.8 GB — w T3 wiąże „mniejszy od głównego” (H-R7).
    - Zespół modeli i tak odrzucony (H-H9).
- [x] **H-R7 (P1) [O]** Embedder, reranker, OCR i enkoder obrazów to „modele” w rozumieniu zasady „liczy się największy” (w T3 muszą być mniejsze od głównego), ale nie wpływają na bazę w T2 (same nie zdają egzaminu).
  - Wynik: **TAK** (organizatorzy, 26.09 ~15:30), z dodatkowym limitem sumy.
    - W T3 liczy się największy plik, więc każdy z nich musi być mniejszy od głównego.
    - W T2 nie podnoszą bazy: same nie zdają egzaminu, więc postęp liczy się od gołego modelu głównego.
    - **Łącznie z głównym modelem muszą mieć < 8.8 GB.** To ta sama koperta co po fine-tuningu (H-R6); LoRA też jest w niej. Baza RAG (teksty, indeks BM25) nadal się nie wlicza.
    - Zapas po odjęciu głównego modelu i enkodera obrazów:
      - T1 Gemma QAT 6.98 + mmproj 0.18 → **1.64 GB** na LoRA, embedder, reranker i OCR. Mały embedder (~0.24 GB) się mieści; duży (0.9–3 GB) nie.
      - T2 PLLuM-12B-base 7.48 → **1.32 GB**. Gemma-4-12B pt 7.38 + mmproj ~0.18 → **~1.24 GB**. Bezpieczny wybór to BM25 (0 GB) i Tesseract (~0.015 GB).
      - Qwen3.5-9B Q6_K 7.46 + mmproj 0.92 = 8.38 → **0.42 GB**. Z widzeniem i miejscem na LoRA zostaje Q5_K_M (zapas 1.30 GB).
      - T3 (Qwen3.5-4B Q4 2.74 + mmproj 0.67 = 3.41) jest daleko pod 8.8 GB. Wiąże zasada „mniejszy od głównego”: przy Qwen3.5-2B Q4 (1.28 GB) embedder musi być od niego mniejszy, a mmproj 0.67 GB nie podnosi rozmiaru w T3.
- [x] **H-R8 (P1) [O]** 8 GB = 8·10⁹ bajtów (GB, nie GiB), liczony jako suma plików wag w formie uruchamianej.
  - Wpływ: Bielik-11B-v3 Q5_K_M (7.91 GB) i Minitron Q8_0 (7.95 GB) są tuż pod limitem.
  - Wynik: **tak** (organizatorzy). Bielik-11B Q5_K_M, Minitron Q8_0 i Gemma-4-12B QAT (6.98 GB) mieszczą się.
- [x] **H-R9 (P1) [O/M]** Finałowy arkusz ma strukturę zbliżoną do CKE: podobne typy zadań, esej ~15 pkt (~25% punktów), część zadań z obrazami.
  - Wpływ: waga eseju w planie T2/T3, budżet punktów T3.
  - Wynik: **TAK** (organizatorzy, 26.09 ~15:30). Finał ma układ jak arkusz CKE: te same typy zadań, esej około **15 pkt (~25% punktów)**, część zadań z obrazami. Waga eseju w T2/T3 i budżet punktów T3 zostają; zbiory DEV z arkuszy CKE są właściwym przybliżeniem finału.
- [x] **H-R10 (P0) [O]** Format pytań: obrazy jako osobne pliki (wycinki), znany schemat `pytania-FORMAT.json`, pole `type` dostępne w pytaniu.
  - Wpływ: adapter harnessu, klasyfikacja typu, format DEV.
  - Wynik: **znany** (przewodnik, raport 01 §5a). `exam.json` z polami `id`, `group`, `max_points`, `question`, `source_text`, `images`, `answer_format`; obrazy jako wycięte PNG. Pola `type` nie ma, ale typ jednoznacznie wynika z `answer_format`.
- [ ] **H-R11 (P1) [M]** Pytania z puli próbnej są stylem podobne do finału (a nie np. wyłącznie generowane z Wikipedii).
  - Wpływ: jak bardzo ufać wynikom przebiegów próbnych.
  - Wynik:
- [x] **H-R12 (P0) [O]** Interfejs skryptu egzaminacyjnego (endpoint zgodny z OpenAI? funkcja?) oraz to, czy pyta **sekwencyjnie** i z jakim limitem czasu na pytanie.
  - Wpływ: głosowanie, best-of-N i zespół modeli mogą nie zmieścić się w czasie; tryb szybki.
  - Wynik: **brak skryptu na żywo.** Pobieramy paczkę, generujemy `answers.json` offline i wgrywamy plik. Nie ma limitu czasu na pytanie; liczy się tylko to, żeby zdążyć przed swoją prezentacją.
- [x] **H-R13 (P1) [O]** Przebiegi egzaminu bazowego i wytrenowanego robimy sami skryptem w nd od 11:00 (a nie organizatorzy na swojej stacji).
  - Wynik: **tak**, każde rozwiązanie (także bazowe) wgrywamy jako osobny `answers.json` z własną nazwą rozwiązania.

## B. Ewaluacja i sędzia

- [ ] **H-E1 (P1) [M]** Sędzia finałowy zachowuje się jak sędzia z benchmarku: kara za sprzeczności i asekurację, wymaga obu elementów „rozstrzygnij + uzasadnij”, esej wg kryteriów CKE.
  - Jak sprawdzić: **oddać próbny egzamin** (`history-2023-mock-v1`) kilkoma wariantami i porównać ocenę organizatorów z oceną `gpt-6-sol` dla tych samych odpowiedzi.
  - Wynik:
- [x] **H-E2 (P0) [E]** Nasz lokalny sędzia (Gemini/GPT + klucz CKE) osiąga **≥ 85% zgodności per zadanie** z ocenami z benchmarku i ±2 pkt na sumie przebiegu.
  - Jak sprawdzić: ponowna ocena odpowiedzi z `CALIB`.
  - Wynik: na 104 otwartych odpowiedziach (4 przebiegi DEV-2023):
    - **`gpt-5.4-mini`** (reasoning low): **92.3% zgodności**, sumy przebiegów różnią się od oficjalnych o 0 / +1 / +2 / 0 pkt, koszt ~0.0017 $ za zadanie — **wybrany sędzia** (`eval/judge_openai.py`);
    - `gpt-4.1-mini`: 85.6% zgodności, ale zawyża sumy o +4–6 pkt.
    - **Forgehand (26.09, 14:00):**
      - **`gpt-6-sol`: 98.1% zgodności**, sumy 0 / +1 / +1 / 0 pkt — najlepszy sędzia, do esejów i decyzji;
      - **`gpt-6-luna`: 95.2%**, sumy +2 / 0 / +1 / −1 — tańszy sędzia do masowej oceny.

      Uruchomienie: `eval/judge_openai.py --key-env FORGEHAND_API_KEY --base-url https://app.forgehand.app/api/v1/teams/01a0da5f-05f4-700d-a554-4c8f829182f1/llm/v1 --model gpt-6-luna`.
- [ ] **H-E3 (P1) [E]** Wyniki na arkuszach 2024–2026 przewidują finał lepiej niż 2023.
  - Jak sprawdzić: porównanie rankingów modeli na 2023 vs 2024–2026 i vs przebiegi próbne.
  - Wynik:
- [x] **H-E4 (P0) [E]** Różnica ≥ 2 pp na połączonym DEV (~120 pkt, 2 seedy) jest powyżej szumu.
  - Jak sprawdzić: 3–5 powtórzeń tej samej konfiguracji (sampling + sędzia); odchylenie standardowe.
  - Wynik: **na jednym arkuszu nie.**
    - Qwen3.5-2B na 3 seedach (DEV-2023 tekst): 25.5 / 21.8 / 18.2%, rozrzut 7.3 pp.
    - Gemma-4-12B na 2 seedach: 80.0 / 80.0%, ale esej 15 vs 11 i otwarte 22 vs 25 — duży szum na pozycjach, stabilna suma.
    - **Reguła:** decyzje dla małych modeli liczymy na ≥ 2 arkuszach × ≥ 2 seedach, a różnice < 4 pp traktujemy jako szum.
- [ ] **H-E5 (P2) [E]** Arkusz 2023 jest skażony (modele znają go z pretreningu), więc zawyża wyniki.
  - Jak sprawdzić: wynik 2023 vs 2026 dla tych samych modeli; test dopełniania dosłownych fragmentów arkusza.
  - Wynik:
- [x] **H-E6 (P0) [E]** Oceny różnych sędziów (stary `gpt-5.4-mini` / Claude sprzed sob 13:40 vs `gpt-6-luna`) są porównywalne.
  - Wynik (sob 19:35): **nie.** Te same odpowiedzi Gemmy (przebiegi `__s42`) oceniła ponownie luna (kopie `__s42L`):

    | Arkusz | stary sędzia | luna |
    |---|---|---|
    | 2024 | 81.7% | 76.3% |
    | 2025 | 81.7% | 78.3% |
    | 2026 | 76.7% | 75.0% |
    | mock 2023 | 81.7% | 76.7% |

    Stary sędzia był łaskawszy o ~4 pp, najbardziej przy esejach (14→11, 13→10). **Reguła:** porównujemy tylko wyniki jednego sędziego. Gdy porównanie ze starym przebiegiem jest potrzebne, oceniamy go ponownie lunką (~0.06 $ za arkusz).
- [x] **H-E7 (P1) [E]** Każde zadanie da się ocenić przez API sędziego.
  - Wynik: **nie.** Zadanie 2024/21 (kadr z wiecu NSDAP) Azure odrzuca filtrem treści przy każdym modelu (`luna`, `sol`). Wcześniej sędzia ponawiał je 6 razy (~2 min straty na przebieg), a raport pokazywał „≥ X/60”. Teraz pozycja dostaje `filtered` i wypada z mianownika (2024 liczony z 59 pkt).

## C. Modele i kwantyzacja

- [x] **H-M1 (P1) [E]** Gemma-4-12B-it QAT q4_0 traci ≤ 2 pp względem BF16.
  - Wynik: **nie traci.** QAT q4_0 w llama.cpp: 81.7% na DEV-2023 z obrazami, a BF16 w benchmarku organizatorów miało 76.7% (inne ustawienia, ta sama rodzina promptów).
- [x] **H-M2 (P0) [E]** Gemma-4-12B-it jest najlepszym pojedynczym modelem ≤ 8 GB na naszym DEV (vs Qwen3.5-9B, Bielik-11B-v3, PLLuM-12B-2512, Ministral-14B Q3).
  - Wynik: **tak na arkuszach w formacie finału:**

    | Model | 2024 | 2025 | 2026 |
    |---|---|---|---|
    | Gemma-4-12B QAT | 81.7% | 81.7% | 76.7% |
    | Qwen3.5-9B Q5 | 70.0% | 65.0% | — |
    | Bielik-11B-v3 Q5 (sam tekst) | 63.3% | 60.0% | 65.0% |

    Na DEV-2023 z opisami obrazków wygrywa Bielik (87.3% vs 80.0%). Ministral nie testowany.
- [x] **H-M3 (P1) [E]** Polskie modele (Bielik-11B-v3, PLLuM-12B) mają lepszą wiedzę o historii Polski (wyższe wyniki na otwartych faktograficznych), choć słabsze rozumowanie i esej.
  - Wpływ: sens zespołu specjalistów w T1.
  - Wynik: **tak dla Bielika-11B-v3:**
    - DEV-2023 tekst: otwarte 28/29, zamknięte 9/11;
    - zamknięte 10/12 (2025) i 10/10 (2026), lepiej niż Gemma;
    - traci na zadaniach z obrazami (model tekstowy) i na eseju (8–11/15 vs 9–15/15);
    - wyrocznia Gemma+Bielik (lepsza z dwóch odpowiedzi): 52 / 51 / 53 z 60 zamiast 49 / 49 / 46 samej Gemmy.

    PLLuM-12B-instruct wyraźnie słabszy (50.9% na DEV-2023).
- [ ] **H-M4 (P0) [E]** Qwen3.5-2B (a może 0.8B) z harnessem i SFT osiąga **≥ 40% na DEV** w formacie finału.
  - Wynik (bez harnessu i SFT):

    | Model | Wyniki | Rozmiar |
    |---|---|---|
    | Qwen3.5-2B | 18–25% | 1.28 GB |
    | Bielik-1.5B | 18–29% | 1.70 GB |
    | Qwen3.5-0.8B | 7–9% | 0.53 GB |
    | **Qwen3.5-4B Q4** | **46.7 / 46.7 / 38.3%** (2023 obrazy / 2024 / 2025); 45.5% z myśleniem na 2023 tekst | 2.74 GB |

    Qwen3.5-4B to bezpieczne zgłoszenie T3 już teraz; Qwen3.5-2B potrzebuje +15 pp.
- [x] **H-M5 (P1) [E]** Kwantyzacja małych modeli (≤ 2B): Q4 kosztuje ≤ 2 pp, IQ3 ≤ 5 pp; imatrix liczony na polskich tekstach historycznych zmniejsza stratę.
  - Wynik (Q4 vs Q8): **różnice w granicach szumu.** Qwen3.5-2B 25.5 vs 21.8%, Bielik-1.5B 27.3 vs 29.1%, Qwen3.5-0.8B 9.1 vs 5.5%. IQ3 i imatrix nie testowane.
- [x] **H-M6 (P1) [E]** Tryb myślenia pomaga w P/F i analizie źródeł, nie pomaga w identyfikacji faktów; w T1 koszt czasu jest akceptowalny.
  - Wynik: **myślenie pomaga dużym, szkodzi najmniejszym:**
    - Gemma-4-12B: 80.0% vs 56.4% bez myślenia (esej 15 vs 6);
    - Qwen3.5-4B: 45.5% vs 29.1% (mimo 8 uciętych);
    - Qwen3.5-2B: 10.9% vs 25.5% (17 odpowiedzi bez końca myślenia).

    Czas Gemmy: 6–10 min na arkusz na L40S przy 3 slotach, bez myślenia 46 s (H-I2).
- [ ] **H-M7 (P1) [E]** Model `-Base` po naszym SFT osiąga wynik ≤ 5 pp gorszy od wersji `-Instruct` z tym samym harnessem.
  - Wynik:
- [ ] **H-M8 (P0) [E]** Modele `-Base` bez treningu w protokole egzaminu (szablon czatu, prompt z benchmarku) mają bardzo niski wynik (≤ 15%).
  - Wynik: **zależy od rodziny.**
    - PLLuM-12B-base-2512: **0.0%** (34/34 odpowiedzi ucięte, powtarzające się bzdury). Wersja instruct tej samej rodziny ma 50.9%, co daje pogląd, jaki zysk jest możliwy po SFT.
    - Qwen3.5-2B-Base: 12.7%, Qwen3.5-0.8B-Base: 9.1% — odpowiadają spójnie (2B nawet „myśli”), więc gorzej nadają się do T2-B1.
    - Gołe bazy na arkuszu 2024 (fala 5b):

      | Baza | Wynik |
      |---|---|
      | Bielik-11B-v3-Base | 40.0% |
      | Bielik-4.5B-v3-Base | 31.7% |
      | Bielik-1.5B-v3-Base | 20.0% |
      | Gemma-4-12B pt | ok. 15% (ocena częściowa — odpowiada, potem dopisuje fikcyjne kolejne zadania, 40/40 uciętych) |

      **Bazy Bielika są mocne już bez treningu, więc słabo nadają się do T2.** Najsłabsze bazy to PLLuM-12B-base (0%) i Gemma-4-12B pt (~15%).
- [ ] **H-M9 (P1) [E]** W T1 natywny VLM jest lepszy niż „opis → model tekstowy”; w T3 najlepszy stosunek punktów do GB daje OCR (bez mmproj).
  - Wynik:
- [ ] **H-M10 (P2) [E]** Bielik-1.5B-v3 wygrywa z Qwen3.5-2B w T3 dzięki lepszej polskiej wiedzy.
  - Wynik:
- [x] **H-M11 (P2) [E]** `Bielik-PL-11B-v3.0-Instruct` jest lepszy od `Bielik-11B-v3.0-Instruct` na historii Polski.
  - Wynik: **nie** — 58.3% wobec 63.3% na arkuszu 2024.

## D. Harness

- [x] **H-H1 (P0) [E]** Formatowanie per typ zadania + zakaz asekuracji + normalizacja wyjścia daje ≥ +3 pp (więcej dla małych modeli).
  - Wynik: **obalona dla promptu v1** (fala 4, arkusz 2024, prompt organizatorów → v1):

    | Model | Organizatorów | v1 |
    |---|---|---|
    | Gemma | 81.7% | 75.0% |
    | Bielik-11B | 63.3% | 58.3% (esej 8 → 3) |
    | Qwen3.5-4B | 46.7% | 41.7% |
    | Bielik-1.5B | 26.7% | 23.3% |
    | Qwen3.5-2B | 20.0% | 16.7% |

    Nakaz „1–3 zdania” obcina uzasadnienia, a sztywne instrukcje eseju szkodzą Bielikowi. **Zostajemy przy prompcie organizatorów**; format zamkniętych lepiej wymuszać parserem lub gramatyką, nie długim promptem.
- [x] **H-H2 (P0) [E]** (częściowo: tak dla małych modeli z HyDE, nie dla dużych) RAG daje ≥ +5 pp małym modelom i ≥ +2 pp dużym; BM25 z lematyzacją jest co najmniej tak dobry jak dense, a hybryda najlepsza.
  - Wynik end-to-end (fala 4, arkusz 2024, v1 → v1 + RAG): **RAG pomaga średnim i małym modelom, Gemmie nie.**

    | Model | v1 | v1 + RAG |
    |---|---|---|
    | Qwen3.5-4B | 41.7% | **55.0%** (+13.3, lepiej niż bez harnessu 46.7%) |
    | Bielik-11B | 58.3% | 66.7% (+8.4) |
    | Qwen3.5-2B | 16.7% | 25.0% (+8.3) |
    | Gemma | 75.0% | 73.3% |
    | Bielik-1.5B | 23.3% | 20.0% |

    **Czysty test (fala 5: prompt organizatorów vs + RAG, bez v1): efekt w granicach szumu.**

    | Model | 2024 | 2025 |
    |---|---|---|
    | Gemma | 81.7 → 80.0% | — |
    | Bielik-11B | 63.3 → 65.0% | — |
    | Qwen3.5-4B | 46.7 → 46.7% | — |
    | Bielik-1.5B | 26.7 → 31.7% | 28.3 → 26.7% |
    | Qwen3.5-2B | 20.0 → 23.3% | 25.0 → 20.0% |
    | Qwen3.5-4B + myślenie | 48.3 → **60.0%** | 50.0 → 50.0% |

    Obecny RAG (BM25 na ogólnej Wikipedii, top-4) nie jest dźwignią; może pomóc lepsza baza (kompendium wg wymagań CKE) albo trening na korzystanie z kontekstu (H-T3).
  - **Diagnoza (26.09, 15:00):** problemem było wyszukiwanie, nie pomysł.
    - Straty małych modeli są głównie w eseju (4–13%) i pytaniach o fakty „podaj” (18–36%).
    - Pokrycie odpowiedzi z klucza w pobranych fragmentach (32 zadania „podaj/wymień” z krótkim kluczem, `eval/rag_coverage.py`):

      | Zapytanie | top-4 | top-10 | top-30 |
      |---|---|---|---|
      | polecenie + źródła (dotychczas) | **28%** | 34% | 53% |
      | słowa kluczowe od `gpt-6-luna` | 69% | 72% | 75% |
      | HyDE od `gpt-6-luna` (górna granica, luna zna odpowiedź) | **81%** | 84% | 88% |
      | HyDE od Bielika-1.5B (lokalnie, `eval/hyde_local.py`) | **47%** | 53% | — |

    - Bielik-1.5B sam zna odpowiedź w 28% tych pytań; spośród 23, których nie zna, RAG z jego HyDE podsuwa odpowiedź w 25% (bez HyDE 22%).
    - **Wniosek:** HyDE + bramkowanie po typie zadania (RAG tylko dla pytań o wiedzę i eseju). Dalsze usprawnienie: kompendium wg wymagań CKE jako baza (generuje je subagent).
  - **Wynik end-to-end HyDE (26.09, 16:30, `server/exp_rag.sh`, sędzia `gpt-6-luna`).** HyDE pisze ten sam model, a zapytanie to HyDE + polecenie + źródło. `hyde_podaj` oznacza RAG tylko dla „podaj/wymień/nazwij”, a `hyde_all` również dla otwartych, „rozstrzygnij” i eseju. Punkty dla 2024 są liczone bez jednej nieocenionej pozycji, wspólnej dla wszystkich przebiegów.

    | Model | 2024: bez RAG / podaj / all | 2025: bez RAG / podaj / all |
    |---|---|---|
    | Bielik-1.5B (Q8) | 9 / 13 / **15** pkt | 21.7 / 25.0 / **28.3%** |
    | Qwen3.5-2B | 11 / **14** / 12 pkt | 16.7 / **23.3** / 21.7% |
    | Qwen3.5-4B + myślenie | **29** / 22 pkt | — (przerwane, zbyt wolne) |

    - **Małe modele: HyDE pomaga spójnie**, średnio o 6–8 pp we wszystkich czterech porównaniach. To powyżej szumu seedów (±4 pp). Zostaje w harnessie T3: Bielik z `hyde_all`, Qwen-2B z `hyde_podaj`.
    - **Qwen3.5-4B z myśleniem: HyDE szkodzi, ale przez urwania.** Bez RAG urwało się 6 z 40 odpowiedzi, z HyDE 12 (dłuższy kontekst wydłuża myślenie). Poprawka w harnessie: przy urwaniu albo pustej odpowiedzi zadanie jest powtarzane bez myślenia (`fallback` w `debug.jsonl`).
  - Wynik (częściowy — samo wyszukiwanie): BM25 na 7 mln pasaży PolQA, 947 pytań walidacyjnych. **Obcięcie słów do 6 znaków wyraźnie pomaga:** recall@10 wzrósł z 61.1% do 70.9%, recall@1 z 29.8% do 37.7%, recall@50 z 75.7% do 85.0%. Połączenie pól `raw+stem` jest gorsze niż samo `stem`. Zapytanie trwa ~0.06 s na CPU. Dense i zysk w wyniku egzaminu — do sprawdzenia.
- [ ] **H-H3 (P1) [E]** Dynamiczne few-shot z podobnych zadań CKE (z kluczem) daje ≥ +2 pp.
  - Wynik:
- [ ] **H-H4 (P1) [E]** Głosowanie (k = 5) na zamkniętych daje ≥ +1 pp na całym arkuszu.
  - Wynik:
- [ ] **H-H5 (P1) [E]** Dla małych modeli ocena log-prob opcji (wybór, P/F per stwierdzenie) jest lepsza niż generowanie odpowiedzi.
  - Wynik:
- [ ] **H-H6 (P0) [E]** Esej „plan → fakty → pisanie → weryfikacja” daje ≥ +3/15 małym i ≥ +1/15 dużym modelom; szablon sekcyjny daje małym modelom ≥ 2/3 za spójność.
  - Wynik:
- [ ] **H-H7 (P1) [E]** Best-of-N esejów z wyborem przez lokalnego sędziego daje ≥ +1/15.
  - Wynik:
- [x] **H-H8 (P1) [E]** Wybór tematu eseju ma znaczenie ≥ 1–2 pkt (np. „3 aspekty” łatwiejsze niż „3 władców”).
  - Jak sprawdzić: wszystkie 3 tematy z arkuszy 2023–2026 i starszych, dla każdego modelu.
  - Wynik (sob 22:00): **nie.** Gemma QAT, 3 eseje trzytematowe 2024–2026 × 3 seedy: bez wyboru 54.8%, z samooceną i wyborem tematu 48.9% (−6 pp). Odrzucone.
- [ ] **H-H9 (P1) [E]** Zespół modeli ≤ 8 GB (głosowanie / wybór przez sędziego) daje ≥ +2 pp względem najlepszego pojedynczego modelu (najpierw liczymy wyrocznię).
  - Wynik (częściowy):
    - wyrocznia Gemma+Bielik-11B daje +3 do +7 pkt na 60 (2024: 52 vs 49, 2025: 51 vs 49, 2026: 53 vs 46), więc zysk jest realny;
    - prosty podział „obrazy i esej → Gemma, reszta → Bielik” daje 47 / 45 / 48 — gorzej lub tyle samo co sama Gemma;
    - **potrzebny selektor** (lokalny sędzia wybierający lepszą odpowiedź albo głosowanie z pewnością modelu).
  - Wynik selektora (fala 5): Gemma-4-12B z myśleniem wybiera między swoją odpowiedzią a Bielika, widząc zadanie i obrazy, ale bez klucza. Daje 49 / 47 / 48 pkt wobec 49 / 49 / 46 samej Gemmy — **brak zysku**. Zespół Gemma + Bielik odkładamy; wyrocznia pokazuje potencjał, ale selekcja bez klucza go nie wydobywa.
- [ ] **H-H10 (P2) [E]** Wyszukiwanie obrazów (SigLIP2 + Commons/WIT) poprawia zadania identyfikacyjne z obrazami.
  - Wynik:
- [ ] **H-H11 (P2) [E]** Narzędzie do tabel (ekstrakcja tabeli + obliczenia w kodzie) poprawia zadania z danymi statystycznymi.
  - Wynik:
- [ ] **H-H12 (P1) [E]** Krótkie odpowiedzi (1–3 zdania) na otwarte dostają nie mniej punktów niż długie, a rzadziej zawierają sprzeczności.
  - Wynik:
- [x] **H-H13 (P0) [E]** Typ zadania da się rozpoznać regułami (regex na stałych formułach poleceń CKE) z trafnością ≥ 95%, bez modelu embeddingowego.
  - Wynik: **97.4% (147/151)** na arkuszach 2023–2026 (`eval/items.py::classify`). Wszystkie 4 pomyłki to „uzupełnij tabelę nazwami”, gdzie rozróżnienie otwarte/zamknięte i tak nie zmienia strategii odpowiedzi. Klasyfikator embeddingowy niepotrzebny (a w T3 byłby kolejnym modelem).
- [ ] **H-H14 (P1) [E]** Esej pisany akapit po akapicie (plan → fakty z RAG dla każdego elementu → osobny akapit na element → wstęp i zakończenie → wygładzenie przejść) daje więcej punktów niż esej w jednym przebiegu — szczególnie w narracji (0–12) i u małych modeli; nie traci na spójności (0–3).
  - Jak sprawdzić: 12 tematów z lat 2023–2026 × 2 warianty × modele z każdego tracku; ocena wg kryteriów CKE.
  - Wynik: **obalona** (12 tematów, średnio pkt / 15, jeden przebieg vs akapit po akapicie, oba z RAG):

    | Model | Jeden przebieg | Akapit po akapicie |
    |---|---|---|
    | Gemma | **12.7** | 10.2 |
    | Qwen3.5-4B | 4.1 | 4.0 |
    | Qwen3.5-2B | 1.2 | 0.4 |
    | Bielik-1.5B | 0.9 | 1.4 |
    | Bielik-11B | 9.75 | — (sampler llama.cpp nie obsłużył trybu JSON) |

    Składanie z części nie naprawia braku wiedzy małych modeli, a dużym psuje spójność. Dla małych modeli esej trzeba poprawiać **treningiem (SFT na wzorcowych esejach)**, nie rozbijaniem na kroki.

## E. Trening i dane

- [ ] **H-T1 (P0) [E]** SFT na 3–10 tys. przykładów w formacie CKE (destylacja) daje małym modelom ≥ +5 pp.
  - Wynik dla Bielika-1.5B (26.09, 18:30): **nie**, zmiana w granicach szumu.
    - Zbiór: 1788 przykładów po deduplikacji (bliskie duplikaty: Jaccard ≥ 0.4 na poleceniu i kluczu, w tej samej sekcji i typie; −101). Zadania z obrazem pominięte.
    - Trening: LoRA r=32, 2 epoki, lr 2e-4 (Modal L4, 10 min), eval_loss 0.96.
    - Ewaluacja: baza Q4_K_M + LoRA (84 MB, 8.7% bazy), a porównanie z bazą Q8 bez treningu:

      | Wariant | 2024 | 2025 |
      |---|---|---|
      | baza Q8 | 9/60 | 21.7% |
      | baza Q8 + HyDE | 15/60 | 28.3% |
      | SFT, Q4 | 8/60 | 26.7% |
      | SFT, Q4 + HyDE | 8/60 | 25.0% |

    - Forma jest wyuczona wzorowo: „Temat nr 1”, teza, akapity argumentacyjne, „Rozstrzygnięcie + uzasadnienie”, dokładny format zamkniętych. Treść pozostaje zmyślona, np. bitwa „pod Korościsławicami” 1411 r. i Wojciech jako „władca Polski”. **SFT uczy formy, nie wiedzy.** Model 1.5B nie ma dość wiedzy na 35%, więc T3 opiera się na Qwen3.5-4B w niższej kwantyzacji.
- [ ] **H-T2 (P1) [E]** SFT na esejach ≥ 13/15 podnosi esej małych modeli do ≥ 5/15.
  - Wynik (Bielik-1.5B): **nie**, esej po SFT ma 1/15 i 3/15. Długość (362–428 słów) i struktura są poprawne, ale kryterium merytoryczne zabijają błędy faktograficzne.
- [ ] **H-T3 (P1) [E]** RAFT (trening z kontekstem RAG, w tym mylącym) poprawia korzystanie z RAG przez małe modele.
  - Wynik:
- [ ] **H-T4 (P2) [E]** LoRA na Gemma-4-12B-it daje ≥ +2 pp i nie powoduje regresji.
  - Wynik:
- [ ] **H-T5 (P2) [E]** CPT na korpusie historycznym (50–100 mln tokenów) poprawia wiedzę małego modelu o ≥ 2 pp. *(niska pewność — literatura sugeruje, że fakty lepiej dostarczać przez RAG)*
  - Wynik:
- [ ] **H-T6 (P2) [E]** DPO/ORPO na parach esejów daje ≥ +1/15 ponad SFT.
  - Wynik:
- [ ] **H-T7 (P1) [E]** LoRA trenowana na wagach `qat-q4_0-unquantized` działa na bazie q4_0 GGUF bez straty.
  - Wynik:
- [ ] **H-T8 (P0) [E]** Dane treningowe nie zawierają zadań z DEV/TEST (deduplikacja n-gramowa i semantyczna).
  - Wynik:
- [ ] **H-T9 (P1) [E]** Domieszka 10–20% ogólnych instrukcji po polsku chroni model `-Base` przed utratą ogólnych umiejętności (bez spadku na formacie i eseju).
  - Wynik:
- [ ] **H-T10 (P1) [E]** Ekstrakcja arkuszy przez Gemini jest wystarczająco dokładna (≥ 95% zadań poprawnych po ręcznej kontroli próbki).
  - Wynik: zamiast Gemini powstał własny konwerter PDF (`eval/build_exam.py`): arkusze 2024–2026 mają 60/60 pkt i klucze zgodne z zasadami. Starsze formuły — do sprawdzenia.
- [ ] **H-T11 (P0) [E]** W T3 opłaca się **mocno skwantyzowana baza + adapter LoRA w BF16 (nieliczony)**. Np. Qwen3.5-4B IQ2_M (1.76 GB) albo Qwen3.5-2B IQ3_XXS (0.93 GB) + LoRA wytrenowana na wagach tej samej bazy odzyskuje stratę kwantyzacji i dokłada wiedzę i format. Wynik ≥ 40% przy mniejszym rozmiarze niż model bez LoRA.
  - Jak sprawdzić: drabina kwantyzacji Qwen3.5-4B (Q4 → Q3 → IQ3 → IQ2) z LoRA i bez niej, ten sam harness (myślenie + RAG).
  - Wynik:

## F. Infrastruktura i czas

- [ ] **H-I1 (P0) [E]** llama.cpp stabilnie obsługuje Gemma 4 i Qwen3.5: mmproj, LoRA w locie, myślenie z budżetem, gramatyki, log-prob, MTP.
  - Wynik (częściowy): obraz `ghcr.io/ggml-org/llama.cpp:server-cuda` (build 11176) działa z Qwen3.5 (tekst + obrazy, przełączanie myślenia), Gemma 4 (tekst, myślenie), Bielikiem i PLLuM; `--kv-unified` i `--reasoning-format deepseek` działają. Nie testowano jeszcze LoRA, gramatyk, log-prob i MTP.
- [x] **H-I8 (P0) [E]** Gemma 4 z obrazami w llama.cpp wymaga większego mikro-batcha.
  - Wynik: **potwierdzone.** Przy domyślnym `-ub 512` serwer pada (`GGML_ASSERT ... non-causal attention requires n_ubatch >= n_tokens`), bo tokeny obrazu używają atencji niekauzalnej. Z `-ub 4096 -b 4096` działa. **Konieczne w konfiguracji egzaminacyjnej.**
- [ ] **H-I2 (P0) [E]** Pełny egzamin w konfiguracji T1 mieści się w ≤ 10 min na L40/H100 (≤ 5 min w trybie szybkim).
  - Wynik (częściowy): Gemma-4-12B QAT z myśleniem na L40S, 3 równoległe sloty: 334–572 s na arkusz (ok. 6–10 min), bez myślenia 46 s. Na H100 i z dekodowaniem spekulatywnym (MTP) powinno być szybciej — do zmierzenia. Czas pojedynczego pytania ma znaczenie, jeśli skrypt pyta sekwencyjnie.
- [ ] **H-I3 (P1) [E]** Kaggle/Colab T4 wystarcza na QLoRA modeli ≤ 4B w ≤ 3 h.
  - Wynik:
- [x] **H-I4 (P1) [E]** Limity Gemini Tier 1 pozwalają wygenerować ≥ 10 tys. przykładów w ≤ 6 h (inaczej przejście na Vertex AI batch z kredytów GCP).
  - Wynik: **nieaktualne** — środków w Gemini nie ma. Dane generuje Forgehand LLM API (`gpt-6-sol` / `gpt-6-luna`).
- [x] **H-I5 (P0) [M]** L40/H100 będą dostępne od sobotniego popołudnia na ≥ 12 h.
  - Wynik: **tak.** Forgehand L40S działa od 13:54 (1 sesja naraz). Od 16:45 dochodzi Nebius (123 $, H100 3.85 $/h na żądanie, czyli ~32 h). Nebius wymaga jeszcze logowania CLI i limitu GPU (H-I9).
- [ ] **H-I9 (P0) [E]** Konto Nebius ma limit ≥ 1 GPU H100 w `eu-north1`, a maszyna z obrazem CUDA startuje w ≤ 15 min.
  - Jak sprawdzić: `~/.nebius/bin/nebius profile create` (logowanie przez przeglądarkę), potem lista limitów i start maszyny.
  - Wpływ: czy T2 dostaje własną kartę; bez niej T2 trenuje na Forgehand po T3, a ewaluacje idą na Modal.
  - Wynik (częściowy, 17:15): **limit jest** — 32 × H100, H200 i L40S w `eu-north1`, 12 maszyn, 8 wywłaszczalnych. CLI zalogowane, a konto serwisowe ma dostęp do projektu `eu-north1` (lista maszyn i platform działa). Czas startu maszyny — do zmierzenia przy pierwszym uruchomieniu. Klucz z `.env` pozostaje kluczem Object Storage (S3).
- [ ] **H-I6 (P1) [E]** Unsloth/TRL obsługuje trening LoRA dla Gemma 4 i Qwen3.5 (w tym warstwy wizualne lub ich zamrożenie).
  - Wynik:
- [ ] **H-I7 (P1) [E]** Harness działa w pełni offline (test z odciętą siecią).
  - Wynik:

## G. Konkurencja i strategia

- [ ] **H-S1 (P1) [M]** W T1 większość mocnych zespołów weźmie Gemmę-4-12B; do wygranej potrzeba ≥ 85%.
  - Wynik:
- [ ] **H-S2 (P1) [M]** W T2 wygrywa duży skok z bardzo słabej bazy; +30 pp może nie wystarczyć, jeśli ktoś użyje `-Base`.
  - Wynik:
- [ ] **H-S3 (P1) [M]** W T3 konkurencja zejdzie do ~1–1.5 GB; do wygranej potrzeba ≤ 0.8 GB.
  - Wynik:
- [ ] **H-S4 (P0) [M]** Leaderboard próbny pokazuje modele bazowe i wyniki konkurencji, co pozwala urealnić strategię po G2.
  - Wynik:

---

## Mapa: hipotezy → decyzje

| Decyzja | Bramka | Kluczowe hipotezy |
|---|---|---|
| Konfiguracja T1 (`t1final` czy stara; esej) | G4 (nd ~08:00) | H-N1, H-N6, H-N7, H-N13, H-E6 |
| Baza T2 (PLLuM-12B-base czy Gemma-4-12B pt) | G3 (sob ~21:30) | H-N2, H-N8, H-M8, H-T1 |
| Runda 2 SFT dla T2 | G3 → G4 | H-N9, H-N10, H-N11, H-N15, H-N26, H-N27 |
| Model i rozmiar T3 | G3 → G4 | H-N3, H-N4, H-N5, H-N16, H-N17, H-N18, H-N22, H-N23, H-N24, H-H2 |
| Baza wiedzy i wyszukiwanie | przed G4 | H-N12, H-N19, H-N20, H-N21, H-N24, H-N25 |
| Wiarygodność pomiarów | stale | H-E4, H-E6, H-E7, H-N14 |

## H. Dodatkowe ustalenia (26.09, południe)

- [x] **H-X1 [M]** Istnieją gotowe modele dostrojone pod maturę z historii.
  - Wynik: **nie.** Na HF nie ma finetune'ów pod maturę ani historię Polski. Najbliższy jest `JohnTdi/egzamin-osmoklasisty-pllum-8b` (egzamin ósmoklasisty, bez historii). Są za to przydatne bazy w GGUF bez bramki: `mradermacher/Bielik-1.5B-v3-ungated-GGUF` i `mradermacher/Bielik-4.5B-v3-Base-ungated-GGUF` (bazy do T2/T3) oraz `macszym/Bielik-PL-11B-v3.0-Instruct-GGUF` (wariant PL, H-M11).
- [x] **H-X2 [E]** Bielik-11B-v3-Base można przekonwertować do GGUF.
  - Wynik: tak, ale repo bazy ma tylko `tokenizer.json`. Konwerter llama.cpp wymaga `tokenizer.model`, który bierzemy z `Bielik-11B-v3.0-Instruct` — słownik jest identyczny (32000 tokenów, te same 131 tokenów specjalnych), a wagi pozostają nietknięte. Gemma-4-12B (pt) wymaga nowszego `transformers` niż przypięty w llama.cpp (`overnight/modal_convert.py`).

## I. Nowe hipotezy (sob 19:40) — do sprawdzenia do G4

Kolejność sprawdzania i maszyny: raport 05, §3–4. Każda ma kryterium z góry, żeby decyzja nie zależała od tego, co wyjdzie.

- [x] **H-N1 (P0) [E]** Docelowa konfiguracja T1 (`t1final`) jest co najmniej tak dobra jak stara konfiguracja z Modal.
  - Skąd wątpliwość: przy tym samym sędzi `t1final` ma 72.0% średnio, a stara 76.6% (2024 74.6 vs 76.3; 2025 **63.3 vs 78.3**; 2026 71.7 vs 75.0; mock 78.3 vs 76.7). Różnice konfiguracji: prompt systemowy dla zadań bez obrazów, dopisek „Zapisz odpowiedź dokładnie w formacie” przy zamkniętych, poprawki eseju.
  - Test: obie konfiguracje × 2 seedy × (2024, 2025), jedna na kartę, w harnessie (stary prompt jako opcja).
  - Kryterium: zostaje wariant z wyższą średnią; różnica < 2 pp → `t1final` (ma poprawki odporności).
  - Wynik (sob 23:00): **nie** (różnica w granicach szumu). Paczki v2, luna, po 2 seedy: `t1final` 72.3 / 69.7% (średnio 71.0%), stary prompt 73.1 / 71.4% (72.3%). Różnica +1.2 pp < 2 pp, więc zostaje `t1final`, który ma poprawki odporności. Wcześniejsza przewaga starych przebiegów (76.6%) wynikała głównie z innej paczki (bez znaczników obrazów) i szumu.
- [x] **H-N2 (P0) [E]** Gemma-4-12B pt z LoRA **scaloną w wagi** działa w `llama.cpp` i daje ≥ 55% na 2024 + 2025.
  - Tło: LoRA nakładana w locie na Gemmę 4 psuje wyjście (`<unused49>`, potem błąd CUDA) przy `-ub 4096` i wielu slotach; w `transformers` ten sam adapter odpowiada poprawnie („Bitwa pod Grunwaldem; Władysław Jagiełło.”). Scalony plik `gemma-4-12B-sft-Q4_K_M.gguf` (7.38 GB, T2 ≤ 8.8 GB z mmproj) jest gotowy.
  - Kryterium wyboru bazy T2: przyrost w pp względem gołej bazy (H-N8). Gemma pt wygrywa, jeśli jej przyrost jest ≥ 3 pp większy niż PLLuM (+35–40 pp).
  - Wynik (sob 23:00): **nie.** Scalona LoRA na Gemmie pt w `llama.cpp` z obrazami (`-ub 4096`, 8 slotów, `--kv-unified`) daje 0.8% (powtarzany `<unused49>`, potem błąd CUDA). Bez obrazów i bez `--kv-unified` (diagnostyka A) działa stabilnie, ale ma 32.2% na 2024, a PLLuM + LoRA 45.8%. **Baza T2: PLLuM-12B-base** (G3). Ten sam błąd CUDA dotyka też Gemmy QAT (T1); zabezpieczenie: nadzorca serwera + ponawianie w harnessie.
- [x] **H-N3 (P0) [E]** W T3 esej bez myślenia, z kompendium jako kontekstem, jest lepszy niż esej z myśleniem.
  - Tło: myślenie w eseju Qwen3.5-4B urywa się przy 12 tys. tokenów, więc i tak powstaje esej awaryjny. Na 12 tematach (luna, esej bez myślenia): bez kontekstu 14.4%, `--careful` 12.8%, kompendium + `--careful` **20.0%**.
  - Kryterium: esej ≥ +1 pkt średnio na 2 arkuszach w konfiguracji T3.
  - Wynik (nd 00:30): **częściowo, efekt mały.** Konfiguracja T3 (esej bez myślenia, kompendium w kontekście) daje esej Qwen3.5-4B Q4 5/30 (17%), a wcześniej z myśleniem i powtórką 4/30 (13%). Esej pozostaje najsłabszym typem w T3.
- [x] **H-N4 (P0) [E]** Qwen3.5-4B UD-IQ3_XXS (1.95 GB) utrzymuje średnio ≥ 40% na 2024 + 2025 w konfiguracji T3.
  - Wcześniejsze próby padły przez OOM na Forgehand (to nie jest wynik modelu).
  - Wynik (sob 23:00): **nie** (36.1% < 40%). IQ3_XXS traci głównie na eseju (2/30) i dopasowaniu (0/6); myślenie częściej się zapętla (22 powtórki na arkusz). Próby ratunku: RAG z bazy wiedzy 33.6% („podaj” +4 pp, „rozstrzygnij” +4 pp, ale esej 0/30), myślenie tylko dla „rozstrzygnij”/otwartych 31.1%.
- [x] **H-N5 (P1) [E]** Qwen3.5-4B UD-IQ2_M (1.76 GB) albo Qwen3.5-2B Q4_K_M (1.28 GB) z myśleniem utrzymuje ≥ 40%.
  - Kryterium: zgłaszamy najmniejszy wariant ≥ 40% na 2024 + 2025 i ≥ 37% na 2026.
  - Wynik (sob 23:00): **nie.** IQ2_M 21.0%, Qwen3.5-2B 17.6% (z HyDE 21.8%). **Nowy kandydat T3: Q3_K_M (2.29 GB) — 48.7% na 2024+2025 i 48.3% na 2026**, tyle co Q4_K_M (48.7%) przy mniejszym rozmiarze. IQ4_XS (2.48 GB): 41.2%.
- [x] **H-N6 (P1) [E]** Esej Gemmy (T1) z kompendium jako kontekstem jest lepszy o ≥ 1 pkt na 12 tematach (`essays12_rag`).
  - Ryzyko: kompendium pokrywa ok. połowę tematów, a nietrafiony kontekst może rozpraszać.
  - Wynik (sob 23:00): **tak na samych esejach, nie na pełnych arkuszach.** 12 tematów: bez kontekstu 52.8%, kompendium (BM25) 62.2% (+9.4 pp), hybryda e5 58.9%. Pełne arkusze v2 (2 seedy): `t1final` 71.0% → z kompendium 68.9%. Dla T1 odrzucone.
- [x] **H-N7 (P1) [E]** Niższa temperatura dla eseju (0.7 zamiast 1.0) zmniejsza rozrzut ocen eseju Gemmy bez spadku średniej.
  - Tło: ten sam model i konfiguracja dawały na 2026 esej 13/15 i 6/15 (inny wybór tematu i inny przebieg).
  - Test: 12 tematów × 2 seedy na obu temperaturach; porównujemy średnią i odchylenie.
  - Wynik (nd 01:00): **bez różnicy dla T1** (Gemma: temperatura 0.6 71.4% vs 1.0 72.3 / 69.7%). **Duża różnica dla T3**: Qwen3.5-4B Q3_K_M przy 1.0 — 48.7 / 38.7 / 42.0% (3 seedy), przy 0.6 — 48.7 / 51.3% i 48.3% na 2026. T3 idzie z temperaturą 0.6.
- [x] **H-N8 (P0) [E]** Goła Gemma-4-12B pt ma w oficjalnym protokole (bez harnessu, szablon domyślny) ~15%.
  - Tło: pomiar z fali 5b jest niepełny (16 i 30 pkt nieocenionych, 38–40 odpowiedzi uciętych). Od tego zależy przyrost T2.
  - Wynik (sob 23:00): **tak (~0%).** Goła Gemma pt i goły PLLuM na paczkach v2 (tryb `--bare`): 0% — prawie wszystkie odpowiedzi urwane albo puste.
- [x] **H-N9 (P1) [E]** Trening Gemmy pt na tym samym szablonie, na którym ją serwujemy (`train/templates/gemma4_turns.jinja`), daje ≥ +2 pp względem treningu na szablonie `-it`.
  - Tło: szablon `-it` przy generowaniu dokleja pusty kanał myślenia, którego w treningu nie było; obecnie obchodzimy to szablonem przy serwowaniu.
  - Wynik (nd 01:00): **nie testowane:** Gemma-4 pt odpadła jako baza T2 (H-N2), więc runda 2 dotyczyła PLLuM.
- [x] **H-N10 (P1) [E]** Dodanie 115 zadań CKE z obrazami (trening wizyjny Gemmy pt) daje ≥ +2 pp na zadaniach z obrazami bez straty na reszcie.
  - Wynik (nd 01:00): **nie testowane:** jak wyżej (trening wizyjny dotyczył tylko Gemmy pt).
- [x] **H-N11 (P2) [E]** 3 epoki zamiast 2 (albo +50% esejów) poprawiają T2 o ≥ 2 pp.
  - Wynik (nd 01:00): **częściowo w H-N26/H-N27:** 2 epoki na ~10–12 tys. przykładów; zysk dał przepis v1 na pełnych danych z RAG.
- [x] **H-N12 (P2) [E]** Dogenerowanie ~300 notatek kompendium dla wymagań CKE bez notatki podnosi trafność wyszukiwania dla tematów esejów z ~50% do ≥ 80% i esej o ≥ 1 pkt.
  - Koszt: ~5–8 $ z API Forgehand (`gpt-6-sol`).
  - Wynik (nd 01:00): **częściowo:** limit budżetu E6 zatrzymał dogenerowanie kompendium na 106 notatkach (zamiast ~300); baza wiedzy dostała za to oś czasu 2817, postacie 940 i pojęcia 627 wpisów (H-N19).
- [x] **H-N13 (P2) [E]** Limit myślenia 4000 tokenów dla zamkniętych skraca przebieg T1 o ≥ 30% bez straty punktów.
  - Wynik: **odrzucone decyzją zespołu (sob 19:40)**, bez testu. Myślenie daje zbyt dużo, żeby je przycinać (raport 08, wniosek 3).
- [x] **H-N15 (P0) [E]** SFT bazy T2 na danych z rozumowaniem (uzasadnienie z kluczem pisane przez `gpt-6-luna`, format myśli danego modelu) daje ≥ +5 pp względem SFT bez rozumowania.
  - Tło: myślenie daje Gemmie-it ~+25 pp, a Qwen3.5-4B +8–19 pp na zamkniętych; bazy T2 nie myślą wcale (raport 08, §3). Koszt danych ~2 $ (luna), kontrola próbki ~50 przez sol lub Claude.
  - Wynik (sob 23:40): **nie.** PLLuM, dane v2 (5 tys., 1 epoka): wariant `think` 37.8%, `answer` 38.7% (v1: 41.2%). Model pisze `<think>` tylko w 7/40 zadań (uzasadnienie miała połowa przykładów) i czasem się rozsypuje.
- [x] **H-N16 (P2) [E]** SFT Qwen3.5-4B na krótkich rozumowaniach (≤ 400 słów) zmniejsza liczbę urwań (dziś 6–14 na arkusz) i daje ≥ +3 pp, bez psucia natywnego myślenia.
  - Wynik (nd 01:00): **zastąpione przez H-N22** (dostrajanie Qwen bez przykładów rozumowania); bramka pokazała, że każde dostrajanie odpowiedzi skraca myślenie, więc wariantu z krótkimi rozumowaniami nie uruchamialiśmy.
- [x] **H-N17 (P1) [E]** Qwen3.5-4B UD-IQ2_XXS (1.52 GB) utrzymuje ≥ 40% w konfiguracji T3 (sprawdzamy tylko, jeśli IQ2_M ≥ 40%).
  - Wynik (sob 23:00): **pominięte:** IQ2_M ma 21%, daleko pod progiem 40%.
- [x] **H-N18 (P1) [E]** Qwen3.5-2B Q4_K_M (1.28 GB) z myśleniem, obrazami i HyDE dla „podaj” osiąga ≥ 35%.
  - Tło: bez myślenia 18–24%; HyDE +6 pp; myślenie w teście z 2023 dawało puste odpowiedzi, a teraz jest powtórka bez myślenia przy urwaniu.
  - Wynik (sob 23:00): **nie:** Qwen3.5-2B z myśleniem i HyDE dla „podaj”: 21.8% (bez HyDE 17.6%).
- [x] **H-N19 (P0) [E]** Baza wiedzy o historii Polski (oś czasu ~2000 wpisów, postacie ~800, pojęcia ~500) podnosi trafność wyszukiwania top-3 dla zadań „podaj / rozstrzygnij” z historii Polski o ≥ 20 pp względem samego PolQA.
  - Tło: historia Polski to najsłabszy obszar wszystkich modeli (Qwen-4B 44% vs 90% w powszechnej; raport 08, wniosek 2). Test tylko na CPU (trafność wyszukiwania), end-to-end dopiero dla zwycięzcy.
  - Wynik (sob 23:00): **tak.** Benchmark wyszukiwania (32 zadania „podaj/wymień/nazwij”, top-3): PolQA 22% (HyDE Qwen-2B 25%) → PolQA + najlepszy wpis z każdej małej bazy 50% (HyDE 56%); historia Polski 55–60% vs 25% (+30 pp). Baza: oś czasu 2817, postacie 940, pojęcia 627, kompendium 218 + 106.
- [x] **H-N20 (P1) [E]** Hybryda BM25 + mały embedder (RRF) daje ≥ +10 pp trafności top-3 względem samego BM25 na tej samej bazie.
  - Ograniczenie: embedder liczy się jako model (H-R7). W T3 musi być mniejszy od głównego; w T1/T2 wchodzi do sumy 8.8 GB.
  - Wynik (sob 23:00): **częściowo.** Hybryda BM25 + e5-small: kompendium 25% → 47% (+22 pp), oś czasu 31% → 34%, postacie 9% → 16%, pojęcia 12% → 16%. W eseju T1 hybryda dała mniej niż samo BM25 (58.9 vs 62.2%).
- [x] **H-N21 (P1) [E]** RAG z bazy o historii Polski, włączany tylko dla zadań z historii Polski („podaj / rozstrzygnij”), poprawia T1 i T3 o ≥ +3 pp, bez straty na powszechnej.
  - Wynik (nd 00:30): **nie dla T3, tak dla T2.** T3 IQ3_XXS z RAG z bazy: „podaj” 42 → 46%, „rozstrzygnij” 39 → 43%, ale całość 36.1 → 33.6% (esej 2/30 → 0/30). T3 Q3_K_M z RAG PolQA + baza: 48.7 → 42.9% (jeden seed). T2 PLLuM z adapterem na pełnych danych: bez RAG 40.3%, z RAG PolQA + baza **52.9%**. Klasyfikatora Polska/świat do bramkowania nie używamy (82% trafności, H-N24).
- [x] **H-N22 (P1) [E]** Model myślący (Qwen3.5-4B, T3) da się dostroić bez przykładów rozumowania i bez utraty myślenia: strata tylko na odpowiedzi, a blok myślenia zamaskowany (`train/sft_lora.py --mask-think`).
  - Tło (sprawdzone 20:10): szablon Qwen3.5 składa przykład jako `assistant\n<think>\n\n</think>\n\nODPOWIEDŹ`, a dotychczasowy trening liczył stratę od `assistant\n`, więc uczył też **pomijania myślenia** (pusty blok). Z maską pusty blok jest częścią promptu, a model przy inferencji myśli sam.
  - Kryterium: średnia długość myślenia i liczba urwań bez istotnej zmiany, wynik ≥ +3 pp na 2024 + 2025. Wariant mocniejszy: odpowiedzi z własnym myśleniem modelu, zostawione tylko tam, gdzie wynik zgadza się z kluczem (rejection sampling), strata nadal tylko na odpowiedzi.
  - Wynik (sob 23:40): **nie** — bramka zatrzymała adapter. Trening z maską (`--mask-think`, strata tylko od `</think>`, r=16, lr 5e-5, 1 epoka na 5 tys. przykładów, Modal L40S 44 min). Sonda 60 zadań: mediana myślenia 12.1 tys. → 2.7 tys. znaków (−77%), zamknięte 70% → 55%, powtórki bez myślenia 20% → 8%. Maska chroni przed uczeniem pustego bloku, ale samo dostrajanie odpowiedzi skraca rozumowanie. T3 zostaje bez LoRA. Technicznie: konwerter LoRA w `llama.cpp` nie obsługuje Qwen3.5 (głowice DeltaNet), więc adapter scalaliśmy w wagi i dopisywaliśmy warstwę MTP z oryginału.
- [x] **H-N23 (P0) [E]** W T3 routing zadań do różnych modeli (liczy się tylko największy plik, suma < 8.8 GB) daje ≥ +5 pp przy tym samym rozmiarze maksymalnym.
  - Pomysł: zadania z historii Polski bez obrazu → polski model podobnego rozmiaru (np. Bielik-4.5B-v3-Instruct w IQ3, ~1.9 GB), zadania z obrazem i historia powszechna → Qwen3.5-4B IQ3_XXS (1.95 GB). Qwen-4B ma 44% z historii Polski i 90% z powszechnej (raport 08).
  - Warunek: polski model musi być lepszy od Qwen na zadaniach z historii Polski; dziś nie mamy pomiaru Bielika-4.5B-Instruct (tylko goła baza 4.5B: 31.7%).
  - Wynik (sob 23:00): **nie** w pierwotnej wersji: Bielik-4.5B-v3-Instruct Q4_K_M (2.88 GB) ma na historii Polski 31% vs Qwen3.5-4B Q4 49%; Q3_K_M Bielika się rozsypuje (7.6%). Bielik pisze lepsze eseje (27% vs 17%), ale jest większy od Qwen, a w T3 liczy się rozmiar — kierowanie esejów do niego zwiększyłoby rozwiązanie.
- [x] **H-N24 (P1) [E]** Klasyfikator „Polska / świat” bez modelu (reguły + pokrycie z bazą wiedzy Polski i świata) osiąga ≥ 90% zgodności z ręcznymi etykietami grup zadań 2024–2026.
  - Po co: router dla H-N23 i bramka RAG dla H-N21. Wariant zapasowy: klasyfikuje sam model główny (0 GB).
  - Wynik (sob 23:00): **nie** (82% < 90%). Reguły słów kluczowych na 74 ręcznie oznaczonych grupach 2024–2026: 82%; wersja ważona (Polska vs świat) 78%. Mylą się głównie tematy ogólne z pojedynczym polskim słowem i tematy polskie bez typowych słów (Jaruzelski, stan wojenny).
- [x] **H-N25 (P1) [E]** RAG bramkowany pewnością wyszukiwania (kontekst tylko, gdy wynik BM25 / pokrycie terminów przekracza próg) nie szkodzi dużym modelom i zachowuje zysk małych.
  - Tło: obecny RAG pomaga małym modelom (+6–8 pp), a dużym szkodzi albo nic nie daje; szkodzą nietrafione fragmenty.
  - Wynik (nd 00:15): **bez efektu** (w granicach szumu). PLLuM + LoRA v2 z RAG PolQA + baza: bez bramki 42.0%, z bramką BM25 ≥ 12 42.9%. Bramki nie włączamy.
- [x] **H-N26 (P1) [E]** Dane SFT wiernie odtwarzające wejście harnessu dają T2 ≥ +3 pp.
  - Co odtwarzamy: numerację jak w arkuszu (poprawione 20:15: wcześniej „Zadanie XL-0-b2”), blok „Materiały pomocnicze” z wynikami naszego wyszukiwarki (także z nietrafionymi fragmentami, RAFT), znaczniki `[Obraz: …]` jak w oficjalnym `source_text`, kompendium w kontekście eseju, dopisek o formacie przy zamkniętych.
  - Wynik (nd 01:00): **nie w tej postaci.** Dane v2 (numeracja jak w arkuszu, znaczniki obrazów, RAFT z kontekstem w 60% zadań otwartych, kompendium w eseju): 5 tys. / 1 epoka — 38.7%; ~10.5 tys. / 2 epoki — 40.0% bez RAG, 43.7% z RAG z bazy, 44.5% z RAG PolQA + baza. Ten sam RAG z adapterem uczonym przepisem v1 (bez kontekstu w danych) na tych samych zadaniach daje 52.9%. Wniosek: w T2 więcej zadań + RAG w ewaluacji działa lepiej niż uczenie korzystania z kontekstu. Numeracja zadań jak w arkuszu została w builderze (poprawka zgodności, bez osobnego pomiaru).
- [x] **H-N27 (P2) [E]** 2–3 tys. dodatkowych przykładów (luna, ~1–2 $), celowanych w słabe typy (dopasowanie, „rozstrzygnij”) i w historię Polski, dają T2 ≥ +2 pp.
  - Wynik (nd 00:15): **tak, zwłaszcza z RAG.** Przepis v1 (2 epoki, bez kontekstu w danych) na ~12 tys. przykładów (v1 + 8.7 tys. E5) zamiast 1.8 tys.: bez RAG 40.3% na 2024+2025 (v1: 41.2%) i 40.0% na 2026 (v1: 26.7%); z RAG PolQA top-3 + 1 notatka z bazy **52.9% i 41.7%** (v1 bez RAG: 41.2% i 26.7%). To nowe rozwiązanie T2: ~49% na trzech arkuszach wobec ~36% (+13 pp), przyrost względem gołej bazy ~+49 pp.
- [ ] **H-N14 (P1) [E]** Ocena organizatorów na mocku jest w ±5 pp od oceny lunki.
  - Sprawdzenie: oddać `runs/mock-2023/gemma4-qat-t1final/answers.json` (luna: 78.3%), gdy przyjdą link i `TEAM_KEY`.
  - Wynik:
