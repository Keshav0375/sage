---
key: "E4-T28"
title: "Numeric grounding gate per sentence, locale-aware"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T11", "E4-T19", "E4-T33"]
arch_refs: ["deep-dive/08-security-and-privacy.md#8.6", "deep-dive/04-components-and-responsibilities.md#4.5", "decision-logs.md#adr-036", "decision-logs.md#adr-037"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 134, "id": 6263476521, "url": "https://github.com/Keshav0375/FinAdvisor/issues/134"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Withhold any sentence whose number or date is not found in the cited spans, across EN, DE and FR number formats.

## Description
Implement `guardrails/numeric_gate.py` as a `ReleaseCheck` (E4-T19). Quote 8.6: 'Deterministic, per sentence, before release. Locale-aware extraction of numbers and dates into `(Decimal, unit)`: EN `1,234.56`, DE/FR `1.234,56` and `1 234,56` (including the narrow no-break space), percent, bps, currency, ISO and long dates in EN/DE/FR. Each must appear in a cited span of that sentence's `[n]`. Rounding is allowed only to the precision the answer states; bps and % are whitelisted; identifiers (CELEX, article and rule numbers, `2014/65/EU`) and the as-of date are excluded; derived figures only from a deterministic `calc` tool whose inputs are grounded. An ungrounded number withholds the answer ("figure X not found in cited sources") with an escalate offer.'

Behaviour: extract from the sentence; resolve each cited `[n]` to the ORIGINAL chunk text fetched by id (not the model-visible copy); a figure passes if the same Decimal (after rounding the chunk figure to the precision the sentence states) occurs in a cited span, or equals a bps-to-percent conversion, or equals a `calc` tool result of this turn whose inputs were each grounded (E4-T33 returns the inputs in the tool record). A failing sentence returns `Withhold('numeric_ungrounded')`: that sentence is withheld, earlier sentences stay released, and the answer ends with `refusal {ANSWER_WITHHELD, reason numeric_ungrounded}` (confirmed per orchestrator, R4-D20). The refusal text names the figure ("figure X not found in cited sources") with `escalate_offer: true`. Locale of a sentence is taken from its cited chunk's language. Config: `NUMERIC_GATE_ENABLED` (default true). The false-reject rate is measured later in E7 (line <= 3% proposed); this ticket exposes counters `numeric_gate_checked_total` and `numeric_gate_rejected_total`. Out of scope: eval measurement (E7), UI text.

## Acceptance criteria
- [ ] Given a sentence 'The fee is 1,234.56 USD [1]' with chunk text containing 1,234.56, a DE sentence '1.234,56 EUR' and an FR sentence '1 234,56 EUR' (narrow no-break space) each with matching chunk text, when checked, then all pass (parametrised unit test test_locale_formats_ground).
- [ ] Given a sentence with a figure absent from every cited span, when checked, then Withhold('numeric_ungrounded') is returned, the refusal message contains the figure, and no delta for that sentence is emitted end to end (test_ungrounded_number_withholds_answer).
- [ ] Given sentences 1 and 3 grounded and sentence 2 ungrounded, when the turn runs, then the delta for sentence 1 is emitted, none for sentences 2 and 3, and the events end with refusal ANSWER_WITHHELD reason numeric_ungrounded then done(refusal) (test_numeric_fail_keeps_earlier_sentences).
- [ ] Given 'rounded to 1.2%' with chunk '1.23%', 'rounded to 1.2%' passes and '1.3%' fails; 150 bps vs chunk 1.5% passes; the CELEX id 32014L0065, rule 275.206 and the as-of date are not treated as figures (unit tests).
- [ ] Given a derived figure with no `calc` call, it is withheld; given a calc result whose inputs were grounded, it passes; given a calc result with an ungrounded input, it is withheld.
- [ ] Hypothesis property test: for any Decimal rendered in EN, DE and FR formats and placed in a chunk, the gate extracts the same value from each rendering (round-trip property), and a number not in the chunk is never accepted.
