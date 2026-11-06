# A3 results: independent coordinator test suite

## Context and limits

- **Date:** 2026-11-04.
- **Branch and starting commit:** `async_hardening/phase_a`, `6172d501` (`docs(async): review A2 evidence and clarify A3 handoff`). The working tree was clean before A3.
- **Commits:** `d32d950a` established the independent suite and runner/CI selection; a second commit records the completed relocation and A3 handoff.
- **Runtime used:** existing Django container, Python 3.14.6, pytest 8.4.2, Django 6.1.2. The lockfile and earlier A1/A2 inspection identify django-q2 1.11.1; A3 did not inspect dependency source again.
- **Scope:** test infrastructure, test relocation, runner/discovery/coverage/CI configuration, and this report. No production implementation, dependency change, browser test, full PowerCRUD run, or CI run was performed. No new worker/concurrency experiment was performed.
- The fresh original mixed-module baseline used its existing test-owned Cluster fixtures and stopped them at teardown. This was explicitly requested by the A3 handoff. The relocated health probes and inline launch check run under synchronous q2 settings and do not establish separate worker execution.
- Test runs below used `./runproj exec` and `runtests`. Test results establish current behavior only; assertions that conflict with agreed A1 clauses remain unchanged for Phase C.

## Relocation ledger

The A2 ownership map specified **63 existing reusable tests**: 57 from `test_sys_functions.py`, three context tests, and three hook tests. All 63 now have coordinator-owned nodes. The old mixed file's three URL/hook compatibility tests moved to PowerCRUD, while eight CRUD/view-manager tests remain in PowerCRUD. This accounts for all 68 methods in the original mixed module.

Each row lists the old and new node IDs. For compactness, repeated file/class path prefixes are stated in the column headings; append the listed method to each prefix to get the complete node ID. Every listed method maps one-to-one and retains its distinct assertions.

### Coordinator nodes

| Old node IDs under `src/tests/async_tests/test_sys_functions.py::TestSysFunctions` | New node IDs under `src/coordinator_tests/test_lifecycle.py::TestSysFunctions` |
|---|---|
| `test_cache_working` | `test_cache_working` |
| `test_q2_cluster_working` | `test_q2_cluster_working` |
| `test_async_working` | `test_async_working` |

| Old node IDs under `src/tests/async_tests/test_sys_functions.py::TestActiveTasks` | New node IDs under `src/coordinator_tests/test_state_locks.py::TestActiveTasks` |
|---|---|
| `test_get_active_tasks` | `test_get_active_tasks` |
| `test_add_and_remove_active_task` | `test_add_and_remove_active_task` |
| `test_cleanup_active_tasks` | `test_cleanup_active_tasks` |

| Old node IDs under `src/tests/async_tests/test_sys_functions.py::TestConflictDetection` | New node IDs under `src/coordinator_tests/test_state_locks.py::TestConflictDetection` |
|---|---|
| `test_add_conflict_ids_success` | `test_add_conflict_ids_success` |
| `test_add_conflict_ids_conflict_detected` | `test_add_conflict_ids_conflict_detected` |
| `test_check_conflict_no_conflicts` | `test_check_conflict_no_conflicts` |
| `test_check_conflict_with_conflicts` | `test_check_conflict_with_conflicts` |
| `test_remove_conflict_ids_cleanup` | `test_remove_conflict_ids_cleanup` |

| Old node IDs under `src/tests/async_tests/test_sys_functions.py::TestAtomicReservation` | New node IDs under `src/coordinator_tests/test_state_locks.py::TestAtomicReservation` |
|---|---|
| `test_atomic_reservation_rollback` | `test_atomic_reservation_rollback` |
| `test_dual_key_structure` | `test_dual_key_structure` |
| `test_idempotent_cleanup` | `test_idempotent_cleanup` |

