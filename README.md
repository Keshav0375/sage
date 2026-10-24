# sage 🧠

**One brain for every project.** sage is Keshav's agentic SDLC harness for Claude Code: a
single repo that plans, builds, reviews, researches, argues with itself, and gets better at all
of it over time, for any project, task or problem.

It talks like your homeboy. It doesn't lie to you.

```
╭─ sage ───────────────────────────────────────────────────────╮
│ project  payments-api · code · Stripe-backed billing service │
│ repo     app → /home/keshav/code/payments-api                │
│ phase    2 — Auth · 3/6 verified                             │
│ branch   dev/phase-2-auth                                    │
│ waves    1: 2.4 2.5 | 2: 2.6                                 │
│   review   2.3 Login API                                     │
│ lessons  2 open · latest: read callers before changing a sig │
│ gate     GREEN (full) 1h ago                                 │
╰──────────────────────────────────────────────────────────────╯
sage · payments-api P2 2.3 review · gate ✓12m · ⎇ dev/phase-2-auth · ↳ builder · ctx 23% · 5h 41% · $0.42
```

---

## Why

Most Claude Code setups are a big CLAUDE.md and a prayer. sage is built on what actually
holds up in production use:

- **Rules that matter live in hooks, not prose.** Deletes become reversible trash moves,
  force-pushes are blocked, held-out evals are sealed, agents can't mark their own work verified.
- **Opus decides, Sonnet types, Haiku checks.** Planning and review are Opus; building to a plan
  is Sonnet; verification is Haiku. Waves of independent tasks run in parallel, one git worktree each.
- **Typed handoffs.** Every subagent reply opens with a status keyword (`DONE`, `GAP`, `HALT`,
  `FINDINGS`…). A hook bounces anything else.
- **Research is a first-class lane.** Parallel scouts across your own library, the web, Reddit,
  official docs, arXiv and GitHub → cited synthesis → adversarial fact-check. Plus an LLM Council
  for expensive decisions.
- **It improves itself, safely.** Mistakes are logged as structured lessons, clustered into
  failure mechanisms, fixed with minimal harness edits, and promoted only if a sealed held-out
  eval set doesn't regress (after *Self-Harness*, arXiv 2606.09498). You approve every promotion.
- **Dynamic per project.** One `project.toml` per project: gate, formatter, LSP servers, dead zones,
  research sources, all detected from the repo, never hardcoded.
- **Cheap to carry.** ~5K tokens of always-loaded context (`sagectl audit`), against a 15K budget.

## Quick start

```bash
git clone https://github.com/Keshav0375/sage && cd sage
python3 bin/sagectl --help                 # stdlib only, Python ≥ 3.11, nothing to install
pip install -e '.[dev]' && pytest -q       # optional: tests + `sagectl` on PATH
claude                                     # SessionStart prints the card; statusline lights up
```

Inside Claude Code:

```
/new-project payments-api app=../payments-api     # detects stack → gate, formatter, LSP
/spec                                              # architecture + ADRs (interviews you first)
/plan                                              # phases + tasks with deps → parallel waves
/build                                             # the whole phase, end to end
```

Then, once per project: install the LSP plugin(s) `/new-project` prints (`/plugin install
pyright-lsp@claude-plugins-official` etc.) and make sure the language server binary is on PATH.
Turn on the sandbox with `/sandbox` (Claude Code ≥ 2.1.2).

## Commands

| Lane | Command | What it does |
|------|---------|--------------|
| **Build** | `/new-project` | scaffold `projects/<name>/`, detect stack, wire LSP + research sources |
| | `/spec` | write the binding architecture + ADRs (interview → research → architect) |
| | `/plan` | cut it into phases and PR-sized tasks with explicit deps |
| | `/build` | DAG orchestrator: context ∥ contract → waves of parallel plan/build → gate → 3 reviewers → PR |
| | `/check` · `/review` · `/ship` | gate verdict · quick diff review · push + honest PR |
| **Think** | `/research <q>` | parallel scouts (library, web, Reddit, docs, arXiv, GitHub) → synthesis → skeptic |
| | `/council <q>` | LLM Council: independent answers → anonymized peer ranking → chairman verdict + dissent |
| | `/grill <idea>` | QA-partner mode: Socratic stress-test, highest risk first |
| | `/decide <title>` | record an ADR, including "what it makes harder later" |
| **Evolve** | `/retro` | log this session's mistakes as lessons; graduate repeats into rules/hooks/evals |
| | `/mine` | cluster failures into named mechanisms |
| | `/evolve` | mine → minimal edit → held-in + sealed held-out evals → promote only on no regression |
| | `/forge-agent` | create a specialist agent (incubator → evals → graduate) or retire unused ones |
| | `/audit` | context budget, unused skills/agents, MCP sprawl |
| | `/handoff` · `/start` | resumable snapshot · session card + next move |
| | `/projects [name]` | every project on one board: phase progress, in-flight tasks, gate, lessons, missing repos |

