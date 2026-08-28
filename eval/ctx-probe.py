#!/usr/bin/env python3
"""How much memory does a given context actually cost, and does it complete?

Watches the server's own memory-pressure reports while one long prompt runs,
so the answer is the observed peak, not a formula.
"""
import json, os, re, subprocess, sys, threading, time, urllib.error, urllib.request
sys.path.insert(0, os.path.expanduser("~/tools/qwen3.8-27b/eval"))
import bench

LOG = os.path.expanduser("~/Library/Logs/omlx.log")
peak = {"gb": 0.0, "note": ""}
stop = threading.Event()


def watch():
    """Tail the server log for the numbers it prints about its own usage."""
    with open(LOG) as f:
        f.seek(0, 2)
        while not stop.is_set():
            line = f.readline()
            if not line:
                time.sleep(0.2)
                continue
            for m in re.finditer(r"current=([\d.]+)GB|at [\d]+ tokens: ([\d.]+)GB", line):
                v = float(m.group(1) or m.group(2))
                if v > peak["gb"]:
                    peak["gb"] = v
            if "Preflight rejected" in line or "throttled" in line:
                peak["note"] = line.strip()[-190:]


def run(tokens):
    t = threading.Thread(target=watch, daemon=True); t.start()
    prompt = f"// ctx:{tokens}:{int(time.time())}\n" + bench.corpus(tokens) + \
             "\n\nIn one short sentence: what is this code about?"
    t0 = time.time()
    r = bench.ttft_and_decode(prompt, 24)
    stop.set(); time.sleep(0.5)
    rss = subprocess.run(
        ["bash", "-c",
         "ps -o rss= -p $(lsof -nP -iTCP:1337 -sTCP:LISTEN -t | head -1) 2>/dev/null"],
        capture_output=True, text=True).stdout.strip()
    print(f"\n=== contexto pedido: ~{tokens} tokens ===")
    if r.get("rejected"):
        print(f"  RECUSADO apos {time.time()-t0:.0f}s")
        print(f"  {r['rejected'][:300]}")
    else:
        print(f"  aceito: prompt={r['prompt_tokens']} tokens  TTFT={r['ttft_s']}s  "
              f"prefill={r['prompt_tokens']/r['ttft_s']:.0f} tok/s")
    print(f"  pico de memoria relatado pelo servidor: {peak['gb']:.1f} GB")
    if peak["note"]:
        print(f"  nota: {peak['note']}")
    print(f"  memoria livre no sistema: "
          f"{subprocess.run(['memory_pressure'],capture_output=True,text=True).stdout.strip().splitlines()[-1]}")


if __name__ == "__main__":
    run(int(sys.argv[1]))