| Old node ID | New node ID |
|---|---|
| `src/tests/async_tests/test_sys_functions.py::TestConcurrentAccess::test_concurrent_atomic_reservation` | `src/coordinator_tests/test_state_locks.py::TestConcurrentAccess::test_concurrent_atomic_reservation` |
| `src/tests/async_tests/test_sys_functions.py::TestCleanupUtilities::test_cache_add_atomicity` | `src/coordinator_tests/test_state_locks.py::TestCleanupCacheAdd::test_cache_add_atomicity` |
| `src/tests/async_tests/test_sys_functions.py::TestTask3ActiveTasksIntegration::test_add_active_task_no_double_locking` | `src/coordinator_tests/test_state_locks.py::TestActiveTaskIntegration::test_add_active_task_no_double_locking` |

| Old node IDs under `src/tests/async_tests/test_sys_functions.py::TestCleanupUtilities` | New node IDs under `src/coordinator_tests/test_lifecycle.py::TestCleanupUtilities` |
|---|---|
| `test_cleanup_completed_tasks_removes_artifacts` | `test_cleanup_completed_tasks_removes_artifacts` |
| `test_cleanup_skips_running_tasks` | `test_cleanup_skips_running_tasks` |

| Old node IDs under `src/tests/async_tests/test_sys_functions.py::TestTask3LaunchPattern` | New node IDs under `src/coordinator_tests/test_lifecycle.py::TestTask3LaunchPattern` |
|---|---|
| `test_launch_async_task_success_without_conflicts` | `test_launch_async_task_success_without_conflicts` |
| `test_launch_async_task_with_conflict_ids_success` | `test_launch_async_task_with_conflict_ids_success` |
| `test_launch_blocks_on_conflict` | `test_launch_blocks_on_conflict` |
| `test_resolve_manager_from_path` | `test_resolve_manager_from_path` |
| `test_resolve_manager_with_config` | `test_resolve_manager_with_config` |
| `test_resolve_manager_fallback` | `test_resolve_manager_fallback` |
| `test_launch_rollback_on_enqueue_failure` | `test_launch_rollback_on_enqueue_failure` |
| `test_task_key_consistency` | `test_task_key_consistency` |

| Old node IDs under `src/tests/async_tests/test_sys_functions.py::TestTask3CompletionHooks` | New node IDs under `src/coordinator_tests/test_lifecycle.py::TestTask3CompletionHooks` |
|---|---|
| `test_completion_hook_wired_correctly` | `test_completion_hook_wired_correctly` |
| `test_handle_task_completion_customizable` | `test_handle_task_completion_customizable` |
| `test_lifecycle_events_fired` | `test_lifecycle_events_fired` |
| `test_handle_task_completion_emits_events` | `test_handle_task_completion_emits_events` |
| `test_handle_task_completion_failure_event` | `test_handle_task_completion_failure_event` |

| Old node IDs under `src/tests/async_tests/test_sys_functions.py::TestTask3ProgressIntegration` | New node IDs under `src/coordinator_tests/test_lifecycle.py::TestTask3ProgressIntegration` |
|---|---|
| `test_progress_key_lifecycle` | `test_progress_key_lifecycle` |
| `test_update_progress_emits_lifecycle` | `test_update_progress_emits_lifecycle` |
| `test_worker_receives_task_key` | `test_worker_receives_task_key` |

| Old node IDs under `src/tests/async_tests/test_sys_functions.py::TestTask3StatusMethods` | New node IDs under `src/coordinator_tests/test_lifecycle.py::TestTask3StatusMethods` |
|---|---|
| `test_status_methods_behavior` | `test_status_methods_behavior` |

| Old node IDs under `src/tests/async_tests/test_sys_functions.py::TestTask3EndToEndIntegration` | New node IDs under `src/coordinator_tests/test_lifecycle.py::TestTask3EndToEndIntegration` |
|---|---|
| `test_e2e_launch_execute_cleanup_cycle` | `test_e2e_launch_execute_cleanup_cycle` |

