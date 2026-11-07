# Confluent Schema Registry extract (fetched 2026-11-01)
Note: WebFetch returns summarized quotes via a small model; quotes below are as returned, not byte-verified.

## Q1 Soft vs hard delete (https://docs.confluent.io/cloud/current/sr/schemas-delete-cc.md ; platform: .../platform/current/schema-registry/schema-deletion-guidelines.html). No last-updated shown.
- "You can perform a soft delete on all schema versions registered under a subject or on a specific version of a subject."
- "On a soft delete, the API only deletes the version and the underlying schema ID would still be available for any lookup."
- "Simply deleting schemas will not free up space in the registry because this will always result in a soft delete."
- "Confluent Cloud supports "hard delete" of a schema as a two-step process (soft delete, followed by hard delete)."
- "support hard delete of a schema with the use of the query string, `?permanent=true`."
- "A hard delete removes all metadata, including schema IDs."
- "You must first soft delete the schema, then hard-delete it."
- Soft-deleted recoverable: "You can recover a soft-deleted schema using the Schema Registry `GET /subjects` and `POST /subjects` APIs as follows:"
- (search summary, not page-verified) hard delete of a version needs an explicit version number, not "latest".
- Example: curl -X DELETE <sr-url>/subjects/<subject>?permanent=true
- Platform fundamentals page (index.html) does not cover this; it links to schema-deletion-guidelines.html. Dated Apr 11, 2023; Platform 8.4.

## Q2 Cloud supports both?
YES: Cloud page above says "Confluent Cloud supports "hard delete" ..." plus soft delete as default.

## Q3 Packages (https://docs.confluent.io/cloud/current/stream-governance/packages.html, updated Oct 29, 2026)
- Essentials: included count of 100. "Schemas created above this free limit are charged." "Essentials doesn't enforce a cap."
- Advanced: included count of 20,000. "For Advanced, the default cap matches the included count of 20,000."
- "Now, continue with Stream Governance Essentials for free." "Upgrade to Stream Governance Advanced starting at $1/hour."
- Per-schema-per-hour overage rate NOT FOUND on page (refers to pricing page).
- SR on Cloud: "You must opt for either the Essentials or Advanced package to use it." (cloud/current/sr/index.html)

## Q4 CSFLE (https://docs.confluent.io/cloud/current/security/encrypt/csfle/client-side.md, no date; manage-keys.html updated Oct 23, 2026)
- "Stream Governance Advanced package must be enabled."
- KEK: "A master key used to encrypt other keys." DEK: "The key used to encrypt the actual data fields." (DEK encrypted by KEK; DEK Registry stores them)
- Google Cloud KMS listed supported ("Google Cloud Key Management Service (Cloud KMS)"), also Azure Key Vault, HashiCorp Vault (search summary), AWS KMS not confirmed here.
- "There is a limit to the number of existing DEKs (10,000) that can be retained in the DEK Registry"
- Crypto-shred: no explicit "crypto-shredding" term found. Closest: "without KEK access from KMS the data can't be decrypted."; manage-keys: "If your Key Encryption Key (KEK) is lost or compromised, all DEKs encrypted with that KEK become inaccessible."; "Deleting a KEK without properly handling associated DEKs can result in data loss."; "For details on how to delete a KEK, see the documentation for your key management service (KMS)."; "Only users with access to the KEK can decrypt the DEK and access your sensitive data."
- KMS destruction windows: NOT FOUND on these pages.
- Platform CSFLE requires Enterprise license (search summary).
