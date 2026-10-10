# Results: Raspberry Pi 4, 9 October 2026

Fixture set: **v1**
Predictions: `predictions.md` in this directory, committed before anything
was installed.
Limits on what these numbers support: `../../LIMITATIONS.md`. Read it
before citing any of this.

> **Read this first.** The grounded QA workflow was run twice on 9 October.
> The first run was invalid: `fixtures/corpus/` had never been committed to
> the repository, so all fifteen questions were asked against an empty
> reference block. Nothing in the harness reported it. The numbers in this
> document are from the rerun, against the restored corpus, and the invalid
> run is described in full under **What this run taught us about the
> harness**, because it is the most useful thing the weekend produced.

## Setup

| Field | Value |
|---|---|
| Device | Raspberry Pi 4, 4 GB RAM |
| Storage | 32 GB SD card |
| Cooling | Heat sinks and fan |
| OS | Debian GNU/Linux 13, 6.18.50+rpt-rpi-v8 |
| Runtime | Ollama 0.40.1 |
| Python | 3.13.5 |
| Models | qwen2.5:1.5b `65ec06548149`, smollm2:360m `297281b699fc` |
| Quantisation | Ollama default for each tag |
| Total hardware cost | $169.99 USD |
| Date | 2026-10-09 |
| Throttled | `0x0` before and after every run, including the QA rerun |

## Summary

| Workflow | Model | Score | Median latency | Median tok/s |
| --- | --- | ---: | ---: | ---: |
| extraction | regex | 30/30 | 0 ms | n/a |
| extraction | qwen2.5:1.5b | 28/30 | 4972 ms | 4.3 |
| extraction | smollm2:360m | 8/30 | 2556 ms | 5.9 |
| classification | qwen2.5:1.5b | 23/50 | 2885 ms | 7.5 |
| classification | smollm2:360m | 15/50 | 1881 ms | 6.2 |
| grounded QA | qwen2.5:1.5b | 9/11 answerable | 6921 ms | 3.7 |
| grounded QA | smollm2:360m | 7/11 answerable | 6406 ms | 4.6 |

The QA scores are hand-checked. The scorer reports abstention counts and a
keyword check, neither of which is the result; both are discussed below.

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

Fifteen questions against a four-document corpus, 2,626 characters,
roughly 650 tokens. Eight are answerable from one passage, three require
combining two, and four have no answer in the material.

Every answer was read by hand against the corpus. The table below is that
reading, not the scorer's.

| | qwen2.5:1.5b | smollm2:360m |
| --- | ---: | ---: |
| Single passage (8) | **8/8** | 7/8 |
| Two passage (3) | 1/3 | 0/3 |
| **Answerable total (11)** | **9/11** | **7/11** |
| Abstained correctly (4) | 2/4 | 0/4 |
| Fabricated (4) | 2/4 | 4/4 |

Three separate capability boundaries show up here, and they are the finding.

### Retrieval works

qwen answered all eight single-passage questions correctly. Six bottles in
the Vineyard tier. Twenty dollars per person. September 9th. Thirty-four
states. No dogs indoors. 21.8 Brix on the 12th. A twenty-five dollar
restocking fee. Ten people on the barrel room tour.

On `qa11`, "if I join the club today and immediately want out, what
happens", it returned the two sentences that answer the question and
nothing else:

> Cancellation requires one completed shipment. Members who cancel before
> receiving a shipment are charged for that shipment.

That is a 1.5 billion parameter model doing competent lookup across four
documents on a $170 computer with no network connection.

smollm2 managed 7 of 8, which is a result in its own right, though several
of its correct answers are the corpus sentence returned verbatim. Asked
when the harvest began it replied "The 2024 harvest began 9 September,
roughly ten days earlier than 2023", which is the source line including the
clause nobody asked about. That is extraction rather than comprehension,
and on a single-fact lookup it is enough.

### Combination does not

All three two-passage questions needed two documents reconciled. qwen got
one. smollm2 got none.

`qa09` is the clearest. A club member brings five guests on a Saturday.
Club policy waives tasting fees for the member plus three guests; the
tasting room charges twenty dollars per person. Six people, four waived,
two paying: forty dollars. **Both models answered twenty.** Neither could
carry "plus three guests" against a party of six and subtract. qwen did get
the second half right, correctly reasoning that a party of six is not a
group larger than six and therefore needs no reservation, which is the only
piece of two-passage reasoning either model performed.

`qa10` is the most instructive failure in the run. Asked why someone would
not find a 2024 rose and what they would be offered instead, qwen quoted
the corpus exactly:

> ...the reference material states that "We did not bottle a rose in 2024.
> The fruit that would normally go to rose was needed to make volume on the
> estate Pinot Noir." Therefore, the 2024 rose would be replaced with the
> fruit that would typically go into the estate Pinot Noir production.

