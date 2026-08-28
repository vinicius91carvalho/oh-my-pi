#!/usr/bin/env python3
"""Join the token measurements with the task scores into one table."""
import json, glob, os, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
LABEL = {
    "base": "full (default)",
    "settings-only": "settings only",
    "p7k": "compact, 6 tools",
    "p5k": "compact, 4 tools",
    "p3k": "compact, 3 tools",
}
ORDER = ["base", "settings-only", "p7k", "p5k", "p3k"]


def tokens(profile):
    # The benchmark ran inside `fixture/`, so its token column must come from
    # the same place. `runs/` is the real-project ladder and belongs elsewhere.
    f = os.path.join(HERE, "runs-fixture", profile, "tokens.json")
    return json.load(open(f)) if os.path.exists(f) else None


def scores(profile, suite="main"):
    """Rows for one suite only.

    `results/<profile>-rep<N>` holds the 12-task suite; `-repprobe` the xd://
    probes; `-repg<N>` the grounding repeats. A glob over `-rep*` silently
    merged all three and inflated the totals, so each caller names its suite.
    """
    pat = {"main": "-rep[0-9]*", "probe": "-repprobe", "grounding": "-repg[0-9]*"}[suite]
    rows = []
    for f in sorted(glob.glob(os.path.join(HERE, "results", f"{profile}{pat}", "scores.jsonl"))):
        rows += [json.loads(l) for l in open(f)]
    return rows


def main():
    print(f"| profile | prompt tokens | tool schemas | rest | tasks passed | median s |")
    print(f"|---|---:|---:|---:|---:|---:|")
    for p in ORDER:
        t, s = tokens(p), scores(p)
        if not t and not s:
            continue
        tok = f"{t['total']:,}" if t else "-"
        tl = f"{t['tools_tokens']:,}" if t else "-"
        rest = f"{t['without_tools']:,}" if t else "-"
        if s:
            ok = sum(r["pass"] for r in s)
            secs = sorted(r["seconds"] for r in s)
            med = f"{secs[len(secs) // 2]:.0f}"
            passed = f"{ok}/{len(s)}"
        else:
            passed, med = "-", "-"
        print(f"| {LABEL.get(p, p)} | {tok} | {tl} | {rest} | {passed} | {med} |")

    print("\nPer axis:\n")
    axes = ["tool choice", "edit", "run tests", "stop", "ask", "rules"]
    print("| profile | " + " | ".join(axes) + " |")
    print("|---" * (len(axes) + 1) + "|")
    for p in ORDER:
        s = scores(p)
        if not s:
            continue
        by = collections.defaultdict(list)
        for r in s:
            by[r["axis"]].append(r["pass"])
        cells = []
        for a in axes:
            v = by.get(a)
            cells.append(f"{sum(v)}/{len(v)}" if v else "-")
        print(f"| {LABEL.get(p, p)} | " + " | ".join(cells) + " |")

    print("\nFailures:\n")
    for p in ORDER:
        for r in scores(p):
            if not r["pass"]:
                print(f"  {LABEL.get(p, p):18s} {r['id']:9s} {r['axis']}")


if __name__ == "__main__":
    main()
