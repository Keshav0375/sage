# Slice E2

## Epic section (from arch/plan.md)

### E2 Gateway and edge

- **Goal.** Traffic reaches the API only through the ALB, Cloud Armor and Kong, with limits that work and SSE that streams.
- **Scope.**
  - Kong 3.9.4 DB-less config + Valkey: per-IP and per-session `rate-limiting` (`X-RL-Key = sha256(Authorization)`), `request-size-limiting`, `cors`, `correlation-id`, `opentelemetry`, `prometheus`, `file-log` audit to Cloud Logging with a BigQuery log sink (G-48; no `/internal` routes), `bot-detection`, request-transformer stripping identity headers; route paths as prefixes or `~` regexes.
  - `pre-function` for `X-Serverless-Authorization` and `X-RL-Key`; `fa-gateway` Cloud Run service (invoker check disabled on this service only, ingress internal-and-cloud-load-balancing); ALB + Cloud Armor in Terraform; private `run.app` DNS zone, Private Google Access and Direct VPC egress `private-ranges-only`.
  - `llm-egress` route with `key-auth` + `ip-restriction` if its spike passes; `kong config parse` in CI; deck / curl smoke tests; kong + valkey in compose.
- **Arch sections.** overview.md#4.1 to #4.3, overview.md#4.6, overview.md#6.5, overview.md#8.3, overview.md#10 (items 1-5, 9); ADR-011, ADR-012, ADR-023, ADR-024.
- **Dependencies.** E1.
- **Spikes first.** (1) SSE pass-through ALB to Kong to chat-api; (2) `X-Serverless-Authorization` passthrough smoke test (user `Authorization` reaches FastAPI unchanged); (3) private-DNS `run.app` egress; (4) LLM egress with `ai-proxy` `route_type: preserve`; (5) `X-RL-Key` behaviour; (6) Cloud Armor cost. Each result is an ADR (conditional ADRs where a spike fails).
- **Done when.**
  - Spike results recorded as ADRs with measurements.
  - SSE through Kong adds <= 50 ms p95 over a direct chat-api stream (measured, `response_buffering: false`).
  - The Kong config parses; a smoke test shows 429 with `Retry-After` for the IP limit and the session-key limit, 413 over the size limit, and client-supplied `X-User-Id` / `X-Tenant-Id` / `X-Serverless-Authorization` / `X-RL-Key` never reaching chat-api; no raw bearer token appears in Valkey keys or in `file-log` output.
  - Gateway audit rows reach BigQuery `gateway_audit` through the log sink with no `Authorization`, body or query string.
  - `chat-api` rejects a call without the Kong service account's ID token (or the ADR fallback is in place); Kong reaches `chat-api` over private DNS with no Cloud NAT (or the ADR fallback is in place).
  - Fixes G-02, G-11, G-14, G-46, G-48.

## Arch files to read (paths; read only the named subsections)

- context/projects/finadvisor/arch/overview/04-components-and-responsibilities.md  (sections: 4.1, 4.6)
- context/projects/finadvisor/arch/overview/06-interfaces-and-contracts.md  (sections: 6.5)
- context/projects/finadvisor/arch/overview/08-security-and-privacy.md  (sections: 8.3)
- context/projects/finadvisor/arch/overview/10-open-questions.md  (sections: 10)
- context/projects/finadvisor/arch/stack.md (versions)
- context/projects/finadvisor/arch/overview/06-interfaces-and-contracts.md §6.6 (config keys), only the keys this epic uses

## ADRs (context/projects/finadvisor/arch/decisions.md; line of heading)

- line 283: ADR-011: Kong as the edge API gateway (Keshav's decision)
- line 263: ADR-012: Edge: external ALB + Cloud Armor, same origin
- line 26: ADR-023: Gateway audit through Cloud Logging and BigQuery
- line 5: ADR-024: VPC egress mode: Direct VPC egress private-ranges-only, no Cloud NAT
