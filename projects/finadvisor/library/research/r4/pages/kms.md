# GCP KMS extract (fetched 2026-11-01)
Note: WebFetch returns summarized text; quotes are as returned by the fetch tool.

## Q1 Duration
Source: https://docs.cloud.google.com/kms/docs/destroy-restore (Last updated 2026-10-27 UTC)
- Introduction: "The default scheduled for destruction duration is 30 days."
- "set a custom scheduled for destruction duration for a key during key creation."
- Org policy "Minimum destroy scheduled duration per key" can set a floor. Page does not use "destroy_scheduled_duration" or give a numeric min.
Source: https://docs.cloud.google.com/kms/docs/key-states (Scheduled for destruction state)
- "By default, keys in Cloud KMS spend 30 days in the Scheduled for destruction state"
- "The duration is only configurable during key creation."
- "The minimum duration is 24 hours for all keys, except for import-only keys which have a minimum duration of 0."
- "The maximum duration is 120 days."
- "While a key version is in this state, it can't be used for cryptographic operations, and requests to use the key fail." Can be restored to disabled state during period.

## Q2 Effect on data
destroy-restore, Before you begin > Understand the risks: "After a key is destroyed, data that was encrypted with the key version can't be decrypted." Data "is considered crypto-shredded."

## Q3 Pricing
NOT FOUND. https://cloud.google.com/kms/pricing fetched but only title returned (truncated; offset read returned 92 chars). docs.cloud.google.com/kms/pricing redirects back to cloud.google.com. key-states page: does not mention billing.

## Q4 Quotas
Source: https://docs.cloud.google.com/kms/quotas (Last updated 2026-10-27 UTC)
- "There are no quotas on the number of key rings, keys, key versions"
- Before Feb 16, 2026: read "300 QPM", write "60 QPM" per calling project.
- After Feb 16, 2026: read usage "600 TPM", write usage "100 TPM" default per minute (token-based metrics).
- Key versions per key limit: covered by the "no quotas" sentence above; no separate figure.
