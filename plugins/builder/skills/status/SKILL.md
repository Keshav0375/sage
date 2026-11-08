---
name: status
description: Sync a project's ticket files with GitHub — closed issues and merged PRs mark tickets done, epic progress, blocked tickets, the next ready tickets. Trigger /builder:status <project>.
argument-hint: "<project>"
---

# /builder:status

1. Read every ticket file in `projects/<p>/epic/*/tickets/` (load `brain:layout`).
2. For each ticket with an `issue`: `gh issue view <n> --repo <r> --json state,closedAt`.
   For each ticket with a `pr`: `gh pr view <url> --json state,mergedAt`.
3. A merged PR or a closed issue sets `status: done` through `mcp__brain__ticket_update`. Do not change any other status.
4. Update the status table in `epic/README.md`.
5. Report per epic: done/total, blocked tickets with reasons, and the ready tickets
   (`todo` with all `depends_on` done). Suggest the next `/builder:build <project> <epic>`.

After syncing the ticket files, run `/researcher:board <project>` so the GitHub board's Status,
Priority and Size match the files.
