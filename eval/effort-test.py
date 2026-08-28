#!/usr/bin/env python3
"""Prove reasoning_effort actually reaches the model, instead of trusting the config.

Same question at each level; count the reasoning tokens the model emits. If the
counts come out the same, the parameter is being ignored and the pretty config
is a lie.
"""
import json, time, urllib.request

Q = ("A bag has 3 red, 5 blue and 2 green marbles. Two are drawn without "
     "replacement. What is the probability both are blue? Show your reasoning.")


def ask(effort):
    body = {"model": "Qwen3.8-27B-AWQ-5.0bpw",
            "messages": [{"role": "user", "content": Q}],
            "max_tokens": 1500, "temperature": 0.0, "stream": True,
            "stream_options": {"include_usage": True}}
    if effort:
        body["reasoning_effort"] = effort
    req = urllib.request.Request("http://127.0.0.1:1337/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    think = answer = 0
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=900) as r:
        for raw in r:
            line = raw.decode("utf-8", "ignore").strip()
            if not line.startswith("data: ") or line[6:] == "[DONE]":
                continue
            try:
                ev = json.loads(line[6:])
            except json.JSONDecodeError:
                continue
            if ev.get("model") == "keepalive":
                continue
            for ch in ev.get("choices", []):
                d = ch.get("delta", {})
                think += len(d.get("reasoning_content") or "")
                answer += len(d.get("content") or "")
    return {"effort": effort or "(sem parametro)", "chars_pensando": think,
            "chars_resposta": answer, "segundos": round(time.time() - t0, 1)}


for e in (None, "low", "medium", "xhigh"):
    r = ask(e)
    print(f"  {r['effort']:<16} pensou {r['chars_pensando']:>6} chars   "
          f"respondeu {r['chars_resposta']:>5}   {r['segundos']:>6}s")
