# Predictions

Fill this in **before installing a single model**. Then commit it and do not
edit the prediction column.

## Why bother predicting

Three reasons, and only the third is about the article.

**It stops the experiment from becoming tuning.** Without a committed
expectation there is always one more model worth trying, one more prompt
tweak, one more quantisation. With one, there is a defined moment when you
are finished: you ran the thing, you compared it to what you said, you are
done.

**It stops you from rationalising the result.** It is remarkably easy to look
at an outcome and feel you knew it all along. Written predictions make that
impossible to do accidentally.

**Where you were wrong is the interesting part.** A result you expected tells
a reader almost nothing. A result that surprised the person who ran the
experiment is the only thing worth their time.

## How to predict when you have no idea

This is the normal situation. If you already knew how a 360M model handles
ambiguous customer messages, you would not need to run anything.

A useless prediction looks like this:

> Small model, classification: 31 out of 50.

You made that number up. If it comes back 38, you have learned nothing,
because you had no basis for 31 and no basis for caring about the difference.
Precise numeric predictions are for people with a prior from similar work.

A useful prediction, with no prior, looks like one of these.

**Directional.** Will the model beat the regex, match it, or lose to it?
Will it over-escalate or under-escalate? Will it abstain or invent? You have
an intuition about direction even when you have none about magnitude, and
direction is what the article argues about.

**Coarse bands.** Not 31 out of 50, but "below half", "roughly half to three
quarters", "better than three quarters". Three buckets, and being in the
wrong bucket actually means something.

**Ordering.** You may not know any absolute number but you probably expect
the bigger model to beat the smaller one. Say so. If the ordering breaks,
that is a finding on its own, and it is the one most likely to break.

**The hardest case.** Point at a single fixture and say "this one will defeat
everything." You are predicting a specific failure, which is checkable, and
it forces you to actually read your own fixtures.

**What would surprise you.** One sentence, freeform. "I expect the small
model to be useless at all three jobs" is a real prediction. If it turns out
to be fine at classification, you have an article.

## How confident are you

Mark each prediction with one of these. It takes two seconds and it changes
how you read the result later.

- **Confident**: I would be surprised to be wrong.
- **Leaning**: I have a hunch, not much behind it.
- **Coin flip**: writing this down only so I cannot pretend afterwards.

A wrong "confident" is worth a paragraph in the article. A wrong "coin flip"
is worth nothing, and that is fine. The point of marking it is to tell them
apart afterwards.

---

## Setup, recorded at the start

| Field | Value |
| --- | --- |
| Pi model | |
| RAM | |
| Storage | |
| Cooling | |
| OS and version | |
| Ollama version | |
| Models, exact tags and digests | |
| Quantisation, if not the Ollama default | |
| Total hardware cost | |
| Date run | |

---

## Workflow 0, extraction

The regex scores 30 out of 30 by construction. The fixtures were built for it.
The question is entirely about the models.

| Prediction | Your call | Confidence | Actual |
| --- | --- | --- | --- |
| Will any model match the regex? | none / only the biggest / all of them | | |
| Small model on the 22 straightforward cases | below half / most / nearly all | | |
| Small model on the 8 absent cases: does it invent an order number? | never / sometimes / usually | | |
| Small model on the 3 decoys (membership number, UPS tracking, phone number) | falls for none / some / all | | |
| Which decoy defeats the most models? | MEM- / tracking / phone | | |
| Will the lowercase cases cause trouble? | yes / no | | |
| Ordering: does the bigger local model beat the smaller? | yes / no / same | | |

## Workflow 1, classification

Fifty messages, six labels, fourteen of them deliberately ambiguous or
borderline.

| Prediction | Your call | Confidence | Actual |
| --- | --- | --- | --- |
| Small model, overall | below half / half to three quarters / above three quarters | | |
| Mid model, overall | below half / half to three quarters / above three quarters | | |
| Does the small model produce invalid output, meaning not one of the six labels? | never / occasionally / often | | |
| When unsure, does it escalate or guess? | escalates / guesses | | |
| Confident wrong, meaning wrong and not an escalation | rare / common | | |
| Which class gets over-predicted? | pick one | | |
| Which two classes bleed into each other? | pick two | | |
| On the fourteen ambiguous cases, any model better than chance? | yes / no | | |

## Workflow 5, grounded question answering

Fifteen questions. Four of them have no answer in the corpus. Those four are
the test.

| Prediction | Your call | Confidence | Actual |
| --- | --- | --- | --- |
| Small model, abstentions out of 4 | none / some / all | | |
| Mid model, abstentions out of 4 | none / some / all | | |
| When a model fabricates, is the answer plausible or obviously wrong? | plausible / obvious | | |
| Does any model over-abstain on an answerable question? | yes / no | | |
| The three two-passage questions | all fail / some / all fine | | |
| Which single question defeats everything? | pick one by id | | |

## Offline

| Prediction | Your call | Confidence | Actual |
| --- | --- | --- | --- |
| Does anything break when the network is pulled? | yes / no | | |
| If yes, what | | | |

## The one that matters

**What do you expect to be surprised by?** One or two sentences, before you
start.

> 

---

## After the run

### Verdicts

| Workload | Unnecessary / Sufficient / Marginal / Insufficient | Why, one line |
| --- | --- | --- |
| Extraction | | |
| Classification | | |
| Grounded QA | | |

- **Unnecessary**: deterministic code already does it
- **Sufficient**: a small local model does it well enough to use unattended
- **Marginal**: usable with a person checking the output
- **Insufficient**: the error or latency profile is not acceptable

### Where I was wrong

Prose, written last. Go through the confidence column first: every wrong
"confident" belongs in this section, and every wrong "coin flip" probably
does not.

This is what the article is for.
