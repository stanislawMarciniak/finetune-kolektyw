# 06 — Datasety i źródła danych

Stan na sob 26.09.2026. Dostępność sprawdzona przez API Hugging Face i stronę CKE; pozycje niezweryfikowane są oznaczone „do sprawdzenia”.

## 0. Najważniejsze wnioski

1. **Nie ma gotowego zbioru zadań maturalnych z historii.** Istniejące polskie zbiory egzaminacyjne (LLMzSzŁ, INCLUDE, `pawel04/*`) zawierają matematykę, fizykę, biologię i WOS, a historii praktycznie wcale. **Zbiór trzeba zbudować z arkuszy CKE** (ekstrakcja przez Gemini).
2. **Arkusze CKE z nowej formuły są dostępne za lata 2023, 2024, 2025 i 2026** (maj; arkusz + zasady oceniania, od 2024 także osobna karta). Maj 2026 najpewniej nie trafił do pretreningu modeli, więc to najczystszy test.
3. **Najcenniejszy gotowy korpus do RAG to PolQA** (`ipipan/polqa`, CC BY-SA 4.0): 7 mln pasaży polskiej Wikipedii już pociętych na fragmenty + 7 tys. pytań z ręcznie oznaczonymi pasażami (do oceny wyszukiwania).
4. **Najwięcej punktów dadzą dane syntetyczne**: odpowiedzi wzorcowe do zadań CKE (z kluczem), eseje wzorcowe filtrowane sędzią wg kryteriów CKE, przykłady RAFT i notatki „kompendium” wg wymagań egzaminacyjnych.
5. **Zasady repo:** treści chronionych (arkusze, podręczniki, cudze zbiory bez licencji) nie wrzucamy do repozytorium. Dajemy linki + skrypt pobierający. Dane z Wikipedii i pochodne publikujemy na CC BY-SA.

---

## 1. Egzaminy CKE — rdzeń danych

| Źródło | Zakres | Zawartość | Zastosowanie | Priorytet |
|---|---|---|---|---|
| **Matura z historii, formuła 2023** | maj 2023, 2024, 2025, 2026 (sprawdzone); terminy czerwcowe i sierpniowe — do sprawdzenia | arkusz, karta, zasady oceniania z przykładowymi rozwiązaniami, esej 15 pkt | **DEV (2023, 2024) i TEST (2025, 2026)**; format docelowy | **MUST** |
| Matura z historii, formuła 2015 (rozszerzona) | 2015–2022 (+ ew. 2023–2024 dla absolwentów starszych roczników), maj/czerwiec/sierpień | zadania ze źródłami (tekst, mapy, ikonografia), wypracowanie | **trening** (SFT, KB-CKE, tematy esejów) | **MUST** |
| Stara matura (przed 2015) | 2005–2014, także poziom podstawowy i próbne | zadania zamknięte i otwarte, wypracowania | trening, więcej tematów esejów | SHOULD |
| Informator o maturze z historii (od 2023) + aneks (zmiany od 2025) | 1 dokument + aneks | przykładowe zadania z rozwiązaniami, opis wymagań | trening + lista wymagań do kompendium | **MUST** |
| Próbne matury CKE (formuła 2023) | np. grudzień 2022 — do sprawdzenia | pełne arkusze z zasadami | trening albo dodatkowy dev | SHOULD |
| Sprawozdania CKE z egzaminu z historii | coroczne | analiza wyników, **przykłady odpowiedzi zdających z komentarzem** | dane do kalibracji sędziego i do DPO (dobre vs słabe odpowiedzi) | SHOULD |
| Egzamin gimnazjalny — część historia i WOS | 2012–2019 | setki zadań zamkniętych ze źródłami (teksty, ilustracje, mapy) | trening zadań zamkniętych, zwłaszcza dla małych modeli | SHOULD |
| Matura z WOS (formuła 2023 i 2015) | 2015–2026 | XX wiek, ustroje, konstytucje, PRL | trening dla słabego obszaru (XX w., PRL) | NICE |
| Matura z historii sztuki (formuła 2023) | 2023–2026 | dużo obrazów: style, dzieła, architektura | zadania obrazowe typu „styl / cecha stylu” (w 2023: zad. 7 i 15) | NICE |
| Materiały z benchmarku organizatorów | 2023 | wersja tekstowa (34 zad.) i obrazowa (37 zad.), ~900 ocen sędziego z uzasadnieniami | `DEV-2023` + **kalibracja sędziego** | **MUST** (już w `assets/benchmark-2023/`) |

