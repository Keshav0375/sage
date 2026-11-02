## 8. Security and privacy

### 8.1 OWASP LLM Top 10 (2025) mapping

Source https://genai.owasp.org/llm-top-10/ . Controls are the ones decided (ADR-009 and others).

| ID | Risk | Controls in v2 | Test |
|---|---|---|---|
| LLM01 | Prompt injection | Untrusted content (retrieved text, tool output) only inside JSON-encoded `tool_result`; Model Armor input screen (500 ms, fail closed); input cap; tools take no tenant / tier / jurisdiction arguments, least privilege; no LLM-based rails on the hot path | L3 refusal and promptfoo red team (injection) |
| LLM02 | Sensitive information disclosure | Presidio pseudonymization before embed / LLM / traces / logs; sentence-buffered output redaction; raw bytes only in bronze; RLS + single retrieval point; redacted-only events, traces (Langfuse `mask_otel_spans`), BigQuery; client sees tool name + status only; Kong `file-log` whitelist | L0 PII and leak matrix; L3 |
| LLM03 | Supply chain | Lockfile installs, trivy, pip-audit, gitleaks, images by digest, pinned versions (`stack.md`), model ids from config + retirement check | CI |
| LLM04 | Data and model poisoning | Ingest from bronze with sha256, Pandera validation and rejects, parser version recorded, tenant-scoped writes (a tenant cannot write PUBLIC or another tenant), worker envelope check, suitability rules validated; contextual headers pass PII scrub and tier rules | L0 write leak matrix; ETL tests |
| LLM05 | Improper output handling | React renders sanitized markdown only; deterministic citation verifier (every `[n]` in retrieved chunk ids, quote overlap); server-emitted citation events with redacted excerpts; error codes not exception text | L0 citation verifier; vitest |
| LLM06 | Excessive agency | Four tools, read-only except `escalate_to_compliance` (server-side licenses, persisted); `chat-api` has no write grant on content tables; max 3 iterations; no write tools for content; no shell, no web | L3 |
| LLM07 | System prompt leakage | No secrets or tenant data in prompts; tenant / user / date text after the cache breakpoint; prompts versioned; assume the prompt is public | red team |
| LLM08 | Vector and embedding weaknesses | RLS on chunks including both retrieval legs; LIST partitions per tenant with no partition grants; iterative scan so filters do not silently shrink results; ACL change = metadata UPDATE by the applier; PII scrub before embed; Voyage `input_type` | L0 leak matrix; L1 |
| LLM09 | Misinformation | Retrieve-first with CRAG-style confidence gate ("no firm documentation"); every claim cited; citation verifier; staleness flags from today's date; degraded retrieval flagged in `meta`; judge differs from answer model | L2 faithfulness, gates |
| LLM10 | Unbounded consumption | Kong rate limits (IP, session key), request-size limit, input cap, `max_tokens`, max 3 iterations, per-tenant token budget and concurrency in FastAPI, explicit timeouts, circuit breaker, BigQuery `maximum_bytes_billed`, budget alerts | load test with stub LLM |

### 8.2 Authentication and tenant discovery

