# Testing PowerCRUD

PowerCRUD has two server-side pytest suites with separate Django settings and coverage data:

- **PowerCRUD consumer suite** covers CRUD behavior, sample flows, template packs, management commands, and compatibility with public PowerCRUD imports and URLs. Root pytest discovery selects `src/tests` and `src/sample/tests`.
- **Coordinator suite** covers reusable async task coordination in `src/coordinator_tests`. It uses its own settings, test app, models, URLs, and fixtures. Run it with `runtests` or `pytest-coordinator.ini`; the root pytest configuration does not discover it.

The suites run in separate pytest processes because they use different Django settings and installed apps. The known minimal-settings test also runs in its own process. Browser tests remain part of the existing Playwright workflow.

## Run tests from the repository

The supported development workflow uses the existing Django container. From the repository root on the host, pass the command to `runproj exec`:

```bash
# Full local workflow: both server suites, then assets and browser suites
./runproj exec "./runtests"

# Server verification only: PowerCRUD, minimal settings, Bootstrap server cases, coordinator
./runproj exec "./runtests --pytest"

# Run each server suite independently
./runproj exec "./runtests --suite powercrud --pytest"
./runproj exec "./runtests --suite coordinator --pytest"

# Run both server suites in separate processes and combine their coverage data
./runproj exec "./runtests --suite all --pytest"

# Collect both test trees without database preflight or coverage reporting
./runproj exec "./runtests --collect-only"
```

`--suite` accepts `coordinator`, `powercrud`, or `all`. It is a server-test and collection option; browser runs continue to use the runner without `--suite`.

## Focused tests and settings

Test paths and node IDs are relative to the repository root, including when the runner is started through the container wrapper. With no `--suite`, the runner infers ownership from the paths. It normalizes directory spellings such as `./`, trailing slashes, and `..` before checking ownership, while preserving pytest node selectors. The coordinator directory itself selects the coordinator suite.

```bash
# Coordinator path: automatically uses coordinator settings and coverage
./runproj exec "./runtests --pytest src/coordinator_tests/test_lifecycle.py"

# PowerCRUD path: automatically uses consumer settings
./runproj exec "./runtests --pytest src/tests/test_async_compatibility.py"

# Minimal-settings tests always use their own settings
./runproj exec "./runtests --pytest src/tests/test_minimal_settings_no_async.py"

# Multiple tests from the minimal-settings module can run together
./runproj exec "./runtests --pytest src/tests/test_minimal_settings_no_async.py::test_powercrud_mixin_imports_without_async_stack src/tests/test_minimal_settings_no_async.py::test_builtin_template_pack_resolves_without_powercrud_settings"

# A focused consumer directory excludes the minimal-settings module
./runproj exec "./runtests --pytest src/tests"

# A focused consumer test can keep an explicit presentation settings overlay
./runproj exec "DJANGO_SETTINGS_MODULE=tests.settings_bootstrap ./runtests --suite powercrud --pytest src/tests/test_template_pack_behaviour_matrix.py"

# Force an asset rebuild for a consumer/browser-focused run
./runproj exec "./runtests --rebuild-assets src/tests/playwright/test_bulk_selection.py::test_bulk_selection_toggle"
```

Do not combine coordinator and PowerCRUD paths, the minimal-settings file and ordinary consumer paths, or focused paths with `--suite all`. The runner rejects these combinations because one pytest process cannot use both settings configurations. Coordinator selection also rejects browser and asset-build options. Focused ordinary consumer tests keep an explicitly selected settings module; the minimal-settings test always selects `tests.settings_minimal`.

Directories containing both suites, including `.` and `src`, are rejected even with an explicit suite selection. Use `--suite all --pytest` to execute both suites in separate processes, or select their directories individually. A focused consumer directory containing the minimal-settings module excludes that file and prints its separate invocation. This applies to plain focused runs, `--pytest`, and `--collect-only`; a full PowerCRUD suite run still executes the minimal module separately. Multiple explicit nodes from that module are compatible with one another, but cannot be combined with ordinary consumer tests or directories.

`--collect-only` uses the same ownership and settings selection but skips the database check, asset builds, and coverage commands. A focused minimal-settings collection selects `tests.settings_minimal`. A broad consumer collection excludes that file, which is run separately during test execution.

