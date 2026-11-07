# finadvisor: arch state

## Decided
- ADR-001 to ADR-025: baseline, target architecture of rounds 1-3, planning resolutions (2026-11-01).
- ADR-026 to ADR-038: round 4 (2026-11-02 to 2026-11-07): connectors, bitemporal versions, atomic publish, erasure and proof of deletion, cells, login per firm, tenant move, data contracts, embedding generations, guardrails on real data, golden set and statistics, residency wording and egress rule. Amendments to ADR-009, 013, 014, 015, 016, 017, 022.
- Decision source: `library/research/decision-r4.md` (R4-D1 to R4-D17).

## Round 4 stage reached
- Stage 1 (evidence) done. Stage 2 (design, decision-r4.md) done. Stage 3 (arch written) done: ADR-026..038, deep-dive files 01-11 with 04-1, 04-2, 05-1, `epic/plan.md`.
- Stage 3 validation partly done: database docs check (`r4/V-docs-db.md`) DONE; AI docs check (`r4/V-docs-ai.md`) DONE; consistency check (`r4/V-consistency.md`) STOPPED, pending a rerun.
- Next: rerun the consistency check, fold the verdicts below, then stage 4 re-plan and publish diff.

## Validation verdicts not yet folded (from the HALTED entry in ../state.md)
- rerank-3 replaces rerank-2.5 as the default (ablation arm 3 = rerank-3 vs rerank-3-lite).
- BigQuery project `default_max_time_travel_hours` = 48.
- Model Armor behind a flag, with a fallback.
- Voyage `llm_egress_ack` wording: opt-out, no region.
- Spikes: Cloud SQL backups while stopped; Identity Platform same email in two tenants.

## Open items (full list: deep-dive/10-open-questions.md)
- Platform spikes (E2, E10): Kong SSE pass-through, `X-Serverless-Authorization`, private-DNS `run.app` egress, ai-proxy egress, `X-RL-Key`, Cloud SQL start time, rerank latency and TPM, Docling on 497K, Cloud Armor and Confluent cost.
- Round-4 unverified: Identity Platform same email, Model Armor latency, Presidio DE/FR recall, second-region prices, PITR log retention, backup expiry while stopped, recall with superseded rows, `as_of` date formats, HNSW build time, Kafka Basic limits, Langfuse deletion rate, two-cell compose footprint, golden-set detectable effect, publisher-document legal view.
- Inputs from Keshav K1-K5 (GCP project, Langfuse keys, domain, 30 labels, branch protection): see ../state.md.
- Implementation gate: no build until Keshav says research is complete and tickets are ready.
