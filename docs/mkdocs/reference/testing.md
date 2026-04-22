# Testing PowerCRUD

PowerCRUD ships with an end-to-end test suite that exercises both the Python surface and the sample UI.

The project now uses a three-layer testing model:

- Local and release preparation: run the full suite with `./runtests`, including the full Playwright browser regression set.
- Blocking CI browser coverage: run a curated `playwright_smoke` subset that covers core CRUD, inline editing, favourites, bulk selection, row actions, and tooltip reinitialisation.
- Broader browser regression coverage: run the full Playwright suite separately from the smoke gate when you want deeper browser validation without making every nuanced browser interaction a merge blocker.

## Test commands

```bash
# recommended: full local suite (core + Playwright, coverage, assets)
./runtests

# run one or more focused tests with an appropriate settings module
./runtests src/tests/test_minimal_settings_no_async.py
./runtests src/tests/test_core_phase1.py::test_book_list_shows_add_filter_control_and_hides_optional_filters_by_default src/tests/test_core_phase1.py::test_book_list_renders_visible_optional_filter_from_url_state
./runtests --playwright src/tests/playwright/test_bulk_selection.py::test_bulk_selection_toggle
./runtests --rebuild-assets src/tests/playwright/test_filter_favourites.py::test_filter_reset_clears_remembered_selected_favourite

# core Python/async suite used in CI (no Playwright)
uv sync --group tests-core
pytest -m "not playwright"

# full Playwright UI suite locally (requires built assets + browser deps)
uv sync --group tests-core --group tests-ui
npm ci
npm run build
pytest -m playwright

# blocking browser smoke subset used in CI
pytest -m playwright_smoke

# raw pytest (advanced): runs everything with DJANGO_SETTINGS_MODULE=tests.settings
# You are responsible for building assets and having django-q2/qcluster/browsers available.
pytest
```

## Reproducing CI compatibility environments

Use the constraints file in `requirements/` when you want to reproduce the exact supported Django line that CI installs.

```bash
# Django 5.2 core suite
uv pip install -c requirements/constraints-django52.txt ".[tests-core]"
pytest -m "not playwright"

# Django 5.2 Playwright smoke subset
uv pip install -c requirements/constraints-django52.txt ".[tests-core]" ".[tests-ui]"
npm ci
npm run build
pytest -m playwright_smoke

# Django 5.2 full Playwright suite
uv pip install -c requirements/constraints-django52.txt ".[tests-core]" ".[tests-ui]"
npm ci
npm run build
pytest -m playwright
```

Use `uv sync --group ...` for the default local development workflow. Use the constraints file when you need to mirror the exact CI compatibility target.

The Playwright tests target the sample app’s CRUD flows, inline editing, favourites, row-action menus, and tooltip lifecycle. Browser binaries are baked into the Docker image; if you are running outside Docker, install them manually:

```bash
playwright install chromium
```

To point Playwright at a different host, set `PLAYWRIGHT_BASE_URL` (defaults to `live_server` during pytest runs).

## Notes

- Tests assume the default sqlite fallback when run locally; Docker builds the full postgres/redis stack used in CI-like environments.
- Playwright requires `DJANGO_ALLOW_ASYNC_UNSAFE=true`, handled automatically via the test fixtures.
- Use markers to focus on areas of interest:
  - `pytest -m "not playwright"` for headless-free runs
  - `pytest -m playwright_smoke` for the curated browser smoke subset
  - `pytest -m playwright` for the full browser suite
- `./runtests` is the easiest way to reproduce the intended local workflow: it sets `DJANGO_SETTINGS_MODULE=tests.settings`, resets coverage, builds static assets when needed, and runs the core + Playwright suites in order.
- `./runtests --playwright <node-id>` lets you run a focused Playwright subset while still forcing the normal test settings and browser marker selection.
- `./runtests --rebuild-assets <node-id>` is useful when debugging frontend flakes or asset-sensitive browser failures and you want to force a fresh bundle before a focused run.
- `./runtests` also accepts multiple explicit pytest node ids or paths in one invocation. In plain path mode it auto-selects `tests.settings_minimal` only if every requested path is a minimal-settings test; mixed minimal and regular test selections are rejected unless you set `DJANGO_SETTINGS_MODULE` explicitly.
- Use `requirements/constraints-django52.txt` when you need to reproduce the exact support-matrix environment rather than the default local workflow.
- A bare `pytest` will use `DJANGO_SETTINGS_MODULE=tests.settings` from `pytest.ini`, but it will not build assets or install browser/OS dependencies; expect Playwright tests (and async/system checks) to fail unless you provision those prerequisites yourself.
- Async-only tests rely on `django_q` (installed via the `tests-core` extras group) and are guarded with `pytest.importorskip("django_q")` so the core suite can be exercised even when async deps are omitted.
- The `tests.settings_minimal` module and `test_minimal_settings_no_async.py` provide a smoke test for importing `PowerCRUDMixin` in a project that never configures async or `POWERCRUD_SETTINGS`.
- GitHub Actions blocks on the curated `playwright_smoke` subset. The full Playwright suite is still intended for local runs, release preparation, and optional manual GitHub Actions runs when you want the extra browser signal.
