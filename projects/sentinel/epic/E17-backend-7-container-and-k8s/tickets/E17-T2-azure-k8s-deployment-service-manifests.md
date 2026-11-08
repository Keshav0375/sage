---
key: "E17-T2"
title: "azure/k8s/ deployment + service manifests"
epic: "E17"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: ["E17-T1", "E15-T4", "E3-T1"]
arch_refs: ["deep-dive/07-backend-hosting-and-ci.md#7.2", "deep-dive/07-backend-hosting-and-ci.md#7.3", "deep-dive/00-mvp-phase-1-and-the-pivot.md#0.4"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 84, "id": 5695000908, "url": "https://github.com/Keshav0375/sentinel-brain/issues/84"}
branch: "dev/backend-phase-7-container-and-k8s"
pr: "https://github.com/Keshav0375/Sentinel/pull/26"
updated: "2026-11-08"
---

## Summary
The K8s manifests the backend-up action applies. Single replica; Service is created/deleted

## Description
Source: backend task 7.2 (`sentinel-brain/implementation/tasks/backend/phase-7-container-and-k8s/task-2-k8s-manifests.md`).

per run (dynamic URL, §8.5).

**Files created:**
- `azure/k8s/deployment.yaml` — Deployment `sentinel-backend`, `replicas: 1`, `strategy: Recreate`, image `sentinelacr.azurecr.io/sentinel-backend:sha-PLACEHOLDER` (CI sets via `kubectl set image`), `envFrom: sentinel-secrets`, readiness `/ready` (initialDelay 10), liveness `/health` (initialDelay 15), resources requests 250m/512Mi limits 1/2Gi.
- `azure/k8s/service.yaml` — `Service type: LoadBalancer`, selector app=sentinel-backend, port 80→8000.

## Acceptance criteria
- [x] `kubectl apply --dry-run=client -f azure/k8s/` validates both manifests.
- [x] Probes point at `/ready` + `/health`; envFrom the K8s Secret; Recreate strategy (never 2 pods on the 4 GB node).
- [x] A `NetworkPolicy` allowing ingress to the backend pods on the service port from the LoadBalancer and from the AKS health probes. The cluster enforces the namespace's `default-deny-ingress` via Cilium (infra PR #16, 2026-10-05), so without this rule `/health` is unreachable through the LB.

## Outcome
Built in 830bf34 "feat: azure/k8s manifests (deployment, service, configmap, networkpolicy)" on dev/backend-phase-7-container-and-k8s.
Files: azure/k8s/{deployment,service,configmap,networkpolicy}.yaml, azure/k8s/placeholders.txt (envsubst var list + recipe), tests/test_infra/test_k8s_manifests.py (25 tests).
No serviceaccount.yaml (infra owns SA sentinel-backend); no namespace in manifests, so pass -n sentinel-dev. Deployment: Recreate, 1 replica, WI label, grace 45s, /ready 10s + /health 15s probes, 250m/512Mi req, 1/2Gi limits, non-root, drop ALL. ConfigMap non-secret only; NetworkPolicy allows TCP 8000. kubectl dry-run=client (orbstack) passed.
Unverified live: startup time vs liveness budget (no startupProbe); B1 estate down. Decisions: dd95eef.
Review fixes 1729dbf (2026-10-24): automountServiceAccountToken false; readOnlyRootFilesystem true with emptyDir mounts for /app/reports and /tmp. Unverified live: automountServiceAccountToken=false combined with workload identity. Gate VERDICT GREEN on 1729dbf (full run, 7 ran, 0 skipped); boot OK. Decisions: dd95eef, b384323.
