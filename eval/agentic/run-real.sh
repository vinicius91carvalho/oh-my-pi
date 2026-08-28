#!/usr/bin/env bash
# Run every seeded bug in real/bugs.jsonl under one profile, inside the real
# project worktrees, and score with the project's own test command.
#
#   ./run-real.sh <profile> [bug-id-filter]
#
# Goes through the tap (1338 -> oMLX 1337) so every request is on disk.
set -uo pipefail

PROFILE="${1:?perfil}"
ONLY="${2:-}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
OMP_SRC="${OMP_SRC:-$HOME/github/vinicius91carvalho/oh-my-pi}"
BUN="$HOME/.local/share/mise/installs/bun/1.4.0/bin/bun"
CFG="$HERE/profiles/$PROFILE.yml"
OUT="${RESULTS_DIR:-$HERE/results-real}/$PROFILE"
mkdir -p "$OUT"
[ -n "$ONLY" ] || : > "$OUT/scores.jsonl"

start_tap() { # $1 = dir for req-NNN.json
  lsof -ti :1338 | xargs kill 2>/dev/null || true
  sleep 0.3
  TAP_OUT="$1" TAP_STUB=0 nohup python3 "$HERE/tap.py" >"$1/tap.log" 2>&1 &
  for _ in $(seq 1 40); do lsof -ti :1338 >/dev/null 2>&1 && break; sleep 0.25; done
}

while IFS= read -r line; do
  [ -n "$line" ] || continue
  # Touch eval/agentic/PAUSE to hold the sweep between bugs (memory-heavy work
  # elsewhere on the machine); remove it to resume.
  while [ -f "$HERE/PAUSE" ]; do sleep 30; done
  get() { printf '%s' "$line" | python3 -c "import json,sys; v=json.load(sys.stdin).get('$1'); print('' if v is None else v)"; }
  ID=$(get id); [ -z "$ONLY" ] || [ "$ID" = "$ONLY" ] || continue
  REPO=$(get repo); BRANCH=$(get branch); LEVEL=$(get level)
  TEST=$(get test_cmd); PROMPT=$(get prompt); HIDDEN=$(get hidden_test); HIDDEN_TO=$(get hidden_test_dest)
  WT="$HERE/real/$REPO"
  RUN="$OUT/$ID"; rm -rf "$RUN"; mkdir -p "$RUN"

  git -C "$WT" checkout -q -f "$BRANCH" && git -C "$WT" clean -fdq -e node_modules -e .venv -e '*.eslintcache'
  # Optional per-task setup (a branch whose lockfile differs from the worktree's install).
  SETUP=$(get setup_cmd); [ -z "$SETUP" ] || (cd "$WT" && eval "$SETUP") >"$RUN/setup.log" 2>&1
  start_tap "$RUN"

  START=$(python3 -c 'import time; print(time.time())')
  (cd "$WT" && perl -e "alarm ${TASK_TIMEOUT:-1800}; exec @ARGV" "$BUN" "$OMP_SRC/packages/coding-agent/src/cli.ts" \
      -p --model omlxtap/Qwen3.8-27B-AWQ-5.0bpw --no-session --auto-approve --config "$CFG" \
      "$PROMPT" </dev/null >"$RUN/answer.txt" 2>"$RUN/stderr.txt") || true
  END=$(python3 -c 'import time; print(time.time())')

  git -C "$WT" diff > "$RUN/agent.diff"
  git -C "$WT" status --porcelain > "$RUN/status.txt"
  # easy/medium/hard: the agent may not touch tests. very hard must add one.
  TOUCHED_TESTS=$(grep -E '(\.test\.|\.spec\.|test_[^/]*\.py|/tests?/)' "$RUN/status.txt" | wc -l | tr -d ' ')
  if [ -n "$HIDDEN" ]; then cp "$HERE/$HIDDEN" "$WT/$HIDDEN_TO"; fi
  if (cd "$WT" && eval "$TEST") >"$RUN/test.log" 2>&1; then TESTS_OK=1; else TESTS_OK=0; fi
  if [ "$TESTS_OK" = 1 ] && { [ "$LEVEL" = "veryhard" ] || [ "$LEVEL" = "lsp" ] || [ "$TOUCHED_TESTS" = 0 ]; }; then PASS=1; else PASS=0; fi
  REQS=$(ls -1 "$RUN"/req-*.json 2>/dev/null | wc -l | tr -d ' ')
  MAXTOK=$(python3 "$HERE/usage.py" --max "$RUN" 2>/dev/null || echo null)
  ABORTED=$(python3 "$HERE/usage.py" "$RUN" 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin)["aborted_streams"])' || echo 0)

  git -C "$WT" checkout -q -f -- . ; git -C "$WT" clean -fdq -e node_modules -e .venv -e '*.eslintcache'; git -C "$WT" checkout -q -f eval-bugs
  python3 - "$ID" "$LEVEL" "$PASS" "$TESTS_OK" "$TOUCHED_TESTS" "$START" "$END" "$REQS" "$MAXTOK" "$ABORTED" >>"$OUT/scores.jsonl" <<'PY'
import json, sys
_, tid, level, ok, tests_ok, touched, start, end, reqs, maxtok, aborted = sys.argv
print(json.dumps({"id": tid, "level": level, "pass": bool(int(ok)), "tests_ok": bool(int(tests_ok)),
  "touched_tests": int(touched), "seconds": round(float(end)-float(start),1), "requests": int(reqs),
  "max_prompt_tokens": None if maxtok=="null" else int(maxtok), "aborted": int(aborted)}))
PY
  tail -1 "$OUT/scores.jsonl"
done < "${BUGS_FILE:-$HERE/real/bugs.jsonl}"
lsof -ti :1338 | xargs kill 2>/dev/null || true
