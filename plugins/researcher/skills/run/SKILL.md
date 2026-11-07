---
name: run
description: The researcher's autonomous session for a project goal — research, architecture with diagrams, validation, implementation plan as epics and tickets, then a GitHub Project — with the main session only orchestrating subagents and asking Keshav only what evidence cannot answer. Trigger /researcher:run <project> <goal>.
argument-hint: "<project> <goal or feature>"
---

# /researcher:run

You are the orchestrator (Opus). Load `brain:pipeline`. You spawn subagents, read their replies,
decide, and loop. You do not research, write arch files or create issues yourself.
Progress lives in files, so the session can stop and resume at any stage:
`projects/<p>/arch/*`, `epic/`, `state.md`.

**You run without Keshav, except for questions.** Evidence decides: the repo, its docs, the
official docs, reference systems and papers. Ask Keshav only what no evidence can answer: his
goals, users, budget, deadline, compliance scope, or a choice between options that are equal on
evidence and differ only in preference. Collect such questions and ask them in one message, as
early as you can. Everything else you decide, record as an ADR with the strongest dissent, and
continue. Keshav can overturn any ADR later with `/researcher:decide`.

**Run state and handoffs.** At the start, call `mcp__brain__run_update` with the goal, `stage`
and `status: active`; update `stage`, `step` and `next` at every stage and wave boundary, and set
`status: done` at the end. The mod keeps this state across compaction and usage-limit stops, so
the run goes from stage 0 to stage 6 in one go: no hard stop between stages and no resume command
for Keshav. A refused tool call from an agent (a guard or permission message) is a harness
defect: fix the config the message names when it is under `projects/`, else report it, and resume
the agent by SendMessage. Agent questions are answered by you (see `brain:pipeline` rule 6).

## Stage 0. Orient
`mcp__brain__where` for the project card. If the project is not registered, run `/brain:register`
first. Read the existing `arch/` by section and `epic/` if present. Spawn `Explore` to
summarize the repo's own docs (README, architecture, MVP and TODO files) and code. Decide which
stage to start at: a project with a decided arch and no epics starts at stage 4.

## Stage 1. Research → `/researcher:architect` steps 1-2
Requirements as numbers, taken from the repo docs where they exist. Ask Keshav only the missing
numbers you cannot estimate (one message). Then the research wave: `reference-scout`, one
`docs-reader` per candidate technology, `paper-scout` when an algorithm matters, `web-scout`.

## Stage 2. Architecture → `/researcher:architect` steps 3-6
Competing proposals, validation against official docs, skeptic. **You pick the design** from the
evidence (step 5 says when Keshav decides instead). `arch-writer` writes `architecture.md`, `architecture-diagram.md` (Mermaid; every node names its
deep-dive file), `deep-dive/*.md` (with the tech stack), `decision-logs.md`, `arch/state.md` and
`epic/plan.md` (phases and epics in order).

## Stage 3. Validate → `/researcher:validate`
Run it on the written arch. Fold every `improve` or `change` that the evidence supports back in
through `arch-writer`, with an ADR for each change.

## Stage 4. Plan → `/researcher:plan`
`ticket-writer` per epic in waves of ≤ 4 with per-epic slices; you check the tickets against the arch; the
ticket-writers write them as files in `epic/<E>-<slug>/tickets/`. No approval gate: the plan is ready when every check in `/researcher:plan` passes.

## Stage 5. Publish → `/researcher:publish`
Part of the run, not a separate approval: it starts when the stage 4 checks pass, unless the
run's brief says not to publish. For an already published plan, publish applies the diff
(update, close, new) the plan stage wrote.
`publisher` creates the GitHub Project, epics and tickets, and writes the links back into the epic and ticket files.

## Stage 6. Hand off
Update `state.md` (`## Now`: plan published, link; `## Open decisions`: only the questions that
wait for Keshav). Report to Keshav: the design in five lines, the ADRs you decided, the project
link, and the command for the first epic: `/builder:build <project> E0` (or `E1` when there is no
foundation epic).
