# 01 — Konkurs: cel i zasady

Stan na: pt 25.09.2026, ~24:00. **Koniec treningu: niedziela 27.09.2026, 11:00** (zostało ok. 35 h).

Źródła (od najnowszego / najbardziej wiążącego):
1. Twoja notatka (informacje z otwarcia hackathonu),
2. slajdy `assets/presentations/rules&faq.pdf` (otwarcie, pt 18:00),
3. aplikacja konkursowa `warsawmodeltrainers.dev/matura.html`,
4. strona `warsawmodeltrainers.dev` + `/rules` (starsza wersja, pisana przed otwarciem).

Tam, gdzie źródła się różnią, obowiązują slajdy i Twoja notatka. Rozbieżności są zebrane na końcu.

---

## 1. Cel

Hackathon **Warsaw Model Trainers** (AI Tinkerers × Kolektyw3, Koszykowa 54, Warszawa), hasło: *„Can a small model pass the matura?”*.

Zadanie: wziąć otwarty model (lub kilka modeli), każdy **≤ 8 GB na dysku**, i sprawić, żeby jak najlepiej zdał **maturę z historii na poziomie rozszerzonym** (dużo historii Polski, ale też historia powszechna). Można:
- fine-tunować (SFT, LoRA, QLoRA, dalszy pretrening),
- budować harness (system prompt, few-shot, chain-of-thought, RAG, agenci, narzędzia, pipeline wielu modeli),
- łączyć jedno i drugie.

## 2. Zasady (slajdy + notatka)

| Obszar | Zasada |
|---|---|
| Rozmiar modelu | Każdy model osobno **≤ 8 GB wag na dysku**, w wersji uruchamianej na egzaminie. Dowolna kwantyzacja (np. 12B skwantyzowany do 7 GB jest OK). Nie ma limitu łącznego — można użyć wielu modeli. |
| LoRA | Adapter LoRA **nie wlicza się** do limitu. |
| Baza RAG | Lokalna baza wiedzy **nie wlicza się** do 8 GB (np. cała Wikipedia). |
| Dane | Dowolne legalnie dostępne źródła, w tym dane syntetyczne z dowolnego LLM (także zamknięte API w trakcie budowania). Bez obchodzenia paywalli/logowań. |
| Egzamin | Model odpowiada **offline**, bez pomocy człowieka. **Zakaz internetu i zamkniętych API** (ChatGPT, Claude, Gemini itd.) w trakcie egzaminu. Lokalny RAG i narzędzia dozwolone. |
| Sprzęt na egzamin | Własny laptop albo maszyna w chmurze (też sponsorska). Zakaz dotyczy zewnętrznych API AI i wiedzy z internetu, nie fizycznej lokalizacji modelu. Brak limitów RAM/VRAM/CPU. **Praktyczny limit: czas na scenie — kilka minut na cały egzamin i prezentację.** |
| Model bazowy | Dowolne otwarte wagi, także już dotrenowane publicznie na historii — wtedy ich wynik jest benchmarkiem. Wolno zgłosić checkpoint pretrenowany (`-Base` / `-pt`), nie tylko `-Instruct` (H-R2, potwierdzone 26.09 ~15:30). Własny model dotrenowany przed hackathonem nie może udawać bazowego (dyskwalifikacja). Można zmienić model bazowy w trakcie; liczy się benchmark modelu, który podchodzi do egzaminu. |
| Własna praca | Oceniana praca musi powstać podczas hackathonu (od pt 18:00). Publiczne biblioteki i własne wcześniejsze narzędzia są OK. |
| Repozytorium | Kod treningu i harnessu, skrypty danych, lista źródeł, README pozwalające odtworzyć wynik. Publiczne albo prywatne z dostępem do odczytu dla organizatorów i jury **przed nd 11:00**. **Bez treści chronionych prawem autorskim** — zamiast tego lista linków + skrypt pobierający. |
| `SOURCE.md` | Obowiązkowy, z tekstem: „Made during the Warsaw Model Trainers hackathon, Kolektyw3, 25–27.09.2026”. Bez niego nie można wygrać nagrody. |
| Licencje | Kod: dowolna licencja. Wagi: licencja modelu bazowego. Dane z Wikipedii: CC BY-SA. Modele i dane z cudzych treści: tylko do celów edukacyjnych i badawczych. |

