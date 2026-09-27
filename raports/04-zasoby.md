# 04 — Dostępne zasoby

## Aktualizacja: sob 26.09, 19:45

| Maszyna | Stan | Koszt |
|---|---|---|
| Nebius H100 `matura-h100` (89.169.126.236) | działa od 17:44; trening + ewaluacje T1/T2 + egzamin | 3.85 $/h |
| Nebius L40S `matura-l40s` (`gpu-l40s-a`, 16 vCPU, 64 GB RAM; 89.169.112.149) | działa od 19:05; instalacja tylko do ewaluacji (`server/bootstrap_eval_vm.sh`) | ~1.7 $/h |
| Forgehand L40S | **zatrzymany** po drugiej awarii montażu `/workspace` (30 GB RAM nie mieści dwóch serwerów Qwen z obrazami); `/workspace` z wynikami przetrwał | przedpłacone |
| Modal | nieużywany od 17:30 | ~11 $ zostało |

- Obie maszyny Nebius należą do konta `tenant-e00j4265yye6dtbee1`, projekt `default-project-eu-north1`. Na obu działa `server/idle_shutdown.sh` (wyłączenie po 60 min bez zadań).
- **L40S na Intelu (`gpu-l40s-d`) był niedostępny** (NotEnoughResources po 6 min czekania). AMD (`gpu-l40s-a`) wstał. Dlatego maszyn nie usuwamy, tylko zatrzymujemy: przy ponownym tworzeniu sprzętu może zabraknąć.
- **Saldo w konsoli Nebius:** według dokumentacji saldo PAYG liczy się na bieżąco, a szczegóły są w Billing → Usage. Do 19:45 zużycie to ~7.5 $ (H100) + ~1.2 $ (L40S). Jeśli saldo stoi w miejscu, trzeba sprawdzić, czy w konsoli wybrany jest tenant `tenant-e00j4265yye6dtbee1` i czy Usage pokazuje Compute w `eu-north1`. Kredyt z kodu promocyjnego może też być pokazywany osobno od salda.
- Token Factory: nie planujemy pod niego.

## Aktualizacja: sob 26.09, 16:45 (obowiązuje zamiast tabeli z 13:40)

Najważniejsza zmiana: **Nebius daje drugą (i ewentualnie trzecią) kartę GPU równolegle do Forgehand**, więc każdy track może mieć własną maszynę. Solari to tylko CPU — pomocniczo.

| Zasób | Stan | Rola w planie |
|---|---|---|
| Serwer Forgehand, L40S 48 GB (4 vCPU, 32 GB RAM, 1.861 $/h) | ~195 $ z 200 $ (sesja od 13:54); do nd 12:00 zużyje jeszcze ~36 $, więc budżet nie ogranicza — ogranicza **1 sesja naraz** i tylko 4 vCPU | **T3**: SFT Qwen3.5-2B/4B, drabina kwantyzacji, RAG; przebieg T3 na egzaminie |
| **Nebius AI Cloud** | **123 $** | **T2** (LoRA 12B na H100), potem T1; nauczyciel z obrazami; bucket S3 do wymiany artefaktów |
| **Solari** | **200 $** | tylko CPU: mikro-VM do 16 vCPU / 64 GB RAM / 100 GB dysku; indeksy, kwantyzacja, orkiestrator zadań API |
| Forgehand LLM API | **30.57 $** z 50 $ (wydane 19.42 $) | sędzia (luna masowo, sol na bramkach), dodatkowe eseje i dane celowane |
| Modal | **13.64 $** (wydane 16.36 $ z 30 $; jedyna aplikacja ma 0 zadań, nic nie nalicza) | rezerwa: równoległe ewaluacje, awaria innej maszyny |
| Nebius Token Factory | możliwe kredyty, termin nieznany | jeśli przyjdą: nauczyciel widzący obrazy, drugi sędzia (API zgodne z OpenAI). Nie planujemy pod to |
| OpenAI | 0.47 $ | awaryjnie |

### Nebius — co działa, a co wymaga logowania

