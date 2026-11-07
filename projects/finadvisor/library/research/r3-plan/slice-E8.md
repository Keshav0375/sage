# Slice E8

## Epic section (from arch/plan.md)

### E8 Frontend

- **Goal.** An advisor can sign in to their firm, ask a question and see a streamed, cited, trustworthy answer.
- **Scope.**
  - Vite + React 19 + TypeScript SPA: tenant discovery (`/t/<slug>`) and Identity Platform sign-in, SSE client with `Last-Event-ID` resume and `Idempotency-Key`, `meta` (degraded retrieval) notice, citations with excerpts, stale badges, conversation history, feedback, error states keyed by error code, sanitized markdown only.
  - vitest unit tests and Playwright end-to-end tests.
- **Arch sections.** overview.md#4.4, overview.md#6.1, overview.md#6.2, overview.md#8.2; ADR-010, ADR-019.
- **Dependencies.** E1, E4.
- **Spikes first.** none (consumes the E4 contract).
- **Done when.**
  - A Playwright run covers sign-in for two tenants, a streamed cited answer, a mid-stream disconnect with resume, a 429 and a 401 handled without a crash, a stale badge and thumbs feedback.
  - No unsanitized HTML reaches the DOM (test with an injected payload); the token is not stored in `localStorage`.
  - Fixes G-13 (SPA), G-57.

## Arch files to read (paths; read only the named subsections)

- context/projects/finadvisor/arch/overview/04-components-and-responsibilities.md  (sections: 4.4)
- context/projects/finadvisor/arch/overview/06-interfaces-and-contracts.md  (sections: 6.1, 6.2)
- context/projects/finadvisor/arch/overview/08-security-and-privacy.md  (sections: 8.2)
- context/projects/finadvisor/arch/stack.md (versions)
- context/projects/finadvisor/arch/overview/06-interfaces-and-contracts.md §6.6 (config keys), only the keys this epic uses

## ADRs (context/projects/finadvisor/arch/decisions.md; line of heading)

- line 305: ADR-010: Authentication with Identity Platform multi-tenancy and tenant discovery
- line 112: ADR-019: Compute mapping: one image, three entrypoints, Cloud Run, Vite SPA
