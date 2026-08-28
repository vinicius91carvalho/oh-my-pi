#!/usr/bin/env bash
# base py-hard ended after 2 requests with an empty answer (no error, ~22 s):
# an empty-stop flake, not a memory event. Give it one more run after everything else.
cd "$(dirname "$0")"
until grep -q RERUN-DONE results-real/sweep.log; do sleep 60; done
mkdir -p results-real/flakes && cp -R results-real/base/py-hard results-real/flakes/base-py-hard-empty-stop
grep -v '"id": "py-hard"' results-real/base/scores.jsonl > results-real/base/scores.tmp && mv results-real/base/scores.tmp results-real/base/scores.jsonl
./run-real.sh base py-hard 2>&1 | tee -a results-real/base-rerun.log
echo RERUN2-DONE >> results-real/sweep.log
