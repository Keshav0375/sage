# sage: Claude Code instructions

**sage is Keshav's one brain for every project**: coding, research, and thinking partner on big
decisions. This repo is the control plane: architecture, trackers, lessons, evals, agents,
skills, hooks. **No application code lives here.** Project code stays in its own repos, and
`projects/<p>/project.toml` says where. This file is a map. Follow the pointer for detail.

@.claude/skills/ground-rules/SKILL.md

## Orient (cheap, use these instead of Read)

```bash
python3 bin/sagectl where                 # active project + phase card: tasks, WAVES, gate, lessons
python3 bin/sagectl projects             # every project on one board (or: projects <name>)
python3 bin/sagectl arch <doc> --list     # TOC + token cost; then: sagectl arch <doc> 3.2
python3 bin/sagectl gate [--fast]         # the project's quality gate → ONE VERDICT line
python3 bin/sagectl lesson list           # open lessons for the active project
python3 bin/sagectl mine                  # failure clusters (weakness mining)
python3 bin/sagectl audit                 # context budget + unused skills/agents
```

The SessionStart hook already injected the card, so don't re-run `where` just to orient.
The active project comes from cwd (inside `projects/<p>/` or one of its repos), `$SAGE_PROJECT`,
or `sagectl use <p>`.

## Where things are

| Need | Where |
|------|-------|
| A project's binding architecture + ADRs | `projects/<p>/arch/` (via `sagectl arch`) |
| Live state, blockers, open decisions | `projects/<p>/STATE.md` (small, read whole) |
| Phases + tasks | `projects/<p>/phases/TODO.md` (via `sagectl where`) |
| Lessons (structured mistakes) | `projects/<p>/lessons.jsonl` (via `sagectl lesson`) |
| Project + harness evals | `projects/<p>/evals/`, `evals/harness/`. `heldout/` is sealed |
| Cross-project knowledge | `library/` (patterns, playbooks, stacks, papers, research, council) |
| Handoff contract | `handoffs/SCHEMA.md` |
| How the whole thing works | `docs/architecture.md` |

## Three lanes

| Lane | Commands | Agents |
|------|----------|--------|
| **Build** | `/new-project` `/spec` `/plan` `/build` `/check` `/review` `/ship` | context-builder · architect · planner · builder · reviewer · safety-reviewer · gate-runner · clerk |
| **Think** | `/research` `/council` `/grill` `/decide` | scout · synthesizer · skeptic · councilor · chairman |
| **Evolve** | `/retro` `/mine` `/evolve` `/forge-agent` `/audit` `/handoff` `/start` `/projects` | miner · harness-smith · agent-smith |

**Opus decides, Sonnet types, Haiku checks.** The main session is always the orchestrator:
subagents can't spawn subagents, so every fan-out is yours. A wave of independent work goes
out in **one message** (that's what makes it parallel), and each builder gets its own git worktree.

## When stuck
The project's `arch/`, then its `decisions.md`, then `library/`, then `/research`, then **ask Keshav.**
