#!/usr/bin/env bash
# Run one configuration end to end: apply settings, restart cold, measure.
#
# The order matters. Clearing the SSD cache under a running server wedges it
# (the layer-cache signature no longer matches what it has open), so the server
# is stopped first, then the cache is cleared, then it comes back.
set -euo pipefail
LABEL="$1"; shift
AGENT="gui/$(id -u)/org.nix-community.home.omlx"

launchctl kill SIGTERM "$AGENT" 2>/dev/null || true
until ! curl -s -m 2 http://127.0.0.1:1337/v1/models >/dev/null 2>&1; do sleep 1; done
rm -rf ~/.omlx/ssd-cache/*

if [ "$#" -gt 0 ]; then
  python3 ~/tools/qwen3.8-27b/eval/setcfg.py "$@" >/dev/null
else
  launchctl kickstart -k "$AGENT"
fi

until curl -s -m 3 http://127.0.0.1:1337/v1/models >/dev/null 2>&1; do sleep 2; done
sleep 3
echo "== $LABEL: servidor pronto, medindo =="
python3 ~/tools/qwen3.8-27b/eval/bench.py "$LABEL"
