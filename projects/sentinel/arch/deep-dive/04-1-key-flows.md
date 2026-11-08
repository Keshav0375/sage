> Part of [architecture](../architecture.md) · [diagram](../architecture-diagram.md)
## 4.1 Key flows (sequence diagrams)

### 4.7 Runtime error: full incident response

```mermaid
sequenceDiagram
    autonumber
    actor Human
    participant DEP as Sentinel-deployment
    participant APP as App Service F1
    participant DD as Datadog
    participant EG as Event Grid and bridge
    participant GHA as ci_incident_response
    participant BE as Backend on AKS
    participant PG as Postgres
    participant LF as Langfuse
    Human->>DEP: merge scenario PR runtime/01
    DEP->>APP: build, deploy, verify (green)
    DEP->>PG: INSERT deployments row (Entra token)
    DD->>APP: synthetic GET / every 30 min
    DD->>EG: runtime-health monitor fires
    EG->>GHA: repository_dispatch, signal_type runtime_error, correlation_id
    GHA->>BE: backend-up (aks start if stopped, apply, resolve LB URL)
    par context fetch
        GHA->>PG: service metadata
        GHA->>DEP: PR details (merge sha, head ref)
        GHA->>DD: recent logs
    end
    GHA->>BE: POST /webhooks/incident (Entra bearer)
    BE-->>GHA: 202 incident_id
    BE->>PG: triage, analysis, reflexion, resolution, reverification
    BE->>LF: trace spans and generations
    GHA->>BE: poll GET /incidents/id until terminal
    alt rollback_proposed
        GHA->>BE: GET /incidents/id/rollback-spec
        GHA->>BE: POST /generate/pr-content
        GHA->>DEP: open revert PR (REVERT_PR_PAT)
        GHA->>PG: UPDATE incidents pr_number, pr_url
        GHA->>Human: Teams card, review the revert PR
    else escalated
        GHA->>Human: Teams card with hypothesis, evidence, what is missing
    end
    GHA->>BE: backend-down unless keep-warm
    Human->>DEP: merge or close the revert PR
```

### 4.8 Deploy failure: rollback fast path

The deploy never went live (or a verify-stage failure left the broken version live). The bridge
stamps `deploy_failure`; the orchestrator skips triage and analysis and drafts the rollback spec for
the failed deploy's SHA, which must equal the merge commit in `pr_details.sha` and match a
`deployments` row, then reverifies. Branches that also break `/health` carry
`also_expected: [runtime_error]`: the second alert must correlate to the same deploy.

### 4.9 Deploy record

```mermaid
sequenceDiagram
    participant GHA as ci_app_deployment
    participant AZ as Azure (gha-app OIDC)
    participant APP as App Service
    participant PG as Postgres
    participant DD as Datadog
    GHA->>GHA: build zip (refuses symlinks)
    GHA->>AZ: azure/login as gha-app
    GHA->>APP: az webapp deploy --track-status
    GHA->>APP: verify /health and /version
    GHA->>AZ: get oss-rdbms token
    GHA->>PG: psql INSERT deployments (values only via psql -v)
    GHA->>DD: dd-report event and log, deploy_status succeeded or failed
```

The record stage is `continue-on-error`: a failed record is reported to Datadog as `stage:record`
and never changes `deploy_status`.

### 4.10 Eval run

```mermaid
sequenceDiagram
    participant GHA as ci_eval
    participant K8S as AKS sentinel-dev
    participant JOB as Eval Job (SA sentinel-backend)
    participant LF as Langfuse
    participant PG as Postgres
    GHA->>K8S: backend-up, then scale Deployment to 0 (quota is one pod)
    GHA->>K8S: create Job from azure/k8s/jobs/eval-job.yaml
    JOB->>LF: read dataset sentinel-scenario-runs
    JOB->>JOB: join items to branches.yaml, judge, four checks
    JOB->>LF: create scores
    JOB->>PG: incidents.eval_score
    GHA->>K8S: read report from Job logs between markers
    GHA->>GHA: upload report, emit one eval.scored per branch
    GHA->>K8S: restore per keep-warm (scale to 1 or backend-down)
```