To run a focused browser test, use the normal runner without suite selection:

```bash
./runproj exec "./runtests --playwright src/tests/playwright/test_bulk_selection.py::test_bulk_selection_toggle"
```

## Coverage files

The consumer suite writes `.coverage`; the coordinator suite writes `.test-artifacts/coverage/coordinator/.coverage`. Full server runs retain those raw files and combine them into `.test-artifacts/coverage/combined/.coverage`. Separate directories keep one suite's coverage tooling from treating another suite's results as parallel input. The full default browser workflow appends browser coverage to consumer data and refreshes the combined file afterward.

To generate an aggregate HTML report from existing suite data inside the container:

```bash
./runproj exec "mkdir -p .test-artifacts/coverage/combined && coverage combine --keep --data-file=.test-artifacts/coverage/combined/.coverage .coverage .test-artifacts/coverage/coordinator/.coverage"
./runproj exec "COVERAGE_FILE=.test-artifacts/coverage/combined/.coverage coverage html"
```

Focused suite runs write only to their own raw coverage file; they do not merge partial results with another suite's possibly stale data. The coordinator coverage configuration measures the current manager, context, hooks, and tracking modules, so its percentage describes those four modules. The consumer coverage configuration retains the whole PowerCRUD source target. Aggregate reports use the union of file/line data from both suites rather than averaging their percentages. The runner requires both raw files before producing an aggregate.

The former root-level `.coverage.coordinator` and `.coverage.combined` files are obsolete. Regenerate results using the two suite commands above, then combine them; there is no automatic migration of old coverage data. Generated coverage directories are ignored by Git. CI keeps its existing downloadable artifact names and places coordinator XML alongside the coordinator raw data.

## Browser suites

The project maintains three browser-testing uses:

- the full local `./runtests` browser regression suite;
- the blocking CI `playwright_smoke` subset and focused Bootstrap browser coverage;
- an optional, broader manually requested browser run.

Browser tests exercise the sample app's CRUD flows, inline editing, favourites, row-action menus, and tooltip lifecycle. The Chromium browser is included in the Docker image. For host-side pytest use, install the browser separately. Browser runs require built assets and the browser dependencies; `runtests` manages the build and uses `DJANGO_ALLOW_ASYNC_UNSAFE=true` through test fixtures.

```bash
./runproj exec "./runtests --playwright"
./runproj exec "./runtests --rebuild-assets src/tests/playwright/test_filter_favourites.py::test_filter_reset_clears_remembered_selected_favourite"
```

To point Playwright at a different host, set `PLAYWRIGHT_BASE_URL` (the default during pytest is `live_server`).

## Reproducing Django compatibility environments

Use the constraints files to install the desired Django compatibility line. After installation, run both server suites through the runner:

```bash
# Django 5.2
uv pip install -c requirements/constraints-django52.txt ".[tests-core]"
./runtests --suite all --pytest

# Django 6.1
uv pip install -c requirements/constraints-django61.txt ".[tests-core]"
./runtests --suite all --pytest
```

The commands above run from the repository root in an environment with the project's test dependencies and database check prerequisites. To reproduce the browser smoke job, install the UI dependencies, build assets, and run the smoke marker under the appropriate settings.

## Notes

- A raw `pytest` uses `pytest.ini` and discovers only the PowerCRUD and sample consumer trees. It does not discover coordinator tests or build assets. Use `./runtests --suite coordinator --pytest` or `pytest -c pytest-coordinator.ini` for coordinator coverage.
- Async test modules do not all skip when django-q2 is absent. The coordinator suite imports the production async modules directly, so run it in the declared test environment with q2 installed.
- `tests.settings_minimal` exercises synchronous PowerCRUD imports without async configuration. It does not prove that django-q2 is uninstalled from the Python environment.
- The repository's container test setup uses its configured PostgreSQL services. A standalone test settings module may use SQLite where its settings specify that database; do not assume every local or CI command has the same database configuration.
- For the supported template-pack acceptance matrix, see [Testing and accepting a template pack](../template_packs/testing-and-acceptance.md).
- GitHub Actions runs the Python/Django compatibility matrix and the blocking browser smoke workflow. Local runner behavior and workflow configuration do not imply that a CI run has passed.
