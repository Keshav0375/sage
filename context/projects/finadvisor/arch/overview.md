# finadvisor: architecture

Binding. Agents read this by section. When it is silent, the orchestrator resolves it with research and an ADR.

## 1. Context and goals

FinAdvisor is a compliance-aware RAG assistant for wealth advisors at a fictional firm, Meridian Wealth Partners. An advisor asks a question; a ReAct agent (Claude via Kong and LiteLLM) searches a synthetic knowledge base of 50 documents (US, EU, UK, 2 APAC) through four tools and answers with `[N]` citations. Postgres row-level security limits what each of four mock advisors can see by tier and jurisdiction. It is an interview-grade MVP: header-only mock auth, never deployed (MVP.md §1).

Target architecture: not yet decided; baseline in MVP.md.

## 2. Quality attributes (with numbers: load, latency, availability, cost)

Inputs from Keshav (2026-11-01):
- Load: about 50 advisors, fewer than 5 QPS.
- Cost: under $100 per month, cloud plus LLM.
- Compliance scope: US, EU and UK, synthetic corpus only (FINRA, SEC, MiFID II, FCA COBS as encoded); no real regulatory certification.
- Latency target: open.
- Availability target: open.

## 3. System context and boundaries

Target not yet decided. As built: MVP.md §2.

## 4. Components and responsibilities

Target not yet decided. As built: MVP.md §3, §4.

## 5. Data model and storage

Target not yet decided. As built: MVP.md §5.

## 6. Interfaces and contracts

Target not yet decided. As built: MVP.md §6.

## 7. Scaling, failure modes and recovery

Target not yet decided. As built: MVP.md §8, §13.

## 8. Security and privacy

Target not yet decided. As built: MVP.md §12.

## 9. Observability

Target not yet decided. As built: MVP.md §11.

## 10. Open questions
