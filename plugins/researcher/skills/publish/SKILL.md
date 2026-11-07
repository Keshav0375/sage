---
name: publish
description: Publish the checked epic and ticket files to GitHub — a GitHub Project, epic issues, ticket issues linked as sub-issues — and save the links back into those files. Trigger /researcher:publish <project>.
argument-hint: "<project>"
---

# /researcher:publish

Load `brain:layout` for the file format.

Keshav authorized the researcher to create GitHub Projects and issues on his own repos without
asking. The owner and repos come from the registry and the git remotes. Ask him only when a repo
has no remote or its owner is not his account.

1. **Check prerequisites.** `gh auth status` shows the `project` scope (fix:
   `gh auth refresh -s project`). Every ticket `repo` maps to a GitHub repo: read
   `git -C <path> remote get-url origin` for each registry repo.
2. **Check for duplicates.** If `epic/README.md` frontmatter already has `github.project_number`, reuse that
   project and create only the epics and tickets with `issue: null` in their frontmatter.
3. **Publish.** Spawn `researcher:publisher` with the project, the `epic/` path, the owner and
   the repo map.
4. **Verify (main session).** Read the epic and ticket files back: every one has an `issue` with
   a URL. Spot-check with `gh project item-list <number> --owner <owner> --format json` that the
   item count matches.
5. **Record.** Add the project URL to `state.md` (`## Now`). Report the URL and the counts.