- Klucz w `.env` (`NEBIUS_CLOUD_API_KEY_ID` / `NEBIUS_CLOUD_API_KEY_SECRET`) to **klucz dostępu do Object Storage (S3)**, nie do Compute. Sprawdzone: `ListBuckets` działa (endpoint `https://storage.eu-north1.nebius.cloud`, obecnie 0 bucketów). **Maszyn GPU tym kluczem nie uruchomimy.**
- **CLI zalogowane (sob 17:15).** Profil `kolektyw` (domyślny) działa na koncie serwisowym `kolektyw`, projekt domyślny `project-e00vktr4pr003rw2ex8avm` (`default-project-eu-north1`). Konto serwisowe należy do projektu `eu-west2`, ale ma dostęp do `eu-north1` (sprawdzone: lista maszyn i platform działa). Agenci mogą więc sami tworzyć maszyny: `~/.nebius/bin/nebius compute instance create ...`.
- **Limity (quota) — wystarczające, ogranicza tylko budżet 123 $:**

  | Limit | Region | Wartość |
  |---|---|---|
  | H100 / H200 / L40S (zwykłe VM) | `eu-north1` | po 32 GPU |
  | liczba maszyn | każdy region | 12 |
  | maszyny wywłaszczalne | każdy region | 8 |
  | dysk Network SSD | `eu-north1` | 4 TiB |
  | **vCPU dla maszyn bez GPU** | **`eu-north1`, `us-central1`** | **0** — maszyn tylko-CPU tam nie ma; zadania CPU idą na maszynę GPU albo na Solari |
  | H200 | `eu-west1`, `us-central1` | 32 |
  | B200 / B300 / RTX PRO 6000 | `us-central1`, `me-west1`, `eu-west2`, `uk-south1`, `us-north1`, `eu-south1`, `uk-south2` | po 32 (dla nas za drogie lub zbędne) |

- **Platformy w `eu-north1`** (nazwa → preset z jedną kartą):
  - `gpu-h100-sxm` → `1gpu-16vcpu-200gb` (główna maszyna T2/T1),
  - `gpu-h200-sxm` → `1gpu-16vcpu-200gb`,
  - `gpu-l40s-a` (AMD) → od `1gpu-8vcpu-32gb`,
  - `gpu-l40s-d` (Intel) → od `1gpu-16vcpu-96gb`.
- Koszty poza GPU są pomijalne: publiczny IP 0 $; dysk Network SSD 0.000097 $/GiB/h (200 GiB ≈ 0.47 $/dobę); Object Storage (Standard) 0.00002 $/GiB/h, a pobieranie poza chmurę Nebius (np. na Forgehand albo laptop) 0.015 $/GiB (10 GB ≈ 0.15 $).
- Ceny GPU w `eu-north1` (od 1.06.2026), za godzinę:

  | GPU | Na żądanie | Wywłaszczalna | Godzin za 123 $ (na żądanie) |
  |---|---|---|---|
  | H100 80 GB (16 vCPU, 200 GB RAM) | 3.85 $ | 2.15 $ | ~32 h |
  | H200 141 GB | 4.50 $ | 2.45 $ | ~27 h |
  | L40S 48 GB, AMD (8 vCPU, 32 GB) | 1.35 $ + CPU/RAM = ~1.53 $ | ~0.74 $ | ~80 h |
  | L40S 48 GB, Intel (16 vCPU, 96 GB) | 1.35 $ + CPU/RAM = ~1.85 $ | ~0.90 $ | ~66 h |

  Przy H100/H200 CPU i RAM są w cenie karty. Przy L40S dolicza się CPU (0.010–0.012 $/vCPU/h) i RAM (0.0032 $/GiB/h).

- Maszynę wywłaszczalną Nebius może zatrzymać w każdej chwili, więc nocny trening bez nadzoru robimy na maszynie **na żądanie**. Wywłaszczalne tylko do ewaluacji, które da się wznowić.
- Plan wydatków:

  | Maszyna | Kiedy | Koszt |
  |---|---|---|
  | H100 na żądanie | sob ~17:30 → nd ~12:00 (18.5 h) | ~71 $ |
  | opcjonalnie L40S AMD na żądanie, tylko przy kolejce ewaluacji | ~12 h | ~19 $ |
  | dyski, IP, S3 | — | ~2 $ |
  | zapas | — | ~30 $ |

