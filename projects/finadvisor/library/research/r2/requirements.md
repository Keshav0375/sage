# FinAdvisor target architecture: requirements (round 2, 2026-11-01)

Baseline: `/Users/keshav/Projects/sage/context/projects/finadvisor/arch/MVP.md` (as built at FinAdvisor d6c2bd3; gap register §13 with 62 gaps, 13 critical; vendor facts §14). Code repo: /Users/keshav/Projects/FinAdvisor.

## Goal (Keshav, verbatim intent)
Make FinAdvisor a production-ready, scalable RAG product that serves multiple customers (tenant firms) and many concurrent sessions, with sound system design and databases. Integrate, as first-class parts that Keshav can learn from: ETL / data engineering, agent evaluation, guardrails, security, Kafka. React + TypeScript frontend; backend; both deployed. Scalable RAG with advanced RAG techniques: faster and more accurate answers.

## Product constraints kept from the MVP
- Compliance-aware wealth-advisor assistant. Every claim cited. Tier (1-4) and jurisdiction (US/EU/UK) access control enforced in the database. PII redacted before embedding, before LLM calls, and on output. Stale-source flags (>12 months).
- Data: synthetic corpus (FINRA, SEC, MiFID II, FCA COBS as encoded). No real regulatory certification (Keshav, 2026-11-01).
- Eval gate blocks deploys (citation accuracy >= 0.95, faithfulness >= 0.90 today).

## Numbers
- Earlier input (single firm): ~50 advisors, < 5 QPS, < $100/month cloud + LLM.
- NEW: multiple tenant firms. Tenant count and total users: PENDING Keshav (design for a range of 5-50 tenants, 50-2,000 advisors, 5-50 QPS peak, unless told otherwise).
- Budget with Kafka and an always-on deployment: PENDING Keshav.
- Corpus: 50 docs / ~114 chunks today; design for 100k-1M chunks across tenants.
- Latency targets (orchestrator estimate, mark as estimate): time to first token p50 < 1.5 s, p95 < 3 s; full answer p95 < 8 s; retrieval p95 < 300 ms.
- Availability (estimate): 99.5% monthly for the chat path; ingestion may be asynchronous with minutes of lag.
- Team: one developer (Keshav), learning-oriented; operating burden matters.

## Existing platform choices (evidence: the repo)
- Cloud: GCP (Terraform in repo), Postgres 16 + pgvector, FastAPI (Python 3.12), Next.js 14 (React + TS), Kong, LiteLLM, Langfuse, Voyage embeddings, Anthropic primary LLM.
- These may change only with evidence.
