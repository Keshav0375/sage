# finadvisor: decisions (ADRs)

Newest first. Each entry: context, options with costs, evidence (docs, papers, council), decision,
what it makes harder later.

## ADR-001: As-built MVP is the baseline

Date: 2026-11-01. Status: accepted (decided by the orchestrator with Keshav).

**Context.** FinAdvisor is an interview-grade MVP, never deployed: Docker, CI on a real PR, `terraform validate`, the live eval and live Kong/LiteLLM/Langfuse checks were all deferred (`TODO.md:763, 818, 847, 877`; commit d6c2bd3). Its docs (README, architecture.md, mvp.md, threat model) disagree with the code in many places. Later research and architecture work needs one trusted statement of what actually exists.

**Options.**
1. Map the code as it is, and use that as the reference. Cost: one mapping and verification round, no design work yet.
2. Start from the docs' intended architecture. Rejected: the docs describe a JWT auth, Kong token budget and PII plugins, citation events and a working cloud deploy that the code does not have.
3. Design the target architecture now. Rejected for this run: no research has been done on scale, cost or compliance fit; the numbers Keshav gave (about 50 advisors, under 5 QPS, under $100 per month, US/EU/UK synthetic corpus) have not yet been checked against vendor facts.

**Evidence.** `arch/MVP.md` was built from four independent code maps, a skeptic re-read of the highest-risk claims, vendor-doc checks (pgvector, PostgreSQL 16 RLS, Voyage, LiteLLM) and spot-checks of every quoted `file:line` at d6c2bd3. It records 62 gaps: 13 critical, 16 high, 27 medium, 6 low (MVP.md §13).

**Decision.** `arch/MVP.md` records the code as of commit d6c2bd3 and is the reference for later research. `arch/stack.md` lists the stack as built. `arch/overview.md` keeps its template headings and records only goals and quality inputs; the target architecture is not yet decided and will be decided in later ADRs, each citing the gap IDs (G-nn) it resolves.

**What it makes harder later.** MVP.md goes stale as soon as the code changes: re-map before each research round and bump the commit hash in MVP.md §0. It also records defects as findings, not as decisions; nothing in it commits the project to fix, keep or replace any component.
