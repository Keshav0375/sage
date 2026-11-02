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
  Stage 4 stopped: the 11 ticket-writers hit the 5-hour usage limit before writing tickets.
  Restart Stage 4 in a FRESH session with per-epic slices, waves of ≤ 4 (new pipeline rules);
  do not resume the old ticket-writers (each carries ~100k of stale context of the old overview.md).
- 2026-11-02 Token audit of this session (observe usage.py, `context/.runtime/traces/usage-*.md`):
  main loop Opus 28.4M cache read / 1.9M write; arch-writer 16.9M / 3.3M; ticket-writers 4.3M / 1.1M;
  docs-readers 4.7M / 0.8M. Fixes: model tiers (Haiku for mechanical + depth-2 page-readers),
  file handoff, slices, waves ≤ 4, fresh session per stage, overview.md split into overview/*.md.
- URGENT for builder: `claude-sonnet-4-20250514` retired 2026-06-15; app and evals fail today.

- 2026-11-02 Stage 4 done: 203 tickets in tracker.json (11 epics, 5 phases), ADR-025 resolutions.
  GitHub project #5 https://github.com/users/Keshav0375/projects/5 : publish STOPPED by Keshav at
  6 epics + 103 tickets (E0-E3 full, E4 to T17) + 5 phase milestones. Plan will change.
- NEXT: research round 4 (real data, data engineering at scale, multi-region, guardrails,
  advanced RAG). Brief: context/.runtime/research/finadvisor/brief-r4.md. Run in a FRESH session.
- 2026-11-01 IMPLEMENTATION GATE: no build work (builder agents, branches, code edits in FinAdvisor)
  until Keshav says research is complete and tickets are ready to execute.

## Open decisions
- (only questions about scope, compliance or money; agents resolve the rest with evidence)
- Inputs needed from Keshav (accounts and money; ADR-025, not design):
  - K1 A GCP project id with billing and Identity Platform multi-tenancy enabled. Gates E1-T1 and all cloud tickets.
  - K2 Langfuse Cloud Hobby project keys, stored as GitHub secrets `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` and in local `.env`. Gates E0-T1.
  - K3 A domain for the ALB managed certificate. Gates E2-T8 and E10.
  - K4 About 30 human labels for the judge spike, labelled by Keshav with the CLI. Gates E7-T1.
  - K5 Enable branch protection on `main` after E0-T14 (R14). Gates the required-check acceptance of E0-T14.

## Blockers
- (none)
