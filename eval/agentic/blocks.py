#!/usr/bin/env python3
"""Token cost of the two MCP-enumeration blocks in a captured request."""
import json, os, re, sys
from tokenizers import Tokenizer

MODEL = os.path.expanduser("~/tools/qwen3.8-27b/True2456/Qwen3.8-27B-AWQ-5.0bpw")
tok = Tokenizer.from_file(os.path.join(MODEL, "tokenizer.json"))
n = lambda t: len(tok.encode(t, add_special_tokens=False).ids)

s = json.load(open(sys.argv[1]))["messages"][0]["content"]
lines = s.split("\n")


def block(start_pat, stop_pats):
    out, on = [], False
    for l in lines:
        if re.match(start_pat, l):
            on = True
        elif on and any(re.match(p, l) for p in stop_pats):
            break
        if on:
            out.append(l)
    return n("\n".join(out)) if out else 0


catalog = block(r"^## Additional devices", [r"^§ ", r"^# [A-Z]"])
routes = block(r"^## MCP Tool Routes", [r"^## (?!MCP Tool Routes)", r"^§ "])
print(json.dumps({"catalog": catalog, "mcp_routes": routes, "sum": catalog + routes}))
