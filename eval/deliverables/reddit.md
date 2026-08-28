# Cut a coding agent's system prompt from 22.6k to 5.9k tokens for a 32k local model, then made it prove itself on real TS + Python bugs

**Why.** I wanted a coding agent on my own laptop (M3 Max, 36 GB, no cloud). Qwen3.8-27B ran at ~11 t/s on `llama-server`; oMLX took it to 17 t/s (the bandwidth limit), and raising its memory guard, 3.5-bit TurboQuant KV and MTP took it to 32 t/s with prefill at 137 t/s. The usable window here is ~32k, and oMLX does not truncate: over the window is HTTP 400. For the harness I picked OMP over plain Pi because it adds what a real project needs on top of Pi's clean core (31 tools with `xd://` lazy loading, `hub` for MCP, LSP/DAP, subagents, skills, rules, memory), and that breadth is exactly what costs 22.6k tokens at the door. The idea worth sharing: OMP already has on-demand tool loading; open it to the expensive tools, keep everything reachable, measure on real bugs.

**The issue.** [OMP (Oh My Pi)](https://github.com/can1357/oh-my-pi) 18.0.7 sends **22,643 tokens** before you type a word, measured on the wire against my local server inside a real TypeScript monorepo. Where it goes: JSON schemas of the 11 top-level tools 11,734 (52%; `hub` alone 2,898), instruction template 6,160, my own context files 3,981, MCP routes 401, misc 367. On a 30k window that leaves ~7k for the actual conversation. Upstream issue: [#1734](https://github.com/can1357/oh-my-pi/issues/1734).

**Why config alone cannot fix it.** OMP already has lazy tool loading: a tool mounted under `xd://` ships no schema, the model runs `read xd://<tool>` when it needs it. But `isMountableUnderXdev()` only accepts tools declared `discoverable`, and `ESSENTIAL_BUILTIN_TOOL_NAMES` + `XDEV_KEEP_TOP_LEVEL` pin 10 of the 11. Extensions get `setActiveTools` but not `setActiveToolPresentation`: from outside the source an expensive tool can be removed, never deferred.

**The change: two settings, off by default.**

```yaml
promptProfile: compact            # same rules, same generated surfaces, no personality/examples/long prose
tools:
  xdevDocs: catalog
  xdevForceMount: [hub, eval, task, todo, web_search]   # any glob; read/write can never be demoted
```

`promptProfile: full` still renders byte-identical to upstream. Three presets of the list, measured with the model's tokenizer on the captured request:

| preset | `config.yml` | tools left top-level | moved to `xd://` (schema fetched on demand) | OMP's share: template + schemas | my context files | request total |
|---|---|---|---|---:|---:|---:|
| base (upstream default) | nothing | 11 | none | 18,531 | 3,923 | **22,643** |
| **p7k** | `promptProfile: compact` + `xdevForceMount: [hub, eval, task, todo, web_search]` | read bash edit glob grep write | hub eval task todo web_search | 6,787 | 3,923 | **10,838** |
| p5k | p7k + `edit, glob` | read bash grep write | + edit glob | 4,416 | 3,923 | **8,574** |
| p3k | p5k + `grep` | read bash write | + grep | 4,036 | 3,923 | **8,204** |
| p3k + my files compacted | same | same | same | 4,033 | 1,486 | **5,886** |

The preset name is OMP's own share, rounded. "Request total" is what the server counts before the first user word: OMP's share plus my `~/.omp/agent/AGENTS.md` and the project's `AGENTS.md` (3,923 tokens, untouched by the fork; the last row is me rewriting them densely with the detail moved to on-demand skills). All presets also need `tools.xdevDocs: catalog`, or the mounted tools' docs come back inline.

**How I tested it.** MacBook Pro M3 Max 14/30, 36 GB. oMLX 0.6.3rc3 serving Qwen3.8-27B-AWQ-5.0bpw (MTP on), 30k window. Every token count is the server's `usage.prompt_tokens`, captured by a logging proxy. Three tests:

1. *Fixture*: a 5-file JS repo, 12 short tasks (pick the right tool, edit the right place, run tests, stop, ask instead of inventing), scored by shell checks.
2. *Real bugs*: 8 bugs seeded into two real repos (a TS pnpm monorepo, 1,488 files; a Python uv workspace, 910 files), one branch each, each one seen failing and passing with a reference fix first. The agent runs headless (`omp -p --auto-approve --config <preset>`), 30-minute cap, scored by the repo's own tests plus "did not edit the tests". Two rounds; round 2 adds a 4th commit and two tooling tasks (rename across 8 files, return-type change across 6 files). Plus 4-turn sessions that cross the compaction threshold.
3. *Speed*: generation, prefill and cache hit from the server's usage on 1,068 requests.

**Results.**

| preset | fixture | 8 real bugs, round 1 -> 2 | rename / contract | 4-turn session |
|---|---:|---:|---:|---|
| base | 11/12 | 4/8 -> 5/8 | 1/2 | not run (does not fit) |
| **p7k** | 11/12 | **7/8 -> 7/8** | **2/2** | fix + test after compaction, 43/44 hidden cases |
| p5k | 12/12 | 7/8 -> 6/8 | 1/2 | - |
| p3k | 12/12 | 7/8 -> 6/8 | 1/2 | with a 20k compaction threshold: fix + test, 45/45 |

| level (2 bugs each, TS + Python) | base | p7k | p5k | p3k |
|---|---|---|---|---|
| easy: 1 line, test names the file | 4/4, 8 min | 4/4, 5 min | 4/4, 4 min | 4/4, 4 min |
| medium: bug in one package, test in another | 4/4, 5 min | 4/4, 4 min | 4/4, 5 min | 4/4, 18 min |
| hard: cause far from symptom, error never names the file | 1/4, rejected by server | 4/4, 8 min | 4/4, 9 min | 4/4, 7 min |
| very hard: documented rule broken, covering test deleted, hidden test at scoring | 0/4 | 2/4, 29 min | 1/4, 20 min | 1/4, 22 min |
| LSP: rename across 8 files / contract change across 6 files | 1/2 | 2/2, 22 min | 1/2, 20 min | 1/2, 12 min |

Times are medians per run (30-minute cap). Speed inside the runs, server-reported over 1,068 requests: generation 28 t/s at 5-10k context falling to 20 t/s at 20-25k (the 32 t/s bench is a 69-token prompt); uncached prefill 95 t/s (base) to 110-118 t/s (compact); prefix-cache hit 84-91%.

The one bug no preset solved (8/8 runs, same diff): a docs rule says the landing-page persona may never claim years of experience; the report showed "12 anos de experiência" slipping through; every run widened the regex for the accent, kept the `\d+` (a number required), wrote a test for the reported sentence, and stopped. The hidden test's "anos de experiencia" without a number still passes validation. Symptom fixed, rule not read: the model, not the prompt size.

**Same tools, different path.** Nothing is removed. With `edit` mounted, p5k/p3k fetched `xd://edit` and edited through it 22/22 times in round 2. Language servers were installed for round 2 and `xd://lsp` was listed in every preset; no run ever called it: this model does rename with grep + edit.

**Repo.** Fork + branch: https://github.com/vinicius91carvalho/oh-my-pi/tree/compact-prompt-for-local-models. Scripts, presets, and every captured request: https://github.com/vinicius91carvalho/oh-my-pi/tree/local-model-eval

**PR.** PR_LINK - five commits with tests. Whether it lands or not, the branch runs today.

**How this was produced.** Everything here (fork, harness, seeded bugs, runs, this post) was done by Claude Fable 5 in Claude Code at high effort, with me setting the goals, taking the calls and approving what ships. About two days wall clock, 80 scored runs, ~22 h of local model time, 1,486 captured requests, on the same laptop that was shipping deploys in another session.

**Caveats.** One machine, one 27B, one harness version, one run per cell (two rounds). Tuned on 36 GB; a 128 GB Mac has no memory-guard rejections and less to gain. `omp compress` (the harness's own context-file compressor) stalled on the local model; I compacted my files by hand.
