## 7. Scaling, failure modes and recovery

### 7.1 Failure modes

Principle: chat depends on Cloud SQL, Voyage, Anthropic, Model Armor and Identity Platform; it never depends on Kafka, BigQuery, Langfuse or Valkey-backed features other than Kong rate limiting. `chat-api` has no Kafka client.

| Failure | Detection | Behaviour | Recovery |
|---|---|---|---|
| Kafka or Schema Registry down | producer errors, `outbox_oldest_age_s` | Chat unaffected. Outbox rows accumulate in Postgres; relay retries with backoff. Consumers idle | Relay drains on recovery; sinks dedupe by `event_id`. Alert on outbox age |
| Poison or invalid message, envelope mismatch, PUBLIC event on a pipeline topic | consumer exception, envelope check | Message to `dlq.v1` (redacted, with reason); consumer continues | Fix, then operator re-publishes from DLQ |
| Consumer crash or duplicate delivery | consumer lag, restarts | At-least-once; `processed_events` makes sinks idempotent | Worker pool restarts consumers from committed offsets |
| ACL change not yet applied (relay or applier lag or failure) | `acl_apply_lag_s`, request status `pending` / `failed` | The old ACL still applies until the applier commits; then `acl_version` bumps and cached answers become unreachable; a racing cache hit is re-verified under RLS | Applier retries (idempotent on `request_id`); failed requests surface through `GET /v1/admin/acl-changes/{id}` |
| Cloud SQL stopped, down or failing over | `/readyz` DB check, connection errors | `demo`: by design off; `prod`: HA failover. Requests fail with `RETRIEVAL_UNAVAILABLE` / 503, stream `error` event | `demo-up`; HA failover; start time is unmeasured (§10) |
| Cloud SQL connection exhaustion | pool errors, `max_connections` metric | Budget keeps pools <= 300 of 400; excess requests wait or fail with `RETRIEVAL_UNAVAILABLE` | Lower `DB_POOL_SIZE` or max instances |
| Anthropic error, 429, timeout | `LLMClient` exceptions | Timeouts, retries with jitter, circuit breaker; if `LLM_FALLBACK_ENABLED` then `claude-sonnet-4-6` (50% pricier, own cache, 1,024-token cache minimum); else SSE `error LLM_UNAVAILABLE`. Never a different provider | Breaker half-opens; alert on fallback use |
| Retired or soon-retiring model id | readiness check, CI check | `/readyz` fails; CI blocks | Change config; rerun gate (also against the fallback) |
| Voyage embed failure | embed exception | No fallback model (single provider accepted). `RETRIEVAL_UNAVAILABLE` error event | Retry by client; alert |
| Voyage rerank timeout or 429 (Tier-1 2M TPM, ~5 QPS) | rerank timeout, 429 counter | Fall back to RRF order and mark the turn degraded: SSE `meta {retrieval_degraded: true}`, `messages.retrieval_degraded = true`, `rerank_fallback_total{reason}` and `rerank_429_total` increment. Counted and visible, never silent | Alert when > 5% of turns are degraded in 15 min; request a Voyage tier upgrade before load tests |
| Model Armor timeout or error | 500 ms timeout | Fail closed: SSE `error GUARD_UNAVAILABLE`, request not answered | Retry; alert |
| Presidio error | exception | Fail closed (no unredacted text goes onward) | Fix; alert |
| Confidence gate fails | gate score | `refusal NO_FIRM_DOCUMENTATION` + escalate offer, no LLM call; counted | n/a (expected behaviour) |
| Citation verifier rejects | verifier result | Answer is not released with unverified `[n]`; error or refusal event; counted | Eval L2 tracks rate |
| Valkey down (Kong counters) | Kong errors | Plugin `fault_tolerant` setting decided in E2. Cloud Armor and FastAPI limits remain | Recreate with `demo-up` |
| Identity Platform verifier cannot refresh keys | auth exception | Use cached keys (firebase-admin caches); with no cached keys, 503 | Keys refresh |
| Langfuse or OTel exporter down | exporter errors | Dropped asynchronously; never blocks a request | n/a |
| `eval-judge` or its topic down | judge lag | No effect on chat; sampled turns judged later | Replay from `eval.sample.v1` |
| BigQuery sink error | sink exception | Retries, then DLQ; idempotent by `event_id` | Replay |
| SSE connection drop | client | Client reconnects with `Last-Event-ID`; server replays persisted events | n/a |
| chat-api instance dies mid-turn | no `done`, lease expiry | Replay endpoint emits `error TURN_INTERRUPTED` | Client resubmits with a new `Idempotency-Key` |
| Pooled connection reuse leak | L0 leak matrix | Prevented: only transaction-local `set_config(.., true)`; unset setting raises (fail closed) | Test blocks merge |
| Hot tenant | per-tenant concurrency / token budget | `RATE_LIMITED` / `TENANT_BUDGET_EXCEEDED` for that tenant | Adjust `tenants.budgets` |
| Rows land in DEFAULT `chunks` or `messages` partition | alert on non-empty | Treated as a bug (missing onboarding or maintenance) | Onboard the partition, move rows |
| Migration failure | `migrate` job exit code | Deploy halts before traffic shift | Fix forward or roll back image |
| Bad deploy | smoke test on tagged no-traffic revision | Traffic not shifted | Shift back to previous revision |
| Zone or region outage | n/a | `demo`: zonal, accepted. `prod`: HA is zonal failover only | No regional DR in scope (RPO / RTO not set) |

