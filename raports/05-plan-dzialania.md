# 05 — Plan działania

Stan na: **nd 27.09.2026, 01:00** (sekcje 1–8 opisują plan z sob 19:40). Freeze i egzamin: **nd 27.09, 11:00**.
Identyfikatory `H-xx` odnoszą się do raportu 07 (hipotezy). Zasoby i ceny: raport 04. Zasady: raport 01. Porównanie przed / po: raport 09.

Wszystkie liczby poniżej pochodzą od sędziego **`gpt-6-luna`**, o ile nie zaznaczono inaczej. Oceny sprzed sob 13:40 wystawiał inny sędzia (`gpt-5.4-mini` / Claude), który był o ~4 pp łaskawszy (H-E6), więc nie mieszamy ich z nowymi.

---

## Decyzje G3 / G4 (nd 01:00) — konfiguracja egzaminacyjna

Paczki v2 (znaczniki obrazów jak w finale), wynik główny 2024 + 2025, potwierdzenie 2026. Konfiguracje: `server/final_configs.json`, procedura: `server/RUNBOOK.md` (próby na sucho na mocku przeszły).

| Track | Rozwiązanie | Wynik 2024+2025 / 2026 | Zmiana wobec sob 20:00 |
|---|---|---|---|
| **T1** | Gemma-4-12B-it QAT q4_0 + mmproj, `t1final` (myślenie wszędzie, obrazy, temperatura 1.0) | 71.0% (2 seedy) / 83.3% | bez zmian — żaden wariant nie pomógł (H-N1, H-N6, H-N7, RAG) |
| **T2** | PLLuM-12B-base Q4_K_M + LoRA `pllum-v1recipe-full` (~12 tys. przykładów, 2 epoki) + RAG PolQA top-3 i 1 notatka z bazy wiedzy | 52.9% / 41.7% (goła baza 0%) | +11.7 pp / +15.0 pp; przyrost vs baza +52.9 / +41.7 pp |
| **T3** | Qwen3.5-4B **Q3_K_M (2.29 GB)** + mmproj, myślenie dla krótkich, esej z kompendium, **temperatura 0.6** | 48.7 / 51.3% (2 seedy) / 48.3% | ten sam wynik przy −0.45 GB (było Q4_K_M 2.74 GB) |

Otwarte: kalibracja z oceną organizatorów na mocku (H-N14) — gdy będą link i `TEAM_KEY`.

## 0. Stan w skrócie (sob 19:40)

| Track | Zgłoszenie, które już mamy | Wynik (2024 / 2025 / 2026 / mock) | Kandydat na lepsze | Następny krok |
|---|---|---|---|---|
| **T1** najlepszy wynik | Gemma-4-12B-it QAT q4_0 (6.98 GB + mmproj 0.18 GB), myślenie, obrazy, harness | stara konfiguracja: 76.3 / 78.3 / 75.0 / 76.7%; `t1final`: 74.6 / 63.3 / 71.7 / 78.3% | — | ustalić, czy `t1final` jest gorszy, czy to szum (H-N1); esej to największa wariancja |
| **T2** największy postęp | PLLuM-12B-base + LoRA (7.48 + 0.23 GB) | 40.7–45.8 / 30–35% (baza goła ~0%) → **+35–40 pp** | Gemma-4-12B pt + LoRA scalona (7.38 GB + mmproj 0.12 GB), baza goła ~15% | ewaluacja scalonej Gemmy pt (H-N2); wybór bazy na G3 |
| **T3** najmniejszy ≥ 35% | Qwen3.5-4B Q4_K_M (2.74 GB) + mmproj, myślenie | 40–49 / 50–55% | IQ3_XXS 1.95 GB, IQ2_M 1.76 GB, Qwen3.5-2B 1.28 GB | drabina rozmiaru w jednej konfiguracji na L40S (H-N4, H-N5) |

