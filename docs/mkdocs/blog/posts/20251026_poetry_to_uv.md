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

1. ✅ **Rewrite project metadata**
   - ✅ Convert `pyproject.toml` to PEP 621 (`[project]`, `[project.optional-dependencies]`, `[tool.uv]` if needed).
   - ✅ Translate Poetry-specific fields (`readme`, package includes, scripts) into their PEP 621/`tool.hatch` equivalents so `pip install .` keeps working.
   - ✅ Choose a non-Poetry build backend (`hatchling`) and wire it into `[build-system]`.
   - ✅ Recreate dev/test extras that mimic the current Poetry groups.
   - ✅ Generate the first `uv.lock` (after metadata rewrite) and remove `poetry.lock`.

2. ☐ **Update runtime tooling**
   - ✅ Replace Poetry install/commands in `docker/dockerfile_django` with `uv` (`UV_PROJECT_ENVIRONMENT=/usr/local`, preinstall Playwright + browsers before `uv sync` to keep cached layers).
   - ☐ Decide whether to let `uv` manage Python versions locally and inside Docker (potentially swap the base image for an `uv`-managed Python install).
   - ✅ Adjust helper scripts, Docker compose build args, and docs to use `uv …` instead of Poetry.
   - ✅ Ensure Playwright install still happens during the Docker build.

3. ☐ **Refresh GitHub workflows**
   - ✅ Modify `publish.yml` to build and upload artifacts without Poetry (use uv’s build step and `uvx twine`).
   - ✅ Replace `poetry version -s` with a new version-discovery step (inline Python using `tomllib`).
   - ☐ Optionally update `deploy_docs.yml` to install MkDocs dependencies via `uv pip` (or leave as plain `pip` if simpler).

4. ☐ **Validation**
   - ✅ Run `pytest` (coverage-enabled) inside the container to confirm dependencies resolve.
   - ☐ Build the Docker image to confirm nothing is missing.
   - ☐ Test PyPI packaging end-to-end (build wheel/sdist, upload to TestPyPI if necessary).

5. ☐ **Communicate & clean up**
   - ✅ Update README/index/testing docs to reflect `uv` commands.
   - ☐ Remove stray references to Poetry across the repo.
   - ☐ Note in the testing roadmap blog post that Poetry→uv migration is complete (once delivered).