## 3. Trzy tracki (kategorie)

Według slajdu „Scoring” i Twojej notatki:

1. **Best matura score** — najwyższy wynik na finałowym arkuszu. Liczy się całe rozwiązanie (pipeline).
2. **Best progress** — największa różnica między Twoim rozwiązaniem a nietkniętym modelem bazowym.
   - Przy rozwiązaniu wielomodelowym **bazą jest ten model, który sam z siebie ma najwyższy wynik**, a wynik końcowy to cały pipeline.
   - Trzeba zgłosić wynik finałowego egzaminu **i dla modelu (modeli) bazowego, i dla wytrenowanego** — bez benchmarku nie ma udziału w tym tracku.
3. **„Mały, ale wariat”** — **najmniejszy model, który uzyska co najmniej 35%**.
   - Przy wielu modelach liczy się **tylko największy z nich**.
   - **Rozmiar mierzony w GB na dysku** (potwierdzone). Agresywna kwantyzacja bezpośrednio pomaga.
   - Plik `mmproj` jest osobnym plikiem: sam musi mieć < 8 GB i w T3 nie podnosi rozmiaru, jeśli jest mniejszy od LLM (H-R5). Wchodzi natomiast do sumy 8.8 GB (H-R7).
   - Embedder, reranker, OCR i enkoder obrazów to modele (H-R7, 26.09 ~15:30): w T3 każdy musi być mniejszy od głównego, w T2 nie podnoszą bazy, a **łącznie z głównym modelem (i LoRA) muszą mieć < 8.8 GB**. Indeks BM25 i teksty RAG się nie wliczają.

Pula nagród: **8 000 PLN** wspólnie dla zwycięzców różnych kategorii + nagrody Quesma (Tokenmaxxer, Token diversity) + 200 USD kredytów Cursor na uczestnika (zwycięzcy: dodatkowe 200 USD na osobę) + K3 Viber Passes (dostęp do biurek w Kolektyw3).

## 4. Harmonogram (pozostały)

| Kiedy | Co |
|---|---|
| **sob 26.09, 12:00** | **Deadline pełnego składu zespołu w aplikacji** (slajdy; strona mówi 16:00 — trzymaj się 12:00) |
| sob 12:00–18:00 | Sloty z mentorami (stoły: harness & ewaluacja / trening & dane). Mocno zalecane. |
| sob (w ciągu dnia) | Organizatorzy mają podać **skrypt egzaminacyjny i instrukcje** („Sunday submission — full details tomorrow”). |
| sob 9:00–24:00 | Lokal otwarty (w nocy zamknięty — trening w chmurze). |
| **nd 27.09, 10:45** | Losowanie kolejności prezentacji. |
| **nd 11:00** | **Stop treningu**, zamrożenie modelu i harnessu. Finałowy arkusz odblokowany dopiero wtedy (próba wcześniejszego zdobycia = dyskwalifikacja). Zgłoszenia problemów technicznych do 11:15. |
| nd 11:00– | Egzamin na żywo + prezentacja (2–3 min o problemach z treningu + 1–2 min pytań jury, PL lub EN). |
| nd 13:00 | Panel. |
| nd 14:00 | Wyniki i nagrody. |

## 5a. Proces testowania — oficjalny przewodnik (26.09, 14:00)