**Co już wiemy (szczegóły i liczby w raporcie 07):**
- **Harness:** prompt organizatorów zostaje. Instrukcje v1, esej akapitowy i RAG dla dużych modeli nie pomagają (H-H1, H-H14, H-H2).
- **RAG z HyDE pomaga małym modelom** o +6–8 pp (Bielik-1.5B, Qwen3.5-2B; H-H2).
- **SFT uczy formy, nie wiedzy.** Małe modele (1.5–2B) zyskują 0–7 pp i nie dochodzą do 35% (H-T1, H-T2). SFT ma sens dla baz `-Base`/`-pt` w T2, bo tam uczy formatu od zera.
- **Qwen3.5-4B z myśleniem traci na urwaniach i na eseju.** Myślenie urywa się przy limicie tokenów, a esej pisany awaryjnie ma 7–12 błędów merytorycznych. Poprawki: powtórka bez myślenia przy urwaniu; esej bez myślenia, z kompendium jako kontekstem (+5.6 pp na 12 tematach; H-N3).
- **Głosowanie odpada** jako „pompowanie” według komunikatu organizatorów (raport 01).

---

## 1. Infrastruktura i zasady pracy

| Maszyna | Koszt | Rola | Uwagi |
|---|---|---|---|
| **Nebius H100 80 GB** `matura-h100` (`server/NEBIUS.md`) | 3.85 $/h, od 17:44 | trening (T2), ewaluacje T1/T2, **egzamin wszystkich tracków** | 196 GB RAM; dysk ~150 MB/s |
| **Nebius L40S 48 GB** `matura-l40s` (AMD, 16 vCPU, 64 GB RAM) | ~1.7 $/h, od 19:05 | ewaluacje T3, powtórki T1, zapas na egzamin | IP 89.169.112.149; instalacja `server/bootstrap_eval_vm.sh` (bez treningu) |
| Forgehand L40S | przedpłacone (~185 $) | zapas | **zatrzymany**: przy 30 GB RAM dwa serwery Qwen z obrazami (po ~10 GB) psują montaż `/workspace` i SSH (dwie awarie). Tylko 1 serwer naraz |
| Modal | ~11 $ | zapas na trening z Unsloth | Unsloth nie obsługuje Gemma-4 pt (`transformers` ≤ 5.5) |
| Forgehand LLM API | ~25 $ | sędzia `gpt-6-luna` (~0.01 $ za arkusz), `gpt-6-sol` na bramkach | filtr treści Azure odrzuca zadanie 2024/21; jest wykluczane z mianownika |

**Budżet Nebius (123 $):** H100 do nd 11:00 to ~60 $, L40S przez ~14 h to ~24 $, razem ~92 $ (wydane ~8 $ do 19:40). Zapas ~30 $ wystarczy na drugą kartę przy ciężkiej kolejce albo na przedłużenie H100 po 11:00. Na obu maszynach działa **strażnik bezczynności** (`server/idle_shutdown.sh`): po 60 min bez harnessu, treningu czy konwersji wyłącza system, więc karta przestaje naliczać.

**Zasady (z lekcji dzisiejszego dnia):**
1. **Najwyżej 2 ciężkie ewaluacje na kartę.** Pięć zadań naraz na H100 wydłużyło przebieg T1 z ~20 min do ponad 2 h na arkusz. Równoległość daje dopiero druga karta.
2. **Skrypty czekają tylko na przebiegi harnessu** (`wait_runs`), nie na `llama-server`. Wcześniejsze `wait` wisiało w nieskończoność i blokowało kolejne kroki.
3. **`pkill -f` tylko ze wzorcem `[x]yz` albo `^bash server/...`**, bo inaczej zabija własną sesję SSH. Nigdy `pkill -f llama-server` (zabija cudze serwery).
4. **Decyzje na ≥ 2 arkuszach** (2024 + 2025), potwierdzenie na 2026 tylko na bramkach. Szum między seedami to ±4 pp na arkusz, a sam esej potrafi skoczyć o ±7 pkt.
5. **Mierzymy artefakt finalny:** GGUF (baza + LoRA albo scalony) + harness w `llama.cpp`, tak jak na egzaminie.
6. **Każdy przebieg ocenia luna** (`server/fetch_runs.sh nebius|<sesja> <budżet> <filtr>`). Wyników różnych sędziów nie porównujemy.

---

## 2. Harness — co jest w środku

`harness/run_exam.py`: `exam.json` (+ `images/`) → `answers.json` (format organizatorów) + `debug.jsonl`.

