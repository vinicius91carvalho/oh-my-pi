#!/usr/bin/env bash
# Run the server by hand, with extra env, so a setting can be swept without a
# nix rebuild per value. The launchd agent must be booted OUT, not killed:
# KeepAlive.SuccessfulExit=false treats a SIGTERM as a crash and restarts it,
# and it then holds port 1337 with the flags from the nix file.
set -euo pipefail
AGENT="gui/$(id -u)/org.nix-community.home.omlx"
launchctl bootout "$AGENT" 2>/dev/null || true
for _ in $(seq 30); do
  pid=$(lsof -nP -iTCP:1337 -sTCP:LISTEN -t 2>/dev/null | head -1) || true
  [ -z "$pid" ] && break
  kill -TERM "$pid" 2>/dev/null || true
  sleep 1
done
rm -rf ~/.omlx/ssd-cache/*
nohup env "$@" /Applications/oMLX.app/Contents/MacOS/omlx-cli serve \
  --model-dir "$HOME/tools/qwen3.8-27b" --host 127.0.0.1 --port 1337 \
  --memory-guard-gb 27 --max-concurrent-requests 2 --hot-cache-max-size 2GB \
  --paged-ssd-cache-dir "$HOME/.omlx/ssd-cache" --paged-ssd-cache-max-size 60GB \
  >> "$HOME/Library/Logs/omlx-manual.log" 2>&1 &
until curl -s -m 3 http://127.0.0.1:1337/v1/models >/dev/null 2>&1; do sleep 2; done
sleep 3
echo "servidor manual de pe com: $*"
