# 21 — T3 na H100: „CUDA error: illegal instruction” w clip_encode

Stan: nd 27.09.2026, ~08:40 CEST. `server/final_configs.json` bez zmian. Skrypty: `work/illegal/` (lokalnie i na H100 `~/repo/work/illegal/`).

## Wynik

- **Przyczyna: (b)+(c)** — ogólny błąd ścieżki CUDA wizji (mmproj, `clip_encode`) na H100 przy **grafach CUDA** i kilku serwerach naraz; **nie** przycięty słownik (a).
- **Poprawka:** `server/exam_run.sh` dla T3 ustawia `GGML_CUDA_DISABLE_GRAPHS=1` (te same kernele, inne tylko uruchamianie → wyniki bez zmian). Zsynchronizowane na H100 i L40S (md5 `9bd5653c…`).
- Pełne obciążenie egzaminu (T1 + T2 z opisami + T3 tuned + T3 base naraz, zimny start, mock 2023): **z grafami 4 awarie T3 na 7 startów, bez grafów 0/4**.

## Dowody

1. **Ta sama sygnatura u Gemmy (T1)**: backtrace `ggml_backend_cuda_synchronize ← clip_encode ← mtmd_batch_encode` w `~/logs/server_8811.log` (6 awarii, 03:20–03:52 UTC), `server_8291.log`, `server_8206.log` — inny model tekstowy i inny mmproj, ten sam błąd.
2. **dmesg (od startu maszyny 00:01 UTC)**: Xid 13 „Graphics SM Warp Exception: Illegal Instruction Parameter” + Xid 43 tylko w dwóch seriach: 03:20–03:52 (Gemma) i 05:28:30 (suchy test T3), rejestry ESR identyczne (`…728=0x1f81fb60 …72c=0x1174`) — ten sam wadliwy kernel. O 05:28:30 padły **oba** serwery T3 (tuned 8403 i base 8413) w tej samej sekundzie, ~10 s po starcie.
3. **Starsze konfiguracje T3**: żaden log Qwen3.5-4B (Q3_K_M, UD-IQ3_XXS, MIX, także MIX-S4K-V124K s44 na H100, `-np 24`) nie ma awarii przed dzisiejszym suchym testem (logi `server_<port>.log` są nadpisywane, ale dmesg potwierdza brak Xid dla Qwena przed 05:28). Restart w `server_8831.log` (UD-IQ3_XXS) to SIGKILL, nie awaria.
4. **Odtworzenie** (flagi T3 z `final_configs.json`, własne porty):

| Test | Wynik |
|---|---|
| V124K sam, 3 zimne starty × 33 zapytania z obrazami (mock 2023 + 10 z 2024) | 0 awarii |
| V124K + MIX (bez przycięcia) + Gemma T1 naraz, 3 × (3 × 33) | 0 awarii |
| Pełny egzamin naraz (kopia `exam_run.sh`, 150 s), grafy włączone | 1/1 ważny start (+ suchy test 05:28 = 2 serwery) |
| to samo, `GGML_CUDA_PDL=0` | 2/4 (awaria T3 ~10.2–10.4 s po starcie) — PDL nie jest przyczyną |
| to samo, **`GGML_CUDA_DISABLE_GRAPHS=1`** | **0/4** |

Awarie zawsze w serwerze T3, ~10 s po starcie, przy kolejnych kodowaniach obrazów o tym samym kształcie (w mocku zadania 5.x i 13.x mają te same obrazy) — wtedy llama.cpp po rozgrzewce przechwytuje i odtwarza graf CUDA dla `clip_encode`. Przycięty słownik nie bierze udziału w kodowaniu obrazu (osadzenia obrazu idą jako embd, bez id tokenów).

## Uwagi

- Wyłączenie grafów może nieco spowolnić dekodowanie T3; T1/T2 bez zmian. Gemma (T1) historycznie miała ten sam błąd (nadzorca go obsługuje); w 11 startach pod pełnym obciążeniem dziś nie padła. W razie potrzeby to samo dla T1: zmienić warunek w `exam_run.sh`.
- Nadzorca w `lib_eval.sh` i ponawianie w harnessie zostają (awaria = ~10 s straty, odpowiedzi kompletne).