| Old node IDs under `src/tests/async_tests/test_sys_functions.py::TestProgressPolling` | New node IDs under `src/coordinator_tests/test_lifecycle.py::TestProgressPolling` |
|---|---|
| `test_as_view_missing_task_name` | `test_as_view_missing_task_name` |
| `test_as_view_with_progress_data` | `test_as_view_with_progress_data` |
| `test_as_view_no_progress_fallback_status` | `test_as_view_no_progress_fallback_status` |
| `test_as_view_unknown_status` | `test_as_view_unknown_status` |
| `test_as_view_error_handling` | `test_as_view_error_handling` |
| `test_progress_polling_with_manual_data` | `test_progress_polling_with_manual_data` |
| `test_as_view_post_method` | `test_as_view_post_method` |
| `test_poll_interval_adaptive` | `test_poll_interval_adaptive` |

| Old node IDs under `src/tests/async_tests/test_sys_functions.py::TestAsyncHookHelpers` | New node IDs under `src/coordinator_tests/test_lifecycle.py::TestAsyncHookHelpers` |
|---|---|
| `test_extract_manager_class_from_dict_kwargs` | `test_extract_manager_class_from_dict_kwargs` |
| `test_extract_manager_class_from_serialized_kwargs` | `test_extract_manager_class_from_serialized_kwargs` |
| `test_extract_manager_class_returns_none_for_unparseable_payload` | `test_extract_manager_class_returns_none_for_unparseable_payload` |
| `test_task_completion_hook_uses_resolved_manager` | `test_task_completion_hook_uses_resolved_manager` |
| `test_task_completion_hook_handles_missing_manager` | `test_task_completion_hook_handles_missing_manager` |
| `test_task_completion_hook_passes_manager_config` | `test_task_completion_hook_passes_manager_config` |

| Old node IDs under `src/tests/async_tests/test_sys_functions.py::TestModelTrackingAsyncManager` | New node IDs under `src/coordinator_tests/test_lifecycle.py::TestModelTrackingAsyncManager` |
|---|---|
| `test_create_event_initialises_dashboard_record` | `test_create_event_initialises_dashboard_record` |
| `test_progress_event_updates_progress_without_overwriting_message` | `test_progress_event_updates_progress_without_overwriting_message` |
| `test_completion_event_sets_result_and_timestamp` | `test_completion_event_sets_result_and_timestamp` |
| `test_fail_event_marks_failure_and_preserves_timestamp` | `test_fail_event_marks_failure_and_preserves_timestamp` |
| `test_cleanup_event_marks_flag_without_status_regression` | `test_cleanup_event_marks_flag_without_status_regression` |
| `test_custom_formatters_are_applied` | `test_custom_formatters_are_applied` |

| Old node IDs under `src/tests/test_async_context.py` | New node IDs under `src/coordinator_tests/test_context.py` |
|---|---|
| `test_task_context_sets_and_resets` | `test_task_context_sets_and_resets` |
| `test_register_descendant_conflicts_without_context` | `test_register_descendant_conflicts_without_context` |
| `test_register_descendant_conflicts_invokes_manager` | `test_register_descendant_conflicts_invokes_manager` |

| Old node IDs under `src/tests/test_async_hooks.py` | New node IDs under `src/coordinator_tests/test_hooks.py` |
|---|---|
| `test_parse_task_kwargs_handles_json` | `test_parse_task_kwargs_handles_json` |
| `test_extract_manager_helpers` | `test_extract_manager_helpers` |
| `test_progress_update_decorator` | `test_progress_update_decorator` |

The grouped rows above use the explicit source and destination file/class prefixes shown in each heading. No cases were consolidated. Distinct cache keys, rollback assertions, enqueue arguments, hook paths, state/status responses, lifecycle payloads, model fields, and formatter outputs remain in their corresponding test bodies.

### PowerCRUD compatibility and retained consumer cases

