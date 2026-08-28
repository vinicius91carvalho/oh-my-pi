#!/usr/bin/env python3
"""Did compaction fire in a long run, and did the agent keep working after it?

Reads req-NNN.json in order. Compaction shows up as a request whose message
count drops while a summary message appears. After it, we check the agent
still called tools and still reached xd:// devices when the profile mounts
them there.
"""
import glob, json, os, re, sys

d = sys.argv[1]
reqs = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(d, "req-*.json")))]
rows, compact_at = [], None
prev_n = 0
for i, r in enumerate(reqs, 1):
    msgs = r.get("messages", [])
    text = json.dumps(msgs, ensure_ascii=False)
    # Two shapes: an in-turn compaction summary, or omp's print-mode resume
    # ("Resume prior conversation. Earlier turns archived under HISTORY").
    is_summary = bool(re.search(r"compact|summary of the (conversation|session)|context was compacted|archived under HISTORY", text, re.I)) and len(msgs) < prev_n
    tools = [t["function"]["name"] for t in r.get("tools", [])]
    xd = len(re.findall(r"xd://", text))
    calls = re.findall(r'"name"\s*:\s*"([a-z_]+)"\s*,\s*"arguments"', text)
    rows.append({"req": i, "messages": len(msgs), "top_level_tools": len(tools), "xd_refs": xd, "tool_calls_in_history": len(calls)})
    if is_summary and compact_at is None:
        compact_at = i
    prev_n = len(msgs)
after = [x for x in rows if compact_at and x["req"] > compact_at]
print(json.dumps({
    "requests": len(rows),
    "compaction_fired": compact_at is not None,
    "compaction_at_request": compact_at,
    "max_messages_before": max((x["messages"] for x in rows[: (compact_at or len(rows))]), default=0),
    "requests_after_compaction": len(after),
    "tool_calls_after_compaction": (after[-1]["tool_calls_in_history"] if after else 0),
    "xd_refs_after_compaction": sum(x["xd_refs"] for x in after),
    "rows": rows,
}, indent=1))
