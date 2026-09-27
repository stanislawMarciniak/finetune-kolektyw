# 21 — T3: powtórka z myśleniem zamiast fallbacku i powtórka dopasowań z cyframi (nd 27.09, 07:25–08:15)

**Wniosek: obie flagi włączone w T3 tuned** (`--think-retry --match-retry` w `server/final_configs.json`, poprzednia wersja w `_comment_T3_old3`). Zysk jest mały, w granicach szumu (~+0.2–0.3 pkt/arkusz), ale zmiana dotyka tylko zadań, które dziś tracą punkty przez fallback albo cyfry zamiast nazw. Pozostałe zadania są identyczne, bo kod wchodzi tylko przy wyzwoleniu. Testy na H100 na pliku MIX (`Qwen3.5-4B-IQ2_M-PL-E4K-MIX.gguf`). Inny agent w międzyczasie przełączył T3 na `MIX-S4K-V124K` (raport 18). Flagi działają tylko w harnessie, więc nie zależą od pliku modelu.

## Flagi (`harness/run_exam.py`, domyślnie wyłączone)

- `--think-retry`: gdy myślenie się urwie (`finish = length`) albo odpowiedź po myśleniu jest pusta, harness raz ponawia pytanie **z myśleniem**, z seedem +7 i tym samym limitem (`--max-tokens`, budżet serwera 5000). Dopiero gdy i to się nie uda, jest stary fallback bez myślenia. W `debug.jsonl` zapisuje się pole `think_retry`; `fallback` = odpowiedź ostatecznie bez myślenia.
- `--match-retry`: dotyczy dopasowań z `match_wants_names` (wzór „A: 1”, polecenie chce nazw; te same zadania co w raporcie 14). Gdy po normalizacji któraś wartość to same cyfry, harness:
  1. bierze nazwy z ostatniego bloku „A: …” odpowiedzi modelu, bez redukcji do numeru. Wtedy „Władysław II (1140–1158)” nie zamienia się w „1140”, a „A: 24 / B: 1598” (liczby wyjęte z rozważań) w odpowiedź modelu. To dzieje się bez wywołania modelu;
  2. jeśli nadal są cyfry, raz ponawia to samo zapytanie z seedem +11 i tą samą konfiguracją myślenia. Nową odpowiedź przyjmuje tylko wtedy, gdy każda wartość ma litery i ≤ 60 znaków.

  **Bez wskazówki `MATCH_NAMES_HINT`**, bo ta szkodziła w raporcie 14. Odpowiedź z samych cyfr przy kluczu z nazwami ma zawsze 0 pkt, więc podmiana nie może jej pogorszyć.

## Metoda

- Odniesienie: `q35-4b-q2-iq2mpl-e4k-mix__struct2-s42/s43` (2024, 2025), `-s42` (2026). Fallbacków było 2 / 1 / 0 / 3 / 3 (+1 w `s43-2026-fh`), czyli ~1.7 na arkusz. Cyfry w dopasowaniu wystąpiły 3 razy: 2024/11.1 s43, 2025/4 s43, 2025/5.1 s43.
- Przebiegi (`server/t3_retry.sh`, `server/t3_retry2.sh`) mają `--only-ids` na zadaniach z fallbackiem albo cyframi i `--merge-from` z bazy. To jest poprawne, bo flagi zmieniają tylko te zadania. Świeże ponowienie jednak losuje nową pierwszą próbę, a ta zwykle się udaje. Dlatego porównuję **odpowiedzi z myśleniem i bez myślenia na tych samych 9 zadaniach**:
  - `rt-*`: flagi, seedy 42/43 (po jednym na bazę), 44, 45; do tego przebiegi bazowe innego seeda, w których dane zadanie nie wpadło w fallback;
  - `nt-*`: `--think ""`, czyli dokładnie to, co daje dzisiejszy fallback, seedy 44 i 45; do tego same odpowiedzi fallbacku z bazy.
- Ocena: `grade.py` (zamknięte), sędzia `gpt-6-luna` (otwarte). Pozostałe oceny skopiowane przez `judge_reuse.py`. **Koszt sędziego $0.104** (0.018 + 0.073 + 0.013).
- Test ścieżki kodu: `rt-smoke` z `--max-tokens 1200`. Myślenie urywa się, powtórka też, potem działa fallback bez myślenia. 3 wywołania, bez wyjątków.

## Wyniki

**Wyzwolenia `--think-retry`:** 7 na 27 świeżych prób (2024/19.2 ×3, 2024/25, 2025/5.2, 2026/6.2 ×2). Powtórka udała się w 5 z 7. 2026/6.2 zapętla się za każdym razem, więc tam zostaje fallback jak dotąd.

