# Cut OMP's (Oh My Pi) system prompt from 22.6k to 5.9k tokens with two settings, then tested it on real TS + Python bugs

**The issue.** [OMP](https://github.com/can1357/oh-my-pi) 18.0.7 sends **22,643 tokens** before you type a word, measured on the wire inside a real TypeScript monorepo. Where it goes: JSON schemas of the 11 top-level tools 11,734 (52%; `hub` alone 2,898), instruction template 6,160, my own context files 3,981, MCP routes 401, misc 367. Fine on a 200k cloud model. On a local 30k window it leaves ~7k for the work. Upstream issue: [#1734](https://github.com/can1357/oh-my-pi/issues/1734).

**Why config alone cannot fix it.** OMP already has lazy tool loading: a tool mounted under `xd://` ships no schema, the model runs `read xd://<tool>` when it needs it. But `isMountableUnderXdev()` only accepts tools declared `discoverable`, and `ESSENTIAL_BUILTIN_TOOL_NAMES` + `XDEV_KEEP_TOP_LEVEL` pin 10 of the 11. Extensions get `setActiveTools` but not `setActiveToolPresentation`: from outside the source an expensive tool can be removed, never deferred.

**The change: two settings, off by default.**

```yaml
promptProfile: compact            # same rules, same generated surfaces, no personality/examples/long prose
tools:
  xdevDocs: catalog
  xdevForceMount: [hub, eval, task, todo, web_search]   # any glob; read/write can never be demoted
```

`promptProfile: full` still renders byte-identical to upstream. Three presets, measured on the captured request:

| preset | `config.yml` | tools left top-level | moved to `xd://` | OMP's share: template + schemas | my context files | request total |
|---|---|---|---|---:|---:|---:|
| base (upstream default) | nothing | 11 | none | 18,531 | 3,923 | **22,643** |
| **p7k** | `promptProfile: compact` + `xdevForceMount: [hub, eval, task, todo, web_search]` | read bash edit glob grep write | hub eval task todo web_search | 6,787 | 3,923 | **10,838** |
| p5k | p7k + `edit, glob` | read bash grep write | + edit glob | 4,416 | 3,923 | **8,574** |
| p3k | p5k + `grep` | read bash write | + grep | 4,036 | 3,923 | **8,204** |
| p3k + my files compacted | same | same | same | 4,033 | 1,486 | **5,886** |

The preset name is OMP's own share, rounded. "Request total" adds my `~/.omp/agent/AGENTS.md` and the project's `AGENTS.md` (untouched by the fork; the last row is me rewriting them densely with detail moved to on-demand skills). All presets also need `tools.xdevDocs: catalog`, or the mounted tools' docs come back inline.

**How I tested it.** Local Qwen3.8-27B on a 36 GB Mac, 30k window, every token count from the server's `usage`. Three tests:

1. *Fixture*: a 5-file JS repo, 12 short tasks (pick the right tool, edit the right place, run tests, stop, ask instead of inventing), shell checks.
2. *Real bugs*: 8 bugs seeded into two real repos (a TS pnpm monorepo, 1,488 files; a Python uv workspace, 910 files), each seen failing and passing with a reference fix first. Headless `omp -p --auto-approve --config <preset>`, 30-minute cap, scored by the repo's tests plus "did not edit the tests". Two rounds; round 2 adds two tooling tasks (rename across 8 files, return-type change across 6 files) and 4-turn sessions that cross the compaction threshold.

**Results.**

| preset | fixture | 8 real bugs, round 1 -> 2 | rename / contract | 4-turn session with compaction |
|---|---:|---:|---:|---|
| base | 11/12 | 4/8 -> 5/8 | 1/2 | not run (does not fit) |
| **p7k** | 11/12 | **7/8 -> 7/8** | **2/2** | 20k threshold: fix + test, 44/44 hidden cases |
| p5k | 12/12 | 7/8 -> 6/8 | 1/2 | - |
| p3k | 12/12 | 7/8 -> 6/8 | 1/2 | 20k threshold: fix + test, 45/45 |

| level (2 bugs each, TS + Python) | base | p7k | p5k | p3k |
|---|---|---|---|---|
| easy: 1 line, test names the file | 4/4, 8 min | 4/4, 5 min | 4/4, 4 min | 4/4, 4 min |
| medium: bug in one package, test in another | 4/4, 5 min | 4/4, 4 min | 4/4, 5 min | 4/4, 18 min |
| hard: cause far from symptom | 1/4, rejected by server | 4/4, 8 min | 4/4, 9 min | 4/4, 7 min |
| very hard: documented rule broken, covering test deleted, hidden test at scoring | 0/4 | 2/4, 29 min | 1/4, 20 min | 1/4, 22 min |
| LSP: rename across 8 files / contract change across 6 | 1/2 | 2/2, 22 min | 1/2, 20 min | 1/2, 12 min |

Times are medians per run. Base fails "hard" because prompt + first reads no longer fit the window: the server rejects, not the model.

The one bug no preset solved (8/8 runs, same diff): a docs rule says the persona may never claim years of experience; every run widened the regex, kept the `\d+`, wrote a test for the reported sentence and stopped. Symptom fixed, rule not read. That is the model, not the prompt size.

**Same tools, different path.** Nothing is removed. With `edit` mounted, p5k/p3k fetched `xd://edit` and edited through it 22/22 times in round 2. Two things the runs taught me and that went into the PR: in compact mode the catalog must name devices as `xd://edit` (not `edit`) and show one example call, or the model calls `edit` by name and gets "unknown tool"; and `xd://<tool>` should be accepted as a tool-call name as a fallback. Language servers were installed and `xd://lsp` listed in every preset; no run called it, this model renames with grep + edit.

**Compaction.** Long sessions work with the compact template; the trick was the threshold. At 27k on a 30k window the summary request itself ran out of room once; at 20k both presets went 4 turns clean (`compaction.thresholdTokens: 20000`).

**Repo.** Fork + branch: https://github.com/vinicius91carvalho/oh-my-pi/tree/compact-prompt-for-local-models. Scripts, presets, every captured request: https://github.com/vinicius91carvalho/oh-my-pi/tree/local-model-eval

**PR.** PR_LINK - five commits with tests. Whether it lands or not, the branch runs today.

**How this was produced.** Fork, harness, seeded bugs, runs and this post were done by Claude Fable 5 in Claude Code at high effort, with me setting goals and approving what ships. About two days, 80 scored runs.

**Caveats.** One machine, one 27B, one harness version, one run per cell. `omp compress` stalled on the local model; I compacted my context files by hand.