The quotation is verbatim and correct. The sentence immediately after it
reverses the direction of the only relationship in that quotation. The
fruit went *into* the Pinot Noir, so what you would be offered is the Pinot
Noir. You cannot be offered fruit. Correct retrieval and inverted
inference, in consecutive sentences, with the evidence sitting on screen
between them.

smollm2's two-passage failures are worse than wrong. They are
cross-contaminated. On `qa09` it imported the fourteen-days-notice rule,
which governs skipping a club shipment, and applied it to booking a tasting
room reservation. On `qa11` it reached into the shipping document and
answered that you would be asked to sign for the shipment. On `qa10` it
invented a "2024 Rose tasting room tour" and attached the private-events
booking line to it. Given more documents to search, it finds more wrong
ones.

### Knowing the answer is absent is the weakest link

qwen abstained correctly on two of the four unanswerable questions and
fabricated the other two. smollm2 fabricated all four.

qwen's fabrications are a more dangerous species than outright invention.
Asked the alcohol percentage of the 2024 estate Pinot Noir, which is not in
the corpus, it answered:

> The 2024 estate Pinot Noir had a Brix range of 23.1 to 24.6 at pick.

Every component of that is true. It is the right wine, the right vintage,
the right numbers, from the right document. Brix is sugar at harvest and
has nothing to do with alcohol in the bottle. The model reached for the
nearest real fact rather than inventing one, and produced something that
reads as expertise and answers a question nobody asked.

Both models made the same category error on `qa14`. Asked what the Cellar
tier costs per quarter, which the corpus does not say, both answered
"twelve bottles per quarter." Grounding gave them the right tier and they
handed back the quantity in place of the price.

### The one answer the corpus did not change

smollm2, asked whether a dog can come inside the tasting room:

> Yes, you can bring a dog inside the tasting room.

Byte for byte the same answer it gave in the invalid run, with no corpus at
all. The corpus says the patio is dog friendly and the indoor room is not,
service animals excepted. Having the evidence directly in the prompt
changed nothing.

That is the single most useful artifact in the experiment, and it is
stronger now than it was before the corpus was restored, because the
obvious objection, that the model had nothing to work from, no longer
applies. It had the answer in front of it and said the opposite,
confidently, in a category where being wrong means a family gets turned
around at the door.

---

## Compute

| Workflow | Model | tok/s | Prompt tokens | Answer tokens | Wait to start |
| --- | --- | ---: | ---: | ---: | ---: |
| extraction | qwen2.5:1.5b | 4.3 | 92 | 9 | 2940 ms |
| extraction | smollm2:360m | 5.9 | 102 | 7 | 1143 ms |
| classification | qwen2.5:1.5b | 7.5 | 104 | 2 | 2369 ms |
| classification | smollm2:360m | 6.2 | 113 | 6 | 939 ms |
| QA | qwen2.5:1.5b | 3.7 | 708 | 15 | 2845 ms |
| QA | smollm2:360m | 4.6 | 786 | 22 | 1330 ms |

**The compute tax does not run the way parameter count suggests.** qwen is
slower than smollm2 on extraction (4.3 against 5.9 tok/s) and faster on
classification (7.5 against 6.2), because on classification it answers in
two tokens where smollm2 takes six.

Note also that the same corpus tokenises to 708 for qwen and 786 for
smollm2. Prompt size is a property of the pairing, not of the text.

### What 650 tokens of context actually cost

This is the one measurement the invalid run could not produce, because its
prompts were empty. Comparing the two QA runs on qwen isolates it:

| | empty corpus | real corpus | change |
| --- | ---: | ---: | ---: |
| Prompt tokens, median | 97 | 708 | 7.3x |
| Wait to start, median | 2471 ms | 2845 ms | +15% |
| Generated tokens, median | 5 | 15 | 3x |
| Generation speed | 4.7 tok/s | 3.7 tok/s | -21% |
| Total latency, median | 3577 ms | 6921 ms | 1.9x |
| Total latency, max | 21.9 s | **98.2 s** | 4.5x |

**Processing the prompt is cheap. Generating the answer is not.** Seven
times the prompt cost 15% more time before output began, because prompt
evaluation runs in parallel. Of the 3.3 second increase in median latency,
roughly three seconds is accounted for by answers that got three times
longer, because the model finally had something to say. The remaining cost
shows up as a 21% drop in per-token generation speed, which is the price of
attending over a longer context on every token.

So the practical lesson for this hardware is the opposite of the intuition:
a bigger prompt is affordable, a longer answer is what you pay for.

The 98 second outlier is not explained by any of this and is worth naming
rather than smoothing away. One call in fifteen took fourteen times the
median. `TIMEOUT=600` covered it; the default would not have.

