# finadvisor: state

## Now
- 2026-11-01 As-built baseline DONE: `deep-dive/00-as-built-baseline.md` maps the code at FinAdvisor d6c2bd3
  (diagrams, data model, interfaces, config, runtime, CI, tests, security posture) with a gap
  register of 62 gaps (13 critical, 16 high, 27 medium, 6 low). ADR-001 makes it the baseline.
  `deep-dive/11-tech-stack.md` filled as built; `overview.md` §1-2 hold the goals and Keshav's inputs.
- Inputs for later research: ~50 advisors, <5 QPS, <$100/month, US/EU/UK synthetic.
- 2026-11-01 Round 2 `/researcher:run` (target architecture). Keshav: demo multi-tenant (2-3
  firms, ~10 QPS, designed for 50), ~$100-200/month demo-on-demand, keep Python FastAPI,
  React+TS, ETL = synthetic + public source. Research wave done (9 scouts →
  `projects/finadvisor/library/research/evidence-r2.md`). Stage 2 done: 3 proposals, skeptic,
  Kong docs check → `decision-r2.md` (D1-D13, epics E0-E10). Keshav: Kong stays (D12).
  Stage 2-3 done: arch written (overview.md, deep-dive/11-tech-stack.md target, ADR-002..024, plan.md E0-E10),
  validated (docs check + consistency skeptic) and fixed (D14-D17 in decision-r2.md).
  Stage 4 stopped: the 11 ticket-writers hit the 5-hour usage limit before writing tickets.
  Restart Stage 4 in a FRESH session with per-epic slices, waves of ≤ 4 (new pipeline rules);
  do not resume the old ticket-writers (each carries ~100k of stale context of the old overview.md).
- 2026-11-02 Token audit of this session (observe usage.py, `projects/.runtime/traces/usage-*.md`):
  main loop Opus 28.4M cache read / 1.9M write; arch-writer 16.9M / 3.3M; ticket-writers 4.3M / 1.1M;
  docs-readers 4.7M / 0.8M. Fixes: model tiers (Haiku for mechanical + depth-2 page-readers),
  file handoff, slices, waves ≤ 4, fresh session per stage, overview.md split into overview/*.md.
- URGENT for builder: `claude-sonnet-4-20250514` retired 2026-06-15; app and evals fail today.

- 2026-11-02 Stage 4 done: 203 tickets in epic/ ticket files (11 epics, 5 phases), ADR-025 resolutions.
  GitHub project #5 https://github.com/users/Keshav0375/projects/5 : publish STOPPED by Keshav at
  6 epics + 103 tickets (E0-E3 full, E4 to T17) + 5 phase milestones. Plan will change.
- NEXT: research round 4 (real data, data engineering at scale, multi-region, guardrails,
  advanced RAG). Brief: projects/finadvisor/library/research/brief-r4.md. Run in a FRESH session.
- 2026-11-02 Round 4 stage 1 DONE: 8 evidence files + 2 skeptic passes in r4/, merged into
  evidence-r4.md. Keshav's checkpoint answers in checkpoint-r4.md (K-R4-1..4: keep D-R4-1;
  FCA API + legislation.gov.uk; publisher docs private only; 200-item golden set).
  NEXT: stage 2 design (2-3 proposals for the changed parts, skeptic, decision-r4.md) in a FRESH
  session: `/researcher:run finadvisor Continue round 4 at stage 2 per brief-r4.md`.
- 2026-11-07 Round 4 stage 2 DONE (decision-r4.md R4-D1..D17: base P-reliability, PG16 ranges,
  physical delete + tombstone ledger, Postgres queues for deletion and ACL, cells.json, E11-E13).
  Stage 3 arch WRITTEN: ADR-026..038 + amendments, deep-dive/01-context-and-goals.md §01-10 (04 split into 04/04.1/04.2,
  05 into 05/05.1), deep-dive/11-tech-stack.md, plan.md. Stage 3 validation IN PROGRESS (r4/V-docs-db.md,
  V-docs-ai.md, V-consistency.md). Then: fold fixes, stage 4 re-plan + publish diff, report.
- 2026-11-07 HALTED by Keshav for token use. Harness fixed: brain mod enforces model+effort tiers
  per step (routing.json `tiers`), budget guard (context ≥ 50%, window ≥ 75%), waves ≤ 3, replies
  ≤ 8 lines, leaves only for long sources. Validation state: V-docs-db.md DONE, V-docs-ai.md DONE,
  V-consistency.md STOPPED (partial). Verdicts so far: rerank-3 replaces rerank-2.5 as default
  (arm 3 = rerank-3 vs rerank-3-lite); BigQuery project default_max_time_travel_hours=48; Model
  Armor behind a flag + fallback; Voyage llm_egress_ack wording (opt-out, no region); spikes:
  Cloud SQL backups while stopped, Identity Platform same email.
  RESUME in a FRESH session: `/researcher:run finadvisor Continue round 4 at stage 3 validation:
  rerun the consistency check (r4/V-consistency.md), then fold the validation fixes per state.md`.
- (history) Round 4 stage 1 was stopped twice by the 5-hour limit. Evidence in
  projects/finadvisor/library/research/r4/. Done: A-us-sources.md, A-eu-uk-sources.md,
  A-eval-sets.md, BC-prior-art.md, leaf pages in r4/pages/. Missing: B-lifecycle-docs.md (pages
  saved, PG18/pgvector leaf missing), C-regions-docs.md, D-guardrail-tools.md, E-rag-papers.md,
  then Anthropic/Voyage rate limits, skeptic, merge to evidence-r4.md, Keshav checkpoint.
  Early findings: FINRA Rulebook terms forbid bulk copy and ML use (drop or licence); no public
  human-checked advisor-regulation QA set (own golden set 150-300 items); FCA site terms vs
  Handbook OGL conflict (unresolved).
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