**Adresy (formuła 2023):**
- archiwum: `https://cke.gov.pl/egzamin-maturalny/egzamin-maturalny-w-formule-2023/arkusze/` (podstrony `2024-2/`, `2025-2/`, `2026-2/`);
- pliki (od 2024): `…/Arkusze_egzaminacyjne/{rok}/Historia/MHIP-R0-100-A-{rr}05-arkusz.pdf`, `…-karta.pdf`, `MHIP-R0-100-{rr}05-zasady.pdf`;
- 2025: zasady w `…/2025/zasady_oceniania/`;
- 2023: `…/2023/Historia/MHIP-R0-100-2305.pdf` i `…-zasady.pdf`.

**Adresy (starsze):** formuła 2015 — `…/egzamin-maturalny-w-formule-2015/arkusze/`; stara formuła — `…/egzamin-w-starej-formule/arkusze/` (lata 2005–2020, podstrony per rok).

**Licencja:** arkusze są publicznymi materiałami CKE, ale zawierają źródła i ilustracje osób trzecich. Do repo trafia **tylko skrypt pobierający i ekstrahujący**, bez PDF-ów i bez wyekstrahowanych tekstów źródeł.

### Ekstrakcja (plan)

- Gemini z PDF na wejściu zwraca JSON na każde zadanie: `id, typ, polecenie, źródła (tekst), obrazy (bbox + podpis), punkty, klucz, zasady oceniania, przykładowe rozwiązanie`.
- Wycinki obrazów generujemy z bboxów (renderowanie strony w 200 dpi). Dzięki temu dostajemy format jak na finale: tekst osobno, obrazy osobno.
- Walidacja: suma punktów zgodna z arkuszem, liczba zadań zgodna, ręczny przegląd 2–3 arkuszy.
- Koszt: kilka dolarów za kilkadziesiąt arkuszy.

---

## 2. Istniejące datasety na Hugging Face (zweryfikowane)

| Dataset | Co zawiera | Licencja | Przydatność | Zastosowanie |
|---|---|---|---|---|
| **`ipipan/polqa`** | 7 tys. pytań (teleturniej „Jeden z dziesięciu”), 87.5 tys. ręcznie oznaczonych pasaży, **korpus 7 mln pasaży plwiki (2022)** | CC BY-SA 4.0 | **wysoka** | gotowy korpus do BM25/dense (KB-WIKI v0); ocena i trening wyszukiwania; test wiedzy modeli |
| `clarin-pl/poquad` | polski odpowiednik SQuAD (pytanie + fragment Wikipedii → odpowiedź) | do sprawdzenia | średnia | trening „odpowiadaj z kontekstu” dla małych modeli (uzupełnienie RAFT) |
| `enelpol/czywiesz`, `allegro/klej-dyk` | pytania „Czy wiesz…” z Wikipedii | do sprawdzenia | niska–średnia | test wiedzy faktograficznej, ocena wyszukiwania |
| `allegro/polish-question-passage-pairs` | pary pytanie–pasaż | do sprawdzenia | niska | trening/ocena embeddera |
| `CohereLabs/aya_dataset` (część polska) | instrukcje pisane przez ludzi | Apache 2.0 | średnia (T2-B1) | domieszka ogólnych instrukcji przy SFT modelu `-Base` |
| `JohnTdi/polish-llm-sft-pl`, `JohnTdi/bielik-distill-polish-10k` | ogólne polskie SFT / destylacja z Bielika | do sprawdzenia | średnia (T2-B1) | jak wyżej; sprawdzić jakość próbki przed użyciem |
| `Wojtekb30/llava-1.5-665k-instructions-Polish` | instrukcje wizualne po polsku (tłumaczenie LLaVA) | do sprawdzenia | niska–średnia | ewentualny SFT części wizualnej (T1/T3) |
| `Igorrr0/ABCD-polish-QA-with-CoT`, `Igorrr0/wikipedia-polish-qa` | polskie QA (częściowo z CoT) | do sprawdzenia | niska | tylko po ręcznej ocenie jakości |
| `amu-cai/llmzszl-dataset` (LLMzSzŁ) | 18.8 tys. pytań zamkniętych z egzaminów CKE; matura: matematyka, fizyka, biologia | brak w karcie | **brak historii** | nie używamy (ew. kontrola ogólnej polszczyzny) |
| `CohereLabs/include-base-44` / `dokato/exam-polish-matura` | 52 polskie pytania z matury (biologia, matematyka, WOS) | CC BY-NC-SA 2.0 | niska | ewentualnie mały test |
| `pawel04/otwarte-pytania-matura-cke`, `pawel04/llmzszl-open-ended` | pytania otwarte — matematyka | — | brak | nie używamy |
| `PleIAs/Polish-PD` | polskie teksty z domeny publicznej | PD | niska–średnia | źródła historyczne do pytań syntetycznych, CPT |
| `SlayerLab/polish-dynaword` | otwarcie licencjonowany korpus polski | do sprawdzenia | niska | CPT (tylko jeśli starczy czasu) |
| `hakari-bench/NanoMTEB-Polish` | mały benchmark wyszukiwania | do sprawdzenia | niska | szybki wybór embeddera |

