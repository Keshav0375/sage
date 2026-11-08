---
key: "E8-T1"
title: "Replace Next.js 14 with a Vite React 19 TS scaffold"
epic: "E8"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E0-T10"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.4", "decision-logs.md#adr-019", "deep-dive/11-tech-stack.md"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 190, "id": 6263565998, "url": "https://github.com/Keshav0375/FinAdvisor/issues/190"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
The frontend builds as a static Vite + React 19 + TypeScript SPA and Next.js is gone.

## Description
Implements deep-dive/04-components-and-responsibilities.md §4.4 ("Vite + React 19 + TypeScript single-page app, static files in a GCS bucket ... Replaces Next.js 14 (G-13, G-57)") and ADR-019. In frontend/: add vite, @vitejs/plugin-react, react/react-dom 19, typescript; index.html + src/main.tsx entry; vite.config.ts (dev server proxies /v1 to the compose gateway so the SPA stays same-origin); keep tailwind, zustand, react-markdown, eventsource-parser only if later tickets use them. Move existing components/hooks from src/app + src/components into a Vite layout without behaviour changes (still the MVP header-user flow until E8-T3). Update the E0-T10 artefacts for Vite: `npm run test` (vitest, jsdom), `npm run typecheck` (tsc --noEmit), and the frontend dev Dockerfile (vite dev server, port documented). Remove next, eslint-config-next, next.config.mjs, next-env.d.ts; replace with plain eslint config. Pin Vite and TypeScript versions in package.json (deep-dive/11-tech-stack.md: pin at implementation). Out of scope: bucket/ALB deploy (E10), auth, new features. Use SPA fallback so /t/<slug> deep links work in the dev server and `vite preview`.

## Acceptance criteria
- [ ] Given a clean checkout, when `npm ci && npm run build` runs in frontend/, then it exits 0 and dist/index.html plus hashed assets exist.
- [ ] Given package.json, when searched, then no `next` or `eslint-config-next` dependency and no next.config.mjs remain (checked by a vitest/grep test or CI step).
- [ ] Given the dev server or `vite preview`, when GET /t/acme is requested, then index.html is returned (SPA fallback), asserted by a vitest or curl check.
- [ ] `npm run typecheck` and `npm run test` exit 0, with at least one smoke test rendering <App/>.
- [ ] The frontend dev Dockerfile builds (`docker build`) and serves the Vite dev server.
