---
name: research
description: Deep research on a question — parallel scouts over current docs, papers, the web and Keshav's library, then a cited synthesis by the main session and an adversarial fact-check. Saves the note to brain/library/research/. Use for tech choices, "what's the best way to…", "is X worth it", tool comparisons.
argument-hint: "<question>"
---

# /researcher:research

## 1. Sharpen the question
Restate it in one sentence with the decision it serves and the constraints that matter. If it is
ambiguous, ask Keshav one question first.

## 2. Check the library
Search `brain/library/` (research, papers, patterns, council) for earlier work. Reuse it and
note its date.

## 3. Scout (one message, in parallel)
Spawn the scouts that fit: `researcher:docs-reader` (official docs, one per technology),
`researcher:reference-scout` (similar well-known systems, vendor reference architectures),
`researcher:paper-scout` (papers), `researcher:web-scout` (practitioner evidence). Give each the same sharpened question and its source.

## 4. Synthesize (main session)
Merge the evidence. Separate consensus from single-source claims. Resolve conflicts by evidence
quality: official docs and measured results beat opinion; newer beats older for fast-moving tools.
Give the answer first, then the reasoning.

## 5. Fact-check
Spawn `researcher:skeptic` on the synthesis. Fix or drop every `WRONG` or `UNSUPPORTED` claim, and mark
`WEAK` ones.

## 6. Save
Write `brain/library/research/<yyyy-mm-dd>-<slug>.md`: question, answer, evidence table with
links and dates, open gaps, and the skeptic's verdicts.
