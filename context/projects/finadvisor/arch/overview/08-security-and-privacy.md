## 8. Security and privacy

### 8.1 OWASP LLM Top 10 (2025) mapping

Source https://genai.owasp.org/llm-top-10/ . Controls are the ones decided (ADR-009, amended in round 4 by ADR-036 and others).

| ID | Risk | Controls in v2 | Test |
|---|---|---|---|
| LLM01 | Prompt injection | Untrusted content (retrieved text, tool output) only inside JSON-encoded `tool_result` with a per-request random nonce (datamarking is an exploratory ablation arm only, on the model-visible copy); Model Armor input screen (timeout set from measured latency, fail closed); **ingest scan** (§8.6): parse-time sanitiser, pattern list, Model Armor document screening, quarantine; input cap; tools take no tenant / tier / jurisdiction / `as_of` arguments, least privilege; role policy deny by default (§8.8); no LLM-based rails on the hot path | L3 refusal and promptfoo red team (injection); #5, #21 (slice G, LLMail-wrapped chunks, ASR line) |
| LLM02 | Sensitive information disclosure | Presidio pseudonymization before embed / LLM / traces / logs; sentence-buffered output redaction; raw bytes only in bronze; RLS + single retrieval point; redacted-only events, traces (Langfuse `mask_otel_spans`), BigQuery; client sees tool name + status only; Kong `file-log` whitelist; no PII in logs (§8.7); subject rows carry a random `pseudonym_id`; private text leaves the cell only when the tenant's `llm_egress_ack` is true (§8.7) | L0 PII and leak matrix; L3; #26 |
| LLM03 | Supply chain | Lockfile installs, trivy, pip-audit, gitleaks, images by digest, pinned versions (`stack.md`), model ids from config + retirement check | CI |
| LLM04 | Data and model poisoning | Ingest from bronze with sha256, contracts and blocking quality rules (Pandera, dbt, §6.8), **ingest injection scan and quarantine** (a chunk exists only if the version passed every gate, ADR-028), parser version recorded, `silent_edit` detection, mass-delete breaker, tenant-scoped writes (a tenant cannot write PUBLIC or another tenant), worker envelope check, suitability rules validated; contextual headers (default OFF) pass PII scrub and tier rules | L0 write leak matrix; ETL tests; #5, #12, #13 |
| LLM05 | Improper output handling | React renders sanitized markdown only; deterministic citation verifier (every `[n]` in retrieved chunk ids, quote overlap); **locale-aware numeric grounding gate** per sentence (§8.6) that withholds an answer with an ungrounded figure; **licence footer** check (§8.8); server-emitted citation events with redacted excerpts; error codes not exception text | L0 citation verifier; numeric-gate property tests; #22; vitest |
| LLM06 | Excessive agency | Tools read-only except `escalate_to_compliance` (server-side licenses, persisted); **role x tool x output-field policy as data in `policy.py`, default deny** (§8.8); `chat-api` has no write grant on content tables; max 3 iterations; no write tools for content; no shell, no web | L3; role x tool matrix generated from `policy.py`; #33 |
| LLM07 | System prompt leakage | No secrets or tenant data in prompts; tenant / user / date text after the cache breakpoint; prompts versioned; assume the prompt is public | red team |
| LLM08 | Vector and embedding weaknesses | RLS on chunks including both retrieval legs; LIST partitions per tenant with no partition grants; iterative scan so filters do not silently shrink results; ACL change = metadata UPDATE by the applier; every retrieval SQL carries the `valid_range @> as_of` predicate (CI check); one embedding model per tenant read, model literal from an allow-list; PII scrub before embed; Voyage `input_type` | L0 leak matrix; L1; #19 |
| LLM09 | Misinformation | Retrieve-first with CRAG-style confidence gate ("no firm documentation"); every claim cited; citation verifier; staleness flags from today's date (for law, warnings by state: superseded, revoked, known pending); as-of check on every cited chunk; numeric gate; mixed-jurisdiction warning; degraded retrieval flagged in `meta`; judge differs from answer model | L2 faithfulness, gates; #9, #25 |
| LLM10 | Unbounded consumption | Kong rate limits (IP, session key), request-size limit, input cap, `max_tokens`, max 3 iterations, per-tenant token budget and concurrency in FastAPI, explicit timeouts, circuit breaker, BigQuery `maximum_bytes_billed`, budget alerts | load test with stub LLM |

### 8.2 Authentication and tenant discovery

