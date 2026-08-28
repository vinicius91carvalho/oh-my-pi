Measured the problem and a fix end to end on a local model; https://github.com/can1357/oh-my-pi/pull/10077 has the change, https://github.com/vinicius91carvalho/oh-my-pi/tree/local-model-eval has the scripts and every captured request.

**Why.** Local-only setup: M3 Max 36 GB, Qwen3.8-27B on oMLX (11 t/s on llama-server -> 17 on oMLX -> 32 with MTP + memory-guard/KV tuning), usable window ~32k and no truncation server-side. OMP is my harness because of what it adds to Pi (31 tools with `xd://`, `hub`, LSP/DAP, subagents, skills/rules, memory); that breadth is what the 22.6k-token door costs, and `xd://` is the mechanism that can pay for it if it is opened to the expensive tools.

**Where the 22,643 tokens go** (18.0.7 defaults, real TS monorepo, one 21-tool MCP server, server `usage.prompt_tokens`): tool JSON schemas 11,734 (52%; `hub` 2,898), instruction template 6,160, the user's context files 3,981, MCP routes 401, misc 367. Harness share 18.5k, user share 3.9k.

**Why settings could not fix it.** `tools.xdev` defers a schema to `read xd://<tool>`, but `isMountableUnderXdev()` only accepts `loadMode: "discoverable"`, and `ESSENTIAL_BUILTIN_TOOL_NAMES` + `XDEV_KEEP_TOP_LEVEL` cover 10 of the 11 tools. `setActiveTools` exists, `setActiveToolPresentation` does not: from outside the source an expensive tool can be removed, never deferred.

**The change.** Two opt-in settings; `promptProfile: full` renders byte-identical.

```yaml
promptProfile: compact
tools:
  xdevDocs: catalog
  xdevForceMount: [hub, eval, task, todo, web_search]
```

| preset | `config.yml` | tools left top-level | moved to `xd://` (schema fetched on demand) | OMP's share: template + schemas | my context files | request total |
|---|---|---|---|---:|---:|---:|
| base (upstream default) | nothing | 11 | none | 18,531 | 3,923 | **22,643** |
| **p7k** | `promptProfile: compact` + `xdevForceMount: [hub, eval, task, todo, web_search]` | read bash edit glob grep write | hub eval task todo web_search | 6,787 | 3,923 | **10,838** |
| p5k | p7k + `edit, glob` | read bash grep write | + edit glob | 4,416 | 3,923 | **8,574** |
| p3k | p5k + `grep` | read bash write | + grep | 4,036 | 3,923 | **8,204** |
| p3k + my files compacted | same | same | same | 4,033 | 1,486 | **5,886** |

The preset name is OMP's own share, rounded. "Request total" is what the server counts before the first user word: OMP's share plus my `~/.omp/agent/AGENTS.md` and the project's `AGENTS.md` (3,923 tokens, untouched by the fork; the last row is me rewriting them densely with the detail moved to on-demand skills). All presets also need `tools.xdevDocs: catalog`, or the mounted tools' docs come back inline.

**How it was tested.** M3 Max 14/30, 36 GB; oMLX 0.6.3rc3, Qwen3.8-27B-AWQ-5.0bpw, MTP on, 30k window. (1) A 12-task fixture on a 5-file repo, scored by shell checks. (2) Eight bugs seeded into two real repos (TS pnpm monorepo, 1,488 files; Python uv workspace, 910 files), each seen failing and passing with a reference fix first; the agent runs headless with `-p --auto-approve --config <preset>`, 30-minute cap, scored by the repo's own tests plus "did not edit tests"; two rounds, plus a rename across 8 files and a return-type change across 6 files, plus 4-turn sessions across the compaction threshold. (3) Speed from the server's usage on 1,068 requests.

| preset | fixture | 8 real bugs, round 1 -> 2 | rename / contract | 4-turn session |
|---|---:|---:|---:|---|
| base | 11/12 | 4/8 -> 5/8 | 1/2 | not run |
| p7k | 11/12 | 7/8 -> 7/8 | 2/2 | 27k threshold: 43/44; 20k threshold: fix + test, 44/44 |
| p5k | 12/12 | 7/8 -> 6/8 | 1/2 | - |
| p3k | 12/12 | 7/8 -> 6/8 | 1/2 | 20k threshold: fix + test, 45/45 |

| level (2 bugs each, TS + Python) | base | p7k | p5k | p3k |
|---|---|---|---|---|
| easy: 1 line, test names the file | 4/4, 8 min | 4/4, 5 min | 4/4, 4 min | 4/4, 4 min |
| medium: bug in one package, test in another | 4/4, 5 min | 4/4, 4 min | 4/4, 5 min | 4/4, 18 min |
| hard: cause far from symptom, error never names the file | 1/4, rejected by server | 4/4, 8 min | 4/4, 9 min | 4/4, 7 min |
| very hard: documented rule broken, covering test deleted, hidden test at scoring | 0/4 | 2/4, 29 min | 1/4, 20 min | 1/4, 22 min |
| LSP: rename across 8 files / contract change across 6 files | 1/2 | 2/2, 22 min | 1/2, 20 min | 1/2, 12 min |

Times are medians per run (30-minute cap). Speed inside the runs, server-reported over 1,068 requests: generation 28 t/s at 5-10k context falling to 20 t/s at 20-25k (the 32 t/s bench is a 69-token prompt); uncached prefill 95 t/s (base) to 110-118 t/s (compact); prefix-cache hit 84-91%.

The one bug no preset solved (8/8 runs, same diff): a docs rule says the landing-page persona may never claim years of experience; the report showed "12 anos de experiência" slipping through; every run widened the regex for the accent, kept the `\d+` (a number required), wrote a test for the reported sentence, and stopped. The hidden test's "anos de experiencia" without a number still passes validation. Symptom fixed, rule not read: the model, not the prompt size.

**What the defaults lose is the machine.** With a 22k prompt every hard bug peaks at 27-39k tokens, where oMLX rejects or aborts the prefill on 36 GB; the same bugs peak at 13-27k on the compact presets. `xd://` devices work: `edit` through `xd://edit` 22/22 in round 2; language servers installed and listed, never called by this model.

**How this was produced.** Fork, harness, seeded bugs, runs and text by Claude Fable 5 (Claude Code, high effort) under human direction; ~2 days wall clock, 80 scored runs, ~22 h of local model time, 1,486 captured requests.

**Caveats.** One machine, one 27B model, one run per cell. `omp compress` stalled on the local model; the context files were compacted by hand.
