---
name: pipeline
description: The orchestration protocol for the researcher and builder agents — the main session (Opus) only orchestrates and decides; depth-1 subagents (Sonnet for judgment, Haiku for mechanical work) research, write, build and check; depth-2 Haiku leaves only read and quote. Work runs in dependency waves (parallel only when inputs are independent), with token rules. Use for any non-trivial task.
---

# Orchestration protocol

## Roles and model tiers
| Depth | Who | Model | Does |
|---|---|---|---|
| 0 | Main session (orchestrator) | Opus (brain mod forces it) | Splits work, decides, records decisions. Never researches, writes arch, edits code or runs tests itself. |
| 1 | Judgment agents | Sonnet | solution-architect, skeptic, arch-writer, ticket-writer, docs-reader, reference-scout, paper-scout, fetcher, editor, code-reviewer, security-reviewer, warden, verifier. |
| 1 | Mechanical agents | Haiku | web-scout, brancher, runner, publisher, Explore. |
| 2 | Leaves (spawned by a depth-1 agent) | Haiku, forced | `researcher:page-reader` (read one source, quote), `Explore` (find code). Nothing else may be spawned at depth 2; leaves spawn nothing. |

The tier lives in each agent's frontmatter and in `context/routing.json`; the brain mod enforces depth 2.
Move an agent to a cheaper tier only when its output is checked by a higher-tier agent (a skeptic,
verifier, or the orchestrator). Never put a step that decides or declares on Haiku.

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
1. **Files, not replies.** Every agent writes its full output to a file under `context/.runtime/`
   and replies with the status keyword, the path and ≤ 8 lines. The orchestrator reads a file only
   for the part it needs (Grep, Read with offset/limit). Never paste an agent's long report back
   into another prompt: pass the path.
2. **Slices, not whole documents.** Give each agent the exact sections it needs
   (`overview.md §5.3-§5.4, ADR-004`), not "read the arch". Agents read by heading (Grep `^## `,
   then Read with offset/limit). Split any binding doc over ~400 lines into section files.
3. **Resume, do not respawn.** A follow-up for an agent that already holds the context goes by
   SendMessage to that agent, not to a new one.
4. **Fresh session per stage.** Progress lives in files (`arch/*`, `tracker.json`, `STATE.md`,
   `context/.runtime/`). Between big stages (research → architecture → plan → build), update
   `STATE.md`, then let Keshav `/clear` or start a new session; the next stage resumes from files.
   The orchestrator's own context is the most expensive context in the system.
5. **Write by section.** Writers create or replace a whole section file in one write; they do not
   make many small edits to one large file (each call re-reads it).
6. **Hard stop per stage.** The orchestrator finishes ONE stage per session: when the stage's
   files are written, it updates `STATE.md` with the exact resume command and stops, even if Keshav
   says "continue". The brain mod's `budget-guard` block (main-loop context ≥ 50% or usage window
   ≥ 75%) is an order: save progress and hand off, or drop to one agent at a time.
7. **Write early.** Every agent writes its output file in its first turns and extends it, so a
   usage-limit stop loses nothing; a stopped agent is resumed by SendMessage, never respawned.
8. **Tiers are enforced.** `context/routing.json` `tiers` sets model and effort per agent type and
   the brain mod applies them on every model request. Do not pass `model` on an Agent call unless
   you mean to override the tier for that one run.
9. **Measure.** After each stage, run `/observe:traces` and note tokens by agent type in `STATE.md`.

## How to spawn
- Give each subagent everything it needs in the prompt: the goal, the input paths and sections,
  the output path, and the reply format. Subagents do not see this conversation.
- Keep each task small and concrete. If a subagent replies `GAP` or `HALT`, the main session
  resolves it with research subagents and spawns again. It never fills the gap itself.

## The two agents
- **researcher** (`/researcher:run`): research → architecture with diagrams in
  `context/projects/<p>/arch/` → validation → epics and tickets in `tracker.json` → GitHub Project.
- **builder** (`/builder:build`): one epic from `tracker.json` → fetch → branch → edit →
  code review, security review, tests and arch check in parallel → verify → loop → PR → CI
  green. Keshav merges.
