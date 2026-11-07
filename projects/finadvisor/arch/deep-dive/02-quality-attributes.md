> Part of [architecture](../architecture.md) · [diagram](../architecture-diagram.md)
## 2. Quality attributes (with numbers: load, latency, availability, cost)

All latency figures are estimates to be measured (D13e). They replace the earlier requirement figures (TTFT p50 < 1.5 s, p95 < 3 s). Round 4 (2026-11-02) added the erasure promise (§2.7), as-of correctness (§2.8), reconciliation freshness (§2.9), the guardrail latency budget (§2.1) and eval sizes (§2.10).

### 2.1 Latency

| Metric | Target | Notes |
|---|---|---|
| Time to first token (TTFT) | p50 < 2.0 s, p95 < 3.5 s | with rerank and guardrails |
| Retrieval first stage (embed + hybrid SQL) | p95 < 300 ms | to be measured; see the reconciliation note below |
| Rerank | p95 < 700 ms | Voyage rerank ~0.68 s per call measured by a third party on short facts (evidence-r2.md) |
| Full answer | p95 < 8 s | |

#### Guardrail latency budget inside TTFT 2.0 / 3.5 s (ADR-036)

Every figure below is an ESTIMATE from r4/P-reliability.md §11, to be measured in E3 and E4; nothing here is a measurement. Sources of the arithmetic: the sums are 0.15 + 0.15 + 0.35 + 0.8 + 0.1 = 1.55 s at p50 and 0.25 + 0.30 + 0.70 + 1.2 + 0.15 = 2.60 s at p95 (checked in r4/S-skeptic-3.md).

| Step on the critical path | p50 / p95 estimate | Status |
|---|---|---|
| Embed query (runs in parallel with the Model Armor prompt screen) | 0.15 / 0.25 s | to be measured |
| Model Armor prompt screen (parallel to embed) | X, unknown | to be measured from the Cloud Run region: latency, SLA and precision are NOT FOUND in the docs. The fail-closed timeout is set from the measured p99 plus a margin, not 500 ms by default |
| First-stage hybrid SQL | 0.15 / 0.30 s | to be measured |
| Rerank | 0.35 / 0.70 s | to be measured |
| LLM first token | 0.8 / 1.2 s | to be measured |
| Sentence buffer + numeric gate + citation verifier | 0.1 / 0.15 s | to be measured; regex + Decimal gate estimated under 10 ms per answer |
| Sum (without Model Armor X and the items below) | 1.55 / 2.60 s | headroom against 2.0 / 3.5 s: 0.45 s at p50, 0.90 s at p95 |

