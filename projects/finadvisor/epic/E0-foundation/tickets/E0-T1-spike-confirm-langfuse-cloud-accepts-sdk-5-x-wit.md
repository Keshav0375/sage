---
key: "E0-T1"
title: "Spike: confirm Langfuse Cloud accepts SDK 5.x with masking"
epic: "E0"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: []
arch_refs: ["deep-dive/01-context-and-goals.md#1", "decision-logs.md#adr-018", "deep-dive/11-tech-stack.md#llm-observability"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 2, "id": 6155564875, "url": "https://github.com/Keshav0375/FinAdvisor/issues/2"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Prove that Langfuse Python SDK 5.x exports traces to Langfuse Cloud with masked and capture-off spans, and record the exact parameter names the wrapper must use.

## Description
Why: ADR-018 chooses Langfuse Cloud Hobby with Python SDK 5.x (5.1.0 current) behind one wrapper, using `@observe` with `capture_input` / `capture_output` off on sensitive spans and `mask_otel_spans` for export masking. The MVP pins langfuse 4.6.1 and calls v2 methods that do not exist (G-15). plan.md E0: "confirm Langfuse Cloud accepts SDK 5.x as the first ticket". The wrapper ticket E0-T8 must not start until this passes.

Build:
- Bump `langfuse` in `backend/pyproject.toml` to the 5.x line (5.1.0 or newer 5.x) and re-lock (`poetry lock`), keeping every other locked version unchanged where possible. Do not touch `backend/src/observability/tracing.py` or its mocked tests (E0-T8 replaces them).
- Add `backend/scripts/spike_langfuse_v5.py`. It reads `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` from the environment (Settings does not exist in its final form yet), creates one trace with (a) a normal span whose input contains the marker `SPIKE-SSN-123-45-6789` and which is exported through SDK-level masking (`mask_otel_spans`, confirm the exact name and signature against the SDK 5.1.0 docs via Context7 or langfuse.com/docs) that replaces the marker with `[REDACTED]`, and (b) a sensitive span created with `capture_input=False, capture_output=False` and non-empty input/output. It flushes, then polls the Langfuse public API (`GET {host}/api/public/traces/{id}`, basic auth with the key pair) for up to 60 s.
- The script exits 0 only if: the trace is retrievable; no observation input/output contains `SPIKE-SSN`; the sensitive span has no input and no output. Otherwise it prints the reason and exits 1. A transport or auth error exits non-zero.
- Write `docs/spikes/langfuse-sdk5.md`: verdict (pass/fail), SDK version, the exact masking and capture-off parameter names that worked, host/region used, and any limitation found (for example if the legacy `mask=` does not cover OTel spans, which ADR-018 says it does not).

Out of scope: the production wrapper, orchestrator changes, Settings keys (E0-T3 and E0-T8). Needs a Langfuse Cloud Hobby project with a key pair supplied by Keshav (see questions).

## Acceptance criteria
- [ ] `cd backend && poetry lock --check` exits 0 and `poetry run python -c "import langfuse, importlib.metadata as m; print(m.version('langfuse'))"` prints a version starting with `5.`.
- [ ] Given a valid Langfuse Cloud key pair in the environment, when `poetry run python scripts/spike_langfuse_v5.py` runs, then it exits 0 and prints the trace id it fetched from `/api/public/traces/{id}`.
- [ ] Given the same run with `LANGFUSE_SECRET_KEY` set to a wrong value, when the script runs, then it exits non-zero (the check can fail).
- [ ] The script exits 1 if any fetched observation input or output contains the string `SPIKE-SSN`, and exits 1 if the sensitive span has a non-empty input or output (demonstrated by running once with masking disabled via a `--no-mask` flag and seeing exit 1).
- [ ] `docs/spikes/langfuse-sdk5.md` exists and contains a `Verdict:` line with `pass` or `fail`, the installed SDK version, and the exact masking and capture-off parameter names.
