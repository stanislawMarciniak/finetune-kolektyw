# Specyfikacja generowania danych SFT (matura z historii, poziom rozszerzony)

Cel: zbiór wysokiej jakości przykładów do fine-tuningu (LoRA) modeli, które mają rozwiązywać maturę z historii CKE (formuła 2023, poziom rozszerzony). Przykłady mają być **jakościowe, niepowtarzalne i pokrywać cały zakres materiału**.

## API i budżet

- Endpoint zgodny z OpenAI: `https://app.forgehand.app/api/v1/teams/01a0da5f-05f4-700d-a554-4c8f829182f1/llm/v1`
- Klucz: zmienna `FORGEHAND_API_KEY` w `/home/stasiek/finetune-kolektyw/.env` (wczytuj przez `set -a; . ./.env; set +a` albo python-dotenv; **nigdy nie wypisuj klucza**).
- Modele: `gpt-6-sol` (mocny, droższy) i `gpt-6-luna` (tańszy). API przyjmuje tylko tekst, maks. 32 768 tokenów wyjścia, timeout 3 min. `response_format={"type":"json_object"}` i `reasoning_effort="low"` działają.
- Szacowane ceny (USD za 1M tokenów, wej./wyj.): luna 0.41 / 2.45, sol 2.04 / 12.2. Licz koszt z `usage` każdej odpowiedzi, mnożąc przez **1.2** (zapas), i zapisuj do `data_gen/cost_log.jsonl`.
- **Twardy limit łączny: 32 USD** (szacunek). Limity etapów niżej. Po przekroczeniu limitu etapu skrypt kończy pracę, zachowując wyniki.
- Współbieżność 6–8 wątków, ponawianie z odczekaniem (429/5xx/timeout), zapis przyrostowy (JSONL, append) i wznawianie (pomijanie gotowych ID).

## Czego NIE wolno używać (zbiory testowe)

Arkusze formuły 2023 z maja 2023, 2024, 2025, 2026 (`MHIP-R0-100-23*`, `-24*`, `-25*`, `-26*`, w tym `-A-`) oraz egzamin próbny `assets/mock-2023/`. Po wygenerowaniu odfiltruj syntetyczne zadania podobne do pytań z `eval/data/*.jsonl` (np. Jaccard na 4-gramach słów > 0.35 albo bardzo podobne pytanie i odpowiedź).

## Format zadania (zgodny z oficjalnym `exam.json`)

Na egzaminie każde zadanie ma pola: `id`, `group`, `max_points`, `question`, `source_text`, `images`, `answer_format`. Przykład prawdziwego egzaminu: `assets/mock-2023/exam.json` (przeczytaj go w całości przed pisaniem promptów).

Dozwolone `answer_format` i składnia wzorowej odpowiedzi (`model_answer`):

| typ | `answer_format` (dokładnie) | `model_answer` |
|---|---|---|
| `closed_tf` | `1: P\n2: F\n3: P` (tyle linii, ile stwierdzeń) | np. `1: F\n2: P\n3: P` |
| `closed_choice` | `A` | jedna litera, np. `C` |
| `closed_match` | `A: 1\nB: 1` (litery opisów → numery/nazwy) | np. `A: 3\nB: 2` |
| `closed_multi` | `1: A\n2: A` (kilka niezależnych wyborów) | np. `1: B\n2: C` |
| `open` | `Tekst po polsku. Podaj wszystkie wymagane elementy odpowiedzi.` | zwięzła, jednoznaczna odpowiedź; jeśli polecenie ma etykiety (`Rozstrzygnięcie:`, `Uzasadnienie:`, `Podobieństwo:`…), użyj ich; odwołanie do źródła, gdy polecenie tego wymaga; **bez wariantów „albo”** |
| `essay` | `Jeden tekst: numer wybranego tematu i całe wypracowanie. Minimum 300 wyrazów zgodnie z poleceniem.` | `Temat nr X\n\n<wypracowanie 450–700 słów>` |

Styl CKE: polecenia zaczynają się od „Rozstrzygnij…”, „Podaj…”, „Wymień…”, „Wyjaśnij…”, „Porównaj…”, „Oceń prawdziwość…”, „Dokończ zdanie. Zaznacz właściwą odpowiedź spośród podanych.”, „Przyporządkuj…”. Zadania są osadzone w źródłach (fragment opracowania historycznego, fragment dokumentu, tabela) i często łączą źródło z wiedzą własną. Wzory stylu: `eval/data/test2024_split.jsonl` itd. **tylko do obejrzenia stylu, nie do kopiowania treści**, oraz informator (niżej).

Rozkład typów (jak w CKE, bez esejów): ok. 20–25% zamkniętych (tf ~10%, choice ~7%, match ~4%, multi ~3%), 75–80% otwartych (rozstrzygnij + uzasadnij ~25%, podaj/wymień ~25%, wyjaśnij ~15%, porównaj/podobieństwo-różnica ~10%).

## Schemat rekordu wyjściowego (JSONL)