**Prompt sizes still never approached the context window.** 786 tokens
against 4096 at the largest. The corpus could grow roughly four times
before the window became the constraint, and latency would become
unacceptable well before that.

**The tok/s figures on extraction and classification are weak evidence and
the scorer says so.** Both generate under ten tokens per answer, which is
too few to time reliably. The clearest demonstration is extraction on qwen,
which reported 4.3 rising to 7.6 tok/s across the run. Hardware does not
speed up partway through. The fast calls are the one-word `NONE` answers.
The QA runs, at 15 and 22 tokens median, are the only generation-speed
numbers here that carry much weight.

---

## Thermals

`throttled=0x0` before and after all runs, including the QA rerun with
700-token prompts and a 98 second call in it. The latency numbers describe
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

The reading is also perishable. `get_throttled` reports bits set since
boot, so the evidence for the QA rerun existed only until the next power
cycle and had to be collected before shutting the board down.

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

**This transcript predates the corpus fix**, which is visible in it: the QA
answer says the Vineyard tier has twelve bottles, and the correct answer is
six. That call was made against the empty reference block. The offline
claim is unaffected, since whether inference reaches the network has
nothing to do with what is in the prompt, but the transcript is evidence
from the invalid state and is kept here as such.

Full transcript: `offline-test.log` in this directory.

---

## What this run taught us about the harness

Five measurement flaws. Every one was found by reading data rather than
code, and four of them share a single shape.

**1. A vacuous fixture.** Found before the run started. A test that passed
while measuring nothing, because the fixture was inert either way.

**2. A metric a stuck classifier can game.** Confident wrong excluded
escalations in order to reward caution. A model that escalated on 86% of
messages scored 3 where a model actually attempting the task scored 26,
and the metric therefore certified the useless one as six times safer.

**3. A metric a refusing model can game.** Correct abstention rewarded
knowing when evidence is absent. A model that abstained on 87% of all
questions scored a perfect four out of four.

**4. A loader that returned a plausible value for a missing input.**
`fixtures/corpus/` was never committed. `corpus_text()` built a list from a
glob and joined it, and a glob that matches nothing joins to the empty
string without raising. Every one of the fifteen QA questions was asked
against an empty reference block.

Nothing reported it. Every call succeeded. Both models behaved correctly
given what they were actually sent: the one instructed to answer `NOT IN
THE MATERIAL` when the material lacked the answer said it thirteen times
out of fifteen, and the one with no such discipline answered from
parametric knowledge and invented a wine. The scorer scored it. The
resulting numbers were internally consistent, had plausible failure modes
on both sides, and were written up as a finding about model capability,
with quoted evidence and a verdict.

The only witness was the prompt token count. A QA prompt carrying the
corpus is about 708 tokens. The run reported 97. That number was in the
compute table, being read as good news about context headroom. Four hundred
and forty-seven words of reference material cannot be ninety-seven tokens,
and nobody noticed for most of a day.

**5. A keyword check that was pure noise.** On the invalid run it scored 1
of 11 for both models, and the single hit was the word "reservation" inside
an answer that invented a $100 fee. On the valid run it scored 11 of 11 for
qwen, which looks like vindication and is not: one of those eleven hits is
`qa09`, which is wrong, and it hit because the answer contains the word
"reservation". The check agreed with the truth on the rerun because the
answers happened to be right, not because it can tell the difference. The
only way to know whether an answer is correct was to read all thirty of
them, twice.

### The common shape, and the thing it did not cover

Flaws 2, 3 and 5 are one error: **a metric that rewards the safe behaviour
will certify any model that only ever does the safe thing.** An exemption
for caution has to be paired with evidence that the model is making
distinctions at all, or it measures nothing and reports it in confident
numbers.

Flaw 4 is a different error and a worse one, and the relationship between
them is the part worth keeping.

The collapse detector written to catch flaw 3 *did* fire on the invalid QA
run. It said: `!! ABSTAINED on 13/15 questions overall. It is refusing, not
judging.` It was correct that something was wrong. Its diagnosis was
completely wrong. The model was not refusing, it was obeying, and the fault
was upstream in a directory that did not exist. Acting on that diagnosis
produced a 2,700 word write-up of a capability failure that had not
occurred.

**A flag that tells you something is off is not a flag that tells you
what.** The check did its job and the conclusion drawn from it was still
false, because the check could only see the output and the fault was in the
input.

And flaw 4 has a sibling, found the same evening. The offline test's only
product is its transcript. The log file was copied into this directory and
never committed, because the standard Python `.gitignore` template carries
`*.log`, which matches at any depth. The copy succeeded, `git status` came
back clean, and the push reported success with the evidence missing.

