# Porting a scanner (rules for builder agents)

Source of the mechanism: career-ops v1.40.0 (MIT) at
`/tmp/claude-0/-home-user-sage/3e78f90f-c3ba-525e-839c-b35fcf089445/scratchpad/ext/career-ops`
- `providers/<name>.mjs` — endpoint, request shape, field names, detect() rules
- `tests/providers/<name>.test.mjs` — real response shapes to copy into our fixtures

We write **our own Python**, not a line-by-line translation. Port the main path: endpoint, request,
pagination (bounded by `ctx.max_jobs`), field mapping, `detect()` for tenant ATSs. Skip upstream edge-case
machinery (caches, office enrichment, giant-board fallbacks) unless the source is unusable without it.

## Files
- `scripts/providers/<module>.py` — module name = provider name with `-` → `_`, and a leading `_` for names
  starting with a digit (`4dayweek` → `_4dayweek` is NOT allowed since `_` means helper; use `four_day_week.py`).
  `PROVIDER.name` keeps the career-ops name exactly (e.g. `"4dayweek"`, `"adp-myjobs"`).
- `tests/providers/test_<module>.py` — unittest, uses `tests.providers._helpers.ctx_with`.

## Contract (see `_base.py`, copy `greenhouse.py`)
- Class attributes: `name`, `wave` (from `projects/gimme-job/providers.md`), `kind`, `tenant`, `hosts`.
- `detect(careers_url) -> Target | None` for tenant ATSs (return None for board-wide sources).
- `fetch(target, ctx) -> list[Job]`; every job `.validate()`d; never invent fields.
- Board-wide sources read `target.query` / `target.location` / `target.options` (e.g. keywords, country).
- HTTP only via `ctx.http.get_json / get_text / post_json / get`. Never import urllib.request in a scanner.
- Helpers in `_parse.py`: `html_to_text`, `feed_items` (RSS/Atom), `json_ld_jobs`, `next_data`, `links`,
  `to_iso`, `parse_salary`, `workplace_from`, `employment_from`, `dig`, `first`, `absolute`, `slug_from_url`.
- Standard library only. No new helper files; if you truly need a helper, keep it private inside your module.
- Single-company providers (amazon, apple, ibm…): `tenant = False`, company name fixed.
- Sources that need login or an API key upstream: still write the module, set
  `extra = {"requires_key": "<ENV_NAME>"}` handling: read `os.environ`, and if absent raise
  `ProviderError("needs <ENV_NAME>")`. Do not hardcode keys.

## Test (minimum per scanner)
1. Fixture copied/adapted from the upstream test's sample payload (real field names).
2. `fetch` returns ≥ 1 Job with correct `title`, absolute `url`, `source == name`, and the company/location the fixture implies.
3. `detect` positive + negative case (tenant ATSs only).
Run: `cd plugins/gimme-job && python3 -m unittest discover -s tests -t . -p 'test_*.py'`
