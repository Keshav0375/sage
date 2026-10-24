# _inbox — evals

Replayable tasks with a real verifier. Created from lessons by `/retro` via
`sagectl eval new -p _inbox --id … --prompt … --verify …` — the split (heldin/heldout) is
assigned by hash, not chosen. `heldout/` is sealed by the guard: agents can run it through
`sagectl eval run --split heldout`, never read it.
