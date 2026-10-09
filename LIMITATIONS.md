# What these numbers do not support

This repository publishes measurements. That only means something if it is
equally clear about what was not measured, so this file is the other half of
the results.

Read it before citing anything here.

## Scope

**Three workflows, not a benchmark suite.** Deterministic extraction,
closed-set classification, and grounded question answering. There is no
summarization, no entity extraction, no multi-turn anything, no tool use, no
code. A model that does well here has done well at three bounded jobs.

**One runtime.** Everything goes through Ollama. Runtime choice is known to
move both speed and memory substantially, so these numbers describe
model-plus-runtime, not the model.

**One quantisation**, whatever Ollama ships by default for each tag. A
different quantisation of the same model is a different measurement.

**One device**, in one thermal situation, run once. There is no repeat
sampling and no variance estimate. Treat a gap of one or two cases as noise.

**Temperature 0, one reply per case.** That makes the run reproducible on
the same setup. It also means nothing here says how stable a model is across
samples, which for the abstention question is arguably the more useful
property.

## Sample sizes

Fifty classification cases, thirty extraction cases, fifteen questions, four
of them unanswerable.

Four is a very small number. "Abstained on 3 of 4" and "abstained on 4 of 4"
are not meaningfully different results, and neither one establishes an
abstention rate. What the four cases can do is tell apart a model that
abstains sometimes from one that never does, which is the distinction worth
having.

The classification set is large enough to show which classes bleed into
which, and too small for per-class precision to mean much.

## The fixtures are invented

The corpus and the messages describe a fictional winery (see `FIXTURES.md`).
They were written to be internally consistent and readable, not sampled from
real traffic. Real customer messages are messier, longer, and more repetitive
than these, so performance here is probably an upper bound on performance
against a real inbox.

One domain, one register, one language.

## Scoring

**Extraction and classification are scored exactly.** String match and label
match. Those numbers are as good as the fixtures.

**Grounded QA is scored two ways, and only one of them is sound.**
Abstention is detected by matching against a list of phrases
(`ABSTAIN_MARKERS` in `scripts/score.py`). That catches the common forms and
will miss a model that declines in wording nobody anticipated, which counts
as a fabrication when it was not one. The answerable questions get a keyword
check that is reported as indicative and is not a test of comprehension. The
README tells you to read the answers yourself for a reason.

## What the comparison does not control for

Prompts were written once, in plain language, and used unchanged for every
model. They were not tuned per model. A small model that does badly here
might do better with a prompt shaped for it, and a result that says "this
model could not do the job" should be read as "this model could not do the
job with a reasonable first prompt."

That is the right test for the question being asked, which is whether a job
can be done without much effort or much hardware. It is the wrong test for
"how good is this model."

## What is deliberately absent

No power measurement. No sustained-load or thermal testing. No concurrency.
No cold-start timing. A machine that handles one prompt and degrades under an
hour of work is a different appliance, and that was not measured.

## What the numbers do support

Within one device, one runtime, one quantisation and these fixtures:

- whether a model matched a deterministic baseline on a job the baseline
  was built for
- whether it routed confidently into the wrong bucket, and which buckets
- whether it declined to answer questions the supplied material does not
  answer, or produced something plausible instead
- roughly what each of those cost in latency

Those are the claims this repository makes. Anything broader is extrapolation
and belongs to whoever is doing the extrapolating.