---
name: tracker
description: The format of brain/projects/<p>/tracker.json — the local state of a project's implementation plan and its GitHub project, epics and tickets. The researcher writes it; the builder reads and updates it. Load before reading or writing a tracker.
---

# tracker.json

`brain/projects/<p>/tracker.json` is the local copy of the plan. GitHub holds the same epics and
tickets as issues in a GitHub Project. The tracker is what agents read; keep both in step.

```json
{
  "version": 1,
  "project": "<project>",
  "github": {
    "owner": "<user or org>",
    "project_number": 3,
    "project_url": "https://github.com/users/<owner>/projects/3",
    "status_field": "Status"
  },
  "epics": [
    {
      "key": "E1",
      "title": "Authentication",
      "summary": "One sentence: the outcome this epic delivers.",
      "repo": "api",
      "arch_refs": ["overview.md#4", "decisions.md#adr-3"],
      "status": "todo",
      "issue": { "repo": "<owner>/<repo>", "number": 12, "id": 123456789, "url": "https://github.com/..." },
      "tickets": [
        {
          "key": "E1-T1",
          "title": "User table and migration",
          "summary": "One sentence.",
          "description": "What to build and why, with the arch sections it implements.",
          "acceptance_criteria": ["Given … when … then …"],
          "arch_refs": ["overview.md#5"],
          "repo": "api",
          "depends_on": [],
          "size": "S",
          "status": "todo",
          "issue": null,
          "branch": null,
          "pr": null
        }
      ]
    }
  ],
  "updated": "<yyyy-mm-dd>"
}
```

## Rules
- `key` values never change. Epics are `E<n>`, tickets are `E<n>-T<m>`.
- `repo` is a repo name from the project's `repos` in `brain/registry.json`.
- `status` is one of `todo`, `in_progress`, `review`, `done`, `blocked`.
- `issue` is `null` until the researcher publishes it to GitHub. `id` is the REST id (needed to
  link sub-issues); `number` is the issue number.
- Each acceptance criterion is a check that can fail. Each ticket names the `arch_refs` it
  implements; a ticket with none is not ready.
- A ticket is small enough for one branch and one PR. Size `L` means split it.
- Write the file with 2-space indentation and update `updated` on every change.
