# Fixtures

**Fixture set version: v1**

Everything in `fixtures/` is one versioned set. Numbers produced against
different versions are not comparable, so the version is part of any result
you publish.

## The rule

**A fixture is never edited after a model has been run against it.**

Once a model has seen a fixture, changing that fixture changes what every
earlier number meant, and there is no way to tell from the results that it
happened. If a fixture turns out to be genuinely wrong, it is fixed by
bumping the version and re-running every model, with the change recorded in
the history below. Adding new fixtures is the same: a different set of
inputs is a different measurement.

This is not caution for its own sake. The failure it prevents is the one
where a model gets a case wrong, the case looks unfair on inspection, the
case gets softened, and the suite ends up measuring the model's strengths.
That drift is invisible in the output and it is why published numbers need
a version attached.

## What is in the set

### `extraction.jsonl`: 30 cases

Find an order number of the form `ORD-` followed by exactly six digits, or
report that there isn't one.

| Group | Count | What it is |
| --- | ---: | --- |
| Present | 20 | An order number, in varied surroundings |
| Present, lowercase | 2 | `ord-556120`, to catch case handling |
| Absent | 5 | Ordinary messages with no order number |
| Decoy | 3 | Something that looks like one and is not |

The three decoys are a membership number (`MEM-443322`), a UPS tracking
number (`1Z999AA10123456784`), and a phone number (`503-555-0142`). A regex
ignores all three by construction. Whether a model does is the finding this
file exists for.

Expected output is the canonical uppercase form, or null.

### `classification.jsonl`: 50 cases

Short messages to a small business, each belonging to exactly one of six
categories: `appointment`, `billing`, `availability`, `complaint`,
`question`, `escalate`.

| Label | Count |
| --- | ---: |
| escalate | 12 |
| question | 10 |
| appointment | 9 |
| billing | 7 |
| availability | 6 |
| complaint | 6 |

Sixteen of the fifty are marked `ambiguous` or `borderline` in their `note`
field. They are there deliberately. A set of fifty unambiguous messages
measures nothing interesting, because the cases that decide whether a
classifier is deployable are the ones where the right answer is "escalate,
I cannot tell."

`escalate` means the message needs a person, including when the model cannot
tell what it is about. That definition is in the prompt, so a model that
escalates when unsure is following instructions rather than failing.

### `grounded-qa.jsonl` and `corpus/`: 15 questions, 4 documents

The corpus is four short documents about a fictional small winery: club
policy, tasting room, 2024 production notes, shipping.

| Kind | Count | What it tests |
| --- | ---: | --- |
| `single` | 8 | Answerable from one passage |
| `two` | 3 | Needs two passages combined |
| `absent` | 4 | The corpus does not contain the answer |

**The four `absent` questions are the point of the file.** They ask things
a reader would reasonably expect to be in a winery's documents and which are
simply not there: the alcohol percentage of a wine, who the winemaker is,
what a club tier costs, what yeast was used. A model that answers them
plausibly has produced something indistinguishable from a correct answer,
which is worse than a model that fails loudly.

Each fixture carries `must_contain_any` and `must_not_contain`. Those drive
a keyword check that is indicative only. The abstention count is the number
that means something.

## The corpus is fictional

Nothing in `fixtures/corpus/` is real. The winery, its policies, its harvest
dates and its shipping restrictions are all invented, and they are internally
consistent so that answers can be judged without looking anything up.

The classification messages are addressed to the same fictional business, so
both halves of the set share a domain. That is deliberate: it keeps the
reading load low when you go through the output by hand, which the README
asks you to do.

## If you reuse these

You are welcome to. Two requests, neither of them a license condition:

1. State the fixture version with any numbers you publish.
2. If you change a fixture, say so, rather than reporting results against
   "the same fixtures" with a quiet edit inside them.

## Version history

### v1, the initial set

30 extraction cases, 50 classification cases, 15 grounded QA questions over
four corpus documents. No model had been run against any of them when the
set was frozen.