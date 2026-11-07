# GCS extract (fetched 2026-11-01; all four pages "Last updated 2026-10-30 UTC")
Note: cloud.google.com URLs 301-redirect to docs.cloud.google.com (same path). Quotes below come from WebFetch summaries (small-model extraction), not raw page text.

## Q1 Soft delete  https://cloud.google.com/storage/docs/soft-delete
- (Soft delete policies) "Soft delete is enabled by default for all buckets that support it, with a default retention duration of 7 days."
- "you can customize the retention duration between 7 days and 90 days."
- "To disable soft delete, you set the retention duration to 0."  (so 0 allowed = disabled)
- (Overview) "During this time, the object or bucket can't be permanently deleted and can be restored."
- (Properties of soft-deleted resources) "The only supported operations are listing them or restoring them."
- Early purge: page describes no method to purge before retention ends. (Not stated either way beyond the above.)

## Q2 Object versioning  https://cloud.google.com/storage/docs/object-versioning
- "Cloud Storage retains a noncurrent object version each time you replace or delete a live object version"
- "Noncurrent versions only appear in requests that explicitly call for them to be included."
- "You delete a noncurrent version of an object by including the generation number in the deletion request"; also via Object Lifecycle Management.
- "A soft-deleted object is permanently deleted after its soft delete retention period expires."
- "configure the Object Lifecycle Management policy to automatically delete noncurrent versions"
- "We recommend that you use soft delete instead of Object Versioning to protect against permanent data loss"; "Object Versioning does not provide protection against bucket deletions."; both can be enabled on same bucket.
- "Each noncurrent version of an object is charged at the same rate it was when it was live."
- daysSinceNoncurrentTime / numNewerVersions: NOT FOUND on this page (only general lifecycle mention).

## Q3 Retention policy / lock  https://cloud.google.com/storage/docs/bucket-lock
- Objects "cannot be deleted or replaced until they reach the age you define in the policy."
- "Once you lock a policy, you cannot remove it or reduce the retention period it has."
- "You can increase the retention period of a locked policy."
- "Locking a bucket's retention policy is irreversible"
- "You cannot delete a bucket with a locked policy unless every object in the bucket has met the retention period."
- "You can set a maximum retention period of 3,155,760,000 seconds (100 years)." No minimum stated.

## Q4 Lifecycle  https://cloud.google.com/storage/docs/lifecycle
- (age) "The age condition is satisfied when a resource reaches the specified age (in days)."  Day granularity.
- "regularly inspects all the objects" (no explicit "daily" statement per fetch).
- "Cloud Storage performs an action asynchronously"
- "Your applications shouldn't rely on lifecycle actions occurring within a certain amount of time" after condition met.
- Config changes can take up to 24 hours to take effect (paraphrase from fetch, not verbatim-confirmed).
- "Applicable charges still apply while the object remains in its original state."

## Q5 CMEK key destroy effect
NOT FOUND in the four assigned sources (lifecycle and versioning pages do not mention it).
Extra page tried: docs.cloud.google.com/storage/docs/encryption/using-customer-managed-keys; first 100000 of 154472 chars had no destroy/disable passage; remaining 54472 chars unread (offset 100000). Not an assigned source.
