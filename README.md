# Pi SLM experiment kit

Everything needed to run the scoped weekend experiment behind "Do You
Actually Need an LLM?". Standard library Python only, so it runs on the Pi
without installing anything beyond Ollama and the models.

```text
fixtures/
  extraction.jsonl       30 cases: 22 with an order number, 5 without, 3 decoys
  classification.jsonl   50 messages across 6 labels, 14 ambiguous or borderline
  grounded-qa.jsonl      15 questions: 8 single-passage, 3 two-passage, 4 unanswerable
  corpus/                4 short documents the QA questions are asked against
scripts/
  run.py                 runs one workflow against one model, writes raw results
  score.py               scores everything in results/ and prints the article's numbers
results/                 output, one JSON per workflow and model
PREDICTIONS.md           fill this in before installing anything
```

## Order of operations

**1. Fill in PREDICTIONS.md.** Before Ollama, before models, before anything.
This is the step that keeps the weekend a weekend: once you are measuring
against a committed expectation, there is a defined moment when you are done.

**2. Pull the models and record their exact tags.**

```bash
ollama pull smollm2:360m
ollama pull qwen2.5:1.5b
ollama list            # record the digests in PREDICTIONS.md
```

Those two are a sensible starting lineup, one sub-1B and one in the 1 to 2B
class. Check what is current the morning you start and substitute freely, but
write down exactly what you used.

**3. Run the deterministic baseline first.**

```bash
python3 scripts/run.py extraction regex
```

Expect 30/30. The regex is in `run.py` as `ORDER_RE` and the fixtures were
built for it. The interesting question is whether a model can match it.

**4. Run each workflow against each model.**

On slow hardware this takes well over an hour, so run it inside `tmux` or
`screen`. An SSH session that drops takes the run with it. Raise the timeout
too; the default is sized for a fast machine:

```bash
tmux new -s run
export TIMEOUT=600

python3 scripts/run.py extraction     smollm2:360m
python3 scripts/run.py extraction     qwen2.5:1.5b
python3 scripts/run.py classification smollm2:360m
python3 scripts/run.py classification qwen2.5:1.5b
python3 scripts/run.py qa             smollm2:360m
python3 scripts/run.py qa             qwen2.5:1.5b
```

Six runs. Classification is 50 calls each and QA sends the whole corpus every
time, so the QA runs are the slow ones. Start them and go do something else.

Each record prints its fixture id as it runs. A call that fails prints why
and the run continues, so one bad case does not cost you the other
twenty-nine.

**5. Score.**

```bash
python3 scripts/score.py
python3 scripts/score.py --csv > results/summary.csv
```

**6. Read the QA answers yourself.** The scorer checks abstention
automatically, which is the number that matters, and does a keyword check on
the rest. A keyword check is not comprehension. Open the result files and
read what the models actually said.

**7. Pull the cable.** Disable wifi, unplug ethernet, confirm no route out,
then re-run one case from each workflow. Record what still works and anything
that unexpectedly wanted the network.

## Hosted reference

Optional, and first on the cut list. If you want it, point the runner at an
OpenAI-compatible endpoint by setting `OLLAMA_HOST`, or add a branch to
`run.py`. The article works with two local models and a stated absence.

## What the scorer reports, and why

**Extraction:** overall, plus a separate count of how often a model invented
an order number when there was none. The three decoys are a membership
number, a UPS tracking number and a phone number. Falling for those is the
interesting failure.

**Classification:** overall accuracy, and separately **confident wrong**,
meaning wrong and not an escalation. A model that escalates when unsure is
usable. A model that routes a legal notice to billing is not. The confusion
matrix shows which classes bleed into which.

**Grounded QA:** correct abstentions out of four. Everything else is
secondary. A system that invents a plausible answer with no evidence is worse
than one that fails loudly, because it is indistinguishable from one that
worked.

## Two kinds of failure

Not every error is the same thing, and conflating them would misreport a
model. The runner tags each failure and the scorer treats them differently.

**Model failure.** The model ran and produced nothing usable. Ollama aborting
a prediction that fell into a repetition loop is the common case. This is a
result: it stays in the denominator, counts against the model, and is listed
on its own line as "no usable answer". Dropping these would quietly discard
exactly the cases a model cannot handle, and score it only on the ones it
could.

**Transport failure.** The call never reached a working model. Ollama was
down, the tag was wrong, the request timed out. Nothing was measured, so
these are excluded from the scores and the run is reported as incomplete.
Fix them and run again before quoting any number from that run.

## Notes

The fixtures are a fictional small winery, chosen so the classification
messages and the QA corpus share a domain and so you can judge the answers
without looking anything up. Nothing in them is real.

Do not edit a fixture after seeing a model fail it. If a fixture turns out to
be genuinely wrong, fix it, note the change, and re-run every model.

Record CPU temperature if it is convenient, but it is not load-bearing and is
on the cut list.