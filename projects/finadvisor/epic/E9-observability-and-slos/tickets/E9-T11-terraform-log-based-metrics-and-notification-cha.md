---
key: "E9-T11"
title: "Terraform: log-based metrics and notification channel"
epic: "E9"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E9-T5"]
arch_refs: ["deep-dive/09-observability.md#9.2", "deep-dive/09-observability.md#9.5"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Terraform defines the log-based metrics and the alert notification channel used by all dashboards and alert policies.

## Description
Implements deep-dive/09-observability.md §9.2 "log-based and OTel, in Cloud Monitoring" for metrics emitted as log lines (event='metric', E9-T5), and creates the notification channel the alerts in 9.5 use. Existing terraform/ has main.tf, cloud_run.tf, variables.tf; add terraform/monitoring.tf.
- google_logging_metric (distribution or counter, label extractors on metric and labels) for every 9.2 metric that is emitted by log line; metrics emitted over OTLP need no resource here.
- google_monitoring_notification_channel (email) with the address from a variable alert_email (required).
- Variables env_profile (matches ENV_PROFILE) used by later tickets.
Out of scope: dashboards (E9-T12), SLOs (E9-T13), alert policies (E9-T14, E9-T15).
Notification channel: email to alert_email (R75).

## Acceptance criteria
- [ ] Given terraform validate and terraform plan -var-file=ci.tfvars, When run in CI, Then both succeed with no errors.
- [ ] Given the plan output, When listed, Then one google_logging_metric exists for each name in the E9-T5 registry that is log-emitted and the notification channel exists (a script scripts/check_monitoring_tf.py compares names to the registry and fails on a gap).
- [ ] Given a log line event='metric', metric='rerank_ms', value=412, When tested against the metric's filter with gcloud logging read in the drill (E9-T17), Then it matches and the extractor yields 412.
- [ ] Given alert_email unset, When terraform plan, Then it errors (required variable).
