# Risk Assessment

## Release Risk Summary

Overall risk: High.

The main production risk is not missing functionality; it is insufficient release confidence. The system has working architectural foundations, but failing tests, broken linting, incomplete CI, and unverified Docker runtime behavior make a production release unsafe.

## Critical Risks

1. Broken full test suite
   - Impact: release may ship known regressions in warehouse, metadata, Excel adapter, and golden dataset behavior.
   - Likelihood: confirmed.
   - Mitigation: fix the failing tests or code paths before release.

2. Red CI path
   - Impact: main branch cannot provide a trustworthy release signal.
   - Likelihood: confirmed because CI runs `pytest` and `pytest` currently fails.
   - Mitigation: restore green CI and make it required.

## High Risks

1. Incomplete security hardening
   - Impact: weak deployment configuration may expose docs, default secrets, or weak password storage patterns.
   - Likelihood: medium.
   - Mitigation: require explicit production secrets, document hashed passwords only, and consider disabling docs/OpenAPI in production.

2. Docker runtime not verified
   - Impact: container may fail during dependency install, migration, startup, healthcheck, or runtime permissions.
   - Likelihood: medium.
   - Mitigation: add Docker build and smoke test to CI.

3. Broken frontend lint
   - Impact: TypeScript build catches type errors, but style/hook/rule regressions are not checked.
   - Likelihood: confirmed.
   - Mitigation: add ESLint 9 flat config or downgrade/configure linting explicitly.

4. Legacy Flask API ambiguity
   - Impact: operators may start the wrong API from README and expose debug mode.
   - Likelihood: medium.
   - Mitigation: remove, archive, or document the legacy module as non-production.

## Medium Risks

1. SQLite default persistence
   - Impact: limited concurrency, backup, and operational scaling profile.
   - Likelihood: medium for daily multi-user operations.
   - Mitigation: define production database target and migration/backup procedures.

2. Broad dependency ranges
   - Impact: future installs can drift and break tests, as shown by openpyxl API incompatibilities.
   - Likelihood: high.
   - Mitigation: lock dependencies and run scheduled dependency updates.

3. Browser-local operational history
   - Impact: Beta 1.1 operational execution records are local to the browser and not system-of-record durable.
   - Likelihood: high if used operationally across users.
   - Mitigation: plan a future API-backed execution workflow without changing current v1.0 contract.

4. Large frontend bundle
   - Impact: slower first load on constrained machines or remote access.
   - Likelihood: medium.
   - Mitigation: code splitting and chart library chunking.

## Low Risks

1. Documentation drift
   - Impact: onboarding and operations confusion.
   - Likelihood: high.
   - Mitigation: update README and frontend README before release.

2. Local generated artifacts
   - Impact: accidental packaging noise.
   - Likelihood: low if `.gitignore` remains effective.
   - Mitigation: clean release workspace before tagging.

## Risk Decision

Production release risk is above acceptable threshold.

Decision: NO GO.
