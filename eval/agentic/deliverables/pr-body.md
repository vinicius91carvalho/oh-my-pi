## feat: let local models fit: `tools.xdevForceMount` + `promptProfile: compact`

Refs #1734. Five commits, each self-contained; defaults are untouched and `promptProfile: full` renders byte-identical (33,440 bytes both sides).

### Why this, in short

I wanted a coding agent that runs on my own laptop: a MacBook Pro M3 Max with 36 GB, no cloud. The road to get there is most of why the prompt size matters:

1. **Serving.** Qwen3.8-27B (AWQ 5 bpw, 17.4 GB) ran at ~11 t/s on `llama-server`. Switching to oMLX (Apple Silicon, continuous batching, SSD prefix cache) gave 17-18 t/s, which is exactly the memory-bandwidth limit (300 GB/s / 17.4 GB). Raising oMLX's memory guard from 24 to 27 GB fixed prefill (9 -> 137 t/s cold; the bottleneck was the prefill scratch at ~10 MB/token, not the KV cache), TurboQuant 3.5-bit KV bought headroom, and enabling MTP (the checkpoint ships a draft head, 88% acceptance) took decode to 32 t/s. ANE offload loses on 36 GB.
2. **The window.** On this machine the usable context is ~32k: 33k tokens peak at 24.7 GB, 64k does not fit, and oMLX does not truncate (over the window is HTTP 400). Every token the harness spends before I type is gone for good.
3. **The harness.** Pi is the minimal, clean core: agent loop, read/write/edit/bash, sessions, compaction, extensions. OMP builds on it and adds the things a real project needs: 31 tools in one namespace with `xd://` devices (lazy loading built in), `hub` for MCP servers, LSP and a debugger, subagents in worktrees, skills and rules, memory, stream rules. That breadth is what I want, and it is also what costs 22.6k tokens at the door, because ten of the eleven default tools cannot use the lazy path.

So the interesting idea is not "shorter prompt". It is: OMP already has on-demand tool loading; open it to the tools that are expensive, keep everything reachable, and measure on real bugs whether a 27B model still does the job. It does.

### The problem, measured

18.0.7 sends **22,643 tokens** before the first user word, measured on the wire against a local oMLX server inside a real TypeScript monorepo with an `AGENTS.md`, a user rules file and one 21-tool MCP server. JSON schemas of the 11 top-level tools 11,734 (52%; `hub` alone 2,898), instruction template 6,160, the user's own context files 3,981, MCP routes 401, misc 367. On a 30k window that leaves ~7k for the conversation.

`tools.xdev` already defers a schema to `read xd://<tool>`, but `isMountableUnderXdev()` only accepts `loadMode: "discoverable"`, and `ESSENTIAL_BUILTIN_TOOL_NAMES` + `XDEV_KEEP_TOP_LEVEL` cover 10 of the 11. Extensions get `setActiveTools` but not `setActiveToolPresentation`: an expensive tool can be removed, never deferred.

### What

| commit | setting | effect |
|---|---|---|
| `feat(tools): add tools.xdevForceMount` | `tools.xdevForceMount: [globs]`, default `[]` | named tools mount under `xd://` even when essential/pinned. `read`/`write` are never demoted (transport). Forcing a `XDEV_KEEP_TOP_LEVEL` name is allowed and documented as a trade-off |
| `feat(prompt): add promptProfile` | `promptProfile: full \| compact`, default `full` | `full` renders byte-identical (33,440 bytes both sides). `compact` keeps the authority/safety contract, tool mapping, stop/ask/verify, edit-and-test loop, `xd://` protocol, and every generated surface (skills, rules, context files, inventory, devices); drops personality, examples, URL catalog, long workflow prose. Instruction block 7,412 -> 6,222 tokens on the same session |
| `fix(prompt): name devices as xd:// paths, show a device call, factor MCP catalog rows` | none | compact profile references a mounted tool as `xd://grep` (a 27B model called `grep` by name otherwise); `read xd://<tool>` ends with one worked `write(...)` call (a model spent 25 min escaping a patch without it); MCP catalog row factors the shared prefix |
| `fix(tools): accept xd://<tool> as a fallback tool-call name` | none | a call literally named `xd://grep` lands on the mounted `grep` device instead of "Tool not found" |
| `perf(prompt): stop enumerating every mounted MCP tool` | none | route block states the naming rule once per server when `createMCPToolName` reproduces every live name; catalog groups a server's tools in one row. `## MCP Tool Routes` 1,222 -> 551 tokens with one 21-tool server |

