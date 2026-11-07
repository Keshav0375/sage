# Langfuse retention + pricing extract (fetched 2026-11-01; no page dates shown on either page)
Note: WebFetch returns summarized text; quotes are as returned by the fetch tool.

## Source 1: https://langfuse.com/docs/administration/data-retention
Q1 min: "we accept a number of days with a minimum of 3 days."
Q1 plans: availability table: Pro and Enterprise available; Self Hosted = Enterprise Edition; Hobby and Core not available.
Q1 deleted: nightly, selects "traces, observations, scores, and media assets that are older than the configured retention period." Not deleted: audit logs, dataset items; media linked to saved dataset items excluded. Halo conversations deleted by last update.
Q4: Backups not mentioned. "Deleted assets cannot be recovered." Self-hosted S3 versioned buckets: "delete markers and non-current versions need to be removed manually or with a lifecycle rule."

## Source 2: https://langfuse.com/pricing
Q2 Hobby (free): "50k units / month included"; data access "30 days"; "2 users"; projects "Unlimited" (comparison table).
Q3: Page does not state a Hobby data retention period. FAQ: data retention is "a separate, opt-in feature on Pro and Enterprise." Table marks data retention management "--" for Hobby.
Other: Core $29: 90 days access, unlimited users, retention mgmt "--". Pro $199: 3 years, Yes. Enterprise $2,499: 3 years, Yes. Older data "is still stored and becomes accessible again when you upgrade."
