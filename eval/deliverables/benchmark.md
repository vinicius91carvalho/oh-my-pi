# Benchmark

## Machine and server

| item | value |
|---|---|
| MacBook Pro M3 Max 14/30, 36 GB, 300 GB/s | oMLX 0.6.3rc3, launchd `org.nix-community.home.omlx`, port 1337 |
| model | `Qwen3.8-27B-AWQ-5.0bpw` (17.4 GB resident, MTP head in the checkpoint) |
| oMLX config | `mtp_enabled` on, `turboquant_kv_bits 3.5`, no ANE, `--memory-guard-gb 27`, SSD paged cache |
| decode | **32.2 t/s** with MTP on the plain-text bench (`eval/results-B3-mtp.json`), 17.2-17.9 t/s without it; **18-27 t/s (median ~21) inside agent runs**, where MTP accepts fewer drafts on tool-call JSON |
| prefill | 137 t/s cold at 12k tokens (TTFT 92 s); 4,143 t/s when the SSD cache hits (TTFT 3 s) |
| usable window | 30,000 tokens set in `models.yml`; ~32k is the memory ceiling (peak 24.7 GB), 64k does not fit. oMLX has no truncation: over the window = HTTP 400 |
| harness | OMP 18.0.7 fork, `bun 1.4.0`, tokens = server `usage.prompt_tokens` via a logging proxy (`tap.py`) |

## 1. Prompt size ladder (real TS monorepo, `AGENTS.md` + user file + one 21-tool MCP server)

Server `usage.prompt_tokens` for the whole request. Of these, the user's own context files are 3,923 tokens in every row until the last one (1,486 after compaction); the rest is OMP's template + tool schemas. See modes.md for the split per preset.

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

## 2. Fixture: 12 agentic tasks, small JS repo with one failing test

Scored by shell checks (tests pass, file exists, tree clean, answer matches), not by reading the answer.

| mode | prompt tokens | passed | median s | failure |
|---|---:|---:|---:|---|
| base | 19,278 | 11/12 | 171 | ask-01: stopped mid-work |
| p7k | 7,888 | 11/12 | 152 | ask-01: invented a rate without saying so |
| p5k | 5,624 | 12/12 | 148 | - |
| p3k | 5,254 | 12/12 | 119 | - |

Extra probes, base vs p3k: `xd://` protocol 3/3 both; grounding (no invented sources) 6/6 both.

## 3. Real projects: 8 seeded bugs, 4 modes

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

### Difficulty levels

| level | definition | time budget the level implies |
|---|---|---|
| easy | one line in one file; the failing test names the file | read the test, read the file, one edit, run tests: minutes |
| medium | bug in one module, failing test in another package; the agent must follow the call chain | plus a grep or two and a rebuild of the touched package |
| hard | symptom far from cause (a wrong constant or regex in a shared module; the error never names the culprit file) | plus real investigation across packages |
| very hard | a documented business rule is broken and the test that would catch it was deleted; the report describes one symptom; the agent must find the rule in the docs, fix it fully, and write the test back; a hidden test with more cases is copied in at scoring | plus reading docs, writing tests, and getting the rule right, not just the symptom |
| LSP | rename an exported symbol used in 4 packages (8 files) / change a function's return type and propagate it to 4 packages (6 files) | plus rebuilding packages so cross-package `tsc` and vitest pass |

### Pass rate and time per level (both rounds together, 4 runs per cell; LSP tasks are round 2 only)

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



### The bug nobody solved: py-veryhard

**The rule.** `docs/decisions.md` D07 in the Python repo: the fictional persona on a landing page may never claim years of experience, and deterministic validation must block such copy. The code already blocked Spanish (`\d+\s*años de experiencia`); the seeded bug removed the Portuguese pattern and the test that covered it.

**The report the agent got.** "A pt-BR bio saying 'Marina tem 12 anos de experiência organizando casamentos.' passes `validate_landing_copy`, but D07 says ... Fix it and add a pytest test that proves it."

**What all 8 runs did (4 presets x 2 rounds), identically.** Found the pattern list, widened it to accept the accent (`experi[eê]ncia`), kept the leading `\d+` (a number is required), added a test with the exact sentence from the report, ran the suite green, and stopped. All 8 diffs are the same one-line regex change (three spell the accent differently); all 8 keep the `\d+`.

