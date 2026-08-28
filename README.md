# Local-model eval for the compact prompt fork

Everything behind the numbers in the `compact-prompt-for-local-models` PR: profiles, runners, the logging proxy, every captured request, and the write-ups.

- `eval/deliverables/` - benchmark.md, modes.md, and the public texts
- `eval/profiles/` - the four modes as `--config` files (`p7k`, `p5k`, `p3k`, `base`, plus `*-long`)
- `eval/run-real.sh`, `eval/run-long.sh`, `eval/table-compare.py`, `eval/tools-used.py`, `eval/tap.py`
- `eval/results-real*/`, `eval/results-long*/` - per-run `req-NNN.json` (exact wire request), `usage-NNN.json` (server usage), `agent.diff`, `test.log`, `scores.jsonl`
- `eval/real/` - the seeded bugs (`bugs.jsonl`, `bugs-lsp.jsonl`, hidden tests); the repos themselves are private worktrees and are not included
- `eval/results-B*.json`, `eval/bench.py` - the oMLX tuning bench (MTP, TurboQuant, ANE)

Machine: MacBook Pro M3 Max 14/30, 36 GB. Server: oMLX 0.6.3rc3, Qwen3.8-27B-AWQ-5.0bpw, 30k window.
