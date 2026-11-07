EVIDENCE — Track C (multi-region, residency, multiple logins), research round 4
Read 2026-11-01/02 via WebFetch (page summarizer, not raw page). Quotes are the summarizer's quotes of the page text. No page-reader leaves were spawned; pages were read directly. Pricing pages (Cloud SQL, Cloud Run, BigQuery, GCS) returned truncated content, so ALL GCP unit prices are UNVERIFIED and are not filled from memory.

## Confirms
- Cloud SQL has the three target regions — "You can create a Cloud SQL instance in the following regions:" europe-west2 London, europe-west3 Frankfurt, us-central1 Iowa — https://docs.cloud.google.com/sql/docs/postgres/locations (Last updated 2026-10-26, read 2026-11-02)
- Cloud SQL cross-region read replicas exist and can be promoted manually — "cross-region read replicas (replicas created in a different region from that of the primary)"; "Promoting a replica is done manually and intentionally." — https://docs.cloud.google.com/sql/docs/postgres/replication/cross-region-replicas (2026-10-26)
- DR replica and switchover are tied to Enterprise Plus — "If you are using Cloud SQL Enterprise Plus edition" ... "designate a cross-region read replica as a disaster recovery replica (DR replica)"; "you can perform a switchover" — same URL. Replication is async: "some recent transactions that were committed to the primary may be lost". Whether plain cross-region read replicas work on Enterprise edition: page silent (UNVERIFIED).
- BigQuery dataset location is fixed and cross-location queries fail — "After you create the dataset, the location cannot be changed."; "BigQuery returns an error if the specified location does not match the location of the datasets in the request."; "This is also true for JOIN statements with tables in both a region and a multi-region." — https://docs.cloud.google.com/bigquery/docs/locations (2026-10-27)
- BigQuery EU multi-region excludes London — EU "not stored in the europe-west2 (London) or europe-west6 (Zürich) data centers" (stored in europe-west1 or europe-west4). europe-west2 London and europe-west3 Frankfurt are single regions. "Multi-region locations ... don't provide regional redundancy." Cross-region copy procedure: not on this page (UNVERIFIED). Cross-region redundancy points to managed disaster recovery.
- GCS location types — "A region is a specific geographic place, such as Iowa (US-CENTRAL1)."; "A dual-region is a specific pair of regions, such as Tokyo and Osaka (ASIA1)."; "A multi-region is a large geographic area..." Dual-region objects "are replicated to each region that makes up the dual-region." — https://docs.cloud.google.com/storage/docs/locations (2026-10-30). Note: page says "You can relocate a bucket after it's created," only with Storage Intelligence configured (this contradicts the common belief that location is immutable). Predefined dual-regions that pair London with Frankfurt: UNVERIFIED (page not read for the list).
- Confluent Basic regions on GCP — us-central1: Basic, Standard, Enterprise, Dedicated; europe-west2 (London): Basic, Standard, Enterprise, Dedicated; europe-west3 (Frankfurt): Basic, Standard, Dedicated (no Enterprise) — https://docs.confluent.io/cloud/current/clusters/regions.html (read 2026-11-02; page date not shown by summarizer)
- Global external ALB supports several serverless NEGs, one per region — "can have several serverless NEGs attached to it"; "only one serverless NEG per region"; "the load balancer sends traffic to the NEG in the closest region to minimize request latency." Needs Premium Network Service Tier. "URL maps are used by Application Load Balancers to set up URL-based routing." Routing is by host or path (header routing not confirmed on this page: UNVERIFIED). — https://docs.cloud.google.com/load-balancing/docs/negs/serverless-neg-concepts (read 2026-11-02, undated)
- Cloud Run multi-region pattern — "Because Cloud Run services deploy into individual regions, you must deploy your service to multiple regions."; one serverless NEG per regional service behind one global external ALB with one anycast IP — https://docs.cloud.google.com/run/docs/multiple-regions (undated)
- Identity Platform tenants are user silos — "Using tenants, you can create unique silos of users and configurations within a single Identity Platform project."; each tenant has its own users and IdPs — https://docs.cloud.google.com/identity-platform/docs/multi-tenancy (2026-10-26)
- Tenant switch in one browser — "To use a single auth instance, modify the tenantId property whenever you want to switch between tenants."; "`tenantId` is not persisted on page reloads."; "if you switch tenantId on the auth instance later, the currentUser property will not change;" or "create a new auth instance for each tenant" — https://docs.cloud.google.com/identity-platform/docs/multi-tenancy-authentication (undated)
- Token verification with tenant — "If the tenant ID is unknown, first verify the token at the project level to extract the tenant ID."; firebase.tenant mismatch raises "auth/mismatching-tenant-id" — https://docs.cloud.google.com/identity-platform/docs/multi-tenancy-managing-tenants (undated). This is the vendor pattern for tenant discovery from a token (verify at project level, then tenant-aware verify).
- Langfuse Cloud regions — US Oregon (AWS us-west-2), EU Ireland (AWS eu-west-1), HIPAA Oregon, plus Japan; "All data, user accounts, and infrastructure are completely separated between the regions." — https://langfuse.com/security/data-regions (undated, read 2026-11-02)
- Anthropic inference geo — "`global` Default. Inference may run in any available geography"; "`us` Inference runs only in US-based infrastructure." Workspace geo: "Currently, "us" is the only available workspace geo." and cannot be changed after creation — https://platform.claude.com/docs/en/build-with-claude/data-residency (read 2026-11-02)
- Confluent Basic limits and pricing — "Maximum capacity is 50 eCKU, with a minimum of 1"; ingress 250 MBps, egress 750 MBps; 1,500 partitions; 99.5% SLA tier only — https://docs.confluent.io/cloud/current/clusters/cluster-types.html ("Last updated: Oct 30, 2026"). Pricing: Basic "First eCKU free, then $0.14" per eCKU-hour; data in/out "$0.05"/GB; storage "$0.08"/GB-month; "$0/Month" estimated start — https://confluent.io/confluent-cloud/pricing/ (read 2026-11-02)

