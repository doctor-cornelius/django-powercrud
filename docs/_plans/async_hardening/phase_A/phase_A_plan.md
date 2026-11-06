# ✅ Phase A: Define ownership and behavior

## Status

- ✅ Phase documents seeded from the overall plan and discussion.
- ✅ A1 contract draft, evidence review, and decision questions prepared in [Phase A notes](phase_A_notes.md#a1-draft-contracts-for-discussion); four focused current-behavior tests recorded in the [audit](phase_A_audit.md#focused-verification).
- ✅ Q1–Q10 resolved and A1 contract decisions complete; agreed behavior and scope limits recorded in the notes.
- ✅ A2 findings qualified, supported configurations inventoried, ownership mapped, and three focused existing-test batches recorded in the [A2 results](phase_A_a2_results.md).
- ✅ A3 established the independent coordinator suite, relocated reusable tests, and separated runner/CI selection ([A3 results](phase_A_a3_results.md)).
- ✅ A4 verification and final review complete on 2026-11-04; [non-coverage review](phase_A_noncoverage_review.md) and [coverage follow-up](phase_A_coverage_results.md) resolve the remaining infrastructure issues. Production implementation has not started.

## Next

- 🔳 Prepare Phase B's plan/notes using the [cross-phase handoff](../0_async_hardening-notes.md#phase-a-completion-and-handoff); preserve established behavior while creating the internal boundary.

## ✅ A1: Define ownership and contracts

1. ✅ Record the coordinator, q2 adapter, and PowerCRUD responsibilities and public integration contract ([issue 13](../0_async_hardening-notes.md#key-async-hardening-issues)).
2. ✅ Settle enablement, explicit launch versus fallback, terminal outcomes, operation failures, lock ownership/expiration, and reconciliation semantics; record compatibility implications ([issues 2–3 and 6–12](../0_async_hardening-notes.md#key-async-hardening-issues)).
3. ✅ State supported cache capabilities and queue result-storage assumptions, distinguishing required behavior from implementation investigations ([issues 9–11](../0_async_hardening-notes.md#key-async-hardening-issues)).

## ✅ A2: Qualify findings and assign coverage

1. ✅ Qualify each [hardening issue 1–13](../0_async_hardening-notes.md#key-async-hardening-issues), recording evidence, coverage gaps, and suite ownership in the [A2 results](phase_A_a2_results.md).
2. ✅ Map relevant test classes, functions, helpers, dependencies, and coverage limits to proposed destinations; distinguish genuine q2/concurrency checks from mocked or sequential coverage.
3. ✅ Audit sample background-task demonstrations, settings, docs, and supporting tests; record scenario owners, evidence limits, and follow-up acceptance in the [shared coverage matrix](../0_async_hardening-notes.md#sample-demonstration-coverage-matrix).

## ✅ A3: Separate tests before Phase B

1. ✅ Establish a dedicated coordinator test tree with suite-owned settings, fixtures, URLs, minimal models, and importable workers ([issues 4 and 13](../0_async_hardening-notes.md#key-async-hardening-issues)).
2. ✅ Relocate the 63 reusable coordinator cases and retain CRUD, sample, presentation, and compatibility coverage in PowerCRUD with all assertions mapped ([A3 results](phase_A_a3_results.md#relocation-ledger)).
3. ✅ Add separate runner, pytest, coverage, and CI selection; record focused verification and residual dependencies ([A3 results](phase_A_a3_results.md#runner-and-ci-behavior)).

## ✅ A4: Verify the split and hand over

1. ✅ Run both suites separately in the required Compose environment, recording exact commands, results, old-to-new test mapping, and remaining dependencies ([A4 results](phase_A_a4_results.md); issues 4 and 13).
2. ✅ Confirm the split preserves the existing assertions and document intentional future contract changes and Phase B dependencies ([A3 ledger](phase_A_a3_results.md#relocation-ledger); [A4 results](phase_A_a4_results.md)).
3. ✅ Complete the Phase A handoff review and record [carry-forward requirements](../0_async_hardening-notes.md#phase-a-completion-and-handoff); hardening issues 1–13 remain open.