---

## 3. Korpusy wiedzy (RAG / ewentualny CPT)

| Źródło | Rozmiar / forma | Licencja | Zastosowanie | Priorytet |
|---|---|---|---|---|
| **Polska Wikipedia** | `wikimedia/wikipedia` (konfiguracja `20231101.pl`), `chrisociepa/wikipedia-pl-20230401`, świeży dump `dumps.wikimedia.org/plwiki/latest/` | CC BY-SA | KB-WIKI (całość albo podzbiór historyczny wg kategorii / Wikidata) | **MUST** (albo korpus PolQA) |
| **Wikidata** | dump albo zapytania SPARQL | CC0 | TIMELINE: władcy + lata panowania, bitwy, traktaty, powstania, daty urodzin i śmierci | SHOULD |
| **Wikiźródła (plwikisource)** | dump | PD / CC BY-SA | teksty źródłowe (konstytucje, traktaty, odezwy, manifesty) → pytania w stylu CKE „na źródle” | SHOULD |
| **ZPE — zpe.gov.pl** (e-podręczniki MEN) | lekcje zgodne z podstawą programową | licencje CC per zasób — **sprawdzić przed użyciem** | treści zgodne z oczekiwaniami egzaminu; sędzia z benchmarku sprawdzał fakty właśnie tam | SHOULD (jeśli licencja pozwala) |
| **Wikimedia Commons + WIT** (`google/wit`, `wikimedia/wit_base`) | obrazy z podpisami i opisami z Wikipedii (jest część polska) | różne wolne licencje | KB-IMG (dopasowanie obrazu z egzaminu do znanego dzieła), dane do zadań obrazowych | NICE |
| English Wikipedia | dump | CC BY-SA | historia powszechna tam, gdzie polska Wikipedia jest uboga | NICE |
| `HuggingFaceFW/fineweb-2` (`pol_Latn`), `HPLT/HPLT2.0_cleaned` (`pol_Latn`) | setki GB tekstu z sieci | ODC-By / CC0 | CPT po filtrze tematycznym — raczej poza budżetem czasu | NICE |
| Encyklopedia PWN, podręczniki komercyjne, portale muzealne i IPN | — | prawa autorskie / regulaminy | **nie używamy** (ewentualnie linki w materiałach) | — |

Praktyczna uwaga: polska fleksja psuje BM25 bez normalizacji słów. Potrzebny jest lematyzator (Morfeusz2, spaCy `pl_core_news_*`), stemmer (pystempel) albo indeks na n-gramach znakowych. To trzeba zmierzyć na zadaniach z DEV (H-H2).

---

## 4. Dokumenty programowe (do planowania danych syntetycznych)

| Dokument | Po co |
|---|---|
| Podstawa programowa historii dla liceum (zakres podstawowy i rozszerzony, z późniejszymi zmianami) | lista zagadnień, które muszą być pokryte w kompendium i pytaniach syntetycznych |
| Wymagania egzaminacyjne 2023–2024 i od 2025 (rozporządzenie + aneks do informatora) | dokładny zakres egzaminu; każde wymaganie = 1 notatka kompendium + kilka pytań |
| Zasady oceniania z arkuszy (wszystkie lata) | szablony punktacji; kryteria eseju (narracja 0–12, spójność 0–3) do sędziego i do generowania esejów |

---

## 5. Dane syntetyczne do wygenerowania

