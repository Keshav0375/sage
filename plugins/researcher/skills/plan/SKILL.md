---
name: plan
description: Divide a project's decided architecture into an implementation plan — a foundation epic, epics from arch/plan.md, builder-ready tickets with summary, description and acceptance criteria — and save it to context/projects/<p>/tracker.json. Trigger /researcher:plan <project>.
argument-hint: "<project>"
---

# /researcher:plan

Load `brain:tracker` for the format. The arch must be decided first: `arch/overview.md` and
`arch/plan.md` exist and `STATE.md` has no open decision that the plan depends on.

1. **Epics.** Read `arch/plan.md`. Each epic delivers one usable outcome and maps to arch
   sections. Give each a key (`E1`...), title, summary, repo and `arch_refs`. Keep existing keys
   when `tracker.json` already exists.
   **Foundation epic `E0`.** Check each repo for what `builder:engineering` needs: a GitHub
   Actions workflow that runs lint, type check, unit and integration tests and security scans on
   pull requests; the single typed config; a way to start dependencies for integration tests.
   Add one `E0` ticket for each missing item. Every other epic depends on `E0`.
2. **Tickets (one message, in parallel).** Spawn one `researcher:ticket-writer` per epic, each
   with the project, the epic, and the arch file paths.
3. **Check (main session).** For each reply:
   - every arch component in the epic's scope is covered by a ticket, and no ticket goes beyond
     the arch,
   - every acceptance criterion can fail, and tests are named,
   - dependencies make sense across epics, with no cycles,
   - no ticket is size `L`.
   Send a ticket-writer back with the specific problems when a check fails.
4. **Questions.** Collect every ticket-writer `questions` entry. Answer each one from the arch or
   with a `researcher:docs-reader`, record the answer as an ADR through `researcher:arch-writer`,
   and send the ticket-writer back. Only questions about product scope, compliance or money go to
   Keshav (one message) and into `STATE.md` open decisions; their tickets stay `blocked`.
5. **Save** `tracker.json` (epics with their tickets, `issue: null`, `status: todo`).
6. **Report.** Show Keshav the plan: epics in order, ticket titles with sizes and dependencies.
   Do not wait for approval; continue to `/researcher:publish`.
