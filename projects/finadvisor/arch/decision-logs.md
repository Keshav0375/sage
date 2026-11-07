# finadvisor: decisions (ADRs)

Newest first. Each entry: status (date, decided-by), context, options with costs, evidence (docs, papers, council), decision, dissent, what it makes harder later, trigger to revisit.

## ADR-039: Stage 3 validation changes

**Status.** Accepted 2026-11-07 (round 4, stage 3). decided-by: researcher (orchestrator decisions R4-D18 and R4-D19). Source: `projects/finadvisor/library/research/r4/decision-r4.md` (section "Stage 3 validation decisions"). Amends ADR-002 (note), ADR-008, ADR-009, ADR-010, ADR-013, ADR-018, ADR-023, ADR-025, ADR-026 to ADR-029, ADR-035 to ADR-038 by dated blocks.

**Context.** Three checks ran on the stage-3 arch: database docs (`projects/finadvisor/library/research/r4/V-docs-db.md`), AI-provider docs (`projects/finadvisor/library/research/r4/V-docs-ai.md`) and an internal consistency audit (`projects/finadvisor/library/research/r4/V-consistency.md`, 8 must-fix and 24 should-fix findings). They found one stale model choice, two unenforceable settings, three unverified vendor claims, and several statements that contradicted each other.

**Options.** Per finding: keep, improve or change; the choice made is listed below. Where a finding conflicted with R4-D1 to R4-D19 the decision won and the finding is noted.

