---
name: pipeline
description: The orchestration protocol for the researcher and builder agents — the main session (Opus) only orchestrates and decides; depth-1 subagents (Opus for research and design reasoning, Sonnet for all other work) research, write, build and check; depth-2 Sonnet leaves only read and quote. Work runs in dependency waves (parallel only when inputs are independent), with token rules. Use for any non-trivial task.
---

# Orchestration protocol

## Roles and model tiers
| Depth | Who | Model | Does |
|---|---|---|---|
| 0 | Main session (orchestrator) | Opus (brain mod forces it) | Splits work, decides, records decisions. Never researches, writes arch, edits code or runs tests itself. |
| 1 | Reasoning and research agents | Opus | solution-architect, skeptic, docs-reader, reference-scout, paper-scout. |
| 1 | All other work and coordination | Sonnet | arch-writer, ticket-writer, web-scout, publisher, fetcher, editor (every fix loop too), code-reviewer, security-reviewer, warden, verifier, brancher, runner, Explore. |
| 2 | Leaves (spawned by a depth-1 agent) | Sonnet, forced | `researcher:page-reader` (read one source, quote), `Explore` (find code). Nothing else may be spawned at depth 2; leaves spawn nothing. |

The tier lives in each agent's frontmatter and in `projects/routing.json`; the brain mod enforces depth 2.
Keshav's rule (2026-11-21): Opus only for reasoning and research; everything else on Sonnet; no
Haiku (Haiku runners and branchers caused rework that cost more than they saved). Save tokens with
short prompts, short replies and reports on disk, not with a weaker model.

## The five steps, each with a different owner
1. **Research**: scouts gather evidence; readers delegate page reading to Haiku leaves.
2. **Decide**: the main session, from at least two independent proposals when there is a real
   tradeoff, after a skeptic checks the leading one. It records each decision as an ADR. Only
   questions that evidence cannot answer (goals, scope, compliance, money) go to Keshav.
3. **Do**: a writer or editor subagent produces the change.
4. **Verify**: subagents that did not do the work check it (review, tests, architecture).
5. **Declare**: a verifier gives the verdict from the other agents' evidence; the main session
   reports it to Keshav. Nobody declares from their own work.

## Waves: parallel only when inputs are independent
- Before spawning, write the dependency graph of the step in one line (`A, B → C → D, E`). Agents
  that need another agent's output wait for it; agents with independent inputs share a wave.
- Wave size: at most **3 depth-1 agents at a time** (each may run up to 2 leaves). A bigger set
  runs in successive waves of 4. Bursts of large parallel reads are what exhaust the usage window.
- Prefer **one agent with a clear list** over many agents with one item each when the items share
  the same inputs (one docs-reader for three related libraries, not three).
- **Cost line before every wave of 2 or more**: tell Keshav one line — agents, tier, rough tokens
  (≈ 100k per Sonnet reader, ≈ 30k per Haiku leaf, writers ≈ size of the files they touch × calls).
  Continue unless he objects.
- Loop until the verifier says `GREEN`, or stop after three loops and report.

## Token rules
1. **Files, not replies.** Every agent writes its full output to a file (research output in `projects/<p>/library/research/<round>/`, transient scratch under `projects/.runtime/`)
   and replies with the status keyword, the path and ≤ 8 lines. The orchestrator reads a file only
   for the part it needs (Grep, Read with offset/limit). Never paste an agent's long report back
   into another prompt: pass the path.
2. **Slices, not whole documents.** Give each agent the exact sections it needs
   (`deep-dive/05-data-model.md#tables`, `decision-logs.md#adr-004`), not "read the arch". Agents read by heading (Grep `^## `,
   then Read with offset/limit). Keep each deep-dive file under 250 lines.
3. **Resume, do not respawn.** A follow-up for an agent that already holds the context goes by
   SendMessage to that agent, not to a new one.
4. **One continuous run, automatic handoff.** Progress lives in files (`arch/*`, `epic/`,
   `state.md`, `library/`) and in the run state (`mcp__brain__run_update`: stage, step, next action).
   Update the run state at every stage and wave boundary. When the main-loop context passes the
   guard, the brain mod compacts the session by itself and keeps the run state; the run continues.
   Never ask Keshav to `/clear` or to type a resume command.
5. **Write by section.** Writers create or replace a whole section file in one write; they do not
   make many small edits to one large file (each call re-reads it).
6. **Keshav decides, agents do the rest.** Only questions about goals, scope, money, compliance
   or a pure preference go to Keshav, batched in one AskUserQuestion message; set the run status
   `waiting_keshav` while you wait and `active` after. Every other question an agent raises is
   answered by the orchestrator from the arch or with a reader, recorded in the round's decision
   file, and sent back to that agent by SendMessage. The `budget-guard` window line is an order:
   drop to one agent at a time.
7. **Write early.** Every agent writes its output file in its first turns and extends it, so a
   usage-limit stop loses nothing; a stopped agent is resumed by SendMessage, never respawned.
8. **Tiers are enforced.** `projects/routing.json` `tiers` sets model and effort per agent type and
   the brain mod applies them on every model request. Do not pass `model` on an Agent call unless
   you mean to override the tier for that one run.
9. **Measure.** After each stage, run `/observe:traces` and note tokens by agent type in `state.md`.

## How to spawn
- Give each subagent everything it needs in the prompt: the goal, the input paths and sections,
  the output path, and the reply format. Subagents do not see this conversation.
- Keep each task small and concrete. If a subagent replies `GAP` or `HALT`, the main session
  resolves it with research subagents and spawns again. It never fills the gap itself.

## The two agents
- **researcher** (`/researcher:run`): research → architecture with diagrams in
  `projects/<p>/arch/` → validation → epics and ticket files in `projects/<p>/epic/` → GitHub Project.
- **builder** (`/builder:build`): one epic from its ticket files → fetch → branch → edit →
  code review, security review, tests and arch check in parallel → verify → loop → PR → CI
  green. Keshav merges.
