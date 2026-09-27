# 08b — Trafność wyszukiwania (top-3), zadania „podaj/wymień/nazwij” z krótkim kluczem

Zadań: 32 (Polska 20, powszechna 12). HyDE Qwen-2B dostępne dla 22 zadań. Generowane przez `eval/retrieval_bench.py`.

| baza | metoda | polecenie+źródła / Polska | polecenie+źródła / powszechna | polecenie+źródła / razem | nazwy własne / Polska | nazwy własne / powszechna | nazwy własne / razem | HyDE Qwen-2B + polecenie / Polska | HyDE Qwen-2B + polecenie / powszechna | HyDE Qwen-2B + polecenie / razem |
|---|---|---|---|---|---|---|---|---|---|---|
| PolQA | BM25 | 25% | 17% | 22% | 15% | 0% | 9% | 25% | 25% | 25% |
| PolQA + top-1 z każdej bazy | BM25 | 55% | 42% | 50% | 15% | 25% | 19% | 60% | 50% | 56% |
| kompendium | BM25 | 30% | 17% | 25% | 10% | 17% | 12% | 40% | 33% | 38% |
| kompendium | dense | 30% | 42% | 34% | 25% | 33% | 28% | 30% | 42% | 34% |
| kompendium | hybryda RRF | 45% | 50% | 47% | 15% | 42% | 25% | 40% | 50% | 44% |
| persons | BM25 | 10% | 8% | 9% | 5% | 17% | 9% | 20% | 8% | 16% |
| persons | dense | 25% | 0% | 16% | 5% | 8% | 6% | 20% | 0% | 12% |
| persons | hybryda RRF | 15% | 17% | 16% | 5% | 8% | 6% | 20% | 17% | 19% |
| terms | BM25 | 10% | 17% | 12% | 0% | 8% | 3% | 20% | 17% | 19% |
| terms | dense | 15% | 25% | 19% | 5% | 8% | 6% | 25% | 25% | 25% |
| terms | hybryda RRF | 15% | 17% | 16% | 10% | 8% | 9% | 20% | 17% | 19% |
| timeline | BM25 | 35% | 25% | 31% | 10% | 25% | 16% | 40% | 25% | 34% |
| timeline | dense | 30% | 17% | 25% | 25% | 0% | 16% | 40% | 8% | 28% |
| timeline | hybryda RRF | 50% | 8% | 34% | 25% | 25% | 25% | 50% | 17% | 38% |
| zadania_z_kluczem | BM25 | 15% | 25% | 19% | 15% | 25% | 19% | 50% | 17% | 38% |
| zadania_z_kluczem | dense | 20% | 8% | 16% | 20% | 17% | 19% | 30% | 8% | 22% |
| zadania_z_kluczem | hybryda RRF | 30% | 17% | 25% | 25% | 25% | 25% | 40% | 17% | 31% |
