#!/usr/bin/env bash
# Fixture (12 tasks) again for p7k with the current fork, after the long sessions.
cd "$(dirname "$0")"
true
export OMP_SRC="$HOME/github/vinicius91carvalho/oh-my-pi-pr"
RESULT_NAME=p7k-v5 ./run-tasks.sh p7k 1 2>&1 | tee results/p7k-v5-rep1.log
echo FIXTURE-DONE >> results-real/sweep.log