| Zadanie (z fallbackiem w bazie) | z myśleniem: śr. pkt (n) | bez myślenia = fallback: śr. pkt (n) |
|---|---|---|
| 2024/9 rozstrz | 0.50 (4) | 0.67 (3) |
| 2024/25 open | **2.00** (4) | 1.33 (3) |
| 2024/19.2 podaj | 0.25 (4, wszystkie po powtórce) | 0.00 (3) |
| 2025/5.2 rozstrz | 0.50 (4) | **1.00** (3) |
| 2025/9.3 podaj | 0 (4) | 0 (3) |
| 2025/14.1 rozstrz | 0 (4) | 0 (3) |
| 2026/6.2 rozstrz | 0 (2) | 0 (5) |
| 2026/8 rozstrz | **1.00** (4) | 0.33 (3) |
| 2026/16.2 podaj | 0.50 (4) | 0.33 (3) |
| **razem** | **0.56 pkt/odp.** (19/34) | **0.38 pkt/odp.** (11/29) |

- Różnica to +0.18 pkt na zadanie z fallbackiem (suma różnic średnich po zadaniach: +1.1 pkt na 8 zadań). Przy ~1.7 fallbacku na arkusz i skuteczności ~70% daje to **~+0.2 pkt/arkusz**, mniej niż szacował audyt (+1–2 pkt na 3 arkusze). Same odpowiedzi po powtórce (5 sztuk) mają 2 pkt, a bez myślenia na tych zadaniach oczekiwane 2.3, czyli remis.
- Przed/po bezpośrednio (seedy bazowe, zadania z fallbackiem i cyframi, scalone): 2024 s42 **+1** (25: 0 → 1), 2024 s43 0, 2025 s43 0, 2026 s42 0 (8: 0 → 1, 16.2: 1 → 0). Razem 2024+2025: **+1 pkt na 2 seedy**; 2026: 0.

**Wyzwolenia `--match-retry`:** 3 w bazie (odtworzone offline na zapisanych odpowiedziach) i 1 w nowych przebiegach.
- 2024/11.1 s43: bez redukcji „A: Małgorzata / B: Małgorzata” (0 → 0);
- 2025/5.1 s43: „Władysław II (1140–1158)” (0 → 0);
- 2025/5.1 s45: cyfry „A: 2 / B: 3” → powtórka → „Władysław II / Władysław II” (0 → 0; klucz: Wacław II, Brzetysław I).
- 2025/4 s43 („A: 1 / B: 2 / C: 3”) to jedyny przypadek z punktami w grze. W świeżych próbach model podał nazwy 5 razy na 5 („Franciszkanie/Benedyktynowie/Jezuici”, „Zakon Braci Mniejszych/…”), więc powtórka prawie na pewno da nazwy. Egzaminator dałby za nie 2 pkt; nasz ścisły `grade.py` daje 0–1 (raport 20: „grader za surowy”). Oczekiwany zysk ≈ +2 pkt × P(cyfry) ≈ 1/6 ≈ **+0.3 pkt na arkusz z takim zadaniem**.

**Czas:** zadanie z wyzwoleniem trwa 150–365 s zamiast ~60–100 s (na współdzielonym H100). Pierwsza próba zjada już 8000 tokenów, a powtórka dokłada do 8000 kolejnych (~100 s przy ~77 tok/s na slot). Wyzwolenia dotyczą ~2 zadań na arkusz, a inne zadania idą równolegle. Arkusz trwa więc najwyżej ~2–4 min dłużej, gdy zadanie z powtórką kończy się ostatnie.

## Test na sucho

`bash server/exam_run.sh assets/mock-2023 T3 tuned 8933` na H100, z nowym `final_configs.json` (MIX-S4K-V124K + obie flagi): **OK**, 37 odpowiedzi, `check_answers.py`: 0 pustych, 0 błędów.
- Wall 892 s. H100 był wtedy mocno współdzielony: 7 serwerów llama, 100% GPU, ~25 tok/s na slot zamiast ~77, więc to nie jest czas miarodajny.
- `--think-retry` wyzwolił się 3 razy: 5.2 udany, a 25.1 i 25.2 urwane ponownie, więc poszedł fallback bez myślenia. Najdłuższe zadanie (5.2, z powtórką) trwało 499 s, następne 300 s.
- `--match-retry` się nie wyzwolił.
- Wynik testu leży w `runs/final/T3-tuned-rtdry`. Wcześniejszy `runs/final/T3-tuned` innego agenta przywróciłem bez zmian.
- Wniosek na egzamin: przy wolnym GPU dodatkowy czas to ~2–4 min na arkusz. Na współdzielonym ~5–8 min, bo zadanie z powtórką kończy się ostatnie.

## Ograniczenia

- Małe n (4 seedy × 9 zadań), więc zysk +0.18 pkt/zadanie mieści się w szumie. Decyzja opiera się na tym, że flaga nie zmienia pozostałych zadań, a średnia wychodzi dodatnia.
- Test na MIX, a finał ma teraz MIX-S4K-V124K (raport 18). Częstość fallbacków może się różnić, ale logika flag jest ta sama.
