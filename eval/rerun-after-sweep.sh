#!/usr/bin/env bash
# Runs that overlapped Docker memory pressure (VM ~21 GB, swap 10-16 GB):
# all of p3k (07:59-09:30), and p5k ts-hard + ts-veryhard (11:18-11:45, the
# latter aborted by the oMLX memory guard). Re-run them once the sweep is over.
cd "$(dirname "$0")"
until grep -q SWEEP-DONE results-real/sweep.log; do sleep 60; done
mkdir -p results-real/docker-affected
cp -R results-real/p3k results-real/docker-affected/p3k
for id in ts-hard ts-veryhard; do cp -R "results-real/p5k/$id" "results-real/docker-affected/p5k-$id"; done
./run-real.sh p3k 2>&1 | tee results-real/p3k-rerun.log
for id in ts-hard ts-veryhard; do
  grep -v "\"id\": \"$id\"" results-real/p5k/scores.jsonl > results-real/p5k/scores.tmp && mv results-real/p5k/scores.tmp results-real/p5k/scores.jsonl
  ./run-real.sh p5k "$id" 2>&1 | tee -a results-real/p5k-rerun.log
done
echo RERUN-DONE >> results-real/sweep.log