| Old node ID | New node ID / status |
|---|---|
| `src/tests/async_tests/test_sys_functions.py::TestTask3EndToEndIntegration::test_hook_import_path_works` | `src/tests/test_async_compatibility.py::TestAsyncCompatibility::test_hook_import_path_works` |
| `src/tests/async_tests/test_sys_functions.py::TestProgressPolling::test_get_url_returns_path` | `src/tests/test_async_compatibility.py::TestAsyncCompatibility::test_get_url_returns_path` |
| `src/tests/async_tests/test_sys_functions.py::TestProgressPolling::test_get_urlpatterns_returns_resolver` | `src/tests/test_async_compatibility.py::TestAsyncCompatibility::test_get_urlpatterns_returns_resolver` |
| `src/tests/async_tests/test_sys_functions.py::TestSingleRecordConflicts::test_check_for_conflicts_single_pk` | Retained at same node ID in the consumer mixed module |
| `src/tests/async_tests/test_sys_functions.py::TestSingleRecordConflicts::test_render_conflict_response_htmx_update` | Retained at same node ID in the consumer mixed module |
| `src/tests/async_tests/test_sys_functions.py::TestSingleRecordConflicts::test_render_conflict_response_htmx_delete` | Retained at same node ID in the consumer mixed module |
| `src/tests/async_tests/test_sys_functions.py::AsyncMixinManagerResolutionTests::test_direct_manager_class_attribute` | Retained at same node ID in the consumer mixed module |
| `src/tests/async_tests/test_sys_functions.py::AsyncMixinManagerResolutionTests::test_manager_class_path_attribute` | Retained at same node ID in the consumer mixed module |
| `src/tests/async_tests/test_sys_functions.py::AsyncMixinManagerResolutionTests::test_view_supplies_manager_config` | Retained at same node ID in the consumer mixed module |
| `src/tests/async_tests/test_sys_functions.py::AsyncMixinManagerResolutionTests::test_settings_default_manager_class` | Retained at same node ID in the consumer mixed module |
| `src/tests/async_tests/test_sys_functions.py::AsyncMixinManagerResolutionTests::test_settings_default_manager_config` | Retained at same node ID in the consumer mixed module |

