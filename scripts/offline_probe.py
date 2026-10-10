#!/usr/bin/env python3
"""
One call from each workflow, for the offline test.

    python3 scripts/offline_probe.py

Deliberately separate from run.py. The offline test asks whether inference
still works with no network, not how well the models score, so this runs
three calls instead of ninety-five and writes nowhere near results/.
Keeping it out of the measurement path means it cannot contaminate a run.

Prints a verdict and exits non-zero if any call failed, so a shell script
can act on it.
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from run import PROMPTS, OllamaError, corpus_text, load, ollama  # noqa: E402

MODEL = sys.argv[1] if len(sys.argv) > 1 else "smollm2:360m"


def probe(label, prompt):
    print(f"  {label:<16} ", end="", flush=True)
    try:
        reply, met = ollama(MODEL, prompt)
        tps = met.get("tps")
        speed = f"{tps:.1f} tok/s" if tps else "no timing"
        print(f"OK   {speed:<14} {reply.strip()[:60]!r}")
        return True
    except OllamaError as e:
        print(f"FAILED ({e.kind})\n      {e}")
        return False


def main():
    ex = load("extraction.jsonl")[0]
    cl = load("classification.jsonl")[0]
    qa = load("grounded-qa.jsonl")[0]

    print(f"Three calls against {MODEL}, one per workflow.\n")
    ok = [
        probe("extraction", PROMPTS["extraction"].format(input=ex["input"])),
        probe("classification", PROMPTS["classification"].format(input=cl["input"])),
        probe(
            "grounded qa",
            PROMPTS["qa"].format(corpus=corpus_text(), question=qa["question"]),
        ),
    ]

    print()
    if all(ok):
        print("All three ran. Inference did not need the network.")
        return 0
    print(f"{ok.count(False)} of 3 failed. Record which, and why.")
    return 1


if __name__ == "__main__":
    sys.exit(main())