- Dla porównania: LoRA BF16 na modelu 12B (~2.5 tys. przykładów × 2 epoki) to szacunkowo ~15–25 min czystego treningu na H100 i ~45 min na L40S. H100 wybieramy dla zapasu pamięci (80 GB, dłuższe sekwencje, eseje ze źródłami) i szybszej ewaluacji, a nie dlatego, że L40S by nie wystarczył.

### Solari — co to jest

- **Nie jest to API LLM ani GPU.** To mikro-VM z samym CPU (Debian 12, Python 3.11, git, gcc, bez cmake), z dostępem do internetu, sterowane przez REST (`https://api.getsolari.com`, `POST /sandboxes`, `POST /sandboxes/:id/exec`). Maksymalnie 16 vCPU, 64 GB RAM, 100 GB dysku na maszynę.
- Test z 26.09 16:33 (1 vCPU, kilka sekund, < 0.01 $): maszyna wstała w ~1 s i przyjęła okno bezczynności 24 h, więc plan to najpewniej **Professional** (do 10 maszyn naraz, sesje do 24 h). Potwierdzić w konsoli.
- Cena na Professional: 16 vCPU / 64 GB ≈ 0.89 $/h, 8 vCPU / 16 GB ≈ 0.32 $/h. 200 $ to więcej, niż zdążymy zużyć.
- Zastosowania — tylko gdy CPU na maszynach GPU jest wąskim gardłem (Forgehand ma 4 vCPU, a kompilacja llama.cpp zajęła tam ~40 min):
  - budowa większego indeksu BM25 (Wikipedia po sekcjach + kompendium) i wysyłka do S3 Nebius,
  - kwantyzacja GGUF i imatrix dla modeli T3 (≤ 4B),
  - stały orkiestrator zadań API (sędzia, generowanie danych), niezależny od laptopa — lokal zamykają o 24:00.
- Nie trenujemy tam i nie serwujemy modeli.

### Forgehand LLM API — realne koszty

- Stan na 16:28: 30.57 $ dostępne. `gpt-6-luna`: 0.80 $ za 3 692 zapytania (~0.0002 $ za zapytanie). `gpt-6-sol`: 18.62 $ za 1 666 zapytań (~0.011 $ za zapytanie).
- Ceny w `data_gen/common.py` (`PRICES`) zawyżają lunę ok. 4–5 razy, a sol o ~15%. Dlatego szacunek subagenta (28.83 $) był wyższy od realnego wydatku (~19 $).
- Wniosek: ocena lunką praktycznie nic nie kosztuje (~0.01 $ za arkusz), więc oceniamy każdy przebieg. Sol zostaje na bramki i eseje.
- Podział reszty: dodatkowe eseje przez sol ~10 $ (~350–400 szt.; E4 kosztowało realnie ~0.025 $ za esej), dane celowane po analizie błędów ~8 $, sędzia sol na bramkach ~4 $, rezerwa ~8 $.

## Aktualizacja: sob 26.09, 13:40 (obowiązuje zamiast starszych kwot poniżej)

| Zasób | Stan | Zastosowanie |
|---|---|---|
| **Serwer Forgehand (Labqoat)** — 40 GB VRAM, 200 $ compute (`app.forgehand.app`) | nowy | **główny trening** (LoRA/QLoRA do 12B), serwowanie modeli na egzamin |
| **Forgehand LLM API** — 50 $, modele `gpt-6-sol` i `gpt-6-luna` | nowy | **sędzia** (po kalibracji) i **nauczyciel** do danych syntetycznych (wzorowe odpowiedzi, eseje). Ograniczenia: tylko tekst (bez obrazów), maks. 32 768 tokenów wyjścia, timeout 3 min. Endpoint zgodny z OpenAI: `https://app.forgehand.app/api/v1/teams/01a0da5f-05f4-700d-a554-4c8f829182f1/llm/v1` |
| Modal | **13.64 $** | krótkie przebiegi ewaluacyjne (L4 / L40S), konwersje GGUF |
| OpenAI | **0.47 $** | praktycznie wyczerpane — tylko awaryjnie |
| Gemini / AI Studio | **brak** (środków nie ma) | — |
| Kaggle / Colab | darmowe T4 | pilotaże małych modeli |

