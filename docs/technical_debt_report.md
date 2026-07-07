# Technical Debt Report

## Summary

The repository has a strong domain-oriented foundation, but production readiness is held back by test drift, dependency drift, legacy entry points, incomplete CI, and documentation drift.

## Critical Debt

1. Test suite drift
   - Full suite currently fails with 6 failures.
   - Failures indicate incompatible assumptions in warehouse amount handling, openpyxl defined names, and path normalization.

2. CI release gate debt
   - CI currently runs only backend pytest.
   - Because pytest fails, CI is not a usable release gate.

## High Debt

1. Frontend quality tooling debt
   - `npm run lint` exists but cannot run with ESLint 9 because no flat config exists.

2. Legacy API debt
   - `src/api/app.py` is a Flask API with `debug=True`.
   - Root README still points to it instead of the FastAPI production API.

3. Deployment verification debt
   - Dockerfile and Compose are present, but no Docker build/runtime validation was executable in the audit environment.
   - CI does not perform Docker build or smoke tests.

4. Security configuration debt
   - Development fallback secret remains in code.
   - Plain-text password configuration is supported.
   - Production docs/OpenAPI exposure is not environment-controlled.

## Medium Debt

1. Dependency management debt
   - Python dependencies are broad lower bounds.
   - No Python lock file or hash checking is present.
   - Frontend dependencies use semver ranges.

2. Persistence scalability debt
   - SQLite default is simple and useful locally, but not a strong production default for concurrent controllership workflows.

3. Frontend operational durability debt
   - Beta 1.1 execution history and validation data are browser-local.
   - This is acceptable for product-layer workflow demonstration but not for durable enterprise audit history.

4. Warning debt
   - Python 3.14 emits many `datetime.utcnow()` deprecation warnings.

5. Bundle debt
   - Frontend build reports chunks larger than 500 kB.

## Low Debt

1. Documentation drift
   - Root README is legacy.
   - Frontend README authentication storage note is outdated.

2. Debug helper debt
   - `tests/unit/debug_pipeline_runner.py` remains in the test tree.

3. Release workspace hygiene
   - Local generated files exist but appear ignored/untracked.

## Recommended Remediation Order

1. Restore full test suite.
2. Fix frontend lint configuration and add it to CI.
3. Add frontend build and npm audit to CI.
4. Add Docker build and healthcheck smoke test to CI.
5. Remove or quarantine legacy Flask API.
6. Harden production security configuration.
7. Lock dependencies.
8. Update README files.
9. Address Python 3.14 deprecation warnings.
10. Plan API-backed operational execution persistence for a post-v1.0 release.
