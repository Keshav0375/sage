---
name: publish
description: Publish an approved tracker.json to GitHub — a GitHub Project, epic issues, ticket issues linked as sub-issues — and save the links back to the local tracker. Trigger /researcher:publish <project>.
argument-hint: "<project>"
---

# /researcher:publish

Creating GitHub issues and projects is outward-facing. Run only after Keshav approved the plan in
this session, and confirm the owner and repos with him first.

1. **Check prerequisites.** `gh auth status` shows the `project` scope (fix:
   `gh auth refresh -s project`). Every ticket `repo` maps to a GitHub repo: read
   `git -C <path> remote get-url origin` for each registry repo.
2. **Confirm.** Tell Keshav: owner, project title, the repos, and the number of epics and
   tickets to create. Wait for yes.
3. **Publish.** Spawn `researcher:publisher` with the project, the tracker path, the owner and
   the repo map.
4. **Verify (main session).** Read `tracker.json` back: every epic and ticket has an `issue` with
   a URL. Spot-check with `gh project item-list <number> --owner <owner> --format json` that the
   item count matches.
5. **Record.** Add the project URL to `STATE.md` (`## Now`). Report the URL and the counts.
