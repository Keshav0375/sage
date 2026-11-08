---
key: "E5-T1"
title: "Deployment config schema + naming module"
epic: "E5"
repo: "Sentinel-infra"
size: "S"
status: "done"
depends_on: ["E5-T0"]
arch_refs: ["deep-dive/09-infra-terraform.md#9.3", "deep-dive/09-1-identity-plane.md#9.9"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 24, "id": 5694991619, "url": "https://github.com/Keshav0375/sentinel-brain/issues/24"}
branch: "dev/infra-phase-5-dynamic-foundations"
pr: "https://github.com/Keshav0375/Sentinel-infra/pull/7"
updated: "2026-11-08"
---

## Summary
Two pieces of machinery every later task depends on.

## Description
Source: infra task 5.1 (`sentinel-brain/implementation/tasks/infra/phase-5-dynamic-foundations/task-1-config-and-naming.md`).

**`azure/config/deployment-config.yaml`** — one file, all deployments, read natively by Terraform:

**A deployment absent from `deployments:` uses `defaults:` entirely.** That is what makes
`deployment: demo1` + `apply` a complete instruction with no file edit — the file is for
exceptions, not enrolment.

**`modules/naming`** — takes `deployment`, `environment`, `location`; returns every resource
name. Azure CAF prefixes, plus `uid = substr(sha1("${subscription}-${deployment}-${env}"), 0, 4)`
for global uniqueness — deterministic, so it is stable across applies and never needs typing.

## Acceptance criteria
- [x] `yamldecode` reads the config; an absent deployment falls back to `defaults` cleanly
- [x] Every generated name satisfies its Azure charset and length rule, verified for an 8-char deployment
- [x] `deployment` longer than 8 chars fails `terraform validate` with an explanatory message
- [x] `uid` is stable across two consecutive plans and differs between environments
- [x] No `0375` string anywhere in the repo

## Outcome
_not yet implemented_
