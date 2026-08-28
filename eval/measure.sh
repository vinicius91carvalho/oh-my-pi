#!/usr/bin/env bash
# Capture the exact request omp sends for one profile and count its tokens.
#
#   ./measure.sh <profile> [prompt] [cwd]
#
# A logging proxy on 1338 forwards to the oMLX server on 1337 and writes each
# request body to disk, so the numbers come from the real wire format, not from
# reading the prompt-assembly code.
set -euo pipefail

PROFILE="${1:?perfil}"
PROMPT="${2:-diga apenas OK}"
WORKDIR="${3:-$HOME/github/vinicius91carvalho/find-best-job}"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
OMP_SRC="$HOME/github/vinicius91carvalho/oh-my-pi"
BUN="$HOME/.local/share/mise/installs/bun/1.4.0/bin/bun"
MODELS="$HOME/.omp/agent/models.yml"
# RUNS_DIR separates measurement contexts: `runs` is the real project,
# `runs-fixture` is the benchmark's own repo. A token count only describes the
# session it was taken in, so the two never share a directory.
OUT="$HERE/${RUNS_DIR:-runs}/$PROFILE"
# Stubbed by default: the sweep only needs the request body, and a real cold
# prefill of 22k tokens costs minutes. STUB=0 forwards to the oMLX server.
STUB="${STUB:-1}"

CFG="$HERE/profiles/$PROFILE.yml"
[ -f "$CFG" ] || { echo "sem perfil: $CFG" >&2; exit 1; }

rm -rf "$OUT"; mkdir -p "$OUT"

# The tap has to be listening before omp resolves the provider.
if ! lsof -ti :1338 >/dev/null 2>&1; then
  TAP_OUT="$OUT" TAP_STUB="$STUB" nohup python3 "$HERE/tap.py" >"$HERE/runs/tap.log" 2>&1 &
  for _ in $(seq 1 40); do lsof -ti :1338 >/dev/null 2>&1 && break; sleep 0.25; done
else
  # Reuse the live tap but point it at this run's directory.
  lsof -ti :1338 | xargs kill 2>/dev/null || true
  sleep 0.5
  TAP_OUT="$OUT" TAP_STUB="$STUB" nohup python3 "$HERE/tap.py" >"$HERE/runs/tap.log" 2>&1 &
  for _ in $(seq 1 40); do lsof -ti :1338 >/dev/null 2>&1 && break; sleep 0.25; done
fi

# A second provider pointing at the tap, added for this run and always removed.
cp "$MODELS" "$MODELS.measure.bak"
restore() { mv -f "$MODELS.measure.bak" "$MODELS" 2>/dev/null || true; }
trap restore EXIT
cat >> "$MODELS" <<'YML'
  omlxaudit:
    baseUrl: http://127.0.0.1:1338/v1
    api: openai-completions
    auth: none
    models:
      - id: Qwen3.8-27B-AWQ-5.0bpw
        name: Qwen3.8 27B (audit tap)
        reasoning: true
        input: [text, image]
        contextWindow: 30000
        maxTokens: 4096
        cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 }
YML

# Run from $WORKDIR so omp discovers that project's context files. Bun resolves
# imports from the entry file's own tree, so node_modules still comes from the
# omp checkout. `bun --cwd` would move omp's cwd too and it would read the omp
# repo's own AGENTS.md instead.
cd "$WORKDIR"
"$BUN" "$OMP_SRC/packages/coding-agent/src/cli.ts" \
  -p --model omlxaudit/Qwen3.8-27B-AWQ-5.0bpw --no-session --config "$CFG" \
  "$PROMPT" </dev/null >"$OUT/answer.txt" 2>"$OUT/stderr.txt" || true

REQ="$(ls -1 "$OUT"/req-*.json 2>/dev/null | head -1 || true)"
[ -n "$REQ" ] || { echo "nada capturado; veja $OUT/stderr.txt" >&2; tail -20 "$OUT/stderr.txt" >&2; exit 1; }

if [ "$STUB" = "1" ]; then
  "$HERE/.venv/bin/python" "$HERE/count_local.py" "$REQ" | tee "$OUT/tokens.json"
else
  python3 "$HERE/count.py" "$REQ" | tee "$OUT/tokens.json"
fi
