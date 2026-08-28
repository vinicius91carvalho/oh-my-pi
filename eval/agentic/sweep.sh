#!/usr/bin/env bash
# Full real-project sweep, then the long-session runs. Sequential: one
# model on one machine, so parallel runs would only fight for memory.
cd "$(dirname "$0")"
for p in p3k p7k p5k base; do ./run-real.sh "$p" 2>&1 | tee "results-real/$p.log"; done
mkdir -p results-long
for p in p3k p7k; do ./run-long.sh "$p" 2>&1 | tee "results-long/$p.log"; done
echo SWEEP-DONE