**Ograniczenie Forgehand:** zespół może mieć **tylko 1 sesję GPU naraz** (próba drugiej: „your team already has 1 GPU session running”). Klasy: `gpu-l40s-small` (L40S 48 GB, 4 vCPU, 32 GB RAM, 1.861 $/h) i klasy CPU (0.20–0.81 $/h). Jedna L40S przez 21 h to ok. 39 $ z 200 $, więc większość budżetu zostaje. Równoległość GPU dają tylko Modal (13.64 $) i darmowe Kaggle/Colab — albo prośba do organizatorów (Labqoat) o podniesienie limitu.

**Forgehand LLM API — koszt realny:** kalibracja 104 ocen przez `gpt-6-luna` i 104 przez `gpt-6-sol` kosztowała łącznie **0.49 $** (szacunek w skrypcie: 1.20 $). Efektywne ceny to ok. 0.4 $/M wejście i 2.5 $/M wyjście dla luny oraz ok. 2 $/M i 12 $/M dla sol (szacunek z jednego pomiaru; do potwierdzenia po pierwszej partii generowania).

Wnioski:
- Sędzia i nauczyciel przechodzą na Forgehand LLM API. Obrazów nie obsługuje, więc przy zadaniach z obrazem daje rozwiązanie CKE i opis zamiast obrazu.
- Trening na serwerze 40 GB: LoRA BF16 do ~9B i QLoRA dla 12B.

Stan na pt 25.09.2026, ~24:00. Do końca treningu (nd 11:00): **~35 h**. Kwoty i ceny godzinowe są orientacyjne — przed większym wydatkiem sprawdź aktualny cennik.

---

## 1. Sprzęt lokalny

| Zasób | Parametry | Do czego się nadaje |
|---|---|---|
| CPU | Intel i7-1165G7 (4 rdzenie / 8 wątków, 2.8–4.7 GHz, AVX-512) | przygotowanie danych, skrypty, RAG (embeddingi małym modelem, BM25), testy małych GGUF przez llama.cpp |
| RAM | 16 GB DDR4 (wspólne z systemem i WSL2) | inferencja CPU modeli do ~4B w Q4/Q8; 12B w Q4 (~7 GB) się zmieści, ale będzie bardzo wolno |
| GPU | Intel Iris Xe (zintegrowane) | praktycznie nieużyteczne (ew. llama.cpp z Vulkan/SYCL — niewielki zysk, nie warto tracić czasu) |
| System | Linux w WSL2 | — |

Orientacyjna prędkość llama.cpp na tym CPU (generowanie): model 1–2B Q4 ≈ 20–35 tok/s, 4B Q4 ≈ 8–15 tok/s, 12B Q4 ≈ 2–4 tok/s. Przetwarzanie promptu jest kilka razy szybsze, ale długie źródła i tak spowalniają.

Wnioski:
- **Lokalnie nie trenujemy.** Lokalnie da się przygotować dane, zbudować RAG i szybko sprawdzać małe modele.
- **Egzamin na scenie ma trwać „kilka minut”**, a z modelem 12B z myśleniem to niewykonalne na tym laptopie. Egzamin trzeba puścić na GPU w chmurze (to dozwolone — zakaz dotyczy internetu i zewnętrznych API AI, nie lokalizacji modelu). Dla modelu 1–2B bez myślenia laptop może wystarczyć jako plan awaryjny.

## 2. Budżety chmurowe i API