### Who puts what in the prompt

Every request starts with a system prompt. Two parties write it:

- **OMP (the harness)**: the instruction template + one JSON schema per top-level tool. This is what the fork shrinks. The preset name (p7k, p5k, p3k) is this share, rounded.
- **You**: `~/.omp/agent/AGENTS.md` (your rules) and the project's `.omp/AGENTS.md`/`AGENTS.md`, plus MCP server instructions. The fork does not touch these; you can shrink them yourself (I did: 3,923 -> 1,486 tokens by moving detail into on-demand skills).

Tokens counted with the model's tokenizer on the captured request (server counts run ~5% higher):

| preset | OMP template | OMP tool schemas | **OMP total** | your context files | MCP block | **request total** |
|---|---:|---:|---:|---:|---:|---:|
| base | 6,503 | 12,028 | **18,531** | 3,923 | 78 | 22,532 |
| p7k | 2,095 | 4,692 | **6,787** | 3,923 | 78 | 10,788 |
| p5k | 2,131 | 2,285 | **4,416** | 3,923 | 78 | 8,417 |
| p3k | 2,141 | 1,895 | **4,036** | 3,923 | 78 | 8,037 |
| p3k + compacted context files | 2,138 | 1,895 | **4,033** | 1,486 | 78 | 5,597 |

### Tools per preset

| preset | top-level (schema in every request) | mounted in `xd://` (fetched on demand) | request total, real TS monorepo (server count) | small repo |
|---|---|---|---|---:|
| **base** (upstream default) | read bash edit eval glob grep task hub todo web_search write | none | 22,320 | 19,278 |
| **p7k** | read bash edit glob grep write | hub eval task todo web_search | 10,838 | 7,888 |
| **p5k** | read bash grep write | + edit glob | 8,574 | 5,624 |
| **p3k** | read bash write | + grep | 8,204 (5,802 with commit 4) | 5,254 |

Nothing is removed in any mode. Every tool still works; the probe "edit a file using the mounted `edit` device" passes on p3k with zero `edit` schema in the request. `ask` and MCP tools follow the same rule.

The tool schema cost that drives this: `hub` 2,898 tokens, `edit` 1,793, `todo` 1,364, `task` 1,258, `eval` 1,185, `read` 1,077, `bash` 679, `glob` 483, `grep` 360, `web_search` 343, `write` 294.

### Config (`~/.omp/agent/config.yml` or project `.omp/config.yml`)

```yaml
# p7k - daily default
promptProfile: compact
personality: none
includeModelInPrompt: false
tools:
  xdevDocs: catalog
  xdevForceMount: [hub, eval, task, todo, web_search]
```

p5k: add `edit, glob` to the list. p3k: add `grep` too.

### Which preset, day to day (measured, see Benchmark below)

| situation | mode | why |
|---|---|---|
| 32k window, daily coding | **p7k** | 7/8 real bugs in both rounds (default: 4-5/8), native `edit`/`grep`, the only mode that finished a 4-package contract change, and the only one whose 4-turn session fixed the bug after compaction |
| 32k window + MCP servers or a big `AGENTS.md` | p5k | 2.3k more tokens freed; `edit` via device worked 22/22 times, but costs one `read xd://edit` per session and 6-7/8 on the bugs |
| absolute floor | p3k | 6-7/8; only 370 tokens below p5k and the model sometimes calls `xd://grep` as a tool name |
| 64k+ window | base or p7k | the cut still shortens prefill (137 t/s here: 12k tokens = 90 s) and keeps you under the memory ceiling |

Two things not to bother with on a 27B local model: the `lsp` device (installed servers, listed in every mode, never called once in 40 runs) and `read.defaultLimit` tuning (the model reads whole files anyway; it is the prompt rule that matters).

Compaction on 36 GB: set `compaction.thresholdTokens: 20000`, not 27000. Single turns overshoot by 10-15k (compaction only runs between turns) and the server aborts above ~25k once it has been up for hours; restart oMLX before a long session.

Context files count too: `~/.omp/agent/AGENTS.md` dense (1,010 tokens) + on-demand skills instead of a 1,875-token rulebook saved 2,437 tokens per request on top of the table above.

