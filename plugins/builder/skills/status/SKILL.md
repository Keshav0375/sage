---
name: status
description: Sync a project's tracker.json with GitHub — closed issues and merged PRs mark tickets done, epic progress, blocked tickets, the next ready tickets. Trigger /builder:status <project>.
argument-hint: "<project>"
---

# /builder:status

1. Read `brain/projects/<p>/tracker.json` (load `base:tracker`).
2. For each ticket with an `issue`: `gh issue view <n> --repo <r> --json state,closedAt`.
   For each ticket with a `pr`: `gh pr view <url> --json state,mergedAt`.
3. A merged PR or a closed issue sets `status: done`. Do not change any other status.
4. Write `tracker.json` back with `updated`.
5. Report per epic: done/total, blocked tickets with reasons, and the ready tickets
   (`todo` with all `depends_on` done). Suggest the next `/builder:build <project> <epic>`.