Two silent absences in one night, one of them manufacturing a headline
result. The lesson is narrower and more useful than "test your tests":
**absence does not raise.** A missing directory, a missing file and a
missing fixture all present as an ordinary successful run. Every input a
harness depends on needs a loader that refuses to proceed without it, and
every artifact it produces needs to be verified as present rather than
assumed from an exit code.

The fixes are in the repository. `corpus_text()` now raises on an empty or
truncated corpus, the QA run prints the corpus size before its first call,
the scorer flags any QA run whose median prompt is under 400 tokens, and
`.gitignore` no longer lets `*.log` swallow run transcripts.

---

## Verdicts

| Workload | Verdict | Why |
| --- | --- | --- |
| Extraction | **Unnecessary** | Regex 30/30 at zero latency; best model 28/30 with two silent errors |
| Classification | **Insufficient** | Best model 46% with 26 confident-wrong; the other collapsed onto one label |
| Grounded QA | **Marginal** | Single-fact lookup 8/8, two-passage 1/3, correct abstention 2/4 |

- **Unnecessary**: deterministic code already does it
- **Sufficient**: a small local model does it well enough to use unattended
- **Marginal**: usable with a person checking the output
- **Insufficient**: the error or latency profile is not acceptable

Grounded QA is the one verdict that moved, and it moved twice. It was
provisionally Insufficient on the invalid run, on the strength of 0 of 11.
With the corpus actually in the prompt it is Marginal: a 1.5B model will
reliably find a single fact in four documents, will not combine two of them
or do arithmetic across them, and cannot be trusted to tell you when the
answer is not there. That is a usable tool with a person reading the output
and an unusable one without.

---

## Where I was wrong

Ten predictions right, eleven wrong, one unresolvable. Two of seven
confident calls broke, down from four before the QA rerun. The tally is in
`predictions.md`; these are the ones that earned a paragraph.

**I expected the small model to get most of the straightforward extraction
cases.** It got 8 of 22. But the way it failed is more interesting than the
number: it found the correct identifier in all 22 and stripped the prefix
on 14 of them. I had the failure in the wrong place, expecting it to
struggle at finding things and finding instead that it struggles at
returning them in a specified shape. The decoys follow from the same gap.

**I expected the small model to produce invalid output often.** Once in
fifty. It is perfectly capable of emitting one of six words on command. It
just emitted the same one 43 times.

**I expected over-abstention on answerable questions.** Zero out of eleven,
for both models, once they had something to read. The nine-of-eleven
over-abstention I recorded on the first pass was the empty corpus, and
reading it as model behaviour was the single largest error of the weekend.

**I expected a gradient on the two-passage questions, where combining two
passages is harder than reading one.** The gradient is real and much
steeper than I pictured. Single passage: 8 of 8. Two passage: 1 of 3. The
cliff is not in reading, it is in holding two facts at once, and the
arithmetic in `qa09` defeated both models identically.

**What I got right, and understated.** The freeform prediction was that a
regex from the 1950s and 60s would still be useful in 2026. It did not
merely hold up. It won outright, and its margin is entirely in the two
error types a regex is structurally incapable of making: inventing an
identifier that is not there, and denying one that is.

**What I was most wrong about, which is not on the prediction sheet at
all.** I predicted model behaviour for a whole weekend and never predicted
harness behaviour. Four of the five flaws above were in code written to
measure with, not in anything being measured, and the worst of them turned
a missing directory into a published conclusion. The prediction sheet asks
what the models will do. The question it should also ask is what would have
to be true for these numbers to be meaningless, and whether anything in the
harness would say so.

---

## What would change my mind

**The 360M model's extraction failure is purely a format failure.** It
located every identifier and returned the wrong shape. That is exactly what
grammar-constrained decoding targets, and it is not tested here. The
obvious follow-up: same fixtures, same version, Ollama's JSON schema
enforcement against raw prompting. Does forcing the format turn 8 into 22,
or does constraining a 360M model into a grammar it cannot satisfy produce
more `ex27`-style repetition loops? One documented loop already exists, so
the second hypothesis is not idle.

**The two-passage result is the one most likely to be a prompt artifact.**
One question needed arithmetic, one needed a direction of causation held
across a paraphrase, and one needed a fee waiver reconciled with a party
size. Three questions is not enough to separate "cannot combine two
passages" from "cannot do arithmetic" from "cannot resist paraphrasing a
quotation backwards". A fixture version with those three failure modes
tested separately, several questions each, would say which boundary is
real.

**The abstention result deserves a second look with a better prompt.** qwen
abstained correctly on two of four, and both of its fabrications answered a
different question with a genuinely relevant corpus fact. That is not
obviously a capability ceiling. It may be a prompt that does not
distinguish "the material does not contain this" from "the material
contains something adjacent".

Each of those belongs in its own run directory, with its own predictions
written first.