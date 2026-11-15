#!/usr/bin/env bash
# Run before every commit/push: all tests + PII guard on staged files. Exit non-zero stops the commit.
set -euo pipefail
PLUGIN="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
out="$(cd "$PLUGIN" && python3 -m unittest discover -s tests -t . -p 'test_*.py' 2>&1 | tail -3)"
echo "$out"
echo "$out" | grep -q '^OK' || { echo "check.sh: tests failed — not committing" >&2; exit 1; }
(cd "$PLUGIN" && python3 scripts/pii_guard.py --staged) || { echo "check.sh: PII guard blocked staged files" >&2; exit 1; }
echo "check.sh: OK"
