# Phase B notes: Internal coordination boundary

Prepared on 2026-11-06 from the [overall plan](../0_async_hardening-plan.md), [shared handoff](../0_async_hardening-notes.md#phase-a-completion-and-handoff), and [A1 contracts C1–C6 / decisions Q1–Q10](../phase_A/phase_A_notes.md#a1-draft-contracts-for-discussion). Phase B is complete on 2026-11-07: B1 specification, B2 q2 isolation, B3 coordinator separation, and [B4 review/verification/handoff](#b4-review-and-handoff--2026-11-07) are recorded below. Phase C intentional hardening and issues 1–13 remain open.

## Scope and sources of truth

Phase B establishes one-way dependencies between PowerCRUD integration, reusable coordination, and q2 execution. Preserve established behavior during structural changes and identify any unavoidable observable change explicitly. Intentional configuration, outcome, ordering, locking, manager propagation, and reconciliation corrections remain Phase C work.

The [shared numbered register](../0_async_hardening-notes.md#key-async-hardening-issues) remains the only issue-completion checklist. The [D1–D8 matrix](../0_async_hardening-notes.md#sample-demonstration-coverage-matrix) remains the sample acceptance inventory. Do not duplicate either here or mark an issue solved merely because its code moved.

django-q2 remains the sole execution backend. A narrow internal adapter is sufficient; no general backend plugin framework is required. Package extraction, final package/class names, repository creation, packaging, and publication remain Phase E. Additional execution engines and dashboard redesign remain deferred.

## Phase A baseline and limits

Phase A settled contracts, qualified findings, separated 63 reusable tests, and retained 11 consumer cases from the original mapped set. The [A3 ledger](../phase_A/phase_A_a3_results.md#relocation-ledger) gives exact old/new nodes and helper replacements; use pre-A3 commit `6172d501` when following historical source references.

The [non-coverage review](../phase_A/phase_A_noncoverage_review.md) accounts for all 74 original cases and 232 assertions. The [final coverage follow-up](../phase_A/phase_A_coverage_results.md) supersedes earlier coverage filenames and file-moving workarounds. It records 114 coordinator passes, 1,055 consumer passes with 23 skips, four minimal-settings passes, and 31 Bootstrap passes on 2026-11-04. These are inherited results, not Phase B execution evidence.

Coordinator tests already own settings, URLs, minimal models, workers, and cache fixtures without installing PowerCRUD/sample apps. They still import current production `powercrud` async modules and depend on `POWERCRUD_SETTINGS`, configuration/logging helpers, q2 imports, legacy hook paths, and cache namespaces. Their file caches, mocked calls, synchronous probes, and sequential reservations do not prove real worker delivery or concurrent backend safety.

## Plan Phases

### B1: Confirm the boundary and compatibility seams

The agreed responsibilities are:

| Owner | Responsibilities |
|---|---|
| Coordinator | Shared state, locks, progress, lifecycle, context, manager reconstruction, optional model tracking, reusable endpoints, and reconciliation/cleanup |
| q2 adapter | Dependency loading, queue configuration/options, enqueueing, execution/result identifiers, result lookup, completion translation, health probes, and scheduling integration |
| PowerCRUD | Settings translation, bulk thresholds/selection, CRUD workers and persistence, conflict/locked-row presentation, progress modal, dashboard CRUD views, and legacy entry points |

The read-only dependency and compatibility inventory is complete in the [Phase B audit](phase_B_audit.md). It documents the current call paths, configuration access, test seams, behavior to preserve, and questions raised for design. D1–D7 record the subsequent agreements; the technical specification below resolves the remaining B1 questions for B2–B3.

Specify configuration values for cache alias and namespace, TTLs and cleanup timing, launch enablement, adapter options, and importable manager reconstruction metadata. PowerCRUD maps its existing settings into that explicit configuration; ordinary Django callers and coordinator tests must be able to supply it without PowerCRUD configuration helpers. Keep queue-specific option handling in the adapter. Introducing an enablement value does not authorize changing current launch/cleanup gating in this structural phase.

Keep legacy entry points working under Q9 through the first extracted-package release and at least one subsequent PowerCRUD minor release; removal requires an announced breaking release. Distinguish reusable implementation from consumer compatibility wrappers even while both remain in this repository. Preserve logical task keys, current return values, configured manager paths, hook paths, and URL consumers. Avoid changing cache namespaces as an incidental consequence of moving code. Any necessary path/namespace migration follows the agreed drained-upgrade procedure; rolling upgrades with in-flight jobs remain excluded.

#### Agreed B1 decisions — 2026-11-07

**B1-D1: Configuration ownership and settings location.** PowerCRUD users keep `POWERCRUD_SETTINGS` as the source of PowerCRUD and coordination configuration. PowerCRUD translates coordination values into explicit configuration supplied to the coordinator; reusable implementation does not read PowerCRUD settings helpers. Other Django applications can supply coordinator configuration directly. Extraction requires a coordinator-owned settings namespace, whose final name/shape remains undecided. A separate physical settings file is not required. Configure each value once rather than maintaining duplicate PowerCRUD/coordinator copies.

Keep three concerns separate:

| Configuration concern | Agreed handling |
|---|---|
| Coordination | Cache alias/key namespace, lock/progress lifetimes, retention and recovery timing, and permission to accept new jobs are supplied explicitly. Preserve existing defaults and cache identity during B; final fields/default resolution remain to be specified. |
| q2 execution | Keep the project's existing `Q_CLUSTER` as q2's configuration source. The internal q2 adapter handles q2 access and per-launch options; PowerCRUD does not require users to copy `Q_CLUSTER` into `POWERCRUD_SETTINGS`. |
| Optional tracking/custom manager | Keep model paths, field mappings, formatters, and other application-specific manager configuration separate from coordination settings. |

`ASYNC_ENABLED` stays in `POWERCRUD_SETTINGS`. Its intended coordinator meaning is permission to accept new jobs: disabling new submissions must still allow progress, completion, and cleanup of existing work. This follows A1/Q1. A name such as `ACCEPT_NEW_TASKS` was illustrative; no new public setting name is settled. Phase B establishes configuration plumbing while preserving current gating behavior; Phase C implements the agreed enforcement changes. Likewise, the agreed 24-hour terminal-result retention is a Phase C requirement, not an already implemented setting.

**B1-D2: Internal implementation location.** Put reusable implementation under `powercrud/_coordinator/` until extraction. That private package contains coordination/configuration/context, optional tracking/progress facilities, and the q2 adapter. Existing public `async_manager.py`, `async_hooks.py`, `async_context.py`, and `async_dashboard.py` remain compatibility entry points delegating to the reusable implementation and translating PowerCRUD configuration where needed. PowerCRUD bulk workers, persistence, view behavior, presentation, and sample code stay outside it. Reusable implementation may depend on Django and its adapter but must not import PowerCRUD configuration/logging helpers, CRUD mixins/views/templates, or sample code. Exact child modules and interface symbols remain to be specified; final standalone package naming remains Phase E work.

**B1-D3: Custom managers and legacy compatibility.** Keep coordination configuration separate from the existing custom manager `config` argument, which may already describe tracking or other application behavior. Preserve custom-manager import paths, subclass relationships, override behavior, and existing constructor signatures. Selected manager identity and application configuration must be available for reconstruction in workers/completion; the concrete metadata and injection mechanism remain to be designed. Full identity propagation and strict invalid-configuration behavior are Phase C outcomes.

Legacy projects should require no Phase B source/configuration changes for existing `AsyncManager()` calls, no-argument custom managers, managers accepting `config=...`, configured manager class paths, completion hooks, URLs, and cache keys. The compatibility layer must accommodate existing constructors instead of unconditionally adding a required argument. Preserve inheritance, `super()` calls, and type checks through one implementation rather than duplicated manager classes. This is an acceptance requirement, not a verified claim that regressions are impossible.

Before completing Phase B, verify representative legacy managers with and without `config`, subclass/lifecycle/completion overrides, inheritance/type checks, and existing import/hook/URL consumers. Separate intentional Phase C changes, including explicit launch enablement and invalid-manager rejection, from this structural work and document their migration impact in the owning phase.

**B1-D4: Completion routing and q2 result boundary.** Preserve `powercrud.async_hooks.task_completion_hook` as an importable legacy entry point. The q2 adapter translates q2 completion into ordinary coordinator data describing task identity, execution success/failure, and returned result. Coordinator lifecycle/cleanup consumes that data without depending on raw q2 models. Preserve custom completion overrides expecting a raw q2 Task through a compatibility bridge. Its exact dispatch/signatures, including overrides calling `super()`, remain to be specified; do not call both old and new handlers in a way that duplicates cleanup or lifecycle events. Phase B preserves current outcome interpretation; Phase C corrects business-outcome reporting, ordering, unknown status, and terminal retention.

**B1-D5: Progress endpoints and URLs.** Coordinator provides a reusable progress endpoint; the application owns URL mounting and access rules. Keep existing PowerCRUD URL names/helpers, including `powercrud:async_progress`, routed to that facility. Existing PowerCRUD projects should retain their URL configuration. PowerCRUD owns progress-modal/dashboard rendering. Phase B preserves existing response behavior; Phase C corrects missing-progress and terminal-outcome reporting. Endpoint construction must also satisfy the reconstruction requirements in D7 below.

**B1-D6: Cleanup and scheduling.** Coordinator owns reconciliation/cleanup logic and reports its outcomes. PowerCRUD retains `pcrud_cleanup_async` and `powercrud.schedules.cleanup_async_artifacts` as compatibility entry points. Applications choose manual invocation or scheduling; coordinator use must not automatically create a recurring job. The q2 adapter owns q2-specific result lookup and scheduling integration. Extraction provides a reusable cleanup function and a coordinator-owned management command for projects without PowerCRUD. Preserve current command/gating behavior during B; Phase C implements conservative cleanup and continued cleanup while new launches are disabled. Cleanup manager/configuration selection must satisfy D7 below.

**B1-D7: Carry resolved coordination configuration with task identity.** Pass a small serializable snapshot of resolved coordination configuration with the job, alongside the logical task key, importable manager class path, and separate application/tracking manager configuration. Values are configured once by the application and then carried across processes; this does not create a second user-maintained settings source. Do not serialize live connections, request objects, or the whole Django settings object. q2 worker/broker setup continues to come from `Q_CLUSTER`. Preserve the distinctions between logical task key, q2 execution ID, and manager identity; the snapshot supplements the existing identity mechanism. Its payload format, constructor integration, and lookup outside the queued job remain open design details.

##### D7 identity review: current behavior, original intent, and implications

Reviewed current source, existing test bodies, and original archived plans/introducing commits on 2026-11-07. This was static inspection; no tests or worker experiments ran. The original launch/dashboard implementation is in commit `67b447f6`; task context was introduced in `5031c502`. The archived [launch/conflict plan](../../../archive/blog/posts/20250805_async_planning.md), [dashboard plan](../../../archive/blog/posts/20251022_async_dashboard.md), and [context plan](../../../archive/blog/posts/20251022_async_task_context.md) explain the original requirements. Historical completion markers are not proof that the current implementation satisfies every stated requirement. The following findings are evidence and design implications, not newly completed hardening work.

| Identity | Current representation and purpose | Required distinction |
|---|---|---|
| Logical task key | UUID created before enqueue; used in lock values, progress keys, active membership, dashboard task name, and caller/polling feedback. | Preserve it across all stages; coordination must be able to reserve resources before q2 returns an execution ID. |
| q2 execution ID | Separate value returned by `async_task`; included in the create lifecycle payload and logs. Current generic state has no universal persisted mapping from logical key to this ID/result locator. | Keep separate from logical key and retain adapter execution/result identity where required; do not replace the logical key with the q2 ID during refactoring. |
| Manager identity/configuration | Importable class path plus optional application/tracking configuration supplied to worker/hook reconstruction. Coordination settings currently come from each process's PowerCRUD/Django settings. | Preserve selected custom behavior and add the resolved coordination snapshot as a separate concern. A manager class path alone cannot reproduce instance/configuration state. |

The current logical-key flow is explicit in [launch](../../../../src/powercrud/async_manager.py#L379): generate/accept key, reserve conflicts, initialize progress, supply the key as q2 `task_name` and worker `task_key`, then return the logical key. [Completion](../../../../src/powercrud/async_hooks.py#L58) reads `Task.name` and calls the reconstructed manager. The [consistency test](../../../../src/coordinator_tests/test_lifecycle.py#L297) checks launch return, supplied q2 name, worker key, and progress-key alignment with mocked enqueueing. It does not prove distributed reconstruction or real worker completion.

**Wrinkles and implications:**

1. **Trailing UUID positional convention.** Built-in bulk views pre-generate a UUID and append it to worker args ([call sites](../../../../src/powercrud/mixins/async_mixin.py#L403)). Launch removes the final UUID-looking string when no explicit `task_key` was supplied. This supports existing callers but can consume a legitimate UUID worker argument. Preserve legacy parsing at compatibility entry points; A1/C6 already requires explicit keyword task-key handling and unchanged arbitrary worker args in the new coordinator API. Specify legacy warning/migration behavior deliberately, rather than losing or reinterpreting arguments during B.
2. **Custom-manager reconstruction is explicit and incomplete.** Built-in views pass `manager_class` and `manager_config`; workers pop them and call `resolve_manager`, while hooks recover them from q2 kwargs. A direct launch on a custom manager does not automatically capture that manager's class/config. The resolver catches failures and falls back to the base manager; a rejected `config` constructor call may be retried without config ([resolver](../../../../src/powercrud/async_manager.py#L1231)). The new metadata must describe the selected manager, preserve old constructor signatures, and distinguish absent metadata from invalid explicit metadata. Preserve baseline fallback during B; automatic propagation and strict failure are Phase C corrections under issue 12.
3. **Class-versus-path precedence differs between launch construction and metadata.** `get_async_manager_class()` prefers an explicit class over a dotted path, but `get_async_manager_class_path()` prefers the dotted path when both exist ([selection methods](../../../../src/powercrud/mixins/async_mixin.py#L111)). A launch can therefore construct one manager and advertise another to worker/hook reconstruction. The design must derive coherent reconstruction identity from the actually selected manager, account for both configured forms, and assign any intentional precedence correction explicitly to the identity-hardening work. Do not assume the two current helpers always agree.
4. **Parent/descendant task identity was intentional.** The original context plan aimed to avoid independent child launches: descendant work should run inside the parent job, register its resources under the parent's key, and publish parent progress. Current `TaskContext` contains only task name and manager path; the descendant helper constructs the base manager, ignores the stored path, integer-coerces IDs, and ignores the acquisition return value ([context/helper](../../../../src/powercrud/async_context.py#L37)). The inspected bulk workers/persistence paths do not automatically enter `task_context` despite the old documentation saying they do. The [sample test](../../../../src/sample/tests/test_async_samples.py#L190) enters context explicitly and mocks manager/registration. Snapshot/reconstruction design must cover context and descendant helpers, keep the parent key, preserve original primary-key types in the reusable contract, and surface lock failures before protected child work. Do not introduce nested job orchestration; full protection/identity behavior belongs to Phase C.
5. **Polling and cleanup do not receive queued-job metadata automatically.** `as_view()` constructs `cls()` from the endpoint's bound class and receives a task name ([polling](../../../../src/powercrud/async_manager.py#L1052)); default PowerCRUD URLs bind the base manager. The current [command](../../../../src/powercrud/management/commands/pcrud_cleanup_async.py#L18) and [schedule](../../../../src/powercrud/schedules.py#L7) construct the base manager too. Sending a snapshot in q2 kwargs alone cannot make these paths recover the originating manager/cache/config. Decide where retained reconstruction metadata lives, how these callers find it from application configuration plus task key, and what happens if it is absent or expired. Avoid requiring a sample/dashboard model merely to recover metadata. Cache alias/namespace discovery must be explicit; a task key by itself does not identify a cache connection.
6. **Serialized kwargs and custom config need deliberate handling.** Hooks accept dict kwargs or parse string kwargs using JSON/literal parsing, but accept `manager_config` only when it is a dict ([parsing/extraction](../../../../src/powercrud/async_hooks.py#L20)). `AsyncDashboardConfig` can contain Python formatter callables ([configuration](../../../../src/powercrud/async_dashboard.py#L21)). The new coordination snapshot must not silently replace/drop existing manager config or assume arbitrary application objects are plain serialized values. Define worker-reconstructible metadata and compatibility treatment for supported manager configuration; retain application-owned dotted paths/subclasses where needed.
7. **Progress helpers use inconsistent key/manager conventions.** Launch injects `task_key`; built-in workers accept it with a `task_name` fallback. The progress decorator instead looks only for `task_name` and creates a base manager ([decorator](../../../../src/powercrud/async_hooks.py#L124)); the sample model's parent-context progress also creates a base manager. Include these paths in identity/config propagation and legacy alias handling; a correct worker constructor alone does not establish consistent progress behavior.

Design acceptance must follow one logical key and coherent selected manager/application config/coordination snapshot through launch, worker, completion, parent context/descendants, progress helpers, polling, and cleanup. Retain a distinct q2 execution identity/result locator. Cover conflicts between metadata sources, absent/invalid metadata, custom constructors, serialized kwargs, literal UUID worker args, and metadata expiry/cache loss in the owning verification phase. Existing mocked consistency, resolver, hook, and explicit-context tests are useful baselines; none proves all these paths today.

**Cleanup clarification and decision status.** D1–D7 remain valid and agreed. Cleanup must identify the correct task/execution and manager, establish that cleanup is safe, and remove only that task's owned artifacts. Use the strengthened identity and lifecycle information already required by A1/C1, C5, and C6.

The following specification completes that design work. Earlier statements that exact details remained open record the discussion stage; the specification governs those implementation details. D1–D7 and the historical identity findings remain intact. No hardening-register issue is completed by specifying its interface or future acceptance criteria.

#### B1 technical specification — 2026-11-07

**Status: complete at the specification level.** This section specifies the B2–B3 structural implementation and the interfaces needed by Phase C. Phase B uses one direct q2 submission path, a shared tracking mixin, and existing cache lifetimes. Phase C's identity retention, backend algorithms, and behavior fixes remain its own work. No code or tests have changed. The source review used clean starting commit `67c72229`; the audit remains the dependency baseline.

##### 1. Configuration and construction

Use a frozen, keyword-only `CoordinatorConfig` dataclass in `_coordinator/config.py`. It contains the following fields. Defaults are defined once there; PowerCRUD's existing `conf.DEFAULTS` retains its public keys by mapping the corresponding internal defaults. Importing the defaults module must not access Django settings, caches, or q2.

| Internal field | Type / default | PowerCRUD source | Phase assignment |
|---|---|---|---|
| `enabled` | `bool = False` | `ASYNC_ENABLED` | Carry in B; enforce new-launch gating in C. Existing-task operations do not use it as a cleanup gate after C. |
| `cache_name` | `str = "default"` | `CACHE_NAME` | B. Django `CACHES` remains the connection source. |
| `key_namespace` | `str = "powercrud"` | Existing fixed prefixes; no new global PowerCRUD setting in B. Explicit non-PowerCRUD callers can override this field. | B, preserving legacy defaults exactly. |
| `key_prefixes` | `dict or None = None` | No new global setting. When `None`, derive the four existing prefix attributes from `key_namespace`; exported snapshots include their resolved values to preserve custom manager overrides. | B. Keys are exactly `active_prefix`, `conflict_prefix`, `conflict_model_prefix`, and `progress_prefix`. |
| `conflict_ttl` | `int = 3600` | `CONFLICT_TTL` | B preserves current cache TTL behavior. Renewal/ownership semantics are C. |
| `progress_ttl` | `int = 7200` | `PROGRESS_TTL` | B preserves current live-progress TTL. |
| `cleanup_grace_period` | `int = 86400` | `CLEANUP_GRACE_PERIOD` | B preserves its actual use as active-membership expiry; do not reinterpret it as proof of abandonment. |
| `max_task_duration` | `int or None = 3600` | `MAX_TASK_DURATION` | B preserves current truthy/falsey handling, including zero disabling the age check. Safe recovery semantics are C. |
| `terminal_result_ttl` | `int = 86400` | Reserve `TERMINAL_RESULT_TTL` for C, with this fallback. | Internal field may exist in B; terminal storage/enforcement and public documentation begin in C. |

`CLEANUP_SCHEDULE_INTERVAL` (300 seconds) and `QCLUSTER_PROBE_TIMEOUT_MS` (300 milliseconds) belong to integration/adapter configuration, not the coordination snapshot. The public manager preserves its existing `cleanup_schedule_interval` attribute; `validate_async_qcluster(timeout_ms=None)` uses the translated probe default. Ordinary callers use `Q2Adapter(probe_timeout_ms=300)` and choose their own cleanup schedule. These values never create or alter a schedule automatically. Other PowerCRUD settings remain with PowerCRUD.

Preserve PowerCRUD setting lookup precedence: a defined user value, including `None`, wins; otherwise use the existing explicit helper fallback/default behavior. Keep the existing non-dict setting error. Do not add stricter value validation, coerce strings into booleans, or change falsey-value semantics as part of B. C supplies targeted explicit-use validation. `CoordinatorConfig.to_snapshot()` / `from_snapshot(mapping)` round-trip exactly the fields above in a mapping with `version: 1`; no Django objects, q2 settings, or application manager config are included.

The internal manager constructor is `AsyncManager(*, coordination_config=None, executor=None)`. Effective configuration is an explicitly supplied `CoordinatorConfig`, then a scoped construction binding, otherwise an `ImproperlyConfigured` error explaining that explicit configuration is required. This check occurs at construction, not import. The default executor is a lazily created `Q2Adapter`; importing or constructing its lightweight Python object does not load q2 runtime modules. Queue settings are accessed only by adapter operations.

The public compatibility constructor has the same optional keywords and adds the final fallback of translating current `POWERCRUD_SETTINGS`. Existing no-argument calls remain valid. Keep `cache_name`, `cache`, TTL attributes, prefix attributes, and cache/validation method overrides observable; effective task snapshots use the manager's resolved attributes after construction, not merely the original default config. `qcluster_settings` remains a lazy public compatibility property backed by the adapter's cluster-settings mapping; legacy assignment supplies that mapping to the adapter. This preserves access without reading queue settings during dormant imports or ordinary construction.

Custom manager application config continues using the existing `config` argument. Class attributes/defaults continue to work. Manager class selection and application-config precedence stay as currently implemented during B; specifically, do not silently fix the conflicting class/path precedence described in wrinkle 3. C derives reconstruction identity from the selected instance and rejects inconsistent explicit metadata.

Use `reconstruction.construct_manager(spec, *, coordination_config, executor, legacy=False, fallback_class_path=None, prepare_config=None)` to construct configured manager classes. It scopes the coordination config/executor in a `ContextVar`, invokes the normal constructor with its existing `config` argument where supplied, and resets the binding in `finally`. Public/core base constructors consume this binding through normal `super()` calls. Never add required kwargs to an arbitrary legacy subclass, bypass `__init__`, mutate process-global settings, or replace the manager after its constructor has run. Legacy resolution retains current `TypeError` retry/default-manager fallback during B; strict reconstruction is C. Public `resolve_manager` passes its own `cls` import path as the fallback and `cls._coerce_manager_config` as the preparation callback; core callers default to the internal base and the selected class's preparation hook. This preserves subclass fallback and existing overrides without an internal import of public wrappers. An override which never calls the base initializer remains responsible for its own initialization, as today.

The base class provides `prepare_manager_config(config)` (identity conversion) and `export_manager_config()` (the constructor config retained by the factory, or `None`). Tracking overrides these to convert a mapping to `AsyncDashboardConfig` and export its effective `_config`. This removes generic resolver imports of tracking. Retain the existing public `_coerce_manager_config(manager_cls, config)` entry point as delegation, preserving user overrides on that compatibility path. Tracking configs, importable formatter functions, and existing q2-serializable application config retain their Python values; do not convert them to strings or force JSON. Unsupported closures/live objects are explicit-use validation failures in C, not silently dropped settings.

`get_coordination_config()` returns the effective snapshot source from the initialized manager attributes, retaining configured overrides. Core `completion_style` defaults to `"core"`; the public base sets it to `"legacy"`, and subclasses inherit it. A directly constructed custom manager with additional constructor-only state exposes it through `export_manager_config()` when using the new internal API; the factory already retains supplied config for factory-created instances. Do not claim arbitrary Python instance state can be inferred automatically. Existing direct legacy launches keep their current explicit metadata behavior in B; C validates the reconstruction/export contract.

##### 2. Modules, types, and minimum interfaces

All paths in this table are below `powercrud/`. `_coordinator/__init__.py` remains lightweight and does not import q2 or resolve settings.

| Module | Contents and allowed dependencies |
|---|---|
| `_coordinator/config.py` | `CoordinatorConfig`, primitive defaults and snapshot conversion; standard library only. |
| `_coordinator/types.py` | Plain call, manager-description, execution-reference, completion, and lookup types; no q2/Django model types. Retained identity fields below are a C contract, not an extra B implementation. |
| `_coordinator/manager.py` | Internal `AsyncManager`; existing locks, active membership, progress, lifecycle and reconciliation methods. Django cache/time utilities, internal config/types/reconstruction, and executor calls only. |
| `_coordinator/reconstruction.py` | Manager import/construction scope and config preparation/export. Standard library and internal types; configured application class imports are permitted, hard-coded PowerCRUD wrapper imports are not. |
| `_coordinator/state.py` | Reserved for C's retained task identity/lifecycle state. Do not create an unused module or new persistent task record during B; existing cache operations stay in the manager. |
| `_coordinator/q2.py` | All direct q2 imports/calls, option handling, result lookup/translation, completion dispatch and probes. Runtime q2 imports occur inside operations. |
| `_coordinator/context.py` | Shared `TaskContext`/`ContextVar`, context helpers and parent-manager access; no CRUD or sample dependencies. |
| `_coordinator/tracking.py` | `AsyncDashboardConfig`, shared `ModelTrackingMixin`, and internal `ModelTrackingAsyncManager`; Django model resolution and internal manager only. |
| `_coordinator/views.py` | `progress_view(*, manager_factory, template_name=None)`; Django request/response helpers and the supplied factory. No PowerCRUD templates, URL names, or settings. |
| `async_manager.py`, `async_hooks.py`, `async_context.py`, `async_dashboard.py` | Public compatibility wrappers/re-exports, PowerCRUD settings translation, legacy call normalization and URL/hook routing. They may import internal implementation; internal implementation must not import them. |

Use standard-library loggers inside `_coordinator`, with no global logging setup or imported `powercrud.logging` helper. Existing public command/schedule logging and output stay in their wrappers. All source modules remain in the current PowerCRUD distribution for B; standalone naming, external packaging and release wiring remain E/F.

The internal data types are deliberately small:

| Type | Fields / interpretation |
|---|---|
| `ManagerSpec` | `class_path: str or None`, `config: object or None`, `completion_style: "core" or "legacy"`. A missing path is allowed only for the retained legacy default. Class/config are otherwise importable/reconstructible; config is separate from coordination settings. |
| `TaskCall` | `func`, `args: tuple`, `kwargs: dict`, `task_key: str`, `conflict_ids`, `user`, `affected_objects`, `manager: ManagerSpec`, `coordination: dict`. Internal submission description; q2 receives the original callable/args/kwargs directly. |
| `ExecutionRef` | `backend: str = "q2"`, `id: str or None`, `locator: dict`. Locator is adapter-owned result-routing/options data; the coordinator stores/passes it without interpreting q2 fields. No live broker/cache connection is retained. |
| `Completion` | `task_key`, `execution: ExecutionRef or None`, `success: bool or None`, `result: object`, `started_at`, `finished_at`. Execution evidence only; ordinary `False` results are not classified as business failure. |
| `ResultLookup` | `kind: "found", "missing", or "unavailable"`, `completion: Completion or None`, `reason: str or None`. Missing retained results are distinct from lookup failure and do not imply abandonment. |
| `TaskIdentity` | C-owned retained state: `version: 1`, `task_key`, `manager: ManagerSpec`, `coordination: dict`, `execution: ExecutionRef or None`. Specifies required identity information; no cache writes or expiry policy for this type in B. |

Keep optional timestamps timezone-aware. Worker args/results retain their existing serialization behavior; only coordination snapshot values are constrained to primitive configuration data. A live broker object remains a supported legacy submission argument handled inside the adapter. For retained lookup, the adapter uses its configured broker/cluster route; applications using a custom broker must supply the same configured adapter instance/factory to lookup operations. Never pretend a live broker object can be serialized as a general result locator.

Minimum callable interfaces:

```text
AsyncManager.launch(func, *args, worker_kwargs=None, task_key=None,
                    conflict_ids=None, user=None, affected_objects=None,
                    execution_options=None) -> str
AsyncManager.complete(completion: Completion) -> None
AsyncManager.as_view(*, manager_factory, template_name=None) -> view

Q2Adapter.submit(call: TaskCall, *, options=None) -> ExecutionRef
Q2Adapter.lookup(ref: ExecutionRef, *, wait_ms=0) -> ResultLookup
Q2Adapter.lookup_legacy_name(task_key, *, wait_ms=0, orm_only=False) -> ResultLookup
Q2Adapter.to_completion(raw_task, *, task_key=None) -> Completion
Q2Adapter.probe(*, timeout_ms=None) -> bool
q2.task_completion_hook(raw_task) -> None
q2.dispatch_completion(raw_task, *, legacy_factory=None) -> None
```

`Q2Adapter(*, probe_timeout_ms=300, broker_factory=None)` is lightweight; `broker_factory` is an optional application callable used to recreate an explicitly configured custom broker for operations, not serialized with jobs. Its `cluster_settings` property lazily reads `getattr(settings, "Q_CLUSTER", {})` unless a legacy override mapping was assigned. Its retained `ExecutionRef.locator` contains `cached` (bool or expiry value), `cluster` (name or `None`), and `options` (effective serializable q2 options, omitting the live broker). ORM lookup uses the execution ID with `fetch(..., cached=False)`; cached lookup uses `fetch_cached(..., broker=resolved_broker)`. Legacy status methods retain the existing wait values of 300 and 0 milliseconds, and cleanup retains its ORM-only name query. Adapter lookup returns `unavailable` on read/route failure and `missing` only on a successful absent-result lookup; wrappers preserve current error handling during B.

Retain existing lock/progress/state/lifecycle method signatures when moving their implementation. `_launch(call, *, options=None)` is the one shared reservation/progress/submission/registration/create sequence used by the internal launch method and legacy wrapper. It calls `executor.submit` in both cases. Public wrappers normalize legacy arguments before entering it; they do not select a different worker implementation or transport format. The adapter is the sole existing execution integration; no backend registry or general plugin framework is introduced.

`launch()` uses keyword task identity, preserves all positional worker arguments including a final UUID, and keeps adapter execution options separate from `worker_kwargs`. Its documented coordination metadata is passed explicitly to workers as specified below. The public `launch_async_task()` preserves its current signature, q2-shaped options, trailing-UUID normalization, worker `task_key` injection and string return. Keep legacy alias handling and exceptions during B; C introduces the agreed deprecation warning and strict conflicts/validation. Names chosen here are internal interfaces, not the final extracted-package branding.

##### 3. Submission, snapshot transport, and completion dispatch

**Use one direct q2 submission implementation.** `Q2Adapter.submit` always enqueues the original callable and its positional/keyword arguments. The public wrapper preserves existing q2 `Task.func`, `args`, `kwargs`, hook path and return behavior. Existing manager-class/config kwargs remain supported; no new metadata kwargs are injected into legacy workers. The internal `launch` uses the same adapter and coordination sequence after preparing its explicit arguments.

For the new internal API, workers accept `task_key`, `manager_class`, `manager_config`, and `_coordinator_config` as keyword metadata, either explicitly or through `**kwargs`. `_coordinator_config` is the small versioned coordination snapshot; the other names reuse the existing conventions. `launch` prepares these values in worker kwargs from its selected manager/config, rejecting conflicting reserved values on this new API. The original worker function receives them directly and uses `construct_manager` under the supplied snapshot when it needs manager behavior. Built-in CRUD workers already accept `**kwargs`; they consume the optional snapshot under the construction scope before calling the existing manager resolver, and follow their unchanged reconstruction route when it is absent. Arbitrary legacy functions acquire no new argument requirements. C handles automatic identity/context propagation and any broader worker integration changes needed by the final contract.

The logical key remains q2's supplied task name and the key returned to callers. `submit` returns the separate execution ID/result route in `ExecutionRef` without creating new persistent identity state during B. Internal `launch` supplies `powercrud._coordinator.q2.task_completion_hook`; the public wrapper supplies the existing `powercrud.async_hooks.task_completion_hook`. The adapter passes options through rather than flattening/reinterpreting them, preserving q2 handling of `q_options`, explicit `sync=False`/`cached=False`, timeout fallback and optional `save`. Custom-hook overrides remain honored; reliable completion under supported hook/save/cache combinations is a Phase C repair.

Both hook entry points delegate to `dispatch_completion`. For explicit internal submissions, it reconstructs from the snapshot and manager metadata in task kwargs. For existing submissions, the public hook supplies the existing PowerCRUD manager factory; the adapter does not import public wrappers. Keep existing dict/string kwargs parsing helpers and their legacy behavior, including dict-only `manager_config` extraction. Explicit internal submissions preserve their supported manager config values separately from that legacy extraction rule.

A core manager uses `complete(Completion)`. A manager with `completion_style="legacy"` receives exactly one call to `handle_task_completion(raw_task, logical_key)` with the actual q2 Task. The public base translates that task through `to_completion` and calls `self.complete(...)`. An override calling `super()` therefore reaches core handling once; an override without `super()` retains its existing responsibility for cleanup/events. Never also call `complete` after a legacy override. Repeated notifications and terminal monotonicity remain C work.

Public `AsyncManager` subclasses the internal manager and supplies settings/default compatibility, legacy launch/resolution/completion, and URL helpers. Share tracking behavior through `ModelTrackingMixin`, which does not inherit either manager. Internal tracking is `ModelTrackingAsyncManager(ModelTrackingMixin, InternalAsyncManager)`; public tracking is `ModelTrackingAsyncManager(ModelTrackingMixin, PublicAsyncManager)`. The mixin's constructor accepts existing tracking `config` plus the optional coordination/executor keywords and calls `super()` once. Each manager has one manager-base chain, and public tracking retains its public `AsyncManager` relationship. Re-export the same `AsyncDashboardConfig` class object. Verify constructors, overrides, `super()` and type checks during B3; do not duplicate tracking behavior.

**Dependency evidence:** Context7 documentation was checked, then matching q2 **v1.11.1** primary source was read for [submission/options and fetch](https://github.com/django-q2/django-q2/blob/v1.11.1/django_q/tasks.py), [stored task fields](https://github.com/django-q2/django-q2/blob/v1.11.1/django_q/models.py), and [completion-hook dispatch](https://github.com/django-q2/django-q2/blob/v1.11.1/django_q/signals.py). In that tag, kwargs use a pickled field and hooks receive Task instances. Option precedence has exceptions: an explicit task name wins over `q_options.task_name`. Preserve dependency behavior rather than relying on a blanket option-merging rule. This was remote source inspection, not installed-version or supported-range/runtime verification. No q2 version-floor or support reduction is selected.

##### 4. Task identity, polling, and cleanup lookup

**B preserves existing task-state storage and expiry.** Move the current active-set, lock, tracking-set and progress operations with their existing keys, values and TTLs. Retain manager metadata in existing job kwargs and carry the explicit internal API's coordination snapshot as described above. Do not introduce `TaskIdentity` cache writes, extra persistence failure handling, or a new retention formula during structural refactoring.

**C implements retained identity with the lifecycle work already required by A1.** `TaskIdentity` supplies the logical key, manager/configuration snapshot, and q2 execution/result reference needed for later reconstruction. It belongs to the configured coordination location alongside that task's lifecycle state. The planned key is `{key_namespace}:async:task:{task_key}` and the minimal operations are `get_identity`, `put_identity`, and `attach_execution`. These are C interfaces; B code must not call unimplemented state operations. Persist versioned mappings rather than internal Python dataclass instances; retain supported application config values. No new database model is required.

Identity must remain available while supported work is live and through the retained terminal-result period, whose agreed default is 24 hours from completion. C defines writes, refresh, expiry and failure handling together with lifecycle/lease behavior. Missing or expired identity is insufficient evidence, never proof of success or stopped execution. Required identity retention remains part of D7/A1; only its runtime implementation is assigned to C.

During B, preserve legacy metadata precedence/fallback; absent metadata still selects the documented base default. The explicit internal API exports its selected manager spec and coordination snapshot into worker kwargs. C unifies automatic capture across supported paths, reconciles conflicting key/class metadata, and makes invalid explicit configuration visible. Snapshot values describe the existing job; new launches must obtain current application enablement rather than treating a previously captured flag as continuing permission to launch work.

Applications bind a manager factory to each endpoint/cleanup invocation, selecting the cache alias/namespace to examine. The default PowerCRUD endpoint/command/schedule uses its existing configured cache/prefixes and public base manager. Existing per-view/custom managers using that location need no URL change. A custom manager using another cache/location must be explicitly bound to a corresponding endpoint or cleanup call, just as a cache connection requires application configuration today. Do not scan arbitrary Django caches or add a new deployment-wide discovery setting. A cleanup command inspects its selected coordination location only.

In B, polling uses the bound factory and current cache strings/status, preserving existing responses. C adds keyed reconstruction: read retained task identity in the selected location, bind its snapshot, reconstruct the manager, and pass the execution reference to the adapter. Confirm key and cache/namespace consistency; a stored record must not redirect lookup to an unrelated location. Polling, cleanup and helpers then share that identity information rather than independently guessing a manager. No cross-cache discovery mechanism is required.

Cleanup uses existing active membership as its inspection set. Through B, `cleanup_completed_tasks()` retains its current ORM-only task-name result interpretation and summary shape via `lookup_legacy_name(..., orm_only=True)`. Do not change missing-row cleanup policy during adapter extraction. C uses retained identity/execution references and the agreed conservative reconciliation policy: missing/pruned results or unreadable identity are uncertain; lookup failures are reported/skipped; release requires safe owner evidence, and force cleanup must be explicit. Lifecycle state will hold submission/start/lease/terminal evidence under A1; backend-specific lock/renewal algorithms remain C work.

`views.progress_view` accepts a factory rather than importing settings. The public `as_view(template_name=None)` retains its existing signature and binds `cls()`; `get_url()` and `get_urlpatterns()` retain default patterns/names and the PowerCRUD namespace. Public command/schedule wrappers retain current enablement gates and output/logging during B. No schedule registration is added. Reusable manager factories and the existing cleanup methods suffice internally; the extracted command/settings namespace is E work.

##### 5. Seven identity wrinkles: implementation assignment

| Wrinkle | B2–B3 specification | Intentional C correction / verification |
|---|---|---|
| Final positional UUID | Public wrapper keeps current parsing; internal `launch` uses an explicit key and preserves worker args. | Warn/deprecate legacy parsing as agreed; verify literal UUID args and conflicting aliases. |
| Direct/custom reconstruction and fallback | Scoped construction binding, separate manager/coordination config, preserved legacy fallback; explicit internal identity export. | Automatic capture for legacy/direct paths and strict invalid-config errors. |
| Class/path precedence mismatch | Preserve current legacy selection/advertised metadata and record it accurately. | Derive coherent identity from actual selected manager and test conflicting declarations. |
| Parent/descendant work | One shared context object and explicit helpers; preserve legacy integer conversion/base-manager behavior in wrappers. | Enter context automatically in supported worker paths, use selected manager, preserve PK types, and stop protected work on acquisition failure. |
| Polling/cleanup reconstruction | Explicit location-bound factories and adapter result interfaces; preserve existing storage, response and cleanup policy. | Retain identity/execution evidence, use it for shared reconstruction, and enforce conservative cleanup and owner-safe release. |
| Serialized kwargs/application config | Preserve existing direct callable/kwargs transport and legacy parsing; explicit internal calls carry the snapshot in a distinct kwarg. | Validate importability/serialization and reject invalid explicit metadata; verify real saved/cached q2 result modes. |
| Progress helper aliases/base manager | Preserve public decorator behavior and shared context/helper entry points. | Normalize aliases at compatibility boundaries and use parent manager/config for helpers/sample progress. |

These assignments preserve known incorrect legacy expectations during structural refactoring. They do not certify those expectations as the final contract. B3 adds explicit configuration and snapshot reconstruction tests while retaining one submission implementation; lifecycle persistence and policy changes remain C work.

##### 6. B2–B3 handoff and source-review acceptance

**B2:** introduce the plain completion/reference/lookup types and `_coordinator/q2.py`; move all q2 imports, enqueue/fetch/ORM queries, hook parsing/translation and probes there. Keep public manager state algorithms in place while adapting them to normalized adapter results. Preserve exact legacy enqueue argument/hook behavior, wait values, cleanup summaries, and resolver fallback. Exercise adapter seams with focused coordinator tests and retain hook/URL consumer checks. No production implementation is part of this B1 documentation commit.

**B3:** move config/manager/reconstruction/context/tracking/views into the internal package; implement settings mapping, constructor binding, shared tracking mixin, public wrappers and manager factories. Use the one direct q2 submission implementation. Built-in workers and hooks consume a coordination snapshot only when the explicit internal API supplied it; legacy calls receive no extra kwargs and keep their current reconstruction behavior. Coordinator settings use explicit `CoordinatorConfig` and suite-owned factories and remove `POWERCRUD_SETTINGS`; no PowerCRUD/sample app installation is added. Do not implement retained identity storage/expiry or other C-assigned fixes during the move.

**Test ownership and patch targets:** q2 mocks move from `powercrud.async_manager.async_task`, `fetch`, and `Task` to lazy adapter-loading/operation seams in `_coordinator.q2`. Generic state tests use internal managers with explicit config; reconstruction/context/tracking helpers use internal modules and suite-owned models. Old public paths, constructor/MRO checks, q2 argument-shape assertions and legacy fallback/deprecation expectations belong to consumer compatibility tests. Update the A3 mapping when an assertion moves owner; preserve every distinct baseline assertion/outcome rather than merely keeping a test count. Helpers that test current bad behavior must label it as retained until C.

Strengthen suite isolation to reject `powercrud.conf`, `powercrud.logging`, public async compatibility modules, CRUD mixins/views and sample imports from the reusable suite after execution. Internal managers/URLs/workers must use explicit suite config/factories. Literal old hook strings may be exercised in adapter tests without importing consumer wrappers; actual wrapper invocation belongs in consumer tests. Update `.coveragerc-coordinator` to measure `_coordinator` source and keep existing separate raw/combined artifact paths. Retain runner settings/process isolation and CI selections; no broader runner redesign is needed.

The following review checked each scenario against current source and the specified route. Results are design acceptance, not runtime passes:

| Scenario | Specified route / required later check |
|---|---|
| Ordinary Django/direct launch | Explicit config and internal `launch`; no PowerCRUD settings/helpers; original callable is submitted directly with its documented metadata kwargs. |
| PowerCRUD bulk update/delete | Existing view selection and legacy launch signature; same worker paths/kwargs/logical key and persistence payload; optional snapshot handling does not alter jobs without one. |
| No-argument/custom `config` constructors | Scoped normal construction reaches the base with explicit coordination config; app config keeps its meaning; legacy retry behavior preserved. |
| Completion/lifecycle overrides and `super()` | Actual raw task sent once to legacy override; base translates once to core completion; no-super override retains old responsibilities. |
| Inheritance/type checks | Shared tracking mixin with one manager-base chain per tracking class; public tracking remains a public-base subclass; config class re-export is the same object. |
| Parent context/descendants/progress | Shared context retained; legacy behavior remains explicit; C tests automatic entry, correct manager, acquisition failures and non-integer PKs. |
| Polling and manual/scheduled cleanup | Factory chooses existing location; responses/output/gates/storage retained in B. C uses retained identity and enforces safe missing-evidence policy. |
| UUID and aliases | Legacy wrapper parses as today; internal path keeps positional UUID; C adds warning/strict normalization. |
| Missing q2 or unconfigured settings | Config/types/imports remain inert; q2 loading delayed to operations; comprehensive targeted-error/absent-distribution proof remains C/D. |
| Cache loss, expired metadata, fast/sync completion | No success/abandonment guarantee inferred from absence in final contract; C verifies identity retention, monotonic state and conservative cleanup. Legacy B behavior remains separately pinned. |

Review found no need to change D1–D7, A1 guarantees, supported cache/q2 claims, or legacy compatibility duration. Configuration, module placement, constructor binding, one direct submission implementation, shared tracking behavior, completion dispatch and test handoff are specified for B2–B3. Identity retention/recovery requirements remain specified for C alongside lifecycle policy and backend proofs. No technical choice needed for B2–B3 is deferred to their implementer, and no new user decision is pending. B2–B4 are complete; hardening issues 1–13 remain open.

### B2: Isolate q2 execution

Move direct q2 imports and calls behind the adapter, including manager enqueue/fetch/cleanup queries, hook translation, and q2 probes. Keep adapter result representations independent of raw q2 models outside legacy hook entry points. Preserve the current interpretation of execution results until the intentional outcome work in Phase C.

Inventory effective options, including per-call `q_options` overrides, rather than assuming manager defaults win. Maintain the distinction between broker transport, result storage, and the logical coordinator key versus q2 execution ID. Preserve currently claimed modes; isolating the adapter does not permit dropping cached results or silently imposing an ORM-only contract.

Dependency access should become adapter-owned and delayed. Record any import-safety improvement and its focused verification separately from the broader issue 1–4 acceptance scenarios. Full targeted validation and genuine absent-distribution proof remain assigned to C/D and later artifact verification.

Keep completion callable import paths usable by workers. Retarget coordinator tests from `powercrud.async_manager.async_task`, `fetch`, and `Task` only when those dependencies actually move. Retain consumer checks for legacy imports, configured hooks, and URL wiring. Do not create a second implementation to satisfy old patch targets.

#### B2 implementation and verification — 2026-11-07

Implemented on `async_hardening/phase_b` from `e32676a4`. Added lightweight `_coordinator` types and `Q2Adapter`; q2 task/model imports, submission, result access, ORM cleanup lookup, completion parsing/translation, health probes, and dependency detection now pass through adapter-owned lazy seams. The manager retains its reservation, progress, registration, lifecycle, and cleanup algorithms. Existing schedule and management-command wrappers were left in place.

Preserved direct callable submission, worker arguments and `task_key`, legacy hook string, option dictionary merge order, `Q_CLUSTER` timeout fallback, `q_options`, optional `save`, live broker forwarding, q2 execution ID lifecycle payload, the blocking/non-blocking wait values, ORM-only cleanup interpretation, missing-row cleanup, status/error behavior, and legacy manager fallback. Completion dispatch sends the raw q2 Task to the legacy override once; the base handler translates it to `Completion`, so `super()` performs core lifecycle handling once. Legacy imports, URL behavior, custom hook overrides, and q2 availability checks remain compatible. The logical task key remains separate from `ExecutionRef.id`.

The coordinator coverage configuration now includes `_coordinator`. Focused adapter, hook, lifecycle, and lock tests passed: 70 passed. Full server suites were run through the repository container runner:

```text
./runproj exec "./runtests --suite coordinator --pytest"
125 passed; Python 3.14.6; Django 6.1.2.

./runproj exec "./runtests --suite powercrud --pytest"
1,056 passed, 23 skipped, 110 deselected, 8 warnings.
The runner also completed its separate minimal-settings selection (4 passed)
and Bootstrap server selection (31 passed).
```

The project lock pins django-q2 1.11.1; the test output did not independently report the installed q2 version. Adapter tests use mocks and do not establish real worker delivery. No concurrency, cached-result hook, supported-q2-range, or distributed backend guarantee is claimed. The previous source evidence remains specific to q2 1.11.1. Missing-progress success, invalid-manager fallback, current registration ordering, and missing-result cleanup remain intentionally unchanged for Phase C. At this B2 checkpoint, hardening issues 1–13 were open and B3–B4 were incomplete.

**Separate follow-up evidence after the async bulk-payload fix:** the handover records a later full PowerCRUD run with **1,057 passed, 23 skipped, and 110 deselected**, followed by **4 minimal-settings** and **31 Bootstrap** passes. The two focused selections for that fix passed **61** and **34** tests. These results supersede the 1,056-pass B2-era consumer count for current branch evidence; they do not rewrite the historical B2 verification above. The handover did not include the exact focused node selections, so they are not reconstructed here.

### B3: Separate coordination from PowerCRUD integration

Reusable implementation must not import PowerCRUD views, mixins, templates, configuration/logging helpers, sample models, or PowerCRUD-specific URL resolution. Framework-facing endpoints should be separable from the service; applications own mounting and authorization. Optional tracking consumes the coordinator lifecycle; sample formatting and dashboard CRUD remain consumer behavior.

PowerCRUD compatibility wrappers may translate defaults, settings, paths, and legacy arguments into the reusable seam. Coordinator settings must stop supplying `POWERCRUD_SETTINGS` after this seam is available. Strengthen the suite import checks to detect consumer configuration dependencies while allowing the internal implementation's actual module paths. Extraction later moves this suite with the implementation; it does not create a permanently duplicated suite.

Preserve known baseline expectations until their owning Phase C fixes: missing progress reported as success, invalid explicit manager fallback, current registration/create ordering, existing cleanup/result-row rules, and current lock/registry behavior. Preserve worker argument handling through legacy entry points; the strict new API and deprecated trailing-UUID compatibility behavior require an explicit implementation/verification decision under C6. Do not claim the manager identity or UUID issue solved by relocating helpers.

#### B3 implementation and verification — 2026-11-07

Implemented the B1 boundary on `async_hardening/phase_b`. `_coordinator` now owns immutable versioned coordination configuration, context storage, reconstruction, the manager algorithms, tracking mixin, progress response algorithm, and q2 completion dispatch. The public manager translates PowerCRUD settings and preserves the legacy constructor, launch, resolver, hook, URL, and qcluster interfaces. Both CRUD workers consume a coordinator snapshot only when present; snapshot-free calls keep their established resolver arguments. Internal and public tracking classes share `AsyncDashboardConfig` and the tracking mixin while retaining their respective manager inheritance chains. The coordinator suite uses explicit configuration and factories and no longer defines `POWERCRUD_SETTINGS`.

The A3 ownership ledger remains historical. This implementation adds an ownership addendum: generic manager state/lifecycle, context, tracking, q2 completion, and progress endpoint assertions now exercise `_coordinator` modules; public settings translation, legacy UUID parsing and transport shape, resolver/hook compatibility, public context/decorator behavior, and CRUD worker reconstruction assertions live in the PowerCRUD consumer suite. Existing actual tracking ORM checks and sample CRUD integration assertions remain in their owning consumer coverage.

Verification ran through the repository container runner on Python 3.14.6, Django 6.1.2, pytest 8.4.2:

```text
./runproj exec "./runtests --suite coordinator --pytest"
132 passed in 13.67s; coordinator coverage 85% (957 statements, 140 missed).

./runproj exec "./runtests --suite powercrud --pytest"
1,066 passed, 23 skipped, 110 deselected, 8 warnings in 26.56s.
Separate minimal-settings selection: 4 passed in 6.72s.
Separate Bootstrap selection: 31 passed in 6.82s.
```

The eight consumer warnings are existing deprecation warnings for modal class options and `get_list_cell_link` modal options. Coverage output retains the established artifacts; `.coveragerc-coordinator` measures only `_coordinator`. `git diff --check` passed, and the internal import scan found only the intentional legacy q2 hook path string in `_coordinator/q2.py`; the suite import guard rejects PowerCRUD configuration/logging, public async wrappers/hooks/context/dashboard, CRUD view/mixin modules, and sample modules. Separate handover evidence after the bulk-payload fix remains recorded above (1,057 consumer passes, 4 minimal-settings passes, 31 Bootstrap passes, and focused selections of 61 and 34); it is historical evidence and is not replaced by the B3 rerun.

The tests verify behavior through patched enqueue seams, inline suite workers, and sequential cache interactions. They do not demonstrate real q2 worker delivery, distributed cache concurrency, locking correctness, or backend support. No Phase C policy changes were made: enablement enforcement, outcome corrections, ordering changes, automatic context propagation, identity retention/expiry, reconciliation changes, concurrency fixes, stricter legacy validation, and UUID deprecation remain open. At this B3 checkpoint, B4 review/handoff and Phase B overall completion were still pending; the later B4 record below completes that work while retaining all hardening issues open.

### B4: Verify behavior preservation and hand over

Place adapter/core tests in `src/coordinator_tests/`; keep settings translation, legacy entry points, CRUD/domain behavior, sample integration, and presentation tests in the consumer suite. Retain the established assertion mapping and add focused coverage for the new seams and import direction. Record observed behavior changes rather than weakening baseline assertions to make a refactor pass.

Implementation verification uses the existing Compose environment and repository runner:

```bash
./runproj exec "./runtests --suite coordinator --pytest"
./runproj exec "./runtests --suite powercrud --pytest"
```

The consumer selection includes separate minimal-settings and focused Bootstrap server runs. Focused paths remain repository-root-relative. Preserve the current separate raw coverage files and exact-union aggregation documented in the [stable testing guide](../../../mkdocs/reference/testing.md). Record runtime versions, commands, results, skips, and any limitations when execution occurs. B1 document preparation ran no tests, builds, service actions, or workflows; subsequent implementation verification is recorded in B2–B4.

Review the resulting import graph, compatibility paths, and suite isolation before marking B complete. Behavior-preservation tests do not certify Redis/Memcached/DatabaseCache concurrency, lease protection, cached-result completion, or real q2 workers. Keep those proofs in their assigned later phases and preserve the currently claimed support. Specific feasibility limitations must return for agreement rather than silently narrowing support.

The handoff should identify implemented seams, retained compatibility dependencies, any explicitly accepted behavior changes, exact verification evidence, and remaining Phase C work. New retry features, durable orchestration/replay, guaranteed notifications, and rolling in-flight upgrades remain excluded. Commit-safe submission, owner-safe locking/recovery, truthful outcomes, terminal retention, and drained compatibility upgrades remain required by A1.

#### B4 review and handoff — 2026-11-07

Reviewed B2/B3 at `0c476b61` against the B1 specification, pre-B2 implementation (`93a7d5c4^`), pre-B3 implementation (`20100b5a`), and A3 ownership ledger. The review found compatibility and evidence gaps and corrected them before Phase B signoff; repairs and regression checks are committed in `b74f2d22`. This record supplements the historical B2 and B3 results above.

| Review area | Finding and final disposition |
|---|---|
| Dependency direction and lazy imports | `_coordinator` imports standard library, Django infrastructure, and internal modules; configured manager classes are imported during reconstruction. It imports no PowerCRUD configuration/logging helpers, public async wrappers, CRUD modules, or sample code. The legacy hook path in the adapter is an intentional string default. The fresh-process test now actually removes `DJANGO_SETTINGS_MODULE`, asserts Django stays unconfigured, and checks that q2 runtime and public helper modules remain unloaded. |
| One submission sequence | Internal `launch` and public `launch_async_task` both use `_launch` and `Q2Adapter.submit`, submitting the original callable. The separate adapter health probe submits only its existing `math.floor` probe. Exact consumer transport assertions verify options, custom hooks, aliases, broker identity, and the absence of new coordinator kwargs on legacy calls. Registration failures preserve the existing reserve → progress → submit → register → create sequence. |
| Legacy identifiers and failed enqueue | B3 canonicalized valid trailing UUID strings and replaced explicit empty keys with generated ones. Restored the original UUID spelling and None-only fallback; empty keys again reach the existing progress-key rejection. B2 converted falsey IDs such as `False` and `0` into truthy strings; the adapter now preserves their failure meaning so the existing enqueue rollback runs. These are refactor regression repairs, not new validation policy. |
| Constructors and resolver behavior | Restored public resolution of sibling public managers when invoked through a subclass, subclass fallback on failure, no-path default construction, and omission of the `config` keyword when `_coerce_manager_config` returns None. Core construction now defaults to the selected class's preparation hook, including tracking mapping conversion. Explicit or bound executors use None-only selection. Distinct nested configurations/executors, failed constructors, fallback, normal `super()` calls, and binding reset are covered. |
| Completion and tracking | Snapshot core completion retains the supplied cache/namespace, adapter, and supported Python application config. Snapshot legacy completion passes the raw task once; an override without `super()` retains cleanup responsibility, and a super-calling override reaches core completion once. The public hook still suppresses application exceptions. Public tracking shares the configuration class and mixin, initializes its public manager base once, and preserves override/super behavior and falsey config fallback. ORM persistence assertions remain real ORM checks. |
| Context, progress, and worker factories | Public context storage and dataclass are the same objects as the core exports. Distinct real cache locations verify endpoint and descendant-factory selection. Suite manager helpers previously masked construction bindings with identical defaults, and the suite worker ignored supplied metadata; both now honor the supplied configuration/executor and worker metadata. Existing inline worker result/progress assertions execute the real suite worker through the patched enqueue seam. Consumer CRUD workers are also checked through their actual public resolver, with and without snapshots. |
| Retained algorithms and integration | AST comparison, excluding docstrings, found unchanged lock, registry, progress, cache-only status, artifact removal, and legacy force-cleanup methods from the pre-B2 implementation. Queue-dependent status and cleanup methods retain their former interpretation through adapter translation. Tracking methods retain their original behavior apart from construction/export hooks. PowerCRUD CRUD, sample, presentation, commands, and schedule integration remain consumer-owned; the bulk-payload fix at `20100b5a` is preserved. |

##### Assertion ownership addendum to A3/B3

The A3 ledger is preserved. The following node mapping records further ownership and interface changes; passing test counts alone are not the ownership proof. Paths below are repository-root-relative.

| Baseline assertion group | Current owner and preserved assertions |
|---|---|
| `src/coordinator_tests/test_lifecycle.py::TestAsyncHookHelpers::{test_task_completion_hook_uses_resolved_manager,test_task_completion_hook_handles_missing_manager,test_task_completion_hook_passes_manager_config}` | `src/tests/test_async_compatibility.py::TestAsyncCompatibility::test_public_hook_preserves_legacy_manager_resolution_arguments` covers all three cases: explicit path without config, absent metadata, and explicit path with dict config; each checks resolver arguments and one raw-task call. Parsing and dict-only legacy extraction assertions remain coordinator-owned. |
| `src/coordinator_tests/test_hooks.py::test_progress_update_decorator` | Consumer `TestAsyncCompatibility::test_progress_decorator_remains_a_public_compatibility_helper` retains the worker result and both ordered progress messages. It also pins the current ignored `task_key` alias for Phase C. |
| `src/coordinator_tests/test_lifecycle.py::TestTask3CompletionHooks::test_handle_task_completion_customizable` | Generic override/key assertions now use `test_core_completion_customizable` and `Completion`. Consumer snapshot/no-super and super-calling tests retain raw-task identity, override responsibility, and single dispatch. |
| Same class: `test_handle_task_completion_emits_events` and `test_handle_task_completion_failure_event` | Renamed `test_core_completion_emits_events` and `test_core_completion_failure_event`; retain success/cleanup and failure status/message assertions through `complete(Completion)`. Public raw-task translation is covered separately by consumer compatibility tests. |
| Existing generic launch, locks, registry, status, cleanup, progress endpoint, context, and tracking assertions | Retained in coordinator tests using internal production modules and explicit suite configuration. Legacy URL/hook/constructor/resolver/UUID/transport behavior is checked in consumer compatibility tests. Existing tracking ORM, sample CRUD/domain, persistence, and presentation assertions remain in their owning suites. |

##### Phase C handoff

The accepted changes are the specified internal APIs and separation, plus repairs restoring pre-refactor behavior. No additional intentional consumer behavior change is accepted by B4. The implementation remains inside the PowerCRUD distribution and continues using django-q2; standalone extraction and installed-artifact proof remain E/F work.

Prepare Phase C's detailed plan from A1 C1–C6, B1 D1–D7 and the seven identity wrinkles, and the shared issues 1–13. Start with explicit-use configuration/enablement, then manager identity/context and retained task/execution evidence, truthful outcomes and terminal retention, safe submission ordering, owner-safe locks/registry updates, and conservative reconciliation. Coordinate these changes with sample scenarios D1–D6 and their consumer tests. Keep code/test changes focused on each intentional contract correction.

The current missing-progress success, queue-success interpretation of ordinary `False` results, post-enqueue registration/create ordering and progress reset, legacy resolver fallback/metadata precedence, integer descendant normalization/base-manager behavior, missing-row cleanup, shared-set registry operations, and ownership-blind release remain baseline behavior for Phase C. Explicit internal snapshot transport does not solve automatic legacy identity capture, retained identity expiry, polling reconstruction, or context propagation.

Evidence remains bounded: synchronous q2 health probes, patched enqueue/fetch/hooks, inline worker execution, actual sequential cache effects and tracking ORM persistence. No separate worker delivery, distributed cache concurrency/leases, cached-result completion reliability, full allowed q2-version range, genuinely absent distributions, or installed-package behavior is certified. Keep supported-backend claims intact while obtaining those proofs in C/D/F; return concrete feasibility limits for agreement. No browser-test or remote CI result is claimed. B4 performed no package build, release, merge, or dependency upgrade.

##### B4 verification evidence

Initial new regression selections reproduced four coordinator/factory failures (9 passed) and four consumer compatibility failures (15 passed) against B3. After repair, the focused coordinator lifecycle/reconstruction/factory/adapter selection passed 67 tests in 3.43s. A follow-up consumer selection passed 36 tests and exposed an incorrect new expectation that an explicit empty key would succeed; the pre-refactor code rejects that key in `create_progress_key`, so the test was corrected to preserve that boundary before final verification.

Final full suites used the existing development Compose container via the repository runner, with Python 3.14.6, Django 6.1.2, and pytest 8.4.2:

```text
./runproj exec "./runtests --suite coordinator --pytest"
141 passed in 24.63s; no reported skips or warnings.
Coordinator coverage: 958 statements, 138 missed, 86%.

./runproj exec "./runtests --suite powercrud --pytest"
1,081 passed, 23 skipped, 110 deselected, 8 warnings in 30.24s.
Separate tests.settings_minimal selection: 4 passed in 5.62s.
Separate tests.settings_bootstrap selection: 31 passed in 7.86s.
Final appended consumer coverage: 9,126 statements, 1,245 missed, 86%.
```

The full consumer invocation completed successfully twice. The retained totals/timings above come from the second run, whose stdout was captured with `tee /tmp/powercrud-b4-verification.log` and filtered for summaries because the first run's long coverage output was truncated by the tool. The eight warnings are the existing modal class and `get_list_cell_link` deprecations. The project lock remains the q2 1.11.1 source/version reference; these test headers do not independently establish the installed q2 version or compatibility across the allowed range.

The established raw coverage paths remain `.coverage` and `.test-artifacts/coverage/coordinator/.coverage`; coordinator measurement remains restricted to `_coordinator`. The existing real-tool artifact test passed, verifying isolation and exact-union aggregation in temporary files. `.test-artifacts/coverage/combined/.coverage` remains the aggregate destination; these separate suite runs do not refresh that aggregate, and no new aggregate percentage is claimed. All 105 local planning links/anchors and `git diff --check` passed; those are documentation/static checks, not additional runtime evidence.

**B4 and Phase B are complete.** The master roadmap, overall plan, shared notes/register observations, and phase checklist now reflect that closure. Issues 1–13 remain open; Phase C is next.