1. The SPA loads at `/t/<slug>`. It calls the public `GET /v1/tenants/{slug}` (Kong IP rate limit) and receives only `{display_name, idp_tenant_id}` from `fa_tenant_lookup` (D13m). Slugs can be enumerated at the Kong IP rate; the response carries nothing else.
2. The SPA signs the user in against that Identity Platform tenant (one IdP tenant per firm; email/password now, SSO path later) and receives an ID token whose `firebase.tenant` claim names the IdP tenant (D15.3).
3. Every API call sends `Authorization: Bearer <ID token>`. Kong strips client identity headers and never trusts or sets identity.
4. `auth` verifies the token tenant-aware with firebase-admin (`tenant_mgt.auth_for_tenant(tenant_id).verify_id_token`: signature, `aud`, `iss`, `exp`, `TenantIdMismatchError`). The IdP tenant id is mapped to `tenants.id` through `fa_tenant_lookup(p_idp_tenant_id)`; the token's `sub` maps to `advisors.idp_uid`. An unknown tenant or advisor is `UNAUTHENTICATED`. The claim name is verified in the first E1 ticket.
5. `principal` loads tier, jurisdictions, licenses, role from `advisors` (60 s cache; the TTL is the revocation bound) and only then sets the transaction settings. Tokens carry identity only, never entitlements.
6. Service-to-service: Kong adds a Google ID token in `X-Serverless-Authorization` (audience = chat-api URL). Cloud Run IAM checks only that header when both are present (https://docs.cloud.google.com/run/docs/authenticating/service-to-service ), so the user `Authorization` reaches FastAPI; "reaches the app unchanged" is inferred and confirmed by an E2 smoke test. FastAPI verifies the user token again.
7. Identity Platform multi-tenancy needs billing enabled for more than 2 tenants; email/password tier free to 50k MAU (https://docs.cloud.google.com/identity-platform/docs/multi-tenancy ). IdP tenants are provisioned by an onboarding script (E1) and Terraform (E10).
8. Multiple logins (ADR-032): one advisor in several firms has one Identity Platform tenant per firm, one `advisors` row per `(tenant_id, idp_uid)` and one token per firm; there is no identity merge, and identity is never an authorization input across firms. The SPA keeps one auth instance per firm and a firm switcher (`currentUser` does not change when `tenantId` is switched). The server verifies at project level, reads `firebase.tenant` and requires it to equal the tenant in the URL and the signed `cells.json` entry; a mismatch is 403 or 421. Whether one email can exist in two tenants is UNVERIFIED and is a spike that gates the E1 identity tickets (§10); if it fails, onboarding uses per-firm email aliases.

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
| D13j | Kafka payloads on a cluster without in-cluster RBAC | Payload minimisation (ids, hashes, redacted text only), one service account + key per service, Kafka ACLs per service account, DLQ payloads redacted; per-tenant topics rejected; FCA content never enters Kafka; revisit at "real client data" |
| D13k, D15.5 | BigQuery exposure | Redacted text only; per-tenant authorized views are primary, row access policies second; `maximum_bytes_billed` on every query |
| D13l | Langfuse Cloud Hobby | Traces carry metadata, hashes, redacted text, tagged by tenant; `capture_input` / `capture_output` off on sensitive spans; `mask_otel_spans`; acceptable while there is no real client data (real public documents and private demo publisher documents are allowed, ADR-038); at "real client data" self-host Langfuse v4 or drop third-party tracing; account per cell; deletion is provider-bound (§2.7) |
| D13n | dbt or gold models bypass RLS | dbt runs as `fa_dbt`; gold = `security_invoker` views or incremental models with a tenant predicate; CI asserts RLS enabled, forced and policies present for every table in tenant schemas; `SECURITY DEFINER` functions banned except `fa_tenant_lookup` |
| D13o | PII via telemetry | OTel / DB instrumentation with SQL parameter capture off; no request bodies in logs or spans; errors carry codes |
| D16.9, D16.10 | Tokens or bodies in gateway logs or Valkey keys | Kong `file-log` whitelist (no `Authorization`, bodies or query strings); rate-limit key is `sha256(Authorization)` |
| MVP | Session-level `SET` leaking tier across pooled requests (G-19) | `set_config(..., true)` inside short transactions; no `SET ROLE`; L0 pooled-reuse test |
| MVP | Tool payloads to client (G-04) | Client receives tool name + status only |
| ADR-036 | Indirect injection in an ingested document | Ingest scan and quarantine (§8.6); chunks never written for a quarantined version; JSON-encode + nonce at query time; citation verifier and numeric gate compare against the original chunk text fetched by id |
| ADR-036 | Ungrounded number or date in an answer | Numeric grounding gate per sentence (§8.6); a failing sentence withholds the answer (`ANSWER_WITHHELD numeric_ungrounded`) with an escalate offer |
| ADR-036 | Tool or output field used by a role that should not have it | `policy.py` role x tool x output-field table, default deny; a tool without a policy row fails CI (§8.8) |
| ADR-036 | Quoting beyond the licence | `licence_footer` from `attribution_text` per licence class; a missing footer blocks release; `publisher` quote cap (§8.8) |
| K-R4-3, ADR-026 | Private publisher document leaks to another tenant, the repo or a public eval set | `private_demo`: firm tenant only (RLS), private bucket, never committed, private eval items run only where the private bucket is mounted; refused unless `llm_egress_ack` is true |
| ADR-026, ADR-029 | FCA purge needs to reach firm messages and cache rows | `purge_source('fca_api')` runs as the PUBLIC owner role; it fans out one `deletion_requests` row per firm tenant, executed under that tenant's own role; no cross-tenant role (D13a stands); FCA content never in Kafka or BigQuery |
| ADR-028 | Erased data resurrected by a late write, replay or restore | Tombstone first under the advisory lock; every sink guards with an uncached ledger read; end-of-window re-sweep; `erasure-replay` after any restore; `tombstone_violations_total` = 0 |
| ADR-029 | PII in logs | Logs carry `pseudonym_id` or `advisor_hash` only, never bodies, prompts, queries, tool payloads or exception text; `_Default` retention 7 d; Kong `file-log` whitelist |
| ADR-031 | Request served by the wrong cell | `principal` checks `home_cell` before any DB read; 421 with a cell hint; each cell holds only its tenants' rows |
| ADR-038 | Private text leaves the cell without consent | `tenants.llm_egress_ack` default false, must be true before private ingest; three named egress paths (§8.7) |

PII handling summary: Presidio pseudonymization (`en_core_web_sm`; reversible within the request only) runs before embedding, before the LLM, before traces and logs; output is redacted sentence by sentence before streaming. Presidio gives no recall guarantee (community project); the L0 PII tests and L2 evals measure it. Presidio covers EN; DE and FR PII recall is measured before any claim is made (ADR-036, §10), and until then a prompt that carries redacted DE/FR text may still contain PII (ADR-038).

### 8.6 Ingest scan, quarantine and the numeric gate (ADR-036)

Real third-party text (publisher PDFs, ESMA and FCA content) can carry hidden or injected instructions; Model Armor latency, SLA and precision are NOT FOUND, and the spotlighting result is a 2023 study on GPT-3.5 and GPT-4 without Claude (https://arxiv.org/abs/2403.14720 [PREPRINT]). No single layer is trusted.

| Layer | Control |
|---|---|
| Ingest scan (a) | Parse-time sanitiser: drops script and style, comments, hidden or off-screen text, zero-width and bidi characters, long base64 runs; records a diff count per document |
| Ingest scan (b) | Deterministic pattern list: instruction-override phrases, role markers, tool-call syntax, URLs outside an allow-list |
| Ingest scan (c) | Model Armor document screening, windowed under 65,536 tokens and 4 MB, throttled to <= 300 QPM of the shared 1,200 QPM (https://docs.cloud.google.com/model-armor/quotas); `EXECUTION_SKIPPED` fails closed into quarantine |
| Quarantine | Version `status = quarantined`, bytes under `quarantine/`, never silver; chunks are never written; operator `release` or `reject` is recorded; a compliance officer sees a summary, never raw quarantined text |
| Query time | ADR-009 unchanged plus a per-request random nonce: JSON-encode spotlighting by default; datamarking is exploratory ablation arm A-INJ-2 on the model-visible copy only. Prompt Guard 2 and InjecGuard-class classifiers are ablation arms only (Llama 4 licence, CPU latency NOT FOUND, over-defense on words like "must" and "ignore") |
| Numeric grounding gate | Deterministic, per sentence, before release. Locale-aware extraction of numbers and dates into `(Decimal, unit)`: EN `1,234.56`, DE/FR `1.234,56` and `1 234,56` (including the narrow no-break space), percent, bps, currency, ISO and long dates in EN/DE/FR. Each must appear in a cited span of that sentence's `[n]`. Rounding is allowed only to the precision the answer states; bps and % are whitelisted; identifiers (CELEX, article and rule numbers, `2014/65/EU`) and the as-of date are excluded; derived figures only from a deterministic `calc` tool whose inputs are grounded. An ungrounded number withholds the answer ("figure X not found in cited sources") with an escalate offer. No paper tests a plain regex gate, so the false-reject rate is measured (line <= 3% proposed) |
| Compliance checks | `licence_footer`; jurisdiction label per citation plus a mixed-jurisdiction warning; as-of validity; staleness by state for law texts (§8.8) |

Evidence: ADR-036; FinGround arXiv 2604.23588 [PREPRINT]; InjecGuard https://arxiv.org/abs/2410.22770 [PREPRINT]; FinRegQA-EU arXiv 2609.36856 [ABS] (judges reward citation density, so citation quality stays deterministic).

### 8.7 Data egress, residency and erasure (ADR-038, ADR-029, ADR-030)

Documented wording (ADR-038): "Data at rest (database, search index, document store, warehouse, event streams, traces) stays in the tenant's home cell. Prompt text and embedding and rerank inputs are processed by Anthropic and Voyage, which are US/global."

- Three egress paths for private text: the Anthropic prompt, Voyage embedding (ingest and query) and Voyage rerank. Each tenant has `llm_egress_ack` (default false); it must be true before private ingest, and it is true for the demo tenants. PUBLIC law is unaffected. Provider retention is outside the erasure promise; Voyage has a ZDR opt-out (region undocumented: https://docs.voyageai.com/docs/faq) and Anthropic Batch is not ZDR-eligible (https://platform.claude.com/docs/en/build-with-claude/data-residency).
- Cells do not isolate an LLM-provider outage. No EU-only processing claim is made. A Vertex EU path needs verification and a new ADR.
- Model Armor is called on its regional endpoint per cell and is not one of the three egress paths.
- Erasure promise and windows: §2.7. Physical delete on all live stores; Postgres queue; ledger replay after any restore; no per-subject KMS keys (cost per key and the effect on backups is undocumented); store settings in §5.14.
- PII in logs: none. Logs carry `pseudonym_id` or `advisor_hash`; retention 7 d.
- Text already streamed to an advisor, and messages that hold text from a later-erased document, are handled as follows: the persisted message is `refused` after an entitlement abort; message rows citing an erased document are in erasure scope through `retrieval_chunk_ids` (ADR-033).

### 8.8 Role policy, licence footers and source terms (ADR-036, ADR-026)

Role policy lives in `policy.py` as a table of role x tool x output field, default deny. A tool without a policy row fails CI; the role x tool matrix test is generated from the table.

| Role | Tools and outputs |
|---|---|
| advisor | `search_firm_kb`, `lookup_product_factsheet`, `lookup_suitability_rule`, `calc`, `escalate_to_compliance`; output fields: quote cap, `show_raw_excerpt`, internal notes off |
| compliance_officer | advisor tools plus the quarantine summary (never raw quarantined text) and full excerpts of the tenant's documents |
| tenant_admin | no LLM tools; admin is API only |

Licence footers are built from `document_versions.attribution_text` per cited `licence_class`; a missing footer blocks release (#22).

| `licence_class` | Required footer text |
|---|---|
| `esma_transformed` | "drafted using material downloaded from ESMA's website" plus a non-endorsement statement (https://www.esma.europa.eu/about-esma/legal-notice-and-data-protection) |
| `eu_consolidated_ccby` | "consolidated text, not authentic, only the OJ is authentic" plus the CC BY 4.0 indicate-changes line (https://eur-lex.europa.eu/content/legal-notice/legal-notice.html) |
| `ogl` | OGL attribution (https://legislation.github.io/data-documentation/reuse-licence.html) |
| `ogl_fca` | "(c) FCA" credit (https://handbook.fca.org.uk/footer-widget/terms-and-conditions) |
| `us_gov` | label eCFR text as an unofficial compilation, not authentic |
| `publisher` | quote cap (default 40 words) plus attribution; `private_demo` documents are firm-tenant only |

Source terms that shape the design: the FCA API terms (cl.13) let FCA revoke access and require deletion, and cl.35.3 bars crawlers (hence API only and the purge in §8.5); FINRA terms forbid bulk copy and ML use (source dropped, https://www.finra.org/terms-of-use). A legal view on publisher documents is pending (evidence-r4.md §0.3).
