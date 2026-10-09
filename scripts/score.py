#!/usr/bin/env python3
"""
Score every result file in results/ and print the numbers the article needs.

    python scripts/score.py
    python scripts/score.py --csv > results/summary.csv

Extraction and classification are scored automatically. Grounded QA is
scored automatically for abstention, which is the part that matters, and
flagged for your eyes on the rest. Read the answers yourself; a keyword
check is not comprehension.

Records that carry an 'error' field are counted and reported separately.
A failed call is not a wrong answer and must not be scored as one.
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


def pct(n, d):
    return f"{100.0 * n / d:.0f}%" if d else "n/a"


def split_errors(recs):
    """Separate failed calls from answered ones. Failures are not wrong answers."""
    ok = [r for r in recs if not r.get("error")]
    bad = [r for r in recs if r.get("error")]
    return ok, bad


def report_errors(bad, total):
    if not bad:
        return
    print(f"  !! {len(bad)}/{total} calls FAILED and are excluded from the scores below")
    seen = Counter(r["error"][:80] for r in bad)
    for msg, n in seen.most_common(3):
        print(f"     {n}x {msg}")
    for r in bad[:5]:
        print(f"     {r['id']}")


def score_extraction(data):
    recs, bad = split_errors(data["records"])
    report_errors(bad, len(data["records"]))
    if not recs:
        return 0, 0
    right = sum(1 for r in recs if (r["answer"] or None) == (r["expected"] or None))
    present = [r for r in recs if r["expected"]]
    absent = [r for r in recs if not r["expected"]]
    decoys = [r for r in recs if r["note"].startswith("decoy")]
    invented = [r for r in absent if r["answer"]]
    print(f"  overall      {right}/{len(recs)}  {pct(right, len(recs))}")
    print(f"  present      {sum(1 for r in present if r['answer'] == r['expected'])}/{len(present)}")
    print(
        f"  absent       {sum(1 for r in absent if not r['answer'])}/{len(absent)}  "
        f"(invented an answer {len(invented)} times)"
    )
    print(f"  decoys       {sum(1 for r in decoys if not r['answer'])}/{len(decoys)}")
    for r in invented:
        print(f"    INVENTED  {r['id']}: {r['answer']!r}  <- {r['note']}")
    return right, len(recs)


def score_classification(data):
    recs, bad = split_errors(data["records"])
    report_errors(bad, len(data["records"]))
    if not recs:
        return 0, 0
    right = sum(1 for r in recs if r["answer"] == r["expected"])
    invalid = [r for r in recs if str(r["answer"]).startswith("INVALID")]
    confident_wrong = [
        r
        for r in recs
        if r["answer"] != r["expected"]
        and not str(r["answer"]).startswith("INVALID")
        and r["answer"] != "escalate"
    ]
    ambiguous = [r for r in recs if r["note"].startswith(("ambiguous", "borderline"))]
    amb_right = sum(1 for r in ambiguous if r["answer"] == r["expected"])
    print(f"  overall          {right}/{len(recs)}  {pct(right, len(recs))}")
    print(f"  invalid output   {len(invalid)}")
    print(f"  confident wrong  {len(confident_wrong)}   <- the number that matters")
    print(f"  ambiguous cases  {amb_right}/{len(ambiguous)}")
    conf = defaultdict(Counter)
    for r in recs:
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
    return right, len(recs)


def score_qa(data):
    recs, bad = split_errors(data["records"])
    report_errors(bad, len(data["records"]))
    if not recs:
        return 0, 0
    absent = [r for r in recs if r["kind"] == "absent"]
    answerable = [r for r in recs if r["kind"] != "absent"]

    def abstained(r):
        low = (r["answer"] or "").lower()
        return any(m in low for m in ABSTAIN_MARKERS)

    correct_abstain = [r for r in absent if abstained(r)]
    fabricated = [r for r in absent if not abstained(r)]
    over_abstain = [r for r in answerable if abstained(r)]
    keyword_hit = [
        r
        for r in answerable
        if not abstained(r)
        and (
            not r["must_contain_any"]
            or any(k.lower() in (r["answer"] or "").lower() for k in r["must_contain_any"])
        )
    ]
    print(f"  abstained correctly  {len(correct_abstain)}/{len(absent)}   <- the number that matters")
    print(f"  fabricated           {len(fabricated)}/{len(absent)}")
    print(f"  over-abstained       {len(over_abstain)}/{len(answerable)}")
    print(f"  keyword present      {len(keyword_hit)}/{len(answerable)}  (indicative only, read them)")
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
        failed = sum(1 for r in data["records"] if r.get("error"))
        rows.append((data["workflow"], data["model"], n, d, med, failed))

    print("\n=== summary")
    print(f"{'workflow':<16}{'model':<22}{'score':<10}{'median ms':>10}{'failed':>9}")
    for w, m, n, d, med, failed in rows:
        print(f"{w:<16}{m:<22}{f'{n}/{d}':<10}{med:>10.0f}{failed:>9}")
    if any(r[5] for r in rows):
        print("\nSome calls failed. Those runs are incomplete and the scores above")
        print("are computed over the calls that succeeded only.")

    if "--csv" in sys.argv:
        print("\nworkflow,model,score,total,median_ms,failed")
        for w, m, n, d, med, failed in rows:
            print(f"{w},{m},{n},{d},{med:.0f},{failed}")


if __name__ == "__main__":
    main()