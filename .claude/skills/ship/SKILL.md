---
name: ship
description: Ship a finished phase or ad-hoc branch — final full gate, push, PR with an honest body, STATE.md update. Never merges; merging is Keshav's. Trigger /ship.
disable-model-invocation: true
---

# /ship

1. `python3 bin/sagectl gate` (full). Anything but GREEN → stop and say what failed.
2. Tree clean? Branch up to date with its base (`git fetch` + merge base in if behind)?
3. `clerk` mode=close-phase (or for an ad-hoc branch: push + PR with what/why/how-tested).
4. Report: PR url, verdict, honest list. Remind Keshav: verify tasks + `sagectl phase sign` are
   his, after he's looked at it working.
