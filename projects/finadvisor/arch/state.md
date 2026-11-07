# finadvisor: arch state

## Decided
- ADR-001 to ADR-025: baseline, target architecture of rounds 1-3, planning resolutions (2026-11-01).
- ADR-026 to ADR-038: round 4 (2026-11-02 to 2026-11-07): connectors, bitemporal versions, atomic publish, erasure and proof of deletion, cells, login per firm, tenant move, data contracts, embedding generations, guardrails on real data, golden set and statistics, residency wording and egress rule. Amendments to ADR-009, 013, 014, 015, 016, 017, 022.
- ADR-039 (2026-11-07): stage 3 validation changes (R4-D18 V1-V5, R4-D19 M1, M3, M5, M6, M7, S1-S24). Dated "Amended 2026-11-07 (validation)" blocks on ADR-002, 008, 009, 010, 013, 018, 023, 025, 026, 027, 028, 029, 035, 036, 037, 038.
- Decision source: `library/research/r4/decision-r4.md` (R4-D1 to R4-D19).

## Round 4 stage reached
- Stage 1 (evidence) done. Stage 2 (design, decision-r4.md) done. Stage 3 (arch written) done: ADR-026..038, deep-dive files 01-11 with 04-1, 04-2, 05-1, `epic/plan.md`.
- Stage 3 validation DONE (2026-11-07): database docs check (`r4/V-docs-db.md`), AI docs check (`r4/V-docs-ai.md`), consistency check (`r4/V-consistency.md`), all folded into the arch and plan. M8 (section pointers) was fixed earlier by script.
- Next: stage 4, re-plan (cut E11-E13 tickets, update the published tickets, publish diff).

## What the validation changed
- Reranker: default `rerank-3-lite`; arm 3 = `rerank-3` vs `rerank-3-lite`; `rerank-2.5` leaves the design; TPM stated by model (02, 07, 10, 11, plan E3, E7, ADR-008, ADR-037).
- First-stage retrieval target p95 <= 600 ms (serial embed 0.25 s + SQL 0.30 s estimated); TTFT 2.0 s / 3.5 s unchanged; latency budget in 02 and the E3 gate recomputed (architecture.md, 02, 09, plan E3).
- Chat events carry ids, hashes, scores and flags only, no text; `eval-judge` reads text from Postgres by `message_id` (06 §6.4, 03, 04, 05-1, 07 #15, plan E5, E7; ADR-013, ADR-023).
- FCA purge is a pull model with a PUBLIC `source_purges` table; `fa_etl_public` has no write on firm tables; ADR-002 D13a stands (04-2 §4.20, 04, 05, 05-1, 06, 07, 08, diagram, plan E1, E11, E12; ADR-026, ADR-029).
- Chunk identity is the 05-1 8-column key; the 3-column key is a non-unique reuse index (ADR-035, 07, 11, plan E6). Cache purge on delete belongs to the `erasure-worker` (05-1 §5.7, plan E3).
- Model Armor behind a feature flag with a Presidio + heuristics fallback (ingest fails closed, prompts fail open with an audit flag) (04, 08, 06 §6.6, 11, ADR-036, ADR-009).
- BigQuery project default `default_max_time_travel_hours = 48`; PITR log retention 7 d; `llm_egress_ack` wording (opt-out, no region); global-data exception in the residency wording (04-2, 05-1 §5.14, 08 §8.7, 11, ADR-029, ADR-038).
- Should-fix items applied: price, `system_range`, no `source_state`, decision paths, `WORKER_ROLES`, judge metric rho^2, K-R4-4 criterion, stale plan originals, edge-case count, topic table columns, error codes, `pseudonym_id` in `acl.changes.v1`, `fund_rr_facts`, table owners, ADR-018 block, diagram edge (indexer embeds), Langfuse in tombstone checks, publish order, auth verification, Kong keys, mermaid `;` in 00.

## Open items (full list: deep-dive/10-open-questions.md)
- Spikes: Identity Platform same email in two tenants (E1, gates the identity tickets); Cloud SQL backup expiry while stopped (E12).
- Measurements: first-stage p95 against 600 ms and rerank latency and TPM by model (E3); Model Armor latency and the flag default (E4); Presidio DE/FR recall; recall with superseded rows; HNSW build time; `as_of` date formats; Kafka Basic limits; Langfuse deletion rate; two-cell compose footprint; golden-set detectable effect; second-region prices.
- Platform spikes (E2, E10): Kong SSE pass-through, `X-Serverless-Authorization`, private-DNS `run.app` egress, ai-proxy egress, `X-RL-Key`, Cloud SQL start time, Docling on 497K, Cloud Armor and Confluent cost.
- Proposed table owners (confirm at stage 4): E1 `pseudonym_map`; E11 `fund_rr_facts`; E12 `source_purges`, `erasure_receipts`, `reconciliation_manifests`, `reconciliation_findings`.
- Publisher-document legal view (pending counsel).
- Inputs from Keshav K1-K5 (GCP project, Langfuse keys, domain, 30 labels, branch protection): see ../state.md.
- Implementation gate: no build until Keshav says research is complete and tickets are ready.
