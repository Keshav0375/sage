---
key: "E10-T6"
title: "Terraform Cloud SQL (PG16, PSC, no public IP, profile HA flag)"
epic: "E10"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E10-T4", "E2-T4", "E2-T5", "E2-T8", "E2-T18", "E2-T19"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.9", "deep-dive/08-security-and-privacy.md#8.3", "ADR-020", "ADR-024"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Provision Cloud SQL PostgreSQL 16 via PSC with private-only access, the connection limit flag and ignore_changes on activation_policy.

## Description
Implements 4.9 and 8.3 ('Cloud SQL: Private IP via PSC; no public IPv4 (fixes G-26)') and ADR-020 ('Cloud SQL Enterprise 2 vCPU / 8 GiB ~101 USD while running (HA ~202)'; 'HA is a Terraform flag for load tests'). Read deep-dive/11-tech-stack.md for the exact PostgreSQL version (16) and the pgvector 0.8.5 note: the extension is created by the migrate job (E1), not here.

Build terraform/cloud_sql.tf (replace the MVP file): google_sql_database_instance, database_version POSTGRES_16, edition ENTERPRISE, tier for 2 vCPU / 8 GiB (db-custom-2-8192), ip_configuration with ipv4_enabled = false and psc_config enabled with allowed consumer project, PSC endpoint (forwarding rule + address) in the E2 VPC subnet and a DNS record or hostname output used for DB_HOST; database_flags max_connections=400; availability_type = REGIONAL when env_profile = prod else ZONAL; deletion_protection true in prod; lifecycle { ignore_changes = [settings[0].activation_policy] }; initial activation_policy ALWAYS at first apply (the demo scripts flip it afterwards). Outputs: instance name, PSC endpoint address. Backups/PITR: see questions.

Out of scope: roles and databases (E10-T7).

## Acceptance criteria
- [ ] `terraform plan` (checked by a policy test, conftest or terraform test) fails if ip_configuration.ipv4_enabled is true; it passes on the tree
- [ ] Plan output for env_profile=demo shows availability_type ZONAL and for prod shows REGIONAL (two terraform test cases)
- [ ] After applying, `gcloud sql instances describe` shows databaseFlags max_connections=400 and no PUBLIC address in ipAddresses
- [ ] After `gcloud sql instances patch --activation-policy=NEVER`, `terraform plan -detailed-exitcode` returns 0 (ignore_changes works)
