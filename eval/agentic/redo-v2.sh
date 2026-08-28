#!/usr/bin/env bash
# Re-run the round-2 entries in results-real-v2/redo.txt after a fresh server:
# runs that hit the bloated-process rejections or the wrong base branch.
cd "$(dirname "$0")"
until grep -q SWEEP2-DONE results-real/sweep.log; do sleep 60; done
export OMP_SRC="$HOME/github/vinicius91carvalho/oh-my-pi-pr" RESULTS_DIR="$PWD/results-real-v2"
launchctl kickstart -k "gui/$(id -u)/org.nix-community.home.omlx"
for _ in $(seq 1 120); do curl -sf -m 3 http://127.0.0.1:1337/v1/models >/dev/null && break; sleep 5; done
echo "omlx restarted for redo $(date +%H:%M)" | tee -a results-real/sweep.log
mkdir -p results-real-v2/redone
while read -r prof id; do
  [ -n "$id" ] || continue
  [ -d "results-real-v2/$prof/$id" ] && cp -R "results-real-v2/$prof/$id" "results-real-v2/redone/$prof-$id-first"
  grep -v "\"id\": \"$id\"" "results-real-v2/$prof/scores.jsonl" > "results-real-v2/$prof/scores.tmp" && mv "results-real-v2/$prof/scores.tmp" "results-real-v2/$prof/scores.jsonl"
  case "$id" in ts-rename|ts-contract) BUGS_FILE="$PWD/real/bugs-lsp.jsonl" ./run-real.sh "$prof" "$id" ;; *) ./run-real.sh "$prof" "$id" ;; esac 2>&1 | tee -a results-real-v2/redo.log
done < results-real-v2/redo.txt
echo REDO2-DONE >> results-real/sweep.log
