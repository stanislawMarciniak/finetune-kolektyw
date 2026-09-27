"""Uruchamia orkiestratora wdrożonej aplikacji `matura-baselines` (działa bez otwartego laptopa).

    modal deploy overnight/modal_baselines.py && python overnight/launch_modal.py [nazwa_zestawu]
Zestawy: domyślnie RUNS z modal_baselines.py; "wave2" = przebiegi na arkuszach 2024–2026.
"""

import json
import sys

import modal

WAVE2_MODELS = ["gemma4-12b-qat", "q35-9b-q5", "bielik-11b-v3-q5", "q35-4b-q4", "q35-2b-q4", "bielik-1.5b-q8"]
WAVE2_SETS = ["test2024_split", "test2025_split", "test2026_split"]


def main():
    wave = sys.argv[1] if len(sys.argv) > 1 else "wave1"
    fn = modal.Function.from_name("matura-baselines", "orchestrate")
    if wave == "wave1":
        call = fn.spawn()
    else:
        runs = [(m, s, 42) for s in WAVE2_SETS for m in WAVE2_MODELS]
        call = fn.spawn(runs, "wave2")
    print(json.dumps({"wave": wave, "call_id": call.object_id}))


if __name__ == "__main__":
    main()
