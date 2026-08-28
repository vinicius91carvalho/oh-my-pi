#!/usr/bin/env python3
"""Measure one oMLX configuration: decode speed, prefill speed and TTFT.

Prompts are built from real source files of the two repos this model is meant
to serve, not synthetic filler, so the prefill numbers reflect the actual
token mix (code, imports, comments) the agent will send.
"""
import json, sys, time, urllib.request, urllib.error, subprocess, glob, os

BASE = "http://127.0.0.1:1337"
MODEL = "Qwen3.8-27B-AWQ-5.0bpw"
REPOS = [os.path.expanduser("~/github/vinicius91carvalho/find-best-job"),
         os.path.expanduser("~/github/vinicius91carvalho/infoproduct")]


def post(path, body, timeout=1800):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())


def put(path, body):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"}, method="PUT")
    return json.loads(urllib.request.urlopen(req, timeout=120).read())


def corpus(approx_tokens):
    """Real source text, roughly `approx_tokens` long (~3.6 chars/token)."""
    want = int(approx_tokens * 3.6)
    out = []
    total = 0
    for repo in REPOS:
        for pat in ("packages/*/src/**/*.ts", "apps/*/src/**/*.ts", "packages/*/*.py", "scripts/*.py"):
            for f in sorted(glob.glob(os.path.join(repo, pat), recursive=True)):
                if "node_modules" in f or ".venv" in f:
                    continue
                try:
                    t = open(f, encoding="utf-8", errors="ignore").read()
                except OSError:
                    continue
                out.append(f"\n// ==== {os.path.relpath(f, repo)} ====\n{t}")
                total += len(out[-1])
                if total >= want:
                    return "".join(out)[:want]
    return "".join(out)[:want] if out else ("x " * (want // 2))


def ttft_and_decode(prompt, max_tokens):
    """Streaming call: measures time to first token and generation rate."""
    body = {"model": MODEL, "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens, "temperature": 0.0, "stream": True,
            "stream_options": {"include_usage": True}}
    req = urllib.request.Request(BASE + "/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        return _stream(req, t0)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")[:300]
        return {"ttft_s": None, "decode_tok_s": 0.0, "out_tokens": 0,
                "wall_s": round(time.time() - t0, 2), "prompt_tokens": None,
                "cached_tokens": None, "prefill_tok_s": None,
                "rejected": f"HTTP {e.code}: {body}"}


def _stream(req, t0):
    """TTFT is the first token of ANY kind.

    Qwen3.8 is a thinking model: it streams `reasoning_content` first and only
    then `content`. Waiting for `content` would report "prefill + all the
    thinking" as time-to-first-token, which on a 69-token prompt measured
    14.5 s instead of well under a second.

    Token counts come from the final usage event, never from counting chunks:
    one SSE chunk carries several tokens, so counting chunks reported 5.4 tok/s
    where the server's own log said 16.3.
    """
    ttft = None
    first_tok_time = None
    usage = {}
    done = False
    tail_events = 0
    end_time = None
    with urllib.request.urlopen(req, timeout=3600) as r:
        for raw in r:
            line = raw.decode("utf-8", "ignore").strip()
            if not line.startswith("data: "):
                continue
            payload = line[6:]
            if payload == "[DONE]":
                break
            try:
                ev = json.loads(payload)
            except json.JSONDecodeError:
                continue
            if ev.get("usage"):
                usage = ev["usage"]
            # The server emits synthetic "keepalive" chunks; one comes before
            # the real work starts (it must not count as the first token) and
            # more keep the socket warm AFTER generation ends. Without breaking
            # on finish_reason the loop sat on those for 926 s and reported
            # 0.3 tok/s for a run the server finished in 20 s.
            if ev.get("model") == "keepalive":
                continue
            for ch in ev.get("choices", []):
                if ch.get("finish_reason"):
                    done = True
                delta = ch.get("delta", {})
                if delta.get("content") or delta.get("reasoning_content"):
                    if ttft is None:
                        ttft = time.time() - t0
                        first_tok_time = time.time()
            if done:
                if usage:
                    break
                tail_events += 1
                if tail_events > 5:      # usage is not coming; stop waiting
                    break
    end_time = time.time()
    wall = end_time - t0
    gen = (end_time - first_tok_time) if first_tok_time else wall
    out = usage.get("completion_tokens") or usage.get("output_tokens") or 0
    return {"ttft_s": round(ttft or wall, 2),
            "decode_tok_s": round(out / gen, 1) if out and gen > 0 else 0.0,
            "out_tokens": out, "wall_s": round(wall, 2),
            "prompt_tokens": usage.get("prompt_tokens"),
            "cached_tokens": (usage.get("prompt_tokens_details") or {}).get("cached_tokens"),
            "prefill_tok_s": None}


def mem_snapshot():
    free = subprocess.run(["memory_pressure"], capture_output=True, text=True).stdout
    pct = [l for l in free.splitlines() if "free percentage" in l]
    swap = subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True, text=True).stdout.strip()
    return {"free": pct[0].split(":")[-1].strip() if pct else "?", "swap": swap}


# A per-run nonce, not just the config label: re-running the SAME config would
# otherwise hit the SSD prefix cache it populated last time and report a prefill
# 7x faster than a cold one. Every run must pay the real prefill.
RUN_NONCE = str(int(time.time()))


def _save(label, res):
    json.dump(res, open(os.path.expanduser(
        f"~/tools/qwen3.8-27b/eval/results-{label}.json"), "w"), indent=2)


def run(label, contexts=(4000, 12000)):
    res = {"config": label, "mem_before": mem_snapshot(), "runs": []}

    # Decode: short prompt so prefill is negligible and the number is pure generation.
    d = ttft_and_decode("Write a Python function that merges two sorted lists, "
                        "then explain each step in detail.", 300)
    d["what"] = "decode"
    res["runs"].append(d)
    _save(label, res)

    # Prefill: long real-code prompts. Ask for few tokens so TTFT dominates.
    for ctx in contexts:
        # The unique marker goes FIRST: prefix caching keys on the prompt prefix,
        # so a different first line makes every later token a cache miss. Without
        # it, config B would reuse config A's cached prefill and look 20x faster.
        text = f"// bench:{label}:{RUN_NONCE}:{ctx}\n" + corpus(ctx)
        p = ttft_and_decode(text + "\n\nIn one short sentence: what is this code about?", 24)
        p["what"] = f"prefill_{ctx // 1000}k"
        if p["prompt_tokens"] and p["ttft_s"]:
            p["prefill_tok_s"] = round(p["prompt_tokens"] / p["ttft_s"], 1)
        res["runs"].append(p)
        _save(label, res)

    # The SSD prefix cache is the main reason to run oMLX for coding agents.
    # Measure it: same 16k prompt twice, the second should be nearly free.
    warm_text = f"// bench:{label}:{RUN_NONCE}:cache\n" + corpus(12000) + "\n\nName one file in this code."
    c1 = ttft_and_decode(warm_text, 16); c1["what"] = "cache_cold"
    c2 = ttft_and_decode(warm_text, 16); c2["what"] = "cache_warm"
    for c in (c1, c2):
        if c["prompt_tokens"] and c["ttft_s"]:
            c["prefill_tok_s"] = round(c["prompt_tokens"] / c["ttft_s"], 1)
    res["runs"] += [c1, c2]

    res["mem_after"] = mem_snapshot()
    _save(label, res)
    return res


if __name__ == "__main__":
    label = sys.argv[1] if len(sys.argv) > 1 else "unnamed"
    out = run(label)
    path = os.path.expanduser(f"~/tools/qwen3.8-27b/eval/results-{label}.json")
    print(f"\n### {label}")
    for r in out["runs"]:
        if r.get("rejected"):
            print(f"  {r['what']:<14} RECUSADO pelo guarda de memoria: {r['rejected'][:110]}")
            continue
        print(f"  {r['what']:<14} prompt={str(r['prompt_tokens']):>6}  "
              f"cached={str(r['cached_tokens']):>6}  TTFT={r['ttft_s']:>7}s  "
              f"prefill={str(r['prefill_tok_s']):>7} tok/s  decode={r['decode_tok_s']:>5} tok/s")
    print(f"  memoria: {out['mem_before']['free']} livre antes -> {out['mem_after']['free']} depois")
    print(f"  swap: {out['mem_after']['swap']}")
    print(f"  -> {path}")
