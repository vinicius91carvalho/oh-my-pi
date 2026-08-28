# Real-project bug benchmark

Two git worktrees of real repos, four seeded bugs each, one branch per bug (`bug/<lang>-<level>`), all off the base commit so they never stack.

| repo | worktree | base | setup |
|---|---|---|---|
| find-best-job (TS, pnpm monorepo) | `real/fbj` | master `48cff17` | `pnpm install --offline`; rsync `stealth-browser/` (submodule, no .git) from the main checkout; `pnpm build` once |
| infoproduct (Python, uv workspace) | `real/infoproduct` | `917142c` | `uv sync --all-packages --group dev` |

`bugs.jsonl` = one line per bug: branch, test command, prompt given to the agent, reference fix. Every bug was seen failing on its branch and passing with the reference fix before it was recorded.

Very-hard bugs also delete the test that would have caught them; `hidden/` holds a hidden test copied in only at scoring time.

Run: `../run-real.sh <profile>` (all bugs) or `../run-real.sh <profile> <bug-id>`. Results: `../results-real/<profile>/`. Table: `../table-real.py`.
