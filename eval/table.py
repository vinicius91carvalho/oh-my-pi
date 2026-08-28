#!/usr/bin/env python3
"""Print every measured configuration side by side."""
import glob, json, os

rows = []
for f in sorted(glob.glob(os.path.expanduser("~/tools/qwen3.8-27b/eval/results-*.json"))):
    d = json.load(open(f))
    by = {r["what"]: r for r in d["runs"]}
    rows.append((d["config"], by, d.get("mem_after", {})))

hdr = f"{'config':<16}{'escrita':>10}{'4k leitura':>13}{'12k leitura':>13}{'12k TTFT':>11}{'cache quente':>14}"
print(hdr); print("-" * len(hdr))
for name, by, mem in rows:
    def pf(k):
        r = by.get(k)
        if not r: return "-"
        if r.get("rejected"): return "INUTIL"
        return f"{r['prefill_tok_s']:.0f} t/s" if r.get("prefill_tok_s") else "-"
    def ttft(k):
        r = by.get(k)
        if not r or r.get("rejected") or not r.get("ttft_s"): return "-"
        s = r["ttft_s"]
        return f"{s/60:.0f} min" if s >= 90 else f"{s:.1f}s"
    dec = by.get("prefill_4k", {}).get("decode_tok_s") or by.get("decode", {}).get("decode_tok_s") or 0
    print(f"{name:<16}{dec:>7.1f} t/s{pf('prefill_4k'):>13}{pf('prefill_12k'):>13}"
          f"{ttft('prefill_12k'):>11}{ttft('cache_warm'):>14}")
    if mem.get("swap"):
        used = [p for p in mem["swap"].split() if p.endswith("M")]
        print(f"{'':<16}swap: {mem['swap'].split('used =')[1].split()[0] if 'used =' in mem['swap'] else '?'}"
              f"   memoria livre: {mem.get('free','?')}")
