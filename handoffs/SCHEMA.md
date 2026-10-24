# Handoff contracts

Every sage subagent returns a **typed handoff**: the first line is a status keyword, then
fixed-label lines. The `SubagentStop` hook bounces a reply that doesn't open with a keyword (once,
so it can never loop). Orchestrators branch on the keyword, never on prose.

Why: free-form agent replies are where multi-agent systems leak. A keyword plus labels makes
a reply machine-checkable, cheap to forward, and diffable when an agent's prompt is evolved.

## Keywords

| Keyword | Meaning | Who |
|---------|---------|-----|
| `BRIEF` | context assembled | context-builder |
| `CONTRACT` | binding names/paths/invariants distilled | architect (distill) |
| `PLANNED` · `HALT` | plan written · cannot plan without a human answer | planner |
| `DONE` · `GAP` · `HALT` | built + gated · plan is wrong/silent · blocked outside the plan | builder |
| `FINDINGS` · `CLEAN` | defects found · nothing found | reviewer, safety-reviewer, architect (review) |
| `VERDICT` | gate result | gate-runner |
| `REPORT` | bookkeeping done | clerk |
| `SCOUT` | sourced evidence from one source | scout |
| `SYNTHESIS` | merged answer with citations | synthesizer |
| `CLAIMS` | fact-check per claim | skeptic |
| `ANSWER` · `RANKING` | council member's answer · peer ranking | councilor |
| `VERDICT` | council final | chairman |
| `CLUSTERS` | named failure mechanisms | miner |
| `PROPOSAL` | one minimal harness edit, on a branch | harness-smith |
| `AGENT` | a new agent drafted into the incubator | agent-smith |
| `ASK` | a question only Keshav can answer (any agent; always with `STATE`) | any |

## Common labels

```
<KEYWORD> <id> · <one-line summary>
FILES     <path>, <path>            (what was read or written)
EVIDENCE  <file:line | url>, …      (anything claimed must point here)
CONFIDENCE high | medium | low      (low = say why)
OPEN      <open question>           (or "none")
NOTES     <what the orchestrator must know>   (or "none")
STATE     <what is on disk now>     (required with HALT / GAP / ASK)
```

Max 12 lines unless the agent file says otherwise. Long material goes to a file
(`.plans/`, `library/research/`), and the handoff carries the path.

## Artifacts on disk

| Artifact | Path | Written by |
|----------|------|-----------|
| plan | `.plans/<project>-<task>.md` (gitignored) | planner |
| research note | `library/research/<YYYY-MM-DD>-<slug>.md` | synthesizer |
| council record | `library/council/<YYYY-MM-DD>-<slug>.md` | chairman |
| harness proposal | git branch `evolve/<cluster>-<slug>` + `.plans/evolve-<cluster>.md` | harness-smith |
| incubating agent | `incubator/agents/<name>.md` | agent-smith |
| snapshot | `.sage/handoffs/<stamp>.md` (gitignored) | PreCompact hook |
