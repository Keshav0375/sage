---
name: validate
description: Validate and improve an existing design or decision — check each technology choice against its current official docs (Azure via Microsoft Learn, AWS, GCP, Context7 for libraries) and compare the design with well-known similar systems and vendor reference architectures. Returns keep / improve / change per decision. Trigger /think:validate <project> [section or ADR].
argument-hint: "<project> [arch section or ADR number]"
---

# /think:validate

## 1. Extract (main session)
Read the target from `brain/projects/<p>/arch/` (one section, one ADR, or the whole overview by
section). List:
- every **decision** (what was chosen, and the reason given),
- every **technology** it relies on (cloud services, databases, brokers, frameworks, libraries),
  with the version when known,
- the **requirements as numbers** the design must meet.

## 2. Gather (one message, in parallel)
- One `think:docs-reader` per technology. Give each the decisions that rely on it and the
  numbers it must meet.
- One `think:reference-scout` with the problem, the scale and the cloud in use: similar
  well-known systems and the vendor's reference architecture for this workload.
- `think:paper-scout` only when a decision has an algorithmic core.

## 3. Challenge
Spawn `think:skeptic` on the decisions that the evidence calls into question.

## 4. Verdict per decision (main session)
One table: decision, verdict, evidence, suggested change.
- **Keep**: the official docs confirm it and the references support it.
- **Improve**: it holds, but the docs or the references show a better setting, pattern or limit
  to plan for.
- **Change**: the docs contradict it, a limit breaks it at our scale, or the references show a
  clearly better approach.
- **Unknown**: the evidence does not settle it; say what would.

## 5. Hand off
Changes to the architecture are Keshav's call. Present the table and the top three
improvements. After he decides, record them with `/think:decide`. Save the evidence to
`brain/library/research/<yyyy-mm-dd>-validate-<project>.md`.
