#!/usr/bin/env bash
# Both round-2 long sessions ran on a worktree whose packages/core/dist was
# built from another branch (tests died with a missing import). Re-run them
# after the redo runner, on a fresh server, with the self-healing setup.
cd "$(dirname "$0")"
until grep -q REDO2-DONE results-real/sweep.log; do sleep 60; done
export OMP_SRC="$HOME/github/vinicius91carvalho/oh-my-pi-pr"
mkdir -p results-long-v2/broken-dist
for p in p3k-long p7k-long; do [ -d "results-long-v2/$p" ] && mv "results-long-v2/$p" "results-long-v2/broken-dist/$p"; done
launchctl kickstart -k "gui/$(id -u)/org.nix-community.home.omlx"
for _ in $(seq 1 120); do curl -sf -m 3 http://127.0.0.1:1337/v1/models >/dev/null && break; sleep 5; done
echo "omlx restarted for long-session redo $(date +%H:%M)" | tee -a results-real/sweep.log
for p in p3k-long p7k-long; do RESULTS_DIR="$PWD/results-long-v2" ./run-long.sh "$p" 2>&1 | tee "results-long-v2/$p.log"; done
echo LONG2-DONE >> results-real/sweep.log