All other A2 inventory entries remain PowerCRUD-owned at their existing nodes: async view/mixin and manager selection; bulk workers, persistence, cleanup commands/schedules, settings validation, and minimal-settings behavior; sample dashboard, model-save/context, domain/service and validation behavior; inline locked-row display/metadata; HTMX threshold/conflict/manager selection; bulk validation and response rendering; DaisyUI/Bootstrap presentation matrix; browser presentation; and legacy URL consumers. The retained sample and presentation assertions were not replaced by generic coordinator tests. D1–D8 ownership remains in the shared sample matrix. The detailed per-entry source list remains in the [A2 ownership map](phase_A_a2_results.md#test-ownership-map).

| Mapped coverage group | Coverage type and dependencies | Assertions/expectations to preserve |
|---|---|---|
| `test_state_locks.py` | Mocked/in-process, sequential operations against the suite file cache. `TestConcurrentAccess` remains sequential; `cache.add` is not cross-process evidence. | Active membership, lock keys/tracking sets, rollback, idempotent cleanup, and first-owner retention. |
| `TestSysFunctions` probes | Synchronous q2 configuration probes against suite settings; no cluster or real worker. | Existing cache/qcluster/system validation booleans. Treat as probes, not worker health proof. |
| `TestCleanupUtilities` | In-process cache operations with mocked q2 `Task` rows; `success=None` is an artificial running result. | Artifact counts, skipped-running behavior, and current cleanup response. |
| Launch, completion, status, progress, and inline launch classes | Mocked/in-process q2 enqueue/fetch/hook calls; the inline worker is invoked by a patched enqueue. | Task UUID/name, worker kwargs, lock reservation, rollback, hardcoded hook, lifecycle payloads, fetch wait values, progress/HTTP response, and inline progress capture. |
| `TestAsyncHookHelpers` | Mocked manager resolution and in-process kwargs parsing. Suite manager paths replace sample manager paths. | Parsed manager path/config and exact completion-hook dispatch. |
| `TestModelTrackingAsyncManager` | Sequential ORM lifecycle against the suite tracking model; no q2 worker. | Status/message/result/progress fields, timestamps, cleanup flag, and custom formatter outputs. |
| Context and hook modules | In-process context checks and mocked manager/progress callbacks. No automatic worker context propagation is asserted. | Context set/reset, descendant IDs, task-kwargs parsing, manager helper behavior, and progress callback forwarding. |
| Runner tests | Local subprocesses with temporary command stubs; no Django database, q2 process, browser, or asset build. | Suite/settings routing, rejection paths, data-file separation, and exact pytest exit status. |
| Compatibility and retained PowerCRUD/sample modules | Import/URL checks, mocked view/manager tests, ORM sample integration, or presentation tests as classified in A2. | Public URL/hook compatibility, CRUD behavior, sample workflow and both maintained template packs. |

### Fixture, helper, coverage, and behavior changes

- The suite now lives at `src/coordinator_tests/`, outside `src/tests/conftest.py`. It has its own settings, URLConf, app config, models, manager helper, worker module, and cache cleanup. The local Book model supports model-path resolution. The tracking model retains the sample model's exercised status choices, field types, names, and timestamps; only this app's migrations are disabled. Django and q2 migrations remain enabled.
- Coordinator settings install Django auth/contenttypes, django-q2, and `coordinator_tests.testapp`; they omit PowerCRUD and sample apps. SQLite and UTC-aware timestamps are enabled. File caches use per-process temporary paths for `default` and `coordinator_async`; the session finalizer clears those aliases and removes the suite directory. Collection-only does not create the temporary directory.
- `POWERCRUD_SETTINGS` is still supplied because current production `AsyncManager` construction reads it. q2 uses the ORM broker, `sync=True`, and timeout 30 below retry 60. These are test settings, not a support decision.
- The coordinator URLConf mounts `AsyncManager.as_view()` directly. Old PowerCRUD URL construction and hook-import checks stay in `TestAsyncCompatibility`.
- The sample manager strings in generic hook tests now resolve to importable `coordinator_tests.managers.CoordinatorAsyncManager`; tracking tests resolve `coordinator_testapp.AsyncTaskRecord`. Context tests use `coordinator_testapp.Book`. `simple_test_worker` moved to `coordinator_tests.workers` with its progress exception suppression unchanged.
- Existing production patch targets remain, including `powercrud.async_manager.async_task`, `fetch`, `Task`, and `AsyncManager`. The hardcoded PowerCRUD completion-hook assertion remains in the launch test until Phase B introduces an adapter.
- The three health-probe methods no longer inherit cluster startup. They retain their assertions with `sync=True` and are not described as real-worker checks. The inline launch test retains its UUID, active-set, and inline progress assertions; it does not assert completion or cleanup. Sequential reservation checks remain sequential. Mocked `success=None` running-result cases remain artificial.
- Known current behavior that A1 expects to change remains asserted: `TestProgressPolling::test_as_view_no_progress_fallback_status` and `test_as_view_unknown_status` treat missing progress as success; `TestTask3LaunchPattern::test_resolve_manager_fallback` accepts fallback from an invalid explicit path; cleanup still follows its current result-row rules; and launch/completion tests preserve current ordering. The literal q2 hook assertion remains in `test_launch_async_task_success_without_conflicts`. A3 adds no feature regression and changes no production code.
- Remaining consumer coverage includes the full sample async module and the shared presentation matrix. The coordinator's generic tracking and lifecycle tests do not replace sample dashboard, CRUD, or presentation assertions.

## Suite dependencies and boundaries

The independent test app and settings do not install PowerCRUD or sample, and the final session check scans loaded modules after all coordinator tests. It rejects `sample` imports and PowerCRUD CRUD mixin/view imports. The suite nevertheless imports current production modules: [async_manager.py](../../../../src/powercrud/async_manager.py), [async_context.py](../../../../src/powercrud/async_context.py), [async_hooks.py](../../../../src/powercrud/async_hooks.py), and [async_dashboard.py](../../../../src/powercrud/async_dashboard.py). Their current configuration/logging dependencies include [conf.py](../../../../src/powercrud/conf.py) and [logging.py](../../../../src/powercrud/logging.py), and manager/hooks still import django-q2. `POWERCRUD_SETTINGS` remains necessary for manager construction. These are expected Phase B dependencies; A3 did not copy or hide production code.

No test in the coordinator suite proves Redis, Memcached, or DatabaseCache behavior, real worker delivery, cross-process locking, transaction visibility, cached-result completion, or concurrent event ordering. The file cache, mocked q2 calls, and sequential checks only establish in-process behavior.

## Runner and CI behavior

- Root [pytest.ini](../../../../pytest.ini) limits default discovery to `src/tests` and `src/sample/tests`. [pytest-coordinator.ini](../../../../pytest-coordinator.ini) selects `src/coordinator_tests`, coordinator settings, and a separate coverage config.
- `./runtests --suite coordinator --pytest [paths]` selects coordinator settings even if consumer settings are inherited. `--suite powercrud --pytest [paths]` preserves focused consumer settings and minimal-settings inference. `--suite all --pytest` starts consumer and coordinator pytest processes separately. Coordinator and consumer paths cannot be mixed; `all` cannot take focused paths.
- `--collect-only` performs no database preflight, asset build, or coverage reporting. With no explicit suite it collects both suites in separate processes. With a selected suite it collects only that suite. Focused paths remain repository-root-relative.
- The broad PowerCRUD run excludes `test_minimal_settings_no_async.py`; the runner then executes it under `tests.settings_minimal`. Existing focused Bootstrap server coverage remains. Browser and asset behavior remains on the existing path and coordinator selection rejects those options.
- Consumer coverage remains `.coverage`. Coordinator coverage uses `COVERAGE_FILE=.coverage.coordinator`, bare `--cov`, and [`.coveragerc-coordinator](../../../../.coveragerc-coordinator) to measure current manager/context/hooks/tracking modules. Aggregate coverage writes `.coverage.combined` using `coverage combine --keep`; both inputs remain. The existing `.gitignore` pattern `.coverage.*` covers these generated files.
- The workflow retains the Python/Django matrix and Bootstrap condition. It runs ordinary consumer, separate minimal-settings append, and coordinator coverage in separate processes; coordinator emits `coverage-coordinator.xml`. On the canonical Python 3.14/Django 6.1 entry it uploads separate consumer/coordinator data artifacts, combines them into the existing `coverage-core.sqlite` artifact for the browser job, and preserves the browser restore/append flow. Workflow edits are not evidence of a passing CI run.
- Eight command-stub tests in `test_runtests.py` cover coordinator settings/routing, path inference, mixed-path rejection, minimal settings, separate collection processes without preflight/build/coverage, separate coverage data files, and pytest exit-code propagation. A suite-isolation test verifies settings/apps/URLConf; the session finalizer checks imports after the complete run.

## Executed verification

All commands below ran through the existing container. Unless noted, pytest used Python 3.14.6, pytest 8.4.2, and Django 6.1.2.

### Fresh pre-relocation baseline

| Command | Result |
|---|---|
| `./runproj exec "./runtests --pytest src/tests/async_tests/test_sys_functions.py"` | **68 passed in 6.59s**, `tests.settings`. This included the test-owned cluster classes; it was a baseline only, not proof that each case used a real worker. |
| `./runproj exec "./runtests --pytest src/tests/test_async_context.py src/tests/test_async_hooks.py src/tests/test_async_mixin_extended.py src/tests/test_powercrud_tasks_and_utils.py"` | **21 passed in 1.43s**, `tests.settings`. |
| `./runproj exec "./runtests --pytest src/tests/test_minimal_settings_no_async.py"` | **4 passed in 3.81s**, `tests.settings_minimal`; the existing q2 timeout/retry warning appeared. |

### Relocated and retained coverage

| Command | Result and limit |
|---|---|
| `./runproj exec "./runtests --suite coordinator --pytest"` | **72 passed in 0.82s**: 63 relocated cases, eight runner tests, and one isolation test. Coordinator settings; in-process, mocked, synchronous, or sequential coverage only. |
| `./runproj exec "./runtests --suite coordinator --collect-only"` | **72 collected** under `coordinator_tests.settings`; no database preflight or coverage report. |
| `./runproj exec "./runtests --suite powercrud --collect-only"` | **1,188 collected** under `tests.settings`; excludes the separate minimal-settings file and discovers no coordinator test. |
| `./runproj exec "./runtests --suite powercrud --pytest src/tests/async_tests/test_sys_functions.py src/tests/test_async_compatibility.py src/tests/test_async_mixin_extended.py src/tests/test_powercrud_tasks_and_utils.py"` | **26 passed in 2.04s**, `tests.settings`: eight retained mixed-module consumer cases, three compatibility cases, five async-mixin cases, and ten task/utility cases. |
| `./runproj exec "./runtests --suite powercrud --pytest src/tests/test_minimal_settings_no_async.py"` | **4 passed in 3.70s**, `tests.settings_minimal`; inherited q2 timeout/retry warning remains. |
| `./runproj exec "./runtests --suite powercrud --pytest src/sample/tests/test_async_samples.py"` | **25 passed in 2.70s**, `tests.settings`; sample behavior remains independently covered. |
| `./runproj exec "./runtests --suite powercrud --pytest src/tests/test_management_commands.py::test_cleanup_async_warns_when_disabled src/tests/test_management_commands.py::test_cleanup_async_json_output src/tests/test_management_commands.py::test_cleanup_async_plain_output src/tests/test_htmx_bulk_mixins.py::test_should_process_async_respects_threshold src/tests/test_htmx_bulk_mixins.py::test_conflict_checking_disabled_when_async_off src/tests/test_htmx_bulk_mixins.py::test_get_async_manager_uses_explicit_class src/tests/test_htmx_bulk_mixins.py::test_get_async_manager_uses_settings_default src/tests/test_htmx_bulk_mixins.py::test_get_async_manager_class_path_prefers_explicit_path src/tests/test_htmx_bulk_mixins.py::test_check_for_conflicts_uses_async_manager src/tests/test_htmx_bulk_mixins.py::test_check_for_conflicts_returns_false_without_hits src/tests/test_inline_editing_mixin.py::test_inline_guard_blocks_locked_state src/tests/test_inline_editing_mixin.py::test_inline_lock_metadata_includes_user_and_label src/tests/test_bulk_view_mixin.py::test_bulk_edit_rejects_invalid_fields_before_async_queueing src/tests/test_bulk_view_mixin.py::test_bulk_edit_process_post_async src/tests/test_template_pack_behaviour_matrix.py::test_shared_bulk_async_and_inline_matrix"` | **15 passed in 2.62s**, `tests.settings`; cleanup output, async selection/manager/conflict behavior, inline lock display, validation-before-queueing, response behavior, and ordinary presentation matrix. |
| `./runproj exec "DJANGO_SETTINGS_MODULE=tests.settings_bootstrap ./runtests --suite powercrud --pytest src/tests/test_template_pack_behaviour_matrix.py::test_shared_bulk_async_and_inline_matrix"` | **1 passed in 2.20s**, `tests.settings_bootstrap`; the shared presentation matrix passed under Bootstrap. |

No inherited test failure remained unexplained. The warning in minimal-settings runs is the same existing django-q2 timeout/retry configuration warning recorded in A2. No full consumer or browser suite was run; no CI result is claimed.

One intermediate 72-item coordinator run failed only in the new `--suite all --collect-only` stub test: its check for coverage commands matched `.coverage` in pytest's environment log. The check was narrowed to lines whose command is `coverage`; the complete coordinator run then passed 72/72.

## A4 handoff

Run the two full suites independently through the required container runner:

```bash
./runproj exec "./runtests --suite coordinator --pytest"
./runproj exec "./runtests --suite powercrud --pytest"
```

The PowerCRUD invocation includes ordinary consumer coverage, its separate minimal-settings module, and focused Bootstrap server coverage. A4 should review the resulting counts and failures against the fresh 68-method mixed-module baseline and the 63-row relocation ledger; inspect generated coverage files and CI execution when available. Browser coverage remains on its existing separate workflow path.

Production dependencies still awaiting Phase B are the PowerCRUD module paths and settings consumed by coordinator tests, q2 imports/options/result handling, and current PowerCRUD hook/cache namespaces. A3 does not resolve A1 behavior questions, prove claimed cache or q2 modes, guarantee concurrency, or mark hardening issues 1–13 complete.