**Why it fails.** The hidden test also sends "Marina traz anos de experiencia com casamentos reais." (no number). D07 forbids the claim, not the number. The agent fixed the symptom in the report and never went back to the rule to ask what else it forbids. The reference fix is a second pattern without `\d+`.

**What it tells you.** This is the model, not the preset: same decision with 22k or 8k of prompt, with or without the compact template. It is also the most useful kind of failure to know about when you use this setup: the agent will make the reported case pass; verifying that it covered the documented rule is still your job. A prompt rule ("when a report cites a documented rule, read the rule and cover every case it names") is the next thing to try; it was not tested here.

## 4. Long session with compaction

One session, 4 chained turns (`-p` then `-p --continue`) on ts-veryhard, until the context crosses `compaction.thresholdTokens` 27,000 of 30,000.

| run | compaction threshold | requests | compaction fired | server aborts | outcome |
|---|---|---|---|---|---|
| p3k, r1 | 27k | 15 | no (never reached) | 3 | every turn ended by a memory abort at 22-24k; nothing fixed |
| p7k, r1 | 27k | 53 | yes, in turn 1 | 3 | fix + test written, 43/44 hidden cases; kept working 47 requests after compaction |
| p3k-long, r2 (stale dist) | 20k | 59 | yes, repeatedly (sawtooth 36k -> 12k) | 0 | survived every compaction; tests broken by a stale `dist` (meter bug 6), discarded |
| **p3k-long, r2 rerun** | 20k | 42 | yes, request 7, then 36 more requests | 2 | **fix + test written, 45/45 including hidden cases** |
| p7k-long, r2 (stale dist) | 20k | 27 | yes | 1 | same broken `dist`, discarded |
| p7k-long, r2 rerun | 20k | (running) | | | |

Mechanics proven: `-p --continue` rebuilds the session as a HISTORY block, in-turn compaction fires and the agent keeps calling tools (including `xd://` devices) afterwards. Quality on this machine: with the 20k threshold and a fresh server, p3k completed the whole 4-turn task (fix, test, explanation, second audit); with 27k, only p7k got close. With a 30k window and a 27k threshold, single turns overshoot to 36-39k (compaction only runs between turns), so on 36 GB the useful threshold is 20k.


## Speed inside the agent (1,068 requests, both rounds, server-reported)

The 32 t/s bench number is a 69-token prompt. Inside agent runs generation falls with context size, because every token attends over the whole KV cache:

| context | generation, median |
|---|---:|
| 5-10k | 27.9 t/s |
| 10-15k | 24.3 |
| 15-20k | 21.5 |
| 20-25k | 20.4 |
| 25-30k | 19.8 |

| preset | generation median / p90 | uncached prefill | prefix-cache hit | TTFT median |
|---|---:|---:|---:|---:|
| base | 21.0 / 23.4 | 95 t/s | 90% | 23-26 s |
| p7k | 21.6 / 27.2 | 110 t/s | 85% | 19-21 s |
| p5k | 22.6 / 28.5 | 117 t/s | 84% | 19-20 s |
| p3k | 22.7 / 29.0 | 112 t/s | 87% | 15-19 s |

The compact presets are faster per request only because they live in smaller contexts. oMLX caches in 2,048-token pages, so up to 2k tokens are re-prefilled every request on top of the new turn (the cache-hit column).

## Meter bugs found on the way (all in the harness, none in the model)

1. `git status --porcelain` as "touched nothing" while the runner writes `answer.txt` into the repo: 3 tasks failed on every mode including the control.
2. `ask-01` regex accepted the word "rate" while the agent invented one.
3. `xd-03` counted currencies per line; `RATES` is one line.
4. Background waiters watching a file the runner pre-creates empty.
5. Compression verifier flagged 2 rules "missing" that were just line-wrapped.
6. A `packages/core/dist` built from another branch (the LSP task's newer base) broke every test on the older branch with `Cannot find package '@smithy/util-retry'`; both round-2 long sessions ran on it. Runners now reinstall + rebuild packages after every checkout.
7. `bun --cwd` moves the agent's cwd (it read the harness repo's own `AGENTS.md`); the agent without a TTY hangs on stdin: redirect `/dev/null`.

## Did not work

- `omp compress` (the harness's own context-file compressor) stalled 35 min on the local model, zero output. Context files were compacted by hand.
- ANE offload: 64 layers = 28.6 GB resident, server rejects a 69-token prompt; 16 layers runs but loses prefill speed and swaps 2 GB.
