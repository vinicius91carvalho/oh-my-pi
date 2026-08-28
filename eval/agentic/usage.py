#!/usr/bin/env python3
"""Summarize usage-NNN.json files of one run: max prompt tokens, request
count, and whether the server ever rejected a prompt (HTTP 400 = too long).

  usage.py <run-dir>           -> JSON summary
  usage.py --max <run-dir>     -> just the max prompt_tokens (or null)
"""
import glob, json, os, sys

def summary(d):
    rows = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(d, "usage-*.json")))]
    prompts = [r["usage"]["prompt_tokens"] for r in rows if r.get("usage") and "prompt_tokens" in r["usage"]]
    return {
        "requests": len(rows),
        "max_prompt_tokens": max(prompts) if prompts else None,
        "first_prompt_tokens": prompts[0] if prompts else None,
        "completion_tokens": sum(r["usage"].get("completion_tokens", 0) for r in rows if r.get("usage")),
        "http_errors": [r["error"] for r in rows if r.get("status", 200) >= 400],
        # 200 with no usage event = the server dropped the stream (oMLX memory
        # guard / prefill capacity rejection). Looks like an empty answer to omp.
        "aborted_streams": sum(1 for r in rows if r.get("status", 200) < 400 and not r.get("usage")),
    }

if __name__ == "__main__":
    if sys.argv[1] == "--max":
        m = summary(sys.argv[2])["max_prompt_tokens"]
        print("null" if m is None else m)
    else:
        print(json.dumps(summary(sys.argv[1]), indent=2))
