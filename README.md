# sage

Sage is my agentic engineering harness for Claude Code. It plans a software project from research to
architecture to tickets, and then builds it ticket by ticket, with one orchestrator and many small,
cheap subagents. Every artifact of that work stays in this repo, so you can read how each project was
planned: the sources, the competing designs, the decisions with their dissent, and the tickets.

## How a project is planned

```
/researcher:run <project> <goal>
  stage 1  research      scouts read official docs, papers, reference systems and the web
                         -> projects/<p>/library/
  stage 2  design        2-3 solution architects propose, a skeptic attacks the leader,
                         the orchestrator decides  -> arch/decision-logs.md
  stage 3  architecture  writers produce architecture.md, the diagram and deep-dive files,
                         then a validation pass checks them against current docs
  stage 4  plan          ticket writers split each epic into tickets with failing acceptance criteria
                         -> epic/<E>/tickets/
  stage 5  publish       GitHub Project, epic and ticket issues
/builder:build <project> <epic>
  per ticket: fetch context -> branch -> edit -> code review, security review, tests, arch check
              -> verifier -> PR with green CI. I merge.
```

The orchestrator (Opus) only splits work and decides. Subagents do the work on the cheapest model that
is good enough, and a stronger agent checks every cheap step:

| Tier | Agents |
|---|---|
| Opus | the orchestrator: decisions, questions to me, state |
| Sonnet, medium/high effort | skeptic, solution architects, arch and ticket writers, code editor, reviewers, verifier |
| Sonnet, low effort | docs reader, reference scout, context fetcher, arch warden |
| Haiku, low effort | page reader (quotes only), web scout, publisher, git brancher, test runner, file finder |

The brain mod enforces these tiers on every model request (`projects/routing.json`), and a project can
override them in its own `routing.json`. Token controls: waves of at most 3 agents, replies of at most
8 lines with the detail in files, one stage per session, and a budget guard that tells the orchestrator
to hand off when its context passes 50% or the usage window passes 75%.

## Project layout

```
projects/
  registry.json, routing.json     projects and default model tiers
  <project>/
    state.md                      where the project is, open decisions, resume command
    routing.json                  project-specific agent tiers
    library/                      every source agents used: index.md, research/<round>/
    arch/
      architecture.md             the whole architecture, top down
      architecture-diagram.md     full-flow Mermaid diagram, each node linked to its deep-dive
      decision-logs.md            ADRs with reasoning and the strongest dissent
      deep-dive/                  one small file per key component or concern
      state.md
    epic/
      plan.md, README.md          phases, epic order, status
      <E>-<slug>/epic.md + tickets/<E>-T<m>-<slug>.md
```

Example: [projects/finadvisor](projects/finadvisor), a multi-tenant compliance RAG assistant for
financial advisors (US, EU, UK), with 38 ADRs, real-source research and 203 tickets.

## Repository

```
.claude-plugin/marketplace.json   marketplace "hq"
plugins/brain/        registry and context mod, model tiers, budget guard, guards, project layout
plugins/researcher/   research and architecture agents and skills
plugins/builder/      build loop agents and skills
plugins/observe/      JSONL traces and token usage by agent type
plugins/ui/           status line: clock, tokens, cost, context, rate limits
projects/             the planned projects (see above)
```

Not committed: `projects/.runtime/` (traces, builder ledger, drafts) and `projects/*/library/files/`
(raw downloads). Third-party documents without a reuse licence and anything secret stay there.

## Install

Inside this repo, `.claude/settings.json` registers the marketplace and enables the plugins. For any
other repo, run once:

```
/plugin marketplace add ~/Projects/sage
/plugin install brain@hq researcher@hq builder@hq observe@hq time@hq
```

Then set the `brain` option `context_dir` to `~/Projects/sage/projects` and the `observe` option
`trace_dir` to `~/Projects/sage/projects/.runtime/traces` in `/config`, and run `/brain:setup`.

## Develop

```
claude plugin validate ./plugins/<name>
cd plugins/brain && claude plugin test
```

Tested with Claude Code 2.1.316.
