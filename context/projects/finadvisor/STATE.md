# finadvisor: state

## Now
- 2026-11-01 As-built baseline DONE: `arch/MVP.md` maps the code at FinAdvisor d6c2bd3
  (diagrams, data model, interfaces, config, runtime, CI, tests, security posture) with a gap
  register of 62 gaps (13 critical, 16 high, 27 medium, 6 low). ADR-001 makes it the baseline.
  `stack.md` filled as built; `overview.md` §1-2 hold the goals and Keshav's inputs.
- Inputs for later research: ~50 advisors, <5 QPS, <$100/month, US/EU/UK synthetic.
- 2026-11-01 Round 2 `/researcher:run` (target architecture). Keshav: demo multi-tenant (2-3
  firms, ~10 QPS, designed for 50), ~$100-200/month demo-on-demand, keep Python FastAPI,
  React+TS, ETL = synthetic + public source. Research wave done (9 scouts →
  `context/.runtime/research/finadvisor/evidence-r2.md`). Stage 2 done: 3 proposals, skeptic,
  Kong docs check → `decision-r2.md` (D1-D13, epics E0-E10). Keshav: Kong stays (D12).
  Stage 2-3 done: arch written (overview.md, stack.md target, ADR-002..024, plan.md E0-E10),
  validated (docs check + consistency skeptic) and fixed (D14-D17 in decision-r2.md).
  Stage 4: 11 ticket-writers running (one per epic). Next: check tickets → tracker.json → publish.
- URGENT for builder: `claude-sonnet-4-20250514` retired 2026-06-15; app and evals fail today.

## Open decisions
- (only questions about scope, compliance or money; agents resolve the rest with evidence)

## Blockers
- (none)
