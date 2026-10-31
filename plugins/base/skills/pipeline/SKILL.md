---
name: pipeline
description: The multi-agent protocol for any non-trivial task — research, decide, do, verify, declare, each owned by a different agent, fanned out in parallel. Use for features, fixes, architecture, and any answer where being wrong is costly.
---

# Pipeline: research → decide → do → verify → declare

No single agent owns more than one step. The main session orchestrates and thinks; subagents
gather, propose, build and check. A wave of independent subagents goes out in **one message** so
they run in parallel.

## 1. Research (≥2 subagents, different sources)
Spawn at least two research agents in one message, each with one source or lens:
- `think:docs-reader` — current official docs for every technology involved (Azure via
  Microsoft Learn, AWS, Google Cloud, Context7 for libraries), one agent per technology.
- `think:reference-scout` — well-known similar systems and vendor reference architectures,
  for any design decision.
- `think:paper-scout` — papers, when the task has an algorithmic or scaling core.
- `think:web-scout` — practitioner evidence: issues, postmortems, benchmarks, discussions.
- `Explore` — the code in the project's repos.

Each returns `EVIDENCE` with a source per claim. Skip a lens only when it clearly cannot apply,
and say which one you skipped.

## 2. Decide (main session, after ≥2 independent proposals)
For a choice with real tradeoffs, spawn ≥2 proposers in one message with different lenses (for
example `think:solution-architect` with lens=simplicity and lens=scale). They do not see each
other's answers. Then the main session:
- compares the proposals against the evidence,
- spawns `think:skeptic` on the leading option's load-bearing claims,
- decides, and writes down the decision, the rejected options, and what the choice makes harder.
An open decision in `STATE.md` goes to Keshav. Do not decide it.

## 3. Do (a builder, not the decider)
`build:builder` follows the plan in its own worktree. It makes no design decisions; a gap in the
plan comes back as `GAP`.

## 4. Verify (an agent that did not do the work)
Spawn in one message:
- `build:verifier` — runs the gate and checks each acceptance criterion with evidence.
- `build:reviewer` — correctness review of the diff.
- `build:safety-reviewer` — when the diff touches auth, IO, secrets, infra, or agent code.
Verifiers are read-only. Where possible, they run on a different model than the builder.

## 5. Declare (main session only)
State the result with the verifier's evidence: gate verdict, criteria met, findings open.
Say exactly what did not run. Never declare from the builder's own report.

## Model routing
Opus decides and reviews, Sonnet builds and reads, Haiku checks and fetches. Agent files set the
default; `brain/routing.json` overrides per agent type; an explicit `model` on the Agent call wins.

## When the task is small
A one-line fix or a factual question still separates do and verify: the main session may do it,
then a verifier (or the gate) checks it before you declare it.
