# Phase A notes: Ownership, contracts, and early test separation

Seeded on 2026-11-04 from the [overall plan](../0_async_hardening-plan.md) and [shared notes](../0_async_hardening-notes.md). Updated with A1 contracts after reviewing the [source audit](phase_A_audit.md#a1-review-addendum--2026-11-04). **Phase A is complete on 2026-11-04**, including test separation, server verification, and both review follow-ups. The [shared completion/handoff](../0_async_hardening-notes.md#phase-a-completion-and-handoff) carries its requirements into later phases.

The [shared hardening register](../0_async_hardening-notes.md#key-async-hardening-issues) is the single numbered completion checklist. Link evidence here back to its issue numbers instead of maintaining another copy. The full [test ownership review](../0_async_hardening-notes.md#test-ownership-review) remains the inventory source; record actual relocation details here as work proceeds.

## Scope and handover

Phase A defines contracts, qualifies findings, and separates tests before Phase B establishes production boundaries. django-q2 remains the sole execution engine. Package extraction follows in Phase E; Django Tasks and alternative backends remain deferred. Preserve behavior during the structural test split, then fix confirmed behavior intentionally in the later implementation phases.

Independent test fixtures/settings are required now. Complete independence from the existing production `powercrud` module paths and their import dependencies may require Phase B; document those dependencies rather than duplicating production code or hiding them with broad mocks.

## Plan Phases

### A1: Define ownership and contracts

The agreed ownership is:

| Owner | Responsibilities |
|---|---|
| Coordinator | Locks, state, progress, lifecycle, context, manager reconstruction, optional model tracking, reusable endpoints, and cleanup |
| q2 adapter | Dependency loading, queue configuration, enqueue/result handling, completion translation, health checks, and scheduling integration |
| PowerCRUD | Bulk decisions and persistence, CRUD workers, settings translation, conflict/locked-row presentation, progress modal, and dashboard CRUD views |

#### A1 draft contracts for discussion

**Status: Q1–Q10 RESOLVED on 2026-11-04; A1 contract decisions complete.** Clauses C1–C6 incorporate the agreed answers below, including the simplified scope discussed for Q6–Q10. The original draft-section heading is retained for existing links. These are agreed behavioral requirements, not implemented or verified guarantees. Backend algorithms and other implementation details remain for investigation in A2 and design in B/C; any unavoidable support/guarantee limitation must return for agreement.

Evidence is linked to the [audit qualification](phase_A_audit.md#finding-qualification) and [q2 review](phase_A_audit.md#dependency-evidence). The review verified locked and installed django-q2 **1.11.1** and ran four existing focused tests; it did not establish full worker, retry, or concurrency behavior. Acceptance scenarios below describe future tests, not tests already passing. Suite owners are the future coordinator tree and PowerCRUD consumer/sample tests.

No final cache algorithm, new package/class name, repository, or general backend plugin system is selected here.

##### C1 — Ownership and public integration (agreed; issue 13)

**Current/evidence:** The [launch and dependency trace](phase_A_audit.md#current-behavior-and-dependency-flow) mixes q2 options, PowerCRUD settings, coordination, and URLs. Launch returns a PowerCRUD task-name string; the q2 ID is separate. The view passes manager identity manually; arbitrary launch sites need the same metadata for completion and context.

**Agreed contract:** PowerCRUD converts its settings and bulk/domain result into the coordinator contract. Other Django callers can launch without CRUD imports. The coordinator accepts an importable callable, worker args/kwargs, optional conflict resources, initiating metadata, and explicit coordinator configuration. Generate a logical task key or accept an explicit one; retain the current string return through compatibility wrappers. Retain q2 execution ID, effective adapter options, and manager class/config separately from that logical key. Metadata/config must be worker-reconstructible; arbitrary Python closures/request objects are not the distributed configuration contract.

Expose observable categories for configuration/disabled use, conflict, definitely rejected submission, and uncertain submission, carrying the task key where allocated. Adapter types and raw q2 Task objects remain behind the adapter except in legacy hooks. Status/progress provide one coherent observation: logical key, state, progress/message, result/error where known, and an observation time/reason. Terminal results must be distinguishable from transient progress. Optional model tracking and HTTP endpoints consume that observation; they must not define separate outcomes. Endpoint mounting and authorization remain application responsibilities and must not depend on PowerCRUD's URL namespace.

**Rationale/compatibility:** Preserves the useful public launch key while removing queue and presentation coupling. Error categories and coherent observations define required behavior; final symbols/wire encoding belong to implementation design. Existing import, hook, and URL consumers need adapters under C6/Q9.

**Acceptance S1:** Coordinator launch/status/context/tracking through minimal Django settings without CRUD/sample imports; same logical key and manager configuration observed at launch, worker, completion, and polling. Configuration and conflict errors are observable before enqueue. Existing PowerCRUD wrappers retain documented entry points. **Owner:** coordinator API/integration suite and PowerCRUD compatibility suite.

##### C2 — Configuration, activation, and fallback (agreed; issues 1–4)

**Current/evidence:** [Audit issues 1–4](phase_A_audit.md#finding-qualification) show a lazy ordinary `PowerCRUDMixin` export but eager q2 imports when async modules are requested. Configuration helper already handles unconfigured settings/defaults and rejects non-dict `POWERCRUD_SETTINGS`. The view flag and global cleanup flag are inconsistent.

**Agreed contract:** Dormant coordinator and PowerCRUD imports do not load q2 models or require configured settings. Validate when an explicit launch/async operation is used: settings shape, app registration, manager/config reconstruction, supported shared-state backend, effective queue/result options, and resource key validity. Produce targeted errors rather than startup health probes, broad catches, or silent fallback to another manager. Connectivity checks establish reachability only; they cannot certify atomicity or a running worker from a synchronous probe.

**Agreed under Q1:** Use one explicit launch-enable flag in coordinator config; PowerCRUD maps `ASYNC_ENABLED` into it. Core views and below-threshold operations stay synchronous. An async-opted view reaching its threshold while disabled or misconfigured reports an actionable error; it does not silently perform potentially expensive work in the request. Direct manager launches also require explicit enablement and report disabled use. Disabling new launches leaves progress, completion, reconciliation, and owner-safe cleanup operational for existing work. Normal dormant use is quiet; genuine explicit-use errors are logged with context. A stopped worker is distinct from invalid setup: accepted work can remain queued awaiting a worker, and must not be reported as executing.

**Rationale/compatibility:** Makes opt-in and operational behavior predictable. This intentionally changes current silent view fallback and direct-launch behavior where callers omit the global flag; document migration under Q1/Q9.

**Acceptance S2:** Import-before-settings and genuinely absent q2 distribution in isolated processes; q2 distribution/app mismatches; missing/wrong settings; invalid cache/queue/config; core sync path and below-threshold path; threshold launch when disabled/misconfigured; active cleanup after disabling launches; probe without live-worker inference. **Owner:** coordinator configuration suite; PowerCRUD sync/threshold/settings translation tests.

##### C3 — Outcomes, progress, and lifecycle (agreed; issues 6–8)

**Current/evidence:** [Audit issues 6–8](phase_A_audit.md#finding-qualification) and [focused verification](phase_A_audit.md#focused-verification) confirm current missing-progress success fallback and terminal events based on execution flags. q2 treats a normal `False` return as successful execution. Tracking can overwrite terminal state with late progress/create events, and unknown completion is emitted as `complete`, which model tracking translates to success.

**Agreed contract:** Keep recognizable states `pending`, `in_progress`, `success`, `failed`, and `unknown`; encode missing/expired/unavailable evidence as reasons for `unknown`, never as success. Pending must not claim queued submission before enqueue has happened; claim running only from actual execution evidence. Record execution outcome separately from business outcome. Ordinary arbitrary worker values, including `False`/`None` or dictionaries with a `success` key, remain successful return values unless the worker opts into a documented outcome contract. PowerCRUD explicitly translates bulk failure/partial failure into that contract, retaining processed counts and useful errors. Business failure is reported without automatically repeating the operation.

Establish task identity and initial state before workers can publish progress/completion; no later registration/create may regress running or terminal state. Terminal outcomes for an accepted execution are monotonic; repeated notifications are idempotent and stale execution events cannot rewrite a newer outcome. Preserve a small final result for polling after active-lock cleanup, with a configurable **24-hour terminal snapshot TTL from completion**, separate from live progress TTL; optional tracking history has separate application retention. Unknown observations must not cause endless polling or be relabeled success merely to stop polling. A durable job-recovery system is outside scope.

Core state transition/lock failures are observable. Optional lifecycle callbacks remain best effort: log reporting failures and keep the actual job outcome separate from callback delivery. Repair dashboard state where retained results make it possible. Persisted notification queues, guaranteed delivery, and automatic notification retries are outside scope.

**Rationale/compatibility:** Preserves arbitrary worker return semantics while fixing PowerCRUD business failures. Polling consumers must handle explicit failure/unknown and terminal retention. Final wire format remains implementation design.

**Acceptance S3:** Plain `False` return versus explicit failed outcome; bulk partial failure; exception; unknown completion; no progress, expired progress, cache error; fast and explicit sync completion; late create/progress; duplicate callback; retained failure after locks release; snapshot expiry; failing optional callback. **Owner:** coordinator outcome/lifecycle/endpoint/tracking suite; PowerCRUD bulk-worker, progress, and both template-pack consumer tests.

##### C4 — Cache capabilities and lock lifetime (agreed; issues 9–10)

**Current/evidence:** [Audit registry/lock findings](phase_A_audit.md#finding-qualification) show shared read/modify/write sets, unconditional deletes, and lease TTL without renewal. Existing named concurrency cases are sequential. File-backed test caches do not certify production coordination guarantees.

**Agreed under Q2:** Harden the coordination backends we currently claim to support, including Redis, Memcached, and DatabaseCache. Inventory the documented claims, implement safe shared-state operations for each supported backend, and verify them with meaningful concurrency tests. Required behavior includes cross-process visibility, conditional ownership-safe acquisition/release, safe registry/index changes, and expiration semantics; a class-name/shared-cache check or set/get probe is insufficient. Testing one backend first is an implementation sequence, not a reduction in support. If a claimed guarantee cannot be provided, bring back the specific limitation and proposed change for agreement. Keep file caches for limited baseline tests, never production-guarantee evidence. No locking algorithm or generic plugin system is selected here.

Resource identity includes normalized model label and original primary-key type; preserve non-integer keys in the reusable API. Reserve requested resources before delivery, undo only this launch's owned reservations on definite rejection, and never delete a replacement owner's lock. Repeated descendant registration by the same task is safe, preserves the full ownership index, uses its configured manager, and surfaces acquisition failure before protected child work proceeds. Registry/index changes cannot lose unrelated tasks.

**Agreed under Q4:** Records must stay protected while supported jobs are working, crashed jobs must be recoverable, and an old job must never remove protection belonging to another job. Investigate renewal of the temporary busy markers while a job runs, together with owner-safe cleanup and a defined response if renewal fails. A busy marker alone cannot stop an old worker from continuing to write after losing contact. Establish how to deliver the agreed behavior across supported backends, including stale queued work, expiration/reacquisition, and worker failure; return any unavoidable guarantee limits for review. Renewal, cancellation, timing limits, and application-enforced write protection remain implementation investigations, not selected algorithms. Account for q2 receipt expiry and queue waiting time when defining supported task timing.

**Rationale/compatibility:** Preserve claimed support and replace unsafe behavior with verified guarantees. The earlier Redis-only/bounded-work proposal is superseded by Q2/Q4. Backend-specific implementation and task-timing design must satisfy the agreed behavior rather than silently narrowing existing deployments.

**Acceptance S4:** Synchronized multi-process registry add/remove and competing reservations across claimed supported backends; partial acquisition/cache failure; expiry/reacquisition during release/rollback; repeated/overlapping descendant IDs; custom-manager propagation; non-integer PK; stale queued worker; continued protection during a long supported job; renewal failure and crash recovery. Tests must demonstrate the actual protection and recovery guarantees. **Owner:** coordinator cache/lock/context integration suite; PowerCRUD verifies conflict presentation.

##### C5 — Reconciliation and recovery (agreed; issues 3, 6, 11)

**Current/evidence:** [q2 dependency evidence](phase_A_audit.md#dependency-evidence) establishes that Task rows are results, not a live-work registry; missing/pruned/skipped rows are normal. Existing `success=None` running rows are test doubles, not persisted q2 state. Legacy cleanup clears all registered work; scheduled/command cleanup is gated by launch enablement.

**Agreed contract:** Reconciliation uses coordinator submission/start/lease metadata plus known adapter evidence. Retained explicit results can reconcile outcomes. Missing result/progress alone never proves abandonment; lookup failures are reported as unavailable and skipped conservatively. Age limits identify work requiring recovery and may close only expired, safely invalidated reservations under C4; they do not prove business rollback or worker termination. Administrative force cleanup requires an explicit request/reason and reports unresolved execution; document worker shutdown/side-effect responsibilities. It must not be a quiet alias for normal reconciliation.

Release only owned coordination artifacts and preserve terminal snapshots/history. Report inspected, reconciled, skipped, uncertain, and failed cleanup outcomes truthfully; repeating cleanup is safe. Clean proven terminal work and safely invalidated stale reservations, while uncertain work remains visible for operator review. Cache eviction/restart can lose coordination evidence; optional model history aids diagnosis. Durable state surviving every cache loss, automatic interrupted-job restart, and safe replay are outside scope; the existing crash/lock-cleanup promises under Q4 still require hardening.

**Rationale/compatibility:** Prevents cleanup from unlocking queued/running work on absent q2 results. Existing force-like methods/commands need explicit compatibility behavior and operator migration guidance.

**Acceptance S5:** Queue accepted without result row, running evidence, saved success/failure, result pruning, read failure, expired reservation, recent/uncertain task, force cleanup with late worker/callback, repeated cleanup, disabled launch flag, and terminal retention. **Owner:** coordinator reconciliation/cleanup suite; PowerCRUD command/schedule wrappers and sample dashboard consumers.

##### C6 — q2 execution, reconstruction, and compatibility (agreed; issues 2, 7–8, 12–13)

**Current/evidence:** Installed q2 1.11.1 [source review](phase_A_audit.md#dependency-evidence) distinguishes `OrmQ` broker rows from saved `Task` results, confirms per-call option precedence, missing cached-result model hooks, and duplicate delivery behavior. Direct launch does not capture its own class/config automatically. Context has manager path but descendant helpers construct the base class; progress decorator looks for `task_name` although manager injects `task_key`.

**Agreed under Q3:** Harden every q2 configuration we currently purport to support. Inventory the actual PowerCRUD documentation/API claims, then test and repair those integration paths, including cached results wherever supported. Keep broker transport and result storage separate in the support matrix. Working on ORM results first is an implementation sequence, not permission to drop cached results or another claimed broker mode. Repair completion delivery where result storage bypasses model-save hooks; do not treat rejecting an existing supported option as the hardening solution without agreement. This does not expand scope to every feature q2 offers. Persist effective q2 ID/result locator and manager reconstruction metadata; do not rely on task-name lookup working for every storage mode. Sync execution is an explicit test/development option and must preserve coordinator ordering/outcome semantics even when q2 raises after work begins.

**Agreed under Q6:** Do not automatically repeat failed PowerCRUD work. Report business failure and acknowledge escaped execution failures by default for PowerCRUD's potentially non-idempotent operations. New retry features, attempt-history management, and a coordinator retry framework are outside scope. Preserve existing application/q2 configuration entry points; applications remain responsible for any deliberately configured retries. Broker redelivery can still duplicate work, so hardening must make repeated/late completion and owner-safe cleanup robust. Do not promise exactly-once business effects or design a retry system as a prerequisite for correctness.

**Agreed under Q8:** Start a background job only after the database successfully saves the information it needs. Inspect actual launch sites and use Django's existing `transaction.on_commit` where needed; a rolled-back save must not submit work. Launch immediately when the relevant inputs are already committed. Handle submission failures honestly; do not say queued before submission, blindly repeat an uncertain submission, or release another execution's owned protection. A new public submission helper, extra status model, and transactional outbox are not required by this decision. Add abstractions only if actual callers need them. Verify saved-data visibility, rollback, and response/error handling at the affected launch sites.

Reconstruct the original importable manager class/config automatically for direct launches, workers, hooks, descendants, and progress helpers. Invalid explicit configuration fails visibly; absent config can choose the documented base default. Normalize the legacy `task_name` alias at compatibility entry points. Prefer keyword `task_key`; retain trailing-UUID parsing only in a deprecated legacy wrapper with warning, while the new coordinator passes arbitrary worker args unchanged. **Agreed under Q9:** Preserve old imports, hook paths, settings translation, and URLs through the first extracted-package release and at least one subsequent PowerCRUD minor release; remove only in an announced breaking release. Stop accepting new jobs, let existing jobs finish, upgrade, restart workers, then resume launches for extraction/path or cache-namespace migration. Rolling upgrades/in-flight migration are outside scope.

**Rationale/compatibility:** Preserve claimed q2 support while repairing lifecycle gaps. The earlier ORM-only support recommendation and blanket rejection of cached results are superseded by Q3. Document the agreed failure-acknowledgement, strict-config, transaction-feedback, and UUID compatibility changes. Verify the supported q2 version range; the broad dependency requirement alone does not establish equal adapter behavior across versions.

**Acceptance S6:** Real q2 launch/worker/completion with ID and custom manager config across the inventoried supported modes; cached and ORM result paths; success under supported save/pruning options; custom-hook interaction; explicit sync success/exception; failure acknowledgement and duplicate/redelivered/late completion safety without new retry features; after-save visibility and rollback; ambiguous enqueue failure; old import/hook and UUID wrapper plus literal UUID argument on the new API; drained upgrade. **Owner:** coordinator q2/reconstruction/integration suite; PowerCRUD transaction, worker and compatibility consumers.

#### Questions to settle together

Q1–Q10 are **RESOLVED** as recorded below on 2026-11-04. Question numbers and answers are retained for the clause/scenario references. Resolution records agreed direction, not an implemented fix or verified guarantee. There are no remaining A1 decision questions; technical investigation continues in A2.

1. **Q1 — When should an async-opted view fall back to synchronous work? — RESOLVED.** **Answer:** Ordinary/core views and operations below the threshold run synchronously. An operation expected to run in the background must return a clear error for disabled or invalid async setup, rather than unexpectedly running inside the web request. Direct launches require explicit enablement too. `ASYNC_ENABLED=False` prevents new background launches while existing tasks can finish and clean up. This avoids unexpectedly slow requests/timeouts. A stopped worker can leave valid work queued; it does not justify synchronous fallback. **Agreed:** 2026-11-04. **Applies:** C2, S2; issues 2–3.

2. **Q2 — Which coordination stores must the first release support? — RESOLVED.** **Answer:** Preserve and harden the cache backends we currently claim to support, including Redis, Memcached, and DatabaseCache. Inventory those claims, implement safe operations, and verify each supported backend. Redis-only support is not the agreed outcome; investigating/testing Redis first can be an implementation step. If a guarantee proves impossible on a claimed backend, present that specific limitation for agreement. **Agreed:** 2026-11-04. **Applies:** C4–C5, S4–S5; issues 9–11.

3. **Q3 — How broad must initial q2 mode support be? — RESOLVED.** **Answer:** Hardening must repair everything PowerCRUD currently purports to support. Inventory documentation/API claims, verify the relevant broker and result-storage combinations, and fix lifecycle gaps. Cached-result support must be repaired wherever claimed; ORM-first implementation must not become a permanent support reduction. This preserves the existing support commitment rather than adding every q2 feature. Any unavoidable reduction requires a specific explanation and agreement. **Agreed:** 2026-11-04. **Applies:** C1–C2/C6, S1–S2/S6; issues 2, 6, 8, 11, 13.

4. **Q4 — What protection is required for work that outlives its lease? — RESOLVED.** **Answer:** Keep a record marked busy while its supported job is working, recover safely when a job crashes, and prevent an old job from clearing another job's protection. Investigate renewing the temporary busy markers during execution, with owner-safe cleanup and a defined response when renewal fails. A marker alone cannot stop a worker that continues writing after losing contact. Agree the required behavior now; investigate the algorithm across supported backends and return any unavoidable limits for review. Renewal/fencing/cancellation algorithms and exact timing rules are not selected by this decision. **Agreed:** 2026-11-04. **Applies:** C4–C5, S4–S5; issues 9–11.

5. **Q5 — How should business failure be declared? — RESOLVED.** **Answer:** Fix bulk jobs that report execution success when the requested changes failed. Built-in bulk workers explicitly report business success/failure, counts, and errors; dashboard/progress use that outcome. Custom worker return values retain ordinary behavior unless the worker explicitly reports an operation failure. **Agreed:** 2026-11-04. **Applies:** C3/C6, S3/S6; issues 6–7.

6. **Q6 — What retry promise should the coordinator make? — RESOLVED.** **Answer:** Report failures clearly without automatically repeating PowerCRUD operations; acknowledge escaped execution failures by default for PowerCRUD. **Retry features are outside this work.** Existing deliberate application/q2 retry settings remain application-owned. Still harden duplicate/late completion and lock cleanup because brokers can redeliver work; promise no exactly-once business effects. **Agreed:** 2026-11-04. **Applies:** C3–C6, S3–S6; issues 7–12.

7. **Q7 — How much retention and automated recovery do users need? — RESOLVED.** **Answer:** Retain a small final result for a configurable period, with a 24-hour default, separately from live progress and optional database history. Do not infer success or stopped execution from missing data. Keep cleanup conservative and uncertain work visible for review. Durable orchestration surviving every cache loss, automatic interrupted-job restart, and replay are outside scope; preserve existing crash-cleanup requirements. **Agreed:** 2026-11-04. **Applies:** C3/C5, S3/S5; issues 6, 10–11.

8. **Q8 — Who owns transactional submission? — RESOLVED.** **Answer:** Start background work only after the database has successfully saved its inputs. Inspect the actual callers and use Django's existing after-save/commit callback where needed. A failed/rolled-back save submits no job, and feedback must not claim submission before it happens. The rule is required; a new helper, extra submission states, or durable outbox is not required unless actual use demonstrates a need. **Agreed:** 2026-11-04. **Applies:** C1/C6, S1/S6; issues 8, 10–13.

9. **Q9 — What migration commitment should we make? — RESOLVED.** **Answer:** Keep old import/hook/settings/URL entry points working through compatibility wrappers through the first extracted-package release and at least one subsequent PowerCRUD minor release; remove only in an announced breaking release. For extraction/path/namespace upgrades, stop new launches, let existing jobs finish, upgrade, restart workers, and resume launches. Rolling upgrades with jobs still in flight are outside scope. **Agreed:** 2026-11-04. **Applies:** C1–C2/C5–C6, S1–S2/S5–S6; issues 5, 12–13.

10. **Q10 — Are lifecycle notifications advisory or durable obligations? — RESOLVED.** **Answer:** Keep the actual job outcome separate from optional reporting. Preserve best-effort callbacks, log reporting failures clearly, and repair dashboard state where a retained result makes it possible. Guaranteed email/webhook/audit delivery, persisted notification queues, and notification retries are outside scope. A failed dashboard update does not turn successful business work into a failed job. **Agreed:** 2026-11-04. **Applies:** C1/C3/C6, S1/S3/S6; issues 6–8, 12–13.

#### A1 completion and implementation handoff

The agreed contracts cover A1.1 through C1/C6, A1.2 through C2–C6, and A1.3 through C4/C6 plus the q2 evidence. Each clause has an owning suite and acceptance scenarios. Four focused existing tests passed as recorded in the audit; they do not verify the agreed future behavior.

A1 is complete at the contract/decision level, A2 qualification and mapping are complete, A3 has separated the test suites, and A4 plus its follow-ups complete server-suite verification and review. Backend/locking feasibility and transactional launch sites remain later implementation work; do not treat the agreed outcomes as implemented guarantees. Nothing here marks a shared hardening issue fixed.

### A2: Qualify findings and assign coverage

**Status: complete.** The detailed issue qualifications, supported-configuration inventory, test destinations, and A2 focused-run results are in the [separate A2 results file](phase_A_a2_results.md). This report distinguishes source evidence from runtime proof and does not mark any hardening-register item complete.

The shared review began as read-only evidence, not runtime verification. A2 now records whether inspection/reproduction confirms each issue, the expected outcome, existing and proposed coverage, and its owning suite. It identifies where stronger tests suffice and where behavior conflicts with agreed contracts; it does not assume every issue requires a rewrite.

Important starting evidence from the shared review:

- `test_sys_functions.py` mixes generic lifecycle/locks/progress, q2 hooks, tracking, CRUD conflicts, and view configuration, with module-level sample/CRUD imports.
- `TestConcurrentAccess.test_concurrent_atomic_reservation` and the cache-add check execute sequentially; they do not prove cross-process atomicity.
- The named end-to-end launch test patches enqueueing to execute inline even though its base starts a cluster; distinguish that from actual worker/completion integration.
- Root pytest configuration selects `tests.settings` and PowerCRUD coverage; those settings include the sample stack and file-based caches. q2 sync is configured as a default but manager launches explicitly override it with `sync=False`; see the audit addendum.
- Minimal settings omit q2 from installed apps but do not establish that q2 is uninstalled; genuine early-import/missing-dependency checks need process/environment isolation.


#### A2 review and discussion — 2026-11-04

**Assessment:** A2 provides enough evidence to begin a bounded A3 test split. Its 80 passing existing tests are a useful baseline, but they exercise current behavior and do not establish the new contracts. A2 can remain complete after the corrections in the [review addendum](phase_A_a2_results.md#review-corrections-and-concrete-dependencies--2026-11-04). A3/A4 and every production hardening item remain open. This review inspected source, test bodies, runner and CI; it did not rerun tests.

Corrections made to the report:

- The named end-to-end test asserts an inline worker's captured progress, UUID and active membership. It never asserts completion or cleanup. The status-method class tests mocked q2 fetch, not cache-only status.
- The two built-in launch calls submit existing row IDs and field values. No save-then-enqueue visibility failure was demonstrated. Q8 still governs callers that submit work within a transaction; worker-side transaction blocks do not establish caller-side commit safety.
- q2 1.11.1 installed-source evidence comes from the prior A1 review. A2 reused it; this review did not refresh installed source or verify the entire allowed q2 version range.
- Checked-in project settings select the ORM broker and use Redis for coordination. The guide's Redis-broker claim needs correcting in the documentation phase; it does not block A3 or require reopening Q3. Claimed Redis broker support remains in the verification inventory.
- References in the relocation map to changing assertions, replacing sequential tests with concurrency tests, or adding stricter workers are later hardening work. **A3 must preserve the current expectations**, including known incorrect behavior, until production fixes land. Moving a test may change its fixtures/imports and helper paths without changing what it asserts.

**Recommended next increment:** implement A3 in two reviewable commits: first suite-owned settings/models/URLs/cache fixtures, a small existing state/lock test group, and explicit runner/CI selection so both suites actually run; then relocate the remaining reusable tests and record every old-to-new node ID. Keep the sample/domain/presentation tests and legacy wrappers in PowerCRUD. Keep current production imports and patch targets until Phase B creates the internal boundary. A4 runs both suites independently and checks that no distinct assertion or test group disappeared. The 80-test baseline excludes cluster-starting health tests, so that group needs its own recorded baseline before claiming relocation parity.

**Discussion points — recommendations only:**

1. **Keep A3 limited to test separation?** Recommend the two commits above, with production fixes and new concurrency/result-mode regressions in their later phases. Combining them would make it harder to tell a relocation mistake from an intentional behavior change. This follows the original Phase A boundary; no A1 contract changes are proposed.
2. **When should we prepare all backend verification environments?** Recommend doing the concrete feasibility and environment work as an early B/C preparation task after the test split. The checked-in [Compose file](../../../../docker/docker-compose.yml) defines Redis and PostgreSQL, but no Memcached service; client/service/CI preparation for Memcached still needs scoped work. Preserve Redis, Memcached and DatabaseCache support as agreed, and bring back specific guarantee limitations with evidence before choosing an implementation. This is an infrastructure/timing choice, not permission to drop a backend.

No further product decision is required to start A3. Do not add retries, a durable orchestration system, or guaranteed notifications to resolve these review points. Cache ownership/renewal, cached-result completion and duplicate/late events remain material production work after the test boundary is established.

#### Sample demonstration audit

The [overall coverage matrix](../0_async_hardening-notes.md#sample-demonstration-coverage-matrix) is the single record for scenario status and ownership. This audit is complete as source/test/doc inspection. At the time of the audit no runtime or browser tests had run; A3 later ran the retained sample async module and shared matrix in ordinary and Bootstrap settings. Follow-up implementation acceptance remains open.

Recommended scenario selection:

- Keep the existing Books bulk path as the main PowerCRUD demonstration: 2+ records queue, the dashboard links to progress, and the shared sample service makes the synchronous validation response and queued failure observable.
- Retain one lock-sensitive edit/conflict story, using the existing delayed delete or another suitable long-running operation; confirm real lock acquisition/release and visible behavior before describing it as end-to-end.
- Keep the parent task / descendant registration example as a concise advanced scenario. Automated package tests prove context and lock semantics; add a visual descendant-lock story only if it communicates value beyond the dashboard and conflict scenario.
- Keep model tracking and the task dashboard as the PowerCRUD integration demo. Generic lifecycle tracking belongs in the package suite; template rendering and PowerCRUD navigation remain consumer checks.
- Add no separate screen for every configuration. Use dedicated settings/process tests for absent package/q2, malformed or missing settings, app registration, caches, and early imports.
- With extraction, add one small standalone non-CRUD maintenance task demonstrating package installation, launch, progress/lifecycle, and cleanup with q2.

The settings reviewed define these distinct test purposes:

| Configuration | Observed shape | Use in evidence |
|---|---|---|
| `config.settings` / `tests.settings` | Both install/enable q2. Development uses Redis coordination and an ORM broker; test settings use file caches and a sync default, overridden by manager launches passing `sync=False`. | Default sample/manual configuration versus unit/integration test environment. The health probe can run inline, and enqueue is mocked in the named end-to-end test; neither proves a separate worker lifecycle. |
| `config.settings_bootstrap` / `tests.settings_bootstrap` | Inherits the default async settings and adds Bootstrap presentation apps/config. | Presentation parity for async form, progress fragment, dashboard, and terminal feedback; not a distinct q2 configuration. |
| `tests.settings_minimal` | Omits q2 from `INSTALLED_APPS`, omits `POWERCRUD_SETTINGS`, and omits async caches; still installs PowerCRUD and sample. | Proves selected synchronous PowerCRUD behavior under reduced settings. Does not prove q2 distribution absence or standalone package independence. |
| Future isolated package configurations | Not yet created. | Package installed without PowerCRUD/sample; settings-not-configured and genuinely absent dependency scenarios; independent core/q2 integration and worker execution. |

Gap assessment: the existing sample already demonstrates threshold-based bulk work, progress, tracking, sync/queued validation differences, and parent-task context at code/unit-test level. The key user-visible gap is a repeatable real queued job observed through progress to a truthful terminal dashboard state; lock conflict/release and cleanup recovery also need real lifecycle evidence once their contracts are hardened. The existing named end-to-end test is mocked inline execution; preserve it as unit/in-process evidence and add separate worker integration only when deterministic setup is available.


### A3: Separate tests before Phase B

**Status: complete.** The independent suite, 63-case relocation, runner/discovery/coverage configuration, and CI selection are recorded in the [A3 results](phase_A_a3_results.md). The results retain the current test expectations and list the PowerCRUD/q2 dependencies that Phase B must remove. A4 server verification is recorded separately; browser verification remains part of the existing browser workflow.

Initial relocation groups from the shared inventory:

| Coverage | Destination |
|---|---|
| Generic manager/locks/progress/status, context helpers, q2 hooks, model tracking, reusable polling, worker helpers | `src/coordinator_tests/` with owned models/settings/URLs and isolated cache resources; done in A3 |
| `TestSingleRecordConflicts`, `AsyncMixinManagerResolutionTests`, `test_async_mixin_extended.py`, CRUD workers/persistence, inline lock display, sample and presentation behavior | PowerCRUD consumer suite |
| Mixed scheduler/cleanup command tests | Generic behavior follows coordinator tooling; legacy PowerCRUD wrapper/configuration translation stays here |

The [A3 relocation ledger](phase_A_a3_results.md#relocation-ledger) records every moved and compatibility node, helper change, and retained assertion. Generic tests now use suite-owned model and manager helpers. Sample formatting, model-save demonstrations, dashboard rendering, domain services, permissions, and form behavior remain in the consumer suite.

Suite-owned fixtures, settings, URLs, minimal models, cache resources, and worker functions are in place. `runtests`, pytest configuration, coverage files, and CI select the suites independently, including minimal-settings invocations. Subsequent regressions belong in their eventual owning suite; extraction moves the coordinator suite rather than copying it.

### A4: Verify the split and hand over

**Complete, including final review.** The [A4 results](phase_A_a4_results.md) record both collections and full server-suite runs, the 63-case relocation accounting, coverage-file isolation and aggregation, documentation updates, and remaining limits. Coordinator coverage remains mocked, sequential, or in-process; no real worker or concurrency guarantee is claimed. Browser tests and CI were not run in this increment.

The initial A4 report was followed by the two reviews below. Phase A is now closed; hardening-register issues 1–13 remain open, and Phase B planning is next.

The subsequent [review excluding coverage coordination](phase_A_noncoverage_review.md) concluded **satisfactory excluding coverage** after fixing directory/settings isolation and multiple minimal-node selection. It records 110 coordinator passes (63 relocated, 46 runner cases, one isolation check), focused consumer/minimal/Bootstrap verification, assertion parity against the pre-A3 source, and the A1–A4 requirement assessment. No remaining non-coverage blocker was found; coverage work was reserved for the follow-up below.

The [coverage follow-up](phase_A_coverage_results.md) replaces conflicting filenames with separate directories and removes the file-moving workaround. It records 114 coordinator passes, the full consumer/minimal/Bootstrap cycle, preservation across consumer execution, the exact file/line union, and unchanged raw inputs after combination. **Coverage coordination is resolved and the Phase A handoff is complete.** The [shared completion record](../0_async_hardening-notes.md#phase-a-completion-and-handoff) identifies the authoritative evidence and remaining requirements for later phases.

## Working evidence and decisions

A1 decisions Q1–Q10 are resolved above. The audit addendum records installed dependency inspection and its initial focused tests. [A2 results](phase_A_a2_results.md) completes finding qualification, support inventory, ownership mapping, and focused existing-test batches. [A3 results](phase_A_a3_results.md) records the independent suite, relocation, runner/CI changes, and focused checks. [A4 results](phase_A_a4_results.md) and the two follow-ups above complete verification and review. Phase A is complete; production implementation has not started. Retain the detailed reports as historical evidence and use the shared handoff when planning Phase B.
