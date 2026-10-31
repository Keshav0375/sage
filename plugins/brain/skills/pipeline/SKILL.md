---
name: pipeline
description: The orchestration protocol for the researcher and builder agents — the main session (Opus) only orchestrates and decides; subagents (Sonnet) research, write, build and check, fanned out in parallel; no subagent owns more than one step. Use for any non-trivial task.
---

# Orchestration protocol

## Roles
- **Main session = orchestrator.** It runs on Opus (the brain mod forces it). It splits the work,
  spawns subagents, reads their replies, decides, and loops. It does not do the research,
  writing, editing or testing itself.
- **Subagents = workers.** Each does one small, well-specified task on Sonnet and returns a typed
  reply (its status keyword first). They do not spawn further subagents.

## The five steps, each with a different owner
1. **Research**: scouts gather evidence from different sources, in parallel.
2. **Decide**: the main session, from at least two independent proposals when there is a real
   tradeoff, after a skeptic checks the leading one. Open decisions go to Keshav.
3. **Do**: a writer or editor subagent produces the change.
4. **Verify**: subagents that did not do the work check it (review, tests, architecture).
5. **Declare**: a verifier gives the verdict from the other agents' evidence; the main session
   reports it to Keshav. Nobody declares from their own work.

## How to spawn
- Independent tasks go out in **one message**, so they run in parallel.
- Give each subagent everything it needs in the prompt: the goal, the inputs (paths, keys, arch
  sections), the output format, and where to write files. Subagents do not see this
  conversation.
- Keep each task small and concrete. If a subagent replies `GAP` or `HALT`, the main session
  resolves it (or asks Keshav) and spawns again. It never fills the gap itself.
- Loop until the verifier says `GREEN`, or stop after three loops and report.

## Model routing
Main loop: Opus, always. Subagents: Sonnet by default (the `subagent_model` option).
`context/routing.json` overrides per subagent type; a `model` on the Agent call wins over both.

## The two agents
- **researcher** (`/researcher:run`): research → architecture with diagrams in
  `context/projects/<p>/arch/` → validation → epics and tickets in `tracker.json` → GitHub Project.
- **builder** (`/builder:build`): one epic from `tracker.json` → fetch → branch → edit →
  review, test and arch check in parallel → verify → loop → PR.
