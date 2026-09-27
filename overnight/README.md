# Zadania nocne

Uruchomione w nocy z 25 na 26.09. Wszystko jest bezpieczne do ponownego uruchomienia (gotowe kroki są pomijane).

## Co działa

| Tor | Co | Gdzie | Weryfikuje (raport 07) |
|---|---|---|---|
| Lokalnie | `local/cke_crawl.py` → `local/pdf_extract.py`: arkusze, zasady i informatory z historii (formuła 2023, 2015, stara matura, historia sztuki) + tekst, rendery stron, wycinki obrazów | `data/cke/` | H-T10 (materiał do ekstrakcji) |
| Lokalnie | `local/build_kb.py`: korpus PolQA (7 mln pasaży plwiki) + indeks BM25 (tantivy, pola `raw` i `stem`) + recall@k na pytaniach PolQA; pobranie polskiej Wikipedii | `data/kb/` | H-H2 (czy obcinanie słów pomaga BM25 po polsku) |
| Modal, fala 1 | 17 konfiguracji na `dev2023_text` + 5 na `dev2023_img` + 3 powtórzenia seedów (llama.cpp, prompt organizatorów) | wolumen `matura-results` | H-M1, H-M2, H-M3, H-M4, H-M6, H-M8, H-M9, H-I1, H-I2, H-E4 |
| Modal, fala 2 | 6 modeli × arkusze 2024, 2025, 2026 w formacie finału (tekst + osobne obrazy; modele tekstowe dostają sam tekst) | wolumen `matura-results` | H-E3, H-E5, H-M2, H-M4, H-M9 |

## Uruchomienie od zera

```bash
./overnight/run_local.sh                                   # zadania lokalne (setsid, przeżywają zamknięcie terminala)
modal deploy overnight/modal_baselines.py                  # aplikacja na Modal
~/.local/share/uv/tools/modal/bin/python overnight/launch_modal.py wave1
~/.local/share/uv/tools/modal/bin/python overnight/launch_modal.py wave2
```

## Rano

```bash
tail -n 5 overnight/logs/*.log                             # stan zadań lokalnych
cat data/kb/retrieval_eval_polqa.json                      # H-H2
modal volume get matura-results / results/ --force         # wyniki z Modal
.venv/bin/python eval/grade.py results/                    # zamknięte automatycznie, otwarte -> results/review/
# sędzia (Claude, potem GPT) ocenia results/review/*/*.md i zapisuje results/grades/*/*.judge.json
.venv/bin/python eval/report.py                            # tabela -> results/report.md
```

Szacowany koszt Modal: fala 1 ≈ 8–10 $, fala 2 ≈ 7 $ (L4 ≈ 0.8 $/h, L40S ≈ 1.95 $/h).

## Druga część nocy (od ~03:30)

- Sędzia: `eval/judge_openai.py` (`gpt-5.4-mini`, kalibracja 92% zgodności). Wydane ok. 2.7 $ z 5 $ (szacunek z cennika w skrypcie — sprawdź w panelu OpenAI).
- `eval/rag_precompute.py`: kontekst RAG (BM25 `stem`, top-4) dopisany do zadań → `eval/data/*_rag.jsonl`; `essays12_rag.jsonl` = 12 tematów esejów z lat 2023–2026.
- **Fala 4 (Modal):** harness `v1` (format per typ), `v1rag` (+RAG), esej `v1rag` vs `v1sect` (akapit po akapicie) dla Gemma-4-12B, Bielik-11B, Qwen3.5-4B, Qwen3.5-2B, Bielik-1.5B. Log: `overnight/logs/modal_wave4.log`.
- `overnight/after_wave4.sh` (działa w tle): po zakończeniu fali 4 pobiera wyniki, ocenia (limit 1.3 $: najpierw eseje, potem 2024) i odświeża `results/report.md`. Log: `overnight/logs/after_wave4.log` (koniec = `AFTER_WAVE4_DONE`).