## Contradicts
- GCS location is NOT strictly immutable per current docs — see GCS bullet above (relocation possible with Storage Intelligence). Do not design on "bucket location can never change".
- Anthropic has NO EU inference or EU workspace option on the first-party API: only "global" and "us" inference geo, and workspace geo "us" only. A UK/EU residency promise cannot be met by the Claude API alone (see Limits).
- Langfuse: no cross-region org. Prior assumption that one org could span EU and US is not supported; accounts are separate per region.

## Limits
- Confluent cluster linking — destination must be Dedicated or Enterprise: "Cluster links can only be created with destination clusters that are Dedicated or Enterprise"; Basic can be a source of destination-initiated links only ("Basic and Standard clusters can be source of destination-initiated links"); "A cluster can have at most 10 cluster links targeting it as the destination." — https://docs.confluent.io/cloud/current/multi-cloud/cluster-linking/index.html (read 2026-11-02). Cross-region Kafka replication from Basic therefore needs an Enterprise/Dedicated destination (Enterprise starting cost "$895/Month" at 70% utilization per pricing page; not available in europe-west3). Practical: keep Kafka regional per cell, no cluster linking.
- Identity Platform quota — "Tenants per project": "Instrumentless: 2 tenants/project", "Billing instrument: Unlimited"; "There is no limit on the number of identity providers allowed per project or tenant." — https://docs.cloud.google.com/identity-platform/quotas (read 2026-11-02). A billing-enabled project is needed for more than 2 tenants.
- Identity Platform tenant limitations — tenants don't support "Disabling account linking" or "Adding a blocking function specific to a given tenant." — multi-tenancy page.
- Cloud Run multi-region caveats — "The base architecture "does not automatically route requests to a different region" when a regional service fails."; "a client cannot know in advance which regional service a request will be routed to" (use custom audiences for authenticated services); minimum instances "applies in each region"; up to 30 minutes for LB to serve — multiple-regions page. Closest-region routing is automatic: it is latency-based, so tenant pinning to a region must be done by URL map or by the app (redirect/regional host names), NOT by the default NEG choice.
- Cloud Armor — global backend/edge policies attach to global external ALB; regional policies to regional ALBs. Page silent on one policy across backend services in several regions and on pricing (UNVERIFIED) — https://docs.cloud.google.com/armor/docs/security-policy-overview
- Shared-core Cloud SQL — "The db-f1-micro and db-g1-small machine types aren't included in the Cloud SQL SLA." "Don't use them for production instances." HA with shared-core: page silent (UNVERIFIED) — https://docs.cloud.google.com/sql/docs/postgres/instance-settings
- Anthropic US-only inference priced "1.1x the standard rate"; "Rate limits are shared across all geos."; `inference_geo` supported on "Claude 4.6 and later models"; not applicable on Bedrock or Google-managed Claude on Vertex ("the inference region is determined by the endpoint URL or inference profile").

