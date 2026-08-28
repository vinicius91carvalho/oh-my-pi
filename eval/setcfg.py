#!/usr/bin/env python3
"""Set per-model oMLX settings and restart the server so they take effect.

The admin API needs a session this script cannot mint, and every setting we
tune here (MTP, TurboQuant KV, ANE prefill, context window) is read when the
model is loaded anyway, so the honest path is to write the file oMLX itself
writes and bounce the launchd agent.

Usage:  setcfg.py mtp_enabled=true turboquant_kv_bits=3.5
        setcfg.py --reset
"""
import json, os, subprocess, sys, time, urllib.request

MODEL = "Qwen3.8-27B-AWQ-5.0bpw"
PATH = os.path.expanduser("~/.omlx/model_settings.json")
AGENT = f"gui/{os.getuid()}/org.nix-community.home.omlx"


def coerce(v):
    if v.lower() in ("true", "false"):
        return v.lower() == "true"
    if v.lower() in ("null", "none"):
        return None
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v)
    except ValueError:
        return v


def main(args):
    data = {"version": 1, "models": {}}
    if os.path.exists(PATH):
        try:
            data = json.load(open(PATH))
        except json.JSONDecodeError:
            pass
    if "--reset" in args:
        data["models"].pop(MODEL, None)
        args = [a for a in args if a != "--reset"]
    cur = data["models"].setdefault(MODEL, {})
    for a in args:
        k, _, v = a.partition("=")
        cur[k] = coerce(v)
    json.dump(data, open(PATH, "w"), indent=2)
    print("settings:", json.dumps(cur, indent=2) if cur else "(vazio)")

    subprocess.run(["launchctl", "kickstart", "-k", AGENT], check=False)
    for _ in range(120):
        time.sleep(1)
        try:
            urllib.request.urlopen("http://127.0.0.1:1337/v1/models", timeout=3).read()
            print("servidor de pe")
            return
        except OSError:
            continue
    sys.exit("servidor nao voltou")


if __name__ == "__main__":
    main(sys.argv[1:])
