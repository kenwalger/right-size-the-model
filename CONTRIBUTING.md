# Contributing

Contributions are welcome. One rule matters more than the rest.

## The fixture rule

**Never change an existing fixture in place.**

New fixtures are welcome. Editing one that models have already been run
against silently invalidates every number published against it, and nothing
in the output reveals that it happened.

If a fixture is genuinely wrong (a mislabelled message, an answer that is
actually in the corpus, a decoy that is not a decoy), say so in an issue
rather than fixing it quietly. Fixing it means bumping the fixture set
version in `FIXTURES.md` and noting the change in its history, and it means
any results in the repository were produced against a version that no longer
exists.

See `FIXTURES.md` for the full reasoning and the current version.

## Adding fixtures

Useful additions, roughly in order:

- **Decoys for the extraction set.** Things that look like an order number
  and are not. This is where the finding lives.
- **Ambiguous classification messages**, especially ones where escalating is
  the right answer and a plausible wrong bucket exists.
- **Unanswerable questions** that a reader would expect the corpus to answer.
  Four is a small number.

Keep to the existing shape: one JSON object per line, with a `note` field
saying what the case is for. The note is what lets a later reader tell a
deliberate edge case from a mistake.

Anything new goes in the next fixture version, not into v1.

## Results

`results/` is committed on purpose. The raw replies are the evidence behind
the scores, and a reader should be able to check one against the other.

If you run the kit on different hardware or with different models, a pull
request adding your results is welcome. Include the setup table from
`PREDICTIONS.md` filled in, and the exact model tags. Results without the
hardware and model versions recorded are not comparable to anything.

## Code

`run.py` and `score.py` are standard library only, so the kit runs on a Pi
with nothing installed beyond Ollama. Please keep it that way.

Changes to scoring need care: a change to how abstention is detected changes
every QA number already in the repository. Say so in the pull request if that
is what you are proposing.

## What this repository is not

It is not a benchmark suite and not trying to become one. It is three
workflows chosen to answer one question, sized so the whole thing runs in a
weekend. Additions that make it more thorough at the cost of being
unrunnable in an afternoon are probably a different project.

`LIMITATIONS.md` says what the numbers do and do not support. A change that
widens the claims should update that file too.