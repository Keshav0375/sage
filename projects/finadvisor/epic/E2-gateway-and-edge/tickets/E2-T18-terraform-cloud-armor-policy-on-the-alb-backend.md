---
key: "E2-T18"
title: "Terraform: Cloud Armor policy on the ALB backend service"
epic: "E2"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E2-T8", "E2-T10"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.2", "decision-logs.md#adr-012"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 56, "id": 6155637383, "url": "https://github.com/Keshav0375/FinAdvisor/issues/56"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Attach DDoS/WAF/geo rules and a coarse per-IP throttle to the gateway backend service.

## Description
Overview 4.2 and ADR-012. Quote 4.2: 'Policy attached to the ALB backend services: DDoS / WAF preconfigured rules, geo rules, coarse per-IP throttle. Kong keeps the fine-grained limits; Cloud Armor keeps DDoS / WAF / geo.' In terraform/edge/: a google_compute_security_policy with the rule set sized in E2-T10, attached to the fa-gateway backend service (the backend bucket cannot take a backend-service policy; note it). Geo allow-list and the throttle threshold are variables (question 11); the throttle must be looser than Kong's limits. Out of scope: Kong limits.

## Acceptance criteria
- [ ] Given `terraform plan`, then the policy lists the WAF rules named in E2-T10, a geo rule, a throttle rule with a variable threshold and a default allow; `gcloud compute security-policies describe` after apply matches.
- [ ] Given a request through the ALB with query q=' OR 1=1-- , then the response is 403 from Cloud Armor, not Kong's (no Kong Via header).
- [ ] Given 10 benign advisor-style chat messages (fund names, words such as select, drop, union in prose) POSTed through the ALB, then none is blocked by Cloud Armor (0 of 10 return 403); any block is reported as a rule exclusion decision.
- [ ] Given more requests per minute from one IP than the throttle threshold, then Cloud Armor returns 429.
