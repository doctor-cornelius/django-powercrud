# Testing PowerCRUD

PowerCRUD ships with an end-to-end test suite that exercises both the Python surface and the sample UI.

## Test commands

```bash
# run the full suite (pytest-django)
pytest

# run the matrix cell that matches CI (Python/Django selected via current environment)
uv sync --group tests-core
pytest -m "not playwright"

# run the Playwright UI suite locally (requires built assets)
uv sync --group tests-core --group tests-ui
npm install
npm run build
pytest -m playwright

# UI smoke tests only (Playwright)
pytest -m playwright
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
