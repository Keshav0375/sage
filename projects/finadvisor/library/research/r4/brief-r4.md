# finadvisor research round 4: real data, data engineering at scale, guardrails, advanced RAG

Written 2026-11-02 by the orchestrator from Keshav's questions. This is the run brief for
`/researcher:run finadvisor`. Read it in full before stage 1.

## Hard rules for this run
- IMPLEMENTATION GATE (STATE.md): no builder agents, no branches, no code edits in FinAdvisor.
  This run ends at re-planned tickets. Keshav alone says when build starts.
- No GitHub publish in this run. Project #5 has 6 epics + 103 tickets already published
  (E0-E3 complete, E4 up to E4-T17). The re-plan states, per published issue: keep, update,
  or close; a later `/researcher:publish` applies it after Keshav approves.
- Binding inputs: `arch/overview/*.md`, `stack.md`, `plan.md`, `decisions.md` (ADR-001..025),
  `tracker.json`, `MVP.md` §13 gap register. Keep every Keshav decision in overview §1.2
  (Kong stays, FastAPI + React/TS, demo multi-tenant fully built in E1, ~$100-200/month
  demo-on-demand) unless evidence forces a change; then it is a question for Keshav, not a
  silent change.
- Pipeline rules: waves of <= 4 subagents, file handoff under `context/.runtime/research/finadvisor/`,
  slices instead of whole files, fresh session per stage if context grows large.
- Every load-bearing claim has a source link and date; the skeptic checks numbers, licences and
  API limits against the source.

## Defaults taken (Keshav may override at the stage-1 checkpoint)
- D-R4-1 Multi-region: designed completely and tested locally (two regional cells simulated in
  docker compose); cloud deploy stays one region within budget. A real second region is a costed
  option in the ADR, not built.
- D-R4-2 Client and advisor records stay synthetic (legal). Documents, regulations, product data
  and eval questions become real.
- D-R4-3 New methods (RAG or guardrails) enter only when an ablation on the real eval set shows a
  gain over the current pipeline.

## Problem statement
The v2 plan evaluates on a synthetic corpus and a synthetic golden set, so the eval does not show
real quality. A real deployment has big data, several regions, many logins, sources that update
and delete all the time, and documents and people that move between jurisdictions at different
pipeline steps. The system must stay correct end to end under those edge cases. Guardrails and
RAG must be built and measured against real documents.

## Track A: real data sources
Find, check and choose real public sources for each need. For each: URL, licence / terms of use,
access method (bulk, API, rate limit, User-Agent rules), size, update frequency, history/versions,
formats (HTML, PDF, XML, XBRL), languages, and jurisdiction.
- US regulation: eCFR API (17 CFR 275 and related, point-in-time versions), FINRA Rulebook.
- US products: EDGAR 497K / N-1A, N-PORT, XBRL risk/return; EDGAR full-text search and daily index.
- US advisor disclosures: SEC IAPD Form ADV Part 2A brochures.
- EU: EUR-Lex (MiFID II, PRIIPs) via CELLAR/SPARQL or API, ESMA Q&As and registers, PRIIPs KIDs.
- UK: FCA Handbook (COBS) access terms, FCA Register API.
- Eval Q&A: FinanceBench, FinQA, TAT-QA, ConvFinQA and newer financial RAG benchmarks; licence
  and fit for a compliance assistant. How to build a real golden set from real documents
  (human-checked, with Keshav labelling budget stated).
- Guardrail eval sets: PII (for example ai4privacy), prompt injection / jailbreak (deepset,
  JailbreakBench, newer), indirect injection in documents.
Output: a source catalogue with a recommended first set (smallest set that covers 3
jurisdictions, updates, deletes, tables and >1 language), and how the synthetic firm corpus
maps onto real documents (which firm sees which real documents, tier and jurisdiction tags).

## Track B: data engineering at real scale
Design questions, each answered with evidence from current docs and similar production systems:
1. Change capture from sources: scheduled diff vs feeds vs CDC; detecting updates and deletes in
   EDGAR, eCFR, EUR-Lex, FCA; source watermarks; late and out-of-order changes.
2. Document versioning: bitemporal model (valid time and system time), "as of date" queries,
   superseded versions, effect on chunks, the index and the answer cache.
3. Deletes everywhere (right to erasure and source withdrawal): Postgres, chunks and index, answer
   cache, GCS bronze, Parquet silver, BigQuery, Kafka retention, Langfuse traces, logs, backups.
   Tombstones, crypto-shredding vs physical delete, proof of deletion.
4. Jurisdiction and tenancy moves: document re-classification (exists, ADR-022), an advisor or a
   firm moving jurisdiction or region, data that must not leave a region.
