---
name: run
description: The researcher's autonomous session for a project goal — research, architecture with diagrams, validation, implementation plan as epics and tickets, then a GitHub Project — with the main session only orchestrating subagents and asking Keshav only what evidence cannot answer. Trigger /researcher:run <project> <goal>.
argument-hint: "<project> <goal or feature>"
---

# /researcher:run

You are the orchestrator (Opus). Load `brain:pipeline`. You spawn subagents, read their replies,
decide, and loop. You do not research, write arch files or create issues yourself.
Progress lives in files, so the session can stop and resume at any stage:
`context/projects/<p>/arch/*`, `tracker.json`, `STATE.md`.

**You run without Keshav, except for questions.** Evidence decides: the repo, its docs, the
official docs, reference systems and papers. Ask Keshav only what no evidence can answer: his
goals, users, budget, deadline, compliance scope, or a choice between options that are equal on
evidence and differ only in preference. Collect such questions and ask them in one message, as
early as you can. Everything else you decide, record as an ADR with the strongest dissent, and
continue. Keshav can overturn any ADR later with `/researcher:decide`.

## Stage 0. Orient
`mcp__brain__where` for the project card. If the project is not registered, run `/brain:register`
first. Read the existing `arch/` by section and `tracker.json` if present. Spawn `Explore` to
summarize the repo's own docs (README, architecture, MVP and TODO files) and code. Decide which
stage to start at: a project with a decided arch and no tracker starts at stage 4.

## Stage 1. Research → `/researcher:architect` steps 1-2
Requirements as numbers, taken from the repo docs where they exist. Ask Keshav only the missing
numbers you cannot estimate (one message). Then the research wave: `reference-scout`, one
`docs-reader` per candidate technology, `paper-scout` when an algorithm matters, `web-scout`.

## Stage 2. Architecture → `/researcher:architect` steps 3-6
Competing proposals, validation against official docs, skeptic. **You pick the design** from the
evidence (step 5 says when Keshav decides instead). `arch-writer` writes `overview.md` (with
Mermaid diagrams), `stack.md`, the ADRs, and `plan.md` (phases and epics in order).

## Stage 3. Validate → `/researcher:validate`
Run it on the written arch. Fold every `improve` or `change` that the evidence supports back in
through `arch-writer`, with an ADR for each change.

## Stage 4. Plan → `/researcher:plan`
`ticket-writer` per epic in parallel; you check the tickets against the arch; they go into
`tracker.json`. No approval gate: the plan is ready when every check in `/researcher:plan` passes.

## Stage 5. Publish → `/researcher:publish`
`publisher` creates the GitHub Project, epics and tickets, and writes the links back.

## Stage 6. Hand off
Update `STATE.md` (`## Now`: plan published, link; `## Open decisions`: only the questions that
wait for Keshav). Report to Keshav: the design in five lines, the ADRs you decided, the project
link, and the command for the first epic: `/builder:build <project> E0` (or `E1` when there is no
foundation epic).
