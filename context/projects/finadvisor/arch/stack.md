# finadvisor: tech stack

As built at commit d6c2bd3 (mapped 2026-11-01). Versions are what the repo pins; "floating" means a lower bound or a moving tag, so the resolved version changes with each build. Where `poetry.lock` resolves a version it is shown as "lock x.y.z" but the backend Dockerfile ignores the lock (`backend/Dockerfile:6-8`), so the lock is not what a container build installs. No target stack is decided yet; the Why column points to the as-built description.

| Layer | Technology | Version | Why (ADR) | Official docs |
|---|---|---|---|---|
| Language (backend) | Python | `>=3.12,<3.14` (`backend/pyproject.toml:8`); Docker `python:3.12-slim` (`backend/Dockerfile:1`); CI 3.12 | as built, see MVP.md §3, §8 | https://docs.python.org/3.12/ |
| Backend framework | FastAPI | floating `>=0.115.0` (lock 0.136.1) | as built, see MVP.md §3.2 | https://fastapi.tiangolo.com/ |
| ASGI server | uvicorn[standard] | floating `>=0.30.0` (lock 0.47.0); one process, no workers flag | as built, see MVP.md §8a | https://www.uvicorn.org/ |
| SSE | sse-starlette | floating `>=2.0.0` (lock 3.4.4) | as built, see MVP.md §4.a, §6.2 | https://github.com/sysid/sse-starlette |
| Settings | pydantic-settings | floating `>=2.0.0` (lock 2.14.1) | as built, see MVP.md §7 | https://docs.pydantic.dev/latest/concepts/pydantic_settings/ |
| ORM / DB access | SQLAlchemy (asyncio) | floating `>=2.0.0` (lock 2.0.49); runtime uses raw `text()` SQL | as built, see MVP.md §3.9 | https://docs.sqlalchemy.org/en/20/ |
| DB driver | asyncpg | floating `>=0.29.0` (lock 0.31.0) | as built, see MVP.md §3.9 | https://magicstack.github.io/asyncpg/current/ |
| Logging | structlog | floating `>=24.0.0` (lock 25.5.0) | as built, see MVP.md §11 | https://www.structlog.org/ |
| LLM SDK | anthropic (Python SDK) | floating `>=0.40.0` (lock 0.102.0); model string `claude-sonnet-4-20250514` hard-coded | as built, see MVP.md §3.4, §6.4 | https://docs.anthropic.com/en/api/client-sdks |
| Embeddings SDK | voyageai | floating `>=0.3.0` (lock 0.3.7); model `voyage-3`, 1024 dims | as built, see MVP.md §3.6 | https://docs.voyageai.com/docs/embeddings |
| Tracing SDK | langfuse (Python SDK) | floating `>=2.0.0` (lock 4.6.1); code written for the v2 API | as built, see MVP.md §11 and G-15 | https://langfuse.com/docs |
| PII (cloud mode) | google-cloud-dlp | floating `>=3.0.0` (lock 3.36.0) | as built, see MVP.md §3.7 | https://cloud.google.com/sensitive-data-protection/docs |
| Vector client | pgvector (Python) | floating `>=0.3.0` (lock 0.4.2); ORM `Vector(1024)` type only | as built, see MVP.md §5 | https://github.com/pgvector/pgvector-python |
| Auth lib (unused) | python-jose[cryptography] | floating `>=3.3.0` (lock 3.5.0); not imported | as built, see MVP.md §3.3 | https://python-jose.readthedocs.io/ |
| Backend dev tools | pytest, pytest-asyncio, ruff, mypy, httpx | floating `>=8.0.0`, `>=0.24.0`, `>=0.7.0`, `>=1.11.0`, `>=0.27.0` (Poetry dev group; no `dev` extra) | as built, see MVP.md §9, §10 | https://docs.pytest.org/ , https://docs.astral.sh/ruff/ , https://mypy.readthedocs.io/ |
| Packaging | Poetry (poetry-core); root `pyproject.toml` plus `backend/pyproject.toml` | build backend `poetry-core` unpinned | as built, see MVP.md §8a, G-28 | https://python-poetry.org/docs/ |
| Frontend framework | Next.js (App Router) | pinned `14.2.35` (`frontend/package.json:13`) | as built, see MVP.md §3.1 | https://nextjs.org/docs |
| UI library | React / react-dom | floating `^18` | as built, see MVP.md §3.1 | https://react.dev/ |
| Client state | zustand | floating `^5.0.13` | as built, see MVP.md §3.1 | https://zustand.docs.pmnd.rs/ |
| Markdown | react-markdown | floating `^10.1.0` | as built, see MVP.md §3.1 | https://github.com/remarkjs/react-markdown |
| SSE parser (unused) | eventsource-parser | floating `^3.0.8`; parser is hand-rolled in `src/lib/api.ts` | as built, see MVP.md §3.1 | https://github.com/rexxars/eventsource-parser |
| Styling / tooling | Tailwind `^3.4.1`, TypeScript `^5`, ESLint `^8`, Prettier `^3.8.3` | floating | as built, see MVP.md §9 | https://tailwindcss.com/docs |
| Frontend runtime | Node.js | 20 (CI only, `ci.yml:48-51`); `@types/node ^20`; no Dockerfile | as built, see MVP.md §8a | https://nodejs.org/docs/latest-v20.x/api/ |
| Database | PostgreSQL + pgvector | image `pgvector/pgvector:pg16` (`docker-compose.yml:3`, floating minor); Cloud SQL `POSTGRES_16` | as built, see MVP.md §5 | https://github.com/pgvector/pgvector , https://www.postgresql.org/docs/16/ |
| Row-level security | PostgreSQL RLS (`chunks` only) | PostgreSQL 16 | as built, see MVP.md §5 | https://www.postgresql.org/docs/16/ddl-rowsecurity.html |
| API gateway | Kong Gateway (DB-less) | `kong:3.9` (`kong/Dockerfile:1`, floating patch) | as built, see MVP.md §3.10 | https://developer.konghq.com/gateway/ |
| LLM proxy | LiteLLM | `ghcr.io/berriai/litellm:main-latest` (floating) | as built, see MVP.md §6.5 | https://docs.litellm.ai/ |
| LLM providers | Anthropic, OpenAI (`gpt-4o`), Google (`gemini-2.5-flash`) | via LiteLLM config (`litellm/config.yaml:1-21`) | as built, see MVP.md §6.5 | https://docs.anthropic.com/ , https://platform.openai.com/docs , https://ai.google.dev/gemini-api/docs |
| Observability backend | Langfuse server | `langfuse/langfuse:2` (floating minor); own `postgres:16` | as built, see MVP.md §11 | https://langfuse.com/self-hosting |
| Cache (unused) | Redis | `redis:7-alpine` (`docker-compose.yml:98`); no consumer | as built, see MVP.md §3.11 | https://redis.io/docs/latest/ |
| Cloud IaC | Terraform with provider google | `required_version >= 1.5`, `hashicorp/google ~> 5.0` (`terraform/main.tf:2-9`); `random` provider implicit | as built, see MVP.md §8b | https://registry.terraform.io/providers/hashicorp/google/latest/docs |
| Cloud runtime (as written, not deployed) | Cloud Run v2, Cloud SQL, Secret Manager, Artifact Registry, GCS, Cloud DLP | region `us-central1`; image tags default `latest` | as built, see MVP.md §8b | https://cloud.google.com/run/docs |
| CI | GitHub Actions | `actions/checkout@v4`, `setup-python@v5`, `setup-node@v4`, `upload-artifact@v4` | as built, see MVP.md §9 | https://docs.github.com/en/actions |
| Local orchestration | Docker Compose | compose file without a `version:` key | as built, see MVP.md §8a | https://docs.docker.com/compose/ |
