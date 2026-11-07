# Cloud Logging extract (fetched 2026-11-01; all docs pages "Last updated 2026-10-30 UTC")
Note: WebFetch returns small-model summaries; quotes below are as returned by the fetcher, not raw page text.
Sources: docs.cloud.google.com/logging/docs/routing/overview, /logging/docs/buckets, /logging/quotas, /logging/docs/routing/managed-encryption (cloud.google.com URLs 301 to docs.cloud.google.com)

## Q1 Delete individual log entries
NOT FOUND on routing/overview, buckets, quotas. Closest:
- buckets: "Logs can't be recovered after the applicable retention period ends."
- quotas: "requests that delete logs or manage resources such as log buckets" count toward control-request quota of 600/min (not increasable). (Refers to deleting logs, ambiguous.)
- overview: "You can't modify or delete the `_Required` log sink."

## Q2 Retention / locking
- buckets: "the default is `30 days`" for a new bucket with no custom retention; retention "between 1 day and 3650 days."
- buckets: "You can't change the retention period of the `_Required` log bucket."
- buckets: "You can also configure the retention period for the `_Default` log bucket when that log bucket is in a project."
- quotas: _Required bucket "400 days," not configurable; _Default in folders/orgs "30 days" not configurable; _Default in projects "30 days" configurable; user-defined "30 days" configurable.
- buckets: "Locking a log bucket is irreversible." "When you lock a bucket against updates, you also lock the bucket's retention policy." Locked bucket cannot be deleted until every entry meets retention.
- quotas: 100 buckets/project (up to 2,500).

## Q3 Exclusion filters
- overview: "If the log entry matches the inclusion filter and at least one exclusion filter, then it isn't routed."
- overview: "Exclusion filters are applied after log entries are received by the Logging API."
- overview: "You can't use exclusion filters to reduce the consumption of your entries.write API quota."
- overview: "You can modify and disable the `_Default` log sink." _Required sink cannot be modified/deleted.

## Q4 CMEK key disabled/destroyed
Log-bucket-specific behavior NOT FOUND. buckets page only links CMEK setup. managed-encryption page (org/folder CMEK settings) says:
- "If you remove Logging's access to a key, then it can take up to one hour for the change to take effect."
- Key unavailable = disabled or permissions removed. "Logging is unable to write temporary disaster-recovery files and, for users, queries stop functioning."
- Cloud EKM keys: "Cloud Logging continues storing logs in log buckets, but users won't be able to access that data." Logging buffers incoming data up to one hour then drops it if key stays unavailable.
- Destroyed keys: not mentioned.

## Q5 Deleting a bucket
- buckets: "The bucket, including all the logs in it, is deleted after 7 days." Pending-deletion state for 7 days; logs keep routing to it until sinks are stopped.

## Q6 Pricing
NOT FOUND. cloud.google.com/stackdriver/pricing -> cloud.google.com/products/observability/pricing returned only the title (page JS-rendered). quotas page: "retention costs apply to logs data retained longer than the default retention period" (effective April 1, 2023) and points to Observability pricing page. (Fetcher's memory figures of $0.50/GiB, 50 GiB free, $0.01/GiB-mo retention are UNVERIFIED, do not use.)
