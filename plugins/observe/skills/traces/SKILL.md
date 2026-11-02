---
name: traces
description: Summarize recent traces and token usage — tool calls and failures by tool, subagent runs by type, tokens by subagent type, model and spawn depth, and the main loop's share. Saves the report under the trace folder. Read-only on the code. Trigger /observe:traces [days].
argument-hint: "[days, default 7]"
---

# /observe:traces

1. Find the trace folder: the observe plugin option `trace_dir`, else `context/.runtime/traces/`.
2. **Tokens.** Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/usage.py --days <N> --out <trace folder>`.
   It reads the Claude Code transcripts (main loop and every subagent, with type, depth and model)
   and writes `usage-<date>.md` and `usage-<date>.json` to the trace folder. Use its tables; do not
   read transcripts into context.
3. **Events.** Read the last N days of `<yyyy-mm-dd>.jsonl` with a short `python3` or `jq` command:
   tool calls per tool with failure counts (`ok: false`), subagent stops per `agent_type`, turns
   per session. Rows with `tokens` (SubagentStop = that agent; Stop = the session so far, take the
   last row per session) give live usage between reports.
4. Report: tokens by agent type, model and depth; the main loop's share; the top 3 agent types by
   cache read; the top 3 tools by failure rate.
5. Point out savings that follow the `brain:pipeline` token rules (an agent type on a tier above its
   need, large repeated reads, long replies pasted into the main loop, waves larger than 4). Do not
   change any rule yourself.