Nauczyciele: Gemini Flash do generowania masowego, Gemini Pro albo GPT do esejów i sędziowania. Każdy zbiór ma filtr jakości i filtr kontaminacji wobec DEV/TEST.

| Zbiór | Cel | Z czego | Liczba | Tracki | Priorytet |
|---|---|---|---|---|---|
| **SYN-CKE-ANS** | odpowiedzi wzorcowe w formacie egzaminu | zadania CKE (trening) + klucz + przykładowe rozwiązanie → nauczyciel pisze idealną, zwięzłą odpowiedź | 2–4 tys. | T1 (LoRA), T2, T3 | **MUST** |
| **SYN-ESSAY** | eseje 13–15/15 | tematy z archiwum CKE (~100) + tematy syntetyczne z wymagań w formule „Zajmij stanowisko… uwzględniając trzy…” (500–1000) → esej z faktami z RAG → sędzia (kryteria CKE) → zostają ≥ 13/15 | 1–2 tys. | T1, T2, T3 | **MUST** |
| **SYN-ESSAY-SECT** | eseje w formacie sekcyjnym (wstęp z tezą / 3 akapity / zakończenie) | jak wyżej, ze sztywną strukturą | 0.5–1 tys. | T3 | **MUST** (T3) |
| **SYN-RAFT** | korzystanie z kontekstu RAG | pytanie + 2–4 pobrane pasaże (w tym mylące) → odpowiedź oparta na właściwym pasażu | 3–5 tys. | T2, T3 | SHOULD |
| **SYN-CKE-Q** | więcej zadań w stylu CKE | pasaże z Wikipedii / Wikiźródeł / kompendium → pytania wg rozkładu typów CKE (wybór, P/F, dopasowanie, rozstrzygnij-uzasadnij, wyjaśnij) + klucz; weryfikacja przez drugiego nauczyciela | 5–10 tys. | T2, T3 | SHOULD |
| **KB-KOMPENDIUM** | precyzyjna baza wiedzy | 1 notatka (400–800 słów) na wymaganie egzaminacyjne: fakty, daty, pojęcia, przyczyny i skutki, typowe pułapki | 1–3 tys. | wszystkie | **MUST** |
| **TIMELINE** | chronologia | Wikidata + Wikipedia, weryfikacja krzyżowa | 2–5 tys. wierszy | wszystkie (esej, P/F) | SHOULD |
| **SYN-DPO** | preferencje | pary: esej dobry vs z błędami merytorycznymi / < 300 słów / wiele tematów; odpowiedź jednoznaczna vs asekurująca / sprzeczna | 1–2 tys. | T2, T3 (opcjonalnie) | NICE |
| **SYN-IMG** | zadania obrazowe | wycinki obrazów z arkuszy (trening) + obrazy z Commons → opis, OCR, pytanie + odpowiedź | 1–3 tys. | T1, T3 | NICE |
| **GEN-PL** | zachowanie ogólnych umiejętności | część polska `aya_dataset` / `JohnTdi/*` / syntetyczne | 1–2 tys. (10–20% miksu) | T2-B1 | SHOULD (T2-B1) |

### Budżet generowania — Forgehand LLM API (49.51 $, stan 26.09 14:10)

Ceny wyprowadzone z realnego kosztu kalibracji: 208 ocen = 0.49 $, czyli ok. 0.001 $ na ocenę lunnym i 0.004 $ sol. Efektywnie: luna ok. 0.4 $/M wejście i 2.5 $/M wyjście, sol ok. 2 $/M i 12 $/M. To szacunek z jednego pomiaru — potwierdzić w panelu po pierwszej partii ~100 przykładów.

| Rodzaj przykładu | Tokeny (wej. / wyj.) | Koszt `gpt-6-sol` | Koszt `gpt-6-luna` | Ile za 10 $ (sol / luna) |
|---|---|---|---|---|
| Wzorowa odpowiedź do zadania CKE (z kluczem) | ~1 800 / ~500 | ~0.010 $ | ~0.002 $ | ~1 000 / ~5 000 |
| Nowe zadanie w stylu CKE + klucz + odpowiedź (z pasażu) | ~1 000 / ~1 000 | ~0.014 $ | ~0.003 $ | ~700 / ~3 300 |
| Esej wzorcowy (plan + ~600 słów) | ~1 000 / ~2 000 | ~0.026 $ | ~0.005 $ | ~380 / ~2 000 |
| Weryfikacja przykładu sędzią (luna) | ~1 800 / ~150 | — | ~0.001 $ | — / ~10 000 |

