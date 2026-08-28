#!/usr/bin/env python3
"""Join results-real/<profile>/scores.jsonl into one markdown table."""
import glob, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
ORDER = ["base", "p7k", "p5k", "p3k"]
data = {}
for p in ORDER:
    f = os.path.join(HERE, "results-real", p, "scores.jsonl")
    if os.path.exists(f):
        data[p] = {json.loads(l)["id"]: json.loads(l) for l in open(f) if l.strip()}
bugs = [json.loads(l) for l in open(os.path.join(HERE, "real", "bugs.jsonl")) if l.strip()]
profs = [p for p in ORDER if p in data]
print("| bug | level | " + " | ".join(profs) + " |")
print("|---|---|" + "---|" * len(profs))
def cell(r):
    if r is None: return "-"
    mark = "pass" if r["pass"] else ("tests ok, touched tests" if r["tests_ok"] else "FAIL")
    if r.get("aborted"): mark += f", {r['aborted']} aborted stream(s)"
    tok = r.get("max_prompt_tokens")
    return f"{mark} ({round(r['seconds']/60)} min, max {tok or '?'} tok)"
for b in bugs:
    print(f"| {b['id']} | {b['level']} | " + " | ".join(cell(data[p].get(b["id"])) for p in profs) + " |")
print("| **total** | | " + " | ".join(f"{sum(r['pass'] for r in data[p].values())}/{len(bugs)}" for p in profs) + " |")
