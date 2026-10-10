# Predictions

Filled in and committed before Ollama was installed or a model pulled.
Prediction and confidence columns are as written then and have not been
edited. Only the Actual column was added afterwards.

Fixture set: **v1**

## How confident are you

- **Confident**: I would be surprised to be wrong.
- **Leaning**: I have a hunch, not much behind it.
- **Coin flip**: writing this down only so I cannot pretend afterwards.

---

## Setup, recorded at the start

| Field                                   | Value                                                |
|-----------------------------------------|------------------------------------------------------|
| Pi model                                | 4                                                    |
| RAM                                     | 4 GB                                                 |
| Storage                                 | 32 GB                                                |
| Cooling                                 | Heat Sink + fan                                      |
| OS and version                          | Debian GNU/Linux 13, 6.18.50+rpt-rpi-v8              |
| Ollama version                          | 0.40.1                                               |
| Models, exact tags and digests          | qwen2.5:1.5b 65ec06548149, smollm2:360m 297281b699fc |
| Python Version                          | 3.13.5                                               |
| Quantisation, if not the Ollama default | default                                              |
| Total hardware cost                     | $169.99 USD                                          |
| Date run                                | 9 October 2026                                       |

The first attempt at this run, on 2026-10-08, was made with heat sinks and
no fan. It throttled (`throttled=0xe0000`) and its latency numbers were
discarded. Correctness was unaffected and reproduced exactly.

---

## Workflow 0, extraction

The regex scores 30 out of 30 by construction. The fixtures were built for
it. The question is entirely about the models.

| Prediction | Your call | Confidence | Actual |
|---|---|---|---|
| Will any model match the regex? | only the biggest | leaning | **WRONG.** None did. qwen 28/30, smollm2 8/30, regex 30/30 |
| Small model on the 22 straightforward cases | most | confident | **WRONG.** 8 of 22 by contract. It located the right identifier in all 22 and stripped the `ORD-` prefix on 14 |
| Small model on the 8 absent cases: does it invent an order number? | usually | coin-flip | **RIGHT.** Invented on 7 of 8; the 8th was the ex27 repetition failure |
| Small model on the 3 decoys | some | leaning | **WRONG.** All three, returned verbatim |
| Which decoy defeats the most models? | tracking | leaning | **UNRESOLVABLE.** No decoy discriminates: smollm2 fell for all three, qwen for none |
| Will the lowercase cases cause trouble? | no | coin-flip | **RIGHT.** ex04 failed the same prefix-strip as 13 uppercase cases. Case was not the factor |
| Ordering: does the bigger local model beat the smaller? | yes | leaning | **RIGHT.** 28/30 against 8/30 |

## Workflow 1, classification

Fifty messages, six labels, sixteen of them deliberately ambiguous or
borderline.

| Prediction | Your call | Confidence | Actual |
|---|---|---|---|
| Small model, overall | below half | leaning | **RIGHT.** 15/50, 30% |
| Mid model, overall | half to three quarters | leaning | **WRONG.** 23/50, 46% |
| Does the small model produce invalid output? | often | confident | **WRONG.** Once in 50 |
| When unsure, does it escalate or guess? | guess | leaning | **WRONG.** It escalated 43 of 50, including on messages that were not ambiguous at all |
| Confident wrong | common | confident | **RIGHT**, for the model that was actually classifying: qwen 26 of 50. smollm2's 3 is an artifact of collapse |
| Which class gets over-predicted? | availability | coin-flip | **WRONG.** smollm2 escalate (86%), qwen complaint (38%) |
| Which two classes bleed into each other? | question / escalate | coin-flip | **WRONG.** qwen's worst are escalate into complaint (7) and billing into complaint (5) |
| On the sixteen ambiguous cases, any model better than chance? | yes | confident | **RIGHT, narrowly.** Chance is about 2.7 of 16. qwen 5/16 genuinely clears it; smollm2's 10/16 does not count, being collapse-driven |

## Workflow 5, grounded question answering

Fifteen questions. Four have no answer in the corpus.

| Prediction | Your call | Confidence | Actual |
|---|---|---|---|
| Small model, abstentions out of 4 | some | leaning | **WRONG.** Zero. It fabricated all four |
| Mid model, abstentions out of 4 | some | confident | **WRONG.** All four, but see below: it abstained on 13 of 15 questions overall |
| When a model fabricates, plausible or obviously wrong? | plausible | confident | **RIGHT**, and the clearest confirmation in the run: "$10 per quarter", "12.5%", "Saccharomyces cerevisiae" |
| Does any model over-abstain on an answerable question? | yes | leaning | **RIGHT**, dramatically: qwen on 9 of 11 |
| The three two-passage questions | some fail | confident | **WRONG.** All three failed, for both models |
| Which single question defeats everything? | qa10 | coin-flip | **TRUE BUT UNINFORMATIVE.** qa10 defeated both models, and so did the other fourteen |

## Offline

| Prediction | Your call | Confidence | Actual |
|---|---|---|---|
| Does anything break when the network is pulled? | yes | leaning | **WRONG.** Nothing broke. All three workflows ran with DNS dead and no route out |
| If yes, what | some dependency package I did not account for | leaning | n/a |

## The one that matters

**What do you expect to be surprised by?**

> That regex, established in the 1950's and 60's, is still pretty darn
> useful. Even when compared to SLMs in 2026.

**Outcome: right, and understated.** The regex did not merely hold up. It
won outright, 30/30 against the best model's 28/30, at zero latency, and
its two fewer errors are both of the silent kind that a regex cannot make.

---

## Tally

| Confidence | Right | Wrong | Unresolvable |
|---|---:|---:|---:|
| Confident | 3 | 4 | 0 |
| Leaning | 3 | 6 | 1 |
| Coin flip | 2 | 2 | 1 |
| **Total** | **8** | **12** | **2** |

Four of seven confident predictions broke. Those four are where the
article is:

1. The small model would get most of the straightforward extraction cases.
   It got 8 of 22, by failing at format rather than at finding.
2. The small model would produce invalid output often. It did so once.
3. The mid model would abstain on some of the unanswerable questions. It
   abstained on nearly everything.
4. Some of the two-passage questions would fail. All of them did.

---

## Verdicts

| Workload | Verdict | Why |
| --- | --- | --- |
| Extraction | **Unnecessary** | Regex 30/30 at zero latency and zero watts; the best model is 28/30 and both its errors are silent |
| Classification | **Insufficient** | Best model 46% with 26 confident-wrong routings; the other collapsed onto a single label |
| Grounded QA | **Insufficient** | Zero of eleven answerable questions correct, for both models, by opposite failure modes |

- **Unnecessary**: deterministic code already does it
- **Sufficient**: a small local model does it well enough to use unattended
- **Marginal**: usable with a person checking the output
- **Insufficient**: the error or latency profile is not acceptable

---

## Where I was wrong

See `results.md` in this directory.