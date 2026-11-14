#!/usr/bin/env python3
"""Block personal data from reaching git: phone numbers, personal emails, PDFs, raw job dumps.

Hook mode (PreToolUse on Bash): reads the event on stdin; for `git commit` / `git push` it scans the
staged files (commit) or the commits not yet on the remote (push) and denies with a reason.
CLI: pii_guard.py [--staged | --range A..B | FILE...]   → exit 1 when something is found.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import knobs as knobs_mod  # noqa: E402

RAW_DUMP = re.compile(r"(^|/)memory/resume/(runs|market/jobs|contact)")


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout


def files_staged() -> list[str]:
    return [f for f in _git("diff", "--cached", "--name-only", "--diff-filter=ACM").splitlines() if f]


def files_unpushed() -> list[str]:
    up = _git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}").strip()
    rng = f"{up}..HEAD" if up else "HEAD~20..HEAD"
    return sorted({f for f in _git("diff", "--name-only", "--diff-filter=ACM", rng).splitlines() if f})


def content_of(path: str, staged: bool) -> str:
    out = _git("show", f":{path}") if staged else ""
    if not out and Path(path).exists():
        try:
            out = Path(path).read_text(encoding="utf-8", errors="ignore")
        except (IsADirectoryError, OSError):
            out = ""
    return out


def scan(paths: list[str], staged: bool = False) -> list[str]:
    k, _ = knobs_mod.load()
    pv = k["privacy"]
    pats = [re.compile(p) for p in pv["block_patterns"]]
    hits: list[str] = []
    for p in paths:
        if any(p.startswith(a) for a in pv["allow_paths"]):
            continue
        if any(p.lower().endswith(ext) for ext in pv["block_extensions"]):
            hits.append(f"{p}: file type blocked ({Path(p).suffix})")
            continue
        if RAW_DUMP.search(p):
            hits.append(f"{p}: private data folder")
            continue
        text = content_of(p, staged)
        for rx in pats:
            m = rx.search(text)
            if m:
                hits.append(f"{p}: matches {rx.pattern!r} ({m.group(0)[:4]}…)")
                break
    return hits


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:  # hook mode
        try:
            ev = json.load(sys.stdin)
        except Exception:
            return 0
        cmd = (ev.get("tool_input") or {}).get("command", "")
        if not re.search(r"\bgit\s+(commit|push)\b", cmd):
            return 0
        hits = scan(files_staged(), staged=True) if re.search(r"\bgit\s+commit\b", cmd) else scan(files_unpushed())
        if hits:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                     "permissionDecisionReason": "gimme-job PII guard:\n" + "\n".join(hits[:10])}}))
        return 0
    if argv[0] == "--staged":
        hits = scan(files_staged(), staged=True)
    elif argv[0] == "--range":
        hits = scan([f for f in _git("diff", "--name-only", argv[1]).splitlines() if f])
    else:
        hits = scan(argv)
    for h in hits:
        print(h)
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
