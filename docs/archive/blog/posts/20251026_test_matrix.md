---
date: 2025-10-26
categories:
    - test
    - uv
---
# Implementing a testing Matrix

This is about implementing a testing matrix approach for running all tests for a matrix of say python vs django versions. I considered using `uv` insteas of `tox` for this.
<!-- more -->

## Objectives

- Guarantee compatibility across the Python/Django combinations we advertise.
- Keep runtimes fast by letting `uv` handle dependency resolution per matrix entry.
- Provide clear, reproducible local commands so contributors can mirror CI.
- Set the stage for future additions (database backends, optional extras).

## Constraints & open questions

- Matrix should cover at least Python 3.12 + 3.13 + 3.14 and Django 4.2 + 5.2 (adjust as release cadence changes).
- Playwright/UI tests add cost; decide whether to run them on every matrix entry or only on the latest pair.
- GitHub-hosted runners are limited; need caching and concurrency limits to avoid timeouts.
- Need a lightweight path for contributors without Docker to run a single matrix cell locally.
- Confirm third-party integrations (q2 worker, Redis) behave consistently across versions.

## Proposed matrix

- **Python versions**: 3.12, 3.13, 3.14 (align with `requires-python` floor and Docker default).
- **Django versions**: 4.2 LTS, 5.2 LTS (current stable); plan to bump as new releases appear.
- **Optional dimension**: `playwright` tag (full UI suite) vs `core` (unit/integration only).

> **Status**: README now documents support for Python 3.12/3.13/3.14 with Django 4.2/5.2; the CI workflow will enforce this grid once built.

## Plan

1. ✅ **Define support policy**
    - ✅ Document the official Python 3.12/3.13/3.14 and Django 4.2/5.2 grid in docs + README so expectations are explicit.
    - ✅ Tie `uv.lock` health to the CI matrix: each matrix job runs `uv sync` against the pinned lock, so failures surface immediately for any Python/Django combo. Release scripts already call `uv lock`, ensuring the lock is refreshed before publishes.

2. ✅ **Refine dependency groups**
    - ✅ Split `pyproject.toml` optional dependencies into logical groups (`tests-core`, `tests-ui`) to reduce redundant installs.
    - ✅ Ensure any Django-specific pins (e.g., `django-template-partials`) resolve cleanly across supported versions.

3. ✅ **Add modular CI workflow**
    - ✅ Create `.github/workflows/run_tests.yml` (manual `workflow_dispatch`) with the Python/Django matrix so we can run the suite on demand.
    - ✅ Configure matrix for Python 3.12/3.13/3.14 × Django 4.2/5.2 (browser suite remains local-only to keep CI lean).
    - ✅ Expose it via `workflow_call` so `publish.yml` can require it before shipping.

4. ✅ **Update existing workflows**
    - ✅ Wire `publish.yml` to depend on the reusable test matrix so releases only ship after the suite passes.
    - ✅ Decide whether docs workflows require any awareness of the matrix (no change needed).

5. ☐ **Local matrix tooling**
    - ✅ Document raw `uv sync` + `pytest` commands so developers can replay each matrix cell locally. Note they cannot run "matrix" cells because that's not how it works. That would be a future [enhancement](../../reference/enhancements.md).

6. ☐ **Validation & rollout**
    - ☐ Trial the matrix on `main` to gather timing data, adjust caching, and tune parallelism.
    - ☐ Once stable, update the testing roadmap blog post with the new guarantees.
    - ☐ Monitor the first few dependency bumps to ensure the matrix catches regressions (dependency sync workflow).