1. The SPA loads at `/t/<slug>`. It calls the public `GET /v1/tenants/{slug}` (Kong IP rate limit) and receives only `{display_name, idp_tenant_id}` from `fa_tenant_lookup` (D13m). Slugs can be enumerated at the Kong IP rate; the response carries nothing else.
2. The SPA signs the user in against that Identity Platform tenant (one IdP tenant per firm; email/password now, SSO path later) and receives an ID token whose `firebase.tenant` claim names the IdP tenant (D15.3).
3. Every API call sends `Authorization: Bearer <ID token>`. Kong strips client identity headers and never trusts or sets identity.
4. `auth` verifies the token tenant-aware with firebase-admin (`tenant_mgt.auth_for_tenant(tenant_id).verify_id_token`: signature, `aud`, `iss`, `exp`, `TenantIdMismatchError`). The IdP tenant id is mapped to `tenants.id` through `fa_tenant_lookup(p_idp_tenant_id)`; the token's `sub` maps to `advisors.idp_uid`. An unknown tenant or advisor is `UNAUTHENTICATED`. The claim name is verified in the first E1 ticket.
5. `principal` loads tier, jurisdictions, licenses, role from `advisors` (60 s cache; the TTL is the revocation bound) and only then sets the transaction settings. Tokens carry identity only, never entitlements.
6. Service-to-service: Kong adds a Google ID token in `X-Serverless-Authorization` (audience = chat-api URL). Cloud Run IAM checks only that header when both are present (https://docs.cloud.google.com/run/docs/authenticating/service-to-service ), so the user `Authorization` reaches FastAPI; "reaches the app unchanged" is inferred and confirmed by an E2 smoke test. FastAPI verifies the user token again.
7. Identity Platform multi-tenancy needs billing enabled for more than 2 tenants; email/password tier free to 50k MAU (https://docs.cloud.google.com/identity-platform/docs/multi-tenancy ). IdP tenants are provisioned by an onboarding script (E1) and Terraform (E10).

### 8.3 Network

| Surface | Control |
|---|---|
| Internet | Only the external ALB with Cloud Armor (DDoS, WAF, geo). No `allUsers` binding on any service |
| `fa-gateway` | Cloud Run ingress internal-and-cloud-load-balancing; invoker check disabled (the only service where it is); admin API off; status listener only. E10 checks the org policy `constraints/run.managed.requireInvokerIam` |
| `chat-api` | Cloud Run ingress internal; `run.invoker` only for the Kong service account (via `X-Serverless-Authorization`) |
| Cloud SQL | Private IP via PSC; no public IPv4 (fixes G-26) |
| Cloud Run egress | Direct VPC egress `private-ranges-only` on all services and jobs (public SaaS APIs go out directly; no Cloud NAT); Private Google Access on the subnet; Cloud DNS private zone mapping `run.app` to `private.googleapis.com` so Kong reaches `chat-api` through the VPC (ADR-024). Startup probe on Cloud Run |
| Service identity | One service account per service (gateway, chat-api, worker, each job), least privilege; no project-wide secretAccessor (G-50) |
| Kafka / Schema Registry | TLS; one service account and API key per service; Kafka ACLs per service account (no RBAC) |
| Kong egress route | `key-auth` (consumer `chat-api`) + `ip-restriction` to the VPC range |
| CI to GCP | Workload Identity Federation, no JSON keys |

### 8.4 Secrets

Secret Manager holds every secret (DB password per role, Kafka and Schema Registry keys per service, Anthropic, Voyage and Langfuse keys, the Kong egress `key-auth` key). Mounted per service account. Terraform never stores secret values in state in plaintext (G-27). The Settings class has no secret defaults and fails boot on a missing value (G-25). Gitleaks runs in CI. The Anthropic key is held by Kong when the egress route is used.

### 8.5 Leak-path controls

| Ref | Leak path | Control |
|---|---|---|
| D13a | Write into another tenant or into PUBLIC; FK existence probes | INSERT / UPDATE / DELETE policies own-tenant only, never PUBLIC; only `fa_etl_public` writes PUBLIC; `fa_app` has no write on content tables; composite FKs; L0 matrix tests writes as well as reads |
| D16.3 | Direct access to a partition around the parent's policies | Partitions carry no grants; startup and CI assert it; L0 tests direct partition SELECT / INSERT as `fa_app` / `fa_worker` give permission denied |
| D16.4 | Advisor raises their own tier or role | `advisors` UPDATE only when `app.role = 'tenant_admin'`; L0 test |
| D16.6 | Cross-tenant or PUBLIC event processed by a worker | Pipeline consumers reject `envelope.tenant_id` ≠ key or tenant = PUBLIC to `dlq.v1` |
| D13i | Cached answer served across tenants, tiers or after ACL change | `answer_cache` has RLS + FORCE; key includes tenant, tier, jurisdiction set, corpus and ACL versions, entitlement version, prompt version, model, normalized redacted question; hit re-runs the citation verifier and staleness; purged by the applier on ACL change and delete; exact match only; turns that called a side-effect tool are not cached |
| D13j | Kafka payloads on a cluster without in-cluster RBAC | Payload minimisation (ids, hashes, redacted text only), one service account + key per service, Kafka ACLs per service account, DLQ payloads redacted; per-tenant topics rejected; revisit at "real firm data" |
| D13k, D15.5 | BigQuery exposure | Redacted text only; per-tenant authorized views are primary, row access policies second; `maximum_bytes_billed` on every query |
| D13l | Langfuse Cloud Hobby | Traces carry metadata, hashes, redacted text, tagged by tenant; `capture_input` / `capture_output` off on sensitive spans; `mask_otel_spans`; acceptable only for synthetic data; at "real firm data" self-host Langfuse v4 or drop third-party tracing |
| D13n | dbt or gold models bypass RLS | dbt runs as `fa_dbt`; gold = `security_invoker` views or incremental models with a tenant predicate; CI asserts RLS enabled, forced and policies present for every table in tenant schemas; `SECURITY DEFINER` functions banned except `fa_tenant_lookup` |
| D13o | PII via telemetry | OTel / DB instrumentation with SQL parameter capture off; no request bodies in logs or spans; errors carry codes |
| D16.9, D16.10 | Tokens or bodies in gateway logs or Valkey keys | Kong `file-log` whitelist (no `Authorization`, bodies or query strings); rate-limit key is `sha256(Authorization)` |
| MVP | Session-level `SET` leaking tier across pooled requests (G-19) | `set_config(..., true)` inside short transactions; no `SET ROLE`; L0 pooled-reuse test |
| MVP | Tool payloads to client (G-04) | Client receives tool name + status only |

PII handling summary: Presidio pseudonymization (`en_core_web_sm`; reversible within the request only) runs before embedding, before the LLM, before traces and logs; output is redacted sentence by sentence before streaming. Presidio gives no recall guarantee (community project); the L0 PII tests and L2 evals measure it.
