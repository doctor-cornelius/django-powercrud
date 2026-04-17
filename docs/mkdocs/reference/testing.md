# Testing PowerCRUD

PowerCRUD ships with an end-to-end test suite that exercises both the Python surface and the sample UI.

## Test commands

```bash
# recommended: full local suite (core + Playwright, coverage, assets)
./runtests

# run one or more focused tests with an appropriate settings module
./runtests src/tests/test_minimal_settings_no_async.py
./runtests src/tests/test_core_phase1.py::test_book_list_shows_add_filter_control_and_hides_optional_filters_by_default src/tests/test_core_phase1.py::test_book_list_renders_visible_optional_filter_from_url_state

# core Python/async suite used in CI (no Playwright)
uv sync --group tests-core
pytest -m "not playwright"

# Playwright UI suite locally (requires built assets + browser deps)
uv sync --group tests-core --group tests-ui
npm ci
npm run build
pytest -m playwright

# UI smoke tests only (Playwright)
pytest -m playwright

# raw pytest (advanced): runs everything with DJANGO_SETTINGS_MODULE=tests.settings
# You are responsible for building assets and having django-q2/qcluster/browsers available.
pytest
```

## Reproducing CI compatibility environments

`pyproject.toml` keeps the published compatibility ranges broad. To reproduce a specific supported Django line exactly as CI installs it, use the constraints files in `requirements/`.

```bash
# Django 4.2 core suite
uv pip install -c requirements/constraints-django42.txt ".[tests-core]"
pytest -m "not playwright"

# Django 5.2 core suite
uv pip install -c requirements/constraints-django52.txt ".[tests-core]"
pytest -m "not playwright"

# Django 5.2 Playwright suite
uv pip install -c requirements/constraints-django52.txt ".[tests-core]" ".[tests-ui]"
npm ci
npm run build
pytest -m playwright
```

Use `uv sync --group ...` for the default local development workflow. Use the constraints files when you need to mirror a specific CI compatibility target.

The Playwright tests target the sample app’s CRUD flows (modal create and bulk selection). Browser binaries are baked into the Docker image; if you are running outside Docker, install them manually:

```bash
playwright install chromium
```

To point Playwright at a different host, set `PLAYWRIGHT_BASE_URL` (defaults to `live_server` during pytest runs).

## Notes

- Tests assume the default sqlite fallback when run locally; Docker builds the full postgres/redis stack used in CI-like environments.
- Playwright requires `DJANGO_ALLOW_ASYNC_UNSAFE=true`, handled automatically via the test fixtures.
- Use markers to focus on areas of interest (e.g. `pytest -m "not playwright"` for headless-free runs).
- `./runtests` is the easiest way to reproduce the CI-like workflow locally: it sets `DJANGO_SETTINGS_MODULE=tests.settings`, resets coverage, builds static assets, and runs the core + Playwright suites in order.
- `./runtests` also accepts multiple explicit pytest node ids or paths in one invocation. When you do that, it auto-selects `tests.settings_minimal` only if every requested path is a minimal-settings test; mixed minimal and regular test selections are rejected unless you set `DJANGO_SETTINGS_MODULE` explicitly.
- Use `requirements/constraints-django42.txt` and `requirements/constraints-django52.txt` when you need to reproduce one exact support-matrix environment rather than the default local workflow.
- A bare `pytest` will use `DJANGO_SETTINGS_MODULE=tests.settings` from `pytest.ini`, but it will not build assets or install browser/OS dependencies; expect Playwright tests (and async/system checks) to fail unless you provision those prerequisites yourself.
- Async-only tests rely on `django_q` (installed via the `tests-core` extras group) and are guarded with `pytest.importorskip("django_q")` so the core suite can be exercised even when async deps are omitted.
- The `tests.settings_minimal` module and `test_minimal_settings_no_async.py` provide a smoke test for importing `PowerCRUDMixin` in a project that never configures async or `POWERCRUD_SETTINGS`.
