---
name: plan
description: Turn a feature or task into reviewed build plans — research, one planner per task, an independent plan check — before any code is written. Trigger /build:plan <task>.
argument-hint: "<task or feature>"
---

# /build:plan

1. **Card.** Get the project with `mcp__base__where`. Halt on an open decision in `STATE.md`
   that the task depends on.
2. **Split.** Break the work into tasks that can each be built and verified alone. Mark which
   tasks are independent (one wave) and which depend on others.
3. **Research (one message, in parallel).** `think:docs-reader` for each library or service the
   tasks rely on; `Explore` for the code they touch.
4. **Plan (one message, one planner per independent task).** Spawn `build:planner` for each,
   with the task, its criteria and the research evidence.
5. **Check the plans.** For each plan, spawn a fresh `build:reviewer` with the plan (not a diff):
   does it meet the criteria, match `arch/`, and leave no decision to the builder?
6. **Report** the waves, the plan paths, and any `HALT` or `GAP` that needs Keshav.
