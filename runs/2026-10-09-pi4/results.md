# Results: Raspberry Pi 4, 9 October 2026

Fixture set: **v1**
Predictions: `predictions.md` in this directory, committed before anything
was installed.
Limits on what these numbers support: `../../LIMITATIONS.md`. Read it
before citing any of this.

## Setup

| Field | Value |
| --- | --- |
| Device | Raspberry Pi 4, 4 GB RAM |
| Storage | 32 GB SD card |
| Cooling | Heat sinks and fan |
| OS and version | TODO |
| Runtime | Ollama, version TODO |
| Models | smollm2:360m, qwen2.5:1.5b (digests TODO) |
| Quantisation | Ollama default for each tag |
| Total hardware cost | $169.99 USD |
| Date | 2026-10-09 |
| Throttled | `0x0` before and after every run |

## Summary

| Workflow | Model | Score | Median latency | Median tok/s |
| --- | --- | ---: | ---: | ---: |
| extraction | regex | 30/30 | 0 ms | n/a |
| extraction | qwen2.5:1.5b | 28/30 | 4972 ms | 4.3 |
| extraction | smollm2:360m | 8/30 | 2556 ms | 5.9 |
| classification | qwen2.5:1.5b | 23/50 | 2885 ms | 7.5 |
| classification | smollm2:360m | 15/50 | 1881 ms | 6.2 |
| grounded QA | qwen2.5:1.5b | 0/11 answerable | 3577 ms | 4.7 |
| grounded QA | smollm2:360m | 0/11 answerable | 4646 ms | 5.4 |

The QA row is the hand-checked number. The scorer reports abstention
counts, which say something different and are discussed below.

---

## Workflow 0: deterministic extraction

Find an order number of the form `ORD-` plus six digits, or report there
isn't one. Thirty cases: 22 present, 5 absent, 3 decoys.

| | regex | qwen2.5:1.5b | smollm2:360m |
| --- | ---: | ---: | ---: |
| Overall | 30/30 | 28/30 | 8/30 |
| Present (22) | 22 | 20 | 8 |
| Absent, declined (8) | 8 | 8 | 0 |
| Decoys ignored (3) | 3 | 3 | 0 |
| Invented an answer | 0 | 0 | 7 |
| No usable answer | 0 | 0 | 1 |

**The regex won.** Not narrowly. 30/30 against 28/30, in zero milliseconds,
and the two errors it does not make are the two that matter most.

**smollm2 found everything and could not say it.** All fourteen of its
wrong answers on present cases are the correct six digits with `ORD-`
stripped: `ORD-556120` came back as `556120`, fourteen times. It did not
fail to extract. It failed to return the format the prompt asked for. By
the contract that is 8 of 22, and by locating the identifier it is 22 of
22, and the post needs both numbers because they describe different
failures.

That reframes the decoys. smollm2 handed back `MEM-443322`,
`1Z999AA10123456784` and `503-555-0142` verbatim. It has no model of the
format at all; it returns whatever in the message looks most like an
identifier, prefix and all. The regex ignores all three without knowing
anything.

**qwen's two errors are the interesting ones**, because at 28/30 the model
looks deployable until you read them.

- `ex10`: input `ORD-999000: wrong address, please hold.` Answer: `999000`.
  The same prefix strip, once.
- `ex18`: input `ORD-111222 please refund`. Answer: `NONE`.

The second is the whole argument in one case. The shortest, least decorated
input in the set, almost entirely order number, and the model returned a
confident, well-formatted assertion that there is no order number in it. A
false negative in a pipeline means the order exists and the system says it
does not. A regex cannot make that mistake.

**One model failure.** `ex27`, "Thanks for a lovely afternoon yesterday.",
where the correct answer is one word. smollm2 fell into a repetition loop
and Ollama aborted it after 21 seconds, roughly eight times a normal call.
Reproducible across two runs at temperature zero, so the input causes it.

---

## Workflow 1: closed-set classification

Fifty short messages to a small business, six labels, sixteen of them
deliberately ambiguous or borderline.

| | qwen2.5:1.5b | smollm2:360m |
| --- | ---: | ---: |
| Overall | 23/50 (46%) | 15/50 (30%) |
| Labels used | 6 of 6 | 3 of 6 |
| Most common label | complaint, 38% | escalate, **86%** |
| Invalid output | 0 | 1 |
| Confident wrong | 26 | 3 (meaningless, see below) |
| Ambiguous cases | 5/16 | 10/16 (meaningless, see below) |

**smollm2 answered `escalate` to 43 of 50 messages.** It is not
classifying. Twelve of its fifteen correct answers are the cases where
escalate happened to be the right label.

This broke the scorer, and the break is a better finding than the score.
Confident wrong deliberately excludes escalations, on the reasoning that a
model which escalates when unsure is usable while one that routes a legal
notice to billing is not. A model that escalates *always* therefore scores
3 against qwen's 26, and the metric certifies the useless model as six
times safer than the merely mediocre one. The ambiguous-cases line is
contaminated the same way.

