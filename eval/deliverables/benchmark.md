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


## 4. Long session with compaction

One session, 4 chained turns (`-p` then `-p --continue`) on ts-veryhard, until the context crosses `compaction.thresholdTokens` 27,000 of 30,000.

| run | compaction threshold | requests | compaction fired | server aborts | outcome |
|---|---|---|---|---|---|
| p3k, r1 | 27k | 15 | no (never reached) | 3 | every turn ended by a memory abort at 22-24k; nothing fixed |
| p7k, r1 | 27k | 53 | yes, in turn 1 | 3 | fix + test written, 43/44 hidden cases; kept working 47 requests after compaction |
| p3k-long, r2 | 20k | 59 | yes, repeatedly (sawtooth 36k -> 12k) | 0 | survived every compaction; test environment was broken by a stale `dist` (see meter bugs) -> rerun in progress |
| p7k-long, r2 | 20k | 27 | yes | 1 | same broken `dist` -> rerun in progress |

Mechanics proven: `-p --continue` rebuilds the session as a HISTORY block, in-turn compaction fires and the agent keeps calling tools (including `xd://` devices) afterwards. Quality on this machine: only p7k completed the 4-turn task. With a 30k window and a 27k threshold, single turns overshoot to 36-39k (compaction only runs between turns), so on 36 GB the useful threshold is 20k.


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