### 7.2 Scale triggers

| Trigger | Action | Source |
|---|---|---|
| One tenant > 250k chunks, or total > 2M chunks, or ANN p95 > 100 ms | Grow partitions / silo a tenant through the `tenants.shard_id` seam | D2, D13b |
| PUBLIC partition > 250k chunks | Sub-partition PUBLIC by source | D13b |
| Separate scaling of retrieval needed, or a second consumer of retrieval | Extract `retrieval` into its own Cloud Run service with its own DB role | D1, D13c |
| > 10 tenants, or a sensor is needed | Run a Dagster daemon in the cloud (today daemon-less) | D3, D15.4 |
| Real firm data | Confluent Standard RBAC (per-tenant ACLs); self-host Langfuse v4 or drop third-party tracing; revisit BigQuery and trace controls | D13j, D13l |
| Rerank at ~5 QPS on Voyage Tier 1 | Request a tier upgrade before load tests | D13e |
| Schema Registry > 100 schemas, or Confluent limits (50 keys, 1,000 ACLs, 1,500 partitions) approached | Move off the free tier / consolidate | evidence-r2.md, D15.8 |
| Need for log-based CDC outbox | Optional Debezium outbox connector (learning epic) | D4 |
| Always-on availability required | Switch to the `prod` profile: HA Cloud SQL flag, min instances >= 1 (~$300+/month) | D13g, D13r |
| Revocation lag above the 60 s TTL becomes unacceptable | Add a push-invalidation path (a new ADR); today there is none | D14.9 |
| Kong limits (OSS cannot key on a verified tenant) become a problem | Move per-tenant limits further into FastAPI or revisit the gateway | D12 |
| Private-DNS `run.app` egress spike fails | All-traffic egress + Cloud NAT (about +$32/month) with an ADR | D16.12 |

Scaling levers: `chat-api` concurrency and max instances (Cloud Run), `fa-gateway` max 2, worker pool instance count (no autoscaling), Cloud SQL tier (2 vCPU / 8 GiB; HA flag), partition per tenant. Connection budget: `max_connections` is 400 on 8 GiB; pool per instance x max instances over all services must stay <= 300, leaving headroom for migrations, dbt and Dagster (managed pooling is Enterprise Plus only).

### 7.3 Recovery

- Ingest is replayable: bronze is immutable, stages are idempotent, chunks are unique on `(tenant_id, chunk_hash, embed_model)`; re-embedding is a replay of `docs.bronze.v1`.
- Analytics are rebuildable from Kafka and the Postgres outbox; BigQuery sinks dedupe by `event_id`.
- Database backups, point-in-time recovery and RPO / RTO are not specified by the brief; they are set in E10 when the `prod` profile is built.
- Deploys: tagged no-traffic revision, smoke test, then shift; rollback is a traffic shift to the previous revision; images by digest.
