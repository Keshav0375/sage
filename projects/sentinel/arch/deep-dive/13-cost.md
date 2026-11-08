> Part of [architecture](../architecture.md) · [diagram](../architecture-diagram.md)
## 13. Cost

### 13.1 Per resource

| Resource | Monthly | Covered by |
|---|---|---|
| AKS control plane | free | Free tier |
| AKS node, 1x `B2pls_v2` ARM64 | about $1-3 | billed only while started (20-80 h/month); the free `B2ats_v2` grant is unusable for AKS (system pools need at least 4 GB RAM) |
| LoadBalancer public IP | about $0 | released at teardown (Service deleted per run) |
| PostgreSQL B1MS + 32 GB | free | 12-month grant (750 h); about $12-26/month on demand afterwards |
| ACR Standard | free | 12-month grant (the grant is on the Standard meter; Basic would have billed) |
| Key Vault, Event Grid, Functions (Y1), App Service F1 | free | always free |
| Azure Managed Redis Balanced B0 | about $13 | billed while the estate is up (phase 11) |
| Terraform state storage | about $0.01 | |
| Langfuse | free | cloud free tier |
| Datadog | free | student offer |
| GitHub Actions | free | GitHub Pro, 3,000 min/month |
| Anthropic API | about $5-10 | low volume |
| OpenAI API (fallback, judge) | about $1-2 | |
| **Total** | **about $5-12/month + Redis while up; infra about $0 at idle** | |

Pause is not zero cost: stopping AKS and Postgres ends compute, but disks, storage, the LB and ACR
continue. The spending limit on the student subscription is on, so exhausting the credit pauses the
subscription rather than billing.

### 13.2 Lessons

- On a subsidised subscription, "cheaper SKU" and "free SKU" are different questions: ACR Basic
  would have cost more than the free Standard grant ([ADR-025](../decision-logs.md#adr-025)).
- The node is the meter, not the pod: scale-to-zero had to target the cluster.
- After the 12-month grant (05/2027) Postgres and ACR bill; about $20-35/month total. `destroy all`
  tears everything down when the project wraps, and the memory backup survives outside the estate.
