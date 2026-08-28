#!/usr/bin/env bash
# Fixture again for p7k on the fixed fixture (clean tree check was impossible before), after the very-hard rerun.
cd "$(dirname "$0")"
until grep -q VERYHARD-DONE results-real/sweep.log; do sleep 60; done
export OMP_SRC="$HOME/github/vinicius91carvalho/oh-my-pi-pr"
RESULT_NAME=p7k-v6 ./run-tasks.sh p7k 1 2>&1 | tee results/p7k-v6-rep1.log
echo FIXTURE2-DONE >> results-real/sweep.log