| Element | Stan |
|---|---|
| Prompt | prompt organizatorów (system) + „Zadanie X (p pkt)” + źródła + polecenie; przy zamkniętych dopisek z `answer_format` |
| Typ zadania | z `answer_format` (100% na mocku); otwarte dzielone na „rozstrzygnij / podaj / inne” (do bramkowania myślenia i RAG) |
| Zamknięte | normalizacja do dokładnej składni (`1: P`, `A`, `A: 1`, `1: A`) |
| Myślenie | per typ (`--think`); **powtórka bez myślenia przy urwaniu lub pustej odpowiedzi** |
| Esej | < 300 wyrazów → napisz ponownie (do 2 razy); brak numeru tematu → dopytanie i dopisanie; opcja `--kb-essay` (kompendium jako kontekst) |
| RAG | `--rag hyde` (HyDE pisze ten sam model, BM25 na PolQA); błąd HyDE nie przerywa egzaminu |
| Odrzucone | instrukcje v1, esej akapitowy, `--careful` (−1.6 pp na esejach), głosowanie |

Konfiguracje per track (docelowe, do potwierdzenia na G4):
- **T1:** `--vision --think essay,rozstrz,open,podaj,closed --temperature 1.0 --top-p 0.95 --top-k 64`, bez RAG.
- **T2 (PLLuM):** `--no-think-kwargs --temperature 0.0 --top-k 1`, bez RAG. **T2 (Gemma pt):** `--vision --no-think-kwargs --temperature 0.3`, szablon `train/templates/gemma4_turns.jinja`.
- **T3:** `--vision --think rozstrz,open,podaj,closed --max-tokens 8000 --kb-essay data/kb/kompendium.jsonl --temperature 1.0 --top-p 0.95 --top-k 20`.

---

## 3. Plan per track

### T1 — najlepszy wynik
- **Model zostaje:** Gemma-4-12B-it QAT. Treningu nie robimy, bo SFT bez śladów rozumowania grozi utratą myślenia, a zysk jest niepewny (H-T4 odłożone).
- **H-N1:** `t1final` kontra stara konfiguracja (inny prompt systemowy dla zadań bez obrazów, brak dopisku o formacie), po 2 seedy na 2024 i 2025. Wygrywa lepsza średnia.
- **H-N6:** esej Gemmy z kompendium jako kontekstem (`--kb-essay`) na 12 tematach.
- **H-N7:** niższa temperatura tylko dla eseju (np. 0.7) zmniejsza wariancję bez straty.
- Mock 2023 oddajemy w konfiguracji docelowej, gdy przyjdą link i `TEAM_KEY` (kalibracja naszego sędziego, H-E1).

### T2 — największy postęp
- **Baza goła:** PLLuM-12B-base ~0%, Gemma-4-12B pt ~15% (pomiar niepełny: 16 i 30 pkt nieocenionych). **H-N8:** dokończyć pomiar gołej Gemmy pt lunką, bo od tego zależy przyrost.
- **H-N2:** Gemma pt + LoRA **scalona w wagi** (`server/exp_h100_gemmapt_merged.sh`). LoRA nakładana w locie psuje Gemmę 4 w `llama.cpp` (powtarzany `<unused49>`, potem błąd CUDA). Plik `gemma-4-12B-sft-Q4_K_M.gguf` jest gotowy na H100.
- **G3 (~21:30): wybór bazy T2** po przyroście w pp (średnia 2024 + 2025).
- **Runda 2 SFT dla wybranej bazy** (~25 min treningu + ~20 min ewaluacji na H100), każda zmiana osobno:
  - Gemma: trening na tym samym szablonie co serwowanie (`--template-file train/templates/gemma4_turns.jinja`, H-N9);
  - Gemma: 115 zadań CKE z obrazami w treningu wizyjnym (H-N10);
  - obie: 3 epoki zamiast 2 albo więcej esejów (H-N11).