Proponowany podział 49.5 $:

| Pozycja | Budżet | Wynik |
|---|---|---|
| Eseje wzorcowe (`gpt-6-sol`, jakość ma znaczenie) | 13 $ | ok. 500 esejów |
| Wzorowe odpowiedzi do zadań CKE ze starszych formuł (`gpt-6-luna`) | 8 $ | ok. 4 000 odpowiedzi — więcej niż jest zadań, więc z zapasem |
| Nowe zadania w stylu CKE z Wikipedii / kompendium (`gpt-6-luna`) | 10 $ | ok. 3 000 zadań |
| Weryfikacja wszystkich przykładów (`gpt-6-luna`) | 8 $ | ok. 8 000 ocen |
| Rezerwa na ocenianie przebiegów w niedzielę | 10 $ | ok. 10 000 ocen lunnym albo ~1 100 esejów przez sol |
| **Razem** | **49 $** | **ok. 7 500 przykładów SFT** (LoRA potrzebuje 3–10 tys.) |

Ograniczenie: API przyjmuje tylko tekst. Zadania z obrazami opisujemy tekstem albo generujemy nauczycielem **Gemma-4-12B-it na serwerze L40S** (widzi obrazy, jest darmowa poza czasem GPU).

### Zasady generowania (w skrócie)

- **SYN-CKE-ANS:** nauczyciel dostaje polecenie, źródła, klucz i przykładowe rozwiązanie; ma napisać odpowiedź, która dostałaby maksimum punktów, w formacie polecenia, bez asekuracji, z odwołaniem do źródła, jeśli jest wymagane. Potem sędzia sprawdza, czy odpowiedź dostaje maksimum; jeśli nie — odrzucamy.
- **SYN-ESSAY:** najpierw plan (teza, 3 elementy, 3–5 faktów na element z datami i terminologią), potem esej 450–650 słów, potem sędzia z rozbiciem na elementy. Fakty sprawdzamy w TIMELINE/RAG, a esej z jakimkolwiek błędem merytorycznym odrzucamy (każdy błąd kosztuje punkty).
- **Rozkład typów** w pytaniach syntetycznych odtwarzamy z arkuszy formuły 2023: ~20% zamkniętych, ~55% otwartych, esej osobno.
- **Kontaminacja:** usuwamy przykłady z n-gramowym lub semantycznym podobieństwem do zadań z DEV/TEST.
- **Koszt łączny:** szacunkowo 30–80 $ w Gemini + do 60 $ w OpenAI.

---

## 6. Zbiory ewaluacyjne — podział i reguły

| Zbiór | Skład | Reguła |
|---|---|---|
| `DEV-2023` | CKE maj 2023 (tekst i obrazy) | porównanie z benchmarkiem; może być skażony |
| `DEV-2024` | CKE maj 2024 | główny dev do codziennych decyzji |
| `TEST-2025`, `TEST-2026` | CKE maj 2025, maj 2026 | **tylko na bramkach**; nigdy w treningu, KB-CKE ani few-shot |
| `DEV-PRACTICE` | pytania z własnych przebiegów próbnych (zestaw *practice*) | styl finału; bez prób dostępu do zestawu finałowego |
| `CALIB` | ~900 ocen sędziego z benchmarku | tylko do kalibracji sędziego |
| `PROBE-KNOW` | zamknięte pytania CKE (trening) + próbka PolQA / „Czy wiesz” | test wiedzy modeli `-Base` metodą log-likelihood |

Opcja na koniec (nd rano): ostatni trening **z włączeniem** DEV/TEST. Daje więcej danych, ale od tego momentu nie mamy już czystego testu. Robimy to tylko wtedy, gdy wcześniejsza wersja jest już zmierzona i zamrożona jako plan awaryjny.

---

## 7. Modele pomocnicze do RAG i obrazów

To modele w rozumieniu zasad (H-R7, potwierdzone 26.09 ~15:30):
- w T3 każdy musi być **mniejszy od głównego** (liczy się największy plik);
- w T2 nie podnoszą bazy, bo same nie zdają egzaminu;
- **suma z głównym modelem i LoRA < 8.8 GB.** Przy Gemmie QAT zostaje 1.64 GB, przy PLLuM-12B-base 1.32 GB, przy Gemma-4-12B pt ~1.24 GB — duży embedder (0.9–3 GB) się nie mieści. BM25 ma 0 GB i się nie wlicza.

