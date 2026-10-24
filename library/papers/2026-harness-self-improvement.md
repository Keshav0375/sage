# Harness self-improvement: what sage borrows (read 2026-10-24)

Sources were read via search summaries. arxiv.org was unreachable from the build container,
so re-verify the numbers before citing them anywhere serious.

## Self-Harness: Zhang et al., arXiv 2606.09498
- Loop: **weakness mining** (cluster failed traces into recurring mechanisms) → **harness
  proposal** (small, targeted edits, one per mechanism) → **validation** (promote only with no
  measurable regression on held-out tasks).
- Reported held-out pass rates: MiniMax M2.5 40.5% → 61.9%, Qwen3.5-35B-A3B 23.8% → 38.1%,
  GLM-5 42.9% → 57.1%.
- Finding: it turns model-specific weaknesses into concrete, executable harness changes rather
  than generic instructions.
- Caveat (commentary): any verifier-driven loop can learn the shape of its evaluator.
- **In sage:** `sagectl mine` + `miner` (mining), `harness-smith` (proposal), `sagectl eval` with
  hash-assigned, guard-sealed held-out (validation), `/evolve` (loop, human-approved promotion).

## Darwin Gödel Machine: Zhang, Hu, Lu, Lange, Clune (ICLR 2026)
- Self-editing coding agent that keeps a population of variants. Parents are chosen by score +
  novelty. SWE-bench 20.0% → 50.0%, Polyglot 14.2% → 30.7%.
- **In sage:** every `evolve/<slug>` branch is a variant; rejected ones are logged in
  `library/evolve-log.md` so the search doesn't repeat itself.

## Hyperagents: DGM follow-up
- Task agent + meta agent in one editable program. **The improvement procedure itself is
  editable**, which is "improve the improver".
- **In sage:** quarterly `/evolve` on the harness-smith's own prompt, scored by its promotion rate.

## Related, not yet used
Meta-Harness (outer-loop code-space search over harnesses), Agentic Harness Engineering,
ModularRSI, RRSI (regularized RSI: edit-size budgets, which sage borrows as "≤15 lines, CLAUDE.md never
grows"), Harness-R1. Overview: Lilian Weng, "Harness Engineering for Self-Improvement" (2026-07-04).
