---
name: decide
description: Record a decision as an ADR in the active project's arch/decisions.md (context, options with costs, council/research links, decision, what it makes harder later), and clear it from STATE.md open decisions. Trigger /decide <title>.
argument-hint: "<decision title>"
---

# /decide

1. Next ADR number from `projects/<p>/arch/decisions.md` (`D<N>`).
2. Fill `_templates/adr.md`: context, options (one line each with its cost), links to any
   `library/research/` or `library/council/` record, the decision, consequences, and **what it
   makes harder later**.
3. Status `accepted` only if Keshav stated the decision; otherwise `proposed` + add it to
   `STATE.md` → Open decisions.
4. If it supersedes an earlier ADR, mark that one `superseded by D<N>` (never delete it).
5. If the arch docs now disagree with the ADR, list the sections to update. Don't silently edit them.
