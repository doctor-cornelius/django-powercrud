# Phase C notes: Configuration and lifecycle hardening

Initial discussion draft prepared on 2026-11-07. The [phase plan](phase_C_plan.md) proposes reviewable increments. Sequence and C1 error-handling direction are now agreed below; remaining technical decisions are still under discussion. Implementation remains on hold.

## Scope and sources of truth

Use the [overall Phase C checklist](../0_async_hardening-plan.md#phase-c-harden-configuration-and-lifecycle), [A1 contracts C1–C6 and resolved Q1–Q10](../phase_A/phase_A_notes.md#a1-draft-contracts-for-discussion), [B1 D1–D7](../phase_B/phase_B_notes.md#agreed-b1-decisions--2026-11-07), [B1 technical specification](../phase_B/phase_B_notes.md#b1-technical-specification--2026-11-07), and [B4 handoff](../phase_B/phase_B_notes.md#phase-c-handoff) as the design baseline. The [A2 qualifications/support inventory](../phase_A/phase_A_a2_results.md) and [A3 ownership ledger](../phase_A/phase_A_a3_results.md#relocation-ledger), supplemented by the [B4 assertion mapping](../phase_B/phase_B_notes.md#assertion-ownership-addendum-to-a3b3), supply evidence and test ownership.

The [shared issue register](../0_async_hardening-notes.md#key-async-hardening-issues) remains the sole issue-completion record; the [sample matrix](../0_async_hardening-notes.md#sample-demonstration-coverage-matrix) remains the acceptance inventory. All issues 1–13 remain open. Phase C stage numbers below are work increments, distinct from A1 contract clause numbers.

Reusable code remains in `src/powercrud/_coordinator/`, inside the PowerCRUD distribution. Preserve one submission sequence through `Q2Adapter.submit()`. PowerCRUD owns settings translation, CRUD workers/persistence, compatibility entry points, and presentation; coordinator/q2 behavior stays independent of those consumers. django-q2 remains the only execution backend. Package extraction and installed-package proof remain E/F; broader separation, presentation parity, and stable documentation remain D.

## Baseline and evidence limits

The starting branch is `async_hardening/phase_b`, clean and matching its remote-tracking branch at `1a8c07d6` when inspected. B3 separation is `0c476b61`; B4 repairs are `b74f2d22`. No remote fetch was performed for this documentation task.

Repository briefing also covered the README, documentation index, `runproj`, `runtests`, `pyproject.toml`, tracked Docker configuration/sample environment files, and project settings/URLs. The checked-in development configuration uses the ORM q2 broker and Redis coordination cache; DatabaseCache aliases are also configured. This is configuration inspection, not evidence that any service is running or that backend guarantees pass.

The [B4 evidence](../phase_B/phase_B_notes.md#b4-verification-evidence) records 141 coordinator passes (86% coordinator coverage), 1,081 PowerCRUD passes with 23 skips, 110 deselections and eight existing warnings, plus separate minimal-settings (4) and Bootstrap (31) passes. These are historical results, not tests rerun for this draft.

Patched enqueue/fetch/hooks, inline workers, synchronous probes, sequential cache effects, and actual tracking ORM checks do not establish separate worker delivery, distributed concurrency/lease safety, cached-result completion reliability, genuinely absent distributions, the allowed q2 version range, or installed-package behavior. Preserve those distinctions in every Phase C result.

## Proposed sequencing and dependencies

Agreed sequence: C1 → shared-state/q2 feasibility checkpoint → C2 → C3 → C4 → C5 → C6 → C7. The checkpoint precedes C2–C6 implementation: C2 retention, C3 monotonic transitions, and C4 rollback all need the safe operations finalized in C5. C6 depends on those ownership/lifetime guarantees. Each implementation increment should pair a deliberate correction with behavioral coverage in its owning suite. Stage headings remain unchanged; they do not require deferring shared-state design until C5.

No production edits, tests, dependency changes, infrastructure actions, or issue-status changes are part of preparing this draft. Future fixture/service needs must be identified concretely; this plan does not authorize provisioning them.

## Agreed discussion decisions — 2026-11-07

The user accepted the sequence and C1 approach during discussion. This agreement settles direction, not exact interfaces or implementation authorization.

- Complete C1 first, then hold the shared-state/q2 feasibility checkpoint before implementing C2–C6. Investigate operations supporting retained identity, monotonic outcomes, completion delivery, and lease protection before building dependent state behavior.
- Direct manager operations raise specific, catchable errors; PowerCRUD translates those errors into actionable user feedback.
- Launch validation occurs before reservations or submission. Validate configuration and required capabilities during routine explicit use; keep connectivity and worker probes separate.
- Preserve the agreed enablement behavior: safe dormant/synchronous use, explicit enablement for direct launches, actionable errors above the async threshold, and continued operations for existing tasks after launches are disabled.

Exact exception symbols/hierarchy, response payloads, logging, and capability-validation mechanics remain open. No cache algorithm, worker wrapper, completion mechanism, or support reduction was selected.

## Plan Phases

### C1: Validate explicit use and enforce launch enablement

Apply A1 contract C2 and B1 configuration ownership. Validate settings shape, installed apps/dependencies, reconstructible manager configuration, resource keys, shared-state capabilities, and effective queue/result options at explicit use. Dormant imports remain quiet and safe before Django settings or q2 runtime are available. Reachability probes cannot establish a live worker or atomic cache guarantees.

PowerCRUD maps `ASYNC_ENABLED` into permission for new launches. Core/below-threshold use stays synchronous; disabled or invalid above-threshold async use reports an actionable error. Existing work can still report progress, finish, reconcile, and clean up. Verify genuine dependency absence in an isolated environment/process rather than equating removal from `INSTALLED_APPS` with uninstalling q2. The agreed error-handling direction is recorded above; exact interfaces remain for design below.

### C2: Preserve identity, context, and execution evidence

Follow B1's [retained identity specification](../phase_B/phase_B_notes.md#4-task-identity-polling-and-cleanup-lookup) and [seven-wrinkle assignment](../phase_B/phase_B_notes.md#5-seven-identity-wrinkles-implementation-assignment). The required identity fields, versioned mapping, planned `{key_namespace}:async:task:{task_key}` key, and location-bound factories are already specified. Implement retention and failure semantics alongside lifecycle state; do not invent cross-cache discovery or require a dashboard model.

Derive reconstruction metadata from the selected manager instance, keeping application config separate from coordination settings and q2 execution/result routing. Invalid explicit metadata must fail visibly; absent metadata may use the documented default. Preserve existing constructor signatures, subclass overrides, and `super()` behavior. Carry current application enablement into new launches rather than treating a retained snapshot as permission to submit again.

Cover direct/legacy launch capture, class/path conflicts, serialized kwargs/config, literal UUID worker args, deprecated positional UUID parsing, aliases, automatic context in supported worker paths, descendant acquisition failure and original PK types, helper progress, polling, and cleanup. How to supply automatic context/identity without breaking arbitrary legacy callable signatures needs investigation; no new worker wrapper or injected argument requirement is selected by this draft.

### C3: Report truthful outcomes and retain terminal state

Apply A1 contract C3: use one coherent observation for endpoint/tracking/consumer state. Ordinary arbitrary `False`, `None`, and dictionaries remain successful returns unless a worker opts into the explicit business-outcome contract. PowerCRUD translates bulk failure/partial failure with useful counts/errors. Execution failure and reporting failure remain separate; do not add automatic business retries.

Retain the agreed small terminal snapshot for a configurable 24 hours from completion, separately from live progress TTL and optional database history. Unknown evidence must remain unknown, with a reason and finite polling behavior. Terminal transitions must withstand duplicate callbacks, stale execution events, late progress/create, and callback errors. Repair optional tracking where retained evidence permits it.

Investigate actual completion delivery across the existing claimed broker/result matrix, including cached results, save/pruning options, and custom hooks. Keep transport and result storage separate. B's normalized completion types and snapshot transport alone do not prove delivery. Outcome symbols/payloads, transition operations, and completion mechanism remain open technical decisions.

### C4: Make submission and lifecycle ordering safe

Establish identity/reservations/initial lifecycle evidence before delivery can trigger worker progress or completion. Pending cannot claim accepted queue submission prematurely. Attaching a returned execution reference or emitting a late event must preserve an already observed terminal outcome. Exercise explicit sync success and exceptions after work starts, alongside fast separate-worker completion.

Classify definitely rejected and uncertain submission honestly. Rollback may remove only reservations owned by that launch; uncertain submission must not cause blind retry or unsafe release. Inspect actual caller transactions and use `transaction.on_commit` where inputs need successful commit, with rollback-no-submit and saved-data visibility checks. Existing committed-input callers can submit immediately. No outbox, new public helper, or extra persistent status model is presumed necessary.

### C5: Protect shared registries and resource ownership

Apply A1 contract C4 and Q2/Q4. Preserve claimed Redis, Memcached, and DatabaseCache support. Inventory existing claims and select backend operations capable of ownership-safe acquisition/release/rollback, non-losing registry/index updates, and safe repeated descendant registration. A get/check/delete sequence alone cannot establish conditional release. File-cache and sequential tests remain limited baselines.

Investigate live protection, queue waiting time, q2 receipt expiry, long work, stale queued delivery, expiration/reacquisition, renewal failure, and crash recovery together. A busy marker cannot itself prevent an old disconnected worker from writing. Select algorithms and supported timing rules only after demonstrating their guarantees; return specific infeasibility or proposed support changes for agreement. Redis-first work is sequencing, not permission to reduce support.

Use synchronized multi-process tests against each claimed backend to verify competing reservation, concurrent membership changes, partial failure, replacement-owner safety, and actual protection/recovery. Record which guarantees were exercised; passing cache probes or sequential cases cannot substitute.

### C6: Reconcile conservatively and expose force cleanup

Apply A1 contract C5 after identity, execution evidence, and lease ownership are reliable. Use retained submission/start/lease/terminal metadata plus adapter evidence. A missing q2 result row is compatible with queued/running/pruned work; lookup failure is unavailable evidence. Neither alone permits cleanup. Age identifies recovery candidates, not proof of worker termination or business rollback.

Define explicit administrative force request/reason and unresolved-execution reporting separately from normal reconciliation. Release only owned artifacts; preserve terminal snapshots/history, report inspected/reconciled/skipped/uncertain/failed outcomes, and make repeated cleanup safe. Keep command/schedule selection bound to its configured location and cleanup operational after launch disablement. Do not automatically register schedules.

### C7: Review consumer alignment and hand over to Phase D

Keep generic state, configuration, q2, reconstruction, context, optional tracking, and endpoint assertions in `src/coordinator_tests/`. Keep settings translation, public compatibility, thresholds, CRUD/domain persistence, command/schedule wrappers, sample behavior, and rendering in the consumer suite. Consult the linked A3/B4 mapping before changing retained wrong-behavior assertions; record intentional changes rather than deleting distinct coverage.

Coordinate D1–D6 sample changes with the corresponding correction: launch/progress, conflicts, business failure, descendants, dashboard lifecycle, and cleanup. D7 configuration permutations belong in automated settings/process tests; D8 remains E/F. Use the existing sample paths rather than creating configuration-specific screens. Phase D owns broader DaisyUI/Bootstrap observation and repeatable user instructions; carry any unverified acceptance there explicitly.

Future implementation verification uses the existing container runner for both suites, including separate minimal-settings and Bootstrap selections. Record focused regression evidence, full-suite outcomes, real worker/backend scenarios, and remaining limits separately. Update issue completion only when its required outcome and relevant verification are complete; neither a Phase C checkbox nor a suite pass alone closes an issue.

## Open technical decisions

These are implementation questions within settled A1/B1 contracts, not reopened product-policy questions. Sequencing and C1 error-handling direction are agreed above; discuss the remaining details before implementation.

| Decision | Required investigation / discussion | Needed by |
|---|---|---|
| Validation and error interface | Direction agreed: catchable manager errors translated by PowerCRUD, launch validation before reservations/submission, and separate probes. Exact error types/payloads/logging, capability checks, and reconciliation with existing public validators remain open. | C1, C4 |
| Retained state and identity lifetime | Live writes/refresh/expiry, execution attachment, failure handling, and atomic transition primitives; retain identity throughout live work and terminal retention without cross-cache discovery. | C2–C5 |
| Legacy worker/context integration | Automatic capture/context with existing callable signatures, constructor/config export, reserved metadata conflicts, and alias/deprecation behavior; preserve B's one submission path. | C2, C4 |
| Outcome and observation encoding | Explicit business-result type/wire representation, bounded retained result/error data, unknown polling stop behavior, and endpoint/tracking compatibility. Ordinary return semantics and 24-hour default are settled. | C3 |
| Reliable q2 completion | Mechanism for claimed cached/ORM results, hook overrides, save/pruning options, failure acknowledgement defaults, and version-range coverage. No support reduction or retry framework is selected. | C3–C4 |
| Ownership and lifetime algorithms | Backend-specific safe registry/index/lock primitives, timing/renewal strategy, loss-of-lease response, and stale-worker protection limits. Bring concrete feasibility limits back for agreement. | C2–C6 |
| Submission and operator feedback | Actual transactional launch sites, before-commit return/response behavior where needed, uncertain enqueue evidence, and explicit force-cleanup API/CLI/report shape. | C4, C6 |

Final package branding/settings namespace and publication decisions remain E/F. Durable orchestration/replay, guaranteed notifications, exactly-once business effects, and rolling in-flight upgrades remain outside the agreed scope; retain Q9's compatibility window and drained-upgrade procedure.

## Draft verification

Documentation-only preparation: all 67 local links/anchors in the three changed documents passed, and `git diff --check` passed. No runtime tests were run; historical B4 passes remain linked above.

After recording the discussion decisions, all 68 local links/anchors in the three updated documents and `git diff --check` passed. No runtime tests were run for this documentation update.

A broader check of 415 local links/anchors also found three pre-existing historical references: `phase_B_audit.md` targets the absent `testing.md#test-suites` anchor; `phase_A_a2_results.md` targets the removed `src/tests/test_async_hooks.py`; and `phase_A_a3_results.md` targets the absent `phase_A_a2_results.md#test-ownership-map` anchor. Those Phase A/B records were left unchanged.
