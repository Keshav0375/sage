---
name: run
description: The researcher's full session for a project goal — research, architecture with diagrams, validation, implementation plan as epics and tickets, then a GitHub Project — with the main session only orchestrating subagents and stopping at Keshav's gates. Trigger /researcher:run <project> <goal>.
argument-hint: "<project> <goal or feature>"
---

# /researcher:run

You are the orchestrator (Opus). Load `brain:pipeline`. You spawn subagents, read their replies,
decide, and loop. You do not research, write arch files or create issues yourself.
Progress lives in files, so the session can stop and resume at any stage:
`context/projects/<p>/arch/*`, `tracker.json`, `STATE.md`.

## Stage 0. Orient
`mcp__brain__where` for the project card. If the project is not registered, run `/brain:register`
first. Read the existing `arch/` by section and `tracker.json` if present. Decide which stage to
start at: a project with a decided arch and no tracker starts at stage 4.

## Stage 1. Research → `/researcher:architect` steps 1-2
Requirements as numbers (ask Keshav for missing ones in one message), then the research wave:
`reference-scout`, one `docs-reader` per candidate technology, `paper-scout` when an algorithm
matters, `web-scout`, `Explore` for existing code.

## Stage 2. Architecture → `/researcher:architect` steps 3-6
Competing proposals, validation against official docs, skeptic, your recommendation.
**Gate A: Keshav picks the design.** Then `arch-writer` writes `overview.md` (with Mermaid
diagrams), `stack.md`, the ADRs, and `plan.md` (phases and epics in order).

## Stage 3. Validate → `/researcher:validate`
Run it on the written arch. Fold accepted improvements back in through `arch-writer` (after
Keshav agrees to each change).

## Stage 4. Plan → `/researcher:plan`
`ticket-writer` per epic in parallel; you check the tickets against the arch; they go into
`tracker.json`. **Gate B: Keshav approves the epics and tickets.**

## Stage 5. Publish → `/researcher:publish`
`publisher` creates the GitHub Project, epics and tickets, and writes the links back.

## Stage 6. Hand off
Update `STATE.md` (`## Now`: plan published, link; `## Open decisions`). Tell Keshav which epic
is ready first, and the command: `/builder:build <project> <epic>`.