```json
{"id": "...", "origin": "real|synthetic|essay", "source_doc": "...", "section": "XXV. Rewolucje XVIII w.", "subtopic": "...",
 "type": "closed_tf|closed_choice|closed_match|closed_multi|open|essay", "group": "...", "max_points": 1,
 "question": "...", "source_text": "...", "answer_format": "...", "model_answer": "...", "rubric": "zasady oceniania (CKE lub w stylu CKE)",
 "needs_image": false, "image_refs": [], "verified": true, "verify_note": "..."}
```

## Etapy

### E1. Prawdziwe zadania CKE → format egzaminu (luna, limit 3 USD)

Źródła (tekst stron już wyekstrahowany: `data/cke/extracted/<formuła>/<plik>/pages.json`, lista i typy plików w `data/cke/raw/manifest.jsonl`):
- informator `data/cke/extracted/f2023/Informator_EM2025_historia_2025_2026` — strony 15–120: przykładowe zadania z zasadami oceniania i rozwiązaniami (także przypisane wymagania = dział podstawy programowej);
- formuła 2015, poziom rozszerzony: `data/cke/extracted/f2015/` (arkusze `MHI-R1_1P-1x2`, `EHIP-R0-100-2x05` + odpowiadające zasady/`_model`);
- stara matura, poziom rozszerzony (`MHI-R1_1P-*`, `*PR*`, `*_pr*` w `data/cke/extracted/stara/`) — opcjonalnie, jeśli zostanie budżet.

Wysyłaj arkusz porcjami (3–5 stron z numerami stron) razem z pełnym tekstem zasad oceniania danego arkusza. Model zwraca zadania w schemacie wyżej, z `model_answer` zbudowanym z rozwiązania CKE (jedna, najlepsza wersja z przykładów, bez „/” i alternatyw), `rubric` = zasady CKE, `answer_format` wg tabeli, `needs_image=true` + `image_refs` (numery stron), gdy zadanie wymaga obrazu (mapa, ilustracja, zdjęcie). Walidacja: suma punktów na arkusz ≈ suma z zasad; brak duplikatów ID.

Tematy wypracowań z tych arkuszy zapisz osobno (`data/sft/real_essay_topics.jsonl`) — użyjesz ich w E4.

Wynik: `data/sft/real_cke.jsonl`.

### E2. Mapa zakresu materiału + kompendium (sol, limit 5 USD)

1. Działy podstawy programowej (wymagania szczegółowe historii LO, zakres podstawowy + rozszerzony, jak w informatorze CKE). Lista działów (uzupełnij brakujące numery wiedzą o podstawie programowej):
   II Pradzieje i historia starożytnego Wschodu; III Świat starożytnych Greków; IV Społeczeństwo, życie polityczne i kultura starożytnego Rzymu; V Bizancjum i świat islamu; VI Europa wczesnego średniowiecza; VII Europa w okresie krucjat; VIII Gospodarcze i społeczne realia średniowiecznej Europy; IX Polska w okresie wczesnopiastowskim; X Polska w okresie rozbicia dzielnicowego; XI Europa późnego średniowiecza; XII Polska w XIV i XV w.; XIII Kultura średniowiecza; XIV Odkrycia geograficzne i europejski kolonializm doby nowożytnej; XV Czasy renesansu; XVI Reformacja i jej skutki; XVII Europa w XVI i XVII w.; XVIII Państwo polsko-litewskie w czasach ostatnich Jagiellonów; XIX Powstanie Rzeczypospolitej Obojga Narodów; XX Pierwsze wolne elekcje i ich następstwa; XXI Renesans w Polsce; XXII Polityka wewnętrzna i zagraniczna Rzeczypospolitej Obojga Narodów; XXIII Ustrój, społeczeństwo i kultura Rzeczypospolitej Obojga Narodów; XXIV Europa w dobie oświecenia; XXV Rewolucje XVIII w.; XXVI Rzeczpospolita w XVIII w. (od czasów saskich do Konstytucji 3 maja); XXVII Upadek Rzeczypospolitej; XXVIII (kultura polskiego oświecenia / ziemie polskie po rozbiorach — sprawdź); XXIX Epoka napoleońska; XXX Europa i świat po kongresie wiedeńskim; XXXI Ziemie polskie i ich mieszkańcy w latach 1815–1848; XXXII Powstanie styczniowe i jego następstwa; XXXIII Europa i świat w II połowie XIX i na początku XX w.; XXXIV Przemiany gospodarcze i społeczne. Nowe prądy ideowe; XXXV Ziemie polskie pod zaborami w II połowie XIX i na początku XX w.; XXXVI Kultura i nauka polska w II połowie XIX i na początku XX w.; XXXVII I wojna światowa; XXXVIII Sprawa polska w przededniu i podczas I wojny światowej; XXXIX Europa i świat po I wojnie światowej; XL Narodziny i rozwój totalitaryzmów w okresie międzywojennym; XLI Walka o odrodzenie państwa polskiego po I wojnie światowej; XLII Dzieje polityczne II Rzeczypospolitej; XLIII Społeczeństwo i gospodarka II Rzeczypospolitej; XLIV (sprawdź: kultura / polityka zagraniczna II RP); XLV Świat na drodze do II wojny światowej; XLVI Wojna obronna Polski w 1939 r.; XLVII II wojna światowa i jej etapy; XLVIII Polska pod okupacją niemiecką i sowiecką; XLIX (sprawdź: Zagłada / Holokaust); L Działalność władz RP na uchodźstwie i w okupowanym kraju; LI Świat po II wojnie światowej. Początek zimnej wojny; LII Dekolonizacja, integracja i nowe konflikty; LIII Przemiany cywilizacyjne na świecie; LIV Świat na przełomie tysiącleci; LV Proces przejmowania władzy przez komunistów w Polsce (1944–1948); LVI Stalinizm w Polsce i jego erozja; LVII Polska w latach 1957–1981; LVIII Dekada 1981–1989; (ew. dalsze: narodziny III RP i Polska po 1989).
