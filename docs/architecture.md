# How sage works

## 1. The split: judgement vs determinism

```
            ┌───────────────────────── Claude Code session (orchestrator) ─────────────────────────┐
 Keshav ──▶ │  Homeboy output style · CLAUDE.md map · ground-rules · 18 skills (slash commands)    │
            │        │ fan-out (one message = parallel)                ▲ typed handoffs            │
            │        ▼                                                 │ (keyword first line)      │
            │  16 subagents: build lane · think lane · evolve lane ────┘                           │
            └────────┬──────────────────────────────────────────────────────────┬──────────────────┘
                     │ Bash                                                     │ every tool call
                     ▼                                                          ▼
            ┌──────────────── sagectl (stdlib Python) ────────────────┐   ┌──── hooks ─────────────┐
            │ where/waves · task · gate · arch · lesson · mine · eval │◀──│ guard · trace · format │
            │ trash · new · audit · card · statusline                 │   │ handoff check · stop   │
            └──────────────┬───────────────────────────────────────────┘   │ gate · snapshot       │
                           ▼                                               └───────────────────────┘
       projects/<p>/ (project.toml · arch · phases · lessons · evals)   library/   .sage/ (local)
```

Agents judge. `sagectl` and hooks do everything that must be right every time: locating
work, computing waves, running the gate, sealing held-out, moving deletes to trash. Rules that
live only in prose get ignored at turn 100. Rules in hooks don't.

## 2. Dynamic per project

Nothing project-specific is in code. `project.toml` declares repos, branch model, gate commands,
formatter, LSP servers, dead zones and research sources. `sagectl new` detects the stack
(pyproject → pyright/ruff/pytest, package.json → tsserver/prettier/tsc, go.mod, Cargo.toml,
Terraform) and proposes it; Keshav confirms. The active project is inferred from cwd, so the
same hooks, guard and statusline adapt to whatever repo you're in.

Behaviour is measured per project, not assumed. Each project has its own
`evals/{heldin,heldout}`, and harness changes are judged on them.

## 3. Build lane: the phase DAG

`TODO.md` tasks declare `deps`. `sagectl where` layers unbuilt tasks into **waves** (each wave
depends only on earlier ones; cycles are reported, never guessed through). `/build` plans a whole
wave in parallel (Opus planners, with a file-overlap check so parallel tasks can't collide),
builds it in parallel (Sonnet builders, one git worktree each), cherry-picks in id order, gates
once, then reviews with three Opus reviewers. Tasks stop at `review`. `verified` and phase
sign-off are human-only (the guard blocks agents).

## 4. Think lane: research + council

- `/research`: one `scout` per source (library first, then web, Reddit, Context7 docs, arXiv,
  GitHub) in parallel → `synthesizer` (consensus vs contested, cited) → `skeptic` (tries to falsify
  every load-bearing claim). Notes land in `library/research/`, so next time the library scout finds them.
- `/council`: Karpathy's llm-council pattern. Independent answers through different lenses,
  ideally on different models → anonymized peer ranking → chairman verdict that keeps the dissent.
- `/grill`: Socratic stress-test, one question at a time, highest risk first.

## 5. Evolve lane: the harness improves itself

```
 traces (hooks) ─┐
 lessons (/retro)├─▶ sagectl mine ─▶ miner ─▶ mechanism ─▶ harness-smith ─▶ branch evolve/<slug>
 corrections ────┘   (cluster)       (name)                (1 minimal edit + eval tasks)
                                                                     │
          held-in (visible)  ─┐                                      ▼
          held-out (sealed) ──┴─▶ sagectl eval run base vs cand ─▶ compare ─▶ PROMOTE / REJECT
                                                                              │
                                                              Keshav approves ┘ → merge
```

- **Weakness mining** (Self-Harness): failures cluster into *mechanisms*, not symptoms.
- **Minimal edits**: ≤ 15 lines, hooks preferred over prose, deletion allowed, CLAUDE.md never grows.
- **Held-out is sealed three ways**: split assigned by hash (nobody chooses), guard denies any
  read/edit/shell access to `evals/**/heldout`, and the referee code (`evals.py`, `guard.py`,
  `hooks.py`) is frozen for subagents.
- **Promotion rule**: held-in improves AND no held-out task that passed before fails now.
- **Improve the improver** (Hyperagents): the harness-smith's own prompt is evolved quarterly,
  scored by its proposals' promotion rate.
- **Lessons graduate**: same mechanism 3+ times → a rule or, better, a hook (`/retro`).

## 6. Safety

| Risk | Control |
|------|---------|
| Data loss | `rm` → `sagectl trash put` (rewritten in place); compound `rm`, `find -delete`, `git clean`, `dd`, disk erase denied |
| History loss | force-push, `reset --hard`, `branch -D`, `checkout --` denied |
| Reward hacking | sealed held-out, hash split, frozen referee, human promotion |
| Self-approval | `verified` / phase sign-off / `SAGE_HUMAN` blocked for agents |
| Secrets | `.env` reads denied; secret-shaped strings blocked from Write/Edit |
| Attribution | Claude co-author / "generated with" lines blocked in commits, PRs, GitHub writes |
| Shell blast radius | Claude Code `/sandbox` (bubblewrap / Seatbelt). Needs v2.1.2+ (CVE-2026-25725) |

## 7. Context economy

Every session pays for what loads every turn. sage's share is ~5K tokens (`sagectl audit`):
the CLAUDE.md map, ground-rules, one-line skill/agent descriptions, the output style. Skill
bodies load on use. Big reads go to subagents. Arch docs are read by section. MCP tools are
deferred. LSP replaces grep-walking for navigation.
