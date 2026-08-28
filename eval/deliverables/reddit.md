# Cut a coding agent's system prompt from 22.6k to 5.9k tokens for a 32k local model. Re-ran it on real TS + Python bugs: nothing broke.

**The issue.** [OMP (Oh My Pi)](https://github.com/can1357/oh-my-pi) sends 22,643 tokens before you type a word. 52% of that is JSON schemas for 11 tools; `hub` alone is 2,900 tokens. On a 30k window that leaves ~7k for the actual conversation. Open upstream issue: [#1734](https://github.com/can1357/oh-my-pi/issues/1734).

**The idea.** OMP already has lazy tool loading (`xd://` devices: the model fetches a schema on demand). It just refuses to apply it to the expensive tools, and the extension API cannot override that. Two settings fix it: `tools.xdevForceMount` (a glob list of tools to mount as devices) and `promptProfile: compact` (same rules, no prose). Nothing is removed; the model still uses `edit` via the device with zero schema in the request.

**Benchmark.** Request total = harness share (template + tool schemas, what the fork shrinks) + my own context files (3.9k, untouched). M3 Max 36 GB, oMLX + Qwen3.8-27B AWQ 5bpw with MTP (32 t/s decode, 137 t/s prefill), 30k window. Tokens are the server's own `usage.prompt_tokens`.

| preset (harness share) | tools top-level | request total (real monorepo) | 12 fixture tasks | 8 real bugs, round 1 -> 2 |
|---|---|---:|---:|---:|
| upstream default (18.5k) | 11 | 22,643 | 11/12 | 4/8 -> 5/8 |
| p7k (6.8k) | 6 | 10,838 | 11/12 | 7/8 -> 7/8 |
| p5k (4.4k) | 4 | 8,574 | 12/12 | 7/8 -> 6/8 |
| p3k (4.0k) | 3 | 8,204 | 12/12 | 7/8 -> 6/8 |

Two rounds (second one with language servers installed and a fourth commit). Extra: p7k was the only mode to finish a 4-package contract change; rename across 8 files passed in all modes; the default mode gets its hard bugs rejected by the server at 27-39k tokens. 4-turn sessions crossing the compaction threshold: p7k kept working 47 requests after compaction and fixed 43/44 hidden cases.

**By difficulty, both rounds.**

| level (2 bugs each, TS + Python) | base | p7k | p5k | p3k |
|---|---|---|---|---|
| easy: 1 line, test names the file | 4/4, 8 min | 4/4, 5 min | 4/4, 4 min | 4/4, 4 min |
| medium: bug in one package, test in another | 4/4, 5 min | 4/4, 4 min | 4/4, 5 min | 4/4, 18 min |
| hard: cause far from symptom, error never names the file | 1/4, rejected by server | 4/4, 8 min | 4/4, 9 min | 4/4, 7 min |
| very hard: documented rule broken, covering test deleted, hidden test at scoring | 0/4 | 2/4, 29 min | 1/4, 20 min | 1/4, 22 min |
| LSP: rename across 8 files / contract change across 6 files | 1/2 | 2/2, 22 min | 1/2, 20 min | 1/2, 12 min |

Times are medians per run (30-minute cap). Speed inside the runs, server-reported over 1,068 requests: generation 28 t/s at 5-10k context falling to 20 t/s at 20-25k (the 32 t/s bench is a 69-token prompt); uncached prefill 95 t/s (base) to 110-118 t/s (compact); prefix-cache hit 84-91%.

The one bug no preset solved (8/8 runs, same diff): a docs rule says the landing-page persona may never claim years of experience; the report showed "12 anos de experiência" slipping through; every run widened the regex for the accent, kept the `\d+` (a number required), wrote a test for the reported sentence, and stopped. The hidden test's "anos de experiencia" without a number still passes validation. Symptom fixed, rule not read: the model, not the prompt size.

**Repo.** Fork + branch: https://github.com/vinicius91carvalho/oh-my-pi/tree/compact-prompt-for-local-models. Benchmark scripts, profiles and every captured request: https://github.com/vinicius91carvalho/oh-my-pi/tree/local-model-eval

**PR.** PR_LINK (one PR, three commits, tests included, `promptProfile: full` renders byte-identical to upstream). Whether it lands or not, you can run the branch today.
