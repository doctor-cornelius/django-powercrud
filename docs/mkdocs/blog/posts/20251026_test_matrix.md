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

- Matrix should cover at least Python 3.12 + 3.13 and Django 4.2 + 5.1 (adjust as release cadence changes).
- Playwright/UI tests add cost; decide whether to run them on every matrix entry or only on the latest pair.
- GitHub-hosted runners are limited; need caching and concurrency limits to avoid timeouts.
- Need a lightweight path for contributors without Docker to run a single matrix cell locally.
- Confirm third-party integrations (q2 worker, Redis) behave consistently across versions.

## Proposed matrix

- **Python versions**: 3.12, 3.13 (align with `requires-python` floor and Docker default).
- **Django versions**: 4.2 LTS, 5.0/5.1 (current stable); plan to bump as new releases appear.
- **Optional dimension**: `playwright` tag (full UI suite) vs `core` (unit/integration only).

## Plan

1. ☐ **Define support policy**
    - ☐ Document the official Python/Django version grid in `docs/mkdocs/blog/posts/20251026_test_matrix.md` and surface it in README.
    - ☐ Add safeguards so `uv.lock` stays compatible with each supported combo (e.g., resolver checks or per-cell lock snapshots).

2. ☐ **Refine dependency groups**
    - ☐ Split `pyproject.toml` optional dependencies into logical groups (`tests-core`, `tests-ui`) to reduce redundant installs.
    - ☐ Ensure any Django-specific pins (e.g., `django-template-partials`) resolve cleanly across supported versions.

3. ☐ **Update CI workflows**
    - ☐ Convert the publish workflow into a reusable job or composite action that accepts Python/Django inputs.
    - ☐ Introduce a dedicated `tests.yml` workflow with a `strategy.matrix` covering Python/Django, caching `.uv` and Playwright assets per cell.
    - ☐ Decide which cells run the Playwright suite vs the core suite; document the rationale.

4. ☐ **Local matrix tooling**
    - ☐ Provide `uv run` snippets (or a Makefile) that let developers execute a single matrix cell locally.
    - ☐ Update docs to explain how to run `pytest` with `DJANGO_SETTINGS_MODULE` overrides per Django version if needed.

5. ☐ **Validation & rollout**
    - ☐ Trial the matrix in CI to gather timing data, adjust caching, and tune parallelism.
    - ☐ Once stable, update the testing roadmap blog post with the new guarantees.
    - ☐ Monitor the first few dependency bumps to ensure the matrix catches regressions (dependency sync workflow).