### T3 — najmniejszy model ≥ 35%
- **Bezpieczne zgłoszenie:** Qwen3.5-4B Q4_K_M (2.74 GB).
- **Drabina w jednej konfiguracji T3** (`server/exp_h100_t3.sh` na L40S): Q4_K_M → IQ3_XXS (1.95) → IQ2_M (1.76) i Qwen3.5-2B Q4_K_M (1.28). Wybieramy najmniejszy wariant ze średnią ≥ 40% na 2024 + 2025 (margines na inny arkusz), a potem potwierdzamy go na 2026 (H-N4, H-N5).
- Wynik Qwen3.5-2B z myśleniem z Forgehand leży na trwałym `/workspace` i trzeba go pobrać po następnym starcie sesji.

---

## 4. Harmonogram (sob 19:40 → nd 11:00)

| Kiedy | H100 | L40S | Człowiek / agent |
|---|---|---|---|
| 19:40–21:30 | T2: scalona Gemma pt na 2024/2025 + goła Gemma pt (baseline) | T3: drabina rozmiaru (4 warianty × 2 arkusze, po 2 naraz) | ocena lunką, raporty |
| **G3 ~21:30** | wybór bazy T2 | wstępny wybór T3 | |
| 21:30–00:30 | T2 runda 2 (szablon / obrazy / epoki) + ewaluacje | T1: H-N1 (2 seedy × 2 arkusze), H-N6 esej z kompendium | |
| noc 00:30–07:00 | kolejka automatyczna: najlepszy T2 na 2026 i 2 seedy, potem wyłączenie | T3: zwycięzca na 2026 + 2 seedy, potem wyłączenie | sen |
| 07:00–09:30 | **G4:** finalne artefakty; test offline | zapas | runbook, `SOURCE.md`, repo dla jury |
| 09:30–11:00 | **freeze**; przebiegi „base” i „tuned” dla każdego tracku | kopia zapasowa przebiegów | zgłoszenia |

---

## 5. Egzamin — runbook (szkic, uzupełnić na G4)

Wszystkie trzy tracki mieszczą się naraz na H100 (VRAM ~35 GB). L40S trzyma kopię na wypadek awarii.

| Track | Serwer (`llama-server --jinja -ngl 999 -c 65536 -np 8 --kv-unified`) | Harness |
|---|---|---|
| T1 | `gemma-4-12b-it-qat-q4_0.gguf --mmproj mmproj-…qat… -ub 4096 -b 4096 --reasoning-format deepseek` | konfiguracja T1 z §2 |
| T2 | wybrany model (PLLuM + `--lora` + `--chat-template-file` albo scalona Gemma pt + `gemma4_turns.jinja` + mmproj) | konfiguracja T2 z §2 |
| T3 | wybrany Qwen3.5 + `mmproj-F16.gguf -ub 4096 -b 4096 --reasoning-format deepseek` | konfiguracja T3 z §2 |

- Przebieg „base” (goły model, bez harnessu) i „tuned” dla każdego tracku, zgodnie z formularzem.
- Offline: bez kluczy w środowisku, `HF_HUB_OFFLINE=1`; test z odciętą siecią przed 10:00.
- Po egzaminie zatrzymujemy wszystkie maszyny (`nebius compute instance stop --id …`, `fh session stop`).

---

## 6. Nowe pomysły i decyzje (sob 20:00, analiza w raporcie 08)

**Wnioski z analizy per typ i zagadnienie (raport 08):** esej to największa strata we wszystkich trackach; historia Polski jest najsłabsza u każdego modelu, także przy tym samym typie zadania (Qwen-4B 44% vs 90% w powszechnej); myślenie podnosi zamknięte o 8–19 pp.