| Zasób | Ile | Najlepsze zastosowanie |
|---|---|---|
| **Google AI Studio** (Gemini API, Tier 1) | 61 $ | generowanie danych syntetycznych po polsku: pytania w stylu CKE, odpowiedzi wzorcowe, **eseje wzorcowe wg kryteriów CKE**, opisy obrazków; lokalny sędzia; embeddingi do RAG |
| **Google Cloud** | 1 114 zł kredytów, zużyte 244 zł → **zostało ~870 zł (~215–240 $)** | Vertex AI (Gemini do generowania danych na większą skalę, batch), VM z GPU (L4/A100 — sprawdź limity/kwoty, na nowych kontach często 0), **TPU** (patrz niżej) |
| **Modal** | 29 $ (+ darmowy Starter 30 $/mies. — sprawdź, czy to te same środki) | krótkie treningi LoRA i ewaluacje; serwowanie modelu na egzaminie (vLLM) |
| **L40 / H100** (później) | nieznany czas dostępu | główny trening (SFT/LoRA modeli 4–12B), szybka ewaluacja, serwowanie na egzamin |
| **OpenAI API** (później) | 100 $ | dane syntetyczne wysokiej jakości (eseje, uzasadnienia), sędzia zbliżony do oficjalnego (strona benchmarku jest na chatgpt.site, a referencyjne przebiegi robił GPT — możliwe, że oficjalny sędzia to model OpenAI) |
| **Cursor** | 200 $ kredytów (każdy uczestnik) | praca z agentem przy kodzie |
| **Google Colab** (darmowy) | GPU T4 16 GB, sesja do ~12 h, rozłącza przy bezczynności, dzienny limit zmienny i nieogłaszany | eksperymenty: QLoRA modeli 1–4B (Unsloth), testy kwantyzacji GGUF, szybkie ewaluacje, generowanie embeddingów do RAG |
| **Kaggle Notebooks** (darmowy) | GPU: **~30 h/tydz.** (2× T4 16 GB albo P100 16 GB), sesja do 12 h; TPU ~20 h/tydz.; ~20 GB zapisu w `/kaggle/working`; internet po weryfikacji telefonu | dłuższe eksperymenty w tle (notebook „Save & Run All” działa bez otwartej przeglądarki), QLoRA do ~8B na 2× T4, ewaluacje równoległe |
| Sponsorzy (ze slajdów, nie ma ich w Twojej notatce) | **Nebius** (kod kredytowy dla każdego uczestnika), **Labqoat** (2 000 $ podzielone po równo między zespoły; `app.forgehand.app`) | dodatkowe GPU — warto odebrać, jeśli jeszcze nie odebrane (stolik przy wejściu / Telegram) |

### Ile GPU-godzin to daje (orientacyjnie)

| Budżet | L4 (~0.8 $/h) | A100 80GB (~2.5 $/h) | H100 (~4 $/h) |
|---|---|---|---|
| Modal 29 $ | ~36 h | ~11 h | ~7 h |
| GCP ~230 $ (jeśli jest kwota GPU) | ~280 h | ~90 h | ~55 h |

Do tego darmowo: Kaggle ~30 h T4/P100 tygodniowo (aktualny pozostały limit widać w ustawieniach konta) + Colab T4 w miarę dostępności. Z dwóch kont zespołu limity się sumują.

### Colab i Kaggle — na co uważać

- **T4 nie obsługuje BF16** — trenuj w FP16 albo 4-bit (QLoRA); Unsloth ma gotowe notebooki pod T4/Kaggle.
- T4 jest ~4–6× wolniejsze od A100: QLoRA modelu 1–2B na kilku tysiącach przykładów to godzina–dwie, modelu 4B kilka godzin; modele 9–12B lepiej trenować na L40/H100.
- Sesje się zrywają: zapisuj checkpointy co kilkaset kroków na Google Drive / Kaggle Dataset / HF Hub i wznawiaj trening.
- Kaggle w trybie „Save & Run All” pozwala zostawić trening na noc bez otwartego laptopa (dobre, bo lokal jest zamknięty 24:00–9:00).
- Nie nadają się do serwowania modelu na egzaminie (brak stabilnego publicznego endpointu, sesja może wygasnąć).
- Dobre do równoległych eksperymentów: np. Kaggle trenuje wariant A, Colab wariant B, a Modal/L40 robi główny przebieg.

Dla skali: LoRA na modelu 4B na 6 mln tokenów to 1.3–5 h na A100, a jedna pełna ewaluacja małego modelu kosztuje < 0.25 $ (raport 03).

### TPU w Google Cloud — czy warto?

