---
name: algorithm-design
description: Paper-driven algorithm and data-structure design — frame the problem formally, gather candidate algorithms from papers and production systems, compare complexity and guarantees, prototype-test the leader. Use for ranking, search, scheduling, matching, streaming, caching, consensus, ML pipelines, or any core with a hard performance or correctness bar.
---

# Algorithm design

## 1. Frame the problem formally
Inputs, outputs, sizes (n, m, value ranges), the objective, hard constraints, and the
correctness criterion. Online vs offline, exact vs approximate, single machine vs distributed,
the failure model. Name the closest known problem class (for example: top-k, nearest neighbor,
bin packing, interval scheduling, stream counting, consensus).

## 2. Gather candidates (in parallel)
- `researcher:paper-scout` — papers and surveys for the problem class; 2-5 candidates.
- `researcher:docs-reader` — libraries that already implement the candidates, current versions.
- `researcher:web-scout` — production write-ups and benchmarks.

## 3. Compare
One table: candidate, time, space, guarantees (exactness, error bound, consistency), assumptions,
implementation effort, library support, evidence quality. Reject candidates whose assumptions do
not hold for our sizes and data.

## 4. Challenge
`researcher:skeptic` checks the leader's claimed complexity, guarantees and benchmark numbers against
the papers.

## 5. Prove it small
Before it goes into the architecture: a minimal prototype or test on representative data that
measures the property that matters (latency, accuracy, memory). The plan for this goes to the
build lane; the result goes into the ADR.

## 6. Record
The chosen algorithm, the paper references (arXiv id or DOI), the measured result, and the
conditions under which to revisit the choice.