### Compaction (long sessions)

Compaction is untouched by the fork and fires on the same setting (`compaction.thresholdTokens`, here 27,000 of 30,000). The modes only change how much room is left before it fires: base has ~7.7k tokens of conversation before compaction, p7k ~19k, p3k ~22k. See "Long sessions" below for the measured runs.

## Benchmark

### Machine and server

| item | value |
|---|---|
| MacBook Pro M3 Max 14/30, 36 GB, 300 GB/s | oMLX 0.6.3rc3, launchd `org.nix-community.home.omlx`, port 1337 |
| model | `Qwen3.8-27B-AWQ-5.0bpw` (17.4 GB resident, MTP head in the checkpoint) |
| oMLX config | `mtp_enabled` on, `turboquant_kv_bits 3.5`, no ANE, `--memory-guard-gb 27`, SSD paged cache |
| decode | **32.2 t/s** with MTP on the plain-text bench (`eval/results-B3-mtp.json`), 17.2-17.9 t/s without it; **18-27 t/s (median ~21) inside agent runs**, where MTP accepts fewer drafts on tool-call JSON |
| prefill | 137 t/s cold at 12k tokens (TTFT 92 s); 4,143 t/s when the SSD cache hits (TTFT 3 s) |
| usable window | 30,000 tokens set in `models.yml`; ~32k is the memory ceiling (peak 24.7 GB), 64k does not fit. oMLX has no truncation: over the window = HTTP 400 |
| harness | OMP 18.0.7 fork, `bun 1.4.0`, tokens = server `usage.prompt_tokens` via a logging proxy (`tap.py`) |

### Prompt size ladder (real TS monorepo, `AGENTS.md` + user file + one 21-tool MCP server)

Server `usage.prompt_tokens` for the whole request. Of these, the user's own context files are 3,923 tokens in every row until the last one (1,486 after compaction); the rest is OMP's template + tool schemas. See "Who puts what in the prompt" above for the split per preset.

| step | prompt tokens | tool schemas | rest |
|---|---:|---:|---:|
| upstream 18.0.7, defaults | 22,643 | 11,734 | 10,909 |
| + settings that already exist (xdevDocs catalog, personality none, no model line) | 19,058 | 11,734 | 7,324 |
| + promptProfile compact | 17,868 | 11,734 | 6,134 |
| + xdevForceMount, 6 tools top-level (p7k) | 10,838 | 4,660 | 6,178 |
| + 4 tools top-level (p5k) | 8,574 | 2,360 | 6,214 |
| + 3 tools top-level (p3k) | 8,204 | 1,980 | 6,224 |
| + context files compacted into on-demand skills | **5,886** | 1,980 | 3,906 |

**22,643 -> 5,886, 3.85x.**

### Fixture: 12 agentic tasks, small JS repo with one failing test

Scored by shell checks (tests pass, file exists, tree clean, answer matches), not by reading the answer.

| mode | prompt tokens | passed | median s | failure |
|---|---:|---:|---:|---|
| base | 19,278 | 11/12 | 171 | ask-01: stopped mid-work |
| p7k | 7,888 | 11/12 | 152 | ask-01: invented a rate without saying so |
| p5k | 5,624 | 12/12 | 148 | - |
| p3k | 5,254 | 12/12 | 119 | - |

Extra probes, base vs p3k: `xd://` protocol 3/3 both; grounding (no invented sources) 6/6 both.

### Real projects: 8 seeded bugs, 4 presets

Worktrees of two real repos: `find-best-job` (TypeScript pnpm monorepo, 1,488 TS files) and `infoproduct` (Python uv workspace, 910 files). One branch per bug. Every bug was seen failing and then passing with a reference fix before use. Pass = project's own test command green and no test file touched (very hard: the agent must also write a test; a hidden test is copied in at scoring time).