2. Dla każdego działu sol generuje 6–10 **podtematów** (konkretnych wymagań egzaminacyjnych) → `data_gen/taxonomy.json`.
3. Dla każdego podtematu sol pisze **notatkę kompendium** (300–500 słów, po polsku): kluczowe fakty, daty, postacie, pojęcia, przyczyny i skutki, typowe pułapki egzaminacyjne. Tylko pewne fakty. → `data/kb/kompendium.jsonl` (`{"section","subtopic","title","text"}`). To będzie też baza RAG.

### E3. Syntetyczne wiązki zadań (generuje sol, weryfikuje luna; limit 14 USD)

Dla każdego podtematu z taksonomii (co najmniej 1, najlepiej 2 wiązki na podtemat, różne aspekty) sol tworzy **wiązkę**: 1 źródło (`source_text`, 60–200 słów: „Fragment opracowania historycznego” napisany na podstawie notatki kompendium, adaptowany fragment dokumentu epoki, który model zna pewnie, albo prosta tabela danych; czasem zadanie bez źródła) + 1–3 zadania różnych typów (zgodnie z globalnym rozkładem — prowadź licznik i przekazuj w prompcie, jakich typów brakuje). Każde zadanie: `question`, `answer_format`, `max_points` (1, czasem 2–3), `model_answer`, `rubric` w stylu CKE. Podawaj notatkę kompendium jako kontekst faktów, żeby nie halucynować.

**Weryfikacja** (luna): rozwiązuje zadanie „na ślepo” (tylko `source_text` + `question` + `answer_format`, bez klucza), potem porównanie:
- zamknięte: identyczność po normalizacji;
- otwarte: luna ocenia, czy odpowiedź na ślepo i klucz są merytorycznie zgodne oraz czy klucz jest poprawny i jednoznaczny.

Zadania z rozbieżnością: odrzuć albo (jeśli klucz ewidentnie błędny) popraw i oznacz. Zapisuj `verified` i `verify_note`. Deduplikacja w obrębie zbioru (podobne pytania) i względem zbiorów testowych.

Cel: ok. 1500–2500 zweryfikowanych zadań, równomiernie po działach. Wynik: `data/sft/synthetic_items.jsonl`.

### E4. Eseje wzorcowe (sol; limit 9 USD)

1. Tematy: po 3 na dział (różne epoki, Polska i świat), w formule CKE: „<teza>. Zajmij stanowisko wobec powyższej tezy i je uzasadnij, uwzględniając w swojej argumentacji <trzy elementy: aspekty / władców / wydarzenia>.” + tematy z `data/sft/real_essay_topics.jsonl`.
2. Esej: sol pisze wypracowanie 450–700 słów (wstęp z jednoznacznym stanowiskiem, trzy akapity — po jednym na element — z konkretnymi faktami, datami i pojęciami, zakończenie wynikające z argumentów; zero wymyślonych faktów). Format odpowiedzi: `Temat nr 1\n\n...` (w zadaniu jeden temat).
3. Ocena wg kryteriów CKE: użyj promptu `SYSTEM_ESSAY` i funkcji liczenia słów z `eval/judge_openai.py` (możesz zaimportować). Sędzia `gpt-6-luna`; zostaw eseje z wynikiem ≥ 12/15 (zapisz ocenę i rozbicie).

Cel: 250–400 esejów. Wynik: `data/sft/essays.jsonl` (rekord jak wyżej, `type="essay"`, `question` = pełne polecenie z jednym tematem, `model_answer` = esej).

## Raport końcowy

- `data/sft/STATS.md`: liczby rekordów na etap i typ, pokrycie działów (tabela dział → liczba zadań), odsetek przechodzących weryfikację, odrzucone duplikaty, koszt na etap (z `cost_log.jsonl`).
- `data/sft/samples/`: po 15 losowych rekordów z każdej kategorii (`real_cke`, `synthetic_closed`, `synthetic_open`, `kompendium`, `essays`) w czytelnym markdown do przeglądu przez człowieka.
- Kod w `data_gen/*.py`, uruchamialny ponownie.
