---
key: "E8-T14"
title: "Add the firm switcher with one session per firm"
epic: "E8"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E8-T3", "E8-T4", "E13-T5", "E13-T11"]
arch_refs: ["decision-logs.md#adr-032", "decision-logs.md#adr-031", "deep-dive/08-security-and-privacy.md#8.2", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 195, "id": 6263575138, "url": "https://github.com/Keshav0375/FinAdvisor/issues/195"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
An advisor who works for two firms can switch between them in one tab; each firm keeps its own token, user and conversations and nothing crosses.

## Description
Implements ADR-032: "The SPA keeps one auth instance per firm and a firm switcher; each API call carries one firm's token" and edge case #17 (7.4). Build on the per-firm factory of E8-T3 and the 421 handling of E8-T4.

- A `FirmSessions` store in memory: a map slug -> {display_name, apiBase, cell_id, auth instance, `/v1/me` result}. A firm is added when the advisor opens `/t/<slug>` and signs in (E8-T2, E8-T3). The switcher lists only firms signed in during this tab session; there is no server call that lists a person's firms and no person-linking (ADR-032: optional UX, never an authorization input).
- Switching sets the active slug, loads that firm's conversation list with that firm's token, and navigates to `/t/<slug>`. Every request is built from the active firm's session only; a request is never sent with another firm's token.
- State is per firm: conversation list, in-flight turn, as-of chip (E8-T13) and error state. Switching away does not abort another firm's in-flight turn but the stream renders only in its own firm view.
- Nothing about firms or tenant ids is persisted (no storage); a reload requires opening the firm link again (client fact of ADR-032: `tenantId` is not persisted).
- If E13-T11 recorded the alias fallback (per-firm email aliases, spike failed), the switcher still works (same code path) and the sign-in form shows a hint that the firm email alias is used; no code branches on the alias.

Out of scope: person linking or identity merge, the server checks (E13-T5, E13-T11), end-to-end browser tests (E8-T16).

## Acceptance criteria
- [ ] Given firm A and firm B both signed in with mocked SDK instances, when the advisor switches A -> B -> A, then `currentUser` of A is the same object throughout and each request's `Authorization` header carries the token of the firm shown (vitest `firmSwitcher.test.tsx::tokens_never_cross`).
- [ ] Given an in-flight stream in firm A, when the advisor switches to B, then A's stream continues into A's store and no delta is rendered in B's view.
- [ ] Given two firms, when storage is dumped, then localStorage, sessionStorage and IndexedDB contain neither firm's token, slug list nor tenantId (unit test).
- [ ] Given a reload, when the SPA loads `/t/a`, then only firm A is in the switcher and firm B must be opened again (unit test of the store initial state).
- [ ] Given firm B's API returns 421 `WRONG_CELL`, when the switcher loads B's conversations, then B's `apiBase` is updated through E8-T4 and firm A's `apiBase` is unchanged.
