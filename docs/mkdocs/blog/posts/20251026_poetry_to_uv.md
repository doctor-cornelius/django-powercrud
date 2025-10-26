---
date: 2025-10-26
categories:
  - poetry
  - uv
---
# Migrating from Poetry to `uv`

May as well get on the bandwagon ;) Also probably better for version management, etc.
<!-- more -->

## Context

PowerCRUD currently relies on Poetry for dependency management, packaging, and the Docker build. The `pyproject.toml`, Dockerfile, and GitHub publish workflow all invoke Poetry commands. Moving to [`uv`](https://github.com/astral-sh/uv) should give faster installs, a simpler CLI, and align with future plans (matrix testing and automated dependency updates).

## Objectives

- Replace Poetry with `uv` for dependency resolution, scripting, and packaging.
- Keep the project publishable to PyPI throughout the transition.
- Update developer tooling (Docker build, docs, scripts) so contributors use `uv`.
- Leave a reversible path until we cut the first release with `uv` in place.

## Constraints & gotchas

- The existing `pyproject.toml` uses `[tool.poetry.*]` sections; we’ll need to migrate to the standard PEP 621 `[project]` metadata and recreate optional dependency groups.
- A new `uv.lock` will replace `poetry.lock`; local docs/tests must sync via `uv sync`.
- The Docker image installs Poetry and runs `poetry install`; we must swap that to install `uv` and run `uv sync` plus `uv run playwright install`.
- GitHub workflows (`publish.yml`) expect Poetry for `poetry build/publish`; we’ll need a uv-friendly publish step (likely `uv build` or `python -m build` + `uv pip`).
- README/testing docs still reference Poetry commands; they must describe the new workflow.
- We must double-check `pip install .` still works for consumers who don’t use uv.

## Migration plan

1. **Rewrite project metadata**
   - Convert `pyproject.toml` to PEP 621 (`[project]`, `[project.optional-dependencies]`, `[tool.uv]` if needed).
   - Recreate dev/test extras that mimic the current Poetry groups.
   - Generate `uv.lock`; drop `poetry.lock`.

2. **Update runtime tooling**
   - Replace Poetry install/commands in `docker/dockerfile_django` with `uv` (`uv sync`, `uv run playwright install --with-deps`).
   - Adjust helper scripts and docs to use `uv run pytest`, etc.
   - Ensure Playwright install still happens during the Docker build.

3. **Refresh GitHub workflows**
   - Modify `publish.yml` to build and upload artifacts without Poetry (use uv’s build step or `python -m build` + `twine` with uv managing deps).
   - Optionally update `deploy_docs.yml` to install MkDocs dependencies via `uv pip` (or leave as plain `pip` if simpler).

4. **Validation**
   - Run `uv sync`, `uv run pytest`, and `uv run pytest -m playwright` on a clean checkout.
   - Build the Docker image to confirm nothing is missing.
   - Test PyPI packaging end-to-end (build wheel/sdist, upload to TestPyPI if necessary).

5. **Communicate & clean up**
   - Update README/index/testing docs to reflect `uv` commands.
   - Remove stray references to Poetry across the repo.
   - Note in the testing roadmap blog post that Poetry→uv migration is complete (once delivered).
