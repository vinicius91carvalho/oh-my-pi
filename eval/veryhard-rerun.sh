#!/usr/bin/env bash
# After the fixture: add the "Rule first" line to the compact template (commit 6
# candidate) and re-run the very-hard bugs on p7k and p3k. The hidden test decides.
cd "$(dirname "$0")"
until grep -q FIXTURE-DONE results-real/sweep.log; do sleep 60; done
( cd "$HOME/github/vinicius91carvalho/oh-my-pi-pr/packages/coding-agent" && python3 "/private/tmp/claude-501/-Users-vinicius91carvalho-tools-qwen3-8-27b/ab826691-e41c-42e0-8d2c-498c9afd6559/scratchpad/rule-first.py" )
export OMP_SRC="$HOME/github/vinicius91carvalho/oh-my-pi-pr" RESULTS_DIR="$PWD/results-real-v3"
mkdir -p "$RESULTS_DIR"
for p in p7k p3k; do for id in py-veryhard ts-veryhard; do ./run-real.sh "$p" "$id" 2>&1 | tee -a "$RESULTS_DIR/$p.log"; done; done
echo VERYHARD-DONE >> results-real/sweep.log
