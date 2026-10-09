#!/usr/bin/env python3
"""
Run one workflow against one model and write raw results.

    python scripts/run.py extraction     regex
    python scripts/run.py extraction     qwen2.5:1.5b
    python scripts/run.py classification smollm2:360m
    python scripts/run.py qa             qwen2.5:1.5b

Talks to Ollama on http://localhost:11434 by default. Override with
OLLAMA_HOST. Standard library only, so it runs on the Pi as-is.

Writes results/<workflow>__<model>.json with one record per fixture:
the input, the raw reply, the parsed answer, and the latency.

Scoring happens in score.py. This script does not judge anything.
"""

import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIX = ROOT / "fixtures"
OUT = ROOT / "results"
HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
TIMEOUT = int(os.environ.get("TIMEOUT", "180"))

ORDER_RE = re.compile(r"\bORD-\d{6}\b", re.IGNORECASE)

LABELS = ["appointment", "billing", "availability", "complaint", "question", "escalate"]

PROMPTS = {
    "extraction": (
        "Extract the order number from the message below.\n"
        "An order number looks like ORD- followed by exactly six digits.\n"
        "If there is no order number, answer exactly: NONE\n"
        "Answer with the order number alone and nothing else.\n\n"
        "Message: {input}\n\nAnswer:"
    ),
    "classification": (
        "Classify the customer message into exactly one category.\n"
        "Categories: " + ", ".join(LABELS) + "\n"
        "Use 'escalate' when the message needs a person rather than a routine reply, "
        "including when you cannot tell what it is about.\n"
        "Answer with the category word alone and nothing else.\n\n"
        "Message: {input}\n\nCategory:"
    ),
    "qa": (
        "Answer the question using ONLY the reference material below.\n"
        "If the reference material does not contain the answer, reply exactly: "
        "NOT IN THE MATERIAL\n"
        "Do not use outside knowledge. Keep the answer to one or two sentences.\n\n"
        "--- REFERENCE MATERIAL ---\n{corpus}\n--- END ---\n\n"
        "Question: {question}\n\nAnswer:"
    ),
}


def ollama(model, prompt):
    body = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0, "num_predict": 200},
        }
    ).encode()
    req = urllib.request.Request(
        f"{HOST}/api/generate", data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read())["response"].strip()


def parse_extraction(reply):
    m = ORDER_RE.search(reply)
    if m:
        return m.group(0).upper()
    if "none" in reply.strip().lower()[:12]:
        return None
    return reply.strip() or None


def parse_label(reply):
    low = reply.strip().lower()
    for label in LABELS:
        if low.startswith(label):
            return label
    for label in LABELS:
        if label in low:
            return label
    return f"INVALID:{reply.strip()[:40]}"


def load(name):
    return [json.loads(l) for l in (FIX / name).read_text(encoding="utf-8").splitlines() if l.strip()]


def corpus_text():
    parts = []
    for p in sorted((FIX / "corpus").glob("*.md")):
        parts.append(p.read_text(encoding="utf-8").strip())
    return "\n\n".join(parts)


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    workflow, model = sys.argv[1], sys.argv[2]
    OUT.mkdir(exist_ok=True)
    records = []

    if workflow == "extraction":
        rows = load("extraction.jsonl")
        for r in rows:
            t0 = time.perf_counter()
            if model == "regex":
                m = ORDER_RE.search(r["input"])
                answer, reply = (m.group(0).upper() if m else None), ""
            else:
                reply = ollama(model, PROMPTS["extraction"].format(input=r["input"]))
                answer = parse_extraction(reply)
            records.append({**r, "raw": reply, "answer": answer,
                            "ms": round((time.perf_counter() - t0) * 1000, 1)})

    elif workflow == "classification":
        if model == "regex":
            print("No deterministic baseline for classification. Skip it, and say so in the post.")
            sys.exit(1)
        for r in load("classification.jsonl"):
            t0 = time.perf_counter()
            reply = ollama(model, PROMPTS["classification"].format(input=r["input"]))
            records.append({**r, "raw": reply, "answer": parse_label(reply),
                            "ms": round((time.perf_counter() - t0) * 1000, 1)})

    elif workflow == "qa":
        if model == "regex":
            print("No deterministic baseline for QA.")
            sys.exit(1)
        corpus = corpus_text()
        for r in load("grounded-qa.jsonl"):
            t0 = time.perf_counter()
            reply = ollama(model, PROMPTS["qa"].format(corpus=corpus, question=r["question"]))
            records.append({**r, "raw": reply, "answer": reply,
                            "ms": round((time.perf_counter() - t0) * 1000, 1)})

    else:
        print(f"Unknown workflow: {workflow}")
        sys.exit(1)

    safe = model.replace(":", "-").replace("/", "-")
    path = OUT / f"{workflow}__{safe}.json"
    path.write_text(json.dumps(
        {"workflow": workflow, "model": model, "host": HOST,
         "when": time.strftime("%Y-%m-%dT%H:%M:%S"), "records": records},
        indent=2), encoding="utf-8")

    lat = sorted(r["ms"] for r in records)
    print(f"{len(records)} records -> {path.name}")
    if lat:
        print(f"latency ms: median {lat[len(lat)//2]:.0f}, max {lat[-1]:.0f}")


if __name__ == "__main__":
    main()
