---
name: board
description: Build or sync a project's GitHub Project board like the sage template (Sentinel style) — prioritized backlog grouped by priority, status board, roadmap, bugs, in review, my items, all tickets, task board, epics and phases, blocked, one view per phase, the 6 automation workflows — and fill Status, Priority, Size, Estimate, Level, Phase, Epic and Task ID from the epic and ticket files. Runs after every publish and on /builder:status. Trigger /researcher:board <project>.
argument-hint: "<project>"
---

# /researcher:board

Load `brain:layout`. The board is built by a script, not by an agent: no LLM tokens.

**Template.** `projects/registry.json` → `github.template_project` (project #6, `sage-template`,
copied from Sentinel #4). It carries the views with their grouping and sorting and the 6 workflows
(auto-add sub-issues, auto-close issue, item added, item closed, PR linked, PR merged). The GitHub
API cannot set grouping or turn workflows on, so a board is always a COPY of the template. Change
the template in the GitHub UI when the standard changes; new boards pick it up.

## Run
```
python3 -I plugins/researcher/scripts/project_board.py --project-dir projects/<p> \
  --owner <github.owner> --template <github.template_project> --title "<Project title>" [--close-old]
```
- First run: copies the template into a new board, saves `board_number`, `project_number`,
  `project_url`, `project_id` in `epic/README.md` frontmatter, keeps the old number as
  `previous_project_number`; `--close-old` closes (never deletes) the old board.
- Every run: Phase options = the plan's phases, Epic options = one per epic, one table view per
  phase (filter `phase:"…" level:Task`), every epic and ticket issue added, and the fields set:
  Status (todo→Backlog, in_progress→In progress, review→In review, done→Done), Priority (phase 0
  → P0, phases 1-2 → P1, later → P2; spikes one level higher), Size and Estimate (XS 1, S 2, M 3,
  L 5, XL 8), Level (Epic or Task), Phase, Epic, Task ID (the key). Rerun-safe.

## When
- After `/researcher:publish` (stage 5 of every research run), automatically.
- On `/builder:status`, to sync Status from the ticket files.
- After a re-plan, with the new publish diff applied first.

## Check
`gh project view <board_number> --owner <owner>` shows the views; the item count equals the
number of epic and ticket files with an `issue`. Report the board URL in `state.md` (`## Now`).
