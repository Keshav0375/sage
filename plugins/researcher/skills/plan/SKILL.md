---
name: plan
description: Divide a project's decided architecture into an implementation plan — epics from arch/plan.md, builder-ready tickets with summary, description and acceptance criteria — and save it to brain/projects/<p>/tracker.json for Keshav's approval. Trigger /researcher:plan <project>.
argument-hint: "<project>"
---

# /researcher:plan

Load `base:tracker` for the format. The arch must be decided first: `arch/overview.md` and
`arch/plan.md` exist and `STATE.md` has no open decision that the plan depends on.

1. **Epics.** Read `arch/plan.md`. Each epic delivers one usable outcome and maps to arch
   sections. Give each a key (`E1`...), title, summary, repo and `arch_refs`. Keep existing keys
   when `tracker.json` already exists.
2. **Tickets (one message, in parallel).** Spawn one `researcher:ticket-writer` per epic, each
   with the project, the epic, and the arch file paths.
3. **Check (main session).** For each reply:
   - every arch component in the epic's scope is covered by a ticket, and no ticket goes beyond
     the arch,
   - every acceptance criterion can fail, and tests are named,
   - dependencies make sense across epics, with no cycles,
   - no ticket is size `L`.
   Send a ticket-writer back with the specific problems when a check fails.
4. **Questions.** Collect every ticket-writer `questions` entry. Ask Keshav, or add them to
   `STATE.md` open decisions.
5. **Save** `tracker.json` (epics with their tickets, `issue: null`, `status: todo`).
6. **Gate.** Show Keshav the plan: epics in order, ticket titles with sizes and dependencies.
   Publishing waits for his approval.
