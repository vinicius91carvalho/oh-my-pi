#!/usr/bin/env bash
# Round 2: same 8 bugs + 2 LSP tasks, all four modes, with (a) language servers
# installed (none existed in round 1, so no mode could use `lsp`), and (b) the
# fourth fork commit: xd:// references in the compact profile, a worked device
# call in the device docs, factored MCP catalog rows.
cd "$(dirname "$0")"
until grep -q RERUN-DONE results-real/sweep.log; do sleep 60; done
export OMP_SRC="$HOME/github/vinicius91carvalho/oh-my-pi-pr"
export RESULTS_DIR="$PWD/results-real-v2"
mkdir -p "$RESULTS_DIR" results-long-v2
{
  echo "== LSP servers"
  npm ls -g --depth=0 2>/dev/null | grep -E "typescript-language-server|pyright" || npm i -g typescript-language-server typescript pyright 2>&1 | tail -2
  which typescript-language-server pyright-langserver
} | tee "$RESULTS_DIR/setup.log"
for p in p7k p5k p3k base; do ./run-real.sh "$p" 2>&1 | tee "$RESULTS_DIR/$p.log"; done
for p in p7k p5k p3k base; do
  BUGS_FILE="$PWD/real/bugs-lsp.jsonl" ./run-real.sh "$p" ts-rename 2>&1 | tee -a "$RESULTS_DIR/$p.log"
  BUGS_FILE="$PWD/real/bugs-lsp.jsonl" ./run-real.sh "$p" ts-contract 2>&1 | tee -a "$RESULTS_DIR/$p.log"
done
# Long sessions: fresh server (the process grows with uptime and aborts at the
# 24.9 GB watermark near 22-24k tokens) and profiles that compact at 20k.
launchctl kickstart -k "gui/$(id -u)/org.nix-community.home.omlx"
for _ in $(seq 1 120); do curl -sf -m 3 http://127.0.0.1:1337/v1/models >/dev/null && break; sleep 5; done
echo "omlx restarted for long sessions $(date +%H:%M)" | tee -a results-real/sweep.log
for p in p3k-long p7k-long; do RESULTS_DIR="$PWD/results-long-v2" ./run-long.sh "$p" 2>&1 | tee "results-long-v2/$p.log"; done
echo SWEEP2-DONE >> results-real/sweep.log