**Evidence.** V-docs-ai.md Q2 (Voyage lists `rerank-3` and `rerank-3-lite` as current; TPM 2M full, 4M lite; https://docs.voyageai.com/docs/reranker , https://docs.voyageai.com/docs/rate-limits ), Q3 (Model Armor GA, SLA and latency not published: https://docs.cloud.google.com/security-command-center/docs/model-armor-overview ), Q5 (Voyage retention and region: https://docs.voyageai.com/docs/faq ); V-docs-db.md (BigQuery project default: https://docs.cloud.google.com/bigquery/docs/default-configuration ; PITR range: https://docs.cloud.google.com/sql/docs/postgres/backup-recovery/configure-pitr ; dbt-bigquery configs page documents no dataset time-travel option); V-consistency.md M1-M7 and S1-S24.

**Decision.**
- V1 Reranker: default `rerank-3-lite`; confirmatory arm 3 is `rerank-3` vs `rerank-3-lite`; the full model enters only with a measured gain; `rerank-2.5` leaves the design (ADR-008, ADR-037; fixes M2, M4, S1).
- V2 BigQuery: project default `default_max_time_travel_hours = 48` via `ALTER PROJECT`; the per-dataset setting stays as a check; dbt sets no dataset options (ADR-029).
- V3 Model Armor: behind a feature flag with a fallback (Presidio + heuristics): ingest quarantine fails closed, prompts fail open with an audit flag (ADR-036, ADR-009).
- V4 `llm_egress_ack` wording: Voyage zero-day retention only after an irreversible org-admin opt-out; Voyage publishes no region; Anthropic first-party is US/global; the flag is acceptance, not a residency claim (ADR-038).
- V5 Spikes: Cloud SQL backup expiry while stopped (E12); Identity Platform same email in two tenants (E1, gates the identity tickets). PITR log retention: Enterprise 1-7 d, set 7.
- M1 Chunk identity is the 05-1 8-column key; generations are unique on it (it includes `embed_model`); the 3-column key is a non-unique reuse index (ADR-035, deep-dive 07, plan E6).
- M3 First-stage retrieval p95 <= 600 ms (embed then SQL, serial, 0.25 + 0.30 s estimated), measured in the E3 spike; TTFT 2.0 s p50 and 3.5 s p95 unchanged; the 02 budget and the E3 gate are recomputed. Dissent: the MVP's 300 ms is rejected because the arch's own estimate cannot meet it.
- M5 `chat.audit.v1` and `eval.sample.v1` carry ids, chunk ids, hashes, scores and flags only; text stays in Postgres `messages` (ADR-013, ADR-023).
- M6 FCA purge is a pull model: a PUBLIC `source_purges` table; each firm tenant's `erasure-worker` inserts its own `deletion_requests`; `fa_etl_public` gets no INSERT on firm tables; ADR-002 D13a stands (ADR-026, ADR-029).
- M7 Cache purge on document delete belongs to the `erasure-worker`, not the `acl-applier` (deep-dive 05-1 §5.7).
- M8 (section pointers) was fixed by script before this ADR. S1-S24 are applied as written in V-consistency.md, with no conflict with R4-D1 to R4-D19.

**Dissent.** The MVP's 300 ms first-stage target (rejected, M3). An INSERT-only exception on ADR-002 D13a instead of the pull model (rejected: it keeps a PUBLIC role writing firm rows).

**What it makes harder later.** The 600 ms first stage leaves 0.05 s of p95 slack over the estimate, so the E3 spike must measure both legs; the prompt path fails open when Model Armor and its flag are off, so the audit flag must be watched; a firm tenant that never runs its `erasure-worker` never applies an FCA purge, so `demo-up` runs the worker first; the `eval-judge` can no longer replay text from Kafka and skips messages that were erased.

**Proved by.** E3 spike (first stage p95 and rerank p95 on the default model). #15 with the pull model and no FCA or answer text in Kafka and BigQuery. Leak matrix: no `fa_etl_public` write on firm tables. E1 same-email spike; E12 stopped-instance backup spike. L0: private ingest with `llm_egress_ack=false` stays refused.

**Trigger to revisit.** Measured first stage above 600 ms; Model Armor publishes GA, SLA and latency; a `rerank-3` gain measured by arm 3; Voyage publishes a region or changes its retention terms.

## ADR-038: Residency promise wording and the LLM egress rule

**Status.** Accepted 2026-11-02 (round 4). decided-by: researcher (orchestrator decision R4-D10 on Keshav's K-R4-1). Source: `projects/finadvisor/library/research/r4/decision-r4.md`; r4/P-reliability.md §8; r4/S-skeptic-3.md H10. Amends the "real firm data" triggers of ADR-013 and ADR-018.

**Context.** K-R4-1 limits residency to data at rest. Anthropic's first-party API has `inference_geo` global or us only; Voyage regions are undocumented. Dropping the "exclude private EU text without an EU LLM path" filter leaves three egress paths for private text: the Anthropic prompt, Voyage embedding (ingest and query) and Voyage rerank. Redaction recall (Presidio) is unmeasured.

**Options.**
1. Exclude private EU documents in a cell with no EU LLM path (P-reliability). Rejected by K-R4-1.
2. Claude on Vertex AI in an EU region. Costed option only; availability UNVERIFIED; not built.
3. Promise data at rest, name the egress paths, and make egress a per-tenant configuration (chosen).

**Evidence.** https://platform.claude.com/docs/en/build-with-claude/data-residency ; Voyage FAQ https://docs.voyageai.com/docs/faq (ZDR opt-out, region silent); evidence-r4.md §0.4, §3.1; Anthropic Batch is not ZDR-eligible (evidence-r4.md §2.5); S-skeptic-3 H10.

**Decision.** Documented wording: "Data at rest (database, search index, document store, warehouse, event streams, traces) stays in the tenant's home cell. Prompt text and embedding and rerank inputs are processed by Anthropic and Voyage, which are US/global." Private EU text reaches Anthropic and Voyage (embed and rerank). Each tenant has a flag `llm_egress_ack`, default false; it must be true before private ingest (set true for the demo tenants). PUBLIC law is unaffected. Cells do not isolate an LLM-provider outage: an Anthropic or Voyage outage hits every cell, and ADR-031 says so. Provider retention is outside the erasure promise (ADR-029). A real second region and Claude on Vertex EU stay costed options. The "real firm data" triggers of ADR-013 and ADR-018 now read: real public documents and private demo publisher documents are allowed; real client data is still not.

**Dissent.** P-reliability: "real residency" by excluding private EU documents in a cell without an EU LLM path. Rejected by K-R4-1.

**What it makes harder later.** No EU-only processing claim can be made; redacted prompts may still carry PII until Presidio recall is measured (ADR-009); an EU claim needs a verified Vertex EU or Voyage region path and a new ADR.

**Proved by.** New L0 test: private ingest with `llm_egress_ack=false` is refused with zero provider calls. Stub providers record that private text leaves only when the flag is true, on all three paths. #6 variant: a provider outage returns `LLM_UNAVAILABLE` in every cell and is not reported as a cell failure.

**Trigger to revisit.** Anthropic or Voyage offers an EU region; a customer needs processing residency; Claude on Vertex EU is verified and priced.

**Amended 2026-11-07 (validation).** (1) The wording gains the declared global data: "Data at rest (database, search index, document store, warehouse, event streams, traces) stays in the tenant's home cell, except the declared global data (ADR-031)." (user id, email, firm membership, tenant-to-cell map, PUBLIC manifest hashes, aggregate metrics; Cloud Logging, Trace and Monitoring are single-region). (2) `llm_egress_ack` records the tenant's acceptance of the egress paths; it is not a residency or zero-retention claim: Voyage offers zero-day retention only after an organization admin opts out in the dashboard (a payment method on file is required and the opt-out cannot be reversed), Voyage publishes no data region, and its default training use is not stated; Anthropic first-party processing is US/global (R4-D18 V4; https://docs.voyageai.com/docs/faq , V-docs-ai.md Q5). (3) The source path now reads `library/research/r4/decision-r4.md`.

## ADR-037: Real golden set, guardrail sets, ablation protocol and statistics

**Status.** Accepted 2026-11-02 (round 4). decided-by: researcher (orchestrator decision R4-D15, R4-D16; Keshav K-R4-4). Source: decision-r4.md; r4/P-reliability.md §12; r4/S-skeptic-3.md. Amends ADR-017 and ADR-016.

**Context.** No human-verified US/EU/UK advisor-regulation QA set exists, and FinanceBench, FinDER and FinTextQA are non-commercial. K-R4-4 asks for 200 items labelled by Keshav with gains of about 5 points or more and above 100 effective items after clustering. P-reliability's ICC 0.3 had no source and its 6-per-document cap gave n_eff about 80-101 (S-skeptic-3).

**Options.**
1. Public benchmarks only. Rejected: NC licences, wrong jurisdictions.
2. Fixed n_eff claim with a design effect from an assumed ICC. Rejected: no source for ICC.
3. 200-item own set, document-clustered analysis, few confirmatory arms (chosen).

**Evidence.** https://arxiv.org/abs/2411.00640 (clustered SE, paired analysis); https://arxiv.org/abs/2311.09476 (ARES, PPI); Sartori and Garcia arXiv 2605.27789 [ABS]; Mangla arXiv 2603.23533 [PREPRINT]; evidence-r4.md §1.5-1.7, §E7; Anthropic pricing https://platform.claude.com/docs/en/about-claude/pricing (Sonnet 5.5 $2/$10 per MTok).

**Decision.** 200 items, public/private split (private items from 497K, KIDs, ADV run only where the private bucket is mounted, K-R4-3). Sampling: the cluster unit is the PROVISION or PRODUCT, not the whole file (a CFR section, an EU article or annex, a COBS chapter section, a legislation.gov.uk provision, or one fund, KID or brochure), at least 40 clusters and at most 5 items per cluster (R4-D17). Analysis at cluster level: per-document aggregation then sign-flip permutation, exact McNemar for binary metrics; no fixed n_eff claim; the detectable effect is computed after a 30-item pilot and recorded. At most 4 confirmatory ablation arms with Holm; other arms are exploratory and cannot enter the default pipeline alone (D-R4-3); slices under 30 items use exact tests or stay exploratory. The four confirmatory arms (R4-D17): (1) LLM contextual retrieval vs the free section-path prefix; (2) voyage-context-4 vs plain chunks; (3) `rerank-3` vs `rerank-3-lite` (default; the full model enters only with a measured gain, amended 2026-11-07); (4) structured lookup (SEC RR facts, KID fee tables) vs table chunks. Exploratory only: datamarking, single-shot query decomposition, cross-lingual query translation, others. The temporal validity filter is a correctness control, not an arm. Tier-1 deterministic metrics (evidence-span recall@10, MRR, gold-version-in-top-5, numeric-in-span, footer present, ASR); tier-2 Haiku 5.5 judge gates only if judge-human rho^2 >= 0.4. Ablation runs use the Message Batches API (50% off). Release gates (proposed lines, not sourced): citation verified >= 0.95, faithfulness >= 0.90, zero ungrounded numbers, zero cross-tenant/ACL/cross-cell leaks, correct refusal >= 0.90, recall@10 non-inferior (paired lower bound >= -2 pp), numeric-gate false rejects <= 3%, injection ASR <= 3 of 300. Guardrail sets: ai4privacy openpii (CC-BY-4.0), Gretel finance, Lakera gandalf (MIT), LLMail-Inject (MIT); licence recorded at integration.
Cost (R4-D16): Sonnet 5.5 at $2/$10 per MTok; steady delta about $22-30/month, first two months about $45; a budget alert at $180/month guards the $200 ceiling; `EVAL_BUDGET_USD` caps eval runs.

**Dissent.** P-simplicity and P-reliability: 200 items cannot separate most arms (conceded); counter: deterministic retrieval metrics have more power and "inconclusive means off". S-skeptic-3: realistic eval is $8-15 per run ($35-60/month with arms), so the $22-30 delta is optimistic and the $180 alert is the control.

**What it makes harder later.** Labelling takes about 39-56 h (ESTIMATE). The first public set has about 8-12 files (S-skeptic-3); clustering by provision or product keeps the 40-cluster floor reachable. Provisions of one act may correlate, so the detectable effect is computed from the pilot (above).

**Proved by.** #21 (injection ASR line on slice G plus LLMail-wrapped chunks, weekly). Stats unit tests: cluster aggregation, Holm family fixed, exact tests on slices under 30. L0 check on the sampling rule (at least 40 clusters, at most 5 items per cluster). Pilot-based detectable-effect record exists before arms run.

**Trigger to revisit.** Judge-human rho^2 below 0.4; the pilot shows a detectable effect above 10 pp; weekly run cost over the alert.

**Amended 2026-11-07 (validation).** Confirmatory arm 3 is `rerank-3` vs `rerank-3-lite` (the default model and the arm now match; the full model enters only with a measured gain, D-R4-3; R4-D18 V1). `rerank-2.5` leaves the design. The K-R4-4 criterion "above 100 effective items after clustering by source document" is replaced by the pilot-based detectable effect. With a floor of 40 clusters and a cap of 5 per cluster, 200 items means exactly 5 items in each of 40 clusters; the floor is raised if the corpus yields more usable provisions (V-consistency.md S7). Judge acceptance is judge-human rho^2 >= 0.4 only.

## ADR-036: Guardrails on real data: ingest scan, numeric gate, licence footers, role policy

**Status.** Accepted 2026-11-02 (round 4). decided-by: researcher (orchestrator decision R4-D14). Source: decision-r4.md; r4/P-reliability.md §11; r4/S-skeptic-3.md. Amends ADR-009.

**Context.** Real third-party text (publisher PDFs, ESMA and FCA content) can carry hidden or injected instructions. Model Armor latency, SLA and precision are NOT FOUND; spotlighting results are a 2023 GPT-3.5/GPT-4 study without Claude; no paper tests a plain regex numeric gate.

**Options.**
1. Query-time defences only (ADR-009). Rejected: poisoned chunks would already be indexed.
2. Prompt Guard 2 or an InjecGuard-class classifier at ingest. Ablation arms only (Llama 4 licence, CPU latency NOT FOUND, over-defense on "must", "ignore").
3. Datamarking as default. Rejected: delimiting only halves attack success and datamarking is a 2023 result; ablation arm only.
4. NeMo, LLM detectors on the hot path. Rejected (latency, ADR-009).
5. Layered ingest scan, quarantine, structure at query time, deterministic gates (chosen).

**Evidence.** https://docs.cloud.google.com/model-armor/quotas (1,200 QPM, 65,536-token and 4 MB limits, EXECUTION_SKIPPED); Spotlighting https://arxiv.org/abs/2403.14720 [PREPRINT]; InjecGuard https://arxiv.org/abs/2410.22770 [PREPRINT]; FinGround arXiv 2604.23588 [PREPRINT]; FinRegQA-EU arXiv 2609.36856 [ABS] (judges reward citation density); evidence-r4.md §4.

**Decision.** (1) Ingest scan: parse-time sanitiser (drop script/style, comments, hidden or off-screen text, zero-width and bidi characters), deterministic pattern list, Model Armor document screening windowed under 65,536 tokens and 4 MB, throttle <= 300 QPM of the shared 1,200; `EXECUTION_SKIPPED` fails closed into quarantine. (2) Quarantine (ADR-034): chunks never written. (3) Query time unchanged (ADR-009) plus a per-request random nonce; JSON-encode spotlighting by default, datamarking only as ablation arm A-INJ-2 on the model-visible copy; citation verifier and numeric gate compare against the original chunk text fetched by id. (4) Locale-aware numeric grounding gate per sentence (EN `1,234.56`, DE/FR `1.234,56` and `1 234,56`; rounding to stated precision, bps to % whitelisted, identifiers and the as-of date excluded, derived figures only from the `calc` tool); an ungrounded number withholds the answer with an escalate offer. (5) Deterministic compliance checks: `licence_footer` from `attribution_text` per licence class (a missing footer blocks release), jurisdiction label per citation with a mixed-jurisdiction warning, as-of validity (ADR-027), staleness by state for law. (6) Role policy as data in `policy.py`, default deny; a tool without a policy row fails CI. (7) Presidio for EN; DE/FR PII recall is measured before any claim. The Model Armor timeout is set from latency measured from the Cloud Run region, not 500 ms by default; a guard adding more than 150 ms p95 on the critical path moves async or is dropped. First visible text is the first complete sentence, not the first token (S-skeptic-3), so the TTFT budget is measured that way.

**Dissent.** Scanning trusted public law adds false-positive quarantines for little threat; counter: publisher PDFs and FCA/ESMA text are third-party and the eval needs the quarantine path exercised. Numeric gate has no published precedent; its false-reject rate is measured (ADR-037).

**What it makes harder later.** Gate false rejects on rounding, derived numbers and units; Model Armor free tier (2M tokens) is under the first full ingest (about $0.50 overage once, S-skeptic-3); quota is shared with prompt checks.

**Proved by.** #5 (malformed, oversized and injected files all quarantined or in the DLQ, consumers continue). #21 (slice G and wrapped chunks, ASR line of ADR-037). #22 (licence footer matrix; removing a footer blocks release). Hypothesis property tests of the numeric gate over locale formats. Role x tool matrix generated from `policy.py`. `EXECUTION_SKIPPED` quarantine test.

**Trigger to revisit.** Measured Model Armor latency or false positives outside tolerance; numeric-gate false rejects above 3%; a Claude-tested spotlighting result.

**Amended 2026-11-07 (validation).** Model Armor sits behind a feature flag with a documented fallback, because no GA status, SLA or latency is published and image screening is Preview (R4-D18 V3; https://docs.cloud.google.com/security-command-center/docs/model-armor-overview ; V-docs-ai.md Q3). Fallback: Presidio plus heuristic injection patterns. Ingest documents fail closed into quarantine; prompts fail open with an audit flag on the turn (the earlier "fail closed, `MODEL_ARMOR_FAIL_OPEN=false`" for prompts is replaced). Only text and PDF up to 4 MB are screened. The timeout is still set from latency measured in the E4 spike. `GUARD_UNAVAILABLE` now means the in-process fallback itself failed.

## ADR-035: Embedding generations (blue/green)

**Status.** Accepted 2026-11-02 (round 4). decided-by: researcher (orchestrator decision R4-D13). Source: decision-r4.md; r4/P-reliability.md §10; r4/S-skeptic-3.md.

**Context.** A new embedding model must be adopted without mixed-model vectors, with rollback, and without breaking erasure. `chunks` identity is the unique 8-column key `(tenant_id, document_id, provision_path, chunk_index, chunk_hash, valid_from, parser_version, embed_model)` (deep-dive 05-1 §5.10, ADR-027); `(tenant_id, chunk_hash, embed_model)` is only a non-unique reuse index, because a unique 3-column key would make text A, B, A impossible (amended 2026-11-07, R4-D19 M1).

**Options.**
1. In-place `UPDATE embedding`. Rejected: no rollback, mixed vector space.
2. A second index service. Rejected: new vendor.
3. Generations as rows beside the old ones (chosen).
4. Shared-parent generations: saves about 40% rows but couples generations. Rejected.

**Evidence.** Notion generations and gradual cutover (evidence-r4.md §2.4, https://www.notion.com/blog/two-years-of-vector-search-at-notion ); Voyage limits https://docs.voyageai.com/docs/rate-limits (voyage-4 8M TPM, 2,000 RPM; batch 33% off, 12 h window, up to 100K inputs); practitioner pattern (single author, evidence-r4.md §2.4).

**Decision.** `embed_generations(model_id, status in {building, validating, active, retired})` and `tenants.active_embed_model`. Build: `embed-backfill` embeds every distinct chunk text with the new model into green rows. Dual write while building. Validate: counts and `chunk_set_hash` equal, ANN self-hit >= 0.99, recall@10 non-inferior on the golden set (paired lower bound >= -2 pp), retrieval p95 <= +20%. Per-tenant flip of `active_embed_model` (eval tenant first); the cache key carries `embed_model`; queries inline the model literal from an allow-list so the per-model partial HNSW is used. Blue stays 7 days for rollback, then is physically dropped as an erasure-class operation with counts and VACUUM. Erasure and withdrawal delete by `doc_id`, so they hit both generations (ADR-029); the generation rows are erased with the chunk. The backfill's Voyage client is capped at 25% of RPM. Times recomputed under that cap: about 20 min at 100k chunks, 200 min at 1M (ceilings, not measurements). Cost at 100k chunks: $2.40 ($1.60 batch), possibly $0 inside the 200M free tokens; at 1M: $24 ($16 batch).

**Dissent.** Duplicated parents waste rows (shared parents save about 40% but couple generations). Kept separate for clean rollback.

**What it makes harder later.** Two generations double HNSW memory during overlap (1M chunks is outside the 8 GiB envelope; 250k per tenant is fine); HNSW build time at 100k-1M is unmeasured (E3 spike); adding a model needs the allow-list entry.

**Proved by.** #19 (half-built green: queries stay blue; flip: green; wrong-model query raises). #20 (erase a document during backfill: zero rows in both generations, receipt issued). #8 (replay twice after a parser bump: hash equals a single run, no duplicates).

**Trigger to revisit.** Voyage batch throughput measured far from the ceilings; a tenant above 250k chunks; HNSW memory over budget.

**Amended 2026-11-07 (validation).** Chunk identity is the unique 8-column key of deep-dive 05-1 §5.10, including `valid_from` and `parser_version`; an embedding generation is a row unique on that identity, which includes `embed_model`. The 3-column key `(tenant_id, chunk_hash, embed_model)` is a non-unique reuse index (R4-D19 M1; V-consistency.md M1). The statement in Context that `chunks` is unique on the 3-column key was wrong and is corrected above.

## ADR-034: Data contracts, quarantine and reconciliation

**Status.** Accepted 2026-11-02 (round 4). decided-by: researcher (orchestrator decision R4-D12). Source: decision-r4.md; r4/P-reliability.md §9; r4/S-skeptic-3.md. Amends ADR-014 and ADR-013 (contracts).

**Context.** Real sources return 200 with an HTML error page, drop fields, change layouts and shrink listings. A chunk in Postgres must mean that the version passed every gate; quality checks in one tool cannot be that gate (Dagster blocking behaviour across runs is undocumented).

**Options.**
1. Dagster asset checks as the gate. Rejected: in-run behaviour only is documented; used as early warning.
2. Great Expectations. Not evaluated (evidence-r4.md §6); rejected for scope.
3. OpenLineage as a gate. Dropped: `dagster-openlineage` 0.2.1 had no release in five months.
4. Contracts in code, blocking rules, exact-equality reconciliation (chosen).

**Evidence.** Pandera 0.35.0 (polars >= 1.20.0; LazyFrame validates schema only unless `PANDERA_VALIDATION_DEPTH=SCHEMA_AND_DATA`), dbt contracts (tables only; not views or snapshots), Dagster 1.13.28 blocking checks: evidence-r4.md §2.2 (PyPI JSON read 2026-11-02). Voyage rate limits https://docs.voyageai.com/docs/rate-limits.

**Decision.** Contracts: Pydantic to JSON Schema in Schema Registry, BACKWARD, CI check (ADR-013); dbt `contract: enforced` on gold tables; Pandera on silver with the depth variable set explicitly. A planted bad row must fail. Blocking rules (failure = `quarantined`, never indexed): licence_class and attribution non-null; jurisdiction and tier non-null; eCFR part has the expected section ids; every CELEX arrives with all three languages or none; every 497K has a recognisable fee table or is `parse_incomplete`; chunk token bounds; no empty `provision_path`; scan passed (ADR-036). More than 5% of a batch quarantined pauses the connector. Quarantine: version `status=quarantined`, bytes under `quarantine/` (never silver), operator `release|reject` recorded. The indexer's atomic gate (ADR-028) is the control. Reconciliation counts plus hashes at every hop, exact equality keyed on `parser_version` (a bump is a planned re-baseline, not an alert storm): source to bronze (sha256), bronze to silver and silver to chunks (`n_chunks`, `chunk_set_hash`), ANN self-hit canary (page below 0.95), Postgres to BigQuery (daily count and md5), cell vs cell PUBLIC manifest, tombstones (ADR-030). The hourly `reconcile` job runs only while the system runs. Backfill and replay are idempotent on `(tenant_id, chunk_hash, embed_model)` and `processed_events`.

**Dissent.** Exact equality is brittle across a parser change; mitigated by the `parser_version` key.

**What it makes harder later.** Every new store or topic needs an erasure step and a reconcile pair (CI lint); parser changes become planned re-baselines.

**Proved by.** #5 (poison corpus). #8 (replay twice after a parser bump: end state hash equals a single run, zero duplicates, zero resurrected tombstones). Planted-bad-row test for Pandera. Reconcile on fixtures per pair. ANN self-hit canary on a deliberately broken index.

**Trigger to revisit.** Quarantine rate above 5% on real sources; Dagster documents cross-run blocking; a maintained OpenLineage release.

## ADR-033: Tenant move protocol (copy, verify, cutover, erase)

**Status.** Accepted 2026-11-02 (round 4). decided-by: researcher (orchestrator decision R4-D10). Source: decision-r4.md; r4/P-reliability.md §8; r4/S-skeptic-3.md H9. Amends ADR-022 (reclassification lock).

**Context.** K-R4-1 asks for designed and locally tested cells, so a firm must be able to change cell, and people, entitlements and documents also move.

**Options.**
1. Offline runbook job that recomputes vectors (P-simplicity). Cheaper, but copies no embeddings and has no verify state machine.
2. One global database. Rejected: breaks residency and blast radius.
3. Copy, verify, cutover, erase, with rollback (chosen; Atlassian pattern).

**Evidence.** Atlassian data residency 2021 [OLD] (copy first, delete after all copies; on failure re-online then delete partial copies; evidence-r4.md §3.4); AWS cell-based architecture, "start with a cell migration mechanism from day one" (evidence-r4.md §3.4).

**Decision.** States `active -> freezing -> copying -> verifying -> cutover -> draining -> source_erased`. Freeze: chat disabled for the tenant and the outbox drained to 0. Copy: ordered per-table `COPY` of the tenant's rows (same `tenant_id`, embeddings as-is, same `embed_model`), GCS prefix copy, BigQuery export and load. Verify: row counts and `md5(string_agg(id||hash ORDER BY id))` per table equal. Cutover: publish a new signed `cells.json` atomically. The source tenant becomes `moved` (421) and is erased after a 7-day grace through ADR-029 with a receipt. Failure before cutover: unfreeze the source, delete partial target rows. Langfuse traces do not move. A person moving firm moves no data; each firm erases under its own policy. Advisor jurisdiction or tier change: `entitlement_version` bump, effective within 60 s; an in-flight turn re-reads it before each retrieval or tool step and before `done`, and a bump aborts with `ENTITLEMENT_CHANGED` and message `refused`. Text already streamed cannot be recalled (exposure bounded to one answer, p95 8 s); message rows holding text from a later-erased document are in erasure scope through `retrieval_chunk_ids`. Document reclassification keeps ADR-022 and takes the per-document advisory lock of ADR-028 so it cannot race an ingest.

**Dissent.** S-skeptic-3 and P-simplicity: a state machine nobody deploys; cells are a config seam plus an offline runbook. Counter: K-R4-1 asks for designed and locally tested cells.

**What it makes harder later.** Freeze means minutes of chat downtime at demo size; copy-verify cost grows with tenant size; traces are lost on move.

**Proved by.** #18 (kill the target mid-copy: source intact and unfrozen, target empty; success path counts and hashes equal). #2 (slow fake LLM, ACL change at token 20: abort, message `refused`, no citations released). #4 (erase from firm A: firm B and its cache untouched).

**Trigger to revisit.** A tenant too large to freeze; a real second cell is deployed.

## ADR-032: Multiple logins: one Identity Platform tenant per firm, no cross-firm identity merge

**Status.** Accepted 2026-11-02 (round 4). decided-by: researcher (orchestrator decision R4-D11). Source: decision-r4.md; r4/P-reliability.md §8; r4/S-skeptic-3.md. Builds on ADR-010.

**Context.** One advisor may belong to several firms. Identity Platform tenants are user silos; whether one email can exist in two tenants is UNVERIFIED (pages silent). Client facts: `currentUser` does not change when `tenantId` is switched, and `tenantId` is not persisted on reload.

**Options.**
1. One tenant, merged identity across firms. Rejected: identity must never be an authorization input across firms.
2. Per-firm email aliases and no switcher in v1 (P-simplicity). Fallback if the spike fails.
3. One Identity Platform tenant per firm, one token per firm (chosen).

**Evidence.** Identity Platform multi-tenancy docs (tenants as silos, `firebase.tenant` claim, project-level verification first; read 2026-11-01): evidence-r4.md §3.2. WorkOS and Slack keep identity global (evidence-r4.md §3.4).

**Decision.** One Identity Platform tenant per firm, one `advisors` row per `(tenant_id, idp_uid)`, one token per firm, no identity merge. The SPA keeps one auth instance per firm and a firm switcher; each API call carries one firm's token. The server verifies at project level, reads `firebase.tenant` and checks it equals the tenant in the URL and the cell map. A billing-enabled project is needed for more than 2 tenants. The "same email in two tenants" test is a spike ticket that gates the Identity Platform tickets in E1 (E1 is not built). If it fails, onboarding uses per-firm email aliases and a new ADR says so. Linking one person across firms is optional, opt-in UX, never an authorization input.

**Dissent.** P-simplicity: aliases and no switcher UI in v1. S-skeptic-3: the design rests on untested behaviour. Kept because E1 is unbuilt, so the spike gates it at no rework cost.

**What it makes harder later.** One auth instance per firm in the SPA; per-tenant SAML or OIDC setup is unverified; identity data location is unknown (treated as global, ADR-031).

**Proved by.** #17 (token A on firm B resource: 403 or 421; two sessions in one browser context keep separate `currentUser`). The same-email spike result is recorded as an ADR addendum before E1 identity tickets start.

**Trigger to revisit.** The spike fails; per-tenant OIDC or session-cookie problems; more than 50 tenants (ADR-010).

## ADR-031: Regional cells with a signed static directory and per-cell PUBLIC ingest

**Status.** Accepted 2026-11-02 (round 4). decided-by: researcher (orchestrator decision R4-D10 on K-R4-1). Source: decision-r4.md; r4/P-reliability.md §8; r4/S-skeptic-3.md. Related: ADR-002, ADR-013, ADR-038.

**Context.** K-R4-1: two regional cells designed and tested locally in docker compose, one region deployed, residency means data at rest. Cloud Run on a global ALB routes by latency with no cross-region failover; BigQuery errors on cross-location joins; Confluent cluster links need a Dedicated or Enterprise destination.

**Options.**
1. One global database. Rejected: residency and blast radius.
2. Global Cloud SQL replicas, cluster linking, a control-plane database. Rejected: unpriced, Enterprise-only, or 50 rows for an extra Cloud SQL.
3. Hash-mod partition routing. Rejected: cannot pin a region.
4. A cell is the whole data plane of one region; the control plane is a signed static `cells.json` (chosen).

**Evidence.** AWS cell-based architecture, thin router (evidence-r4.md §3.4); https://docs.cloud.google.com/run/docs/multiple-regions ; https://docs.cloud.google.com/bigquery/docs/locations ; https://docs.confluent.io/cloud/current/multi-cloud/cluster-linking/index.html ; https://langfuse.com/security/data-regions ; evidence-r4.md §3.1.

**Decision.** `cells.json` (tenant slug, `tenant_id`, `home_cell`, `residency_class`, endpoints) is signed, stored in GCS with a baked fallback, refreshed every 60 s; no control-plane database. Each cell physically holds only its tenants. `principal` checks `home_cell == this cell` and returns 421 plus a cell hint with zero DB reads otherwise. Per cell: Cloud Run, Cloud SQL, GCS, BigQuery dataset (location per cell; EU multi-region excludes London, so UK uses europe-west2), Confluent cluster and Schema Registry, Langfuse account (US Oregon or EU Ireland), KMS keyring, Model Armor endpoint. Nothing is shared or replicated across cells. PUBLIC is ingested independently per cell by its own `etl-public`; a manifest (document count and `chunk_set_hash` per version) alerts on drift. Global data (user id, email, firm membership, tenant-to-cell map, PUBLIC manifest hashes, aggregate metrics) is declared in the privacy notice. Per-cell hostnames route the SPA (`GET /resolve?slug=`). Two-cell docker compose suite (`cell-us`, `cell-eu` networks, a router serving `cells.json`; RAM 4-6 GB is an ASSUMPTION). Cells do not isolate an LLM-provider outage (ADR-038). A real second region is a costed option only; verified prices do not exist (evidence-r4.md §3.3), the P-reliability ESTIMATE is $15-40/month on demand or $90-150 standing, UNVERIFIED.

**Dissent.** P-simplicity: cells are a config seam and an offline runbook. Counter: only the `tenants.cell_id` column, the 421 check and the move protocol (ADR-033) exist in the one-region deploy.

**What it makes harder later.** A second real cell means two Confluent clusters, two Langfuse accounts and two BigQuery locations; ALB host rules are an unpriced spike; duplicate PUBLIC embedding costs about $1 per cell.

**Proved by.** #6 (stop cell-eu: US passes, EU tenants get 503 with a clear code, no US data touched). #16 (wrong-cell request: 421, DB query log empty). Compose separation test (a service in one cell cannot resolve the other). PUBLIC manifest equality across cells. `cells.json` unreadable: last good copy then baked fallback.

**Trigger to revisit.** A customer needs a deployed second region; Anthropic or Voyage region options (ADR-038); ALB host-rule spike fails.

## ADR-030: Proof of deletion: receipts, canary drill and the tombstone invariant

**Status.** Accepted 2026-11-02 (round 4). decided-by: researcher (orchestrator decision R4-D6, R4-D9, R4-D12). Source: decision-r4.md; r4/P-reliability.md §7; r4/S-skeptic-3.md H1.

**Context.** "Erased within N days" is the maximum over per-store windows, and no end-to-end erasure was ever measured (evidence-r4.md §2.3). BigQuery fail-safe and Cloud SQL PITR logs are documented windows and are not observable. Demo-on-demand stops the system, so a weekly cron cannot run.

**Options.**
1. A documented, unmeasured SLA. Rejected (evidence-r4.md §0.5 warns against it).
2. A weekly cloud canary measuring every store. Rejected: fail-safe, PITR and provider windows cannot be observed, and the system is often stopped.
3. Two-phase receipts, a canary at each demo start for observable stores, and the tombstone invariant (chosen).
4. Unlinking as proof of erasure. Rejected (Spotify Padlock; Presidio recall unmeasured).

**Evidence.** https://docs.cloud.google.com/bigquery/docs/time-travel (fail-safe not queryable); Langfuse deletion "usually within 15 minutes", no confirmation (evidence-r4.md §2.3); Spotify Padlock 2018 [OLD] (evidence-r4.md §2.3).

**Decision.** Receipt phase 1 "executed" (hours): `erasure_steps(request_id, store, status, executed_at, rows_affected, probe_result)`. Phase 2 "windows closed": `erasure-verify` runs each store's probe after its window timer, then signs the JSON receipt (HMAC with a KMS key, stored in GCS, hashed in the ledger). A receipt never says "erased everywhere" before phase 2. Scope is resolved by lineage (`lineage_edges`: bronze sha256, version, chunk hash, embed generation, cited messages, BigQuery events); lineage is never a gate. The canary drives a synthetic advisor with unique tokens through chat, trace, events and BigQuery, erases it, and records when each observable store reaches zero; it runs at each demo start. BigQuery fail-safe, PITR logs and provider retention are stated as documented windows, not measured. Invariant: tombstone implies absence in Postgres, GCS, BigQuery (current), Langfuse and the cache, with `tombstone_violations_total` = 0; reconcile checks hourly for 24 h after any erasure, then daily, only while the system runs. A resurrected row restarts that store's window (S-skeptic-3 H1), which is why ADR-028 uses uncached guards. Langfuse not honouring a delete: retry, alert at 24 h, receipt stays phase 1.

**Dissent.** P-reliability: a weekly cloud canary measuring the maximum of the last 12. P-simplicity: a simpler "10 d" promise. Rejected because nothing measures the unobservable windows.

**What it makes harder later.** Phase 2 needs 9 to 14 days; the system must be running for verify jobs (the erasure job runs first at every start, ADR-029).

**Proved by.** #24 (Langfuse stub returns 202 without deleting: alert fires, receipt stays phase 1). #7 (Kafka stopped, erasure issued: Postgres done, others pending; restart: all done, phase 1 issued once). #14 (restore then replay: counts 0). #1 (invariant after the race harness). A BigQuery probe test that proves only the 2-day time-travel window closed.

**Trigger to revisit.** Langfuse documents a confirmation; an observable fail-safe probe appears; the demo runs always-on.

## ADR-029: Erasure architecture: store windows, unlinking, ledger replay, no per-subject KMS

**Status.** Accepted 2026-11-02 (round 4). decided-by: researcher (orchestrator decision R4-D6, R4-D9; skeptic S-skeptic-3 #7, H2, H12). Source: decision-r4.md; r4/P-reliability.md §6; r4/P-simplicity.md (queue). Amends ADR-013 (topic retention).

**Context.** Real subjects (advisors, conversations) and withdrawn documents must be deletable from every store. Windows differ per store; per-row purge from backups does not exist; PG18 temporal FKs cannot cascade, so children are deleted explicitly.

**Options.**
1. Kafka-driven erasure. Rejected: a Kafka outage would delay deletes.
2. Per-subject KMS keys (crypto-shredding). Rejected: $0.72 per key per year (about $18/month at 300 advisors, $120 at 2,000), destroyed-key effect on standard backups undocumented. The 100 write TPM quota objection was CORRECTED by the skeptic and is not a reason.
3. Encrypting vectors, BigQuery AEAD, GCS retention lock, Kafka compaction. Rejected: defeats pgvector, undocumented, irreversible, at least 7 d plus cleaner.
4. Physical delete on all live stores, Postgres queue, ledger replay (chosen).

**Evidence.** https://cloud.google.com/bigquery/docs/time-travel ; https://docs.confluent.io/cloud/current/topics/manage.html (retention.ms default 7 d, segment.ms minimum 4 h); https://cloud.google.com/sql/docs/postgres/backup-recovery/backups ; https://docs.cloud.google.com/kms/quotas ; https://cloud.google.com/kms/pricing ; evidence-r4.md §2.3.

**Decision.** Queue: Postgres `deletion_requests` polled with `FOR UPDATE SKIP LOCKED` by `erasure-worker` (from P-simplicity); no Kafka on the delete path. `DELETE /v1/admin/documents/{id}` writes a `deletion_requests` row; `acl_change_requests` is for ACL and reclassification only (R4-D17, ADR-022). Ledger keyed as in ADR-028 holds salted hashes only, is exported daily to an append-only GCS object, and `erasure-replay` re-applies it after any restore before traffic. Subject rows carry a random `pseudonym_id`; deleting the mapping unlinks at once. Per-store: Postgres explicit ordered DELETE in one transaction with counts, then VACUUM (target < 24 h); GCS soft delete 0; BigQuery batched DML hourly on refs older than 30 min and `max_time_travel_hours=48` enforced on every dataset including dbt-created ones (2 d + 7 d fail-safe = 9 d); delete-policy topics with retention 7 d and `segment.ms` 1 d (about 8 d), payloads minimised to ids and `pseudonym_id`; Cloud SQL backups 7 d (PITR log retention 7 d, the Enterprise maximum; amended 2026-11-07); logs 7 d with no PII. Erasure re-sweeps each store at the end of its window. Promise wording, not "instant": live stores (Postgres, index, answer cache, GCS) within 24 h of the system running, and in demo-on-demand the erasure job runs first at every start; BigQuery and Kafka within 14 d; backups within 7 d plus ledger replay; Langfuse provider best effort ("usually within 15 minutes"), stated as provider-bound. Records under legal hold carry `retention_class` and the receipt says "retained: legal basis X".

**Dissent.** P-learning: an HMAC pseudonym with a deletable DEK row. Adopted only as `pseudonym_id` unlinking. Crypto-shredding dissent: "provable delete in backups"; rejected for cost and the undocumented backup effect.

**What it makes harder later.** The 14 d outer bound is a long tail (lever: no subject-linked rows in BigQuery gives 24 h); backups on a stopped Cloud SQL instance may not expire on schedule (untested).

**Proved by.** #7 (Kafka stopped during deletes). #14 (restore into scratch, replay, counts 0). #23 (erase within 5 min of events: removed on the next batch). #20 (erase mid re-embed). #4 (erase from firm A leaves B). Assertion that every BigQuery dataset has `max_time_travel_hours=48`. Test that backups expire on schedule while Cloud SQL is stopped.

**Trigger to revisit.** A customer demands cryptographic erasure; BigQuery or Kafka windows change; the 14 d bound is unacceptable.

**Amended 2026-11-07 (validation).** (1) The FCA purge is a pull model through a PUBLIC `source_purges` table (ADR-026 amended); the execution window is unchanged. (2) BigQuery: the project default `default_max_time_travel_hours = 48` is set with `ALTER PROJECT` (per region) so new datasets, including dbt-created ones, inherit it; dbt-bigquery does not document dataset options, so the per-dataset `max_time_travel_hours = 48` stays only as a check (the earlier "enforced on every dataset including dbt-created ones" had no mechanism) (R4-D18 V2; https://docs.cloud.google.com/bigquery/docs/default-configuration , V-docs-db.md). (3) Cloud SQL PITR log retention is set to 7 d (Enterprise range 1-7 d, default 7: https://docs.cloud.google.com/sql/docs/postgres/backup-recovery/configure-pitr); whether old backups expire while the instance is stopped is unverified and is an E12 spike (R4-D18 V5). (4) Subject-bearing topic payloads are ids, hashes, scores, flags and `pseudonym_id`; no text (ADR-013 amended).

## ADR-028: Atomic version publish, tombstones and per-document locking

**Status.** Accepted 2026-11-02 (round 4). decided-by: researcher (orchestrator decision R4-D5, R4-D6; S-skeptic-3 #2, #3, #10, H1, H5, H7). Source: decision-r4.md; r4/P-reliability.md §5. Amends ADR-022 (lock with ingest).

**Context.** Erasure, withdrawal, ingest and replay race. A 60 s cached tombstone check can miss a tombstone committed seconds earlier, and a resurrected BigQuery row restarts its window. A ledger without a tenant column would let firm A's erasure block firm B's ingest, and permanent tombstones block legitimate re-ingest.

**Options.**
1. Cache tombstones for 60 s in sinks. Rejected (S-skeptic-3 #2).
2. A tombstone keyed on document or subject hash only. Rejected: cross-tenant blocking.
3. Advisory lock, tombstone-first, uncached guards, tenant-scoped ledger key with release (chosen).

**Evidence.** PostgreSQL advisory locks and deadlock detection (S-skeptic-3 H7); Notion content-hash pattern (evidence-r4.md §2.1); r4/S-skeptic-3.md #2, #3, #10.

**Decision.** The indexer is the only writer of chunks. It embeds outside any transaction, then one transaction per document: `pg_advisory_xact_lock(hash(tenant_id, doc_id))` first, then check no tombstone and `contract_passed AND scan_passed`, insert or extend chunks, set the version `active`, purge cache rows, write `processed_events`, bump the tenant `corpus_version` row last (the order of deep-dive 04-2 §4.17; amended 2026-11-07). Erasure and withdrawal use the same order, one document per transaction, retry with jitter, and insert the tombstone first. Tombstone ledger key `(tenant_id, doc_key, sha256)` with an explicit operator `release` action (`released_at`) for legitimate re-ingest. Every sink (bq-sink, silver, contextualizer, indexer) guards writes with an UNCACHED point read of the ledger in its own write path (no 60 s cache) and pauses if it cannot read it; the silver worker checks before and after writing Parquet and deletes its own output if a tombstone appeared. Erasure re-sweeps each store at the end of its window (ADR-029). A chunk in the table means the version passed every gate; Dagster checks are advisory (ADR-034).

**Dissent.** P-reliability's 60 s cache saves reads; rejected because it defeats the race control.

**What it makes harder later.** A long erasure blocks that tenant's publishes (hence one document per transaction); the hot `corpus_version` row serialises a tenant's publishes; operators must handle `release`.

**Proved by.** #1 (N interleavings of erase vs indexer, including a tombstone committed immediately before the sink write; zero rows or objects). #4 (tombstone key includes `tenant_id`: erase in A, B still ingests). Ledger release test (FCA module revoked then reinstated re-ingests after `release`). Two concurrent multi-document erasures plus an ingest storm: no deadlock loss, lock order held. #8 (zero resurrection on replay).

**Trigger to revisit.** Publish throughput limited by the `corpus_version` row; deadlock aborts above noise.

**Amended 2026-11-07 (validation).** The publish order is cache purge, `processed_events`, then the tenant `corpus_version` bump last, one transaction per document (not per document version), as in deep-dive 04-2 §4.17 (R4-D5; V-consistency.md S21).

## ADR-027: Bitemporal documents and chunks on Postgres 16 ranges, as-of semantics and cache key

**Status.** Accepted 2026-11-02 (round 4). decided-by: researcher (orchestrator decision R4-D3, R4-D4; S-skeptic-3 #1, #5, H3, H4, H8). Source: decision-r4.md; r4/P-reliability.md §4; r4/P-simplicity.md (`reconcile_lineage`, `valid_from` in key). Amends ADR-015.

**Context.** Real law has versions, revocations and reinstatements, and "as of" is a compliance question. The arch binds PG16. PG16 cannot declare an exclusion constraint on a partitioned parent. Text A, B, A again must be representable.

**Options.**
1. PG18 `WITHOUT OVERLAPS` (P-learning). Rejected: PG16 binding, temporal FKs cannot cascade, PG18 re-tests E0-E3.
2. XTDB. Rejected: no erasure, budget.
3. Overwrite `documents.status`. Rejected: cannot answer "as of".
4. PG16 `daterange` valid time and `tstzrange` system time (chosen).

**Evidence.** https://www.postgresql.org/docs/16/ddl-partitioning.html (no exclusion constraint across a partitioned table); https://www.postgresql.org/docs/17/release-17.html (added in 17); https://www.postgresql.org/docs/18/sql-createtable.html (temporal FKs cannot cascade); pgvector iterative scan https://github.com/pgvector/pgvector ; FiscalQA Pro arXiv 2608.09393 [PREPRINT]; evidence-r4.md §2.2.

**Decision.** `document_versions` (unpartitioned): `EXCLUDE USING gist (tenant_id =, doc_id =, valid_range &&) WHERE upper_inf(system_range) AND status NOT IN ('ingesting', 'quarantined', 'erased')` (`btree_gist`); closed system-time history is not constrained, and upserts use a separate unique key because `ON CONFLICT DO UPDATE` cannot arbitrate on an exclusion constraint. `chunks` (LIST per tenant, ADR-003): the EXCLUDE goes into the per-tenant partition-creation migration on each leaf, with an L0 test that every leaf has it. Chunk identity includes `valid_from` and `parser_version`, so replay after a parser fix re-parses (no "same bytes = no-op") and A-B-A text is representable. `reconcile_lineage(doc)` is one idempotent transaction that derives the target chunk set from the ordered versions and swaps the old parse atomically; it covers late, out-of-order, withdrawn and replayed versions. Unchanged chunk hashes extend `valid_to` with no embed call. As-of: `as_of` comes from the deterministic date parser, the UI chip, or the Postgres date in UTC, never the model; half-open ranges; the answer echoes the parsed `as_of`; a post-generation check requires every cited chunk's `valid_range @> as_of`; CI checks every retrieval SQL carries the predicate. UK sources use `valid_from_basis='observed'` and refuse pre-observation dates. Cache key adds `as_of`, `embed_model`, `source_epoch`; any publish, supersede, retire, withdraw or erase bumps `corpus_version` in the same transaction and deletes `answer_cache` rows by `source_document_ids`. Conversations and messages are plain rows, not bitemporal.

**Dissent.** P-learning: native `WITHOUT OVERLAPS` is cleaner and teaches more. Rejected for the PG16 binding. P-simplicity: current text only. Counter: the first corpus has the versions that make "as of" real.

**What it makes harder later.** Moving to PG18 temporal constraints is a migration; superseded rows are post-filtered by iterative scan with no recall guarantee under RLS plus LIST partitions (E3 spike with 30% superseded rows; partial index `WHERE is_current` is the trigger).

**Proved by.** #3 (cached answer, then a new version: miss and new text; hit inside the publish transaction re-verified). #8, #11 (versions v3, v1, v2 in all permutations, plus an A-B-A reversion: identical final line). #9 (boundary days, app clock +/-2 h, DST). #13 (silent edit). #25 (FCA question as of 2019 refused). L0 every-leaf EXCLUDE test. Bump parser, replay: no chunk of the old parse is retrievable. As-of echo present in the answer.

**Trigger to revisit.** Recall or p95 miss in the superseded-row spike; a decision to move to PG18.

**Amended 2026-11-07 (validation).** The system-time column is `system_range` everywhere (not `sys_range`), and the EXCLUDE predicate carries the `status NOT IN ('ingesting', 'quarantined', 'erased')` clause of deep-dive 05-1 §5.9 (V-consistency.md S2).

## ADR-026: Source connector framework, listing-diff change capture and source classes (retire vs erase)

**Status.** Accepted 2026-11-02 (round 4). decided-by: researcher (orchestrator decision R4-D1, R4-D2, R4-D8; Keshav K-R4-2, K-R4-3). Source: decision-r4.md; r4/P-reliability.md §2-§3; r4/P-simplicity.md (FCA path); r4/S-skeptic-3.md H6.

**Context.** The first real corpus mixes law, regulator Q&A and publisher documents with different licences, revocability and delete signals. Feeds miss silent edits and hard deletes. The FCA Handbook API is current-only and revocable, and its terms require deleting copies on revocation (cl.13).

**Options.**
1. Per-source scripts. Rejected: no shared idempotency or delete rules.
2. Feeds or CDC only. Rejected: EDGAR removals appear only in the weekly rebuild; cursors miss silent edits (Airbyte).
3. Crawl the FCA Handbook. Rejected: cl.35.3 bans crawlers. FINRA dropped (terms ban copying and ML use).
4. One framework: append-only observations, full-listing diff as truth for deletes, feeds only accelerate (chosen).

**Evidence.** https://handbook.fca.org.uk/footer-widget/terms-and-conditions ; https://www.finra.org/terms-of-use ; https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data ; https://www.ecfr.gov/api/versioner/v1 ; https://eur-lex.europa.eu/content/legal-notice/legal-notice.html ; https://www.esma.europa.eu/about-esma/legal-notice-and-data-protection ; https://legislation.github.io/data-documentation/reuse-licence.html ; evidence-r4.md §1, §2.1.

**Decision.** Sources: eCFR 17 CFR 275 (versioner API, gzip, 1 rps), SEC RR quarterly datasets (structured facts) plus 497K (2 rps, declared User-Agent), EUR-Lex CELLAR PRIIPs and MiFID in EN/DE/FR (1 rps), legislation.gov.uk (1 rps), FCA Handbook API (current only). ESMA Q&As optional, with the ESMA transformed-text disclaimer. Publisher documents (KIDs, 497K, ADV brochures) are `private_demo`: firm tenant only, never in the public repo or public eval sets. One interface (`list`, `changes`, `fetch`, `classify`). `source_observations` is append-only on `(source_id, external_id, version_key, content_sha256)` with the cursor, overlap and `last_listing_at` on `source_registry` updated in the same transaction (there is no `source_state` table); incremental reads overlap by 48 h; ordering uses the source's version key. Same bytes is a no-op; same `version_key` with new bytes is a `silent_edit` event and alert. Withdrawal needs two consecutive listings without the item; mass-delete breaker (more than 5 items or 10% of a source) freezes the connector; an empty listing is a failure. Source classes: law and Q&A are RETIRED (`valid_to` set, text kept for as-of); FCA API and publisher documents are ERASED (ADR-029). FCA content lives only in the PUBLIC tenant and never enters Kafka or BigQuery. `purge_source('fca_api')` runs as the PUBLIC owner role, bumps `source_epoch`, and writes a row to the PUBLIC `source_purges` table; each firm tenant's `erasure-worker` pulls it under its own role and enqueues its own erase job for messages and cached answers quoting FCA text; no cross-tenant write (ADR-002 D13a stands; amended 2026-11-07). The connector suspends on 401 or 403 and the purge is drilled quarterly.

**Dissent.** Skip FCA until written consent (revocable API, conflicting licence texts); the kill switch bounds exposure and K-R4-2 chose to include it.

**What it makes harder later.** Listing diffs double read volume (seconds at this size); a revocation mid-demo removes UK COBS; legal view on publisher documents is pending (evidence-r4.md §0.3); each source adds a fixture set.

**Proved by.** #12 (listing returns 0 or drops 30%: nothing applied, connector frozen, page). #13 (silent edit). #15 with the pull model (purge on fixtures empties PUBLIC and writes a `source_purges` row; each firm tenant's erasure-worker enqueues and erases its own messages and cache rows quoting FCA text; leak matrix shows `fa_etl_public` has no write on any firm table; FCA content and chat answer or excerpt text absent from Kafka and BigQuery). Retire vs erase policy test per source class.

**Trigger to revisit.** FCA grants consent or changes the API terms; counsel rules on publisher documents; a second revocable source.

**Amended 2026-11-07 (validation).** `purge_source` is a pull model: it erases the PUBLIC rows, bumps `source_epoch` and writes one row to a PUBLIC `source_purges` table that every tenant may read; each firm tenant's `erasure-worker` run, under that tenant's own role, polls it and inserts its own `deletion_requests`. `fa_etl_public` gets no INSERT on firm tables, and ADR-002 D13a stands. Chat events carry no answer or excerpt text, so FCA text cannot reach Kafka or BigQuery through them (ADR-013 amended). No `source_state` table exists; cursor, overlap and `last_listing_at` live on `source_registry`. R4-D19 M5, M6; V-consistency.md S3.

## ADR-025: Planning resolutions for the v2 tickets

**Status.** Accepted 2026-11-01. decided-by: researcher (orchestrator resolutions R1-R85, round 3 ticket questions). Source: `projects/finadvisor/library/research/resolutions-r3.md`. Amends ADR-010 (R19). Items K1-K5 are account and money inputs for Keshav, not design.

**Context.** The ticket-writers for epics E0-E10 raised questions the architecture left open or set "in Ex". Each resolution follows the arch or picks the simplest default the arch allows. Numbers below are exact as decided; keys named here are in deep-dive/06-interfaces-and-contracts.md §6.6 (cited to this ADR).

**Options.** None compared here. Each item was decided by the orchestrator; where an earlier ADR already decided the matter, that ADR wins (R19).

**Evidence.** resolutions-r3.md (R1-R85); ADR-002 and ADR-004 (entitlement cache TTL, R19); ADR-003 (ANN trigger, R16); ADR-022 (acl-applier); ADR-024 (VPC egress, R4). No new external sources were added by this ADR.

**Decision.**

Cross-cutting
- R1 Spike ADRs: a spike ticket writes `docs/adr/<topic>.md` in FinAdvisor with measurements and the fallback taken; after merge the researcher copies it into `arch/decision-logs.md` as the next ADR number.
- R2 Migrations: E0-T9 creates revision 0001 = MVP `schema.sql`, immutable. E1 adds 0002+ that drop and recreate the MVP content tables with no data migration (never deployed).
- R3 Table ownership: E1 creates every table in deep-dive/05-data-model-and-storage.md §5.2, including `answer_cache`, `turn_events` (with `request_hash`), `escalations`, the `halfvec(1024)` and `tsv` columns. E3-T4 adds only the HNSW and GIN indexes and the iterative-scan settings. E3-T13 adds only the `AnswerCache` class.
- R4 Cloud provisioning: local and CI bootstrap is E1-T3. Cloud SQL roles, passwords, the `dagster` database, Cloud Run jobs (`migrate`, `etl`, `etl-public`, `dbt`, `maintenance`, `eval`) and Cloud Scheduler are E10. VPC, Private Google Access, the private `run.app` zone, fa-gateway, ALB, Cloud Armor and the log sink are E2 (`terraform/edge/`); E10 reuses them. The SPA bucket is E10; E2-T8 takes it as a variable. BigQuery datasets, tables, authorized views and row policies are repo-managed idempotent DDL in E6-T17.
- R5 Weekly eval runs from a GitHub Actions cron (E7-T13); no Cloud Scheduler for evals.

E0 (repo and tooling)
- R6 Model lifecycle check: an allowlist in config of known model ids with retirement dates. Unknown ids fail. A model fails when retired or retiring within 30 days (`MODEL_RETIRE_WARN_DAYS`, default 30). A deprecated model with no retirement date passes with a warning.
- R7 `DB_PORT` (default 5432) added to §6.6.
- R8 E0-T10 adds vitest and the dev image to the current Next.js app; E8-T1 replaces it with Vite (accepted throwaway).
- R9 E0 compose holds postgres, kafka, migrate, api, frontend. Kong + Valkey come in E2-T11, Schema Registry in E5-T3, worker in E5-T9. The self-hosted Langfuse compose and Redis are removed.
- R10 The root Poetry project is removed; `backend/poetry.lock` is the one lockfile (G-28).
- R11 Historical MVP docs stay as history under an allowlist; `.claude/settings.local.json` is untracked and removed from git.
- R12 Removing the MVP Kong service from Terraform in E0-T7 is intended; E2 adds the target gateway.
- R13 E0-T13 deletes `eval-gate.yml`; E7-T11 adds the new gate.
- R14 Branch protection required checks are a manual step for Keshav after E0-T14, listed in its acceptance criteria as a `gh api` check the builder can only report.
- R15 `JWT_SECRET` stays required with no default until E1-T15 removes it. `EMBED_MODEL` / `EMBED_DIM` belong to E3-T3.

E1 (data, auth)
- R16 Planner-cost pass line for the partition spike: planning time p95 <= 10 ms at 52 partitions, and the ADR-003 trigger (ANN p95 <= 100 ms).
- R17 Neutral `app.*` values for principal load: nil uuid, empty role, tier `0`, empty jurisdictions. With these values RLS returns no content rows.
- R18 First advisors come from a seed command `migrate --seed-advisors <file>` in E1-T11, used by demo setup. No auto-provision on first login.
- R19 Entitlement cache: TTL-only, 60 s (ADR-002 and ADR-004 win). The ADR-010 text is fixed accordingly (ADR-010 "amended by ADR-025").
- R20 `MESSAGES_RETENTION_MONTHS` default 6.
- R21 The DEFAULT-partition alert for `chunks` and `messages` is E9 (log-based metric + alert).
- R22 `fa_tenant_lookup(NULL, NULL)` returns no rows. Discovery never resolves the PUBLIC tenant (404).
- R23 Auth tests: Firebase Auth emulator in CI if the E1-T1 spike shows it supports multi-tenancy; else locally signed test JWTs with a test JWKS. E1-T1 records which.

E2 (gateway and edge)
- R24 `X-RL-Key` fallback: if `pre-function` cannot run before `rate-limiting`, limit by IP only and rely on the chat-api per-tenant budget; record it in the spike ADR.
- R25 The 50 ms SSE budget compares ALB+Kong against ALB direct to a test route on chat-api.
- R26 Rate limits (from 10 QPS peak, ~300 advisors): `RATE_LIMIT_IP_PER_MIN` 300 on all routes; `RATE_LIMIT_TOKEN_PER_MIN` 120 on api routes; `RATE_LIMIT_CHAT_PER_MIN` 20 per session on chat routes. Valkey down: fail open (`fault_tolerant: true`); chat-api budgets still apply.
- R27 `INPUT_MAX_CHARS` 4000; Kong request-size limit 64 KB until E4 and after.
- R28 Client IP hash: HMAC-SHA256 with a secret salt from Secret Manager (`AUDIT_IP_SALT`).
- R29 `pre-function`: metadata server failure returns 503 (fail closed). Missing `Authorization` on chat/api routes returns 401 at Kong.
- R30 Client identity headers are stripped on all routes, including tenant-discovery.
- R31 Cloud Armor: no geo allow-list (demo users travel); throttle 600 req/min per IP; OWASP CRS preconfigured rules `sqli-v33-stable`, `xss-v33-stable` in preview first. Cost pass: <= $10/month idle.
- R32 E2-T21 cloud acceptance uses the E10 demo-up Valkey; E2-T21 moves to depend on E10's demo-up ticket. Pin Valkey 8.0 (Memorystore) and `valkey/valkey:8.0` locally.
- R33 nginx `error_log` level `crit` on proxied routes; the T15 test proves no query string reaches Cloud Logging.
- R34 Two Kong services, same upstream: chat routes with `read_timeout` 3,600,000 ms; others default.
- R35 The Kong ID-token check runs against the stub in E2; E10 re-runs it against the real chat-api.

E3 (retrieval)
- R36 Other rerank errors (5xx, network, bad response) fall back like a timeout with reason `error`. `embed_query`: 2 retries with jitter, then the turn fails with `RETRIEVAL_UNAVAILABLE` (`EMBED_MAX_RETRIES` = 2).
- R37 Degraded gate: pass if RRF returns at least `GATE_MIN_RESULTS` (default 2) candidates; the answer is marked `retrieval_degraded`.
- R38 E3-T16 sets the initial `GATE_MIN_SCORE`; E7-T7 sets the final value.
- R39 `STALE_AFTER_MONTHS` default 12; one key for retrieval, gold models and UI.
- R40 `SEARCH_TOP_K_MAX` 10 and `RETRIEVAL_LEG_LIMIT` 40 become §6.6 keys.
- R41 E4 owns verifier and cache wiring in the orchestrator; E5-T11 (acl-applier) and E1-T12 (maintenance) own purge call sites.
- R42 PUBLIC changes rely on the PUBLIC `corpus_version` in the cache key; no cross-tenant purge.
- R43 `FACTSHEET_MAX_CHUNKS` default 8; E4 can change it.
- R44 import-linter names the chat-api source roots; worker and job code stay outside.
- R45 Seeded synthetic vectors are fine for ANN latency; recall is measured in E7 with real embeddings.

E4 (agent)
- R46 Citation verifier on rejection: strip the unverified `[n]` marker, keep the sentence, count `citation_rejected_total`. If no verified citation is left in an answer that needs one, the turn becomes a refusal. Overlap threshold `CITATION_MIN_OVERLAP` default 0.5, tuned by E7.
- R47 Tenant token budget: daily window (UTC), counters in Postgres `tenant_usage` (no Valkey dependency in chat-api), `TENANT_TOKEN_BUDGET` default 2,000,000 tokens/day, `TENANT_MAX_CONCURRENCY` 20.
- R48 `turn_id` = uuid5(namespace, tenant_id || advisor_id || Idempotency-Key) (as deep-dive/05-data-model-and-storage.md §5.2). `turn_events.request_hash` = SHA-256 of the canonical JSON request body (sorted keys); the same Idempotency-Key with a different hash returns 409. Deltas batch every 250 ms or 512 chars.
- R49 Resume tails by polling `turn_events` every 250 ms. After `SSE_REPLAY_TTL_S` (default 600) resume returns 410 `TURN_EXPIRED`.
- R50 Presidio pseudonyms stay redacted in output; no re-identification.
- R51 MVP `litellm/` directory removal is E0-T6.

E5 (events)
- R52 E5 defines minimal payload models; E4, E6, E7 add fields when they produce the event.
- R53 Keys: `KAFKA_CONSUMER_MAX_ATTEMPTS` 5, `KAFKA_RETRY_BACKOFF_MS` 500, `OUTBOX_RELAY_BATCH` 100, `OUTBOX_RELAY_POLL_MS` 500; added to §6.6.
- R54 E4-T21 owns the outbox insert helper; E5-T12 depends on it.
- R55 The metrics conventions module is E9; E5 emits `outbox_unpublished` as an OTel gauge now.
- R56 One `oneOf` schema per topic under `<topic>-value`; `dlq.v1-value` registered.
- R57 Gap closed: no ticket built the `bq-sink` worker role; it is added to E5.

E6 (ETL)
- R58 Pipeline payloads: E5 envelope + id-only payloads.
- R59 Pandera: a failed chunk is rejected alone; a document with > 20% failed chunks is rejected whole.
- R60 Synthetic corpus: 60 documents per tenant, 3 tenants; 10k-chunk set for benchmarks.
- R61 E6 depends on E5-T7 (consumer framework), E5-T9 (worker entrypoint), E5-T11 (acl-applier, which updates the denormalised ACL columns).

E7 (eval)
- R62 E7-T16 owns the `eval.sample.v1` outbox row; E4 owns the feedback endpoint.
- R63 Judge acceptance: Cohen's kappa >= 0.6 against human labels. SUPERSEDED 2026-11-07 by the judge-human rho^2 >= 0.4 gate of ADR-017 (amended) and ADR-037.
- R64 PR gate uses the point estimate; the weekly full run uses the CI lower bound.
- R65 Baselines live in `data/eval/` in the repo.

E8 (frontend)
- R66 Playwright runs against a stubbed API and the Firebase Auth emulator; one smoke spec runs against compose.
- R67 Firebase web config comes from `VITE_*` build env; E10 sets it in the deploy job.
- R68 `GET /v1/conversations/{id}/messages` returns `retrieval_degraded` and the caller's feedback score; E4 adds them.
- R69 `escalate_offer=true` shows a hint and an "Ask compliance" button that sends the follow-up turn.
- R70 SSE resume: 5 attempts, backoff 1, 2, 4, 8, 16 s.

E9 (observability)
- R71 Shared metrics module `backend/src/observability/metrics.py` is created by E9-T5. Earlier epics emit with plain OTel meters and E9-T5 moves them to the registry.
- R72 Alert numbers: outbox oldest age > 300 s, ACL apply lag > 120 s, consumer lag > 1000 for 10 min; availability burn rate 14.4x / 1 h and 6x / 6 h.
- R73 `llm_cost_usd_total{provider,model}` computed from token counts and a price table in config (`LLM_PRICE_TABLE_JSON`); the budget alert uses GCP billing plus this metric, against `LLM_MONTHLY_BUDGET_USD` = 75.
- R74 `readiness_failing` and `model_retirement_days` (gauge) added to §9.2.
- R75 Notification channel: email to `alert_email`.
- R76 The maintenance job runs every 15 min in demo mode (E10 schedules it); the DEFAULT-partition alert window is 30 min (with R21).
- R77 OTel export: direct OTLP to the Google Cloud Telemetry API endpoint with ADC, no sidecar. E9-T2 checks this first; fallback is an OTel Collector sidecar, recorded as a spike ADR.

E10 (infrastructure and demo ops)
- R78 Backups: demo profile daily automated backups, 7 retained, PITR off (RPO 24 h, RTO 1 h); prod profile PITR on, 7-day log retention (RPO 5 min, RTO 1 h).
- R79 A `db-bootstrap` Cloud Run job as `fa_owner` creates roles and writes passwords to Secret Manager versions; no passwords in Terraform state.
- R80 Scheduler pause state goes in `ignore_changes`. Crons (UTC): etl daily 02:00, etl-public weekly Mon 03:00, dbt daily 04:00, redteam weekly Sun 05:00, maintenance every 15 min (R76); eval weekly is GitHub Actions (R5). Demo-down pauses all.
- R81 `DEMO_TTL_HOURS` 4.
- R82 Kong reads the Valkey endpoint from env `KONG_VALKEY_HOST` / `KONG_VALKEY_PORT` (E2-T11 sets the names); fa-gateway Terraform does not ignore them; demo-up applies them.
- R83 SPA bucket: uniform bucket-level access, `allUsers` with `roles/storage.legacyObjectReader` only (object read, no listing). Static assets only, no data. This is an explicit, recorded exception to "no allUsers"; the rule covers Cloud Run services and stays in force for them.
- R84 Demo-down drain checks run inside a Cloud Run job.
- R85 Terraform apply and deploy use the GitHub environment `prod` with Keshav as required reviewer.

Inputs from Keshav (accounts and money, not design)
- K1 A GCP project id with billing, Identity Platform multi-tenancy enabled (E1-T1, all cloud tickets).
- K2 Langfuse Cloud Hobby project keys, stored as GitHub secrets `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` and in local `.env` (E0-T1).
- K3 A domain for the ALB managed certificate (E2-T8, E10).
- K4 About 30 human labels for the judge spike: Keshav labels them with the CLI (E7-T1).
- K5 Enable branch protection on `main` after E0-T14 (R14).

**Dissent.** None recorded.

**What it makes harder later.** The SPA bucket is publicly readable (R83): nothing but static assets may ever be placed in it. The 60 s TTL-only entitlement cache (R19) means an entitlement revocation takes up to 60 s to apply. Tenant budgets in Postgres (R47) add a write per turn to `tenant_usage`. Dropping and recreating the MVP tables in E1 (R2) is safe only while nothing is deployed.

**Trigger to revisit.** A spike ADR (R1) records a fallback; the R16 or R25 pass lines fail; the R47 default budget does not fit the measured demo load; the SPA bucket gains non-static content.

**Amended 2026-11-07 (validation).** R63 (Cohen's kappa >= 0.6) is superseded by judge-human rho^2 >= 0.4 (ADR-017 amended, ADR-037). R78: RPO 5 min and RTO 1 h are ESTIMATES; the prod 7-day PITR log retention is the Cloud SQL Enterprise maximum (range 1-7 d, default 7). R82: the Kong Valkey keys `KONG_VALKEY_HOST` and `KONG_VALKEY_PORT` are listed in deep-dive 06 §6.6 (V-consistency.md S6, S24).

## ADR-024: VPC egress mode: Direct VPC egress private-ranges-only, no Cloud NAT

**Status.** Accepted 2026-11-01. decided-by: researcher (orchestrator rulings D15.2, D16.12). Resolves G-11 (wiring) and keeps G-26 closed.

**Context.** Kong must reach `chat-api` (ingress internal) through the VPC, while every service also calls public SaaS APIs (Anthropic, Voyage, Model Armor, Confluent, Langfuse). An all-traffic egress route needs Cloud NAT for the public calls.

**Options.**
1. Direct VPC egress, all-traffic routing, Private Google Access, plus Cloud NAT for public SaaS: simple routing, about +$32/month (D16.12).
2. Direct VPC egress `private-ranges-only`, Private Google Access on the subnet, and a Cloud DNS private zone mapping `run.app` to `private.googleapis.com` so the internal `run.app` URL of `chat-api` is reached through the VPC; public SaaS calls leave directly; no NAT (chosen).
3. Serverless VPC Access connector. Not chosen: Direct VPC egress is the documented newer path with a startup probe requirement.

**Evidence.** https://docs.cloud.google.com/run/docs/authenticating/service-to-service ; Direct VPC egress and Private Google Access notes in decision-r2.md D15.2 and D16.12; Cloud Run VPC docs https://cloud.google.com/run/docs/configuring/vpc-direct-vpc .

**Decision.** All Cloud Run services and jobs use Direct VPC egress in `private-ranges-only` mode with a startup probe; Private Google Access on the subnet; a Cloud DNS private zone maps `run.app` to `private.googleapis.com`. No Cloud NAT. The E2/E10 spike verifies Kong to `chat-api` over this path (deep-dive/10-open-questions.md §10 item 3).

**Dissent.** None recorded.

**What it makes harder later.** Egress to SaaS has no fixed source IP (no allow-listing by IP). The private-zone mapping is a DNS trick that must keep working across Cloud Run changes.

**Trigger to revisit.** The spike fails: switch to all-traffic egress + Cloud NAT (about +$32/month) and record an ADR.

## ADR-023: Gateway audit through Cloud Logging and BigQuery

**Status.** Accepted 2026-11-01. decided-by: researcher (orchestrator ruling D16.9). Resolves G-48.

**Context.** The MVP Kong `http-log` posts to `/api/audit/kong`, which does not exist (G-48). An HTTP log target on `chat-api` would need the IAM header that Kong's `http-log` cannot add, and would put gateway volume through the outbox.

**Options.**
1. Kong `http-log` to an internal FastAPI route `/internal/audit/gateway` and the outbox. Needs service IAM and adds an unauthenticated-looking internal route.
2. Kong `file-log` to stdout with a field whitelist, to Cloud Logging, then a log sink to BigQuery `gateway_audit` (chosen). Logging costs $0.50/GiB after 50 GiB per project (evidence-r2.md).
3. Gateway events on a Kafka topic. Not chosen: no Kafka producer in the gateway path.

**Evidence.** decision-r2.md D16.9; Cloud Logging pricing in evidence-r2.md.

**Decision.** Kong `file-log` to stdout with a whitelist (timestamp, route, method, status, latency, request id, client IP hash; no `Authorization`, no bodies, no query strings). A Cloud Logging sink exports to BigQuery `gateway_audit`. The `/internal/audit/gateway` route and the `gateway.audit.v1` topic do not exist; `chat-api` serves no `/internal/*` endpoints.

**Dissent.** None recorded.

**What it makes harder later.** Gateway audit rows carry no verified tenant (Kong cannot see it); correlation to a tenant goes through `X-Request-Id` and the application audit. The whitelist is a security control that must be reviewed when plugins change.

**Trigger to revisit.** Per-tenant gateway audit is required; log volume exceeds the free logging allowance.

**Amended 2026-11-07 (validation).** BigQuery `chat_audit` and `eval_events` receive ids, hashes, scores and flags only, never answer, question or excerpt text (R4-D19 M5; ADR-013). Gateway audit is unchanged.

## ADR-022: Asynchronous ACL changes through acl_change_requests and an acl-applier worker

**Status.** Accepted 2026-11-01. decided-by: researcher (orchestrator rulings D14.8, D14.9, D16.8). Resolves G-20, G-21 (no app write on content tables).

**Context.** The first draft let the `admin` module call `retrieval.update_acl` and gave `fa_app` UPDATE and DELETE grants on `documents` and `chunks`. That widens the write surface of the user-facing role on the tables the whole isolation design protects, and made `chat-api` the cache-invalidation point (a Kafka listener on every instance).

**Options.**
1. `fa_app` updates ACL columns directly (first draft). Synchronous, but `chat-api` can write content.
2. Synchronous call from `chat-api` to a worker service. Adds a service and a network hop.
3. Admin API writes an `acl_change_requests` row plus an outbox event in one transaction; a worker applies it as `fa_worker` (chosen).
4. A Kafka listener in every `chat-api` instance for cache invalidation. Rejected: chat must not depend on Kafka, and a background consumer needs CPU outside requests on Cloud Run.

**Evidence.** Notion: a permission change is a metadata patch, with no re-embedding (https://www.notion.com/blog/two-years-of-vector-search-at-notion ); RLS write split D13a; decision-r2.md D14.8-D14.9, D16.8.

**Decision.** `chat-api` never writes content tables. `POST /v1/admin/documents/{id}/acl-changes` (and `DELETE /v1/admin/documents/{id}`) inserts an `acl_change_requests` row and an `AclChangeRequested` outbox row in one transaction and returns 202. The `acl-applier` worker role consumes `acl.changes.v1` and, as `fa_worker` (UPDATE grants on the ACL columns of `documents` and `chunks` only, own-tenant WITH CHECK), applies the change, marks the request `applied`, bumps `tenants.acl_version` and purges `answer_cache` rows that cite the document. Advisor entitlement changes remain a direct `UPDATE advisors` by a `tenant_admin`. `chat-api` does not consume Kafka; the 60 s `principal` cache TTL is the revocation bound for entitlements. For documents, `acl_version` in the answer-cache key makes older cached answers unreachable once the applier commits, and a cache hit that raced the bump is re-verified against freshly fetched chunks under the caller's RLS.

**Dissent.** None recorded.

**What it makes harder later.** The old ACL applies until the applier commits (relay plus consumer lag, tracked as `acl_apply_lag_s`); admin UX is two-step (202, then status); failed requests need operator handling.

**Trigger to revisit.** The lag is unacceptable (add a synchronous path or push invalidation, with a new ADR); a second ACL source appears.

**Amended 2026-11-02 (round 4).** The applier no longer depends on Kafka; the rest of the decision above stands. The `acl-applier` polls `acl_change_requests` in Postgres with `FOR UPDATE SKIP LOCKED`; the outbox row and `acl.changes.v1` remain for analytics only. A Kafka outage therefore cannot delay an ACL tightening (test: stop Kafka, tighten an ACL, the answer is refused within 60 s). Applying a change takes the per-document advisory lock first and the tenant `corpus_version` row last (ADR-028), so a reclassification cannot race an ingest. `DELETE /v1/admin/documents/{id}` writes a `deletion_requests` row (ADR-029) and no longer goes through `acl_change_requests`, which carries ACL and reclassification changes only (R4-D17). Reclassification and entitlement moves: ADR-033.

## ADR-021: CI/CD with GitHub Actions, WIF and a gated deploy

**Status.** Accepted 2026-11-01. decided-by: researcher. Resolves G-05, G-06, G-28, G-47, G-51.

**Context.** The MVP CI cannot install its tools (`dev` extra missing), the eval gate cannot run, images build from unpinned floors, Terraform has no pipeline and image tags default to `latest`. One developer needs a pipeline that is cheap, keyless and blocks regressions.

**Options.**
1. Keep the MVP workflows and patch. Cost: unpinned builds, no deploy path.
2. GitHub Actions + Workload Identity Federation + Artifact Registry + Cloud Run tagged revisions (chosen). Cost: free runner minutes within plan; no stored cloud keys.
3. Cloud Build / GitLab. Rejected: second system, no gain.

**Evidence.** `gcloud run deploy --tag pr-N --no-traffic` preview pattern and WIF (evidence-r2.md, Compute / CI section); Cloud Run docs https://cloud.google.com/run/docs ; deep-dive/00-as-built-baseline.md §9 and G-05, G-06.

**Decision.** GitHub Actions with WIF. Lockfile installs only. Python: ruff, mypy, pytest, import-linter; frontend: eslint, tsc, vitest; security: trivy, gitleaks, pip-audit; `kong config parse`; `terraform fmt`, `validate`, `plan` on PR. L0 and the ~60-question eval subset run on the runner with real pgvector and Kafka service containers (ADR-017). Images pushed to Artifact Registry and referenced by digest. Deploy order: `migrate` Cloud Run job before traffic, then a tagged no-traffic revision, smoke test, then traffic shift. Provider keys for evals come from the CI secret store. CI service containers and compose pin `pgvector/pgvector:0.8.5-pg16` to match Cloud SQL (D16.20).

**Dissent.** None recorded.

**What it makes harder later.** The eval gate costs LLM money on every PR touching the path filter; the PR subset is kept to ~60 questions for that reason. Service containers pin the CI Postgres / Kafka versions, which must track the Cloud SQL and Confluent versions.

**Trigger to revisit.** CI cost or duration grows past the budget; more than one developer needs preview environments.

## ADR-020: Demo-on-demand operations and Cloud SQL sizing

**Status.** Accepted 2026-11-01. decided-by: researcher, on Keshav's input (budget $100-200/month, demo-on-demand; cloud prod is real but scales to zero).

**Context.** Keshav's budget cannot carry an always-on stack. An always-on `prod` profile is ~$300+/month.

**Options.**
1. Cloud SQL `db-g1-small` ~$26/month (no SLA). Cheap but small for pgvector HNSW.
2. Cloud SQL Enterprise 2 vCPU / 8 GiB ~$101 while running (HA ~$202), stopped by default (chosen).
3. AlloyDB 2 vCPU / 16 GiB ~$227+. Rejected on cost.
4. Always-on everything. Rejected: ~$300+.

**Evidence.** Cloud SQL pricing and AlloyDB figures in evidence-r2.md (Data layer); Memorystore Valkey shared-core-nano ~$23/month; budget recomputation D13r; Cloud Run billing (min instances bill while idle).

**Decision.** Terraform owns everything; `make demo-up` and `make demo-down` flip the Cloud SQL activation policy, `fa-gateway` / `chat-api` min instances, the worker pool count, and Cloud Scheduler pause state; Valkey is created on up and deleted on down. Down order (D13h): stop Scheduler triggers (the hourly `demo-ttl` job stays active), drain outbox and consumers to idle (10-minute timeout, then force; leftover outbox rows go out on the next up), scale the worker pool to 0, API and Kong min 0, delete Valkey, stop Cloud SQL. Up is exactly the reverse (D16.13): start Cloud SQL, create Valkey (fixed Memorystore name, outside Terraform state), deploy a new Kong revision with the Valkey endpoint and raise API / Kong min instances, scale the worker pool up, resume Scheduler triggers, then run `maintenance` and the `demo-prewarm` job inside the VPC. An hourly `demo-ttl` job (role `fa_maint`, Cloud Run admin rights) auto-downs the demo as a safety net. Terraform uses `lifecycle.ignore_changes` on `activation_policy`, `min_instance_count`, `manual_instance_count`. HA is a Terraform flag for load tests. Availability: the 99.5% SLO applies to the `prod` profile only; demo mode has no SLA (D13g). Budget: idle ~$40-55; demo month (~40 h, ~2,000 chats) ~$110-160.

**Dissent.** Simplicity proposal: `g1-small` always on.

**What it makes harder later.** Cold start: Cloud SQL start time is undocumented (spike, deep-dive/10-open-questions.md §10). Idle cost is fixed by the ALB ($18.25) and Cloud Armor (~$6-10, unverified). The idle estimate assumes a stopped instance bills storage only; unverified. Worker pool scale-to-0 and its Terraform support are unverified. Demo-down must drain the outbox first or audit events are delayed to the next up.

**Trigger to revisit.** Measured start time too slow for demos; a real customer needs availability (switch to `prod` profile); budget changes.

## ADR-019: Compute mapping: one image, three entrypoints, Cloud Run, Vite SPA

**Status.** Accepted 2026-11-01. decided-by: researcher (Keshav's inputs: keep FastAPI, React + TypeScript). Resolves G-13, G-49, G-51.

**Context.** One developer, learning goals, scale-to-zero, SSE streaming, continuous Kafka consumers, batch ETL.

**Options.**
1. GKE. Rejected: operating burden, no scale to zero at the budget.
2. Cloud Run services only (consumers as services). Services autoscale and bill on requests; consumers need continuous pull.
3. Cloud Run services + worker pools + jobs (chosen). Worker pools: no autoscaling, ~37% cheaper CPU.
4. Frontend as Next.js 16 standalone on Cloud Run vs Vite SPA on GCS + CDN. The SPA removes the BFF buffering hop and Next multi-instance issues.

**Evidence.** Cloud Run request timeout <= 60 min (SSE needs reconnect + `Last-Event-ID`), worker pools for continuous consumers, jobs <= 168 h; estimates: API min=1 ~$20-30, worker pool 0.5-1 vCPU ~$18-33, ETL jobs ~$1-2 (evidence-r2.md). FastAPI 0.162 native `fastapi.sse`; SQLAlchemy 2.1, asyncpg 0.32, alembic 1.20.

**Decision.** One Python image with entrypoints `api | worker | jobs`. Cloud Run service `chat-api` (SSE, explicit concurrency, timeout 3600, `Last-Event-ID` resume, `Idempotency-Key`), Cloud Run service `fa-gateway` (ADR-011), Cloud Run worker pool `fa-worker`, Cloud Run jobs (migrate, maintenance, etl, etl-public, dbt, eval, redteam, demo-prewarm, demo-ttl). Worker roles: outbox-relay, silver, contextualizer, indexer, acl-applier, eval-judge, bq-sink. All services use Direct VPC egress `private-ranges-only` (ADR-024). Vite + React 19 + TypeScript SPA on GCS behind the ALB. Local dev = docker compose with the same image. One Uvicorn process per container.

**Dissent.** None recorded.

**What it makes harder later.** A modular monolith needs import-linter discipline; worker pool autoscaling is manual (count flipped by `demo-up`); worker pool scale to 0 and Terraform support are to be verified.

**Trigger to revisit.** Retrieval needs separate scaling (ADR-004); a consumer needs autoscaling; SSR/SEO needs for the frontend.

## ADR-018: Observability and Langfuse Cloud

**Status.** Accepted 2026-11-01. decided-by: researcher. Resolves G-15, G-40, G-41, G-44.

**Context.** MVP tracing uses Langfuse v2 methods that do not exist in the locked SDK, so chat fails with keys set; logs carry raw queries; health is static.

**Options.**
1. Self-host Langfuse v4: needs ClickHouse + Redis + S3 + Postgres, >= 4 vCPU / 16 GiB. Rejected on cost.
2. Langfuse Cloud Hobby: free 50k units/month, 30-day retention (chosen), synthetic data only.
3. Drop LLM tracing. Rejected: eval datasets and judges use it.
4. Cloud Trace (free to 2.5M spans), Logging ($0.50/GiB after 50 GiB per project).

**Evidence.** https://langfuse.com/docs/observability/sdk/python/upgrade-path , https://langfuse.com/self-hosting , https://langfuse.com/pricing ; GCP ops pricing in evidence-r2.md.

**Decision.** Langfuse Cloud Hobby with Python SDK 5.x (5.1.0 current) behind one wrapper: `@observe` with `capture_input` / `capture_output` off on sensitive spans and `mask_otel_spans` for export masking (the legacy `mask=` does not cover OTel spans; D15.6); scrubbed input only, tagged by tenant (D13l). OpenTelemetry (Kong to API to workers, `traceparent` in Kafka headers) to Cloud Trace; SQL parameter capture off; no request bodies in logs or spans (D13o). Structured redacted logs; log-based metrics (TTFT, gate refusals, guard blocks, consumer lag); `/healthz` and `/readyz`; one availability SLO with burn-rate alert (prod only) plus latency SLOs; budget alerts.

**Dissent.** None recorded.

**What it makes harder later.** Traces live at a third party: acceptable only for synthetic data. SDK 5.x needs server v4 (self-hosting would too); Cloud compatibility is confirmed when the wrapper is built in E0. Hobby retention is 30 days.

**Trigger to revisit.** "Real firm data": self-host Langfuse v4 in the project or drop third-party tracing; Hobby unit cap reached.

**Amended 2026-11-07 (validation).** The trigger "real firm data" reads, as ADR-038 states: real public documents and private demo publisher documents are allowed; real client data is still not. Langfuse keeps metadata, hashes and redacted text only, and trace erasure is provider-bound (ADR-029). This block is the amendment that ADR-038 refers to (V-consistency.md S16).

## ADR-017: Evaluation strategy and deploy gate

**Status.** Accepted 2026-11-01. decided-by: researcher. Resolves G-06, G-54, G-56.

**Context.** The MVP eval scores only LLM-judged faithfulness and citation accuracy, with the same model family as judge, and never ran on a PR. JPM and Morgan Stanley run regression suites with per-component evals.

**Options.**
1. LLM-judge only (MVP). Rejected: no retrieval metrics, self-judging.
2. Layered evals L0-L4 with deterministic checks first (chosen).
3. Full 300-question suite on every PR. Rejected on cost and time.

**Evidence.** Ragas collections, Langfuse datasets, ARES https://arxiv.org/abs/2311.09476 (CI bounds), MT-Bench swap order https://arxiv.org/abs/2306.05685 , JPM Ask DAVID and Morgan Stanley https://openai.com/index/morgan-stanley/ , EvidenT https://aclanthology.org/2026.emnlp-industry.69.pdf , Bloomberg RAG risk (evidence-r2.md).

**Decision.** L0 deterministic on every PR with real pgvector + Kafka service containers: RLS leak matrix (reads, writes, FK probes, pooled-connection reuse), fail-closed, citation verifier, PII, model-retirement check. L1 retrieval recall@k / MRR / nDCG with dense / FTS / hybrid / rerank ablation. L2 Ragas collections (faithfulness, context precision / recall, noise sensitivity) with a Haiku 5.5 judge (judge differs from the answer model) calibrated on ~30 human labels (Cohen's kappa) and CI lower bounds reported. L3 cross-tenant / tier / jurisdiction refusal and promptfoo red team. L4 online sampled judge and thumbs: the `eval-judge` worker consumes `eval.sample.v1` (a 5-10% sample), judges with Haiku 5.5 and writes scores to Langfuse and `eval_scores`; Langfuse-side evaluators are not used (D14.14). The `eval` and `redteam` jobs run as `fa_eval`, pinned to a dedicated `eval` tenant (D16.18). Golden set 50 growing to ~300, tenant-parameterised. Gate: citation >= 0.95, faithfulness >= 0.90, leaks = 0, recall regression <= 2 pts. PR runs a ~60-question path-filtered subset; the full set runs weekly and before demos, and once against the fallback model.

**Dissent.** None recorded.

**What it makes harder later.** Human labels take time; the golden set must be curated per tenant; judge calibration drifts with model changes; gate thresholds need re-tuning when the corpus grows.

**Trigger to revisit.** Judge kappa below acceptable; gate flakiness; model change.

**Amended 2026-11-02 (round 4).** Layers L0-L4 stand; see ADR-037. The golden set is 200 items labelled by Keshav (K-R4-4), public/private split, at least 40 source documents and at most 5 items per document, analysed at document-cluster level with no fixed n_eff claim. Tier-1 deterministic metrics come first; the Haiku judge gates only if judge-human rho^2 >= 0.4. At most 4 confirmatory ablation arms with Holm; others are exploratory and cannot enter the default pipeline alone. Ablation runs use the Message Batches API. L0 gains: race harness, as-of boundaries, numeric-gate property tests, licence-footer matrix, role x tool matrix, replay idempotence, reconcile on fixtures, per-leaf EXCLUDE check, cell isolation. Connectors run against recorded fixtures in PR; live source smoke, golden-200, guardrail sets and arms run weekly.

## ADR-016: Contextual retrieval at ingest, behind a flag

**Status.** Accepted 2026-11-01. decided-by: researcher.

**Context.** Chunks lose context when split; Anthropic reports top-20 retrieval failure 5.7% to 2.9% with contextual headers, at a one-time ~$1.02 per million document tokens.

**Options.**
1. Defer (simplicity). Cost: lower recall.
2. On, Haiku 5.5 via Batch API (-50%), behind a flag (chosen; cost proposal and scale proposal).
3. Semantic chunking. Rejected (arXiv 2410.13070: not worth it).

**Evidence.** https://www.anthropic.com/news/contextual-retrieval ; Haiku 5.5 $0.10 / $0.50 per MTok, Batch -50% (https://platform.claude.com/docs/en/about-claude/pricing ).

**Decision.** Generate headers with `claude-haiku-5-5` through the Batch API in the `contextualizer` role, enabled by `CONTEXTUAL_RETRIEVAL_ENABLED`. Input is redacted text; output must pass the PII scrub and tier rules. The L1 ablation decides whether it stays. The header is stored in `chunks.context_header` and is part of the embedded and FTS text.

**Dissent.** Simplicity proposal: defer.

**What it makes harder later.** Ingest becomes asynchronous on Batch API latency; changing the header prompt changes `chunk_hash` inputs and forces re-embedding.

**Trigger to revisit.** The ablation shows no gain; Batch cost or latency.

**Amended 2026-11-02 (round 4).** Contextual retrieval is an ablation arm and the default is OFF (`CONTEXTUAL_RETRIEVAL_ENABLED` stays, default false); the original mechanism above is unchanged. Baseline B0 is the free structural prefix (title plus section path). The Haiku-header arm and the `voyage-context-4` arm (no LLM call, $0.12/M) are two of the four confirmatory arms of ADR-037 (R4-D17) and must pass its line (gain of about 5 points or more, Holm) before the flag can turn on. Reason: Anthropic's 35/49/67% figures use a dense-only baseline and no financial data, an independent off-domain preprint finds a free section prefix roughly equal under a strong retriever, and the ingest cost spread is large (about $3 chunk-only vs about $78 whole-document uncached per 1k real 497K filings).

## ADR-015: Exact-match answer cache

**Status.** Accepted 2026-11-01. decided-by: researcher.

**Context.** Repeated questions cost an LLM call; in a regulated multi-tenant product a wrong cache hit is a leak or a stale answer.

**Options.**
1. Defer (simplicity).
2. Semantic cache. Rejected: cross-user leak risk.
3. Exact-match cache in a Postgres UNLOGGED table (chosen).

**Evidence.** Pattern ranking in evidence-r2.md (fix filtered ANN, then tenant + tier + corpus-version-keyed answer cache); D9, D13i.

**Decision.** Table `answer_cache` (UNLOGGED), own RLS + FORCE. Key = hash(tenant, tier, jurisdiction set, corpus_version (own and PUBLIC), acl_version, user entitlement version, prompt_version, model, normalized redacted question). Single-turn only, TTL 24 h. On a hit, re-run the citation verifier against freshly fetched chunks under the caller's RLS and recompute staleness; any failure is a miss. Turns that called a side-effect tool (`escalate_to_compliance`) are never cached. Purged by the `acl-applier` on ACL change and document delete, and by the `maintenance` job when expired (D16.8, D16.18).

**Dissent.** Simplicity proposal: defer.

**What it makes harder later.** Every new version input must be added to the key; UNLOGGED data is lost on a crash (acceptable for a cache); cache hit rate stays low because questions rarely repeat exactly.

**Trigger to revisit.** Measured hit ratio too low to justify the table; a safe semantic cache design emerges.

**Amended 2026-11-02 (round 4).** The key in the decision above gains three inputs (ADR-027): `as_of` date, `embed_model` and the PUBLIC `source_epoch`. Any version publish, supersede, retire, withdraw or erase bumps the tenant `corpus_version` in the same transaction and deletes `answer_cache` rows whose `source_document_ids` contain the document (GIN index). The FCA purge bumps `source_epoch` and runs a per-tenant erase job for cached answers quoting FCA text (ADR-026). Hit-time re-verification stays, and a cited chunk must satisfy `valid_range @> as_of`. `answer_cache` is a live store in the erasure scope (24 h, ADR-029).

## ADR-014: ETL stack: Dagster, dbt, BigQuery, bronze/silver/gold

**Status.** Accepted 2026-11-01. decided-by: researcher, on Keshav's explicit goal to learn ETL / data engineering and his data input (synthetic per-tenant corpus + a real public source). Resolves G-03, G-07, G-39, G-62.

**Context.** MVP ingest is a script with random ids, no idempotency, a raw-content column and no suitability-rule path.

**Options.**
1. SQL views and a script (simplicity). Cheapest; no learning value.
2. Dagster OSS + dbt Core + BigQuery (chosen). All three are free at this size.
3. Cloud Composer. Rejected: continuous billing. Dagster+ Solo $10/month: not needed.
4. Document AI for parsing: only as an OCR fallback ($1.50/1k pages).

**Evidence.** Bronze / silver / gold, Dagster sensors https://dagster.io/docs/guides/automate/sensors , SEC access rules https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data , Notion per-span content hash https://www.notion.com/blog/two-years-of-vector-search-at-notion , Uber replayable index https://www.uber.com/us/en/blog/how-uber-indexes-streaming-data-with-pull-based-ingestion-in-opensearch/ , BigQuery free 1 TiB queries (evidence-r2.md).

**Decision.** Bronze: GCS by sha256, raw immutable, with URL and fetch time. Silver (Parquet in GCS `silver/`, partitioned tenant / dt): Docling parse (HTML supported; first public source = fund summary prospectuses 497K; inline-XBRL tables tested in a spike), Presidio scrub, structure-aware chunking with Voyage `count_tokens`, Pandera validation, rejects table, `parser_version`. Contextual headers (ADR-016), suitability-rule extraction (Haiku structured output, validated; fixes G-07), embed-indexer upserts. Gold: dbt Core on Postgres as `fa_dbt`: views with `security_invoker = true`, or incremental models with a tenant predicate, never full-table rebuilds; the `gold` schema is owned by `fa_dbt` and exempt from the not-owner assertion; CI asserts RLS enabled, forced and policies present for every tenant-schema table (D13n, D16.14). Dagster OSS assets (partitioned tenant x date, `run_key` dedupe) run daemon-less as Cloud Run jobs from Cloud Scheduler (`dagster asset materialize`), with run and event storage in Postgres (`dagster-postgres`, database `dagster` on the same Cloud SQL instance, role `fa_dagster`, no access to app schemas) so run history survives (D15.4); `dagster dev` locally; no cloud daemon until > 10 tenants or a sensor is needed. Silver, contextualize and embed-indexer run as worker consumers (`fa_worker`); PUBLIC ingest runs all stages in-process in the `etl-public` job (`fa_etl_public`); the embed-indexer bumps `corpus_version` after the `chunks` upsert (D14.5, D16.6, D16.7). BigQuery marts for audit / usage / eval analytics: redacted text only, partitioned by day, clustered by `tenant_id`, `maximum_bytes_billed` on every query; per-tenant authorized views are the primary isolation and row access policies the second layer (they do not prune partitions and can bill more rows; D15.5); marts built by `dbt-bigquery`; fed by a Kafka sink worker with event-id dedupe. Idempotent ingest: unique `(tenant_id, chunk_hash, embed_model)`, re-embed only changed chunks, ACL change = metadata UPDATE, `documents.raw_content` dropped.

**Dissent.** Simplicity proposal: SQL views suffice for the product; a second platform to run and learn.

**What it makes harder later.** Three tools to keep current; dbt runs need a dedicated per-tenant connection to set `app.tenant_id`; EDGAR limits (<= 10 req/s, declared User-Agent) shape the fetcher. Two execution paths (worker consumers for tenants, in-process job for PUBLIC) must stay behaviourally identical.

**Trigger to revisit.** > 10 tenants or a sensor need (Dagster daemon); Docling fails on 497K / XBRL (spike result); BigQuery cost.

**Amended 2026-11-02 (round 4).** The stack stays; the original decision above stands except as follows. Silver path is versioned per document: `silver/tenant_id=/doc_id=/version=` (was tenant / dt), so erasure deletes by prefix and a parser bump re-parses (ADR-027). Real connectors write `source_observations` (ADR-026). Quality: Pandera with `PANDERA_VALIDATION_DEPTH=SCHEMA_AND_DATA`, dbt `contract: enforced` on tables, Dagster blocking checks advisory only (the atomic indexer gate is the control, ADR-028), a `quarantine/` prefix, and reconcile pairs (ADR-034). BigQuery: `max_time_travel_hours=48` on every dataset including dbt-created ones; FCA content never lands in BigQuery; subject rows carry `pseudonym_id` (ADR-029). OpenLineage is dropped (`dagster-openlineage` 0.2.1 stalled); lineage is an own table, never a gate (ADR-030).

## ADR-013: Kafka on Confluent Cloud Basic, Schema Registry, transactional outbox

**Status.** Accepted 2026-11-01. decided-by: researcher, on Keshav's goal that Kafka is a first-class learning part and that dev runs Kafka locally.

**Context.** Event volume is ~1-5k events/day; no reference puts Kafka in front of pgvector at tens of tenants; Kafka is justified for learning, replay and per-tenant ordering, not load.

**Options.**
1. GCP Managed Kafka: min 3 vCPU, 3 zones, ~$189-248/month. Rejected.
2. Confluent Cloud Basic: first eCKU free then $0.14/eCKU-h, $0.05/GB; ~$0-10/month (UNVERIFIED estimate; confirm in console); 99.5% SLA; Essentials Schema Registry free (100 schemas); $400 trial (chosen).
3. Aiven Free (250 KiB/s, 5 topics) $0 / Developer $35. 4. Self-hosted KRaft on e2-medium ~$27, single broker. 5. Pub/Sub ~$0 but no Kafka API.
6. Outbox vs fire-and-forget (D4): fire-and-forget loses audit when Kafka is down.

**Evidence.** https://cloud.google.com/managed-service-for-apache-kafka/pricing , https://www.confluent.io/pricing/ , https://github.com/confluentinc/confluent-kafka-python , Debezium outbox https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html .

**Decision.** Confluent Cloud Basic in us-central1 (create the cluster first: the Schema Registry region is fixed by the first cluster, D13q); `apache/kafka:4.4.0` KRaft and cp-schema-registry locally; `confluent-kafka` 2.16.1. Versioned topics `*.v1` keyed by `tenant_id`; JSON Schema in Schema Registry generated from Pydantic (D5). Idempotent producers; at-least-once consumers with idempotent sinks (`processed_events`); DLQ topic `dlq.v1`. Transactional outbox table with a relay loop in the worker, no Debezium (D4); chat never depends on Kafka. Payloads minimised (ids, hashes, redacted text only), separate API keys per service, DLQ payloads redacted (D13j). Per-tenant topics rejected (topic and partition count). `chat-api` has no Kafka credentials and no consumer: its events leave through the outbox and the relay, and the 60 s entitlement TTL is the revocation bound (D14.9, ADR-022). Confluent Basic has no RBAC: one service account and API key per service, Kafka ACLs per service account, limits of 50 API keys, 1,000 ACLs and 1,500 partitions (D15.8). Pipeline consumers reject events whose envelope tenant differs from the key or is PUBLIC (D16.6). Added topics: `eval.sample.v1` (judge input), `ingest.analytics.v1` (PUBLIC ingest analytics); no gateway audit topic (ADR-023).

**Dissent.** All three proposals: Schema Registry is an extra component and Pydantic envelopes alone would work. Kept for the Kafka learning goal at small cost.

**What it makes harder later.** Confluent Basic has no in-cluster RBAC, so tenant isolation of events rests on payload minimisation; the relay is custom code to operate; Basic has 99.5% SLA only.

**Trigger to revisit.** "Real firm data": Confluent Standard RBAC; > 100 schemas; Debezium outbox connector as an optional learning epic.

**Amended 2026-11-02 (round 4).** Kafka keeps analytics and audit events only; the original decision above stands for those. Kafka is no longer on the delete path (`deletion_requests` in Postgres, ADR-029) or the ACL path (ADR-022 amendment, polling), and FCA content never enters Kafka (ADR-026). Subject-bearing topics are delete-policy with `retention.ms` 7 d and `segment.ms` set (1 d; Confluent minimum 4 h), payloads minimised to ids and `pseudonym_id`, so the window is about 8 d (ADR-029). `source_observations`, `docs.*` and `chunks.*` events are Schema Registry contracts, BACKWARD (ADR-034). The "real firm data" trigger now reads: real public documents and private demo publisher documents are allowed; real client data is still not (ADR-038).

**Amended 2026-11-07 (validation).** Payloads are ids, hashes, scores and flags. `chat.audit.v1` and `eval.sample.v1` carry no answer, question or excerpt text (the "redacted text" wording is withdrawn): text stays in erasable Postgres `messages`, and the `eval-judge` reads it by `message_id`. The outbox writer enforces this and test #15 checks Kafka and BigQuery (R4-D19 M5; V-consistency.md M5). The "real firm data" trigger reads as in ADR-038.

## ADR-012: Edge: external ALB + Cloud Armor, same origin

**Status.** Accepted 2026-11-01. decided-by: researcher. Resolves G-02, G-13, G-46.

**Context.** The MVP exposes backend and frontend with `allUsers` invoker and no load balancer, WAF or CORS.

**Options.**
1. Firebase Hosting + public API with JWT (cost proposal): cheaper, but a public API.
2. External ALB + Cloud Armor, same origin (chosen): `/*` to a GCS backend bucket (SPA, CDN), `/v1/*` to the gateway.

**Evidence.** Network guidance in evidence-r2.md (ALB + Cloud Armor ~$0.75/1M requests + policy fee; Cloud Run ingress internal-and-cloud-load-balancing); ALB $18.25/month; Cloud Armor ~$6-10/month UNVERIFIED.

**Decision.** External ALB with Cloud Armor (DDoS, WAF, geo rules) in front of everything; SPA on the GCS backend bucket; `/v1/*` goes to Kong (`fa-gateway`, ADR-011). Persistent (~$18-25/month) because certificate provisioning is slow, so `demo-down` never removes it. `fa-gateway` has the Cloud Run invoker check disabled (the only service where it is; Google recommends this over `allUsers`, https://docs.cloud.google.com/run/docs/authenticating/public ), ingress internal-and-cloud-load-balancing, Cloud Armor on the backend service; no `allUsers` anywhere (D15.1, D16.1). IAP was rejected: it replaces the caller identity and conflicts with end-user ID tokens. E10 checks the org policy `constraints/run.managed.requireInvokerIam`.

**Dissent.** Cost proposal: Firebase Hosting.

**What it makes harder later.** Fixed idle cost; the invoker-check exception on `fa-gateway` depends on the org policy allowing it (checked in E10).

**Trigger to revisit.** Cloud Armor cost verification fails the idle budget; budget change.

## ADR-011: Kong as the edge API gateway (Keshav's decision)

**Status.** Accepted 2026-11-01. decided-by: Keshav ("include kong for rate limiting and proxy plugins as well we need it"). Binding. Resolves G-02, G-10, G-11, G-14, G-46, G-48.

**Context.** The three proposals dropped Kong (Cloud Armor + FastAPI limits suffice). Keshav requires it. Kong docs check, 2026-11-01: Kong OSS ends at 3.9.x (latest 3.9.4, 2026-10-12); 3.10+ has no free mode. OSS has `rate-limiting` (`limit_by`: consumer, credential, ip, service, header, path; policies local / redis in DB-less), `request-size-limiting`, `cors`, `correlation-id`, `ip-restriction`, `bot-detection`, `request/response-transformer`, `pre-function`, `prometheus`, `opentelemetry`, `http-log`, `proxy-cache`, `ai-proxy`, `ai-prompt-guard`. Enterprise-only: `openid-connect` (JWKS), `rate-limiting-advanced`, `ai-rate-limiting-advanced`, `ai-proxy-advanced`, `ai-semantic-cache`, `ai-sanitizer`. OSS `jwt` uses static per-consumer keys (no JWKS), so it cannot verify rotating Google ID tokens. OSS `ai-proxy` 3.9 has no native Anthropic Messages format (`llm_format anthropic` is 3.10+).

**Options.**
1. No gateway: Cloud Armor + FastAPI (all three proposals). Cheapest, fewest hops.
2. Kong OSS 3.9.4 DB-less on Cloud Run (chosen). Cost: a hop, a Cloud Run service (min 0, max 2), Valkey ~$0.03/h while up.
3. Kong 3.10+ / Konnect / Enterprise. Rejected: paid.
4. Apigee ($365+/month) and API Gateway (streaming preview). Rejected.

**Evidence.** https://developer.konghq.com/plugins/rate-limiting/reference/ ; Kong docs check recorded in decision-r2.md D12; deep-dive/00-as-built-baseline.md G-14 (the MVP `identifier` parameter does not exist).

**Decision.** External ALB + Cloud Armor, then Kong (`fa-gateway`, Cloud Run, ingress internal-and-cloud-load-balancing, invoker check disabled on this service only (no `allUsers`; D15.1, D16.1), admin API off, status listener), then `chat-api` (ingress internal, `run.invoker` only for the Kong service account). Kong `pre-function` fetches a Google ID token from the metadata server (audience = chat-api URL, cached until near expiry) into `X-Serverless-Authorization`, leaving the user's `Authorization` intact; verified in a spike (fallback = ingress-internal + app JWT, recorded as an ADR). Token verification stays in FastAPI; Kong does not trust or set identity headers and a `request-transformer` strips client `X-User-Id`, `X-Tenant-Id`, `X-Serverless-Authorization`. Rate limits (OSS only): per client IP and per session key (`limit_by: header` on `X-RL-Key = sha256(Authorization)`, set by the `pre-function`, so raw tokens never reach Valkey keys; D16.10), stricter on `POST /v1/chat`, request-size limit, 429 with `Retry-After`; policy `redis` against Valkey (local container; Memorystore shared-core-nano created by `demo-up` and deleted by `demo-down` with a fixed instance name, outside Terraform state; `demo-up` passes the endpoint to Kong by deploying a new revision), `sync_rate: 0` on the chat route. Per-tenant token budgets and concurrency stay in FastAPI. Also `cors` (SPA allow-list), `correlation-id`, `opentelemetry`, `prometheus`, `file-log` to stdout with a field whitelist into Cloud Logging and a log sink to BigQuery (fixes G-48, ADR-023; no `/internal/*` routes), `bot-detection`. SSE route: `response_buffering: false`, `request_buffering: false`, `read_timeout` 3,600,000 ms; verified in a spike. LLM egress ("proxy plugins"): spike `ai-proxy` `route_type: preserve` (or a plain proxy) to `api.anthropic.com` with streaming and tool use; if it passes, `LLMClient` calls Anthropic through an internal Kong route that adds the API key, a global LLM rate limit and `log_statistics`, protected by `key-auth` (consumer `chat-api`, key from Secret Manager) and `ip-restriction` to the VPC range (D16.11); if not, `LLMClient` calls Anthropic directly (ADR). Native Messages format only. Local: `kong:3.9.4` + Valkey in compose; `kong.yml` validated with `kong config parse`. Kong reaches `chat-api` through Direct VPC egress `private-ranges-only` with a private `run.app` zone (ADR-024). Not used: Konnect, Enterprise image, `openid-connect`, `ai-*` Enterprise plugins, `http-log`.

**Dissent.** Cost, simplicity and scale proposals: Kong OSS duplicates Cloud Armor and FastAPI limits, cannot see the verified tenant, and adds a hop and a service. Kept because Keshav requires it.

**What it makes harder later.** An extra hop and failure surface for SSE (buffering risk until the spike passes); the OSS line ends at 3.9.x so there is no upgrade path inside OSS; per-tenant limiting cannot live in Kong; three spikes (SSE, IAM header, egress) can each change the design; the egress route would put the Anthropic key in Kong.

**Trigger to revisit.** Any spike fails (record a conditional ADR); 3.9.x stops receiving fixes; Keshav drops the requirement.

## ADR-010: Authentication with Identity Platform multi-tenancy and tenant discovery

**Status.** Accepted 2026-11-01. decided-by: researcher. Resolves G-01.

**Context.** MVP identity is a header over 4 hard-coded users. Needs one sign-in configuration per firm and a path to SSO.

**Options.**
1. Single Identity Platform pool (simplicity, cost). No per-firm configuration.
2. Identity Platform multi-tenancy, one IdP tenant per firm (chosen; D6). Billing must be enabled for > 2 tenants; email/password free to 50k MAU; SAML/OIDC $0.015/MAU after 50.
3. Auth0 Free (25k MAU, 5 orgs), Clerk free 50k MRU. Rejected: another vendor.
4. Verify in Kong: OSS `jwt` has static keys; `openid-connect` is Enterprise. Rejected.

**Evidence.** https://docs.cloud.google.com/identity-platform/docs/multi-tenancy ; PostgreSQL docs on SECURITY DEFINER risk via D13m review.

**Decision.** FastAPI verifies ID tokens tenant-aware with firebase-admin: the `firebase.tenant` claim names the IdP tenant and `tenant_mgt.auth_for_tenant(tenant_id).verify_id_token` checks signature, `aud`, `iss`, `exp` and raises `TenantIdMismatchError` (D15.3; https://docs.cloud.google.com/identity-platform/docs/multi-tenancy-managing-tenants ). The token identifies only `sub` and the IdP tenant; entitlements (tier, jurisdictions, licenses, role) come from `advisors` (60 s TTL-only cache, no event invalidation, per ADR-002 and ADR-004) (amended by ADR-025, R19). Tenant discovery: the SPA resolves the firm from `/t/<slug>` through the public `GET /v1/tenants/{slug}`, which returns only `{display_name, idp_tenant_id}` from a `SECURITY DEFINER` function `fa_tenant_lookup`, reviewed in CI and the only such function allowed (D13m); it is owned by the NOLOGIN role `fa_lookup` (not `fa_owner`), which has a SELECT policy on `tenants` only, with `EXECUTE` revoked from PUBLIC and granted to `fa_app` (D16.2). It serves both slug discovery and the `idp_tenant_id` to `tenants.id` mapping (D14.4). The IdP tenant id maps to `tenants.id` before settings are set.

**Dissent.** Cost and simplicity proposals: a single pool.

**What it makes harder later.** Billing must stay enabled; the public discovery endpoint allows slug enumeration (bounded by the Kong IP limit); one `SECURITY DEFINER` exception must be kept reviewed.

**Trigger to revisit.** SSO requirement; > 50 tenants; enterprise customer needs a different IdP.

**Amended 2026-11-07 (validation).** `auth` verifies the ID token at project level and requires the `firebase.tenant` claim to equal the tenant in the URL and the signed `cells.json` entry (ADR-032); the tenant-aware `auth_for_tenant(...).verify_id_token` procedure of the decision text is dropped (V-consistency.md S23).

## ADR-009: Guardrails (OWASP LLM Top 10 2025)

**Status.** Accepted 2026-11-01. decided-by: researcher. Resolves G-04, G-17, G-23, G-37, G-38, G-41, G-42, G-45, G-55.

**Context.** The MVP sends the user message unredacted to Anthropic, Voyage and Langfuse, emits raw tool JSON to the client, and has no injection screen. Measured: classifier-style rails 20-250 ms and 0-4% false positives; LLM-based rails 0.5-1.5 s and up to 16% (arXiv 2605.06669); stacking guards compounds false positives.

**Options.**
1. LLM-based rails (NeMo). Rejected: latency, false positives.
2. Cloud DLP API ($3/GiB after 1 GiB free) for PII. Rejected: network call; Presidio is in-process.
3. Deterministic guards plus Model Armor (chosen). Model Armor free to 2M tokens/month then $0.10/1M; REST API detects, the app acts.

**Evidence.** https://genai.owasp.org/llm-top-10/ ; https://docs.cloud.google.com/model-armor/overview ; https://data-privacy-stack.github.io/presidio/ ; Anthropic guidance (untrusted content only in `tool_result`); EvidenT https://aclanthology.org/2026.emnlp-industry.69.pdf ; ALCE https://arxiv.org/abs/2305.14627 .

**Decision.** Cloud Armor edge limits; input cap; Presidio in-process pseudonymization (presidio-analyzer 2.2.x, spaCy `en_core_web_sm`, latency benchmarked in E4) before embed / LLM / traces / logs; Model Armor input screen in parallel with embed (500 ms timeout, fail closed); untrusted content only in a JSON-encoded `tool_result`; least-privilege tools (tenant, tier, jurisdiction never tool arguments); `escalate_to_compliance` uses server-side licenses and persists; the client receives tool name + status only; errors carry codes, not exception text; sentence-buffered output PII redaction; deterministic citation verifier (every `[n]` in retrieved chunk ids, quote overlap) with server-emitted citation events carrying redacted excerpts; React renders sanitized markdown only; no LLM-based rails on the hot path.

**Dissent.** None recorded.

**What it makes harder later.** Presidio has no recall guarantee; fail-closed Model Armor makes chat depend on it (500 ms timeout); sentence buffering adds a small latency to first visible tokens; the citation verifier can reject good answers and must be tuned by the evals.

**Trigger to revisit.** Measured Presidio recall or Model Armor latency / false positives outside tolerance.

**Amended 2026-11-02 (round 4).** Real third-party documents add layers; the original decision above stands. Added (see ADR-036): an ingest scan (parse-time sanitiser, deterministic pattern list, Model Armor document screening with `EXECUTION_SKIPPED` failing closed into quarantine, ADR-034); JSON-encode spotlighting plus a per-request nonce (datamarking is an ablation arm only); a locale-aware numeric grounding gate per sentence; deterministic compliance checks (licence footer, jurisdiction label, as-of validity); role policy as data, default deny. The fixed 500 ms Model Armor timeout is replaced by a timeout set from latency measured from the Cloud Run region (none was found, evidence-r4.md §0.10). Presidio DE/FR recall is measured before any claim. First visible text is the first complete sentence, so the TTFT budget is measured that way.

**Amended 2026-11-07 (validation).** Model Armor is behind a feature flag with a documented fallback, because no GA status, SLA or latency is published (see ADR-036). The "fail closed, 500 ms" input screen of the decision above is replaced by that rule.

## ADR-008: Hybrid retrieval, rerank, confidence gate and chunking

**Status.** Accepted 2026-11-01. decided-by: researcher. Resolves G-33, G-34, G-35, G-36, G-52, G-62.

**Context.** MVP retrieval is dense-only IVFFlat on an empty table, `input_type="document"` for queries, filters applied after the ANN scan (short results), no rerank, no gate.

**Options.**
1. Dense only (MVP).
2. Hybrid dense + FTS with RRF in one SQL statement (Wang et al. arXiv 2407.01219: +2.3 nDCG@10 for +0.6 s prototype).
3. Add a cross-encoder rerank of the top candidates (RankGPT arXiv 2304.09542; Anthropic failure 2.9% to 1.9%). LLM listwise rerank costs 11-32 s: rejected. HyDE +4.6 s: rejected. SPLADE, ColBERT, GraphRAG, RAPTOR, Self-RAG, semantic chunking: not now.
4. Gate: CRAG-style confidence gate (arXiv 2401.15884), no web fallback.
5. pg_textsearch (BM25) needs PG17+ (not on Cloud SQL PG16); `ts_rank` is not BM25.

**Evidence.** pgvector README (HNSW defaults m 16, ef_construction 64, ef_search 40; iterative scan; halfvec <= 4,000 dims) https://github.com/pgvector/pgvector ; practitioner 52/400 queries returned 0 rows with default HNSW https://dev.to/ji_ai/pgvector-hnsw-filtering-returned-0-rows-for-52-of-my-400-queries-ghp ; AWS Aurora iterative scan https://aws.amazon.com/blogs/database/supercharging-vector-search-performance-and-relevance-with-pgvector-0-8-0-on-amazon-aurora-postgresql/ ; Voyage https://docs.voyageai.com/docs/embeddings ; Cloud SQL extensions https://docs.cloud.google.com/sql/docs/postgres/extensions ; rerank price $0.05/M and Tier-1 2M TPM (D13e).

**Decision.** Voyage `voyage-4` with `input_type` query / document; `halfvec(1024)`; HNSW (m 16, ef_construction 64) with `SET LOCAL hnsw.iterative_scan = relaxed_order`, `hnsw.max_scan_tuples = 20000`, `ef_search` ~80-100; `tsvector` + GIN FTS leg (`websearch_to_tsquery`) for rule ids and tickers; RRF `k = 60` in one SQL statement with RLS on both legs; Voyage `rerank-3-lite` (arm 3 compares `rerank-3`; amended 2026-11-07) with timeout; a rerank timeout or 429 falls back to RRF order and marks the turn degraded (SSE `meta {retrieval_degraded: true}` and `messages.retrieval_degraded`), increments `rerank_fallback_total{reason}`, and alerts when > 5% of turns in 15 min are degraded (visible, so not silent; D14.2); kept or dropped by the eval ablation on recall and latency; `RERANK_CANDIDATES` default 15 (range 10-30), set by the L1 ablation (D14.1); CRAG-style gate yields "no firm documentation" + escalate offer without an LLM call; parent expansion; staleness computed server-side from today's date. Chunking: structure-aware 256-512-token children, ~1k-token parents, title then section heading prefix. Latency targets (estimates): TTFT p50 < 2.0 s, p95 < 3.5 s; first stage p95 < 300 ms; rerank p95 < 700 ms; full answer p95 < 8 s.

**Dissent.** None recorded. The skeptic replaced rerank-2 with rerank-2.5-lite and relaxed the earlier latency targets (D13e).

**What it makes harder later.** FTS is not BM25; rerank is single-vendor (Voyage) and rate limited (about 5 QPS on Tier 1); the gate threshold must be tuned by evals; ANN with RLS needs iterative scan tests.

**Trigger to revisit.** BM25 available on managed Postgres (PG17+); recall regression; ANN p95 > 100 ms; rerank latency or TPM unmet.

**Amended 2026-11-07 (validation).** The rerank default is `rerank-3-lite` (current on Voyage's page, 4M TPM, 2,000 RPM, $0.02 per 1M tokens, lower latency); `rerank-3` is 2M TPM and $0.05; `rerank-2.5` and `rerank-2.5-lite` are "older" and leave the design (R4-D18 V1; https://docs.voyageai.com/docs/reranker , https://docs.voyageai.com/docs/rate-limits ; V-docs-ai.md Q2). The first-stage retrieval target is p95 <= 600 ms, not 300 ms: embed (0.25 s) then hybrid SQL (0.30 s) are serial, 0.55 s in the estimate, measured in the E3 spike; TTFT targets 2.0 s p50 and 3.5 s p95 are unchanged (R4-D19 M3). The 2M TPM figure of the original text belonged to the full models, not the default.

## ADR-007: Retrieve-first orchestration and conversation state

**Status.** Accepted 2026-11-01. decided-by: researcher. Resolves G-22, G-32, G-53.

**Context.** MVP is a ReAct loop of up to 5 non-streaming LLM calls with the DB connection held open; no conversation memory.

**Options.**
1. ReAct loop with the model deciding when to retrieve (MVP). Slow, non-streaming, injection surface.
2. Retrieve-first in code, then one streaming call with tools, max 3 iterations (chosen).
3. Multi-agent / sub-agent orchestration (JPM Ask DAVID). Not now.

**Evidence.** Anthropic guidance: untrusted content only in `tool_result`, JSON-encoded; Azure single retrieval layer https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/secure-multitenant-rag ; JPM figures (<50% to ~80% with retrieval tuning, ~90% with orchestration; evidence-r2.md).

**Decision.** Retrieval runs in code before the first LLM call and is injected as a JSON-encoded `tool_result`; one streaming call with tools (`lookup_product_factsheet`, `lookup_suitability_rule`, `escalate_to_compliance`, follow-up `search_firm_kb`), max 3 iterations, `max_tokens` bounded. Short DB transactions, never held across the LLM loop. Conversation state in Postgres: `conversations` and `messages` (monthly range partitions), last 6 turns <= 3k tokens, follow-up condensation with Haiku only when history exists (D11). Persist events in `turn_events` for resume.

**Dissent.** None recorded.

**What it makes harder later.** The model cannot skip retrieval, so every question pays embed + SQL (+ rerank); the gate handles irrelevant questions; the synthetic prefetch tool call is a convention the prompt must follow.

**Trigger to revisit.** The follow-up search tool hurts precision in evals; multi-step tasks need sub-agents.

## ADR-006: Models and prompt caching

**Status.** Accepted 2026-11-01. decided-by: researcher. Resolves the urgent retirement of `claude-sonnet-4-20250514` (G-58).

**Context.** `claude-sonnet-4-20250514` retired 2026-06-15 (app and evals fail today); `claude-sonnet-4-5` retires 2026-11-30; `claude-haiku-4-5` deprecation ~2026-10-15. `temperature`, `top_p`, `top_k` removed in the API on 2026-10-21 (400).

**Options.**
1. Sonnet 5.5 $2 / $10 per MTok (cache read $0.10; cache minimum 512 tokens) (chosen for answers).
2. Sonnet 4.6 $3 / $15 (1,024-token cache minimum): fallback only.
3. Haiku 5.5 $0.10 / $0.50 for aux work (chosen); Haiku 4.5 $1 / $5 rejected. Batch API -50%.

**Evidence.** https://platform.claude.com/docs/en/about-claude/model-deprecations , https://platform.claude.com/docs/en/about-claude/pricing .

**Decision.** Answer `claude-sonnet-5-5`; judge, contextual headers, rule extraction, condensation and citation spot-checks `claude-haiku-5-5` (judge differs from the answer model); Batch API for offline / bulk. No `temperature` / `top_p` / `top_k`. Model ids only from config; CI and readiness fail on a retired or soon-retiring model. Prompt caching on system prompt + tools (cache order tools, system, messages); tenant / user / date text after the breakpoint; tool definitions are versioned with the prompt because changing them invalidates the cache.

**Dissent.** None recorded.

**What it makes harder later.** Model churn is continuous: the retirement check is a standing maintenance cost; changing prompt or tools invalidates caches and answer-cache keys.

**Trigger to revisit.** Any deprecation notice; price change; a model passes the eval gate at lower cost.

## ADR-005: Drop LiteLLM; in-process LLMClient with same-provider fallback

**Status.** Accepted 2026-11-01. decided-by: researcher (Kong egress interaction: ADR-011). Resolves G-08, G-09, G-10, G-24, G-31.

**Context.** The MVP LiteLLM config shuffles across Claude, GPT-4o and Gemini under one model name (G-08), its fallback key matches nothing (G-09), and recent LiteLLM releases had OOM regressions.

**Options.**
1. Keep LiteLLM pinned v1.106.6: >= 4 Gi per pod, canary + soak, Redis for > 1 replica, budgets need its DB.
2. Kong `ai-proxy` as the LLM layer: OSS 3.9 has no native Anthropic Messages format.
3. Thin in-process `LLMClient` over the Anthropic SDK (chosen).
4. Cross-provider fallback. Rejected: changes regulated answers.

**Evidence.** https://docs.litellm.ai/docs/routing , https://docs.litellm.ai/blog/retry-breadcrumb-oom-incident ; Kong ai-proxy limits (D12).

**Decision.** `LLMClient` with streaming, explicit timeouts, retries with jitter, circuit breaker, same-provider fallback only (`claude-sonnet-5-5` to `claude-sonnet-4-6`). The fallback costs 50% more ($3 / $15), has a 1,024-token cache minimum and its own cache; it is budgeted and enabled only if it passes the eval gate (D13f). Model ids only from config. Base URL from config: direct, or Kong egress route if the spike passes (ADR-011), protected by `key-auth` (consumer `chat-api`) and `ip-restriction` (D16.11).

**Dissent.** None recorded.

**What it makes harder later.** Adding another provider means writing it; no central spend dashboard (usage goes through `chat.usage.v1` and Langfuse); the breaker and fallback logic is ours to test.

**Trigger to revisit.** A second model provider is required (only after equivalence evals); the Kong egress spike changes the path.

## ADR-004: Single retrieval enforcement point

**Status.** Accepted 2026-11-01. decided-by: researcher. Resolves G-20, G-21, G-35.

**Context.** In the MVP, tools query content tables directly with app-level WHERE clauses, and only `chunks` has RLS. Azure guidance: a single retrieval API layer is the enforcement point; every retrieval, including agent tool calls, carries tenant and user filters.

**Options.**
1. Separate retrieval service (scale proposal): stronger isolation, +network hop, +service.
2. In-process module with a second pool and DB role `fa_retrieval` (original D1): double connections, two snapshots, a nominal boundary.
3. In-process `RetrievalService(principal)` module; one DB login role per process; import-linter + test; RLS as the backstop (chosen, D13c).

**Evidence.** https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/secure-multitenant-rag .

**Decision.** `RetrievalService(principal)` is the only code that touches content tables; tools never take tenant, tier or jurisdiction arguments; entitlements come from `advisors` (60 s cache; the TTL is the revocation bound, no Kafka invalidation, D14.9). `fa_app` has SELECT only on content tables; ACL changes and deletes are applied by the `acl-applier` worker (ADR-022). Roles per process are listed in deep-dive/05-data-model-and-storage.md §5.3.

**Dissent.** Scale proposal: a network boundary is stronger isolation than a module boundary.

**What it makes harder later.** The boundary is enforced by tooling, not topology; a developer error inside `retrieval` is the risk the RLS backstop and L0 tests cover.

**Trigger to revisit.** Retrieval needs separate scaling, or a second consumer of retrieval appears: extract it to its own Cloud Run service with its own role.

## ADR-003: LIST partitions of chunks by tenant

**Status.** Accepted 2026-11-01. decided-by: researcher (skeptic correction D13b replaced the original HASH decision).

**Context.** Pgvector applies filters after the ANN scan. Partitioning gives each tenant its own HNSW and GIN index and prunes at plan time.

**Options.**
1. Partition at a trigger (simplicity, cost proposals). Cheap now; retrofit needs a replay.
2. HASH(tenant_id) x 8 partitions (original D2). Four tenant keys in 8 hash buckets collide with probability ~59%.
3. LIST partitions: one per tenant, one for PUBLIC, plus DEFAULT (chosen).

**Evidence.** Practitioner: 40 tenants / 1.2M chunks, default HNSW returned 0 rows for 52/400 queries; small tenants best with exact scan (https://dev.to/ji_ai/pgvector-hnsw-filtering-returned-0-rows-for-52-of-my-400-queries-ghp ); pgvector README on partitioning https://github.com/pgvector/pgvector ; runtime pruning with the RLS `current_setting` policy confirmed by test on the 8-partition setup ("Subplans Removed: 6 of 8", pgvector 0.8.7 / PG16.15).

**Decision.** `chunks` is `PARTITION BY LIST (tenant_id)`, with HNSW and GIN per partition declared on the parent. Tenant onboarding creates its partition and indexes in the `migrate` job. Partitions get no grants; runtime roles reach them only through the partitioned parent (D16.3). PUBLIC can be sub-partitioned by source later.

**Dissent.** Simplicity proposal: partitioning adds indexes and planner complexity for 3 tenants.

**What it makes harder later.** Onboarding is a migration step, not a row insert; rows in the DEFAULT partition mean a missed onboarding; planner and migration cost at ~50 partitions is unmeasured (E1 measures it); the pruning test must be repeated on LIST partitions.

**Trigger to revisit.** One tenant > 250k chunks, total > 2M chunks, or ANN p95 > 100 ms: grow partitions or silo a tenant through `tenants.shard_id`. PUBLIC > 250k chunks: sub-partition by source.

## ADR-002: Pool tenancy in one Postgres with RLS (read/write split, role per process)

**Status.** Accepted 2026-11-01. decided-by: researcher; scope input by Keshav (demo multi-tenant: 2-3 synthetic firms, designed for 50 tenants / 2,000 advisors). Resolves G-12, G-19, G-20, G-21, G-43.

**Context.** The MVP applies RLS to `chunks` only, connects as a superuser and uses session-level `SET` on pooled connections. v2 must isolate several firms in one deployment at demo cost.

**Options.**
1. Silo, project-per-tenant (Google multi-tenant agentic reference): strongest isolation; cost per tenant exceeds the budget.
2. Bridge: schema or database per tenant.
3. Pool: shared tables with `tenant_id` and RLS (chosen). Cheapest; no per-tenant CMEK or performance isolation (AWS pool / bridge / silo).

**Evidence.** https://aws.amazon.com/blogs/machine-learning/multi-tenant-rag-with-amazon-bedrock-knowledge-bases/ , https://aws.amazon.com/blogs/database/self-managed-multi-tenant-vector-search-with-amazon-aurora-postgresql/ , https://docs.cloud.google.com/architecture/multi-tenant-agentic-ai-system , https://www.postgresql.org/docs/16/ddl-rowsecurity.html , https://www.postgresql.org/docs/16/sql-set.html , Notion workspace-ID sharding https://www.notion.com/blog/two-years-of-vector-search-at-notion .

**Decision.** `tenant_id NOT NULL` on every table; `ENABLE` + `FORCE` RLS on all tenant tables; the app connects as a non-owner, non-superuser, NOBYPASSRLS login role (no `SET ROLE`); per-transaction `set_config('app.*', $n, true)` with bind parameters; `current_setting` without `missing_ok` (fail closed); short transactions never held across the LLM loop; composite FKs `(tenant_id, ...)` because FK checks bypass RLS; migrations as a separate owner role in a Cloud Run job; startup and readiness assert role flags, FORCE RLS on every table and pgvector >= 0.8. A reserved PUBLIC tenant holds the public corpus. Write split (D13a): SELECT = own tenant OR PUBLIC; INSERT / UPDATE / DELETE = own tenant only; only `fa_etl_public` writes PUBLIC. One DB login role per process (D13c): `fa_app` (chat-api, SELECT only on content tables), `fa_worker`, `fa_etl`, `fa_etl_public`, `fa_dbt`, `fa_owner`, plus `fa_maint` (maintenance, `demo-ttl`), `fa_eval` (eval and redteam, pinned to the `eval` tenant), `fa_lookup` (NOLOGIN, owns the one `SECURITY DEFINER` function) and `fa_dagster` (separate database). `tenants` is under FORCE RLS with policies for `fa_app` (own and PUBLIC rows), `fa_lookup` (SELECT) and `fa_owner` (onboarding) (D16.2). `advisors`: SELECT own row or, for `tenant_admin`, the tenant; UPDATE only for `tenant_admin`, so no self-escalation (D16.4). Tenant and monthly partitions carry no grants (D16.3). Two explicit exemptions to the not-owner assertion: `fa_dbt` on schema `gold`, `fa_maint` on `messages` (partition DDL needs ownership of the parent). Entitlements are cached <= 60 s per process and the TTL is the revocation bound; `chat-api` does not consume Kafka (D14.9, ADR-022). The L0 leak matrix tests reads and writes, FK probes, direct partition access, advisor self-escalation and pooled-connection reuse.

**Dissent.** None among the three proposals (all agreed); the skeptic found the write-through-PUBLIC hole, fixed by D13a.

**What it makes harder later.** One RLS or code bug can expose all tenants, so the leak matrix is a permanent gate; six roles multiply pools and secrets; no per-tenant CMEK or performance isolation (noisy neighbours); `SECURITY DEFINER` is banned except `fa_tenant_lookup`.

**Trigger to revisit.** A tenant requires CMEK or performance isolation, "real firm data", or > 50 tenants: silo through `tenants.shard_id`.

**Amended 2026-11-07 (validation).** D13a stands unchanged: INSERT, UPDATE and DELETE are own-tenant only and only `fa_etl_public` writes PUBLIC. The FCA purge needs no exception because it is a pull model (a PUBLIC `source_purges` row; each firm tenant's `erasure-worker` inserts its own `deletion_requests` under its own role). The grant "`fa_etl_public` INSERT on firm tenants' `deletion_requests`" in deep-dive 05 §5.3 and 05-1 §5.13 is removed, and the L0 leak matrix asserts that `fa_etl_public` has no write on any firm tenant table (R4-D19 M6; ADR-026, ADR-039).

## ADR-001: As-built MVP is the baseline

Date: 2026-11-01. Status: accepted (decided by the orchestrator with Keshav).

**Context.** FinAdvisor is an interview-grade MVP, never deployed: Docker, CI on a real PR, `terraform validate`, the live eval and live Kong/LiteLLM/Langfuse checks were all deferred (`TODO.md:763, 818, 847, 877`; commit d6c2bd3). Its docs (README, architecture.md, mvp.md, threat model) disagree with the code in many places. Later research and architecture work needs one trusted statement of what actually exists.

**Options.**
1. Map the code as it is, and use that as the reference. Cost: one mapping and verification round, no design work yet.
2. Start from the docs' intended architecture. Rejected: the docs describe a JWT auth, Kong token budget and PII plugins, citation events and a working cloud deploy that the code does not have.
3. Design the target architecture now. Rejected for this run: no research has been done on scale, cost or compliance fit; the numbers Keshav gave (about 50 advisors, under 5 QPS, under $100 per month, US/EU/UK synthetic corpus) have not yet been checked against vendor facts.

**Evidence.** `deep-dive/00-as-built-baseline.md` was built from four independent code maps, a skeptic re-read of the highest-risk claims, vendor-doc checks (pgvector, PostgreSQL 16 RLS, Voyage, LiteLLM) and spot-checks of every quoted `file:line` at d6c2bd3. It records 62 gaps: 13 critical, 16 high, 27 medium, 6 low (deep-dive/00-as-built-baseline.md §13).

**Decision.** `deep-dive/00-as-built-baseline.md` records the code as of commit d6c2bd3 and is the reference for later research. `deep-dive/11-tech-stack.md` lists the stack as built. `arch/overview.md` keeps its template headings and records only goals and quality inputs; the target architecture is not yet decided and will be decided in later ADRs, each citing the gap IDs (G-nn) it resolves.

**What it makes harder later.** deep-dive/00-as-built-baseline.md goes stale as soon as the code changes: re-map before each research round and bump the commit hash in deep-dive/00-as-built-baseline.md §0. It also records defects as findings, not as decisions; nothing in it commits the project to fix, keep or replace any component.