| bug | level | what the agent has to do |
|---|---|---|
| ts-easy | easy | one `.trim()` in `packages/core/src/timezone.ts`; the failing test names the file |
| ts-medium | medium | `salaryMin ?? salaryMax` swapped in `packages/llm`; the failing test is in `packages/pipeline` |
| ts-hard | hard | host regex in `packages/core/posting-identity.ts` lost `job-boards.`; symptom is "unknown" in a pipeline test that never names the file |
| ts-veryhard | very hard | `AGENTS.md` rule "legal-status questions get the negative": function answers "yes" with no evidence; visible tests all pass; must write the test |
| py-easy | easy | `<=` vs `<` in `research/scoring.py` |
| py-medium | medium | pt-BR thousands separator in `landing_gen/locales.py`, test in another module |
| py-hard | hard | `CAROUSEL_CARDS_MAX = 5` in `campaign/models.py`; 16 pydantic errors elsewhere |
| py-veryhard | very hard | `docs/decisions.md` D07: Portuguese "anos de experiencia" claim must be blocked; only Spanish is; must write the test |

#### Difficulty levels

| level | definition | time budget the level implies |
|---|---|---|
| easy | one line in one file; the failing test names the file | read the test, read the file, one edit, run tests: minutes |
| medium | bug in one module, failing test in another package; the agent must follow the call chain | plus a grep or two and a rebuild of the touched package |
| hard | symptom far from cause (a wrong constant or regex in a shared module; the error never names the culprit file) | plus real investigation across packages |
| very hard | a documented business rule is broken and the test that would catch it was deleted; the report describes one symptom; the agent must find the rule in the docs, fix it fully, and write the test back; a hidden test with more cases is copied in at scoring | plus reading docs, writing tests, and getting the rule right, not just the symptom |
| LSP | rename an exported symbol used in 4 packages (8 files) / change a function's return type and propagate it to 4 packages (6 files) | plus rebuilding packages so cross-package `tsc` and vitest pass |

#### Pass rate and time per level (both rounds together, 4 runs per cell; LSP tasks are round 2 only)

| level | base | p7k | p5k | p3k |
|---|---|---|---|---|
| easy | 4/4, 8 min median (6-12) | 4/4, 5 min (2-6) | 4/4, 4 min (4-6) | 4/4, 4 min (2-6) |
| medium | 4/4, 5 min (4-14) | 4/4, 4 min (3-5) | 4/4, 5 min (5-7) | 4/4, 18 min (9-30)* |
| hard | 1/4, 4 min (0-14)** | 4/4, 8 min (4-20) | 4/4, 9 min (4-30) | 4/4, 7 min (4-17) |
| very hard | 0/4, 13 min (2-30) | 2/4, 29 min (11-30) | 1/4, 20 min (7-30) | 1/4, 22 min (13-30) |
| LSP (rename / contract) | 1/2, 19 min (16-22) | 2/2, 22 min (15-30) | 1/2, 20 min (10-30) | 1/2, 12 min (10-15) |

\* p3k medium: one 30-minute run was the `xd://edit` escaping loop (fixed by commit 4); the other was 16 min of the agent saving notes to Basic Memory as the user's rules ask.
\*\* base hard: "4 min" is misleading: 3 of the 4 runs ended in 0-5 minutes because the server rejected the prompt, not because the agent was fast.

Reading: easy and medium are solved by every preset; the presets differ in time, not in outcome. Hard is where the default breaks (the machine rejects its 21-31k contexts). Very hard is where the 30-minute budget breaks: every preset finds the fix on ts-veryhard, and writing the extra test on top is what runs out the clock. The one bug no preset solved is below.

