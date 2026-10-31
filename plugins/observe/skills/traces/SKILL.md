---
name: traces
description: Summarize recent traces — tool calls and failures by tool, subagent runs by type, sessions per project directory. Read-only. Trigger /observe:traces [days].
argument-hint: "[days, default 7]"
---

# /observe:traces

1. Find the trace folder: the observe plugin option `trace_dir`, else `context/.runtime/traces/`.
2. Read the last N days of `<yyyy-mm-dd>.jsonl` files (default 7). Use a short `python3` or `jq`
   command; do not read the files into context whole.
3. Report: tool calls per tool with failure counts (`ok: false`), subagent stops per
   `agent_type`, turns per session, and the top 3 tools by failure rate.
4. Point out patterns worth a lesson or a rule change. Do not change any rule yourself.
