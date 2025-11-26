# Testing PowerCRUD

PowerCRUD ships with an end-to-end test suite that exercises both the Python surface and the sample UI.

## Test commands

```bash
# recommended: full local suite (core + Playwright, coverage, assets)
./runtests

# run a single test file with an appropriate settings module
./runtests src/tests/test_minimal_settings_no_async.py

# core Python/async suite used in CI (no Playwright)
uv sync --group tests-core
pytest -m "not playwright"

# Playwright UI suite locally (requires built assets + browser deps)
uv sync --group tests-core --group tests-ui
npm install
npm run build
pytest -m playwright

# UI smoke tests only (Playwright)
pytest -m playwright

# raw pytest (advanced): runs everything with DJANGO_SETTINGS_MODULE=tests.settings
# You are responsible for building assets and having django-q2/qcluster/browsers available.
pytest
```

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
- A bare `pytest` will use `DJANGO_SETTINGS_MODULE=tests.settings` from `pytest.ini`, but it will not build assets or install browser/OS dependencies; expect Playwright tests (and async/system checks) to fail unless you provision those prerequisites yourself.
- Async-only tests rely on `django_q` (installed via the `tests-core` extras group) and are guarded with `pytest.importorskip("django_q")` so the core suite can be exercised even when async deps are omitted.
- The `tests.settings_minimal` module and `test_minimal_settings_no_async.py` provide a smoke test for importing `PowerCRUDMixin` in a project that never configures async or `POWERCRUD_SETTINGS`.
