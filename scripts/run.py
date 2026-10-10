#!/usr/bin/env python3
"""
Run one workflow against one model and write raw results.

    python scripts/run.py extraction     regex
    python scripts/run.py extraction     qwen2.5:1.5b
    python scripts/run.py classification smollm2:360m
    python scripts/run.py qa             qwen2.5:1.5b

Talks to Ollama on http://localhost:11434 by default. Override with
OLLAMA_HOST. Standard library only, so it runs on the Pi as-is.

Writes results/<workflow>__<model>.json with one record per fixture: the
input, the raw reply, the parsed answer, the wall-clock latency, and the
execution metrics Ollama reports. A call that fails records the error and
the run continues, because a partial run with known holes is worth more
than a traceback at fixture 7 of 30.

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
TIMEOUT = int(os.environ.get("TIMEOUT", "600"))

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


class OllamaError(RuntimeError):
    """An Ollama call that failed, carrying whatever the server actually said.

    `kind` separates two very different things that both arrive as exceptions:

    "transport"  the call never reached a working model. Ollama was down, the
                 model was missing, the request timed out, the reply was
                 malformed. Nothing was measured, so these are excluded from
                 scores and mark the run incomplete.

    "model"      the model ran and failed to produce a usable answer. Ollama
                 returned 5xx from the generate endpoint, for instance when it
                 aborts a prediction that fell into a repetition loop. This IS
                 a result. Excluding it would quietly drop the cases a model
                 cannot handle and flatter its score.
    """

    def __init__(self, message, kind):
        super().__init__(message)
        self.kind = kind


def metrics_from(payload):
    """Pull Ollama's execution metrics out of a generate response.

    Ollama reports durations in nanoseconds. Every field is optional here,
    because a different Ollama version may not send all of them and a missing
    number should produce a null rather than a crash mid-run.

    The fields, and what they separate:

      prompt_tokens / prompt_ms   reading the prompt, before any output
      gen_tokens / gen_ms         producing the answer
      load_ms                     loading the model, large on the first call
                                  of a run and near zero afterwards
      tps                         gen_tokens per second of generation

    `first_token_ms` is load + prompt, which is how long the caller waits
    before the model starts producing. It is NOT time-to-first-token in the
    streaming sense: this harness uses stream=false, so there is no
    first-token event to observe. Named for what it actually measures.

    tps is the number to watch across a run. Wall-clock latency conflates a
    slow machine with a long answer; tps does not, so a CPU being clocked
    down shows up here as decay and nowhere else.
    """

    def ns_to_ms(key):
        v = payload.get(key)
        return round(v / 1e6, 1) if isinstance(v, (int, float)) else None

    prompt_ms = ns_to_ms("prompt_eval_duration")
    gen_ms = ns_to_ms("eval_duration")
    load_ms = ns_to_ms("load_duration")
    gen_tokens = payload.get("eval_count")
    prompt_tokens = payload.get("prompt_eval_count")

    tps = None
    if isinstance(gen_tokens, int) and isinstance(gen_ms, float) and gen_ms > 0:
        tps = round(gen_tokens / (gen_ms / 1000.0), 2)

    first_token_ms = None
    if prompt_ms is not None:
        first_token_ms = round(prompt_ms + (load_ms or 0.0), 1)

    return {
        "prompt_tokens": prompt_tokens,
        "gen_tokens": gen_tokens,
        "prompt_ms": prompt_ms,
        "gen_ms": gen_ms,
        "load_ms": load_ms,
        "total_ms": ns_to_ms("total_duration"),
        "tps": tps,
        "first_token_ms": first_token_ms,
        "done_reason": payload.get("done_reason"),
    }


EMPTY_METRICS = {
    k: None
    for k in (
        "prompt_tokens",
        "gen_tokens",
        "prompt_ms",
        "gen_ms",
        "load_ms",
        "total_ms",
        "tps",
        "first_token_ms",
        "done_reason",
    )
}


def ollama(model, prompt):
    """Call Ollama. Return (reply_text, metrics), or raise OllamaError.

    urllib raises HTTPError and discards the response body by default, which
    is exactly where Ollama puts its reason. Read it before giving up.
    """
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
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            payload = json.loads(r.read())
            return payload["response"].strip(), metrics_from(payload)
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8", "replace").strip()
        except Exception:
            detail = "(no response body)"
        # A 5xx from the generate endpoint means the model ran and the
        # generation failed. A 4xx means the request or the setup was wrong
        # and no model ever ran.
        kind = "model" if 500 <= e.code < 600 else "transport"
        raise OllamaError(f"HTTP {e.code} from Ollama: {detail[:1000]}", kind) from None
    except urllib.error.URLError as e:
        raise OllamaError(f"Could not reach Ollama at {HOST}: {e.reason}", "transport") from None
    except TimeoutError:
        raise OllamaError(f"No reply within TIMEOUT={TIMEOUT}s", "transport") from None
    except (KeyError, json.JSONDecodeError) as e:
        raise OllamaError(f"Unexpected reply shape from Ollama: {e}", "transport") from None


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
    return [
        json.loads(l)
        for l in (FIX / name).read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]


CORPUS_MIN_CHARS = 1500
CORPUS_MIN_DOCS = 3


def corpus_text():
    """The whole reference corpus, concatenated in filename order.

    Refuses to return anything implausibly small, because the first version
    of this function did. It built a list from a glob and joined it, and a
    glob that matches nothing joins to the empty string without raising.
    An entire grounded-QA run was conducted that way, against a reference
    block containing nothing at all.

    What makes that worth this much commentary is that no part of the
    system reported it. Every call succeeded. Both models behaved correctly
    given what they were actually sent: the one told to say NOT IN THE
    MATERIAL when the material lacked the answer said it thirteen times out
    of fifteen, and the one with no such discipline answered from parametric
    knowledge and invented a wine. The scorer scored it. The numbers were
    internally consistent, had plausible failure modes, and were written up
    as a finding about model capability.

    The only trace was the prompt token count. The real prompt is about 740
    tokens; the run reported 97. Four hundred and forty-seven words of
    reference material cannot be ninety-seven tokens, and that number was
    sitting in the results table the whole time.

    A loader that returns a plausible value for a missing input will
    eventually be believed. So this one raises instead.
    """
    corpus_dir = FIX / "corpus"
    paths = sorted(corpus_dir.glob("*.md"))

    if not paths:
        raise SystemExit(
            f"\nNo corpus documents found in {corpus_dir}\n\n"
            "Grounded QA cannot run without reference material, and running\n"
            "it against an empty reference block produces numbers that look\n"
            "like a result. If the directory is missing or empty, this\n"
            "checkout is incomplete: confirm fixtures/corpus/*.md were\n"
            "committed and pulled.\n"
        )

    parts = [p.read_text(encoding="utf-8").strip() for p in paths]
    text = "\n\n".join(parts)

    if len(paths) < CORPUS_MIN_DOCS or len(text) < CORPUS_MIN_CHARS:
        found = ", ".join(p.name for p in paths)
        raise SystemExit(
            f"\nCorpus is too small to be the real fixture set: "
            f"{len(paths)} file(s), {len(text)} characters.\n"
            f"Found: {found}\n\n"
            f"Fixture set v1 is 4 documents totalling about 2,600 "
            f"characters.\nA truncated corpus scores as a capability "
            f"failure, so this stops here.\n"
        )

    return text


def progress(i, total, fixture_id, note=""):
    """One line per record, to stderr, so a failure names the fixture."""
    print(f"  [{i}/{total}] {fixture_id} {note}", file=sys.stderr, flush=True)


def tail(rec):
    """Print the per-call speed so a slowing machine is visible as it runs."""
    tps = rec.get("tps")
    if tps is not None:
        print(f"      {tps:.1f} tok/s", file=sys.stderr, flush=True)


def median(xs):
    xs = sorted(x for x in xs if x is not None)
    return xs[len(xs) // 2] if xs else None


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    workflow, model = sys.argv[1], sys.argv[2]
    OUT.mkdir(exist_ok=True)
    records = []
    errors = {"transport": 0, "model": 0}

    if workflow not in ("extraction", "classification", "qa"):
        print(f"Unknown workflow: {workflow}")
        sys.exit(1)

    if workflow == "extraction":
        rows = load("extraction.jsonl")
        for i, r in enumerate(rows, 1):
            progress(i, len(rows), r["id"])
            t0 = time.perf_counter()
            if model == "regex":
                m = ORDER_RE.search(r["input"])
                rec = {
                    **r,
                    "raw": "",
                    "answer": (m.group(0).upper() if m else None),
                    **EMPTY_METRICS,
                }
            else:
                try:
                    reply, met = ollama(model, PROMPTS["extraction"].format(input=r["input"]))
                    rec = {**r, "raw": reply, "answer": parse_extraction(reply), **met}
                except OllamaError as e:
                    errors[e.kind] += 1
                    print(f"      FAILED ({e.kind}): {e}", file=sys.stderr, flush=True)
                    rec = {
                        **r,
                        "raw": "",
                        "answer": None,
                        "error": str(e),
                        "error_kind": e.kind,
                        **EMPTY_METRICS,
                    }
            rec["ms"] = round((time.perf_counter() - t0) * 1000, 1)
            tail(rec)
            records.append(rec)

    elif workflow == "classification":
        if model == "regex":
            print("No deterministic baseline for classification. Skip it, and say so in the post.")
            sys.exit(1)
        rows = load("classification.jsonl")
        for i, r in enumerate(rows, 1):
            progress(i, len(rows), r["id"])
            t0 = time.perf_counter()
            try:
                reply, met = ollama(model, PROMPTS["classification"].format(input=r["input"]))
                rec = {**r, "raw": reply, "answer": parse_label(reply), **met}
            except OllamaError as e:
                errors[e.kind] += 1
                print(f"      FAILED ({e.kind}): {e}", file=sys.stderr, flush=True)
                rec = {
                    **r,
                    "raw": "",
                    "answer": "ERROR",
                    "error": str(e),
                    "error_kind": e.kind,
                    **EMPTY_METRICS,
                }
            rec["ms"] = round((time.perf_counter() - t0) * 1000, 1)
            tail(rec)
            records.append(rec)

    elif workflow == "qa":
        if model == "regex":
            print("No deterministic baseline for QA.")
            sys.exit(1)
        corpus = corpus_text()
        rows = load("grounded-qa.jsonl")
        # Say out loud what is being sent. The run that went out with an
        # empty corpus would have been caught here by anyone watching the
        # first line of output.
        print(
            f"  corpus: {len(sorted((FIX / 'corpus').glob('*.md')))} documents, "
            f"{len(corpus)} characters, roughly {len(corpus) // 4} tokens",
            file=sys.stderr,
            flush=True,
        )
        for i, r in enumerate(rows, 1):
            progress(i, len(rows), r["id"], f"({r['kind']})")
            t0 = time.perf_counter()
            try:
                reply, met = ollama(
                    model, PROMPTS["qa"].format(corpus=corpus, question=r["question"])
                )
                rec = {**r, "raw": reply, "answer": reply, **met}
            except OllamaError as e:
                errors[e.kind] += 1
                print(f"      FAILED ({e.kind}): {e}", file=sys.stderr, flush=True)
                rec = {
                    **r,
                    "raw": "",
                    "answer": "",
                    "error": str(e),
                    "error_kind": e.kind,
                    **EMPTY_METRICS,
                }
            rec["ms"] = round((time.perf_counter() - t0) * 1000, 1)
            tail(rec)
            records.append(rec)

    safe = model.replace(":", "-").replace("/", "-")
    path = OUT / f"{workflow}__{safe}.json"
    path.write_text(
        json.dumps(
            {
                "workflow": workflow,
                "model": model,
                "host": HOST,
                "when": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "errors": errors,
                "records": records,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    lat = sorted(r["ms"] for r in records)
    print(f"\n{len(records)} records -> {path.name}")
    if lat:
        print(f"latency ms: median {lat[len(lat) // 2]:.0f}, max {lat[-1]:.0f}")

    med_tps = median([r.get("tps") for r in records])
    if med_tps is not None:
        med_prompt = median([r.get("prompt_tokens") for r in records])
        max_prompt = max(
            (r.get("prompt_tokens") or 0 for r in records), default=0
        )
        print(f"generation: median {med_tps:.1f} tok/s")
        print(f"prompt    : median {med_prompt} tokens, max {max_prompt}")

    if errors["model"]:
        print(
            f"{errors['model']} of {len(records)} calls produced NO USABLE ANSWER. "
            "The model ran and failed; these count against it."
        )
    if errors["transport"]:
        print(
            f"{errors['transport']} of {len(records)} calls never reached a working model. "
            "The run is incomplete; fix these and run again before scoring."
        )


if __name__ == "__main__":
    main()