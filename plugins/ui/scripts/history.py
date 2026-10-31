"""Sum token usage from Claude Code session transcripts, per session and local day.

Reads every *.jsonl under the projects folder (main sessions and subagents). A transcript writes
one line per content block, and each line repeats the response's usage, so each API response is
counted once: per message id, the highest value of each count (a later line can carry the final
output count). Prints JSON:
  {"<sessionId>": {"<yyyy-mm-dd>": {"input": n, "output": n, "cacheRead": n, "cacheWrite": n}}}

Usage: python3 history.py [projects_dir]   (default ~/.claude/projects)
"""

import datetime
import json
import os
import sys


def local_day(ts: str) -> str:
    t = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return t.astimezone().date().isoformat()


def scan(root: str) -> dict:
    responses: dict = {}
    for dirpath, _, files in os.walk(root):
        for name in files:
            if not name.endswith(".jsonl"):
                continue
            try:
                f = open(os.path.join(dirpath, name), encoding="utf-8", errors="replace")
            except OSError:
                continue
            with f:
                for line in f:
                    if '"usage"' not in line:
                        continue
                    try:
                        d = json.loads(line)
                    except ValueError:
                        continue
                    msg = d.get("message") or {}
                    usage = msg.get("usage")
                    if d.get("type") != "assistant" or not isinstance(usage, dict) or not d.get("timestamp"):
                        continue
                    key = msg.get("id") or (name, d.get("uuid"))
                    counts = (
                        usage.get("input_tokens") or 0,
                        usage.get("output_tokens") or 0,
                        usage.get("cache_read_input_tokens") or 0,
                        usage.get("cache_creation_input_tokens") or 0,
                    )
                    prev = responses.get(key)
                    if prev:
                        counts = tuple(max(a, b) for a, b in zip(prev[2], counts))
                        responses[key] = (prev[0], prev[1], counts)
                    else:
                        sid = d.get("sessionId") or d.get("session_id") or "unknown"
                        responses[key] = (sid, local_day(d["timestamp"]), counts)
    out: dict = {}
    for sid, day, (i, o, cr, cw) in responses.values():
        b = out.setdefault(sid, {}).setdefault(day, {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0})
        b["input"] += i
        b["output"] += o
        b["cacheRead"] += cr
        b["cacheWrite"] += cw
    return out


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/.claude/projects")
    json.dump(scan(root), sys.stdout, separators=(",", ":"))
