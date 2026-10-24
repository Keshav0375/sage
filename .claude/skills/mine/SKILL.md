---
name: mine
description: Weakness mining — cluster recent failures (lessons, tool failures, corrections) across projects into named failure mechanisms ranked by cost. Read-only; feeds /evolve. Trigger /mine [project] [days].
argument-hint: "[project] [days=30]"
---

# /mine

1. `python3 bin/sagectl mine [-p <project>] --days <d>` to show Keshav the raw clusters.
2. If there are ≥ 2 clusters with ≥ 2 members: spawn `miner` to name mechanisms and rank them.
3. Reply with the CLUSTERS block. For the top mechanism, say whether it's ready for `/evolve`
   (needs ≥ 3 signals and at least one reproducible eval task) or needs more data first.

Honest note: with < ~20 signals the clusters are anecdotes, not patterns. Say so when that's the case.
