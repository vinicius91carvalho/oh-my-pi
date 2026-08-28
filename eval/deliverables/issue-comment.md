Measured on a 30k-window local model (oMLX, Qwen3.8-27B, M3 Max 36 GB), tokens from the server's `usage.prompt_tokens`:

- 18.0.7 defaults, real TS monorepo + one 21-tool MCP server: **22,643 tokens** before the first user word. Tool schemas 11,734 (52%), template 6,160, `AGENTS.md` + user file 3,981.
- `tools.xdev` cannot help: `isMountableUnderXdev()` only mounts `loadMode: "discoverable"`, and `ESSENTIAL_BUILTIN_TOOL_NAMES` + `XDEV_KEEP_TOP_LEVEL` cover 10 of the 11 tools. Extensions get `setActiveTools` but not `setActiveToolPresentation`, so an expensive tool can be removed, never deferred.

PR_LINK adds two opt-in settings, defaults unchanged (`promptProfile: full` renders byte-identical):

| | prompt tokens | 12-task fixture | 8 real bugs (TS+Py) |
|---|---:|---:|---:|
| defaults | 22,643 | 11/12 | 4/8, 5/8 |
| `promptProfile: compact` + `xdevForceMount: [hub, eval, task, todo, web_search]` | 10,838 | 11/12 | 7/8, 7/8 |
| + `edit, glob` | 8,574 | 12/12 | 7/8, 6/8 |
| + `grep` | 8,204 | 12/12 | 7/8, 6/8 |

With `edit` mounted, the model fetches `xd://edit` and edits with it; the probe for that passes 3/3. Compaction is untouched and was exercised in a 4-turn session past the 27k threshold (p7k: 53 requests, compaction in turn 1, fix + test written afterwards; the default mode's hard bugs are rejected by the server at 27-39k tokens on 36 GB). Full write-up and scripts: https://github.com/vinicius91carvalho/oh-my-pi/tree/local-model-eval