Round 1 = fork commits 1-3, no language server installed. Round 2 = + commit 4 (xd:// references, device-call example, factored MCP rows), `typescript-language-server` and `pyright` installed, 2 extra LSP-shaped tasks. Timeout 30 min per task. `+Nab` = N streams the oMLX memory guard aborted mid-run (the agent recovers or not).

| bug | base r1 | base r2 | p7k r1 | p7k r2 | p5k r1 | p5k r2 | p3k r1 | p3k r2 |
|---|---|---|---|---|---|---|---|---|
| py-easy | pass 12m | pass 8m | pass 6m | pass 5m | pass 4m | pass 5m | pass 3m | pass 6m |
| py-medium | pass 4m | pass 5m | pass 5m | pass 3m | pass 5m | pass 5m | pass 30m* | pass 16m |
| py-hard | FAIL (server rejected prefill at 21k) | pass 4m | pass 4m | pass 5m | pass 4m | pass 5m | pass 5m | pass 4m |
| py-veryhard | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL |
| ts-easy | pass 6m | pass 8m | pass 2m | pass 6m | pass 4m | pass 6m | pass 2m | pass 4m |
| ts-medium | pass 14m | pass 5m | pass 5m | pass 4m | pass 7m | pass 6m | pass 19m | pass 9m |
| ts-hard | FAIL (rejected at 21k) | FAIL (2 aborts at 31k) | pass 20m | pass 11m | pass 30m | pass 12m | pass 8m | pass 17m |
| ts-veryhard | FAIL (39.5k, timeout) | FAIL (abort at 28k) | pass 30m | pass 30m | pass 30m | FAIL 30m | pass 30m | FAIL 30m |
| **8 bugs** | **4/8** | **5/8** | **7/8** | **7/8** | **7/8** | **6/8** | **7/8** | **6/8** |
| minutes, 8 bugs | 85 | 58 | 83 | 92 | 91 | 80 | 110 | 101 |
| ts-rename (8 files, 4 packages) | - | pass 22m (4 aborts) | - | pass 15m | - | pass 10m | - | pass 10m |
| ts-contract (6 files, 4 packages + hidden test) | - | FAIL | - | **pass** 30m | - | FAIL | - | FAIL |

\* p3k r1 py-medium: the test passed at minute 4 but the agent spent 25 more minutes and 53 bash calls escaping the JSON payload of `write xd://edit`; commit 4 adds a worked call to the device doc and the loop did not recur in r2 (1 device write).

What the table says:
- **Every compact mode matches or beats the default on the 8 bugs; the default loses 3-4 to the machine, not to the model.** Its 22k prompt puts every hard bug at 27-39k tokens, where the oMLX memory guard rejects or aborts the prefill. The same bugs peak at 13-27k on p7k/p5k/p3k.
- **py-veryhard fails identically in all 8 runs**: the model fixes the reported case (`\d+ anos de experiência`) and never the documented rule (any claim of years of experience). That is the model, not the mode.
- **ts-veryhard** is the 30-minute wall: every mode finds the fix; writing the extra test on top is what times out.
- **p7k is the sweet spot**: same score as r1 both rounds, native `edit`/`grep`, and the only mode that completed the multi-package contract change.
- **p3k/p5k cost the device round-trips**: `edit` via `xd://` worked 22/22 times in r2, but each session pays one `read xd://edit` (1.3k tokens) and the model occasionally calls the device by name (`xd://grep`: 5 "Tool not found" in p3k r2; `grep` by name: 5 in r1).
- **LSP was never used.** With `typescript-language-server` and `pyright` installed and `xd://lsp` listed in every mode, no run in any mode read or wrote the device. Rename was done with grep + edit in all four modes. For this model, LSP is a cost (its row in the catalog) with no measured benefit.
- Aborts happen above ~25k tokens whenever the server has been up for hours (process grows to 24 GB + 18 GB compressed); a restart clears it. This is the 36 GB ceiling, and the strongest argument for a small prompt.



#### The bug nobody solved: py-veryhard

**The rule.** `docs/decisions.md` D07 in the Python repo: the fictional persona on a landing page may never claim years of experience, and deterministic validation must block such copy. The code already blocked Spanish (`\d+\s*años de experiencia`); the seeded bug removed the Portuguese pattern and the test that covered it.

**The report the agent got.** "A pt-BR bio saying 'Marina tem 12 anos de experiência organizando casamentos.' passes `validate_landing_copy`, but D07 says ... Fix it and add a pytest test that proves it."

**What all 8 runs did (4 presets x 2 rounds), identically.** Found the pattern list, widened it to accept the accent (`experi[eê]ncia`), kept the leading `\d+` (a number is required), added a test with the exact sentence from the report, ran the suite green, and stopped. All 8 diffs are the same one-line regex change (three spell the accent differently); all 8 keep the `\d+`.

**Why it fails.** The hidden test also sends "Marina traz anos de experiencia com casamentos reais." (no number). D07 forbids the claim, not the number. The agent fixed the symptom in the report and never went back to the rule to ask what else it forbids. The reference fix is a second pattern without `\d+`.

**What it tells you.** This is the model, not the preset: same decision with 22k or 8k of prompt, with or without the compact template. It is also the most useful kind of failure to know about when you use this setup: the agent will make the reported case pass; verifying that it covered the documented rule is still your job. A prompt rule ("when a report cites a documented rule, read the rule and cover every case it names") is the next thing to try; it was not tested here.

### Long sessions with compaction

One session, 4 chained turns (`-p` then `-p --continue`) on ts-veryhard, until the context crosses `compaction.thresholdTokens` 27,000 of 30,000.

| run | compaction threshold | requests | compaction fired | server aborts | outcome |
|---|---|---|---|---|---|
| p3k, r1 | 27k | 15 | no (never reached) | 3 | every turn ended by a memory abort at 22-24k; nothing fixed |
| p7k, r1 | 27k | 53 | yes, in turn 1 | 3 | fix + test written, 43/44 hidden cases; kept working 47 requests after compaction |
| p3k-long, r2 (stale dist) | 20k | 59 | yes, repeatedly (sawtooth 36k -> 12k) | 0 | survived every compaction; tests broken by a stale `dist` (meter bug 6), discarded |
| **p3k-long, r2 rerun** | 20k | 42 | yes, request 7, then 36 more requests | 2 | **fix + test written, 45/45 including hidden cases** |
| p7k-long, r2 (stale dist) | 20k | 27 | yes | 1 | same broken `dist`, discarded |
| **p7k-long, r2 rerun** | 20k | 45 | yes, request 6, then 39 more requests | 4 (all recovered) | **fix + test written, 44/44 including hidden cases** |

Mechanics proven: `-p --continue` rebuilds the session as a HISTORY block, in-turn compaction fires and the agent keeps calling tools (including `xd://` devices) afterwards. Quality on this machine: with the 20k threshold and a fresh server, both p3k and p7k completed the whole 4-turn task (fix, test, explanation, second audit); with 27k, only p7k got close. With a 30k window and a 27k threshold, single turns overshoot to 36-39k (compaction only runs between turns), so on 36 GB the useful threshold is 20k.

### Meter bugs found on the way (all in the harness, none in the model)

1. `git status --porcelain` as "touched nothing" while the runner writes `answer.txt` into the repo: 3 tasks failed on every mode including the control.
2. `ask-01` regex accepted the word "rate" while the agent invented one.
3. `xd-03` counted currencies per line; `RATES` is one line.
4. Background waiters watching a file the runner pre-creates empty.
5. Compression verifier flagged 2 rules "missing" that were just line-wrapped.
6. A `packages/core/dist` built from another branch (the LSP task's newer base) broke every test on the older branch with `Cannot find package '@smithy/util-retry'`; both round-2 long sessions ran on it. Runners now reinstall + rebuild packages after every checkout.
7. `bun --cwd` moves the agent's cwd (it read the harness repo's own `AGENTS.md`); the agent without a TTY hangs on stdin: redirect `/dev/null`.

### Did not work

- `omp compress` (the harness's own context-file compressor) stalled 35 min on the local model, zero output. Context files were compacted by hand.
- ANE offload: 64 layers = 28.6 GB resident, server rejects a 69-token prompt; 16 layers runs but loses prefill speed and swaps 2 GB.

### How this was produced

The fork, the benchmark harness, the seeded bugs, every run and this write-up were done by Claude Fable 5 (Claude Code, high reasoning effort), directed by a human who set the goals, chose the trade-offs and approved what gets published. Wall clock: about two days (Aug 26-28, 2026). Local model time: 80 scored runs, ~15.5 h of agent runs plus ~6 h of long sessions, 1,486 captured requests, on a laptop that was also serving deploys from another session in the same period (hence the pause protocol and the memory findings).

### Tests

- `test/xdev-force-mount.test.ts` (6): empty list, essential, pinned, transport invariant, globs, malformed entries
- `test/system-prompt-profile.test.ts` (5): default, dropped prose, size relation, retained surfaces, `SYSTEM.md` precedence
- `test/mcp-xdev-guidance-rule.test.ts` (4): derivable server, underivable, mixed, empty
- `test/xdev-compact-refs.test.ts` (5): xd:// reference in compact, bare name in full, worked call in device docs, factored MCP row, `xd://<tool>` fallback resolution
- `bun run check` green; the four coding-agent CI buckets green

### Try it

```yaml
promptProfile: compact
tools:
  xdevDocs: catalog
  xdevForceMount: [hub, eval, task, todo, web_search]
```

Benchmark scripts, presets and every captured request: https://github.com/vinicius91carvalho/oh-my-pi/tree/local-model-eval
