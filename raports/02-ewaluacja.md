# 02 — Ewaluacja: jak oceniano modele (z dokładnymi promptami)

Źródło: strona z metodyką benchmarku [warsaw-matura-method.ania-olchowik.chatgpt.site](https://warsaw-matura-method.ania-olchowik.chatgpt.site/) (Ania Olchowik, mentorka i jurorka), jej pliki `methodology.md` i pliki JSON z wynikami (`*.json`, `*.reviews.json`), oficjalne zasady oceniania CKE oraz slajdy `benchmarks&examples.pdf`.

Kopie surowych materiałów są w `assets/benchmark-2023/` (lista na końcu).

> **Najważniejsze zastrzeżenie.** Strona **nie publikuje dosłownego promptu AI-sędziego** (gradera). Przeszukałem wszystkie podstrony HTML, `methodology.md`, wszystkie pliki JSON z odpowiedziami i ocenami oraz skrypty JS obu stron — takiego tekstu tam nie ma. Opublikowane są:
> - **dokładne prompty podawane modelom** (systemowy + wiadomość użytkownika, także wyrenderowane szablony czatu),
> - **reguły oceniania** zapisane w metodyce,
> - **oficjalny klucz CKE**, do którego sędzia porównywał odpowiedzi,
> - **ustrukturyzowane uzasadnienia sędziego** dla każdego zadania (z tych pól da się odtworzyć procedurę).
>
> Niżej są te elementy dosłownie oraz **zrekonstruowany prompt sędziego** (wyraźnie oznaczony jako rekonstrukcja) do lokalnej ewaluacji.
>
> Dodatkowo: benchmark na stronie jest **propozycją metodyki** („proposal for discussion”). Potwierdzone przez organizatorów: na finale **pytania otwarte i esej ocenia LLM-sędzia ze szczegółowymi kryteriami jak w CKE**. Nie wiadomo, czy to ten sam sędzia i prompt co w benchmarku, dlatego reguły z tego raportu to najlepsze dostępne przybliżenie.

---

## 0. Aktualizacja: oficjalny proces oceny (26.09)

- Organizatorzy oceniają `answers.json` **LLM-em według zasad CKE**, partiami mniej więcej co 30 min. Przy wgrywaniu sprawdzają tylko format.
- Wejście to `exam.json` w formacie `separate-text-and-images-v1` (raport 01, sekcja 5a). Obrazy są **wycięte** (nie całe strony), skany tekstu mają transkrypcje, a pole `answer_format` podaje wymaganą składnię dla zamkniętych.
- Próbny egzamin (maj 2023, 37 zadań / 60 pkt) można oddać wiele razy pod różnymi nazwami rozwiązań i dostać **ocenę prawdziwego sędziego**. Pozwala to skalibrować nasz lokalny proces (`gpt-6-sol` 98% / `gpt-6-luna` 95% zgodności z sędzią benchmarku) z sędzią finałowym.
- Konsekwencje:
  - odpowiedzi zamknięte zapisujemy **dokładnie w składni `answer_format`**;
  - odpowiedź zawiera tylko wynik końcowy, bez myślenia;
  - esej zawiera numer tematu.

## 1. Arkusz testowy

- **CKE, matura z historii, poziom rozszerzony, 18 maja 2023** (arkusz MHIP-R0-100-2305). 180 minut, 26 numerowanych zadań, **60 pkt**.
- Polskie polecenia, polskie odpowiedzi. Sprawdza wiedzę historyczną, analizę źródeł i dłuższą argumentację.
- Dwie wersje benchmarku:

| | Wersja tekstowa | Wersja z obrazami stron |
|---|---|---|
| Liczba zadań | 34 punktowane pozycje | 37 punktowanych pozycji |
| Punkty | **55** (usunięte zad. 7, 8, 15 = 5 pkt) | **60** |
| Źródła | przepisane teksty i tabele + **stałe polskie opisy obrazków** | całe strony PDF jako PNG (200 dpi) |
| Polecenie | numer zadania i polecenie jako tekst | numer zadania i polecenie jako tekst |

Usunięte z wersji tekstowej: **7** (style architektoniczne, 2 pkt), **8** (rycina reformacyjna, 2 pkt), **15** (styl obrazu, 1 pkt) — opis albo gubiłby kluczowe dowody, albo podpowiadał odpowiedź.

Zasady opisów obrazków: opisywać to, co widać (napisy, daty, obiekty, położenie, relacje), **bez interpretacji** — bez nazw stylów, nazwisk postaci i rozwiązań z klucza. Wszystkie modele dostają te same zamrożone opisy (z sumą kontrolną SHA-256).

### Podział punktów

| Kategoria | Tekst | Obrazy |
|---|---|---|
| Zamknięte (7 pozycji: 2.2, 3, 10, 11.2, 13.2, 19, 21) | 11 | 11 |
| Otwarte (bez eseju) | 29 | 34 |
| Esej (zad. 26) | 15 | 15 |
| **Razem** | **55** | **60** |

Wynik = zdobyte punkty ÷ 55 (lub 60) × 100%. Esej raportowany osobno, żeby nie maskował słabych krótkich odpowiedzi.

Dodatkowe podzbiory (liczone z tych samych odpowiedzi, nie osobne przebiegi): „originally text only” — zadania 2, 6, 11, 12, 16, 22, 23, 25, 26 (13 pozycji, 28 pkt); „text only + data table” — to samo plus zad. 10 (14 pozycji, 30 pkt).

### Typy pytań (z przykładami ze slajdów)

| Typ | Obrazek? | Przykład (zadanie) | Oczekiwana odpowiedź |
|---|---|---|---|
| Jednokrotny wybór | czasem w źródłach | 11.2: który akt zniósł liberum veto? A Sejm Niemy, B Prawa kardynalne, C Sejm Wielki, D Uniwersał połaniecki | C |
| Dopasowanie (A/B ↔ 1/2/3) | nie (w tym arkuszu) | 2.2: A. rada byłych archontów, B. najniższa grupa bez praw obywatelskich → fragment 1/2/3 | A–3, B–2 (1 pkt tylko za oba) |
| Prawda/fałsz | czasem (mapa, tabela) | 3: „Korsyka stała się rzymska po II wojnie punickiej” (mapa) | F (po I wojnie punickiej) |
| P/F z tabeli danych | tabela | 10: „Podatki nadzwyczajne miały największy udział w czasie potopu” | F (87,5% w ostatnim okresie) |
| Krótka identyfikacja | często | 14.1: nazwisko osoby na monecie | Łukasiewicz |
| Rozstrzygnięcie + uzasadnienie | czasem | 1: paleolit czy neolit? uzasadnij ilustracją | neolit; stałe domy = osiadły tryb życia |
| Wyjaśnienie / porównanie | czasem | 18: karykatura „Duch roku ’76” (1917) — przesłanie, 2 detale, tytuł; 6: porównaj dwie opinie o Łokietku | USA spłaca dług wobec Francji (Lafayette, 1776), wejście do I wojny; 1 podobieństwo + 1 różnica |
| Esej | nie | 26: wybierz 1 z 3 tematów, min. 300 słów | 15 pkt wg kryteriów CKE (niżej) |

Formy źródeł w arkuszu: mapy i plany (zad. 3, 4, 13, 19), ilustracje/sztuka/zdjęcia/moneta/karykatury (1, 5, 7, 8, 14, 15, 17, 18, 20, 24), drzewa genealogiczne (5, 9), skan dokumentu (21), tabela statystyczna (10), tylko tekst (2, 6, 11, 12, 16, 22, 23, 25, 26).

---

## 2. Dokładne prompty podawane modelom

Każde zadanie idzie w **osobnym, świeżym kontekście**, z kompletem źródeł danej grupy zadań. Bez narzędzi, wyszukiwania i dostępu do klucza. Używany jest natywny szablon czatu modelu.

### 2.1 Prompt systemowy — wersja tekstowa (dosłownie)

```text
Rozwiąż zadanie z historii po polsku. Otrzymujesz tekst źródeł, a obrazy zastąpiono opisami. Wykorzystaj źródła i własną wiedzę zgodnie z poleceniem. Udziel tylko odpowiedzi na podane zadanie. Nie dopisuj innych zadań. Nie masz dostępu do narzędzi ani internetu.
```

### 2.2 Prompt systemowy — wersja z obrazami stron (dosłownie)

```text
Rozwiąż zadanie z historii po polsku. Otrzymujesz obrazy oryginalnych stron arkusza ze źródłami i poleceniami. Wykorzystaj widoczne źródła i własną wiedzę zgodnie z poleceniem. Udziel tylko odpowiedzi na wskazane zadanie. Inne zadania widoczne na tych samych stronach pomiń. Nie masz dostępu do narzędzi ani internetu.
```

### 2.3 Wiadomość użytkownika

Wersja tekstowa: `Zadanie {id} ({max_points} pkt)\n\n{źródła}\n\n{polecenie}`. Przykład (zad. 1, dosłownie):

```text
Zadanie 1 (1 pkt)

Ilustracja przedstawiająca rekonstrukcję zabudowań
[Opis źródła Z01]
Ilustracja przedstawia skupisko przylegających do siebie, prostokątnych budynków o jasnobrązowych ścianach i płaskich dachach. Dachy znajdują się na różnych wysokościach. W dachach widać kwadratowe otwory, a przy ścianach i otworach stoją drabiny. Niektóre ściany pokazano w przekroju. W odsłoniętych wnętrzach znajdują się naczynia, podwyższenia przy ścianach i zaokrąglone konstrukcje z otworami. Widoczne są belki podtrzymujące dachy. Na ścianie jednego z wnętrz znajdują się ornamenty i wystające elementy przypominające rogi. Między częściami zabudowy występują niewielkie otwarte przestrzenie.

Rozstrzygnij, czy przedstawiona rekonstrukcja dotyczy epoki paleolitu czy neolitu.
Odpowiedź uzasadnij, odwołując się do ilustracji i własnej wiedzy.
Rozstrzygnięcie:
Uzasadnienie:
```

Wersja obrazowa: najpierw obraz(y) stron, potem `Zadanie {id} ({max_points} pkt)\n\n{polecenie}` (bez przepisanych źródeł).

Esej (zad. 26, dosłownie, w obu wersjach):

```text
Zadanie 26 (15 pkt)



Zadanie zawiera trzy tematy. Wybierz jeden z nich do opracowania. Twoja wypowiedź
powinna liczyć minimum 300 wyrazów.
1. W życiu politycznym państwa polskiego w okresie XI–XII wieku dominowały tendencje
decentralizacyjne. Zajmij stanowisko wobec powyższej tezy i je uzasadnij, uwzględniając
w swojej argumentacji panowanie trzech wybranych władców z tego okresu.
2. Rewolucja amerykańska i francuska z końca XVIII wieku miały podobne przyczyny. Zajmij
stanowisko wobec powyższej tezy i je uzasadnij, uwzględniając w swojej argumentacji
aspekt polityczny, społeczno-gospodarczy i kulturowy.
3. Zimna wojna osiągnęła apogeum w latach 50. XX wieku. Zajmij stanowisko wobec
powyższej tezy i je uzasadnij, charakteryzując trzy wybrane wydarzenia z tego okresu.
```

### 2.4 Modyfikacje promptu zależne od modelu (dosłownie z danych przebiegów)

- **Gemma 3 (1B, 4B)** — brak roli systemowej, więc prompt systemowy doklejany dosłownie na początek pierwszej wiadomości użytkownika.
- **Gemma 4 12B** (tryb myślenia) — szablon wstawia `<|think|>` w turze systemowej:
  ```text
  <bos><|turn>system
  <|think|>
  Rozwiąż zadanie z historii po polsku. Otrzymujesz obrazy oryginalnych stron arkusza (...) Nie masz dostępu do narzędzi ani internetu. <turn|>
  <|turn>user
  <|image|>Zadanie 1 (1 pkt)
  (...)<turn|>
  <|turn>model
  ```
- **InternVL3.5-8B** — do promptu systemowego dopisany oficjalny „InternVL Thinking System Prompt”:
  ```text
  You are an AI assistant that rigorously follows this response protocol:

  1. First, conduct a detailed analysis of the question. Consider different angles, potential solutions, and reason through the problem step-by-step. Enclose this entire thinking process within <think> and </think> tags.

  2. After the thinking section, provide a clear, concise, and direct answer to the user's question. Separate the answer from the think section with a newline.

  Ensure that the thinking process is thorough but remains focused on the query. The final answer should be standalone and not reference the thinking section.
  ```
- **SmolLM3-3B** — szablon dodaje nagłówek:
  ```text
  ## Metadata

  Knowledge Cutoff Date: June 2025
  Today Date: 22 September 2026
  Reasoning Mode: /think

  ## Custom Instructions

  Rozwiąż zadanie z historii po polsku. (...)
  ```
- **Qwen3 / Qwen3.5 / Qwen3-VL-Thinking** — myślenie włączane natywnym szablonem (`enable_thinking`); ocenia się tylko tekst po `</think>`.
- **Pozostałe** (Bielik, PLLuM, Phi-4-mini, Llama 3.2, Qwen3-4B-Instruct-2507, LLaVA-*, Ministral) — natywna rola systemowa, bez zmian.

### 2.5 Ustawienia generowania

| Wersja | Limity tokenów | Dekodowanie | Kontekst |
|---|---|---|---|
| **v0.1** (pierwsze przebiegi) | 2048 tokenów na krótkie zadanie / 4096 na esej, **łącznie z myśleniem** | greedy, seed 42, BF16, batch 1 | 8192 |
| **v0.2** (od 22.09) | osobno: myślenie do 8192 (esej 16384) + odpowiedź końcowa do 2048 (esej 4096) | modele z myśleniem: sampling wg zaleceń producenta (np. Qwen3.5: T=1.0, top_p 0.95, top_k 20; Gemma 4: T=1.0, top_p 0.95, top_k 64; Qwen3 / SmolLM3 / InternVL: T=0.6); modele bez myślenia: greedy | 32768 |

Zasady v0.2: licznik odpowiedzi końcowej startuje od faktycznego znacznika końca myślenia. Gdy myślenie wyczerpie limit przed odpowiedzią — **brak odpowiedzi = 0 pkt** (bez wymuszania `</think>`, bez naprawiania, bez ponawiania). Odpowiedzi ucięte limitem są oceniane tak, jak zostały wygenerowane (oznaczane flagą).

Wniosek z pilota budżetów (Qwen3-VL-2B-Thinking, 5 zadań): przy greedy model kończył myślenie tylko w 1/5 zadań, przy samplingu w 5/5. Małe modele z myśleniem często nie zdążają z odpowiedzią — w pełnym przebiegu tekstowym tego samego modelu 21 z 34 zadań skończyło się bez odpowiedzi końcowej (a w obrazowym 30 z 37).

---

## 3. Zasady oceniania

### 3.1 Reguły ogólne (z metodyki)

- Punktacja wg **oficjalnego klucza CKE** dla każdego zadania, z zachowaniem punktów częściowych. Nagłówek klucza CKE: *„Akceptowane są wszystkie odpowiedzi merytorycznie poprawne i spełniające warunki zadania.”*
- **Zamknięte**: sprawdzane deterministycznie, gdy odpowiedź jest jednoznaczna. Nieczytelny format idzie do przeglądu, nie dostaje automatycznie 0.
  - 2.2: 1 pkt tylko za **oba** dopasowania.
  - 3, 10, 19: 2 pkt za 3 poprawne stwierdzenia, 1 pkt za 2, 0 za mniej.
  - 21: 1 pkt za każdy poprawny wybór.
- **Otwarte**: AI ocenia poprawność, uzasadnienie i odwołania do źródeł względem klucza CKE; akceptuje poprawne alternatywy wobec przykładowych odpowiedzi.
- **Tylko AI, bez etapu ludzkiego** („organizer-selected AI-only grading policy”). Dla każdej decyzji zapisuje się punkty i krótkie uzasadnienie. Te same instrukcje dla każdego zgłoszenia. Ocena **bez nazwy modelu i zespołu**.
- Ocenia się **tylko odpowiedź końcową** (`final_answer`), nigdy myślenie.
- Pusta odpowiedź = 0. Awaria techniczna = nieudany przebieg (nie zamienia się w 0). Ucięcie limitem tokenów — flaga, ocena tego, co jest.
- Odpowiedź na **inne** widoczne zadanie nie daje punktów za zadanie wskazane.
- Wynik łączny publikowany dopiero, gdy wszystkie pozycje są ocenione.

### 3.2 Esej — oficjalne kryteria CKE (zad. 26, 0–15 pkt)

Temat: zająć stanowisko wobec tezy i je uzasadnić, uwzględniając **trzy elementy** wskazane w temacie (np. trzech władców / trzy aspekty / trzy wydarzenia).

**A. Narracja historyczna (0–12 pkt).** Każdy z trzech elementów dostaje poziom argumentacji:

| Poziom argumentacji | Za 1 element | Definicja CKE (skrót) |
|---|---|---|
| **Bogata** | 4 pkt | rzeczowa, pogłębiona, poparta trafnie dobraną i szczegółową faktografią oraz adekwatną terminologią; jako całość wnikliwa analiza problemu |
| **Zadowalająca** | 3 pkt | rzeczowa, poparta prawidłową faktografią i terminologią, zawiera elementy refleksji / głębszego namysłu |
| **Powierzchowna** | 1 pkt | oparta na uogólnieniach, niewnikająca w istotę, mało dokładna, podstawowa faktografia, czasem bez przykładów |
| brak / niefunkcjonalna | 0 pkt | referowanie wszystkiego, co się pamięta, bez odniesienia do tezy, albo argumentacja sprzeczna ze stanowiskiem |

Suma za trzy elementy daje wynik w tabeli CKE (np. 4+4+4 = 12, 3+3+3 = 9, 1+1+1 = 3). Tabela CKE ma kilka nieaddytywnych przypadków, np. „bogata ×2” bez trzeciego elementu = 8, a „bogata + zadowalająca + powierzchowna” = 8.

**Odejmowanie za błędy merytoryczne** (od punktów w kryterium A, bez wychodzenia poniżej 0):
- 1–2 błędy: −1 pkt,
- 3–5 błędów: −2 pkt,
- powyżej 5 błędów: −3 pkt.

Błąd merytoryczny to ewidentna pomyłka w **chronologii** (złe osadzenie w czasie), **terminologii** (błędne użycie pojęć) albo **związkach przyczynowo-skutkowych**.

**B. Spójność wypowiedzi (0–3 pkt):**

| Pkt | Warunek |
|---|---|
| 3 | ≥ 300 słów **i** spójna (logicznie uporządkowana) |
| 2 | ≥ 300 słów, drobne zaburzenia spójności |
| 1 | ≥ 300 słów, istotne zaburzenia spójności |
| 0 | < 300 słów **i/lub** nieuporządkowana, zbiór niezależnych elementów |

Spójność: wstęp – rozwinięcie – zakończenie tworzą logiczną całość; każdy akapit wynika z poprzedniego. Zaburzenia to m.in. błędy logiczne, wątki poboczne, dygresje, skróty myślowe, zazębianie się wątków, treści zbędne.

**Reguły benchmarku dla eseju (interpretacja organizatorów):**
- < 300 słów → 0 za spójność, ale **nie** automatycznie 0 za cały esej.
- Kilka tematów w jednej odpowiedzi → ocenia się **tylko pierwszy wyraźnie wybrany** temat i tylko jego słowa.
- Liczenie słów: słowa rozdzielone białymi znakami, po usunięciu znaczników Markdown, nagłówków list i numeracji; tytuł i treść nagłówków zostają.
- Powtarzanie tego samego akapitu w kółko nie podnosi oceny (0 za spójność mimo długości).

### 3.3 Co sędzia faktycznie zapisywał (pola w `*.reviews.json`)

```json
{
  "id": "26",
  "points": 2,
  "reason": "2/15: historical argument 2/12; coherence 0/3. ...",
  "reviewer": "AI rubric assessment",
  "grading_method": "AI",
  "grading_policy": "Final benchmark grade under organizer-selected AI-only grading policy.",
  "assessed_output_field": "final_answer",
  "parsed_choices": {"A": "3", "B": "2"},
  "parsing_note": "...",
  "essay_breakdown": {
    "topic": 1,
    "components": [{"name": "Mieszko II", "points": 1, "level": "superficial", "reason": "..."}],
    "historical_points_before_deduction": 3,
    "distinct_factual_errors": 2,
    "factual_error_deduction": 1,
    "historical_points_after_deduction": 2,
    "coherence_points": 0,
    "word_count": 291,
    "word_count_method": "First selected topic only; whitespace-separated words after removing Markdown emphasis, headings/list markers and numbering. Title and heading text retained.",
    "multiple_topic_policy": "Benchmark interpretation: grade the first explicitly selected topic only..."
  },
  "fact_check_sources": [{"label": "ZPE: Mieszko II restored to power, died in 1034", "url": "https://zpe.gov.pl/..."}]
}
```

Sędzia był **agentem z dostępem do źródeł** — przy esejach weryfikował fakty na zpe.gov.pl (Zintegrowana Platforma Edukacyjna). Referencyjne przebiegi „GPT Astra” (gpt-6-astra) oceniał „AI assessment (grading agent)”. Strona jest hostowana na `chatgpt.site`, więc sędzią był prawdopodobnie model OpenAI — to wniosek, nie fakt podany na stronie.

### 3.4 Zaobserwowane zachowania sędziego (z ~960 uzasadnień)

Te wzorce mają bezpośrednie znaczenie dla harnessu:

1. **Sprzeczności = 0.** Jeśli model zaznacza jedną odpowiedź, a w uzasadnieniu mówi coś innego, albo podaje dwie wersje — sędzia „nie naprawia po cichu”. Przykłady: „The name field says A. Dziurok, while the explanation says Leonid Brezhnev… contradictory submission” → 0; „Renaissance (or Baroque) supplies incompatible alternatives… the grader does not silently select Renaissance” → 0.
2. **Asekuracja = 0.** Podawanie kilku alternatyw („X albo Y”) jest traktowane jak brak odpowiedzi.
3. **Oba elementy wymagane.** Przy „rozstrzygnij i uzasadnij”: poprawne rozstrzygnięcie bez uzasadnienia opartego na źródle = 0 (1 pkt tylko za całość).
4. **Dokładnie to, o co pytano.** Np. 5.1: podanie bitwy (Crécy) zamiast wojny (stuletnia) = 0; 9.2: przyczyna dynastyczna, którą polecenie wykluczało = 0.
5. **Ostatnia jednoznaczna odpowiedź się liczy**, ale przy konflikcie etykieta vs nazwa (np. litera C z nazwiskiem niepasującym do opcji C) = 0.
6. **Opis bez interpretacji nie wystarcza** (karykatury, zdjęcia): trzeba podać sens historyczny.
7. **Zbędne, ale nieszkodliwe dodatki są OK** („the extra explanation is not required”); fałszywe dodatki nie odbierają punktu, jeśli wymagane elementy są poprawne i spójne.
8. **Pętle i powtórzenia** (typowe dla małych modeli do limitu tokenów) — oceniana jest treść, powtórzenia nie pomagają, w eseju zabijają spójność.
9. **Esej na złym temacie / z władcami spoza epoki** (np. Mieszko I albo Łokietek w temacie XI–XII w.) → 0 za ten element + błędy merytoryczne.

Praktyczne wnioski dla harnessu:
- wymuszać **krótką, jednoznaczną odpowiedź końcową** w formacie polecenia (`Rozstrzygnięcie: … / Uzasadnienie: …`, litera, P/F, A–3);
- zawsze **odwoływać się do źródła** („w źródle 2 …”), gdy polecenie tego wymaga;
- myślenie trzymać poza odpowiedzią końcową;
- w eseju: jeden temat, wyraźne stanowisko, **3 elementy × konkretne fakty/daty/terminy**, 350–600 słów, wstęp – 3 akapity – zakończenie, zero zmyślonych dat.

---

## 4. Rekonstrukcja promptu sędziego (do lokalnej ewaluacji)

**To nie jest oficjalny prompt** — to rekonstrukcja z metodyki, klucza CKE i pól zapisywanych przez sędziego. Nadaje się do lokalnego sędziego (GPT / Gemini z Twoich kredytów) do porównywania wersji modelu.

```text
Jesteś egzaminatorem matury z historii (poziom rozszerzony, CKE). Oceniasz JEDNĄ odpowiedź modelu na JEDNO zadanie, wyłącznie według podanych zasad oceniania CKE.

ZASADY OGÓLNE
- Akceptowane są wszystkie odpowiedzi merytorycznie poprawne i spełniające warunki zadania, także inaczej sformułowane niż przykładowe rozwiązanie.
- Oceniaj tylko odpowiedź końcową. Ignoruj ewentualne rozumowanie/myślenie.
- Nie poprawiaj odpowiedzi „po cichu”: jeśli odpowiedź zawiera sprzeczne wskazania, kilka alternatyw albo etykietę niezgodną z treścią — nie wybieraj za zdającego; przyznaj punkty tylko za elementy jednoznacznie poprawne.
- Jeśli polecenie wymaga rozstrzygnięcia i uzasadnienia (albo odwołania do źródła), punkt wymaga obu elementów.
- Odpowiedź na inne zadanie niż wskazane = 0.
- Pusta odpowiedź = 0. Odpowiedź uciętą oceniaj tak, jak jest.
- Stosuj dokładnie reguły punktów częściowych z zasad oceniania danego zadania.

ESEJ (zadanie wypracowania)
- Oceń tylko pierwszy wyraźnie wybrany temat.
- Kryterium A (0–12): dla każdego z trzech elementów tematu określ poziom argumentacji: bogata (4), zadowalająca (3), powierzchowna (1), brak/niefunkcjonalna (0). Zastosuj tabelę CKE. Policz odrębne błędy merytoryczne (chronologia, terminologia, związki przyczynowo-skutkowe): 1–2 → −1, 3–5 → −2, >5 → −3; minimum 0.
- Kryterium B (0–3): policz słowa (rozdzielone białymi znakami, bez znaczników Markdown i numeracji). <300 słów → 0. Inaczej: spójna 3, drobne zaburzenia 2, istotne 1, nieuporządkowana 0. Powtarzanie tych samych fragmentów to zaburzenie spójności.

DANE
[ZADANIE] {polecenie + źródła}
[MAKS. PUNKTÓW] {max_points}
[ZASADY OCENIANIA CKE I PRZYKŁADOWE ROZWIĄZANIE] {fragment klucza}
[ODPOWIEDŹ ZDAJĄCEGO] {final_answer}

Zwróć wyłącznie JSON:
{"points": <int>, "reason": "<krótkie uzasadnienie po polsku>", "parsed_choices": {...} | null,
 "essay_breakdown": {"topic": <int>, "components": [{"name": "...", "level": "rich|satisfactory|superficial|none", "points": <int>}],
   "historical_points_before_deduction": <int>, "distinct_factual_errors": <int>, "factual_error_deduction": <int>,
   "coherence_points": <int>, "word_count": <int>} | null}
```

---

## 5. Materiały skopiowane do repozytorium (`assets/benchmark-2023/`)

| Plik | Zawartość |
|---|---|
| `methodology.md` | pełna metodyka v0.2 (oryginał) |
| `exam-text-34items.json` | **gotowy zbiór 34 zadań w wersji tekstowej** (polecenie, źródła, opisy obrazków, punkty) — do lokalnej ewaluacji |
| `exam-images-37items.json` + `vision-pages/page-04..28.png` | wersja obrazowa: polecenia + strony arkusza (200 dpi) |
| `cke-2023-arkusz.pdf` | oryginalny arkusz CKE |
| `cke-2023-zasady-oceniania.pdf` / `.txt` | oficjalny klucz i zasady oceniania CKE |
| `reviews/*.reviews.json` | wszystkie oceny AI-sędziego (punkty + uzasadnienia) dla 25 przebiegów i Astry |
| `runs/*.json` | pełne przebiegi 6 modeli (prompty wyrenderowane, odpowiedzi, tokeny, czasy) |
| `gpu-generation-by-model.csv` | czasy GPU na model |

Uwaga: arkusz 2023 jest publiczny i mógł trafić do danych treningowych modeli. **Nie trenuj na nim**, jeśli chcesz go używać jako walidacji — finałowy arkusz będzie inny.