**qwen is classifying, and is not good at it.** 46% overall with 26
confident-wrong routings. The pattern worth reading:

- All five billing messages about money problems went to `complaint`
- Seven of twelve escalations went to `complaint`
- The sulfite allergy question went to `complaint`
- The trademark notice went to `complaint`
- "Someone slipped on the steps and hurt their wrist" went to `complaint`

That last group is the deployment answer. An injury report, a legal notice
and an allergy question all routed to the complaints queue, confidently,
with no escalation.

---

## Workflow 5: grounded question answering

Fifteen questions against a four-document corpus. Four have no answer in
the material.

| | qwen2.5:1.5b | smollm2:360m |
| --- | ---: | ---: |
| Answerable questions correct | **0/11** | **0/11** |
| Abstained correctly (of 4) | 4 | 0 |
| Fabricated (of 4) | 0 | 4 |
| Over-abstained (of 11) | 9 | 1 |
| Abstained overall (of 15) | **13** | 1 |

**Neither model answered a single answerable question correctly.** This is
the hand-checked result and it is not visible anywhere in the automated
output.

smollm2 answered ten of eleven and missed all ten. Vineyard tier is six
bottles, it said twelve. Harvest began 9 September, it said 15 April. A
returned shipment is a $25 restocking fee, it invented a return shipping
fee. The two-passage fee question is $40, it said $100.

qwen answered two of eleven and missed both, producing generic
e-commerce boilerplate for the returned-shipment question and getting the
club-member fee question wrong on both halves.

**qwen's perfect abstention score is the same collapse as smollm2's
escalate.** It said `NOT IN THE MATERIAL` to 13 of 15 questions. Its 4/4 on
the unanswerable ones is not discrimination, it is a stuck needle that
happened to point the right way four times.

### Two answers worth keeping

smollm2, asked how many people can take the barrel room tour:

> The barrel room tour is a popular attraction in New Orleans, where
> visitors can explore the historic barrel-making process.

Nothing in the corpus mentions New Orleans. The answer is ten.

smollm2, asked whether a dog can come inside the tasting room:

> Yes, you can bring a dog inside the tasting room.

The corpus says the patio is dog friendly and the indoor room is not,
service animals excepted. A confident yes to a question whose answer is no,
in a category where being wrong means someone gets turned away at the door.

And the fabrications on the four unanswerable questions, which are what a
system with no evidence produces when it will not say so:

> The alcohol percentage of the 2024 estate Pinot Noir is 12.5%.
> The Cellar tier costs $10 per quarter.
> The yeast strain used on the 2024 Pinot Gris was Saccharomyces
> cerevisiae, commonly known as white wine yeast.

The yeast answer is the dangerous one. That genuinely is the common wine
yeast, so it reads as expertise rather than invention.

---

## Compute

| Workflow | Model | tok/s | Prompt tokens | Answer tokens | Wait to start |
| --- | --- | ---: | ---: | ---: | ---: |
| extraction | qwen2.5:1.5b | 4.3 | 92 | 9 | 2940 ms |
| extraction | smollm2:360m | 5.9 | 102 | 7 | 1143 ms |
| classification | qwen2.5:1.5b | 7.5 | 104 | 2 | 2369 ms |
| classification | smollm2:360m | 6.2 | 113 | 6 | 939 ms |
| QA | qwen2.5:1.5b | 4.7 | 97 | 5 | 2471 ms |
| QA | smollm2:360m | 5.4 | 110 | 20 | 924 ms |

The compute tax does not run the way parameter count suggests. qwen is
slower than smollm2 on extraction (4.3 against 5.9 tok/s) and faster on
classification (7.5 against 6.2), because on classification it answers in
two tokens where smollm2 takes six.

**Prompt sizes never approached the 4096-token context window.** The
largest prompt in the whole run was 125 tokens, on grounded QA with the
entire corpus attached. Context budget was never a constraint at this
scale, and the QA corpus could grow roughly thirty times before it became
one.

**The tok/s figures are weak evidence and the scorer says so.** Every
workflow here generates under ten tokens per answer, which is too few to
time reliably. The clearest demonstration is extraction on qwen, which
reported 4.3 rising to 7.6 tok/s across the run. Hardware does not speed up
partway through. The fast calls are the one-word `NONE` answers.

---

## Thermals

`throttled=0x0` before and after all six runs. The latency numbers describe
the models.

This matters because **the previous day's attempt did not.** Running with
heat sinks and no fan, a thirty-call run of a 360M model was enough to hit
the Pi 4's soft temperature limit and start capping the clock:
`throttled=0xe0000`, three bits set, all of them "has happened since boot".
Those latency numbers were discarded.

