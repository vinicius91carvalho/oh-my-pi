#!/usr/bin/env bash
# Run every task in tasks.jsonl under one profile, in a fresh copy of the
# fixture repo, and score each with its own check command.
#
#   ./run-tasks.sh <profile> [rep]
#
# Goes to the real oMLX server: this measures behavior, not tokens.
set -uo pipefail

PROFILE="${1:?perfil}"
REP="${2:-1}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
OMP_SRC="$HOME/github/vinicius91carvalho/oh-my-pi"
BUN="$HOME/.local/share/mise/installs/bun/1.4.0/bin/bun"
CFG="$HERE/profiles/$PROFILE.yml"
OUT="$HERE/results/$PROFILE-rep$REP"
mkdir -p "$OUT"
: > "$OUT/scores.jsonl"

while IFS= read -r line; do
  ID=$(printf '%s' "$line" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
  AXIS=$(printf '%s' "$line" | python3 -c 'import json,sys; print(json.load(sys.stdin)["axis"])')
  PROMPT=$(printf '%s' "$line" | python3 -c 'import json,sys; print(json.load(sys.stdin)["prompt"])')
  CHECK=$(printf '%s' "$line" | python3 -c 'import json,sys; print(json.load(sys.stdin)["check"])')

  WORK="$OUT/$ID"
  rm -rf "$WORK"; cp -R "$HERE/fixture" "$WORK"

  START=$(python3 -c 'import time; print(time.time())')
  # A stuck task must not block the sweep: kill it and score it as a failure.
  (cd "$WORK" && perl -e "alarm ${TASK_TIMEOUT:-900}; exec @ARGV" "$BUN" "$OMP_SRC/packages/coding-agent/src/cli.ts" \
      -p --model omlx/Qwen3.8-27B-AWQ-5.0bpw --no-session --auto-approve --config "$CFG" \
      "$PROMPT" </dev/null >answer.txt 2>stderr.txt) || true
  END=$(python3 -c 'import time; print(time.time())')

  if (cd "$WORK" && eval "$CHECK") >/dev/null 2>&1; then PASS=1; else PASS=0; fi
  python3 - "$ID" "$AXIS" "$PASS" "$START" "$END" >>"$OUT/scores.jsonl" <<'PY'
import json, sys
_, tid, axis, ok, start, end = sys.argv
print(json.dumps({"id": tid, "axis": axis, "pass": bool(int(ok)), "seconds": round(float(end) - float(start), 1)}))
PY
  tail -1 "$OUT/scores.jsonl"
done < "$HERE/tasks.jsonl"

python3 - "$OUT/scores.jsonl" "$PROFILE" <<'PY'
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1])]
ok = sum(r["pass"] for r in rows)
print(f"\n{sys.argv[2]}: {ok}/{len(rows)} passaram, {round(sum(r['seconds'] for r in rows)/60,1)} min no total")
PY
