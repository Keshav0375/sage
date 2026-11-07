---
key: "E10-T6"
title: "Terraform Cloud SQL (PG16, PSC, no public IP, profile HA flag)"
epic: "E10"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E10-T4", "E2-T4", "E2-T5", "E2-T8", "E2-T18", "E2-T19"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.9", "deep-dive/08-security-and-privacy.md#8.3", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.14", "decision-logs.md#adr-020", "decision-logs.md#adr-024", "decision-logs.md#adr-029", "decision-logs.md#adr-039"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 254, "id": 6263676564, "url": "https://github.com/Keshav0375/FinAdvisor/issues/254"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Provision Cloud SQL PostgreSQL 16 via PSC with private-only access, the connection limit flag, ignore_changes on activation_policy, 7-day backups and 7-day PITR log retention.

## Description
Implements 4.9 and 8.3 ('Cloud SQL: Private IP via PSC; no public IPv4 (fixes G-26)') and ADR-020 ('Cloud SQL Enterprise 2 vCPU / 8 GiB ~101 USD while running (HA ~202)'; 'HA is a Terraform flag for load tests'). Read deep-dive/11-tech-stack.md for the exact PostgreSQL version (16) and the pgvector 0.8.5 note: the extension is created by the migrate job (E1), not here.

Build terraform/cloud_sql.tf (replace the MVP file): google_sql_database_instance, database_version POSTGRES_16, edition ENTERPRISE, tier for 2 vCPU / 8 GiB (db-custom-2-8192), ip_configuration with ipv4_enabled = false and psc_config enabled with allowed consumer project, PSC endpoint (forwarding rule + address) in the E2 VPC subnet and a DNS record or hostname output used for DB_HOST; database_flags max_connections=400; availability_type = REGIONAL when env_profile = prod else ZONAL; deletion_protection true in prod; lifecycle { ignore_changes = [settings[0].activation_policy] }; initial activation_policy ALWAYS at first apply (the demo scripts flip it afterwards).

Retention (round 4, ADR-029; 5.14 "Cloud SQL backups: 7 d; no on-demand backups kept; PITR log retention set to 7 d (Enterprise range 1-7 d)"): `backup_configuration { enabled = true, point_in_time_recovery_enabled = true, transaction_log_retention_days = 7, backup_retention_settings { retained_backups = 7, retention_unit = "COUNT" } }` with daily automated backups (7 backups = 7 days), driven by variables `sql_backup_retained_days` and `sql_pitr_log_days` whose validation rejects values above 7 (the Enterprise PITR range is 1-7). The Terraform code creates no on-demand backup and the runbook says none are kept. Whether old backups expire while the instance is stopped is the E12 spike (E12-T1), not tested here; this ticket only provides the non-prod instance that spike uses. Outputs: instance name, PSC endpoint address.

Out of scope: roles and databases (E10-T7), the retention checker (E10-T26), the restore drill (E10-T28).

## Acceptance criteria
- [ ] `terraform plan` (checked by a policy test, conftest or terraform test) fails if ip_configuration.ipv4_enabled is true; it passes on the tree
- [ ] Plan output for env_profile=demo shows availability_type ZONAL and for prod shows REGIONAL (two terraform test cases)
- [ ] Plan JSON shows `backup_configuration.enabled` true, `point_in_time_recovery_enabled` true, `transaction_log_retention_days` 7 and `retained_backups` 7; setting `sql_pitr_log_days = 8` makes `terraform plan` fail on the validation block (terraform test)
- [ ] After applying, `gcloud sql instances describe` shows databaseFlags max_connections=400, no PUBLIC address in ipAddresses, backupRetentionSettings.retainedBackups 7 and transactionLogRetentionDays 7
- [ ] After `gcloud sql instances patch --activation-policy=NEVER`, `terraform plan -detailed-exitcode` returns 0 (ignore_changes works)
