---
name: layout
description: The binding layout of sage/projects/<p>/ — library, arch (architecture.md, architecture-diagram.md, decision-logs.md, deep-dive/, state.md), epic folders with Markdown tickets, state.md and the project routing.json — and the ticket frontmatter format. Load before reading or writing any project file.
---

# Project layout

All project knowledge lives in the sage repo under `projects/` (the plugin option `context_dir`
points here). The repo is public on purpose: it shows how a project is planned with agents.

```
projects/
  registry.json            projects, kinds, local repo paths
  routing.json             default model/effort tiers for every agent type
  .runtime/                git-ignored scratch: traces, builder ledger, context packs, drafts
  _inbox/state.md
  <p>/
    state.md               project state: Now, Open decisions, Blockers, Resume command
    routing.json           project overrides of the tiers (optional), merged over the default
    library/               every resource an agent used
      index.md             one row per source: id | title | link | type | date read | licence | used in
      research/<round>/    evidence notes, skeptic verdicts, proposals, decision drafts (.md)
      files/               raw downloads (PDF, HTML, ZIP) — git-ignored, never committed
    arch/
      state.md             arch status: what is decided, validated, open
      architecture.md      the whole architecture explained, top down, linking each deep-dive
      architecture-diagram.md  the full-flow Mermaid diagram; every node names its deep-dive file
      decision-logs.md     ADRs, newest first, with the reasoning and the strongest dissent
      deep-dive/<nn>-<slug>.md  one key component or concern per file, small (≤ 250 lines)
    epic/
      README.md            GitHub project link, phases, epic order, status table
      <E>-<slug>/
        epic.md            frontmatter + goal, scope, ADRs, exit criteria
        tickets/<E>-T<m>-<slug>.md
```

## Rules
- Agents write only inside their project folder. Research output goes to
  `library/research/<round>/` (committed); only transient scratch goes to `projects/.runtime/`.
- Every source an agent cites gets a row in `library/index.md`. Downloads go to `library/files/`.
- Never commit secrets, credentials, personal data of real people, or third-party documents
  without a reuse licence; those stay in `library/files/` or `.runtime/`.
- `architecture-diagram.md` is the map: each component node carries the deep-dive file name, and
  each deep-dive starts with a link back to the diagram and to `architecture.md`.
- A ticket's `arch_refs` point at `deep-dive/<file>.md#<heading>` or `decision-logs.md#adr-<n>`.
  A phase or builder reads only the deep-dive files its tickets name.
- `decision-logs.md` keeps every ADR; a superseded ADR stays, marked `Superseded by ADR-<n>`.

## Ticket file
Frontmatter values are JSON (valid YAML), one key per line, in this order:

```markdown
---
key: "E1-T3"
title: "User table and migration"
epic: "E1"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E1-T1"]
arch_refs: ["deep-dive/05-data-model.md#tables", "decision-logs.md#adr-002"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
One sentence.

## Description
What to build and why.

## Acceptance criteria
- [ ] Given … when … then … (each one a check that can fail)
```

- `status` is one of `todo`, `in_progress`, `review`, `done`, `blocked`.
- `issue` is `null` until published, then `{"repo":"o/r","number":12,"id":123,"url":"…"}`.
- Keys never change. Size `L` means split the ticket. A ticket with no `arch_refs` is not ready.
- During a build, change frontmatter only through `mcp__brain__ticket_update`.

## Epic file
`epic.md` frontmatter: `key`, `title`, `phase`, `phase_name`, `repo`, `status`, `depends_on`,
`arch_refs`, `issue`, `updated`; body: Goal, Scope, ADRs, Exit criteria.
`epic/README.md` frontmatter: `github` (`{"owner","project_number","project_url","status_field"}`)
and `updated`; body: phases and the epic order line, and a status table.
