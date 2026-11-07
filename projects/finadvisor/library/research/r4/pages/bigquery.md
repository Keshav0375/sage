# BigQuery extract (fetched 2026-11-02; sources redirected to docs.cloud.google.com)
Note: WebFetch returns small-model paraphrase-filtered text; quotes are as returned by the fetcher.

## Q1 AEAD + Cloud KMS wrapped keysets, crypto-shredding
URL: https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/aead_encryption_functions (Last updated 2026-10-27 UTC)
- KEYS.NEW_WRAPPED_KEYSET: "Creates a new keyset and encrypts it with a Cloud KMS key."
- "The Cloud KMS key must reside in the same Cloud region where this function is executed."
- KEYS.REWRAP_KEYSET: "Re-encrypts a wrapped keyset with a new Cloud KMS key." / "During this process, the decrypted keyset is never visible to customers."
URL: https://docs.cloud.google.com/bigquery/docs/column-key-encrypt (Last updated 2026-10-27 UTC)
- "A user must be granted permission to both the table and the encryption key to read data in cleartext."
- "It is not possible to rotate a wrapped keyset using the `KEYS.ROTATE_KEYSET` function."
Crypto-shredding / deleting key or keyset: NOT FOUND (no statement on either page; fetcher-reported, aead page read in full across two chunks).

## Q2 DML DELETE limits, streaming buffer, partition delete
URL: https://docs.cloud.google.com/bigquery/docs/data-manipulation-language (Last updated 2026-10-28 UTC)
- "BigQuery runs up to 2 of them concurrently, after which up to 20 are queued as `PENDING`." (mutating: UPDATE, DELETE, MERGE)
- "Queued mutating DML statements share a per-table queue with maximum length 20." Beyond: "Too many DML statements outstanding against table".
- "These rates do not limit the total number of DML statements that can be run." (no specific DELETE quota stated)
- Streaming: "The recent writes are those that occurred within the last 30 minutes."
URL: https://docs.cloud.google.com/bigquery/docs/write-api (no date shown)
- "You can use data manipulation language (DML), such as the `UPDATE`, `DELETE`, or `MERGE` statements, to modify rows" (fetcher truncated sentence)
- "Recent writes are those that occurred within the last 30 minutes."
- "Running mutating DML statements within a multi-statement transaction against recently streamed data is unsupported."
- Note: page does not use "streaming buffer"; fetcher's reading of DML page says recent writes cannot be modified by DML for a while (exact sentence not captured; ambiguous vs write-api page, verify).
Partition-level delete vs DROP partition: for fine-grained DML tables, "A table enabled with fine-grained DML can't have partitions individually deleted or overwritten." DROP-partition comparison for standard tables: NOT FOUND.

## Q3 Cost of DELETE
- "Enabling fine-grained DML won't reduce the amount of scanned bytes of the DML statement itself."
- Standard DML bytes computed by "DML sizing rules" for on-demand; capacity pricing: mutating statements consume slots. Exact bytes-processed formula for DELETE: NOT FOUND in captured text.

## Q4 Time travel
NOT FOUND on these pages (DML page: "doesn't address time travel").
