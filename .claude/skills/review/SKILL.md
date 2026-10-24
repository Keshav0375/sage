---
name: review
description: Quick review of uncommitted or last-commit changes in the active project's repo for correctness and security. Mid-task check; the authoritative review is /build step 6.
argument-hint: "[base ref, default HEAD]"
---

# /review

1. Determine the diff: uncommitted (`git diff HEAD`), else the last commit.
2. ONE message: `reviewer` and `safety-reviewer` (safety only if the diff touches auth, IO,
   shell, infra, workflows, agents, or secrets-adjacent code).
3. Merge their lines into one finding block (ground-rules format), dedupe, max 10 lines.
4. Recurring defect (it's in `sagectl lesson list` already)? Say so: it's a candidate for `/retro`.