Źródło: [Matura testing process](https://matura-json-guide.ania-olchowik.chatgpt.site/) + README z paczki. Paczka próbna zapisana w `assets/mock-2023/`.

**Egzamin to plik, nie zapytania na żywo.** Skrypt nie odpytuje naszego modelu; sami uruchamiamy harness gdziekolwiek (laptop, Modal, serwer Forgehand) i oddajemy tylko odpowiedzi.

1. **Pobranie paczki:** `exam.json` (pytania i teksty źródeł), `images/` (osobne PNG), `answers-template.json` (wszystkie ID z pustymi odpowiedziami), `README.md`.
2. **Uzupełnienie szablonu:** dla każdego `id` wpisujemy odpowiedź (string, po polsku) i zapisujemy jako `answers.json`.
3. **Wysłanie:** na stronie zgłoszeń podajemy **TEAM_KEY i nazwę rozwiązania** (= osobne rozwiązania dla tracków) i wgrywamy `answers.json`. Link podają organizatorzy.
4. **Ocena:** organizatorzy oceniają **LLM-em według zasad CKE**, partiami **mniej więcej co 30 min** (może się wydłużyć). Przy wgrywaniu sprawdzany jest tylko format (exam_id, komplet ID, duplikaty, typy, rozmiar).

**Format `exam.json`** (`input_format: separate-text-and-images-v1`):
- poziom egzaminu: `exam_id`, `title`, `language`, `source_exam_id`, `source_url`, `max_points`, `instructions`, `items`;
- każde zadanie: `id` (string, np. „2.1”), `group`, `max_points`, `question`, `source_text` (teksty, tabele, transkrypcje skanów, znaczniki `[Obraz: images/Z01.png]`), `images` (`path`, `source_page`, `sha256`), **`answer_format`**;
- `answer_format` jednoznacznie wskazuje typ zadania:

  | Typ | `answer_format` |
  |---|---|
  | P/F | `1: P\n2: F\n3: P` |
  | jednokrotny wybór | `A` |
  | dopasowanie | `A: 1\nB: 1` |
  | kilka wyborów | `1: A\n2: A` |
  | otwarte | „Tekst po polsku. Podaj wszystkie wymagane elementy odpowiedzi.” |
  | esej | „Jeden tekst: numer wybranego tematu i całe wypracowanie. Minimum 300 wyrazów…” |

**Zasady pliku odpowiedzi:**
- tylko `exam_id` i `answers`, każde ID dokładnie raz i jako string;
- każda odpowiedź jest stringiem, także wybór i P/F;
- dozwolone `""` (brak odpowiedzi);
- bez rozumowania i logów czatu;
- esej w odpowiedzi „26” z numerem tematu;
- UTF-8, maks. 1 MiB, maks. 100 000 znaków na odpowiedź.

**Próbny egzamin:** matura maj 2023 (`history-2023-mock-v1`), 37 zadań, 60 pkt, 19 obrazów PNG (23 zadania z obrazem). To ten sam arkusz co w benchmarku, ale w nowym formacie z wyciętymi obrazami. **Można go oddawać i dostać ocenę prawdziwego sędziego** — najlepsza kalibracja naszego sędziego (H-E1). **Finał** to osobna paczka z własnym `exam_id`, zablokowana do czasu udostępnienia.

## 5. Jak wygląda egzamin (aplikacja konkursowa)

Z kodu strony `matura.html` wynika mechanika:
- Są dwa zestawy pytań: **`probny` (practice)** i **`finalny` (final)**. Pytania mają pola `id`, `type`, `question`, `points`.
- **Skrypt egzaminacyjny** uruchamiany z `TEAM_KEY` odpytuje Twój model i wysyła **tylko odpowiedzi**. Skrypt dostaniecie w sobotę.
- Widok „Live exam”: pytanie po pytaniu, zielone = poprawne, czerwone = błędne. Każda odpowiedź ma pola `given`, `correct` (tak/nie), `points`.
- **Ocena (potwierdzone): pytania otwarte i esej ocenia LLM-sędzia ze szczegółowymi kryteriami jak w CKE** (punkty częściowe, kryteria eseju). Model i dokładny prompt sędziego nie są znane — najbliższym przybliżeniem są metodyka i rekonstrukcja z raportu 02.
- **Obrazki i tekst przychodzą osobno (potwierdzone)**, tak żeby modele czysto tekstowe mogły odpowiedzieć przynajmniej na podstawie tekstu. Dokładny format (URL / base64 / plik) i `pytania-FORMAT.json` — jeszcze nieznane.
- Interfejs skryptu egzaminacyjnego (endpoint zgodny z OpenAI? funkcja w Pythonie?) i limity czasu na pytanie — jeszcze nieznane. Dopóki nie wiadomo, harness najbezpieczniej wystawić jako serwer zgodny z OpenAI (`/v1/chat/completions`) z cienką warstwą adaptera, którą łatwo podpiąć pod dowolny skrypt.
- Leaderboard: kolumny *Practice · base*, *Practice · best*, *Final · base*, *Final · tuned*, *Gain*. W czasie finału ranking: „by final score, then by gain over the untouched base model”.
- Wg `/rules`: próbne zgłoszenia max **raz na godzinę**, pytania losowane z dużej puli przy każdym zgłoszeniu. **Wyniki próbne się nie liczą**; strona z metodyką wspomina, że pula na stronie wydarzenia jest generowana z Wikipedii, więc może się różnić od arkusza maturalnego.
- W panelu organizatora jest opcja „Upload questions” w formacie `pytania-FORMAT.json` — format pytań finałowych będzie więc taki sam jak próbnych. Warto go poznać jak najwcześniej (prośba do organizatorów / Telegram).

## 6. Rozbieżności między źródłami (do potwierdzenia na Telegramie)

| Temat | Strona www / `/rules` | Slajdy / Twoja notatka | Co przyjmuję |
|---|---|---|---|
| Limit modelu | ≤ 12B parametrów | ≤ 8 GB na dysku, dowolna kwantyzacja, wiele modeli | 8 GB na dysku, per model |
| Punktacja | 40% wynik + 40% postęp + 20% prezentacja (jury), jeden ranking | 3 osobne tracki, wspólna pula | 3 tracki; jury i tak ocenia prezentacje (karta: czy wiecie, co zadziałało i dlaczego; jakość danych i metody; odtwarzalność) |
| Wielkość zespołu | do 4 osób | bez limitu | bez limitu |
| Deadline składu | sob 16:00 | sob 12:00 | **sob 12:00** |
| Przedmiot | historia | slajd 2 z benchmarków: „separate from the hackathon’s **geography** final” | historia (prawdopodobnie literówka na slajdzie — warto dopytać) |
| Track 3 — miara | brak | „najmniejszy model” | **GB na dysku (potwierdzone)**, liczy się tylko największy model |
| Format finałowego arkusza | brak | obrazki i tekst osobno | obrazki osobno od tekstu; układ jak CKE (esej ~15 pkt, te same typy zadań) — H-R9 |
| Ocena otwartych i eseju | brak | LLM-sędzia z kryteriami CKE | LLM-sędzia z kryteriami CKE (potwierdzone) |

## 7. Status pytań do organizatorów

| Pytanie | Odpowiedź | Status |
|---|---|---|
| Track 3: GB czy parametry? | GB na dysku; liczy się tylko największy model | potwierdzone |
| Czy `mmproj` wlicza się do rozmiaru? | osobny plik < 8 GB; w T3 liczy się największy plik, więc mniejszy mmproj nie podnosi rozmiaru; wchodzi do sumy 8.8 GB (H-R7) | potwierdzone |
| Format pytań z obrazkami, `pytania-FORMAT.json` | obrazki i tekst przychodzą osobno (modele text-only mogą odpowiedzieć na podstawie tekstu); format pliku nieznany | częściowo |
| Ocena otwartych pytań i eseju | LLM-sędzia ze szczegółowymi kryteriami jak w CKE; model i prompt nieznane | częściowo |
| Interfejs skryptu egzaminacyjnego, limity czasu na pytanie | **brak skryptu na żywo**: pobieramy `exam.json` + obrazy, generujemy `answers.json` gdziekolwiek i wgrywamy go z TEAM_KEY i nazwą rozwiązania (sekcja 5a) | potwierdzone (przewodnik) |
| Format pytań z obrazkami | tekst w `question` / `source_text`, obrazy jako osobne PNG w `images/`, typ zadania w `answer_format` | potwierdzone (przewodnik) |
| Czy zespół może mieć osobne rozwiązania dla tracków? | **tak — trzy osobne rozwiązania** | potwierdzone |
| Czy wolno zgłosić model `-Base` / `-pt` jako bazę? | **tak** | potwierdzone (26.09 ~15:30) |
| Embedder, reranker, OCR, enkoder obrazów | to modele: w T3 mniejsze od głównego, w T2 nie podnoszą bazy; **suma z głównym modelem < 8.8 GB** (LoRA w tej samej kopercie) | potwierdzone (26.09 ~15:30) |
| Struktura finałowego arkusza | jak CKE: te same typy zadań, esej ~15 pkt (~25%), część zadań z obrazami | potwierdzone (26.09 ~15:30) |
| Postęp: pp czy zysk względny? | **różnica w punktach procentowych** | potwierdzone |
| Czy `mmproj` wlicza się do rozmiaru LLM? | **nie** jako część pliku LLM — osobny plik < 8 GB; w T3 liczy się największy. Do sumy 8.8 GB z głównym modelem **tak** (H-R7) | potwierdzone |
| Czy LoRA wlicza się w T3? | ~~nie~~ → **nowy komunikat: baza ≤ 8 GB, po fine-tuningu ≤ 8.8 GB (+10%)**; bez „pompowania” (wyższa precyzja, kopie, głosowanie) | potwierdzone (26.09 ~14:30) |
| 8 GB = GB czy GiB? | **8·10⁹ bajtów**, pliki wag w formie uruchamianej | potwierdzone |
| Czy wynik bazowy liczy się bez harnessu? | **tak — goły model**, więc zysk z harnessu wlicza się do postępu | potwierdzone |

Konsekwencje dla przygotowań:
- W T2 wolno iść w wariant B1: pretrenowana baza (`-Base` / `-pt`) + nasz SFT. Postęp liczy się od gołego checkpointu.
- Jedna koperta **8.8 GB** obejmuje główny model, LoRA, embedder, reranker, OCR i enkoder obrazów. Przy Gemmie QAT zostaje 1.64 GB, przy PLLuM-12B-base 1.32 GB, przy Gemma-4-12B pt ~1.24 GB. Duży embedder (0.9–3 GB) przy tych bazach się nie mieści; BM25 (0 GB) i Tesseract (~0.015 GB) tak. Qwen3.5-9B z mmproj i zapasem na LoRA to Q5_K_M (zapas 1.30 GB), nie Q6_K (zapas 0.42 GB).
- W T3 suma jest daleko pod 8.8 GB. Wiąże „największy plik”: embedder, reranker, OCR i mmproj muszą być mniejsze od głównego LLM.
- Finał ma układ arkusza CKE (esej ~15 pkt, część zadań z obrazami), więc waga eseju i budżet punktów z DEV zostają.
- Model czysto tekstowy jest pełnoprawną opcją (dostanie tekst pytań), ale bez obrazków straci część punktów. Pytania z obrazkami, które w arkuszu 2023 dawały ok. połowy punktów, wymagają albo modelu multimodalnego, albo małego modelu opisującego obrazki (VLM → opis → LLM tekstowy). W tracku 3 taki VLM też musi być mniejszy od głównego modelu i zmieścić się w sumie 8.8 GB.
- Ponieważ ocenia LLM-sędzia z kryteriami CKE, obowiązują wnioski z raportu 02: jednoznaczna odpowiedź końcowa, bez asekuracji i sprzeczności, uzasadnienie z odwołaniem do źródła, esej wg schematu CKE (1 temat, 3 elementy z faktami, ≥ 300 słów, spójna struktura).