Rozmiary „~” to szacunek dla FP16.

| Rola | Model | ~Rozmiar | Uwagi |
|---|---|---|---|
| Wyszukiwanie bez modelu | BM25 (`bm25s`, Pyserini, Tantivy) + lematyzacja | 0 | pierwszy wybór dla T3 |
| Embedder PL (mały) | `sdadas/mmlw-retrieval-e5-small`, `intfloat/multilingual-e5-small` | ~0.24 GB | mieści się pod Qwen3.5-0.8B tylko po kwantyzacji / ONNX-int8 |
| Embedder PL (średni) | `sdadas/mmlw-retrieval-roberta-base`, `ipipan/silver-retriever-base-v1.1` | ~0.25 GB | dobre wyniki na polskich zbiorach |
| Embedder PL (duży) | `sdadas/mmlw-retrieval-roberta-large(-v2)`, `sdadas/stella-pl-retrieval(-mini)-8k` | ~0.9–3 GB | nie mieści się w kopercie 8.8 GB obok bazy ~7 GB (H-R7) |
| Embedder wielojęzyczny | `google/embeddinggemma-300m`, `Qwen/Qwen3-Embedding-0.6B`, `BAAI/bge-m3` | ~0.6 / 1.2 / 1.1 GB | przy bazie ~7 GB tylko najmniejszy, i tylko gdy zostaje zapas po LoRA |
| Reranker | `sdadas/polish-reranker-roberta-v3`, `BAAI/bge-reranker-v2-m3`, `Qwen/Qwen3-Reranker-0.6B` | ~0.3–1.2 GB | tylko jeśli poprawia wynik końcowy |
| OCR | Tesseract (`pol`, tessdata_best) | ~0.015 GB | napisy na monetach, mapach, plakatach (T3) |
| Enkoder obrazów | SigLIP2-base | ~0.4 GB | KB-IMG: dopasowanie do obrazów z Commons |

---

## 8. Licencje i zasady repozytorium

- **Do repo:** kod, prompty, konfiguracje, skrypty pobierające i przetwarzające, lista źródeł z linkami, zbiory pochodne z Wikipedii (CC BY-SA), własne dane syntetyczne (z adnotacją o modelu-nauczycielu).
- **Poza repo (tylko skrypt):** PDF-y CKE i wyekstrahowane z nich teksty źródeł, materiały ZPE (chyba że licencja pozwala), cudze datasety bez jasnej licencji.
- **Wagi:** licencja modelu bazowego. Sprawdzone w kartach modeli: Gemma 4, Qwen3.5, Bielik v3 (w tym `-Base` i `Bielik-PL-11B-v3.0`) i PLLuM-12B-2512 (instruct i base) mają **Apache 2.0**. Modele Bielika są „gated” (automatyczna akceptacja): przed pobraniem trzeba się zalogować na HF i zaakceptować warunki — zrób to od razu, nie w nocy przed treningiem. Modele i dane z treści osób trzecich — tylko do celów edukacyjnych i badawczych.

---

## 9. Kolejność budowy

| Kolejność | Zbiór / zasób | Szac. czas | Blokuje |
|---|---|---|---|
| 1 | pobranie arkuszy CKE + ekstrakcja (2023–2026 najpierw) | 2–3 h (w tle) | DEV/TEST, SYN-CKE-ANS |
| 2 | KB-WIKI v0 (korpus PolQA albo Wikipedia) + BM25 | 1–2 h (w tle) | RAG we wszystkich trackach |
| 3 | kalibracja sędziego na `CALIB` | 1–2 h | wszystkie decyzje |
| 4 | SYN-CKE-ANS + SYN-ESSAY (pierwsze 1–2 tys.) | 2–4 h (API) | pilot SFT |
| 5 | KB-KOMPENDIUM | 2–3 h (API) | RAG v1 |
| 6 | formuła 2015 + stara matura + gimnazjum → trening i KB-CKE | 3–4 h (w tle) | SFT S1 |
| 7 | SYN-RAFT, SYN-ESSAY-SECT | 2 h (API) | SFT T3 |
| 8 | TIMELINE, SYN-CKE-Q | 2–3 h | esej, P/F |
| 9 | SYN-DPO, SYN-IMG, KB-IMG | stretch | — |