| Pomysł | Decyzja | Hipoteza |
|---|---|---|
| **Dane z rozumowaniem** (uzasadnienie z kluczem, `gpt-6-luna`, ~2 $) do SFT baz T2; dla T3 jako eksperyment | **tak**, priorytet dla T2 | H-N15, H-N16 |
| **Baza wiedzy o historii Polski:** oś czasu, postacie, pojęcia (luna, ~1–2 $) | **tak**, najpierw test trafności wyszukiwania na CPU | H-N19, H-N21 |
| Embedder i hybryda BM25 + dense | sprawdzić na tym samym benchmarku wyszukiwania | H-N20 |
| Dogenerowanie kompendium dla eseju | po osi czasu i postaciach | H-N12 |
| Wybór tematu eseju przez samoocenę modelu (jedna generacja, nie głosowanie) | **sprawdzić** | H-H8 |
| Limit myślenia per typ | **odrzucone** | H-N13 |
| Szybkie zbiory kontrolne z esejów (12 tematów, ~10 min) | **tak**, ale zwycięska zmiana eseju przechodzi potem pełne arkusze (czy nie psuje reszty) | — |
| T3 poniżej 1.5 GB: Qwen3.5-4B IQ2_XXS (1.52 GB), Qwen3.5-2B z myśleniem i HyDE | **tak** (IQ2_XXS tylko, jeśli IQ2_M ≥ 40%) | H-N17, H-N18 |

**Decyzje z sob 20:20:**
- **Modele myślące dostrajamy bez rozumowania w danych**, z zamaskowanym blokiem myślenia (`--mask-think`, H-N22). Dotychczasowy trening Qwen uczył pomijać myślenie (pusty blok `<think></think>` był w stracie).
- **Więcej przykładów zamiast rozumowania dla modeli myślących** (H-N27); dane z rozumowaniem zostają dla baz T2 (H-N15).
- **Baza wiedzy: Polska i świat** (oś czasu, postacie, pojęcia dla obu), z naciskiem na Polskę (H-N19).
- **T3: routing między modelami** (liczy się tylko największy plik): historia Polski bez obrazu → polski model ~1.9 GB, obrazy i powszechna → Qwen3.5-4B IQ3 (H-N23), z klasyfikatorem bez modelu albo z samym modelem głównym jako klasyfikatorem (H-N24). W T1/T2 routing między dużymi modelami odpada, bo suma przekroczyłaby 8.8 GB.
- **Dane SFT odtwarzają wejście harnessu** (H-N26); numeracja zadań poprawiona.
- **Bramka RAG według pewności wyszukiwania** (H-N25).

**Budżet API (30.31 $):** dane z rozumowaniem ~2 $, baza wiedzy ~2 $, kompendium ~1–2 $ (luna zamiast sol), sędzia ~3 $; rezerwa ~20 $ (np. sol do kontroli próbek i esejów).

---

## 7. Ryzyka

| Ryzyko | Mitygacja |
|---|---|
| Awaria maszyny w nocy lub rano | dwie maszyny Nebius; artefakty finalne na obu i na laptopie; Forgehand jako trzecia (1 serwer) |
| Brak sprzętu przy ponownym starcie (L40S Intel był niedostępny) | nie usuwamy maszyn; strażnik tylko je zatrzymuje; start ~1.5 min |
| Nasz sędzia ≠ sędzia finałowy | oddanie mocka i porównanie z naszą oceną (H-E1) |
| Wariancja eseju (±7 pkt) | decyzje na ≥ 2 arkuszach i 2 seedach; H-N7 |
| Zadania z obrazami w T2 (PLLuM nie widzi obrazów) | Gemma pt z mmproj jako kandydat; przy PLLuM odpowiedź z samego tekstu |
| Budżet Nebius | strażnik bezczynności; plan ~92 $ z 123 $ |

---

## 8. Archiwum decyzji (skrót)

- sob 03:30 — trzy osobne rozwiązania (H-R1), baseline na gołym modelu (H-R3), `-Base` dozwolone (H-R2, potwierdzone 15:30).
- sob 13:30 — prompt organizatorów zostaje; esej akapitowy odrzucony; RAG dla dużych modeli w granicach szumu.
- sob 14:15 — oficjalny proces: harness wsadowy `exam.json` → `answers.json`; typ z `answer_format`.
- sob 14:30 — rozmiar: baza ≤ 8 GB, po treningu ≤ 8.8 GB; bez „pompowania” (wyższa precyzja, kopie, głosowanie).
- sob 16:30 — HyDE pomaga małym modelom (+6–8 pp).
- sob 18:30 — SFT małych modeli bez zysku; T3 = Qwen3.5-4B.
- sob 19:30 — przejście z Forgehand na Nebius (H100 + L40S); poprawki skryptów (`wait_runs`), sędziego (filtr treści) i danych (filtr zbieżności z arkuszami).