Technicznie się da (JAX / MaxText, `optimum-tpu`, PyTorch/XLA), ale:
- wymaga konfiguracji innej niż zwykły stos HF/PEFT/Unsloth, co przy 35 h jest kosztowne czasowo,
- kwoty TPU trzeba mieć przyznane w danym regionie,
- część modeli (np. multimodalne) i bibliotek (bitsandbytes, Unsloth) na TPU nie działa.

Rozsądniej przeznaczyć kredyty GCP na **Vertex AI Gemini** (dane syntetyczne, sędzia) albo na VM z GPU, jeśli kwota jest dostępna. TPU tylko wtedy, gdy masz już działający przepis JAX.

## 3. Zasoby danych i wiedzy

| Zasób | Uwagi |
|---|---|
| `assets/benchmark-2023/` | arkusz CKE 2023 (tekst + strony PNG), klucz CKE, oceny sędziego dla 25 przebiegów — **walidacja lokalna** (nie trenować na nim) |
| Arkusze i zasady oceniania CKE (inne lata, poziom rozszerzony, stara i nowa formuła) | cke.gov.pl — najlepsze źródło formatów zadań i przykładowych odpowiedzi; w repo tylko linki + skrypt pobierający (prawa autorskie) |
| Informatory CKE, zbiory zadań | jak wyżej |
| **Wikipedia PL** (dump) | CC BY-SA — wolno umieścić w bazie RAG (nie liczy się do 8 GB) i trenować; zbiory pochodne na CC BY-SA |
| ZPE (zpe.gov.pl) | źródło, z którego korzystał sędzia do sprawdzania faktów; sprawdź licencję przed użyciem do treningu |
| Dane syntetyczne z Gemini / OpenAI | dozwolone; najcenniejsze: eseje wg kryteriów CKE, pytania z historii XX w./PRL (najsłabszy obszar modeli), uzasadnienia z odwołaniem do źródła |
| Modele bazowe na HF | Bielik (speakleash), PLLuM (CYFRAGOVPL), Qwen3 / Qwen3.5, Gemma 3 / 4, Llama, gotowe GGUF-y |

## 4. Ograniczenia czasowe

| Do kiedy | Co |
|---|---|
| **sob 12:00** | pełny skład zespołu w aplikacji |
| sob (w ciągu dnia) | skrypt egzaminacyjny i instrukcje od organizatorów; sloty mentorów 12:00–18:00 |
| sob 24:00 → nd 9:00 | lokal zamknięty — nocny trening tylko w chmurze |
| **nd 11:00** | zamrożenie modelu i harnessu, repozytorium z `SOURCE.md` udostępnione jury, wyniki bazowe + wytrenowane zgłoszone |

## 5. Co ta pula zasobów umożliwia

1. **Dane (lokalnie + Gemini/OpenAI):** RAG z Wikipedii PL (BM25 + mały embedder na CPU) oraz syntetyczny zbiór SFT: kilka tysięcy pytań w stylu CKE + ~200–500 esejów wzorcowych. Koszt API: kilkanaście–kilkadziesiąt $.
2. **Trening (Kaggle/Colab → Modal → L40/H100):** darmowe T4 na eksperymenty z małymi modelami (1–4B, QLoRA), Modal na krótkie szybkie przebiegi, model 9–12B dopiero na L40/H100.
3. **Ewaluacja:** lokalny benchmark 34 zadań (raport 02) + sędzia na Gemini/GPT z rekonstrukcją promptu sędziego — koszt poniżej 1 $ za przebieg.
4. **Egzamin:** serwer vLLM / llama.cpp na L40/H100 (albo Modal) z równoległymi zapytaniami. Laptop jako plan awaryjny tylko dla małego modelu.

Ryzyka:
- dostęp do L40/H100 przychodzi „później” — pierwsze eksperymenty najlepiej robić na Kaggle / Colab / Modal / Nebius / Labqoat,
- limit Tier 1 w AI Studio (RPM/TPM) może spowolnić masowe generowanie danych; wtedy przejście na Vertex AI batch z kredytów GCP,
- WSL2 i 16 GB RAM: przy dużych plikach (dump Wikipedii, indeks) pilnuj limitu pamięci WSL (`.wslconfig`).
