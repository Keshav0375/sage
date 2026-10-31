# time (in plugins/ui)

Terminal UI mod for Claude Code. Pins one status line under the prompt (`$.ui.status`), next to
Claude Code's own notices, so it is always in view:

```
00:37  │  today 67k tok  │  all-time 1.21B tok  │  session $0.33  │  ctx 7%  │  5h 44% 7d 17%
```

- **Clock**: local time, updated twice a minute.
- **Tokens** (input + output + cache read + cache write, as the API bills them):
  - history: `scripts/history.py` sums every transcript in `~/.claude/projects`, main sessions
    and subagents, each API response once. Re-run every 10 minutes. This includes sessions from
    before the plugin was installed.
  - live: each model response of this session, saved to `$.store` as `u:<day>:<session>`, so
    the line moves at once. Per session-day, the higher value of each count wins.
- **session $**: this session's cost. Turn off with the `show_cost` option.
- **ctx**: context window use. **5h / 7d**: rate-limit windows.

Why the total is lower than `/usage`: a transcript writes one line per content block, and each
line repeats the response's usage. Counting lines (as `/usage` appears to) counts most responses
two or more times; this plugin counts each response once.

Planned: project pane, gate band, lesson toast, theme.
