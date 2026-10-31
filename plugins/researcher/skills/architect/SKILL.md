---
name: architect
description: Create or extend a project's binding architecture in brain/projects/<p>/arch/ at solution-architect level — current docs, papers, competing designs, adversarial check, then Keshav's decision. Trigger /researcher:architect <project> <problem>.
argument-hint: "<project> <problem or feature>"
---

# /researcher:architect

The output is `brain/projects/<p>/arch/`: `overview.md` (sections from the template, with
diagrams), `stack.md`, `decisions.md` and `plan.md`. Architecture is binding, so every load-bearing choice needs evidence.
Follow the `base:pipeline` skill. The main session orchestrates; it never skips a step.

## 1. Frame (main session)
- Get the project card with `mcp__base__where`. Read the existing `arch/` by section.
- Write the requirements as numbers: users, QPS (peak and average), data size and growth,
  latency targets (p50, p99), availability, consistency needs, budget, team size, deadline.
- Missing numbers are questions for Keshav. Ask them now, in one message. Do not guess them.

## 2. Research (one message, in parallel)
- `researcher:reference-scout` — well-known systems that solved a similar problem, and the cloud
  vendor's reference architecture for this workload (Azure Architecture Center, AWS
  Architecture Center, Google Cloud Architecture Center).
- `researcher:docs-reader` ×N — one per key technology candidate: official docs, limits, vendor
  recommended patterns, pricing.
- `researcher:paper-scout` — when there is an algorithmic or distributed-systems core.
- `researcher:web-scout` — production experience: postmortems, benchmarks, migration stories.
- `Explore` — the current code, when the project has code.

## 3. Propose (one message, in parallel)
Spawn ≥2 `researcher:solution-architect`, each with a different lens (default: `simplicity` and
`scale`; add `cost` or `reliability` when they matter). Give each the same requirements and
evidence.

## 4. Validate and challenge (one message, in parallel)
- For each technology the leading proposal picks, a `researcher:docs-reader` checks it against the
  official docs at our numbers: confirms, contradicts, limits, vendor recommends.
- `researcher:skeptic` on the strongest proposal (or on each, if they are close).
Fold the `Improvements:` from the docs and the reference takeaways into the proposal before you
compare. This is the same check `/researcher:validate` runs on an existing design.

## 5. Decide (main session → Keshav)
Compare the options in one table: requirement fit, evidence strength, cost, operating burden,
what each makes harder later. Recommend one, with the reason and the strongest dissent.
Architecture decisions are Keshav's: present the recommendation and wait for his choice.

## 6. Record (delegate the writing)
After Keshav decides, spawn `researcher:arch-writer` with the decided design, the requirements,
the evidence links and the rejected options. It writes:
- `arch/overview.md` by section, with Mermaid diagrams: system context, containers/components,
  key flows (sequence), and deployment when infrastructure is in scope,
- `arch/stack.md`: the tech stack table with versions and official docs links,
- an ADR in `arch/decisions.md` (context, options with costs, evidence, decision, what it makes
  harder later),
- `arch/plan.md`: the high-level implementation plan, phases and epics in order.
Then the main session reads the result: diagrams match the text, every choice has evidence.
Remove the question from `STATE.md` open decisions. Next step: `/researcher:plan`.
