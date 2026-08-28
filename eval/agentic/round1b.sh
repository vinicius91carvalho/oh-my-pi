#!/usr/bin/env bash
# Round 1b: redo every run that hit memory pressure (Docker VM, then a bloated
# oMLX process that rejected prefills at ~20k), after restarting the server.
cd "$(dirname "$0")"
R=results-real
# 1. wait for the last base bug to be scored, then stop the sweep before run-long
until grep -q '"id": "ts-veryhard"' "$R/base/scores.jsonl" 2>/dev/null; do sleep 30; done
pkill -f sweep.sh; sleep 2; pkill -f "run-long.sh"; pkill -f "cli.ts -p"; lsof -ti :1338 | xargs kill 2>/dev/null
# 2. restart oMLX (launchd agent), wait for /v1/models
launchctl kickstart -k "gui/$(id -u)/org.nix-community.home.omlx"
for _ in $(seq 1 120); do curl -sf -m 3 http://127.0.0.1:1337/v1/models >/dev/null && break; sleep 5; done
echo "omlx restarted $(date +%H:%M)" | tee -a "$R/sweep.log"
# 3. keep the pressured results aside, then re-run
mkdir -p "$R/docker-affected"
cp -R "$R/p3k" "$R/docker-affected/p3k"
for id in ts-hard ts-veryhard; do cp -R "$R/p5k/$id" "$R/docker-affected/p5k-$id"; done
for id in py-hard ts-hard; do cp -R "$R/base/$id" "$R/docker-affected/base-$id"; done
./run-real.sh p3k 2>&1 | tee "$R/p3k-rerun.log"
for id in ts-hard ts-veryhard; do
  grep -v "\"id\": \"$id\"" "$R/p5k/scores.jsonl" > "$R/p5k/scores.tmp" && mv "$R/p5k/scores.tmp" "$R/p5k/scores.jsonl"
  ./run-real.sh p5k "$id" 2>&1 | tee -a "$R/p5k-rerun.log"
done
for id in py-hard ts-hard; do
  grep -v "\"id\": \"$id\"" "$R/base/scores.jsonl" > "$R/base/scores.tmp" && mv "$R/base/scores.tmp" "$R/base/scores.jsonl"
  ./run-real.sh base "$id" 2>&1 | tee -a "$R/base-rerun.log"
done
mkdir -p results-long
for p in p3k p7k; do ./run-long.sh "$p" 2>&1 | tee "results-long/$p.log"; done
echo SWEEP-DONE >> "$R/sweep.log"
echo RERUN-DONE >> "$R/sweep.log"
