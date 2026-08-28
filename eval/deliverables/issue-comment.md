Measured the size problem and a fix, end to end, on a local model. Everything below is reproducible from the fork; numbers are the server's own `usage.prompt_tokens`, captured on the wire.

**Setup.** MacBook Pro M3 Max 14/30, 36 GB. oMLX 0.6.3rc3 serving Qwen3.8-27B-AWQ-5.0bpw (MTP on: 32 t/s decode on plain text, ~21 t/s inside agent runs; prefill 137 t/s cold), 30k context window. OMP 18.0.7. Real TypeScript pnpm monorepo with an `AGENTS.md`, a user-level rules file, one 21-tool MCP server.

**Where the 22,643 tokens go before the first user word.** Tool JSON schemas 11,734 (52%; `hub` alone 2,898), instruction template 6,160, user + project context files 3,981, MCP routes 401, misc 367. The harness's share (template + schemas) is 18.5k; the user's files are 3.9k.

**Why settings could not fix it.** `tools.xdev` already defers a schema to `read xd://<tool>`, but `isMountableUnderXdev()` only accepts `loadMode: "discoverable"`, and `ESSENTIAL_BUILTIN_TOOL_NAMES` + `XDEV_KEEP_TOP_LEVEL` cover 10 of the 11 tools. Extensions get `setActiveTools` but not `setActiveToolPresentation`: an expensive tool can be removed, never deferred.

**The change** (PR_LINK, five commits, defaults untouched, `promptProfile: full` renders byte-identical):
- `tools.xdevForceMount: [globs]` - named tools mount under `xd://` even when essential or pinned; `read`/`write` never demoted.
- `promptProfile: compact` - same rules and every generated surface (skills, rules, context files, inventory, devices), without the personality, examples and long prose.
- MCP catalog rows factored per server; compact profile names devices as `xd://grep`; `read xd://<tool>` ends with a worked call; a call literally named `xd://grep` resolves to the device.

| preset | `config.yml` | tools left top-level | moved to `xd://` (schema fetched on demand) | OMP's share: template + schemas | my context files | request total |
|---|---|---|---|---:|---:|---:|
| base (upstream default) | nothing | 11 | none | 18,531 | 3,923 | **22,643** |
| **p7k** | `promptProfile: compact` + `xdevForceMount: [hub, eval, task, todo, web_search]` | read bash edit glob grep write | hub eval task todo web_search | 6,787 | 3,923 | **10,838** |
| p5k | p7k + `edit, glob` | read bash grep write | + edit glob | 4,416 | 3,923 | **8,574** |
| p3k | p5k + `grep` | read bash write | + grep | 4,036 | 3,923 | **8,204** |
| p3k + my files compacted | same | same | same | 4,033 | 1,486 | **5,886** |

The preset name is OMP's own share, rounded. "Request total" is what the server counts before the first user word: OMP's share plus my `~/.omp/agent/AGENTS.md` and the project's `AGENTS.md` (3,923 tokens, untouched by the fork; the last row is me rewriting them densely with the detail moved to on-demand skills). All presets also need `tools.xdevDocs: catalog`, or the mounted tools' docs come back inline.

| preset | 12-task fixture | 8 real bugs, two rounds |
|---|---:|---:|
| base | 11/12 | 4/8, 5/8 |
| p7k | 11/12 | 7/8, 7/8 |
| p5k | 12/12 | 7/8, 6/8 |
| p3k | 12/12 | 7/8, 6/8 |

**How the bugs were tested.** Eight bugs seeded into two real repos (a TS pnpm monorepo with 1,488 files and a Python uv workspace with 910), one branch per bug, easy to very hard (very hard = a documented business rule broken, the covering test deleted, the agent must write it back; a hidden test is copied in at scoring time). Each bug was seen failing and passing with a reference fix before use. The agent runs headless (`omp -p --auto-approve --config <preset>`), 30-minute timeout, scored by the repo's own test command plus "did not edit tests". Two extra tasks for tooling: a rename across 8 files / 4 packages (passed in all presets) and a return-type contract change across 6 files / 4 packages (only p7k finished). Language servers were installed for round 2; no run in any preset ever called `lsp`.

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

**What the defaults lose is the machine, not reasoning.** With a 22k prompt every hard bug peaks at 27-39k tokens, where oMLX rejects or aborts the prefill on 36 GB; the same bugs peak at 13-27k on the compact presets. Long sessions (4 chained turns crossing the compaction threshold): compaction fires, the agent keeps calling tools and `xd://` devices afterwards; with `compaction.thresholdTokens: 20000` the p3k session completed fix + test (45/45 hidden cases).

**Caveats.** One machine, one 27B model, one harness version, single runs per cell. The one bug every preset failed is the model's (it fixes the reported case and not the documented rule). `omp compress` stalled on the local model; context files were compacted by hand.

Fork: https://github.com/vinicius91carvalho/oh-my-pi/tree/compact-prompt-for-local-models - benchmark scripts, presets and every captured request: https://github.com/vinicius91carvalho/oh-my-pi/tree/local-model-eval - write-up: REDDIT_LINK
