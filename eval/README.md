# Measuring what OMP sends, and whether cutting it hurts

Two harnesses. One counts the tokens OMP puts in front of a local model before
the conversation starts. The other checks whether cutting them costs anything.

## What is here

| File | Does |
|---|---|
| `tap.py` | Proxy on 1338. Forwards to the oMLX server on 1337 and writes every request body to disk. `TAP_STUB=1` answers from the proxy instead, so a profile sweep needs no inference. |
| `measure.sh` | Runs one profile through the tap and prints its token breakdown. |
| `count_local.py` | Counts a captured request with the model's own chat template and tokenizer. No server. |
| `count.py` | Counts the same request with the server (`usage.prompt_tokens`). Slower, authoritative. |
| `profiles/*.yml` | Config overlays, one per profile. Passed with `omp --config`. |
| `tasks.jsonl` | 12 agentic tasks with a shell check each. |
| `fixture/` | Small git repo the tasks run against. Has one real failing test. |
| `run-tasks.sh` | Runs every task under one profile in a fresh copy of the fixture and scores it. |
| `table.py` | Joins tokens and scores into the final table. |

## Counting tokens

```bash
./measure.sh base          # stubbed: fast, no inference
STUB=0 ./measure.sh base   # through the real server
```

Both write to `runs/<profile>/`: the captured request as `req-001.json`, the
answer, and `tokens.json`.

`count_local.py` matches the server exactly on the message half (10790 vs 10792
on the same request) and runs about 2% high on the tool half, because oMLX
normalizes tool schemas slightly tighter than `tojson` does. The offset is
constant across profiles, so the local counter ranks them and the server
confirms the winners.

## Scoring behavior

```bash
./run-tasks.sh <profile> [rep]
python3 table.py
```

Each task runs in its own copy of `fixture/`, so a task that edits files cannot
affect the next one. The check is a shell command run inside that copy: a file
exists, `npm test` passes, the answer matches a pattern, `git status` is clean.

The tasks cover the five things the OMP issue thread agreed matter more than
token count: picking the right tool, editing the right place, running the tests
and reading the result, stopping when done, and pushing back instead of
inventing an answer.

## Two traps worth knowing

- **`bun --cwd` moves OMP's working directory.** Run OMP from inside the target
  project and point at the source entry file instead, or it discovers the
  wrong `AGENTS.md`.
- **OMP without a TTY reads stdin and waits for EOF.** In a script, redirect
  from `/dev/null` or it hangs forever on "readPipedInput".
