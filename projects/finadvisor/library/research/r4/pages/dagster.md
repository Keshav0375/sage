# Dagster extract (fetched 2026-11-02)
Note: docs.dagster.io 308-redirects to https://dagster.io/docs/... (fetched there). WebFetch quotes are via a summarizing model; treat as near-verbatim.

Q1 Blocking asset checks (https://dagster.io/docs/guides/test/asset-checks, "Blocking downstream materialization")
- "By default, if a parent's asset check fails during a run, the run will continue and downstream assets will be materialized."
- "set the `blocking` argument to `True` in the `@asset_check` decorator."
- Example: if `orders_id_has_no_nulls` fails, "the downstream `augmented_orders` asset won't be materialized." (downstream assets of the checked asset, within the run)

Q2 Backfills (https://dagster.io/docs/guides/build/partitions-and-backfills/backfilling-data)
- "Launching single-run backfills using backfill policies": "Dagster supports backfills that execute as a single run that covers a range of partitions." Set asset `backfill_policy` to `single_run` (BackfillPolicy).
- Concurrency limits/pools: NOT FOUND on this page.
- Whether schedules/sensors keep running during backfill: NOT FOUND on this page.

Q3 Declarative automation (https://dagster.io/docs/guides/automate/declarative-automation)
- "Declarative Automation is a framework that uses information about the status of your assets" ...
- "To use Declarative Automation, you will need to enable the default" automation condition sensor in the UI.
- Page has no deprecated/experimental/beta label. Auto-materialize relation: NOT FOUND (page does not mention it). Sidebar has "Migrating from sensors to Declarative Automation".

Q4 Sensors (https://dagster.io/docs/guides/automate/sensors)
- Cursors: "may want to implement a cursor to optimize sensor performance"; cursors store state across evaluations.
- Run key: "Dagster will skip processing requests with previously used run keys, ensuring that duplicate runs won't be created."
- minimum_interval_seconds: "the minimum number of seconds that will elapse between sensor evaluations."
- Observable source assets: NOT FOUND on this page.

Q5 dagster-openlineage (https://pypi.org/project/dagster-openlineage/)
- Exists. Summary "Dagster integration for OpenLineage." "Asset-centric OpenLineage emission for Dagster."
- Latest 0.2.1, 2026-05-22 (PyPI JSON confirms 2026-05-22T19:45:13). Prior: 0.2.0 2026-05-19, 0.1.0 2025-12-23. No deprecation notice. Migration note: "`OpenLineageEventListener` is removed"; `include_asset_events` default changes in v0.3. Maintenance status not stated explicitly (maintainer elementl).
- CHANGES.md line ~405 (under Documentation): "Added documentation for the OpenLineage integration."

Q6 Latest version
- CHANGES.md top heading: "## 1.13.28 (core) / 0.29.28 (libraries)" (no date in file). PyPI dagster 1.13.28 uploaded 2026-10-30T14:40:30.
