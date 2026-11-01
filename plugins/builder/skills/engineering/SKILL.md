---
name: engineering
description: Binding engineering standards for builder agents — design principles, configuration knobs, no single point of failure, security, testing protocol, branching and CI. The editor writes to them; the code-reviewer, security-reviewer, runner and verifier check against them. Load before writing or checking code.
---

# Engineering standards (binding for every builder agent)

The project's `arch/` wins where it is more specific. These rules fill everything the arch does
not say. A violation is a finding like any other.

## 1. Design
- One responsibility per module and function. Depend on interfaces at boundaries (repositories,
  clients, providers), so a test or a second implementation can replace them.
- No dead code, no commented-out code, no TODO without a ticket key.
- Errors are typed or explicit. Never swallow an exception; log it with context or return it.
- Pure logic stays separate from I/O, so the logic has fast unit tests.
- Reuse the repo's existing helpers before adding new ones.

## 2. Configuration knobs (one place)
- Every tunable value (timeouts, retries, limits, batch sizes, model names, URLs, feature flags,
  thresholds) lives in the repo's single typed config (for example a pydantic `Settings` class or
  one `config.ts`), with a safe default, and an environment variable override.
- No magic numbers or URLs in the code. A new knob is added to the config, to `.env.example`,
  and to the config docs in the same commit.
- The config is validated at startup: a missing or bad value fails fast with a clear message.

## 3. No single point of failure
- Every network call has a timeout, bounded retries with backoff and jitter, and only retries
  idempotent operations.
- Dependencies that can fail have a fallback or a clear degraded mode (for example, a second
  model provider, a cached answer, or a clear error to the user). Use the fallbacks the arch lists.
- No process-wide mutable state. Services stay stateless, so more than one instance can run.
- Health and readiness checks show the state of the dependencies.
- Background work is idempotent and safe to run again after a crash.

## 4. Security
- No secrets in code, tests, logs or commits. Secrets come from the environment or the secret
  store the arch names.
- Validate all input at the boundary. Use parameterized queries only. Encode output.
- Check authorization on every request path. Deny by default. Respect the tenant and role rules
  of the arch (for example, row-level security).
- Never log personal or financial data in clear text. Mask it.
- Pin new dependencies to an exact version, and only add a dependency that `stack.md` lists.

## 5. Testing protocol
- Tests first: each acceptance criterion has a named test that fails before the change.
- **Unit**: every new branch of logic, the edge cases (empty, null, limits, errors), no network.
- **Integration**: every change that crosses a boundary (database, HTTP API, queue, external
  service) has a test against the real dependency, started the way the repo defines (for example
  docker compose or testcontainers). Mock only third-party services that cost money or are not
  reachable, and say so in the test.
- Tests are deterministic: no sleeps, no real clock, no test order dependence.
- Integration services take their host ports from environment variables with defaults, so two
  worktrees can run them at the same time.
- Never weaken, skip or delete a test to make the run pass.

## 6. Branching and commits
- One ticket = one branch = one PR. Branch name `<type>/<ticket-key>-<slug>`.
- The base is the default branch. A ticket that depends on a ticket still in review branches from
  that ticket's branch, and its PR targets that branch (a stacked PR). Say so in the PR body.
- Commits: `<ticket-key>: <imperative summary>`. No Claude attribution.
- Never force-push, never merge, never push to the default branch.

## 7. Pre-PR validation (all must pass before `brancher mode=ship`)
1. Lint, format check and type check.
2. Unit tests: the changed area, then the full suite.
3. Integration tests for the changed boundaries.
4. Security checks the repo supports: dependency audit (`pip-audit`, `npm audit`), static scan
   (`bandit`, `semgrep`) and a secret scan (`gitleaks`), when installed or defined in CI.
5. After the PR opens, the GitHub Actions checks on it must pass (`gh pr checks --watch`).
   A failed check goes back to the fix loop like a failed local test.

## 8. Continuous integration
- The repo must have a GitHub Actions workflow that runs steps 1-4 on every pull request. If the
  repo has none, the plan's foundation epic (`E0`) adds it before any feature ticket.