## Vendor recommends
- Cloud Run: deploy per region, one NEG each, global external ALB; for failover use Cloud Run health and outlier detection (page links, not read).
- Identity Platform: verify token at project level first when tenant is unknown, then tenant-aware client for revocation.
- Confluent: "To obtain a higher uptime SLA, you can upgrade from Basic to a Standard cluster at any time."

## Changes
- Anthropic data residency doc now (2026-11) lists models including Sonnet 5.5, with `inference_geo` and Admin API `allowed_inference_geos` / `default_inference_geo`; legacy org-level opt-out migrated. Status "stable".
- Docs moved: cloud.google.com/<svc>/docs now 301-redirects to docs.cloud.google.com (links in the repo should be updated).

## Q3 answers (Identity Platform multiple logins)
- Same email in several tenants: the official pages read are SILENT. UNVERIFIED. Evidence only supports that each tenant has its own user set ("unique silos of users"). Needs a 5-minute live test (create two tenants, sign up same email in both) before design relies on it.
- Tenant-scoped ID token: `user.tenantId` is set after tenant sign-in; verification expects `firebase.tenant` to equal the tenant ID. Session cookies per tenant: UNVERIFIED (only listed as "Session cookie management" in Admin SDK feature table, no detail).
- SAML per tenant: confirmed ("instantiate a SAMLAuthProvider instance with the provider ID"). OIDC per tenant: listed as supported sign-in method for tenants; setup detail UNVERIFIED.
- Tenant switching in one browser: confirmed above; currentUser does not change on switching tenantId, so use one auth instance per tenant for two simultaneous logins; tenantId does not persist across reload (app must store it).
- Token verification across regions: tokens are signed by the project; any region's service can verify them at project level (same public keys) — this follows from the project-level verification statement but cross-region claim is not stated in docs: UNVERIFIED.

