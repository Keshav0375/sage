# Round 4, stage 4: ticket changes for E7, E8, E9, E10 (2026-11-07)

Counts: keep-changed 23, new 27 (23 in E7-E10 plus E11-T28, E6-T22, E4-T34 written for the stage-4 answers; E8-T17 is counted in the 23), close 1. Tickets folders: `epic/E7-evaluation/tickets`, `epic/E8-frontend/tickets`, `epic/E9-observability-and-slos/tickets`, `epic/E10-cloud-deploy-and-operations/tickets`. Dependency check run over all 311 ticket files: every `depends_on` key exists, sizes are S or M, no cycle. Epics: E7 depends on E11 (E11-T17, T21, T26, T13) and E9-T5; E9 depends on E11, E12 only; E8 depends on E13; E10 depends on E12 and not on E9 tickets.

| key | action | reason |
|---|---|---|
| E7-T1 | keep-changed | Judge acceptance is judge-human rho^2 >= 0.4, not kappa; separate from the pilot (ADR-037 amended, ADR-017) |
| E7-T2 | keep-changed | Schema gets cluster_id and unit, slice, tranche, split public/private/synthetic, evidence spans; private skipped without the bucket (ADR-037, R4-D17, K-R4-3) |
| E7-T3 | keep-changed | Probe set kept as synthetic (outside the 200); templates for the refusal and injection slices of the 200 (ADR-037, ADR-017 L3) |
| E7-T4 | close | Superseded by ADR-037: 200 items by Keshav, not about 300; moved to `_superseded/` |
| E7-T5 | keep-changed | PR subset = tranche 1 (60 items); required `EVAL_BUDGET_USD` aborts a run; skipped private count (ADR-037) |
| E7-T6 | keep-changed | Tier-1 deterministic metrics (evidence-span recall@10, MRR, gold-version-in-top-5, numeric-in-span, footer present) per cluster; arm config (ADR-037, ADR-039 V1) |
| E7-T7 | keep-changed | Depends on E6-T22 and E4-T34 for arms 2 and 4; rerank/contextual spike becomes the four confirmatory arms with Holm via the Batches API; rerank-3 vs rerank-3-lite (ADR-037, R4-D17, ADR-039 V1) |
| E7-T8 | keep-changed | Cluster-level intervals; judge metrics gate only when rho^2 >= 0.4, else exploratory (ADR-037) |
| E7-T10 | keep-changed | Release gates: refusal >= 0.90, numeric false rejects <= 3%, zero ungrounded numbers, paired recall lower bound >= -2 pp, ASR <= 3/300 (ADR-017, ADR-037) |
| E7-T13 | keep-changed | Weekly run on the 200-item set plus guardrail sets and edge case #21 ASR line (ADR-037, 07 7.4 #21) |
| E7-T16 | keep-changed | `eval.sample.v1` carries ids, hashes, flags only, no text (ADR-039 M5) |
| E7-T17 | keep-changed | Judge reads redacted text from Postgres `messages` by `message_id`, skips erased messages (ADR-039 M5, 9.6) |
| E7-T19 | new | Keshav labels the 30-item pilot (about 6-8 h) with the labelling CLI (K-R4-4, ADR-037, R4-D15) |
| E7-T20 | new | Keshav labels items 31-60 (about 6-8 h) to complete tranche 1 = PR subset (K-R4-4, ADR-037) |
| E7-T21 | new | Keshav labels tranche 2, 140 items (about 28-39 h of the 40-55 h) and the 15% intra-rater check (K-R4-4, ADR-037, 2.10) |
| E7-T22 | new | L0 `golden_stats` check: at least 40 clusters, at most 5 per cluster (ADR-037, R4-D17) |
| E7-T23 | new | Cluster aggregation, sign-flip permutation, exact McNemar, Holm over a fixed family, small slices exact or exploratory (ADR-037) |
| E7-T24 | new | Frozen pre-registration naming exactly the four arms before the first run (ADR-037, R4-D17) |
| E7-T25 | new | PII sets openpii-1.5m and Gretel finance, DE/FR recall, gauges (ADR-037, ADR-036, 9.9) |
| E7-T26 | new | Injection sets gandalf, deepset (smoke only), LLMail-Inject wrapped chunks, ASR line (ADR-037, ADR-036, 7.4 #21) |
| E7-T27 | new | Detectable effect computed from the pilot and recorded before any arm runs (ADR-037, R4-D15) |
| E8-T2 | keep-changed | Resolve slug to cell, then tenant from the per-cell host (ADR-031, 6.11) |
| E8-T3 | keep-changed | One auth instance per firm, in-memory, no persisted tenantId (ADR-032) |
| E8-T4 | keep-changed | WRONG_CELL and TENANT_MOVED follow the hint once, CELL_UNAVAILABLE per-firm state, full 6.1 code table incl. ENTITLEMENT_CHANGED (ADR-031, 6.11, ADR-033) |
| E8-T6 | keep-changed | Renders `notice` kinds, ANSWER_WITHHELD reasons, ENTITLEMENT_CHANGED abort (6.2, ADR-033, ADR-036) |
| E8-T7 | keep-changed | Jurisdiction chip on citations from the new `jurisdiction` field (6.2, ADR-027) |
| E8-T13 | new | As-of chip sends ISO `as_of`; echoes the date the server applied (ADR-027, 6.10) |
| E8-T14 | new | Firm switcher, one session per firm, nothing persisted (ADR-032, #17) |
| E8-T15 | new | Licence footers per cited class and `private_demo` label for publisher sources (ADR-036, ADR-026, 8.8, K-R4-3) |
| E8-T16 | new | Playwright for #17 browser part, 421/503, as-of echo, footers, ENTITLEMENT_CHANGED (ADR-032, ADR-036, 7.4 #17) |
| E9-T5 | keep-changed | Registry equals the whole 9.2 table incl. round-4 rows, with a dashboard attribute (ADR-034, ADR-036) |
| E9-T12 | keep-changed | First-stage line 600 ms not 300; guardrail panels on the chat dashboard (ADR-039 M3, 9.9) |
| E9-T13 | keep-changed | Retrieval first-stage SLO <= 600 ms, TTFT unchanged (ADR-039 M3) |
| E9-T16 | keep-changed | Budget alert at $180 against the $200 ceiling plus the $75 LLM share (R4-D16, 9.5, 2.5) |
| E9-T18 | new | Data-lifecycle dashboard: erasure windows per store, deletion receipts, canary, reconcile, ingest (ADR-030, ADR-034, 9.8) |
| E9-T19 | new | Reconciliation alert policies per pair, ticket vs page, silent when the system is stopped (ADR-034, 9.7) |
| E9-T20 | new | Erasure age > 4 h, Langfuse 24 h, FAILED-canary (E12-T21) and E12 job-failure alerts (ADR-029, ADR-030, 9.8) |
| E9-T21 | new | Connector frozen, > 5% quarantined and silent-edit alerts (ADR-026, ADR-036, E11-T7 hand-off) |
| E9-T22 | new | Guardrail hit, skip, latency and numeric-gate metrics on the live path; precision/recall gauges come from E7-T25/T26 (ADR-036, ADR-037, 9.9) |
| E9-T23 | new | Drill for every new round-4 alert (E9 Done-when, ADR-029, ADR-034) |
| E10-T6 | keep-changed | Cloud SQL backups 7 d and PITR log retention 7 d, validated (ADR-029, ADR-039 V5) |
| E10-T12 | keep-changed | Nine Scheduler triggers incl. reconcile and erasure-verify; no cron for canary or erasure (4.12, ADR-034) |
| E10-T18 | keep-changed | Erasure job runs first after Cloud SQL is up and before any traffic path (ADR-029, ADR-039, 5.14) |
| E10-T25 | new | Terraform for the E12 jobs, per-cell KMS HMAC receipt key, append-only ledger export bucket (ADR-030, ADR-029, 4.12) |
| E10-T26 | new | Retention settings in Terraform and checked: BigQuery 48 h default, GCS soft delete 0, topics, logs 7 d (ADR-029, ADR-039 V2) |
| E10-T27 | new | demo-up canary drill then 1-token model preflight (ADR-030, 9.8, R4 E10 line) |
| E10-T28 | new | Cloud restore drill: PITR clone, erasure-replay before traffic (ADR-029, ADR-030, 7.4 #14) |
| E8-T4 | keep-changed | (updated again) cell hint is followed only when its host equals the `/resolve` answer (R4-D20 Q15) |
| E8-T15 | new | (updated) per-citation `source_class` label and stored footers in history (R4-D20 Q2) |
| E8-T17 | new | Quarantine summary view for the compliance role, depends on E11-T28 (R4-D20 Q1, ADR-036) |
| E11-T28 | new | `GET /v1/admin/quarantine/summary`: counts by source and reason code, compliance role, no text (R4-D20 Q1, ADR-036) |
| E6-T22 | new | `voyage-context-4` eval-only embedding generation on the E12 generations, for arm 2 (R4-D20 Q14, ADR-037, ADR-035) |
| E4-T34 | new | Flagged `lookup_fund_facts` tool over `fund_rr_facts` and KID fee rows, for arm 4 (R4-D20 Q14, ADR-037) |
| E10-T12 | keep-changed | (updated again) ten triggers incl. daily `ledger-export`; erasure-verify hourly at minute 30 (R4-D20 Q5, Q8) |
| E10-T25 | new | (updated) `KAFKA_VERIFY_API_KEY` read-only key; ledger-export scheduled, erasure-replay manual (R4-D20 Q5, Q6) |
| E9-T5 / T18 / T20 / T21 / T23 | keep-changed / new | (updated) E11/E12 metric names adopted, no extras list; ledger-export job alert (R4-D20 Q9, Q10) |
| E7-T1 / T2 / T21 | keep-changed | (updated) binary labels with phi coefficient, `JUDGE_MIN_RHO2` and `EVAL_PRIVATE_BUCKET_URI` named; Keshav total about 46-63 h with the relabel (R4-D20 Q11, Q13) |

## Questions

Answered: see decision-r4.md (block "E7-E10 (answers to changes-E7-E10.md Q1-Q16)").

One ticket-level adjustment: the arch has no stored KID fee structure, so E4-T34 creates a minimal `kid_fee_rows` table filled by a deterministic parser over KID table chunks (eval tenant), behind the flag.
