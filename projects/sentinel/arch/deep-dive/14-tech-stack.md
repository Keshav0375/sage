> Part of [architecture](../architecture.md) · [diagram](../architecture-diagram.md)
## 14. Tech stack

### 14.1 As built

| Area | Choice |
|---|---|
| Language | Python 3.12, Poetry with `poetry.lock` |
| Agents | OpenAI Agents SDK `openai-agents` 0.6.4, LiteLLM models |
| LLMs | Anthropic `claude-sonnet-4-6`, `claude-haiku-4-5` (default); OpenAI `gpt-4o`, `gpt-4o-mini` (fallback); judge `gpt-4.1` / `claude-opus-4-1` |
| API | FastAPI, uvicorn; `pyjwt[crypto]` for Entra JWKS |
| Data | Azure PostgreSQL Flexible Server 16, pgvector, asyncpg, Alembic |
| Embeddings | `all-MiniLM-L6-v2` (384), sentence-transformers, torch CPU, baked into the image |
| Cache / hot state | Azure Managed Redis Balanced B0 (Entra auth) with an in-process fallback |
| Azure SDK | `azure-identity`, `azure-keyvault-secrets` |
| Tracing / eval | Langfuse v3 (traces, prompts, scores, datasets) |
| Signal | Datadog (US5): events, logs, Synthetics, monitors |
| Notifications | Microsoft Teams (GHA only) |
| Logging | structlog |
| Container | multi-stage Dockerfile, `python:3.12-slim` by digest, `linux/arm64` |
| Hosting | AKS Free tier, 1x `Standard_B2pls_v2` ARM64, workload identity, Cilium |
| Target app | FastAPI + gunicorn on App Service F1, zip deploy via `az webapp deploy` |
| Glue | Event Grid custom topic, Azure Functions (Python, Y1): bridge and rotator |
| IaC | Terraform >= 1.9, `azurerm ~> 4.0` (pinned 4.81.0 at the time), `azuread ~> 3.0` |
| CI/CD | GitHub Actions, composite actions pinned by SHA, native arm64 runners, CI runner image in ACR |
| Quality gate | `scripts/quality_gate.py`: ruff, pyright, pytest, pip-audit, gitleaks (backend); terraform fmt/validate, tflint, shellcheck, tfsec, py unittest (infra); ruff, actionlint, yamllint, pytest (deployment) |
| Dashboard | React 18, TypeScript, Vite, Tailwind, Radix UI, TanStack Table/Virtual, Recharts, date-fns, pnpm, Vitest, Playwright, Lighthouse |
| Control plane | Claude Code agents and skills (Opus decides, Sonnet builds, Haiku verifies), Python helper scripts, a GitHub project board mirror |
