#!/usr/bin/env python3
"""
Score every result file in results/ and print the numbers the article needs.

    python scripts/score.py
    python scripts/score.py --csv > results/summary.csv

Extraction and classification are scored automatically. Grounded QA is
scored automatically for abstention, which is the part that matters, and
flagged for your eyes on the rest. Read the answers yourself; a keyword
check is not comprehension.

Two kinds of failure are handled differently, and the distinction matters:

  transport  the call never reached a working model. Excluded from the
             scores, and the run is reported as incomplete.
  model      the model ran and produced no usable answer, for instance a
             prediction Ollama aborted for repetition. Counted against the
             model on a line of its own. Dropping these would quietly
             discard the cases a model cannot handle.

Each run also gets a compute section: generation speed, prompt size, and a
check for whether speed decayed across the run. That last one is a
throttling detector. Wall-clock latency cannot separate a slow machine from
a long answer; tokens per second can.
"""

import json
import pathlib
import sys
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
RES = ROOT / "results"
ABSTAIN_MARKERS = [
    "not in the material",
    "not in the reference",
    "does not contain",
    "no information",
    "cannot find",
    "can't find",
    "not specified",
    "not mentioned",
    "not stated",
    "unable to find",
]

# How much slower the end of a run may be than the start before it is
# called out. Thermal throttling on a small board shows up as a steady
# decline well beyond this.
DECAY_FLAG = 0.90


def pct(n, d):
    return f"{100.0 * n / d:.0f}%" if d else "n/a"