Not yet in the budget (to be measured; named by r4/S-skeptic-3.md): Kong hop, `auth` and `principal`, Presidio on the prompt, answer-cache lookup, Cloud Run cold start, and the sentence-level release of the numeric gate. The user sees the first complete sentence, not the first token, so first visible text is later than TTFT by an amount to be measured (the skeptic's rough figure is +0.3-0.5 s at typical streaming speed, unmeasured).

Rule (ADR-036): any guard that adds more than 150 ms p95 to the critical path moves to async-after-first-sentence or is dropped. Precision, recall and latency per guardrail are measured weekly on the sets of §2.10 and reported through §9.2.

Reconciliation to do by measurement: the p95 estimates for embed (0.25 s) and first-stage SQL (0.30 s) sum to 0.55 s when serial, against the 300 ms first-stage target above (§10).

### 2.2 Availability

| Profile | Target | Basis |
|---|---|---|
| `demo` (default) | No SLA | Zonal Cloud SQL, stopped by default, Confluent Basic 99.5% (D13g) |
| `prod` | 99.5% monthly on the chat path | HA Cloud SQL flag on, min instances >= 1. Applies to `prod` only |
| Ingest | Asynchronous, minutes of lag | requirements.md |
| Entitlement revocation | <= 60 s worst case | `principal` cache TTL 60 s is the bound; `chat-api` does not consume Kafka (D14.9). Document ACL changes are applied asynchronously by the `acl-applier` worker, which now polls `acl_change_requests` in Postgres (R4-D7, ADR-022 amended), so a Kafka outage does not delay them; the bump of `acl_version` then makes older cached answers unreachable. An in-flight turn re-reads `entitlement_version` before each retrieval or tool step and before `done` (ADR-033) |
| Cell isolation | A failed cell affects only its own tenants | stated limit: an Anthropic or Voyage outage hits every cell (ADR-031, ADR-038) |

RPO / RTO: not set by the brief.

### 2.3 Scale envelope

| Dimension | Demo (built and tested) | Designed (documented) |
|---|---|---|
| Tenants | 2-3 synthetic firms + PUBLIC | 50 |
| Advisors | a few hundred | 2,000 |
| Peak QPS | ~10 | 5-50 (requirements.md range) |
| Corpus | 50 docs / ~114 chunks today. First real set: about 25,000 child chunks from about 25-30 MB of text, about 7M tokens (ASSUMPTION: 4 chars/token, ~400-token children; r4/P-reliability.md A1) plus synthetic per tenant | 100k-1M chunks across tenants (1M x 1024 halfvec ~ 2 GB); two embedding generations double HNSW memory during a re-embed, so 1M chunks is outside the 8 GiB instance envelope and 250k per tenant fits (ADR-035) |
| Rerank throughput | Voyage Tier 1: 2M TPM, ~5 QPS at 10-15 candidates x <= 400 tokens (~6k tokens/query) | request a tier upgrade before load tests (D13e). Round-4 evidence lists rerank-2.5-lite at 4M TPM; E3 measures which applies (§10) |
| Partition triggers | n/a | one tenant > 250k chunks, total > 2M chunks, or ANN p95 > 100 ms (§7.2) |
| Anthropic and Voyage limits, re-embed times | n/a | §7.5 |

### 2.4 Quality gates (blocking)

Citation accuracy >= 0.95, faithfulness >= 0.90, cross-tenant/tier/jurisdiction leaks = 0, retrieval recall regression <= 2 points (ADR-017). Round 4 adds the lines proposed in ADR-037 (proposed by the author, not sourced): zero ungrounded numbers in released answers on the golden set, zero cross-cell leaks, unanswerable-correct-refusal >= 0.90, numeric-gate false rejects on correct answers <= 3%, indirect-injection attack success <= 3 of 300 trials. Staleness: sources with `last_reviewed_at` older than 12 months are flagged, computed server-side from today's date; for law texts the warning is about state (`superseded`, `revoked`, `known_pending`), not age (ADR-036).

### 2.5 Cost (monthly, us-central1 list prices; D13r)

| Profile | Estimate |
|---|---|
| Idle | $40-55: ALB $18.25, Cloud Armor ~$6-10 (UNVERIFIED), Cloud SQL storage + IP ~$4-6, PSC endpoint, Confluent Basic ~$0-5 (UNVERIFIED), Artifact Registry / Secrets / GCS / logs ~$5, Kong / API / workers at 0 |
| Demo month (~40 h up, ~2,000 chats) | $110-160 including LLM, evals, Valkey and Cloud SQL hours |
| Round-4 delta (R4-D16) | Steady about $22-30/month; first two months about $45 (ablation arms one-off). r4/S-skeptic-3.md: at the upper baseline the first two months can reach about $205, and a realistic eval run is $8-15 ($35-60/month with arms), so the delta is optimistic |
| Budget alert | $180/month total guards the $200 ceiling (R4-D16; §9.5). `EVAL_BUDGET_USD` caps eval runs; ablation runs use the Message Batches API (50% off) |
| Always-on `prod` | $300+ (out of budget, by design) |
| Budget | $100-200/month (Keshav) |

Unit prices (evidence-r2.md, confirmed for Sonnet 5.5 and Haiku 5.5 on https://platform.claude.com/docs/en/about-claude/pricing on 2026-11-02): Sonnet 5.5 $2 / $10 per MTok in/out, cache read $0.10; Haiku 5.5 $0.10 / $0.50; Batch API -50%; fallback Sonnet 4.6 $3 / $15; voyage-4 $0.06/M tokens (200M free); rerank-2.5-lite $0.05/M; Model Armor free to 2M tokens/month then $0.10/1M; Cloud SQL Enterprise 2 vCPU / 8 GiB ~$101 while running (HA ~$202); Memorystore Valkey shared-core-nano ~$23/month (~$0.03/h, only while the demo is up).

### 2.6 Other attributes

- Isolation: zero cross-tenant reads or writes; enforced by Postgres RLS, tested by the L0 leak matrix on every PR (§5.4, ADR-017). Cross-cell: each cell physically holds only its tenants (ADR-031).
- Cost control: per-tenant token budgets and per-tenant concurrency in FastAPI (numbers set in E4); BigQuery `maximum_bytes_billed`; budget alerts (§9).
- Operability: one developer; one Python image with three entrypoints; Terraform owns everything except the Valkey instance lifecycle, which the demo script creates and deletes (fixed instance name, outside Terraform state; stated once here and in §4.12); demo up/down is one command each. At every demo start the erasure job runs first, then the canary (§2.7, §9.8).

### 2.7 Erasure promise (R4-D9, ADR-029, ADR-030)

Documented wording, not "instant". The promise is stated in windows per store class; no window is claimed that the system cannot observe.

| Store class | Stores | Promise | Basis |
|---|---|---|---|
| Live stores | Postgres, search index, answer cache, GCS | Within 24 h of the system running. In demo-on-demand the erasure job runs first at every start | Postgres explicit ordered DELETE, then VACUUM; GCS soft delete 0 (ADR-029) |
| Analytics and streams | BigQuery (including 48 h time travel and 7 d fail-safe), Kafka | Within 14 d | BigQuery `max_time_travel_hours=48` on every dataset (2 d + 7 d fail-safe = 9 d; https://cloud.google.com/bigquery/docs/time-travel); delete-policy topics with retention 7 d and `segment.ms` 1 d, about 8 d (https://docs.confluent.io/cloud/current/topics/manage.html) |
| Backups | Cloud SQL backups | Within 7 d, plus ledger replay on every restore before traffic | automated backup retention 7 d (https://cloud.google.com/sql/docs/postgres/backup-recovery/backups); PITR log days UNVERIFIED (§10) |
| Traces | Langfuse | Provider best effort, "usually within 15 minutes", no confirmation; stated as provider-bound | evidence-r4.md §2.3 |
| Logs | Cloud Logging | 7 d retention and no PII in logs | ADR-029 |
| Model providers | Anthropic, Voyage | Outside the promise (provider retention terms; Anthropic Batch is not ZDR-eligible) | ADR-038 |

Not promised and not observable: the BigQuery fail-safe and Cloud SQL PITR log retention are documented windows. The canary measures only observable stores and runs at each demo start, not on a weekly cron (the system is often stopped). Text already shown to an advisor and records under legal hold (`retention_class`) are not recalled; the receipt says "retained: legal basis X". A receipt never says "erased everywhere" before phase 2 (§6.9). Subject rows carry a random `pseudonym_id`; deleting the mapping unlinks them at once, but unlinking alone is not claimed as erasure.

### 2.8 As-of correctness (ADR-027)

- `as_of` comes from the deterministic date parser, the UI chip, or the Postgres date in UTC, never from the model. Ranges are half-open.
- The answer echoes the parsed `as_of` date (§6.10).
- A post-generation check requires every cited chunk's `valid_range` to contain `as_of`; a violation blocks release.
- UK sources use `valid_from_basis = 'observed'` and refuse a date before the first observation ("no version history for this source").
- The answer cache key carries `as_of`, `embed_model` and `source_epoch` (amends ADR-015); every publish, supersede, retire, withdraw or erase bumps `corpus_version` in the same transaction.
- Tests: boundary days, app clock +/-2 h and a DST day return the same chunks (§7.4 #9).

### 2.9 Reconciliation freshness while running (ADR-034, ADR-030)

| Check | Frequency | Bound |
|---|---|---|
| source to bronze, bronze to silver, silver to chunks | hourly `reconcile` job, only versions idle > 30 min | a divergence is found within one run after the version has been idle 30 min; the job runs only while the system runs, so a stopped system raises no alert |
| ANN self-hit canary | with each reconcile | rate >= 0.99 expected; page below 0.95 |
| Postgres to BigQuery | daily count and md5 | one day |
| Cell vs cell PUBLIC manifest | with each reconcile | ticket on drift |
| Tombstones (invariant: tombstone implies absence everywhere) | hourly for 24 h after any erasure, then daily | page; `tombstone_violations_total` = 0 |

A parser bump is a planned re-baseline keyed on `parser_version`, not an alert storm (§9.7).

### 2.10 Eval sizes (ADR-037, K-R4-4)

| Set | Size | Notes |
|---|---|---|
| Golden set | 200 items, labelled by Keshav (about 39-56 h, ESTIMATE) | Slices (sum 200): single-hop US 25 / EU 25 / UK 15; tables and fee numbers 25; temporal as-of, superseded, revoked 30; multi-document and cross-jurisdiction 20; cross-lingual 20; unanswerable, out-of-scope and ACL refusal 20; injection-in-document 10; compliance checks 10. Tranche 1 = 60 items (the PR subset), tranche 2 = 140. Public items about 165 and private items about 35 (private items run only where the private bucket is mounted, K-R4-3) |
| Cluster rule | at least 40 clusters, at most 5 items per cluster | cluster unit = provision or product (R4-D17); analysis at cluster level; no fixed n_eff claim; the detectable effect is computed after a 30-item pilot and recorded |
| Confirmatory arms | exactly 4, Holm | contextual retrieval vs section-path prefix; voyage-context-4 vs plain chunks; rerank-3 vs rerank-2.5; structured lookup vs table chunks. All others exploratory. Slices under 30 items use exact tests or stay exploratory |
| Intra-rater check | 15% relabelled after one week; agreement >= 0.8 or the labelling guide is revised | no second reviewer exists |
| PII guardrail set | 2,000 sampled en/de/fr from ai4privacy openpii-1.5m (CC-BY-4.0 per card) + 2,000 Gretel finance multilingual (Apache-2.0) | per-class precision and recall; IBAN and account numbers get generated cases with valid checksums |
| Direct injection | 1,000 Lakera gandalf (MIT); deepset 662 (licence conflict: smoke only); JBB benign plus the golden questions as benign | over-refusal measured |
| Indirect injection | LLMail-Inject (MIT) strings wrapped into 300 real chunks plus 300 clean real chunks per source | attack success line in §2.4 |

Pass lines for the guardrail sets (PII recall >= 0.90 on must-redact classes, direct-injection recall >= 85% at FPR <= 2%, scanner FPR <= 1% on real chunks) are the author's proposals in r4/P-reliability.md §12, not sourced. Cost: baseline run estimated $4.2 by P-reliability and $8-15 by the skeptic (tool turns resend context).
