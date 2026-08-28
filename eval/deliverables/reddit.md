# Cut a coding agent's system prompt from 22.6k to 5.9k tokens for a 32k local model. Re-ran it on real TS + Python bugs: nothing broke.

**The issue.** [OMP (Oh My Pi)](https://github.com/can1357/oh-my-pi) sends 22,643 tokens before you type a word. 52% of that is JSON schemas for 11 tools; `hub` alone is 2,900 tokens. On a 30k window that leaves ~7k for the actual conversation. Open upstream issue: [#1734](https://github.com/can1357/oh-my-pi/issues/1734).

**The idea.** OMP already has lazy tool loading (`xd://` devices: the model fetches a schema on demand). It just refuses to apply it to the expensive tools, and the extension API cannot override that. Two settings fix it: `tools.xdevForceMount` (a glob list of tools to mount as devices) and `promptProfile: compact` (same rules, no prose). Nothing is removed; the model still uses `edit` via the device with zero schema in the request.

**Benchmark.** M3 Max 36 GB, oMLX + Qwen3.8-27B AWQ 5bpw with MTP (32 t/s decode, 137 t/s prefill), 30k window. Tokens are the server's own `usage.prompt_tokens`.

| mode | tools top-level | first prompt (real monorepo) | 12 fixture tasks | 8 real bugs, round 1 -> 2 |
|---|---|---:|---:|---:|
| upstream default | 11 | 22,643 | 11/12 | 4/8 -> 5/8 |
| p7k | 6 | 10,838 | 11/12 | 7/8 -> 7/8 |
| p5k | 4 | 8,574 | 12/12 | 7/8 -> 6/8 |
| p3k | 3 | 8,204 | 12/12 | 7/8 -> 6/8 |

Two rounds (second one with language servers installed and a fourth commit). Extra: p7k was the only mode to finish a 4-package contract change; rename across 8 files passed in all modes; the default mode gets its hard bugs rejected by the server at 27-39k tokens. 4-turn sessions crossing the compaction threshold: p7k kept working 47 requests after compaction and fixed 43/44 hidden cases.

**Repo.** Fork + branch: https://github.com/vinicius91carvalho/oh-my-pi/tree/compact-prompt-for-local-models. Benchmark scripts, profiles and every captured request: https://github.com/vinicius91carvalho/oh-my-pi/tree/local-model-eval

**PR.** PR_LINK (one PR, three commits, tests included, `promptProfile: full` renders byte-identical to upstream). Whether it lands or not, you can run the branch today.
