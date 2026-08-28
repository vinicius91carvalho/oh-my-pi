#!/usr/bin/env python3
"""Round 1 (results-real) vs round 2 (results-real-v2): pass, minutes, peak
prompt tokens per bug and mode, side by side. Round 2 also has the LSP tasks."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
ORDER = ["base", "p7k", "p5k", "p3k"]
def load(d):
    out = {}
    for p in ORDER:
        f = os.path.join(HERE, d, p, "scores.jsonl")
        if os.path.exists(f):
            out[p] = {json.loads(l)["id"]: json.loads(l) for l in open(f) if l.strip()}
    return out
r1, r2 = load("results-real"), load("results-real-v2")
ids = [json.loads(l)["id"] for f in ("real/bugs.jsonl", "real/bugs-lsp.jsonl") for l in open(os.path.join(HERE, f)) if l.strip()]
def cell(r):
    if r is None: return "-"
    m = "pass" if r["pass"] else "FAIL"
    if r.get("aborted"): m += f"+{r['aborted']}ab"
    return f"{m} {round(r['seconds']/60)}m {round((r.get('max_prompt_tokens') or 0)/1000,1)}k"
print("| bug | " + " | ".join(f"{p} r1 | {p} r2" for p in ORDER) + " |")
print("|---|" + "---|" * (2 * len(ORDER)))
for i in ids:
    print(f"| {i} | " + " | ".join(f"{cell(r1.get(p, {}).get(i))} | {cell(r2.get(p, {}).get(i))}" for p in ORDER) + " |")
def tot(rs, p, subset):
    d = rs.get(p); 
    if not d: return "-"
    rows = [d[i] for i in subset if i in d]
    return f"{sum(r['pass'] for r in rows)}/{len(rows)}" if rows else "-"
bugs8 = ids[:8]; lsp = ids[8:]
print("| **8 bugs** | " + " | ".join(f"{tot(r1,p,bugs8)} | {tot(r2,p,bugs8)}" for p in ORDER) + " |")
print("| **LSP tasks** | " + " | ".join(f"{tot(r1,p,lsp)} | {tot(r2,p,lsp)}" for p in ORDER) + " |")
def minutes(rs, p):
    d = rs.get(p)
    return "-" if not d else str(round(sum(r["seconds"] for r in d.values() if r["id"] in bugs8)/60))
print("| **min, 8 bugs** | " + " | ".join(f"{minutes(r1,p)} | {minutes(r2,p)}" for p in ORDER) + " |")
