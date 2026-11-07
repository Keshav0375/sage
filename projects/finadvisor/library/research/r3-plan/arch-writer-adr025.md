# arch-writer: ADR-025 report
Status: DONE. Base: /Users/keshav/Projects/sage/context/projects/finadvisor/
- arch/decisions.md: new ADR-025 at top (R1-R85 grouped by epic, K1-K5 under "Inputs from Keshav", R83 as recorded exception to "no allUsers"). ADR-010 text fixed to 60 s TTL-only, "(amended by ADR-025, R19)".
- arch/overview/06 §6.6: DB_PORT, MODEL_RETIRE_WARN_DAYS, GATE_MIN_RESULTS, SEARCH_TOP_K_MAX, RETRIEVAL_LEG_LIMIT, STALE_AFTER_MONTHS, CITATION_MIN_OVERLAP, KAFKA_CONSUMER_MAX_ATTEMPTS, KAFKA_RETRY_BACKOFF_MS, OUTBOX_RELAY_BATCH, OUTBOX_RELAY_POLL_MS, AUDIT_IP_SALT added; INPUT_MAX_CHARS, TENANT_*, SSE_REPLAY_TTL_S, FACTSHEET_MAX_CHUNKS, RATE_LIMIT_*, DEMO_TTL_HOURS, MESSAGES_RETENTION_MONTHS filled (owner column kept). Each cites ADR-025.
- arch/overview/09 §9.2: llm_cost_usd_total, readiness_failing, model_retirement_days, citation_rejected_total, outbox_unpublished; §9.5 R72 thresholds, R76/R21 window, R75 channel.
- arch/overview/05 §5.2 + ER diagram: tenant_usage added; turn_events.request_hash added.
- STATE.md Open decisions: K1-K5 with gated tickets.
- arch/overview/10: item 11 added (turn_id conflict, below).
No diagrams added (ER diagram edited only).
Flags for orchestrator:
1. R48 says turn_id = UUIDv5(tenant_id, Idempotency-Key); §5.2 says uuid5(namespace, tenant_id||advisor_id||Idempotency-Key). I did not change §5.2's formula; recorded as §10 item 11 and in ADR-025 consequences.
2. request_hash semantics are not defined in R3/R48; added the column only.
3. R36 (embed_query 2 retries) and R73 (price table) name no config key; not added to §6.6.

Update (coordinator rulings): R48 amended to uuid5(namespace, tenant_id||advisor_id||Idempotency-Key) + request_hash rule (409 on mismatch); §10 item 11 removed; EMBED_MAX_RETRIES=2, LLM_PRICE_TABLE_JSON, LLM_MONTHLY_BUDGET_USD=75 added to §6.6.