## Agents (16)

| Lane | Agent | Model | Job |
|------|-------|-------|-----|
| Build | `context-builder` | sonnet | ≤250-word BRIEF: prior work consumed, tasks, lessons, drift |
| | `architect` | opus | distill the verbatim contract · review conformance · draft arch |
| | `planner` | opus | every decision for one task → an exact plan (with file-overlap check) |
| | `builder` | sonnet | build to the plan in a worktree → tests → gate → one commit |
| | `reviewer` · `safety-reviewer` | opus | correctness · security + agentic-safety |
| | `gate-runner` | haiku | independent gate + tree + attribution check |
| | `clerk` | sonnet | reports, status, STATE.md, PRs. Never `verified` |
| Think | `scout` | sonnet | one source, evidence only, every claim linked |
| | `synthesizer` · `skeptic` | opus | cited merge · adversarial fact-check |
| | `councilor` · `chairman` | sonnet/opus | council member (answer / rank) · final verdict |
| Evolve | `miner` | sonnet | name failure *mechanisms*, rank by cost |
| | `harness-smith` | opus | one minimal harness edit per mechanism, on a branch, + eval tasks |
| | `agent-smith` | opus | draft new agents into `incubator/`, propose retirements |

## Hooks

| Event | What sage does |
|-------|----------------|
| `SessionStart` | injects the project card (and the last snapshot after a compaction) |
| `PreToolUse` | **guard**: rm→trash rewrite · no force/destructive ops · no attribution · sealed held-out · human-only `verified` · dead zones · secret-shaped writes · frozen referee for subagents · logs skill/agent usage |
| `PostToolUse` | runs the project's formatter on the edited file |
| `PostToolUseFailure` · `UserPromptSubmit` | traces tool failures and your corrections ("no bro, that's wrong…") for mining |
| `SubagentStop` | enforces the typed-handoff contract (one bounce, never loops) |
| `Stop` | optional per project: fast gate on uncommitted changes; blocks "done" on RED |
| `PreCompact` | writes a snapshot so the next context picks up exactly where you were |

## The homeboy

`.claude/output-styles/homeboy.md` is the default output style. It's slang, sarcasm, and it roasts
your *moves* (never you). Its morals outrank the bit: **honesty over comfort, always correct you,
never fake a fact or a result, jokes off when it's serious, and it'll tell you to go sleep.**
Code, commits and docs stay professional. Switch anytime with `/output-style`.

## Layout

```
sage/
├── CLAUDE.md                    # the map (+ ground rules import)
├── .claude/
│   ├── settings.json            # permissions, hooks, statusline, output style
│   ├── output-styles/homeboy.md
│   ├── agents/                  # 16 agents, three lanes
│   └── skills/                  # 19 slash commands + ground-rules
├── .mcp.json                    # github (read-only), context7, playwright, reddit
├── sagectl/                     # deterministic tooling (stdlib Python) + tests/
├── bin/sagectl                  # run without installing
├── projects/<name>/             # project.toml · CLAUDE.md · STATE.md · arch/ · phases/ · lessons.jsonl · evals/
├── library/                     # your cross-project knowledge: patterns, playbooks, stacks, papers, research, council
├── evals/harness/               # evals for sage itself (heldin / sealed heldout)
├── handoffs/SCHEMA.md           # typed handoff contract
├── incubator/agents/            # draft agents (not loaded until graduated)
├── _templates/                  # project, task, phase report, ADR, agent
└── docs/architecture.md         # how it all fits
```

`.sage/` (gitignored) holds local runtime state: traces, trash, gate cache, snapshots, eval results.

## Honest status

- **Built and tested:** `sagectl` (21 tests: guard, waves, cycles, promotion rule, split,
  mining, statusline, stack detection, trash), all hooks (smoke-tested with real payload shapes),
  agents, skills, output style, 3 seed harness evals (each verified to fail on the broken fixture
  and pass on a correct fix).
- **Needs real usage before it means anything:** `/evolve`. With a handful of eval tasks, one or
  two flips are noise. Expect ~50+ logged failures before mining finds real patterns. Until then,
  `/retro` every session and let the data build.
- **Verify on your machine:** MCP servers are pinned to `@latest` (pin exact versions once they
  work for you). LSP plugin names drift, so confirm with `/plugin`. `ENABLE_LSP_TOOL` comes from a
  community post (March 2026) and may be default by now.

## Credits

Ideas borrowed, with thanks: *Self-Harness* (weakness mining, held-out promotion), *Darwin Gödel
Machine* and *Hyperagents* (variant populations, improving the improver), Karpathy's *llm-council*
and the coding guidelines distilled in *andrej-karpathy-skills*, obra's *superpowers*
(brainstorm-before-code, fresh subagent per task), the r/ClaudeCode community (MISTAKES.md
graduation, hooks over prose, LSP, trash-not-delete, context audits). Design lineage: `sentinel-brain`.

## License

MIT. See [LICENSE](LICENSE).
