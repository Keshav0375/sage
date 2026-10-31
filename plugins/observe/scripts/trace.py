"""Append one JSON line per hook event to <trace_dir>/<yyyy-mm-dd>.jsonl.

Reads the hook input from stdin. Never blocks the session: any error exits 0.
"""

import datetime
import json
import os
import sys


def trace_dir() -> str:
    configured = os.environ.get("CLAUDE_PLUGIN_OPTION_TRACE_DIR", "").strip()
    if configured:
        return os.path.expanduser(configured)
    return os.path.join(os.environ.get("CLAUDE_PLUGIN_DATA", "."), "traces")


def record(event: dict) -> dict:
    name = event.get("hook_event_name", "")
    row = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "event": name,
        "session": event.get("session_id"),
        "cwd": event.get("cwd"),
    }
    if event.get("agent_id"):
        row["agent_id"] = event.get("agent_id")
    if event.get("agent_type"):
        row["agent_type"] = event.get("agent_type")
    if name == "PostToolUse":
        row["tool"] = event.get("tool_name")
        response = event.get("tool_response")
        if isinstance(response, dict):
            row["ok"] = not (response.get("is_error") or response.get("isError") or response.get("error"))
    return row


def main() -> None:
    try:
        event = json.load(sys.stdin)
        row = record(event)
        directory = trace_dir()
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, datetime.date.today().isoformat() + ".jsonl")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
    except Exception:
        pass


if __name__ == "__main__":
    main()
