# Async hardening and coordinator extraction

## Status

- ✅ Discussion captured and scope includes roadmap steps 1, 2a, and 2b; step 3 remains deferred.
- ✅ A1 contracts and Q1–Q10 decisions recorded; four focused current-behavior tests are documented in the Phase A audit.
- ✅ A2 qualified all 13 findings, inventoried current support claims, mapped test ownership, and recorded three focused existing-test batches in the [A2 results](phase_A/phase_A_a2_results.md).
- ✅ A3 established the independent coordinator suite, relocated 63 reusable cases, and added separate runner/CI selection ([A3 results](phase_A/phase_A_a3_results.md)).
- ✅ Phase A complete on 2026-11-04: contracts, qualification, test separation, server verification, and infrastructure follow-ups reviewed ([handoff](0_async_hardening-notes.md#phase-a-completion-and-handoff)).
- 🔳 Production implementation has not started; django-q2 remains the only execution backend, and hardening issues 1–13 remain open.

## Next

- 🔳 Prepare Phase B's plan/notes from the [Phase A handoff](0_async_hardening-notes.md#phase-a-completion-and-handoff), then establish the internal boundary before intentional behavior fixes.

## ✅ Phase A: Define ownership and behavior

Detailed work: [Phase A plan](phase_A/phase_A_plan.md) and [notes](phase_A/phase_A_notes.md).

1. ✅ Record the coordinator, q2 adapter, and PowerCRUD responsibilities and their public integration contract ([issue 13](0_async_hardening-notes.md#key-async-hardening-issues)).
2. ✅ Establish expected enablement, fallback, status, failure, lock ownership, and reconciliation behavior; identify compatibility implications ([issues 2–3 and 6–12](0_async_hardening-notes.md#key-async-hardening-issues)).
3. ✅ Qualify the review findings, identify focused regressions, and map existing test ownership ([issues 1–13](0_async_hardening-notes.md#key-async-hardening-issues); [A2 results](phase_A/phase_A_a2_results.md)).
4. ✅ Before Phase B, separate coordinator/q2 tests from PowerCRUD integration tests using the [ownership inventory](0_async_hardening-notes.md#test-ownership-review); give the coordinator suite independent fixtures, settings, URLs, test models, and importable workers ([A3 results](phase_A/phase_A_a3_results.md); issues 4 and 13).
5. ✅ Run both suites separately, verify discovery and migration coverage, and distinguish mocked execution from real q2/concurrency evidence; keep all subsequent tests in their owning suite ([A4 results](phase_A/phase_A_a4_results.md); issues 4 and 6–13).
6. ✅ Audit sample background-task demonstrations and record current evidence, ownership, gaps, and acceptance criteria in the [coverage matrix](0_async_hardening-notes.md#sample-demonstration-coverage-matrix).

## Phase B: Establish the internal boundary

1. 🔳 Isolate q2 imports, enqueueing, result access, completion translation, and execution options behind an internal adapter ([issues 1–2 and 13](0_async_hardening-notes.md#key-async-hardening-issues)).
2. 🔳 Give coordination explicit configuration and dependencies without importing PowerCRUD views, mixins, templates, or configuration helpers ([issues 2–3 and 13](0_async_hardening-notes.md#key-async-hardening-issues)).
3. 🔳 Keep CRUD decisions, workers, persistence, and presentation in PowerCRUD, with existing public imports preserved where practical ([issue 13](0_async_hardening-notes.md#key-async-hardening-issues)).
4. 🔳 Verify the structural change preserves established behavior before applying intentional fixes, keeping coordinator and PowerCRUD test dependencies separate ([issues 4 and 13](0_async_hardening-notes.md#key-async-hardening-issues)).

## Phase C: Harden configuration and lifecycle

1. 🔳 Keep dormant imports safe and make explicit background-task use produce targeted configuration errors, with consistent enablement, inactivity logs, and cleanup rules; pass misconfiguration regressions ([issues 1–4](0_async_hardening-notes.md#key-async-hardening-issues)).
2. 🔳 Preserve manager identity/configuration through launch, worker context, completion, and descendant conflict registration ([issue 12](0_async_hardening-notes.md#key-async-hardening-issues)).
3. 🔳 Preserve truthful terminal status and operation results across queue execution, progress polling, lifecycle events, and dashboard persistence ([issues 6–7](0_async_hardening-notes.md#key-async-hardening-issues)).
4. 🔳 Make launch registration and lifecycle ordering safe for fast workers and synchronous execution without resetting newer progress ([issue 8](0_async_hardening-notes.md#key-async-hardening-issues)).
5. 🔳 Prevent concurrent registry updates from losing active tasks and make lock acquisition, release, expiration, and cache failure handling safe ([issues 9–10](0_async_hardening-notes.md#key-async-hardening-issues)).
6. 🔳 Reconcile queued, running, unknown, and abandoned work without inferring abandonment from a missing result row or success from missing progress ([issues 6 and 11](0_async_hardening-notes.md#key-async-hardening-issues)).
7. 🔳 Keep sample demonstrations aligned with the corrected launch, progress, failure, and cleanup contracts; record any example changes against the [coverage matrix](0_async_hardening-notes.md#sample-demonstration-coverage-matrix) ([D1–D6](0_async_hardening-notes.md#sample-demonstration-coverage-matrix)).

## Phase D: Verify separation and document the contract

1. 🔳 Demonstrate coordinator launch, progress, completion, tracking, and cleanup without CRUD components, and synchronous PowerCRUD use without the background-task stack ([issues 1–4 and 13](0_async_hardening-notes.md#key-async-hardening-issues)).
2. 🔳 Verify PowerCRUD bulk workers, failure reporting, conflict presentation, and both maintained template packs against the coordinator contract ([issues 6–8 and 10–12](0_async_hardening-notes.md#key-async-hardening-issues)).
3. 🔳 Pass focused regressions and appropriate integration checks in the full Compose environment; record results and update the hardening register only for verified outcomes ([issues 1–13](0_async_hardening-notes.md#key-async-hardening-issues)).
4. 🔳 Correct reusable examples, document enablement and minimal-settings tests, update README, async guides/reference and release notes, and record extraction readiness ([issue 5](0_async_hardening-notes.md#key-async-hardening-issues)).
5. 🔳 Verify async sample presentation and observed outcomes under DaisyUI and Bootstrap; keep settings/dependency permutations in automated tests ([D1–D7](0_async_hardening-notes.md#sample-demonstration-coverage-matrix)).

## Phase E: Extract the standalone package

1. 🔳 Settle package/class names, repository location, supported versions, license, and release destination before creating the standalone project.
2. 🔳 Move coordination and its q2 adapter into one independent source of truth with package-owned settings, optional model tracking, progress endpoints, and cleanup utilities ([issues 12–13](0_async_hardening-notes.md#key-async-hardening-issues)).
3. 🔳 Move the already separate coordinator/q2 suite into the package without duplicating it; provide metadata, wheel/sdist artifacts, independent CI, installation/API documentation, a non-PowerCRUD example, and a working release process ([issues 4 and 13](0_async_hardening-notes.md#key-async-hardening-issues)).
4. 🔳 Define and verify migration of settings, public imports, manager/hook paths, URLs, cache namespaces, and queued/in-flight work ([issues 2–3 and 10–13](0_async_hardening-notes.md#key-async-hardening-issues)).
5. 🔳 Include a runnable non-PowerCRUD background-task example with package installation, launch, progress/lifecycle observation, and cleanup instructions ([D8](0_async_hardening-notes.md#sample-demonstration-coverage-matrix)).

## Phase F: Integrate and verify the extracted package

1. 🔳 Make PowerCRUD optionally depend on and consume the package for background work, preserving synchronous use without the package or q2 installed ([issues 1–4 and 13](0_async_hardening-notes.md#key-async-hardening-issues)).
2. 🔳 Pass standalone and PowerCRUD integration checks against built and installed package artifacts without relying on a sibling source checkout.
3. 🔳 Verify supported Django/Python combinations, real q2 lifecycle and cleanup, compatibility paths, and both maintained presentation packs; recheck the hardening register against installed artifacts ([issues 1–13](0_async_hardening-notes.md#key-async-hardening-issues)).
4. 🔳 Complete package release readiness and PowerCRUD dependency wiring; document migration, verification evidence, and any required repository or publication decisions ([issues 5 and 13](0_async_hardening-notes.md#key-async-hardening-issues)).
5. 🔳 Verify package example and PowerCRUD sample against the installed package; ensure examples have repeatable setup and observable acceptance outcomes ([D1–D8](0_async_hardening-notes.md#sample-demonstration-coverage-matrix)).
