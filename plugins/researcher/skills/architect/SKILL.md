---
name: architect
description: Create or extend a project's binding architecture in context/projects/<p>/arch/ at solution-architect level — current docs, papers, competing designs, adversarial check, then an evidence-based decision recorded as an ADR. Trigger /researcher:architect <project> <problem>.
argument-hint: "<project> <problem or feature>"
---

# /researcher:architect

The output is `context/projects/<p>/arch/`: `overview.md` (sections from the template, with
diagrams), `stack.md`, `decisions.md` and `plan.md`. Architecture is binding, so every load-bearing choice needs evidence.
Follow the `brain:pipeline` skill. The main session orchestrates; it never skips a step.

## 1. Frame (main session)
- Get the project card with `mcp__brain__where`. Read the existing `arch/` by section.
- Write the requirements as numbers: users, QPS (peak and average), data size and growth,
  latency targets (p50, p99), availability, consistency needs, budget, team size, deadline.
- Take the numbers from the repo docs (README, architecture, MVP files) first. Estimate a number
  from evidence when you can, and mark it as an estimate. Ask Keshav, in one message, only the
  numbers that depend on his goals (users, budget, deadline, compliance scope).

## 2. Research (waves of ≤ 4 per `brain:pipeline`; independent inputs only)
One docs-reader per *decision-relevant* technology group (not per candidate); readers delegate pages
to Haiku page-readers. Each writes to `context/.runtime/research/<p>/`.
- `researcher:reference-scout` — well-known systems that solved a similar problem, and the cloud
  vendor's reference architecture for this workload (Azure Architecture Center, AWS
  Architecture Center, Google Cloud Architecture Center).
- `researcher:docs-reader` ×N — one per key technology candidate: official docs, limits, vendor
  recommended patterns, pricing.
- `researcher:paper-scout` — when there is an algorithmic or distributed-systems core.
- `researcher:web-scout` — production experience: postmortems, benchmarks, migration stories.
- `Explore` — the current code, when the project has code.

## 3. Propose (waves of ≤ 4 per `brain:pipeline`; independent inputs only)
Architects get the evidence digest path, not pasted evidence.
Spawn ≥2 `researcher:solution-architect`, each with a different lens (default: `simplicity` and
`scale`; add `cost` or `reliability` when they matter). Give each the same requirements and
evidence.

## 4. Validate and challenge (waves of ≤ 4 per `brain:pipeline`; independent inputs only)
- For each technology the leading proposal picks, a `researcher:docs-reader` checks it against the
  official docs at our numbers: confirms, contradicts, limits, vendor recommends.
- `researcher:skeptic` on the strongest proposal (or on each, if they are close).
Fold the `Improvements:` from the docs and the reference takeaways into the proposal before you
compare. This is the same check `/researcher:validate` runs on an existing design.

## 5. Decide (main session → Keshav)
Compare the options in one table: requirement fit, evidence strength, cost, operating burden,
what each makes harder later. **Pick one** from the evidence, with the reason and the strongest
dissent. Wait for Keshav only when the options are equal on evidence and the choice depends on his
preference, budget or compliance scope: then ask one short question with your recommendation.

## 6. Record (delegate the writing)
After the decision, spawn `researcher:arch-writer` with the decided design, the requirements,
the evidence links and the rejected options. It writes:
- `arch/overview.md` by section, with Mermaid diagrams: system context, containers/components,
  key flows (sequence), and deployment when infrastructure is in scope,
- `arch/stack.md`: the tech stack table with versions and official docs links,
- an ADR in `arch/decisions.md` (context, options with costs, evidence, decision, what it makes
  harder later),
- `arch/plan.md`: the high-level implementation plan, phases and epics in order.
Then the main session reads the result: diagrams match the text, every choice has evidence.
Remove the question from `STATE.md` open decisions. Next step: `/researcher:plan`.
