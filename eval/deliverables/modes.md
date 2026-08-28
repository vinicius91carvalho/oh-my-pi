# The four modes

Two settings do all the work: `promptProfile: compact` (shorter instruction template, same rules) and `tools.xdevForceMount` (move a tool's JSON schema out of the prompt; the model fetches it on demand with `read xd://<tool>`). `tools.xdevDocs: catalog` is mandatory with the second one, or the docs come back inline and the saving is zero.

## Tools per mode

| mode | top-level (schema in every request) | mounted in `xd://` (fetched on demand) | first prompt, real TS monorepo | first prompt, small repo |
|---|---|---|---|---:|
| **base** (upstream default) | read bash edit eval glob grep task hub todo web_search write | none | 22,320 | 19,278 |
| **p7k** | read bash edit glob grep write | hub eval task todo web_search | 10,838 | 7,888 |
| **p5k** | read bash grep write | + edit glob | 8,574 | 5,624 |
| **p3k** | read bash write | + grep | 8,204 (5,802 with commit 4) | 5,254 |

Nothing is removed in any mode. Every tool still works; the probe "edit a file using the mounted `edit` device" passes on p3k with zero `edit` schema in the request. `ask` and MCP tools follow the same rule.

The tool schema cost that drives this: `hub` 2,898 tokens, `edit` 1,793, `todo` 1,364, `task` 1,258, `eval` 1,185, `read` 1,077, `bash` 679, `glob` 483, `grep` 360, `web_search` 343, `write` 294.

## Config (`~/.omp/agent/config.yml` or project `.omp/config.yml`)

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

## Which one, day to day (measured, see benchmark.md)

| situation | mode | why |
|---|---|---|
| 32k window, daily coding | **p7k** | 7/8 real bugs in both rounds (default: 4-5/8), native `edit`/`grep`, the only mode that finished a 4-package contract change, and the only one whose 4-turn session fixed the bug after compaction |
| 32k window + MCP servers or a big `AGENTS.md` | p5k | 2.3k more tokens freed; `edit` via device worked 22/22 times, but costs one `read xd://edit` per session and 6-7/8 on the bugs |
| absolute floor | p3k | 6-7/8; only 370 tokens below p5k and the model sometimes calls `xd://grep` as a tool name |
| 64k+ window | base or p7k | the cut still shortens prefill (137 t/s here: 12k tokens = 90 s) and keeps you under the memory ceiling |

Two things not to bother with on a 27B local model: the `lsp` device (installed servers, listed in every mode, never called once in 40 runs) and `read.defaultLimit` tuning (the model reads whole files anyway; it is the prompt rule that matters).

Compaction on 36 GB: set `compaction.thresholdTokens: 20000`, not 27000. Single turns overshoot by 10-15k (compaction only runs between turns) and the server aborts above ~25k once it has been up for hours; restart oMLX before a long session.

Context files count too: `~/.omp/agent/AGENTS.md` dense (1,010 tokens) + on-demand skills instead of a 1,875-token rulebook saved 2,437 tokens per request on top of the table above.

## Compaction (long sessions)

Compaction is untouched by the fork and fires on the same setting (`compaction.thresholdTokens`, here 27,000 of 30,000). The modes only change how much room is left before it fires: base has ~7.7k tokens of conversation before compaction, p7k ~19k, p3k ~22k. See benchmark.md, "long session", for the measured run.
