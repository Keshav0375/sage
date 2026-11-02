## 2. Quality attributes (with numbers: load, latency, availability, cost)

All latency figures are estimates to be measured (D13e). They replace the earlier requirement figures (TTFT p50 < 1.5 s, p95 < 3 s).

### 2.1 Latency

| Metric | Target | Notes |
|---|---|---|
| Time to first token (TTFT) | p50 < 2.0 s, p95 < 3.5 s | with rerank |
| Retrieval first stage (embed + hybrid SQL) | p95 < 300 ms | |
| Rerank | p95 < 700 ms | Voyage rerank ~0.68 s per call measured by a third party on short facts (evidence-r2.md) |
| Full answer | p95 < 8 s | |

### 2.2 Availability

| Profile | Target | Basis |
|---|---|---|
| `demo` (default) | No SLA | Zonal Cloud SQL, stopped by default, Confluent Basic 99.5% (D13g) |
| `prod` | 99.5% monthly on the chat path | HA Cloud SQL flag on, min instances >= 1. Applies to `prod` only |
| Ingest | Asynchronous, minutes of lag | requirements.md |
| Entitlement revocation | <= 60 s worst case | `principal` cache TTL 60 s is the bound; `chat-api` does not consume Kafka (D14.9). Document ACL changes are applied asynchronously by the `acl-applier` worker; the bump of `acl_version` then makes older cached answers unreachable (ADR-022) |

RPO / RTO: not set by the brief.

### 2.3 Scale envelope

| Dimension | Demo (built and tested) | Designed (documented) |
|---|---|---|
| Tenants | 2-3 synthetic firms + PUBLIC | 50 |
| Advisors | a few hundred | 2,000 |
| Peak QPS | ~10 | 5-50 (requirements.md range) |
| Corpus | 50 docs / ~114 chunks today; EDGAR 497K + synthetic per tenant | 100k-1M chunks across tenants (1M x 1024 halfvec ~ 2 GB) |
| Rerank throughput | Voyage Tier 1: 2M TPM, ~5 QPS at 10-15 candidates x <= 400 tokens (~6k tokens/query) | request a tier upgrade before load tests (D13e) |
| Partition triggers | n/a | one tenant > 250k chunks, total > 2M chunks, or ANN p95 > 100 ms (§7.2) |

### 2.4 Quality gates (blocking)

Citation accuracy >= 0.95, faithfulness >= 0.90, cross-tenant/tier/jurisdiction leaks = 0, retrieval recall regression <= 2 points (ADR-017). Staleness: sources with `last_reviewed_at` older than 12 months are flagged, computed server-side from today's date.

### 2.5 Cost (monthly, us-central1 list prices; D13r)

| Profile | Estimate |
|---|---|
| Idle | $40-55: ALB $18.25, Cloud Armor ~$6-10 (UNVERIFIED), Cloud SQL storage + IP ~$4-6, PSC endpoint, Confluent Basic ~$0-5 (UNVERIFIED), Artifact Registry / Secrets / GCS / logs ~$5, Kong / API / workers at 0 |
| Demo month (~40 h up, ~2,000 chats) | $110-160 including LLM, evals, Valkey and Cloud SQL hours |
| Always-on `prod` | $300+ (out of budget, by design) |
| Budget | $100-200/month (Keshav) |

Unit prices (evidence-r2.md): Sonnet 5.5 $2 / $10 per MTok in/out, cache read $0.10; Haiku 5.5 $0.10 / $0.50; Batch API -50%; fallback Sonnet 4.6 $3 / $15; voyage-4 $0.06/M tokens (200M free); rerank-2.5-lite $0.05/M; Model Armor free to 2M tokens/month then $0.10/1M; Cloud SQL Enterprise 2 vCPU / 8 GiB ~$101 while running (HA ~$202); Memorystore Valkey shared-core-nano ~$23/month (~$0.03/h, only while the demo is up).

### 2.6 Other attributes

- Isolation: zero cross-tenant reads or writes; enforced by Postgres RLS, tested by the L0 leak matrix on every PR (§5.4, ADR-017).
- Cost control: per-tenant token budgets and per-tenant concurrency in FastAPI (numbers set in E4); BigQuery `maximum_bytes_billed`; budget alerts (§9).
- Operability: one developer; one Python image with three entrypoints; Terraform owns everything except the Valkey instance lifecycle, which the demo script creates and deletes (fixed instance name, outside Terraform state; stated once here and in §4.12); demo up/down is one command each.
