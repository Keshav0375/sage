---
name: ship
description: Prepare verified work for merge — confirm a GREEN verifier verdict, push the branch, open a PR with a summary and the evidence. Never merges. Trigger /build:ship.
---

# /build:ship

1. Require a `GREEN` verdict from `build:verifier` on the current HEAD. If there is none, run
   `/build:check` first.
2. Ask Keshav before you push. Push the branch (never force-push).
3. Open a PR with `gh pr create`: what changed, why, the verifier's gate lines, open findings.
   No Claude attribution.
4. Update `brain/projects/<p>/STATE.md` (`## Now`) with the PR link.
5. Merging is Keshav's call. Stop here.
