---
name: build
description: Build ONE whole phase of the active project end-to-end as a DAG — locate → context + contract → waves of parallel plan/build (one worktree per builder) → integrate + gate → review → PR → Keshav's sign-off. Trigger /build [<phase> | status | resume].
argument-hint: "[<phase number> | status | resume]"
disable-model-invocation: true
---

# /build: the phase orchestrator

You are the **orchestrator**. You sequence, decide, talk to Keshav, and integrate short handoffs.
**You don't write product code or edit the tracker yourself.** Specialists do, each in a
fresh context that's discarded afterward. Deterministic steps (gate, status, git integration) are
plain commands you run, never agents. Your context holds only: the card, the BRIEF, the CONTRACT,
and handoff lines.

**Opus decides, Sonnet types, Haiku checks.** Every call of one wave goes out in **ONE message**.
That's what makes it parallel. Subagents can't spawn subagents, so every fan-out is yours.

| Step | Who | Returns |
|------|-----|---------|
| 0 locate | `python3 bin/sagectl where [--phase N]` | card · exit 1 = don't enter |
| 1 context + contract | `context-builder` ∥ `architect` mode=distill | BRIEF · CONTRACT |
| 2 plan (per wave) | `planner` × wave, parallel | PLANNED / HALT |
| 3 build (per wave) | `builder` × wave, parallel, one worktree each | DONE / GAP / HALT |
| 4 integrate | you: cherry-pick, `sagectl gate`, boot check | VERDICT |
| 5 record | `clerk` mode=record-task (background) | REPORT |
| 6 review | `architect` review ∥ `reviewer` ∥ `safety-reviewer` | FINDINGS / CLEAN |
| 7 close | `clerk` mode=close-phase | PR url |

## Step 0: locate
`python3 bin/sagectl where`. Exit 1 → report the HALT line verbatim and stop (previous phase
unsigned, nothing open). Note `branch:` and `repo:` from the phase meta. Branch from the repo's
`branch_from` (project.toml) if the branch doesn't exist.

## Step 1: context + contract (ONE message, two agents)
`context-builder`: "PROJECT <p> PHASE <n>". `architect`: "mode=distill PROJECT <p> PHASE <n>".
CONFLICTS or BLOCKERS → stop, show Keshav, ask. Never pick a side yourself.
Print two lines: `ctx ✓ …` and `arch ✓ … conflicts: none`.

## Steps 2-4: one wave at a time (WAVES from the card)
For each wave:
1. **Plan:** one `planner` per task, ONE message. Pass BRIEF, the CONTRACT rows, and
   `WAVE_FILES` = the files every other task in this wave is expected to touch (from task specs).
   Any `HALT` → resolve with Keshav before building that task.
2. **Build:** single-task wave → build in the repo on the phase branch. Multi-task wave →
   `git -C <repo> worktree add ../.wt/<repo>-<task> -b wt/<task> <phase-branch>` per task, then one
   `builder` per task, ONE message, `PARALLEL yes`. `GAP` → send the planner the gap, then
   SendMessage the builder the amended plan.
3. **Integrate:** cherry-pick each wave commit onto the phase branch in task-id order. Conflict
   = the wave was wrong: stop, tell Keshav, log a lesson. Then
   `python3 bin/sagectl gate` (full). Not GREEN → fix batch (planner FIX → builder) before the
   next wave. Remove worktrees after integration.
4. **Record:** `clerk` mode=record-task for the wave, in the background.

## Step 6: review (ONE message, three agents)
`architect` mode=review · `reviewer` · `safety-reviewer` (skip safety only for docs-only diffs).
Any 🚨 → fix batch → re-gate → re-review only the reviewers that flagged. Show Keshav ⚠️ lines;
he decides which to fix.

## Step 7: close
`clerk` mode=close-phase → PR url. Tell Keshav: what shipped, the gate verdict, the honest list,
and the see-it-working checklist. Tasks sit at `review` until **he** verifies and signs
(`sagectl task <id> verified`, `sagectl phase sign <n>`), which agents are blocked from doing.

## Rules
- Mistake or correction during the phase → `sagectl lesson add` right then, not at the end.
- `/build status` = step 0 only. `/build resume` = step 0, then continue from the first task not
  `review`/`verified`.