5. Data contracts, schema evolution, data quality (Pandera, dbt tests), lineage (OpenLineage /
   Dagster), backfills during live traffic, replay, reconciliation (source vs bronze vs chunks vs
   index vs BigQuery counts and hashes) with alerts.
6. Re-embedding at scale: blue/green index on model change, cost and time at 100k-1M chunks.
7. Scale envelope: ingest throughput, Voyage/Anthropic rate limits, Kafka partitions, Postgres
   size, cost per 1k documents.

## Track C: system design for multi-region, reliability and edge cases
1. Residency and regional cells: cell-based architecture vs one global database; global control
   plane (tenants, routing, IdP) vs regional data plane; what Cloud SQL, Kafka (Confluent),
   BigQuery, GCS, Identity Platform and Langfuse allow per region; cost of a real second region.
2. Multiple logins: one advisor in several firms, SSO per firm, session and token rules across
   cells.
3. End-to-end failure and edge-case catalogue, each with the design control and the test that
   proves it: delete during ingest; ACL change during a streaming chat; PUBLIC document updated
   while cached; duplicate document in two firms; poison document; partial region outage; Kafka
   outage during deletes; replay after a bug fix; clock skew on "as of" queries; model retirement
   during a demo.
4. Test strategy for these: fault injection in compose, contract tests, chaos drills, synthetic
   probes; which gate in CI and which run weekly.

## Track D: guardrails on real data
Start from ADR-009 and overview §8. Research and decide:
1. Indirect prompt injection in ingested documents: scan at ingest, quarantine, spotlighting /
   delimiting in prompts; measured detectors.
2. Numeric and factual grounding: every number and date in an answer appears in a cited span.
3. Deterministic compliance checks in code: license scope, suitability rules, jurisdiction of
   cited sources vs advisor jurisdiction, stale-source warnings.
4. Tool-call authorization and output policy per role.
5. Guardrail metrics: precision, recall and latency per guardrail on the Track A sets; budget in
   the 2.0 s / 3.5 s TTFT targets.
6. Compare: Model Armor, Presidio, NeMo Guardrails, Llama Guard / newer open classifiers, and
   provider-native features, for cost, latency and fit.

## Track E: advanced RAG on real data
Start from ADR-008 and ADR-016 and the current non-goals in overview §1.3 (they may be revisited
only with ablation evidence). Research and decide:
1. Tables and structured data: XBRL facts and prospectus fee tables as structured lookups vs
   table chunks; Docling table quality.
2. Temporal retrieval ("as of" date) on versioned documents.
3. Multi-document comparison and multi-hop questions: query decomposition, agentic retrieval
   loops with a step budget, and their latency cost.
4. Multilingual retrieval for EU documents (voyage-4 multilingual quality, cross-lingual queries).
5. Span-level citations and the citation verifier on real documents.
6. Chunking for long regulatory text (structure-aware by article / section) and contextual
   retrieval on real data.
7. The ablation plan: which methods, on which real eval slices, with which metrics and pass lines.

## Stages and outputs
1. Stage 1 research (Tracks A-E in waves of <= 4 scouts + paper-scout + docs-readers), evidence
   to `evidence-r4.md`. Checkpoint: one message to Keshav with the source catalogue, the
   multi-region default (D-R4-1) and any money or scope question. Wait for his answer.
2. Stage 2 design: 2-3 solution-architect proposals (lenses: simplicity, reliability, learning
   value within budget) for the changed parts only; skeptic; decision file `decision-r4.md`.
3. Stage 3 arch: arch-writer updates overview sections, stack.md, ADR-026+ (and amendments),
   plan.md epics (changed epics and any new ones, e.g. "Real data onboarding", "Data lifecycle
   and deletion", "Regional cells"); diagrams for data flow, deletion flow and cells.
   `/researcher:validate` on the changed sections.
4. Stage 4 re-plan: ticket-writers for changed and new epics only (slices, waves <= 4); merge into
   `tracker.json`; a publish diff for project #5 (keep / update / close / new per issue).
5. Report to Keshav and stop. Update STATE.md. No build, no publish.

## Done when
- A source catalogue with licences and limits checked by the skeptic, and a chosen first set.
- A real eval plan: golden set from real documents, guardrail sets, ablation slices, pass lines.
- ADRs for change capture, versioning, deletion, residency/cells, guardrails on real data and
  advanced RAG choices, each with the edge-case tests that prove it.
- Re-planned tickets in `tracker.json` with no cycles, all S/M, failing acceptance criteria, and
  a publish diff for the 109 existing issues.
