#!/usr/bin/env python3
"""Count prompt tokens for a captured omp request without touching the server.

Renders the model's own chat template over the request and tokenizes the result.

Calibration, measured against the server's own `usage.prompt_tokens` on the
same request: the message half matches (10790 here vs 10792 there), and the
tool half runs about 2% high (22977 vs 22526 total). oMLX normalizes tool
schemas slightly more tightly than `tojson` does. The offset is a constant
across profiles, so this counter is exact enough to rank them; the winners are
re-measured against the server before anything is published.
"""
import json, os, sys
from jinja2 import Environment, BaseLoader

MODEL = os.path.expanduser("~/tools/qwen3.8-27b/True2456/Qwen3.8-27B-AWQ-5.0bpw")


def _tokenizer():
    from tokenizers import Tokenizer

    return Tokenizer.from_file(os.path.join(MODEL, "tokenizer.json"))


def render(req):
    src = open(os.path.join(MODEL, "chat_template.jinja")).read()
    env = Environment(loader=BaseLoader(), trim_blocks=True, lstrip_blocks=True)
    # Compact separators, no key sorting: what the serving side emits. Jinja's
    # default (spaces after ":" and ",") inflated the tool block by ~700 tokens.
    env.policies["json.dumps_kwargs"] = {"ensure_ascii": False, "separators": (",", ":"), "sort_keys": False}
    tmpl = env.from_string(src)
    kwargs = dict(req.get("chat_template_kwargs") or {})
    return tmpl.render(
        messages=req["messages"],
        tools=req.get("tools") or None,
        add_generation_prompt=True,
        enable_thinking=req.get("enable_thinking", True),
        reasoning_effort=req.get("reasoning_effort"),
        **{k: v for k, v in kwargs.items() if k not in ("reasoning_effort",)},
    )


def count(req):
    return len(_tokenizer().encode(render(req), add_special_tokens=False).ids)


def breakdown(path):
    req = json.load(open(path))
    total = count(req)
    notools = count({**req, "tools": []})
    tools = req.get("tools") or []
    per_tool, prev = {}, notools
    for i in range(1, len(tools) + 1):
        n = count({**req, "tools": tools[:i]})
        per_tool[tools[i - 1].get("function", tools[i - 1])["name"]] = n - prev
        prev = n
    sysmsg = req["messages"][0]
    return {
        "total": total,
        "without_tools": notools,
        "tools_tokens": total - notools,
        "n_tools": len(tools),
        "per_tool": per_tool,
        "system_chars": len(sysmsg["content"]) if isinstance(sysmsg.get("content"), str) else 0,
    }


if __name__ == "__main__":
    print(json.dumps(breakdown(sys.argv[1]), indent=2, ensure_ascii=False))
