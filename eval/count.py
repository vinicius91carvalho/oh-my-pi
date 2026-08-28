#!/usr/bin/env python3
"""Count the prompt tokens of a captured omp request, using the oMLX server
itself (`usage.prompt_tokens`) rather than a tokenizer estimate."""
import json, sys, urllib.request, urllib.error

SERVER = "http://127.0.0.1:1337/v1/chat/completions"


def count(payload):
    p = dict(payload)
    p["stream"] = False
    p["max_completion_tokens"] = 1
    p.pop("stream_options", None)
    req = urllib.request.Request(
        SERVER, data=json.dumps(p).encode(), headers={"Content-Type": "application/json"}
    )
    try:
        return json.loads(urllib.request.urlopen(req, timeout=1800).read())["usage"]["prompt_tokens"]
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode()[:200]}


def main(path):
    d = json.load(open(path))
    total = count(d)
    notools = count({**d, "tools": []})
    tools = d.get("tools", [])
    sys_chars = len(d["messages"][0]["content"]) if d["messages"] and d["messages"][0]["role"] == "system" else 0
    out = {
        "total": total,
        "without_tools": notools,
        "tools_tokens": (total - notools) if isinstance(total, int) and isinstance(notools, int) else None,
        "n_tools": len(tools),
        "tool_names": [t.get("function", t)["name"] for t in tools],
        "system_chars": sys_chars,
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1])
