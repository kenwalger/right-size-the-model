# Results

Fixture set version: **v1**
Date run:
Run by:

Predictions were committed before any model was installed. They are in
`PREDICTIONS.md` and are not edited after the fact.

What these numbers do and do not support is in `LIMITATIONS.md`. Read that
before citing anything here.

## Setup

| Field | Value |
| --- | --- |
| Device | |
| RAM | |
| OS and version | |
| Runtime and version | |
| Models, exact tags | |
| Quantisation | |
| Total hardware cost | |

## Summary

| Workflow | Model | Score | Median ms |
| --- | --- | --- | ---: |
| extraction | regex | 30/30 | 0 |
| | | | |

## Workflow 0, extraction

The regex scores 30/30 by construction; the fixtures were built for it.

| Model | Overall | Present | Absent | Decoys | Invented |
| --- | ---: | ---: | ---: | ---: | ---: |
| regex | 30/30 | 22/22 | 8/8 | 3/3 | 0 |
| | | | | | |

Notes:

## Workflow 1, classification

**Confident wrong** means wrong and not an escalation. It is the number that
decides whether a model is deployable; overall accuracy hides it.

| Model | Overall | Confident wrong | Invalid output | Ambiguous (of 16) |
| --- | ---: | ---: | ---: | ---: |
| | | | | |

Which classes bled into which:

Notes:

## Workflow 5, grounded question answering

Four of the fifteen questions have no answer in the corpus.

| Model | Abstained (of 4) | Fabricated | Over-abstained | Keyword hit |
| --- | ---: | ---: | ---: | ---: |
| | | | | |

When a model fabricated, was the answer plausible or obviously wrong?

Notes from reading the answers by hand:

## Offline

What still worked with the network pulled, and anything that unexpectedly
wanted it:

## Verdicts

| Workload | Verdict | Why |
| --- | --- | --- |
| Extraction | | |
| Classification | | |
| Grounded QA | | |

- **Unnecessary**: deterministic code already does it
- **Sufficient**: a small local model does it well enough to use unattended
- **Marginal**: usable with a person checking the output
- **Insufficient**: the error or latency profile is not acceptable

## Where the predictions were wrong

Go through the confidence column in `PREDICTIONS.md` first. Every wrong
"confident" belongs here; a wrong "coin flip" probably does not.

## Raw output

Every reply is in `results/`, one JSON file per workflow and model. The
scores above are reproducible from those files with `scripts/score.py`.