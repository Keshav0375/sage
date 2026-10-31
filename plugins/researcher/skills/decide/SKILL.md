---
name: decide
description: Record a decision Keshav made as an ADR in context/projects/<p>/arch/decisions.md and clear it from STATE.md open decisions. Trigger /researcher:decide <title>.
argument-hint: "<title>"
---

# /researcher:decide

Only record a decision Keshav stated. If he has not decided, present the options and stop.

1. Get the project with `mcp__brain__where`.
2. Add an entry at the top of `context/projects/<p>/arch/decisions.md`:
   ```
   ## ADR-<n>: <title> (<yyyy-mm-dd>)
   **Context:** why this came up, the requirements that matter.
   **Options:** each with its cost and risk.
   **Evidence:** links to research notes, council notes, docs, papers.
   **Decision:** what Keshav chose.
   **Makes harder later:** what this rules out or costs in future.
   ```
3. Update `arch/overview.md` sections the decision changes.
4. Remove the question from `## Open decisions` in `STATE.md`.
