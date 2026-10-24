---
name: research
description: Deep research on a question — parallel scouts across Keshav's own library, the web, Reddit, official docs (Context7), papers (arXiv) and GitHub; then a cited synthesis and an adversarial fact-check. Saves the note to library/research/. Use for tech choices, "what's the best way to…", "is X worth it", market/tool comparisons.
argument-hint: "<question>"
---

# /research

1. **Sharpen the question** in one line (what decision does it serve?). Pick sources:
   - always: `library` (Keshav's own lessons, ADRs, past research. Check before the internet)
   - tech choice: `web` + `reddit` + `docs` + `github`
   - method / ML / "state of the art": add `papers`
   - pull subreddits/libraries from the active project's `[research]` in project.toml.
2. **Fan out:** one `scout` per source, ALL in ONE message. Each gets `QUESTION`, `SOURCE`, `HINTS`.
3. **Synthesize:** `synthesizer` with all SCOUT blocks. It writes `library/research/<date>-<slug>.md`.
4. **Fact-check:** `skeptic` on the synthesis. ❌ claims get removed or corrected in the note;
   ⚠️ claims get marked single-source.
5. Reply: the answer (2-4 lines), consensus vs contested, what's unknown, the note's path. If it
   decides something for a project → suggest `/decide` to record the ADR.

Cost check: 4-6 scouts + 2 opus calls. For a quick fact, just WebSearch it yourself. Don't fire
the whole pipeline at a one-liner.
