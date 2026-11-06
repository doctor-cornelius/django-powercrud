# Phase A coverage artifact simplification

## Outcome and limits

**Coverage coordination is resolved. Phase A is ready for final approval.** The new locations isolate the data without moving or restoring files. Real pytest-cov execution and a fresh full server cycle verify artifact creation, independence, and exact aggregation. Combined with the [non-coverage review](phase_A_noncoverage_review.md), no remaining Phase A implementation blocker was found. Final approval remains pending user review; hardening issues 1–13 remain open and Phase B has not started.

Completed on 2026-11-04 on `async_hardening/phase_a`, starting at `270cbbd1`. The working tree was clean. This supersedes the artifact layout and preservation mechanism described in the historical [A3](phase_A_a3_results.md) and [A4](phase_A_a4_results.md) reports. Their recorded test outcomes remain historical evidence.

Changes are limited to the runner, coordinator coverage configuration, CI artifact paths, generated-file exclusions, infrastructure regressions, and documentation. Production code, suite selection, the 63 relocated cases, measurement targets, matrix conditions, and browser behavior are preserved. No dependencies were installed, services started, assets built, browser tests run, or workflows dispatched. CI changes were reviewed, not executed.

## Replacement design

| Artifact | Location |
|---|---|
| Consumer raw data | `.coverage` |
| Coordinator raw data | `.test-artifacts/coverage/coordinator/.coverage` |
| Combined data | `.test-artifacts/coverage/combined/.coverage` |
| Coordinator XML in CI | `.test-artifacts/coverage/coordinator/coverage.xml` |

The small [coordinator config](../../../../.coveragerc-coordinator) still measures only manager, context, hook, and tracking modules. Its explicit data path now sits outside the consumer's parallel-file namespace. [The runner](../../../../runtests) creates output directories during execution, never collection, and requires both raw files before combining named inputs with `--keep`. Combination replaces old aggregate data; reporting explicitly selects that aggregate. Focused runs do not combine stale results from another suite.

`run_preserving_coordinator_coverage`, its backup names, and all file-moving invocations are removed. The consumer function is invoked directly, including focused and browser routes; ordinary pytest failure codes remain failures. No signal cleanup or restoration mechanism is needed to protect the other suite's artifacts because they stay in their own directories throughout execution.

The [workflow](../../../../.github/workflows/run_tests.yml) copies the new raw paths while preserving the existing downloadable artifact names and `coverage-core.sqlite` handoff. The browser job still restores core data to `.coverage`, appends its results, and generates the existing combined XML. No service, dependency, matrix, or browser selection changed. The generated directory is ignored by Git. Old root-level coordinator/combined files are obsolete; regeneration is documented without automatic migration machinery.

## Regression verification

[Runner regressions](../../../../src/coordinator_tests/test_runtests.py) now use the new locations and direct calls. They check unchanged routing, collection without directory creation, explicit combined reporting, focused-run isolation, missing-input rejection, and preservation after success, ordinary failure, and SIGTERM. The interruption test terminates only a copied runner with harmless stubs in a temporary directory. There are no backup files to recover. Stub-created files are routing fixtures, not evidence of real coverage behavior.

One new [real artifact regression](../../../../src/coordinator_tests/test_coverage_artifacts.py) runs actual pytest-cov in temporary directories, using the repository's coordinator config and consumer coverage options. Its small payload reads the real context module without Django setup. It sanitizes inherited coverage/plugin settings, verifies the actual configured file is emitted, runs consumer and coordinator processes in both orders, and compares bytes. It seeds stale aggregate data, combines with real Coverage.py, and verifies replacement with the exact union while retaining both raw inputs.

| Command | Result |
|---|---|
| `./runproj exec "PYTEST_ADDOPTS=--no-cov ./runtests --suite coordinator --pytest src/coordinator_tests/test_runtests.py src/coordinator_tests/test_coverage_artifacts.py"` | Final focused check: **50 passed in 4.33s**, exit 0. The outer run disables coverage; the isolated real regression enables its own pytest-cov explicitly. |
| `./runproj exec "./runtests --suite coordinator --pytest"` | **114 passed in 4.72s**, exit 0, `coordinator_tests.settings`; four-module report remains 82%. |
| `./runproj exec "./runtests --suite powercrud --pytest"` | Exit 0. Ordinary `tests.settings`: **1,055 passed, 23 skipped, 110 deselected, 8 warnings in 17.23s**. Separate `tests.settings_minimal`: **4 passed, 1 warning in 3.76s**. `tests.settings_bootstrap`: **31 passed in 3.51s**. |

Runtime: Python 3.14.6, Django 6.1.2, pytest 8.4.2, pytest-cov 7.1.0. These full server runs occurred once each after the focused checks passed. The final 114 coordinator cases comprise 63 relocated cases, 49 runner cases, one real artifact regression, and one suite-isolation case. The increase from the non-coverage review's 110 is one extra failure/signal parameter, two missing-input parameters, and the real regression.

The first focused check had four test-only failures: three command-log assertions incorrectly matched `coverage|` inside the new filename, and the seeded aggregate fixture lacked its parent directory. Command checks now match the command at the start of a log line, and the fixture creates its directory. All four passed after those corrections; no production or selection fix was required. Existing consumer deprecation/q2 warnings and skips remain. No unexplained failure remains.

## Real full-run artifacts

Immediately after the coordinator run, a SHA-256 snapshot was taken through the container. The consumer run left the coordinator file byte-for-byte unchanged. A container Python checker used the public `CoverageData` constructor, `read()`, `measured_files()`, and `lines()` APIs to verify module ownership and union semantics, and invoked these effective commands inside the container:

```bash
coverage combine --keep --data-file=.test-artifacts/coverage/combined/.coverage .coverage .test-artifacts/coverage/coordinator/.coverage
COVERAGE_FILE=.test-artifacts/coverage/combined/.coverage coverage html
```

| Artifact | Measured files | Recorded lines |
|---|---:|---:|
| Consumer | 85 PowerCRUD files | 11,376 |
| Coordinator | Exactly the four intended modules | 769 |
| Combined | 85 files, exact file/line union | 11,725 |

Every combined file and line set equaled the union of the raw inputs, including 349 coordinator lines absent from consumer data. Both raw files survived combination byte-for-byte unchanged. Their hashes were:

- Consumer: `e338ac211e8ef8ef6d96751dd45dc2087f358e946b0bd6e88f90427afa23f33a`.
- Coordinator, unchanged before/after consumer execution and combination: `ed0f2327f07db547dc86aed408eb2ca5beda2b81592a37d94f3be7d2714c588a`.

HTML generation succeeded at `htmlcov/index.html` using the combined file. The file/line counts match the earlier A4 evidence. Coordinator percentages describe its four-module target; overall reporting uses the whole PowerCRUD target and combined covered lines, rather than averaging suite percentages.

The [canonical testing guide](../../../mkdocs/reference/testing.md#coverage-files) now records the new paths, aggregation commands, targets, focused-run limits, and obsolete artifacts. The non-coverage selection fixes remain intact and passed within the complete coordinator suite. No broader runner redesign or production hardening is included in this result.
