# Langfuse data deletion extract
Source: https://langfuse.com/docs/administration/data-deletion (fetched 2026-11-01). Alt URL /docs/api-and-data-platform/features/data-deletion = 404.
Page date/version: none shown. References Langfuse v4+ (self-hosted session deletion), v3.117.0+ (self-service account deletion).
Caveat: fetched via WebFetch (small-model summarizer); quotes should be re-verified against the live page before being load-bearing.

## Q1 Endpoints
- "Note that all trace deletions will delete related entities like scores and observations across all data storages."
- Single: DELETE /api/public/traces/{traceId}
- Batch: DELETE /api/public/traces, body {"traceIds": [...]}
- Sessions: "To delete a session's traces, retrieve their IDs and pass them to the existing batch deletion endpoint:" (GET /api/public/v2/observations to find trace IDs, then DELETE /api/public/traces). No dedicated session/score/observation delete endpoint stated. "This workflow does not block future data for the same `sessionId`."
- "It does not remove personal data that may also be stored in other objects, such as datasets."

## Q2 Timing
- "Most deletions in Langfuse happen instantly, but the deletion of tracing data does not."
- "Usually, trace data is deleted from our system within 15 minutes of the delete call."
- "There is no deletion confirmation or notification; to verify that your data got deleted, query it again."
- Session workflow: "It is asynchronous; see deletion limitations for timing and verification."
- ClickHouse / S3 blob / backups: NOT FOUND (not mentioned on page).

## Q3 Project / org deletion
- "This action immediately revokes all API keys and schedules the project for deletion."
- "Project deletion is asynchronous, and the time it takes scales with the size of the project."
- "For very large projects, deletion can take multiple days."
- "Deleting a project is irreversible and all data will be removed."
- Org: "Only organization owners can delete an organization" (after projects deleted/transferred); "The organization and all associated user information will be removed from our system."; error "Deletion of your projects is still being processed, please try deleting the organization later"
- Account deletion: org/projects/data "are not deleted".
- Alternative: Data Retention "automatically deletes traces, observations, scores, and media assets older than a configured number of days."

## Q4 Limits
- "we rate limit how many deletions we process at any point in time." No numeric rate limit or max batch size documented (example script batches at 1,000 trace IDs by its own choice).
- Cloud Observations API v2 read window (affects session-deletion lookup): 30 days Hobby, 90 days Core; Pro/Team/Enterprise/self-hosted no limit.

## Q5 Plan availability
- Session deletion: Hobby, Core, Pro, Enterprise "Available"; Self Hosted "Langfuse v4+".
- Trace deletion API plan gating: NOT FOUND (no restriction stated).
