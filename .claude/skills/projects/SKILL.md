---
name: projects
description: Show every sage project on one board — kind, active phase with a progress bar, what's in flight, next wave, gate, open lessons, missing repos, last touched — or one project's full card. Use when Keshav asks what he's working on, how projects stand, or to pick what to do next. Trigger /projects [name].
argument-hint: "[project name]"
---

# /projects

1. No argument: `python3 bin/sagectl projects`. With a name: `python3 bin/sagectl projects <name>`
   (that project's full card). Print the output **verbatim in a code block**. Don't re-draw it.
2. Under it, one line per thing that needs attention, worst first:
   - a RED gate → "`<p>` gate is RED, `/check` it before anything else"
   - a task sitting in `review` → "`<p>` <id> is waiting on you to verify"
   - a missing repo path → "`<p>` repo `<r>` isn't on this machine, fix `project.toml`"
   - a CYCLE → "`<p>` has a dependency cycle, fix deps in TODO.md"
   - 3+ open lessons on one project → "`<p>` has <n> open lessons, `/retro` time"
3. End with **one** suggested move (e.g. "`/start payments-api` then `/build`"). Nothing needs
   attention? Say so in one line.

For machine-readable output (dashboards, other tools): `python3 bin/sagectl projects --json`.
