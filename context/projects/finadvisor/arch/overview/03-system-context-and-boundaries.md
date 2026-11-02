## 3. System context and boundaries

```mermaid
flowchart LR
    adv["Advisor (browser)"]
    tadm["Tenant admin (browser)"]
    op["Operator (Keshav)"]
    subgraph sys["FinAdvisor v2 (GCP project, us-central1)"]
        fa["FinAdvisor platform: edge, chat-api, workers, jobs, data stores"]
    end
    idp["Identity Platform"]
    ant["Anthropic API"]
    voy["Voyage AI"]
    marm["Model Armor"]
    lf["Langfuse Cloud"]
    cc["Confluent Cloud Kafka + Schema Registry"]
    edgar["SEC EDGAR (public source)"]
    gh["GitHub Actions"]
    adv -->|"HTTPS SPA + /v1 SSE"| fa
    tadm -->|"HTTPS /v1/admin"| fa
    op -->|"make demo-up / demo-down, Terraform"| fa
    fa -->|"verify ID tokens (JWKS)"| idp
    fa -->|"Messages API, Batch API"| ant
    fa -->|"embeddings, rerank"| voy
    fa -->|"screen input"| marm
    fa -->|"scrubbed traces, datasets"| lf
    fa -->|"Kafka protocol, Schema Registry REST"| cc
    fa -->|"HTTPS fetch, declared User-Agent, <= 10 req/s"| edgar
    gh -->|"WIF deploy, eval gate"| fa
```

Boundaries:
- Users reach the system only through the external ALB (`/*` SPA, `/v1/*` API). Nothing else is internet-facing; Cloud Run services use ingress internal-and-cloud-load-balancing or internal.
- The tenant boundary is inside the database (RLS, §5.4), not at the network. All tenants share one deployment.
- Trust: browsers, SaaS responses, retrieved documents and tool outputs are untrusted. Identity comes only from a verified ID token (sub + IdP tenant); entitlements come from the DB.
- Data classification: synthetic data only. Redacted text may leave to Anthropic, Voyage, Langfuse, Confluent, BigQuery; raw documents leave only to GCS bronze.
- SEC EDGAR: at most 10 requests/s, declared User-Agent, nightly index about 10 pm ET (evidence-r2.md).