## Q1 gaps
- Identity Platform residency: no dedicated page found; search found only "every app in a Google Cloud project shares a user database." (https://docs.cloud.google.com/identity-platform/docs/concepts-manage-users). cloud.google.com/terms/data-residency fetch returned truncated content; whether Identity Platform is listed is UNVERIFIED. Treat identity as global/not residency-controllable until proven.
- Voyage data location / Marketplace / Vertex: docs.voyageai.com FAQ and embeddings pages are SILENT on location and regions. Only: "customers can opt-out from Voyage storing and using their data ... so that there is a zero-day retention of the data." (https://docs.voyageai.com/docs/faq). Region and Marketplace options UNVERIFIED (vendor says contact contact@voyageai.com).
- Claude on Vertex regions: Vertex pages fetched did not contain the regions table. Anthropic doc says Google-managed Claude on Vertex determines region by endpoint, and Anthropic-managed Claude on Google Cloud has workspace geo "us" and `inference_geo` "us"/"global". EU regional Vertex endpoints UNVERIFIED.
- Cloud SQL per-region prices UNVERIFIED (pricing page truncated, twice). Cloud Run tier of europe-west2/3 UNVERIFIED. BigQuery and GCS unit prices UNVERIFIED.

## Q4 cost of a real second region (delta per month)
Assumptions: demo-on-demand, idle most of the month, one cell identical to the first; Cloud Run min instances 0; no traffic to speak of; Cloud SQL smallest non-HA Enterprise instance. All GCP unit prices must be taken from the calculator: https://cloud.google.com/products/calculator

| Item | Delta assumption | Verified figure | Pricing link |
|---|---|---|---|
| Cloud SQL smallest instance, non-HA (second region) | always-on instance + storage (stop it when idle to pay storage only: UNVERIFIED behaviour) | UNVERIFIED | https://cloud.google.com/sql/pricing |
| Cloud SQL HA | roughly doubles instance cost (multiplier not read: UNVERIFIED) | UNVERIFIED | same |
| Cloud SQL cross-region replica for DR | extra instance; DR replica needs Enterprise Plus (more expensive tier) | UNVERIFIED | same |
| Cloud Run, min instances 0 | request-based, no idle charge beyond free tier (idle price when min>0 reduced: UNVERIFIED) | UNVERIFIED | https://cloud.google.com/run/pricing |
| Confluent Basic cluster | "First eCKU free, then $0.14" per eCKU-hour; $0.05/GB in/out; $0.08/GB-month storage; "$0/Month" estimated start | $0 base at idle, plus data and storage | https://confluent.io/confluent-cloud/pricing/ |
| BigQuery dataset | empty dataset has no fixed charge; pay storage and queries | UNVERIFIED | https://cloud.google.com/bigquery/pricing |
| GCS bucket | storage per GB-month and operations only | UNVERIFIED | https://cloud.google.com/storage/pricing |
| Global external ALB | already global; a second region adds a NEG and backend service, not a forwarding rule (per-rule/LCU pricing not read: UNVERIFIED); an additional forwarding rule (e.g. HTTP redirect) "incur[s] charges" | UNVERIFIED | https://cloud.google.com/vpc/network-pricing |
| Cloud Armor | one policy attaches to the global backend; extra per-policy/rule fee not read | UNVERIFIED | https://cloud.google.com/armor/pricing |
| Langfuse Cloud | separate account per region (no cross-region org) | UNVERIFIED (plan price not read) | https://langfuse.com/pricing |

Main cost driver: Cloud SQL (always-on). The Confluent Basic cluster is near zero at idle, which is a point for the two-cell plan. Total delta cannot be stated as a number from verified docs; fill the SQL, Cloud Run, BQ and GCS rows from the calculator.

## Improvements
- Keep D-R4-1 (design two cells, deploy one): docs show nothing in Basic Kafka that blocks a second cell, but cross-region cluster linking is impossible from/to Basic as destination, so design each cell with its own Kafka and no cross-cell stream.
- Do not promise EU/UK-only LLM inference: Claude API offers `global` or `us` only and workspace geo `us` only. Either state that prompts go to US/global inference in the privacy notice, or evaluate Claude on Vertex (Google-managed) with a regional endpoint (UNVERIFIED regions).
- Use host-based routing (e.g. firm.<region>.example) in the URL map to pin tenant to region; default ALB routing is closest-region only.
- Keep BigQuery per-cell in a single region dataset (europe-west2 London if UK residency matters; EU multi-region does NOT include London).
- Identity Platform: run the same-email-in-two-tenants test; project is shared across regions, so treat identity as the global slice and say so explicitly.
- Billing-enabled project required for more than 2 tenants.

## Gaps
- Same email in multiple tenants; session cookies per tenant; Identity Platform data location.
- All unit prices (Cloud SQL, Cloud Run, BQ, GCS, ALB, Armor, Langfuse).
- Voyage region/Marketplace; Claude on Vertex EU regions; Cloud SQL cross-region replica on Enterprise (non-Plus) edition; Cloud Run multi-region GA/preview status; Cloud Armor cross-region attachment.
- URL-map header routing on global external ALB (page shows host/path only).
