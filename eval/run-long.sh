#!/usr/bin/env bash
# One long session: the very-hard TS bug plus chained follow-ups, in the same
# session (-p then -p --continue), until the context crosses the compaction
# threshold (27k of a 30k window). Proves the compact profile survives
# compaction: the tap keeps every request, so we can see the summary land and
# the tools still being used correctly after it.
#
#   ./run-long.sh <profile>
set -uo pipefail
PROFILE="${1:?perfil}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
OMP_SRC="${OMP_SRC:-$HOME/github/vinicius91carvalho/oh-my-pi}"
BUN="$HOME/.local/share/mise/installs/bun/1.4.0/bin/bun"
CFG="$HERE/profiles/$PROFILE.yml"
OUT="${RESULTS_DIR:-$HERE/results-long}/$PROFILE"; rm -rf "$OUT"; mkdir -p "$OUT"
SESS="$OUT/sessions"; mkdir -p "$SESS"
WT="$HERE/real/fbj"

line=$(grep '"id": *"ts-veryhard"' "$HERE/real/bugs.jsonl")
get() { printf '%s' "$line" | python3 -c "import json,sys; v=json.load(sys.stdin).get('$1'); print('' if v is None else v)"; }
BRANCH=$(get branch); TEST=$(get test_cmd); PROMPT1=$(get prompt); HIDDEN=$(get hidden_test); HIDDEN_TO=$(get hidden_test_dest)

git -C "$WT" checkout -q -f "$BRANCH" && git -C "$WT" clean -fdq -e node_modules -e .venv -e '*.eslintcache'
# The worktree's node_modules and packages/*/dist must match the checked-out
# branch: a dist built from another branch breaks every test with a missing
# import (seen: '@smithy/util-retry' after an eval-lsp build).
(cd "$WT" && { pnpm install --offline --frozen-lockfile || pnpm install --frozen-lockfile; } >"$OUT/setup.log" 2>&1 && pnpm --filter './packages/*' build >>"$OUT/setup.log" 2>&1)
lsof -ti :1338 | xargs kill 2>/dev/null || true; sleep 0.3
TAP_OUT="$OUT" TAP_STUB=0 nohup python3 "$HERE/tap.py" >"$OUT/tap.log" 2>&1 &
for _ in $(seq 1 40); do lsof -ti :1338 >/dev/null 2>&1 && break; sleep 0.25; done

turn() { # $1 = n, $2 = prompt, $3 = extra flags
  local n="$1" p="$2"; shift 2
  while [ -f "$HERE/PAUSE" ]; do sleep 30; done
  echo "== turn $n: $p" | tee -a "$OUT/turns.log"
  (cd "$WT" && perl -e "alarm ${TASK_TIMEOUT:-2400}; exec @ARGV" "$BUN" "$OMP_SRC/packages/coding-agent/src/cli.ts" \
     -p --model omlxtap/Qwen3.8-27B-AWQ-5.0bpw --session-dir "$SESS" --auto-approve --config "$CFG" "$@" \
     "$p" </dev/null >"$OUT/answer-$n.txt" 2>"$OUT/stderr-$n.txt") || true
  ls -1 "$OUT"/req-*.json | wc -l | xargs echo "   requests so far:" | tee -a "$OUT/turns.log"
}

turn 1 "$PROMPT1"
turn 2 "Now add a vitest test that would have caught this bug. Run it and make sure it passes." --continue
turn 3 "Explain in 5 lines what the bug was, where it lived, and why the docs rule matters. Then run the full test file once more." --continue
turn 4 "Look for one more place in the same package that could break the same rule. If you find one, fix it and test; if not, say so." --continue

git -C "$WT" diff > "$OUT/agent.diff"
git -C "$WT" status --porcelain > "$OUT/status.txt"
[ -z "$HIDDEN" ] || cp "$HERE/$HIDDEN" "$WT/$HIDDEN_TO"
if (cd "$WT" && eval "$TEST") >"$OUT/test.log" 2>&1; then echo '{"tests_ok": true}' > "$OUT/score.json"; else echo '{"tests_ok": false}' > "$OUT/score.json"; fi
python3 "$HERE/usage.py" "$OUT" | tee "$OUT/usage.json"
python3 "$HERE/compaction-check.py" "$OUT" | tee "$OUT/compaction.json"
git -C "$WT" checkout -q -f -- . ; git -C "$WT" clean -fdq -e node_modules -e .venv -e '*.eslintcache'; git -C "$WT" checkout -q -f eval-bugs
lsof -ti :1338 | xargs kill 2>/dev/null || true
