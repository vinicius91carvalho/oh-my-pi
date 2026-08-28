## feat: let local models fit: `tools.xdevForceMount` + `promptProfile: compact`

Refs #1734. Five commits, each self-contained; defaults are untouched.

### Why

On a 30k-window local model, 18.0.7 spends 22,643 prompt tokens before the first user word; 11,734 of them are the JSON schemas of the 11 top-level tools. `tools.xdev` already defers a schema to `read xd://<tool>`, but `isMountableUnderXdev()` only accepts `loadMode: "discoverable"`, and `ESSENTIAL_BUILTIN_TOOL_NAMES` + `XDEV_KEEP_TOP_LEVEL` cover 10 of those 11. Extensions get `setActiveTools` but not `setActiveToolPresentation`, so an expensive tool can be removed, never deferred.

### What

| commit | setting | effect |
|---|---|---|
| `feat(tools): add tools.xdevForceMount` | `tools.xdevForceMount: [globs]`, default `[]` | named tools mount under `xd://` even when essential/pinned. `read`/`write` are never demoted (transport). Forcing a `XDEV_KEEP_TOP_LEVEL` name is allowed and documented as a trade-off |
| `feat(prompt): add promptProfile` | `promptProfile: full \| compact`, default `full` | `full` renders byte-identical (33,440 bytes both sides). `compact` keeps the authority/safety contract, tool mapping, stop/ask/verify, edit-and-test loop, `xd://` protocol, and every generated surface (skills, rules, context files, inventory, devices); drops personality, examples, URL catalog, long workflow prose. Instruction block 7,412 -> 6,222 tokens on the same session |
| `fix(prompt): name devices as xd:// paths, show a device call, factor MCP catalog rows` | none | compact profile references a mounted tool as `xd://grep` (a 27B model called `grep` by name otherwise); `read xd://<tool>` ends with one worked `write(...)` call (a model spent 25 min escaping a patch without it); MCP catalog row factors the shared prefix |
| `fix(tools): accept xd://<tool> as a fallback tool-call name` | none | a call literally named `xd://grep` lands on the mounted `grep` device instead of "Tool not found" |
| `perf(prompt): stop enumerating every mounted MCP tool` | none | route block states the naming rule once per server when `createMCPToolName` reproduces every live name; catalog groups a server's tools in one row. `## MCP Tool Routes` 1,222 -> 551 tokens with one 21-tool server |

### Presets and what they cost

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

`xd://` probes (read device list, edit with the mounted `edit`, plan with mounted `todo`): 3/3 on defaults and on the 3-tool config. Compaction unchanged; a 4-turn session past the threshold: p7k kept working 47 requests after compaction, fix + test landed. Scripts and captured requests: https://github.com/vinicius91carvalho/oh-my-pi/tree/local-model-eval

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
