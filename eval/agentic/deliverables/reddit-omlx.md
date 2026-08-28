# Qwen3.8-27B on a 36 GB M3 Max: 11 -> 17 -> 32 t/s with oMLX, and what a coding agent does to those numbers over 1,068 requests

**Why.** I wanted a coding agent on my own laptop, no cloud. MacBook Pro M3 Max 14/30, 36 GB. Model: [True2456/Qwen3.8-27B-AWQ-5.0bpw](https://huggingface.co/True2456/Qwen3.8-27B-AWQ-5.0bpw) (18.8 GB resident).

**The speed ladder** (short prompt, 69 tokens):

| server | change | generation |
|---|---|---:|
| llama-server | baseline | ~11 t/s |
| oMLX 0.6.3rc3 | default | 17 t/s (bandwidth limit) |
| oMLX | memory guard raised to 27 GB, TurboQuant KV 3.5-bit, MTP on | **32 t/s**, prefill 137 t/s |

With 36 GB the usable window is ~30k tokens (`contextWindow: 30000` in the harness config). oMLX does not truncate: over the window is HTTP 400, which is the right behaviour for an agent, it just has to be planned for.

**The exact oMLX setup** (0.6.3rc3, launched as a launchd service):

```
omlx-cli serve --model-dir ~/tools/qwen3.8-27b --host 127.0.0.1 --port 1337 \
  --memory-guard-gb 27 --max-concurrent-requests 2 --hot-cache-max-size 2GB \
  --paged-ssd-cache-dir ~/.omlx/ssd-cache --paged-ssd-cache-max-size 60GB
```

`~/.omlx/model_settings.json`:

```json
{ "Qwen3.8-27B-AWQ-5.0bpw": { "turboquant_kv_enabled": true, "turboquant_kv_bits": 3.5, "mtp_enabled": true } }
```

`~/.omlx/settings.json`, the parts that matter: `memory_guard_custom_ceiling_gb: 27`, `soft_threshold: 0.85`, `prefill_priority: "context"`, `chunked_prefill: false`, `max_concurrent_requests: 2`, `burst_decode_mode: "balanced"`, `preserve_mid_system_cache: true`, `hot_cache_max_size: 2GB`, `ssd_cache_max_size: 60GB`, `max_context_window: 32768`, `temperature: 1.0`, `top_p: 0.95`.

Why 27 GB and not the default: oMLX derives the prefill cap as ceiling x soft_threshold. With 24 GB and an 18.8 GB model that left ~1.2 GB for the prefill working set; the scheduler does not refuse, it shrinks the chunk to 32 tokens and grinds (a 12.6k prompt took 23 minutes at 9 t/s). 27 GB puts the cap near 22.5 GB and stays under this Mac's Metal working-set limit (28.1 GB). Concurrency 2 instead of 8 because each in-flight request carries its own KV cache.

**What an agent does to those numbers.** I ran 80 scored coding-agent runs (harness: [OMP](https://github.com/can1357/oh-my-pi), a Pi fork; 8 seeded bugs in two real repos, plus multi-turn sessions) with a logging proxy in front of oMLX, so every number below is the server's own `usage` on 1,068 requests.

Generation falls with context size, because every token attends over the whole KV cache:

| context | generation, median |
|---|---:|
| 5-10k | 27.9 t/s |
| 10-15k | 24.3 |
| 15-20k | 21.5 |
| 20-25k | 20.4 |
| 25-30k | 19.8 |

Per agent preset (smaller system prompt = smaller context = faster):

| system prompt at the door | generation median / p90 | uncached prefill | prefix-cache hit | TTFT median |
|---|---:|---:|---:|---:|
| 22.6k (harness default) | 21.0 / 23.4 | 95 t/s | 90% | 23-26 s |
| 10.8k | 21.6 / 27.2 | 110 t/s | 85% | 19-21 s |
| 8.6k | 22.6 / 28.5 | 117 t/s | 84% | 19-20 s |
| 8.2k | 22.7 / 29.0 | 112 t/s | 87% | 15-19 s |

**Things I learned about running oMLX under an agent for ~22 hours:**

- Prefix cache works in 2,048-token pages. An agent turn re-prefills up to 2k tokens on top of the new content every request; that is the 84-90% hit rate above. Smaller pages would help agent workloads.
- Prefill capacity rejections: with the 27 GB guard, requests around 21-23k context got rejected or came back as HTTP 200 with an empty stream (no `usage`, no tokens). The harness read that as "the model said nothing". I had to add abort detection to the proxy to see it.
- Process bloat with uptime: after several hours the server process sat at ~24 GB resident + 18 GB compressed and rejections started at lower context. `launchctl kickstart -k` before each long batch fixed it. Restart on a schedule if you run batches.
- Anything else on the machine kills it. Docker Desktop's VM (~21 GB) pushed 10-16 GB into swap and the model dropped to ~1 t/s with aborted streams. Quit Docker, restart oMLX, rerun.
- The 22.6k default system prompt of the harness left ~7k of a 30k window for the actual work. I cut it to 5.9k in a fork (different post, [PR](PR_LINK)); on this machine that was the difference between "does not fit a real monorepo" and 7/8 bugs fixed.

**Repo.** Presets, scripts and every captured request: https://github.com/vinicius91carvalho/oh-my-pi/tree/local-model-eval

**How this was produced.** The harness fork, the benchmark, the runs and this post were done by Claude Fable 5 in Claude Code at high effort, with me setting goals and approving what ships. About two days, ~22 h of local model time.

**Caveats.** One machine, one model, one harness. A 128 GB Mac has no guard rejections and a bigger window; most of this is a 36 GB story.