Nothing in Ollama's output, the scorer, or the result files reported it.
Every number on screen was internally consistent and describing a machine
that was slowing down. The only way to find out was to ask the firmware a
question you have to already suspect the answer to.

Correctness was unaffected. Extraction reproduced exactly across the
throttled and clean runs, including the same `ex27` failure, which is what
you would expect at temperature zero and is worth having confirmed rather
than assumed.

The scorer now carries a decay check that flags the shape in the data. It
was written because of that run.

---

## Offline

```
=== before: the network should be up
    dns lookup  reachable
    ping 1.1.1.1 reachable

=== after: the network should be gone
    dns lookup  no answer
    ping 1.1.1.1 no route

=== running one call from each workflow, with no route out
  extraction       OK   5.8 tok/s      'ORD-448120'
  classification   OK   6.2 tok/s      'Category: Escalate'
  grounded qa      OK   5.7 tok/s      'The Vineyard tier has 12 bottles per quarter.'
```

All three workflows ran with the radio off, DNS dead and no route out.

**The claim this supports is narrow.** This configuration, on this
afternoon, ran with no route to the internet. It is not a claim that local
models are private, or that this setup is secure. A Raspberry Pi can be
misconfigured as thoroughly as a cloud service.

Note the QA answer in that transcript is wrong: the Vineyard tier is six
bottles, not twelve. The probe only establishes that inference ran.

Full transcript: `offline-test.log` in this directory.

---

## What this run taught us about the harness

Three measurement flaws, all found by looking at the data rather than by
reading the code, and all the same shape.

**1. A vacuous fixture.** Found before the run. A test that passed while
measuring nothing, because the fixture was inert either way.

**2. A metric a stuck classifier can game.** Confident wrong excluded
escalations to reward caution, and a model that escalated always scored
near zero on it while being useless.

**3. A metric a refusing model can game.** Correct abstention rewarded
knowing when evidence is absent, and a model that abstained on 87% of
questions scored a perfect four out of four.

The common failure: **a metric that rewards the safe behaviour will
certify any model that only ever does the safe thing.** The exemption needs
to be paired with evidence that the model is making distinctions at all,
or it is measuring nothing and saying so in confident numbers.

A fourth, smaller: the keyword check on QA answers scored 1 of 11 for both
models, and that single hit was the word "reservation" inside an answer
that invented a $100 fee where the correct answer is $40. It was labelled
"indicative only" and was in fact noise. The only way to know whether an
answer is right was to read all thirty of them.

---

## Verdicts

| Workload | Verdict | Why |
| --- | --- | --- |
| Extraction | **Unnecessary** | Regex 30/30 at zero latency; best model 28/30 with two silent errors |
| Classification | **Insufficient** | Best model 46% with 26 confident-wrong; the other collapsed onto one label |
| Grounded QA | **Insufficient** | 0 of 11 for both models, by opposite failure modes |

---

## Where I was wrong

Eight predictions right, twelve wrong, two unresolvable. Four of seven
confident calls broke. The tally is in `predictions.md`; these are the four
that earned a paragraph.

**I expected the small model to get most of the straightforward extraction
cases.** It got 8 of 22. But the way it failed is more interesting than the
number: it found the correct identifier in all 22 and stripped the prefix
on 14 of them. I had the failure in the wrong place, expecting it to
struggle at finding things and finding instead that it struggles at
returning them in a specified shape. The decoys follow from the same gap.

**I expected the small model to produce invalid output often.** Once in
fifty. It is perfectly capable of emitting one of six words on command. It
just emitted the same one 43 times.

**I expected the mid model to abstain on some of the unanswerable
questions.** It abstained on all four, and then on nine of the eleven
answerable ones too, which is a different behaviour wearing the same
result. I was predicting judgement and observed refusal. The scorer could
not tell the difference either, which is how the flaw got found.

**I expected some of the two-passage questions to fail.** All three did,
for both models, along with all eight single-passage ones. I was imagining
a gradient where combining two passages is harder than reading one. There
is no gradient here. Neither model could answer anything.

**What I got right, and understated.** The freeform prediction was that a
regex from the 1950s and 60s would still be useful in 2026. It did not
merely hold up. It won outright, and its margin is entirely in the two
error types a regex is structurally incapable of making: inventing an
identifier that is not there, and denying one that is.

---

## What would change my mind

The 360M model's extraction failure is purely a format failure. It located
every identifier and returned the wrong shape. That is exactly what
grammar-constrained decoding targets, and it is not tested here.

The obvious follow-up: same fixtures, same version, Ollama's JSON schema
enforcement against raw prompting. Does forcing the format turn 8 into 22,
or does constraining a 360M model into a grammar it cannot satisfy produce
more `ex27`-style repetition loops? One documented loop already exists, so
the second hypothesis is not idle.

That belongs in its own run directory, with its own predictions written
first.

