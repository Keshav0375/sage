---
name: start
description: Show the session card for the active project (or switch project) — phase, tasks, waves, gate, open lessons, latest handoff — and suggest the next move. Trigger /start [project].
argument-hint: "[project]"
---

# /start

1. If a project was named: `python3 bin/sagectl use <project>`.
2. `python3 bin/sagectl card` and print it in a code block.
3. Latest `.sage/handoffs/*.md`? Show its NEXT line.
4. Suggest exactly one next move (e.g. "phase 2 wave 1 is ready, `/build`", "3 open lessons
   on auth, `/retro` first", "no arch yet, `/spec`").
