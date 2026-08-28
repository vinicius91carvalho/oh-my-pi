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

### Measured (server `usage.prompt_tokens`, real TS monorepo, one 21-tool MCP server)

| config | prompt tokens | 12-task fixture | 8 real bugs (TS + Python) |
|---|---:|---:|---:|
| defaults | 22,643 | 11/12 | 4/8, 5/8 (hard bugs rejected by the server at 27-39k tokens) |
| compact + `xdevForceMount: [hub, eval, task, todo, web_search]` | 10,838 | 11/12 | 7/8, 7/8 |
| + `edit, glob` | 8,574 | 12/12 | 7/8, 6/8 |
| + `grep` | 8,204 | 12/12 | 7/8, 6/8 |

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
