#!/usr/bin/env bash
# Analyze and independently verify every kubelb claim from the committed
# results/hits.jsonl. No cluster needed. To regenerate raw hits on a real cluster:
#   python tools/run_bench.py   (requires kubectl context to a running cluster)
set -euo pipefail
cd "$(dirname "$0")"
PY=.venv/bin/python; [ -x "$PY" ] || PY=python3
$PY tools/analyze.py
$PY tools/verify.py
