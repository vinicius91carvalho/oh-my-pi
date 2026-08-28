#!/usr/bin/env python3
"""Which tools each run actually called, from the captured requests.

  tools-used.py results-real            -> per profile: tool call counts, xd:// devices used
  tools-used.py results-real/p3k/ts-hard -> one run, in order
"""
import glob, json, os, re, sys
from collections import Counter

def calls_of(run_dir):
    fs = sorted(glob.glob(os.path.join(run_dir, "req-*.json")))
    if not fs: return []
    # The last request holds the whole history (minus what compaction dropped),
    # so union the tool calls of every request by their id.
    seen, out = set(), []
    for f in fs:
        for m in json.load(open(f)).get("messages", []):
            for tc in (m.get("tool_calls") or []):
                if tc.get("id") in seen: continue
                seen.add(tc.get("id"))
                fn = tc["function"]["name"]
                try: args = json.loads(tc["function"]["arguments"])
                except Exception: args = {}
                path = str(args.get("path", ""))
                dev = None
                if path.startswith("xd://"):
                    dev = path[5:].split("/")[0].split("?")[0]
                    fn = f"{fn}(xd://{dev})"
                out.append((fn, dev, args))
    return out

def summarize(run_dirs):
    c, devs = Counter(), Counter()
    for d in run_dirs:
        for fn, dev, _ in calls_of(d):
            c[fn] += 1
            if dev: devs[dev] += 1
    return c, devs

root = sys.argv[1]
if glob.glob(os.path.join(root, "req-*.json")):
    for fn, dev, args in calls_of(root):
        print(fn, json.dumps({k: (str(v)[:60]) for k, v in args.items() if k != "i"}, ensure_ascii=False))
    sys.exit()
for prof in sorted(os.listdir(root)):
    runs = [d for d in glob.glob(os.path.join(root, prof, "*")) if os.path.isdir(d)]
    if not runs: continue
    c, devs = summarize(runs)
    total = sum(c.values())
    print(f"\n## {prof}: {total} tool calls in {len(runs)} runs")
    for fn, n in c.most_common(): print(f"  {n:4}  {fn}")
    if devs: print("  xd:// devices touched:", dict(devs))
