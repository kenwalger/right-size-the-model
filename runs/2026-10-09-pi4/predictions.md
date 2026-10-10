# Predictions

Filled in and committed before Ollama was installed or a model pulled.
Prediction and confidence columns are as written then and have not been
edited. Only the Actual column was added afterwards.

Fixture set: **v1**

> **The grounded QA section was graded twice.** The first grading was
> against an invalid run: `fixtures/corpus/` had never been committed, so
> every question was asked against an empty reference block. Four rows in
> that section were marked against behaviour that was an artifact of the
> missing corpus. They are regraded here against the rerun, and the
> original wrong gradings are noted inline, because a prediction sheet that
> quietly corrects itself is worth nothing.

## How confident are you

- **Confident**: I would be surprised to be wrong.
- **Leaning**: I have a hunch, not much behind it.
- **Coin flip**: writing this down only so I cannot pretend afterwards.

---

## Setup, recorded at the start

| Field | Value |
|---|---|
| Pi model | 4 |
| RAM | 4 GB |
| Storage | 32 GB |
| Cooling | Heat sink + fan |
| OS and version | Debian GNU/Linux 13, 6.18.50+rpt-rpi-v8 |
| Ollama version | 0.40.1 |
| Models, exact tags and digests | qwen2.5:1.5b `65ec06548149`, smollm2:360m `297281b699fc` |
| Python version | 3.13.5 |
| Quantisation, if not the Ollama default | default |
| Total hardware cost | $169.99 USD |
| Date run | 9 October 2026 |

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

Fifteen questions. Four have no answer in the corpus. Graded against the
rerun with the restored corpus; see the note at the top of this file.

| Prediction | Your call | Confidence | Actual |
|---|---|---|---|
| Small model, abstentions out of 4 | some | leaning | **WRONG.** Zero. smollm2 fabricated all four |
| Mid model, abstentions out of 4 | some | confident | **RIGHT.** qwen abstained correctly on 2 of 4. *(First graded WRONG against the invalid run, where it abstained on everything.)* |
| When a model fabricates, plausible or obviously wrong? | plausible | confident | **RIGHT**, and more so than expected. qwen answered an alcohol-percentage question with the real Brix range from the real document: true in every component, wrong in kind |
| Does any model over-abstain on an answerable question? | yes | leaning | **WRONG.** Zero of eleven, for both models. *(First graded RIGHT against the invalid run, where qwen "over-abstained" on 9 of 11 because there was nothing to read.)* |
| The three two-passage questions | some fail | confident | **RIGHT.** qwen got 1 of 3, smollm2 none. *(First graded WRONG against the invalid run, where all three failed for both.)* |
| Which single question defeats everything? | qa10 | coin-flip | **RIGHT.** qa10 defeated both models, though it shares the honour with qa09. Those two are the only answerable questions neither model got. *(First graded "true but uninformative" against the invalid run, where all fifteen defeated both.)* |

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
| Confident | 5 | 2 | 0 |
| Leaning | 2 | 7 | 1 |
| Coin flip | 3 | 2 | 0 |
| **Total** | **10** | **11** | **1** |

Before the QA rerun this read 8 right, 12 wrong, 2 unresolvable, with four
of seven confident calls broken. Three QA rows moved from wrong to right,
one moved from right to wrong, and one resolved from uninformative to
right. The corrected sheet is a better score and a worse story, which is
the honest trade.

**Two of seven confident predictions broke.** Those two:

1. The small model would get most of the straightforward extraction cases.
   It got 8 of 22, by failing at format rather than at finding.
2. The small model would produce invalid output often. It did so once in
   fifty, then emitted the same valid word 43 times.

**And the leaning column is where the real humility is: 2 right out of 10.**
On the calls with a hunch behind them but not much, the hit rate was worse
than the coin flips. Three of five coin flips landed. That ordering is the
wrong way round and is worth more than any individual row.

---

## Verdicts

| Workload | Verdict | Why |
| --- | --- | --- |
| Extraction | **Unnecessary** | Regex 30/30 at zero latency and zero watts; the best model is 28/30 and both its errors are silent |
| Classification | **Insufficient** | Best model 46% with 26 confident-wrong routings; the other collapsed onto a single label |
| Grounded QA | **Marginal** | Single-fact lookup 8/8 for the 1.5B model; two-passage 1/3; correct abstention 2/4 |

- **Unnecessary**: deterministic code already does it
- **Sufficient**: a small local model does it well enough to use unattended
- **Marginal**: usable with a person checking the output
- **Insufficient**: the error or latency profile is not acceptable

---

## What this sheet did not ask

Every row above predicts what a model will do. Not one predicts what the
harness will do, and four of the five measurement flaws found over the
weekend were in the measuring code rather than in anything measured. The
worst of them, a corpus directory that was never committed, turned an
empty reference block into a published capability finding and cost four
rows of this sheet their first grading.

A future version of this template should carry two more rows, filled in
before anything runs:

- **What would have to be true for these numbers to be meaningless?**
- **Would anything in the harness tell me if it were?**

## Where I was wrong

See `results.md` in this directory.