def median(xs):
    xs = sorted(x for x in xs if x is not None)
    return xs[len(xs) // 2] if xs else None


def split(recs):
    """Answered, model failures, transport failures.

    Model failures stay in the denominator. Transport failures do not: nothing
    was measured, so counting them would be reporting a number that was never
    taken.
    """
    answered = [r for r in recs if not r.get("error")]
    failed_model = [r for r in recs if r.get("error_kind") == "model"]
    failed_transport = [r for r in recs if r.get("error_kind") == "transport"]
    # Older result files have no error_kind; treat them as transport.
    legacy = [r for r in recs if r.get("error") and not r.get("error_kind")]
    return answered, failed_model, failed_transport + legacy


def report_failures(no_answer, unreachable, total):
    if no_answer:
        print(f"  no usable answer  {len(no_answer)}/{total}   <- counts against the model")
        for r in no_answer:
            reason = r["error"].split(":", 1)[-1].strip()[:90]
            print(f"    {r['id']}  {reason}")
    if unreachable:
        print(f"  !! {len(unreachable)}/{total} calls never reached a working model")
        for msg, n in Counter(r["error"][:80] for r in unreachable).most_common(3):
            print(f"     {n}x {msg}")
        print("     These are excluded. The run is incomplete.")


def report_compute(recs):
    """Generation speed, prompt size, and whether the machine slowed down.

    Printed for every run that carries metrics. Result files written before
    metrics capture was added have none, and are skipped silently.
    """
    timed = [r for r in recs if r.get("tps") is not None]
    if not timed:
        return None

    med_tps = median([r["tps"] for r in timed])
    med_prompt = median([r.get("prompt_tokens") for r in recs])
    max_prompt = max((r.get("prompt_tokens") or 0 for r in recs), default=0)
    med_gen = median([r.get("gen_tokens") for r in recs])
    med_first = median([r.get("first_token_ms") for r in recs])

    print("  compute:")
    print(f"    generation     {med_tps:.1f} tok/s median")
    print(f"    prompt size    {med_prompt} tokens median, {max_prompt} max")
    print(f"    answer length  {med_gen} tokens median")
    if med_first is not None:
        print(f"    wait to start  {med_first:.0f} ms median (model load + prompt)")

    # Throttle detector. Compare the first third of the run to the last.
    decay = None
    if len(timed) >= 6:
        third = max(1, len(timed) // 3)
        early = median([r["tps"] for r in timed[:third]])
        late = median([r["tps"] for r in timed[-third:]])
        if early and late:
            decay = late / early
            verdict = "steady" if decay >= DECAY_FLAG else "SLOWED DOWN"
            print(
                f"    across the run {early:.1f} -> {late:.1f} tok/s "
                f"({decay * 100:.0f}% of starting speed, {verdict})"
            )
            if decay < DECAY_FLAG:
                print("      Check vcgencmd get_throttled. A run that slows like this")
                print("      was measured on a CPU being clocked down, and the latency")
                print("      numbers above describe the throttling, not the model.")

    # Anything Ollama stopped early rather than finishing.
    cut = Counter(
        r.get("done_reason") for r in recs if r.get("done_reason") not in (None, "stop")
    )
    for reason, n in cut.most_common():
        print(f"    {n} answers ended on '{reason}' rather than finishing")

    return med_tps


def score_extraction(data):
    recs = data["records"]
    answered, no_answer, unreachable = split(recs)
    scored = answered + no_answer
    report_failures(no_answer, unreachable, len(recs))
    if not scored:
        return 0, 0
    right = sum(1 for r in answered if (r["answer"] or None) == (r["expected"] or None))
    present = [r for r in scored if r["expected"]]
    absent = [r for r in scored if not r["expected"]]
    decoys = [r for r in scored if r["note"].startswith("decoy")]
    invented = [r for r in answered if not r["expected"] and r["answer"]]
    declined = [r for r in answered if not r["expected"] and not r["answer"]]
    print(f"  overall      {right}/{len(scored)}  {pct(right, len(scored))}")
    print(
        f"  present      "
        f"{sum(1 for r in answered if r['expected'] and r['answer'] == r['expected'])}"
        f"/{len(present)}"
    )
    print(
        f"  absent       {len(declined)}/{len(absent)} declined correctly  "
        f"(invented {len(invented)}, no usable answer "
        f"{sum(1 for r in no_answer if not r['expected'])})"
    )
    print(
        f"  decoys       "
        f"{sum(1 for r in decoys if not r.get('error') and not r['answer'])}/{len(decoys)}"
    )
    for r in invented:
        print(f"    INVENTED  {r['id']}: {r['answer']!r}  <- {r['note']}")
    return right, len(scored)


def score_classification(data):
    recs = data["records"]
    answered, no_answer, unreachable = split(recs)
    scored = answered + no_answer
    report_failures(no_answer, unreachable, len(recs))
    if not scored:
        return 0, 0
    right = sum(1 for r in answered if r["answer"] == r["expected"])
    invalid = [r for r in answered if str(r["answer"]).startswith("INVALID")]
    confident_wrong = [
        r
        for r in answered
        if r["answer"] != r["expected"]
        and not str(r["answer"]).startswith("INVALID")
        and r["answer"] != "escalate"
    ]
    ambiguous = [r for r in scored if r["note"].startswith(("ambiguous", "borderline"))]
    amb_right = sum(1 for r in answered if r in ambiguous and r["answer"] == r["expected"])
    print(f"  overall          {right}/{len(scored)}  {pct(right, len(scored))}")
    print(f"  invalid output   {len(invalid)}   (a reply that is not one of the six labels)")
    print(f"  confident wrong  {len(confident_wrong)}   <- the number that matters")
    print(f"  ambiguous cases  {amb_right}/{len(ambiguous)}")
    conf = defaultdict(Counter)
    for r in scored:
        conf[r["expected"]][r["answer"]] += 1
    print("  confusion (expected -> got):")
    for exp in sorted(conf):
        got = ", ".join(f"{k} {v}" for k, v in conf[exp].most_common())
        print(f"    {exp:<13} {got}")
    for r in confident_wrong:
        print(
            f"    WRONG  {r['id']}  exp {r['expected']:<12} got {r['answer']:<12} "
            f"{r['input'][:48]!r}"
        )
    return right, len(scored)


def score_qa(data):
    recs = data["records"]
    answered, no_answer, unreachable = split(recs)
    report_failures(no_answer, unreachable, len(recs))
    scored = answered + no_answer
    if not scored:
        return 0, 0
    absent = [r for r in scored if r["kind"] == "absent"]
    answerable = [r for r in scored if r["kind"] != "absent"]

    def abstained(r):
        if r.get("error"):
            return False
        low = (r["answer"] or "").lower()
        return any(m in low for m in ABSTAIN_MARKERS)

    correct_abstain = [r for r in absent if abstained(r)]
    no_answer_absent = [r for r in absent if r.get("error")]
    fabricated = [r for r in absent if not abstained(r) and not r.get("error")]
    over_abstain = [r for r in answerable if abstained(r)]
    keyword_hit = [
        r
        for r in answerable
        if not abstained(r)
        and not r.get("error")
        and (
            not r["must_contain_any"]
            or any(k.lower() in (r["answer"] or "").lower() for k in r["must_contain_any"])
        )
    ]
    print(
        f"  abstained correctly  {len(correct_abstain)}/{len(absent)}"
        "   <- the number that matters"
    )
    print(f"  fabricated           {len(fabricated)}/{len(absent)}")
    if no_answer_absent:
        print(f"  no usable answer     {len(no_answer_absent)}/{len(absent)}  (neither, see above)")
    print(f"  over-abstained       {len(over_abstain)}/{len(answerable)}")
    print(
        f"  keyword present      {len(keyword_hit)}/{len(answerable)}"
        "  (indicative only, read them)"
    )
    for r in fabricated:
        print(f"    FABRICATED  {r['id']}: {r['question']}")
        print(f"                {(r['answer'] or '').strip()[:160]}")
    return len(correct_abstain), len(absent)


def main():
    files = sorted(RES.glob("*.json"))
    if not files:
        print("No results yet. Run scripts/run.py first.")
        return
    rows = []
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        lat = sorted(r["ms"] for r in data["records"])
        med = lat[len(lat) // 2] if lat else 0
        print(
            f"\n=== {data['workflow']} / {data['model']} "
            f"(median {med:.0f} ms, max {lat[-1]:.0f} ms)"
        )
        if data["workflow"] == "extraction":
            n, d = score_extraction(data)
        elif data["workflow"] == "classification":
            n, d = score_classification(data)
        else:
            n, d = score_qa(data)
        tps = report_compute(data["records"])
        _, no_answer, unreachable = split(data["records"])
        rows.append(
            (
                data["workflow"],
                data["model"],
                n,
                d,
                med,
                tps,
                len(no_answer),
                len(unreachable),
            )
        )

    print("\n=== summary")
    print(
        f"{'workflow':<16}{'model':<22}{'score':<10}{'median ms':>10}"
        f"{'tok/s':>8}{'no answer':>11}{'unreached':>11}"
    )
    for w, m, n, d, med, tps, na, un in rows:
        speed = f"{tps:.1f}" if tps is not None else "-"
        print(f"{w:<16}{m:<22}{f'{n}/{d}':<10}{med:>10.0f}{speed:>8}{na:>11}{un:>11}")
    if any(r[7] for r in rows):
        print("\nSome calls never reached a working model. Those runs are incomplete")
        print("and their scores are computed over the calls that ran.")

    if "--csv" in sys.argv:
        print("\nworkflow,model,score,total,median_ms,median_tps,no_answer,unreached")
        for w, m, n, d, med, tps, na, un in rows:
            print(f"{w},{m},{n},{d},{med:.0f},{tps if tps is not None else ''},{na},{un}")


if __name__ == "__main__":
    main()