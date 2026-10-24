---
name: council
description: LLM Council for decisions that are expensive to reverse (after Karpathy's llm-council) — independent answers from members with different lenses and models, anonymized peer ranking, then a chairman verdict that preserves dissent. Trigger /council <question>.
argument-hint: "<decision question>"
disable-model-invocation: true
---

# /council

Use for architecture forks, build-vs-buy, career/strategy calls. Costs ~4-6× a normal answer.
Don't convene it for trivia.

1. **Frame:** the decision, options on the table, constraints, what "good" means. Gather
   context paths (arch docs, research notes) members may read.
2. **Members (ONE message):** 3 `councilor` agents, mode=answer, each with a different LENS:
   `pragmatist-shipper` · `systems-architect-at-scale` · `skeptic-risk` (swap in `cost-and-ops`
   or `user-and-product` when relevant). **Diversify models** via the Agent tool's `model`
   param (e.g. opus / sonnet / opus). Same-model councils share blind spots. If an external
   CLI is installed and Keshav allows it (`codex exec`, `gemini -p`), add it as a 4th member
   through Bash.
3. **Anonymize:** shuffle the answers, label them A, B, C… Keep the key to yourself.
4. **Rank (ONE message):** the same councilors (or fresh ones), mode=rank, each gets all
   anonymized answers.
5. **Chair:** `chairman` with answers + rankings + the de-anonymization key. It writes
   `library/council/<date>-<slug>.md`.
6. Reply with the VERDICT block. If it's a project decision → `/decide`.
