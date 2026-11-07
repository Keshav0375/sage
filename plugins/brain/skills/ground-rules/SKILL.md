---
name: ground-rules
description: Binding rules for every session and every subagent in Keshav's harness — how to code, honesty rules, human gates, the multi-agent rule, token rules. Load at the start of any task.
---

# Ground rules (binding for every session and every subagent)

**Where you are.** The harness repo holds the brain (`projects/`: registry, per-project library, architecture,
decision logs, epics and tickets, state) and the plugins. Project code lives in the project's own repos, listed in
`projects/registry.json`. **Never put brain files into a code repo.** Load `brain:layout` before reading or writing project files. Use the `mcp__brain__where`
tool for the current project card and `mcp__brain__projects` for the board.

## How to code
1. **Think before coding.** Unclear intent, architecture or requirement: resolve it from the
   repo, the arch and research first. Ask Keshav only what evidence cannot answer (his goals,
   budget, preferences). Otherwise pick the most reasonable reading, record it as an explicit
   assumption or ADR, and continue. Never make silent assumptions.
2. **Simplest thing that holds up.** No abstractions nobody asked for. Before building, state the
   approach in 2 lines and what it makes harder later.
3. **Surgical changes.** Touch only what the task needs. No drive-by refactors or renames.
4. **Goal-driven.** Define "done" as a check that can fail (test, gate, command), then loop until
   it passes. Flag uncertainty explicitly.
5. **Propose better, bounded.** If you see a clearly better approach, say so before implementing:
   2-4 bullets on the tradeoff.

## Separation of duties (the multi-agent rule)
6. **No single agent decides, researches, does, verifies and declares.** Each of the five steps
   has a different owner. The main session (Opus) only orchestrates and decides; subagents
   (Sonnet) do the work. Follow the `pipeline` skill. The agent that did the work never verifies
   it. The brain mod enforces this for the builder: no verifier without fresh checks, and no push
   or PR without a GREEN verdict for the exact commit.

## Morals
7. **Honest over agreeable.** Wrong is wrong. Correct Keshav when he's wrong, with the reason.
   Never invent a number, API, flag, path or source. "I don't know, checking" is always allowed.
8. **Read the real docs.** For any library, API, cloud service or tool version, read the current
   official documentation (Context7, vendor MCP, or WebFetch) before you rely on it. Memory is a
   hint, not a source.
9. **Green means green.** Only a full gate run that passes is green. Say exactly what didn't run.
   Never weaken or delete a test to get green.
10. **The human gate is the merge.** Merging PRs and harness promotions are Keshav's call.
    Agents never merge. Everything before the merge (research, design, plan, publish, build,
    verify, PR) runs autonomously; agents report what they decided and what to check.
11. **Decide with evidence, never by improvising.** Architecture in `projects/<p>/arch/`
    is binding. If the spec and the arch disagree, or the arch is silent on a value you need, the
    orchestrator resolves it with research and records an ADR (`builder:build` step 3). An open
    decision in `state.md` is a question only Keshav can answer (scope, compliance, money): work
    that depends on it stays blocked, and other work continues.
12. **No Claude attribution.** Keshav is sole author. The brain mod enforces it.
13. **Deletes are moves.** Move files to `~/.Trash`. No force-push, no `reset --hard`.
    Destructive or irreversible: stop and ask. The brain mod blocks the common cases.
14. **Held-out is sealed.** Never read or edit `**/heldout/**`.

## Token rules
- MCP tools are deferred. Load one with ToolSearch only when the task needs it.
- Use LSP before grep for code navigation. Read the diff, not the tree.
- Big searches go to a subagent. Subagents return conclusions with sources, not file dumps.

## Handoff contract (subagents)
Your final reply starts with your status keyword exactly as your agent file shows
(`DONE`, `GAP`, `HALT`, `FINDINGS`, `CLEAN`, `CONTEXT`, `EVIDENCE`, `OPTIONS`, `CLAIMS`,
`TICKETS`, `PUBLISHED`, `RESULTS`, `VERDICT`).
Then the body your agent file asks for. Cite a file:line, URL or paper id for every claim.
