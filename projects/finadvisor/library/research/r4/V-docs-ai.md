EVIDENCE (V-docs-ai, round 4). Read 2026-11-07 via WebFetch (small-model summarizer; quotes are as returned, 125-char-class fidelity not guaranteed - re-check decisive table cells live). No page-reader leaves used.

## Q1 voyage-context-4 (ADR-035 / ADR-037 arm 2)
Confirms
- Endpoint - "POST https://api.voyageai.com/v1/contextualizedembeddings" - https://docs.voyageai.com/docs/contextualized-chunk-embeddings (read 2026-11-07)
- Current model, v3 legacy - "Voyage currently provides the following contextualized chunk embedding models:" voyage-context-4 current; voyage-context-3 under older models - same page
- Input shape - Python input type "List[List[str]]" ("Embed pre-chunked documents"); REST curl example on the page shows flat list (docs inconsistent; one inner list = one document's chunks) - same page
- 1024 available and is default - "Options: 2048, 1024 (default), 512, and 256." - matches halfvec(1024) - same page
Limits
- "The total number of chunks across all inputs must not exceed 16K."; "The total number of tokens across all inputs must not exceed 120K."; "The list must not contain more than 1,000 inputs."; per-chunk context window 32,000 - same page
- Rate: "| voyage-4-large / voyage-context-4 | 3M | 2000 |" (TPM / RPM, tier 1); tier 2 "2x Tier 1", tier 3 "3x Tier 1" - https://docs.voyageai.com/docs/rate-limits
- Price: voyage-context-4 $0.12 / 1M tokens, first 200M free - https://docs.voyageai.com/docs/pricing
Gaps: per-input token cap (separate from 120K total) NOT FOUND. Batch API supports /v1/contextualizedembeddings (from G-gapfill).

## Q2 rerankers (ADR-037 arm 3)
- Status - page lists rerank-3 and rerank-3-lite under "Voyage currently provides the following reranker models:"; rerank-2.5 / -2.5-lite are under older models "still accessible from our API" (rerank-3 marked recommended) - https://docs.voyageai.com/docs/reranker
  NOTE: this reverses G-gapfill's reading (rerank-2.5 listed as current). Docs now: rerank-3 current, rerank-2.5 older.
- Limits (same for all four) - context 32,000; "The query can contain a maximum of 8,000 tokens"; "The number of documents cannot exceed 1,000."; total "cannot exceed 600K" where total = query tokens x docs + sum(doc tokens)
- TPM, CURRENT official - "| rerank-3 / rerank-2.5 / rerank-2 / rerank-1 | 2M | 2000 |" and "| rerank-3-lite / rerank-2.5-lite / rerank-2-lite / rerank-lite-1 | 4M | 2000 |" - https://docs.voyageai.com/docs/rate-limits. So the figures are 2M (full) and 4M (lite) at tier 1; the "two different figures" in arch are likely these two; use 2M for rerank-3, 4M for lite, x2/x3 by tier.
- Price - rerank-3 $0.05, rerank-3-lite $0.02, rerank-2.5 $0.05, -lite $0.02 per 1M tokens; "The first 200 million tokens for rerank-2.5, rerank-2.5-lite, rerank-2, and rerank-2-lite are free"; rerank-3 row shows 200M free; older-models section says "we do not offer free tokens for them" - page self-conflicts on free tokens - https://docs.voyageai.com/docs/pricing
- Cost note: the 600K cap with query x docs means 100 docs x ~1K tokens + query is fine; 1000 docs of 600 tokens busts it.

## Q3 Model Armor (ADR-036 / ADR-009) - https://docs.cloud.google.com/security-command-center/docs/model-armor-overview and /key-concepts-model-armor
- GA status: overall NOT FOUND on these pages. Image screening is Preview: "Pre-GA features are available" (limited support).
- SLA: NOT FOUND. Latency figures: NOT FOUND.
- Locations: "Image screening is supported only in the us and eu multi-regions." Regional endpoints mentioned ("To access Model Armor regional endpoints from within a VPC network, you must"); URL format NOT FOUND (the regional-endpoints page lists only securitycenter.LOCATION.rep.googleapis.com; Model Armor column marks europe-west1, europe-west2, asia-southeast1 etc.; "Model Armor is not supported in this region." for me-central2). Full Model Armor location list NOT FOUND in fetched pages.
- Document screening: types PDF, CSV, plain text, Word, PowerPoint, Excel; "Supported files are limited to 4 MB in size."; files under 69 bytes rejected (InvalidDocumentInputException).
- Methods: SanitizeUserPrompt / SanitizeModelResponse exist; "Screening multiple images at a time isn't supported" (one image per request).
- Floor settings: "They define minimum requirements for all templates created at the project level" (resource-hierarchy scoped). Templates: "Model Armor templates let you configure how Model Armor screens prompts and responses."
- Filters: prompt injection/jailbreak, Sensitive Data Protection, malicious URL, Responsible AI, CSAM. Confidence: "A lower threshold identifies more events but might increase the frequency of false positives."
- Pricing: "Model Armor uses the total number of tokens in AI prompts and responses for pricing purposes and filter limit enforcement." Per-filter token limits: linked, values NOT FOUND. Price table not read (gap).

## Q4 Identity Platform multi-tenancy (ADR-032) - https://docs.cloud.google.com/identity-platform/docs/multi-tenancy
- Per-tenant users - "Each tenant has its own:" ... "Users"; "All imported users will have their tenantId set to the tenantAuth.tenantId." (managing-tenants page)
- Same email in two tenants: NOT FOUND (docs silent; implied by per-tenant user stores but not stated - needs a spike).
- Account linking across tenants: NOT FOUND. Only "Disabling account linking" listed as unsupported feature.
- createSessionCookie with tenant: NOT FOUND (feature table lists "Session cookie management", no tenant detail). Cookie doc URLs tried returned 404.
- Quota: "2 tenants/project" for instrumentless projects; billing-instrumented projects "Unlimited" - https://docs.cloud.google.com/identity-platform/quotas. Email uniqueness and SLA NOT FOUND.

## Q5 Voyage retention / residency - https://docs.voyageai.com/docs/faq
- "customers can opt-out from Voyage storing and using their data for future model training" (Voyage-hosted API endpoints only); result "zero-day retention of the data"; need "a payment method on file and be an organization Admin"; "You won't be able to opt-in again in the dashboard after you opt out." Default (training on/off) not stated.
- Data residency / region: NOT FOUND. SOC 2: NOT FOUND. DPA: NOT FOUND.
- Implication: llm_egress_ack wording may claim "zero-day retention only after the org opts out in the dashboard"; must NOT claim regional residency.

Improvements:
- Switch arm-3 default to rerank-3 (current) and treat rerank-2.5 as legacy; budget 2M TPM tier 1 (4M lite).
- Cap rerank request: query x docs + doc tokens <= 600K; chunk candidate set accordingly.
- voyage-context-4 at 1024 fits halfvec(1024); batch chunks per doc, <=1000 docs / 120K tokens per call; embed uses 3M TPM shared bucket with voyage-4-large.
- Add Model Armor feature-flag fallback: no SLA/latency published, image screening Preview; use only text/PDF (<=4MB).
- Identity Platform: spike same-email-two-tenants and createSessionCookie(tenantId) before ADR-032 is binding; keep fallback of tenant_id mapping in own DB.
Gaps: Model Armor GA label, latency, SLA, location list, endpoint URL, price table; Identity Platform email uniqueness/linking/session cookie tenant; Voyage residency/SOC2/DPA/default training; voyage-context-4 per-input cap.
