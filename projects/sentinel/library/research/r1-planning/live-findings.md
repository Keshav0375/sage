# r1: What Azure and the stack taught live

Research note for sentinel. Facts the design could not have known on paper; each one changed the
architecture. Source: `sentinel-brain/architecture/decisions.md` and the phase reports.

| Date | Finding | Consequence |
|---|---|---|
| 2026-08-15 | The subscription is Azure for Students inside a university tenant: Owner on the subscription, no directory write rights; app registration denied by policy | identity plane on managed identities; two tenants ([ADR-021](../../../arch/decision-logs.md#adr-021), [ADR-022](../../../arch/decision-logs.md#adr-022)) |
| 2026-08-15 | Built-in Contributor cannot create role assignments; phase 1 passed only because it applied locally as Owner | "a phase can be fully green and still not have exercised the thing it built"; CI identities redesigned |
| 2026-08-16 | A soft-deleted Key Vault lives at subscription scope; CI's purge returned 403, silently swallowed by the script | destroy redesigned twice ([ADR-024](../../../arch/decision-logs.md#adr-024), [ADR-028](../../../arch/decision-logs.md#adr-028)) |
| 2026-08-16 | The student offer's 12-month grant covers Postgres B1MS and ACR **Standard**; Basic would have billed | ACR Standard ([ADR-025](../../../arch/decision-logs.md#adr-025)) |
| 2026-08-23 | The free `B2ats_v2` fails the AKS system-pool RAM floor; `B2s` not allowed in the region; every allowed small SKU is ARM64; a system pool cannot scale below 1 node | `B2pls_v2` ARM64, `aks stop/start`, arm64 images ([ADR-026](../../../arch/decision-logs.md#adr-026)) |
| 2026-08-23 | Y1 and F1 Linux plans cannot share a resource group | separate Functions resource group |
| 2026-08-23 | New Entra tenants reject bare `api://name` identifier URIs | tenant-qualified identifier; audience parameterised |
| 2026-08-23 | A B2B guest invitation must be redeemed interactively before CLI tokens work; an earlier scripted check was a false positive | "the provider's real request is the only proof" |
| 2026-08-23 | Event Grid batch defaults and Postgres `authentication.tenant_id` are server-populated | declare them or live with a perpetual diff; plans now run with zero warnings |
| 2026-08-23 | `terraform plan` works against a stopped AKS cluster but fails (400) against a stopped Postgres | preflight checks Postgres is awake |
| 2026-08-24 | `workflow_dispatch` accepts at most 10 inputs; the stack has about 40 knobs | form for intent, YAML config for detail |
| 2026-08-24 | The regional quota is 6 vCPU; one AKS cluster per deployment stops at three | one cluster, a namespace per deployment |
| 2026-08-24 | GitHub never mints an `environment:X` subject for a `pull_request` event | PR-unreachable deploy identity by construction |
| 2026-09-13 | Destroying the Postgres Entra admin concurrently with the database it owns deadlocks (`2BP01`), hangs 30 min and leaves Postgres billing | destroy ordering fixed (infra PR #14) |
| 2026-09-13 | An inline `run:` block hung actionlint (550 s timeout); extracted to a script it took 0.5 s | scripts, not inline blocks |
| 2026-10-05 | The Datadog org is on US5; Datadog template variables cannot produce the ISO-8601 `eventTime` Event Grid's default schema needs | `DD_SITE` everywhere; a flat webhook body |
| 2026-10-07 | 5-minute synthetics cold-started the F1 app all day, hit the 60 CPU-min quota (`QuotaExceeded`), and the next deploy got a Kudu 403 | synthetics every 30 min ([ADR-031](../../../arch/decision-logs.md#adr-031)) |
| 2026-10-07 | About half the original scenario faults could not produce their label on F1 with GET-only synthetics | deterministic catalog |
| 2026-10-12 | Langfuse v3 trace ids are W3C hex; `str(uuid)` is invalid; a keyless client raises on `get_prompt` | `incident_id.hex`; mandatory file fallback |
| 2026-10-15 | The openai-agents default exporter uploads full spans (LLM inputs and outputs with tool and log data) to OpenAI whenever an OpenAI key is set | exporter removed; processors set once |
| 2026-10-19 | Entra v2 access tokens carry `aud` = the client-id GUID, not the identifier URI | audience is a list, GUID first |
| 2026-10-24 | litellm caps filelock `<4.0`, blocking 13 CVE fixes | dated pip-audit exception ([ADR-040](../../../arch/decision-logs.md#adr-040)) |
