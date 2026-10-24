---
name: audit
description: Harness health check — context budget (what loads every turn), unused skills/agents, MCP count, settings drift. Run monthly or when sessions feel slow. Trigger /audit.
---

# /audit

1. `python3 bin/sagectl audit --days 30`. Budget is 15K tokens for sage-owned context.
2. Ask Keshav to run `/context` once and paste the total. The CLI only estimates sage's share.
3. `/mcp` to list connected servers. More than ~5 always-on servers is a smell; per-project ones
   belong in that project's `[mcp]` notes, not global `.mcp.json`.
4. Propose cuts: unused 30d skills/agents → retire via `agent-smith` RETIRE or trash; bloated
   CLAUDE.md/ground-rules lines that never prevented anything → delete. Deletion is a valid edit.
5. Reply: total vs budget, top 3 cuts, expected savings. Bloat posts on Reddit report big speedups
   after cleanup (one user cut 63% of their setup). Treat that as anecdote, measure ours.
