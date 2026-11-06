# A4 results: suite verification and testing guide

## Context and limits

Reviewed and verified on 2026-11-04 on branch `async_hardening/phase_a`. The starting commit was `fcc63998` (`test(async): relocate reusable coordinator coverage`); the working tree was clean before A4 edits. Verification ran in the existing Compose Django container with Python 3.14.6, Django 6.1.2, pytest 8.4.2, pytest-cov 7.1.0, and Coverage.py 7.16.2.

This increment changed test infrastructure, its regression tests, CI ordering, and testing documentation. It did not change production code. No dependency installation, service startup, browser test, asset build, or workflow dispatch occurred. No CI result was available or claimed.

## Relocation parity and suite isolation

The A3 relocation ledger remains the case-by-case source for old and new node IDs. Its 63 reusable cases remain in `src/coordinator_tests/`. The original 68 methods from the mixed sys-functions module remain accounted for as 57 coordinator cases and 11 PowerCRUD consumer cases: eight retained in the mixed module and three compatibility checks in `test_async_compatibility.py`. The final coordinator collection and execution include all 63 relocated cases, 19 runner regression checks, and one isolation check (83 tests total). The broad consumer run includes the retained compatibility and sample, CRUD, command, and presentation coverage.

Coordinator tests continue to use their own settings, models, URLs, workers, and cache fixtures, without importing PowerCRUD settings or fixtures. The session import check runs after coordinator execution. The test app alone has migrations disabled; Django and django-q2 keep their normal test database setup. Current production imports and patch targets remain as listed in the [A3 suite dependency record](phase_A_a3_results.md#suite-dependencies-and-boundaries), for Phase B to remove or adapt.

Coverage remains mocked, sequential, or in-process for these cases. The synchronous q2 checks are configuration probes. They do not establish real worker execution, cross-process locking, cache backend behavior, or concurrency guarantees. Existing tests continue to preserve known behavior that later hardening phases are expected to change.

## Infrastructure defects and repairs

The first artifact inspection found that the coordinator process did not create `.coverage.coordinator`: pytest-cov was still writing to `.coverage` even though the runner exported `COVERAGE_FILE`. The coordinator coverage config now sets `data_file = .coverage.coordinator` explicitly.

The next check found that pytest-cov treats files matching `.coverage.*` as parallel data associated with `.coverage`. A consumer run could therefore absorb or remove `.coverage.coordinator`; an existing `.coverage.combined` file could be treated the same way. The runner now temporarily moves those two files to names outside that pattern while consumer tests run and restores them afterward. Consumer runs clear only `.coverage`. Coordinator runs clear only `.coverage.coordinator`. Aggregate creation removes the old combined file, then combines the two named raw inputs with `--keep`.

The CI job now runs the Bootstrap consumer batch before the coordinator job so it cannot remove the coordinator data before artifact creation. The coordinator config writes the expected raw file for its separate artifact. Runner regressions use a copied runner and harmless command stubs in a temporary directory; the stubs emulate pytest-cov's matching and cover default routing, preservation, suite selection, settings, rejection cases, aggregation, and failure propagation. Default-route stubs include npm, so they cannot build assets or touch repository outputs.

The coverage fixes were driven by actual data-file behavior and checked against the explicit A4 requirement to preserve separate suite data. They do not change test outcomes or production behavior.

## Executed verification and coverage artifacts

All test commands ran through `./runproj exec` and `runtests`.

| Command | Result |
|---|---|
| `./runproj exec "./runtests --suite coordinator --collect-only"` | 83 collected in 0.23s under `coordinator_tests.settings`. |
| `./runproj exec "./runtests --suite powercrud --collect-only"` | 1,188 collected in 2.11s under `tests.settings`, including browser nodes. Root consumer discovery contains no coordinator tests. |
| `./runproj exec "./runtests --suite coordinator --pytest"` | 83 passed in 0.99s under coordinator settings. Coverage report measured the four configured async production modules (82% combined for those modules). |
| `./runproj exec "PYTEST_ADDOPTS=-qq ./runtests --suite powercrud --pytest"` | Exit 0. The ordinary consumer process selected 1,078 tests after deselecting 110: 1,055 passed, 23 skipped, zero failures in 16.89s. The separate minimal-settings process passed 4 tests in 3.85s; the Bootstrap server batch passed 31 in 3.59s. |

The consumer run emitted the existing deprecation and q2 timeout/retry configuration warnings. The minimal-settings process emitted its existing q2 timeout/retry warning. No test failure remained unexplained. The 23 skips are retained pytest skips; this run did not force those cases to execute.

Before the PowerCRUD run, `.coverage.coordinator` and `.coverage.combined` existed. Both survived the consumer run byte-for-byte unchanged. Coverage.py's public `CoverageData` API then confirmed:

- `.coverage` contains 85 PowerCRUD source files and 11,376 recorded lines.
- `.coverage.coordinator` contains only `async_manager.py`, `async_context.py`, `async_hooks.py`, and `async_dashboard.py`: four files and 769 recorded lines.
- 349 coordinator lines absent from the consumer file remained exclusive to coordinator data.
- `coverage combine --keep --data-file=.coverage.combined .coverage .coverage.coordinator` produced an 85-file, 11,725-line union. A line-by-line comparison verified the combined data exactly equals the union, and both raw inputs remained byte-for-byte unchanged.

The root `pytest.ini` still discovers only `src/tests` and `src/sample/tests`. Coordinator collection requires the coordinator config. The CI workflow edits were inspected, not executed; they are not evidence of a passing workflow. Browser tests and asset builds were intentionally outside this A4 verification.

## Stable documentation

`docs/mkdocs/reference/testing.md` now describes suite ownership, runner options, focused path inference, settings selection, minimal settings, coverage files, combined reports, and the host/container command boundary. It corrects the claims that raw pytest discovers every suite and that every async test skips when django-q2 is missing. Compatibility examples now run both server suites.

README development examples use the container runner and link to the published testing guide. The documentation site was not built.

## Remaining limits and Phase A recommendation

The full server selections, suite collections, coverage separation, aggregation, and stable documentation checks are complete. The A3 relocation ledger accounts for all cases. No CI or browser result is claimed.

Phase B still needs to remove or adapt coordinator imports of PowerCRUD modules and `POWERCRUD_SETTINGS`, isolate q2 access behind the intended boundary, and preserve public compatibility paths. The suites do not prove real worker delivery, Redis/Memcached/DatabaseCache semantics, cached q2 results, cross-process lock safety, or duplicate and late callback handling. Hardening register issues 1–13 remain open; no Phase B documents were created.

The evidence supports completing A4's verification tasks and presenting Phase A for review. Keep final A4 and Phase A sign-off pending that review. Do not mark production hardening complete based on these test-infrastructure results.
