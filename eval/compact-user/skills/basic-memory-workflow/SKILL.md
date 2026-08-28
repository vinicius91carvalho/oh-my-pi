---
name: basic-memory-workflow
description: How to load and write Vinicius's Basic Memory notes, and where plans live.
---

# Basic Memory

Local only, under `~/basic-memory/<org>/<repo>`. There is no cloud: never
suggest `bm cloud login`, never pass a `workspace` parameter. Vinicius reads the
same files in Obsidian, so write notes a human enjoys reading.

## Start of every task, before touching code

1. Pick the project from the folder. `~/github/<org>/<repo>` maps to the Basic
   Memory project `<repo>`. Anywhere else, use `personal`. If it does not exist,
   create it with `create_memory_project` and a local path.
2. `search_notes` for what was asked, plus the words around it.
3. `build_context` on the `memory://` links that look related.
4. `recent_activity` when picking up older work.

Never start from zero when a note already exists.

## While you work

Save decisions, root causes, traps, and constraints with `write_note` as they
happen, without being asked. Grow the note that already exists with `edit_note`;
never write a near-copy.

Shape: observations as `- [category] fact #tag`, links as
`- relates_to [[Exact Note Title]]`, so the wikilinks resolve in Obsidian.

Both doors work: the MCP tools inside a session, and the `bm` CLI in a shell
(`bm tool search-notes`, `write-note`, `edit-note`, `recent-activity`). Use the
CLI when already in a terminal or doing many at once.

## Plans

Every plan becomes a note in the `plans/` folder of that project. The file in
`~/.claude/plans/` is only a scratchpad; copy it over when planning ends and
keep the two the same. Read `plans/` at the start of a session and continue what
is open; never restart work that already has a plan. Update that same note as
things move. A finished plan is marked finished, never deleted.
