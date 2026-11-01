# finadvisor: state

## Now
- 2026-11-01 As-built baseline DONE: `arch/MVP.md` maps the code at FinAdvisor d6c2bd3
  (diagrams, data model, interfaces, config, runtime, CI, tests, security posture) with a gap
  register of 62 gaps (13 critical, 16 high, 27 medium, 6 low). ADR-001 makes it the baseline.
  `stack.md` filled as built; `overview.md` §1-2 hold the goals and Keshav's inputs.
- Inputs for later research: ~50 advisors, <5 QPS, <$100/month, US/EU/UK synthetic.
- Next: a research round on the target architecture, starting from MVP.md §13-§14
  (`/researcher:run finadvisor <target goal>`). Re-map first if the code has changed.

## Open decisions
- (only questions about scope, compliance or money; agents resolve the rest with evidence)

## Blockers
- (none)
