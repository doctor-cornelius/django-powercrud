# Phase C: Harden configuration and lifecycle

## Status

- 🔳 Initial discussion draft prepared on 2026-11-07 from the [overall checklist](../0_async_hardening-plan.md#phase-c-harden-configuration-and-lifecycle), [A1 contracts](../phase_A/phase_A_notes.md#a1-draft-contracts-for-discussion), [B1 specification](../phase_B/phase_B_notes.md#b1-technical-specification--2026-11-07), and [B4 handoff](../phase_B/phase_B_notes.md#phase-c-handoff).
- ✅ Sequence and C1 error-handling approach agreed on 2026-11-07; see the [decision record](phase_C_notes.md#agreed-discussion-decisions--2026-11-07).
- 🔳 Phase C implementation has not started; all [hardening issues 1–13](../0_async_hardening-notes.md#key-async-hardening-issues) remain open.

## Next

- 🔳 Discuss remaining [open technical decisions](phase_C_notes.md#open-technical-decisions), including the shared-state/q2 feasibility checkpoint after C1; implementation remains on hold.

## C1: Validate explicit use and enforce launch enablement

1. 🔳 Keep dormant imports and synchronous use safe; explicit async use produces targeted configuration/dependency errors (issues 1–4).
2. 🔳 Enforce enablement for new launches and threshold-triggered async work while preserving existing-task observation, completion, and cleanup (issues 2–4).

## C2: Preserve identity, context, and execution evidence

1. 🔳 Capture the selected manager/configuration automatically and retain versioned identity plus execution/result routing in the configured location (issues 12–13).
2. 🔳 Resolve all [seven identity wrinkles](../phase_B/phase_B_notes.md#5-seven-identity-wrinkles-implementation-assignment), including strict explicit metadata, parent context, descendant PK types, aliases, polling, and cleanup reconstruction (issues 2, 10, 12–13).

## C3: Report truthful outcomes and retain terminal state

1. 🔳 Keep execution and explicit business outcomes distinct; missing/expired/unavailable evidence remains unknown across status, polling, tracking, and PowerCRUD consumers (issues 6–7).
2. 🔳 Retain terminal snapshots with the agreed configurable 24-hour default; duplicate/late events and optional callback failures cannot rewrite the job outcome (issues 6–8).
3. 🔳 Deliver completion across claimed q2 result/hook modes without adding automatic PowerCRUD retries (issues 6–7, 13).

## C4: Make submission and lifecycle ordering safe

1. 🔳 Establish identity/state before worker events; fast and explicit synchronous execution cannot be reset by late registration or execution attachment (issue 8).
2. 🔳 Distinguish definite rejection from uncertain submission; verify rollback ownership and commit-safe behavior at affected launch sites (issues 8, 10–13).

## C5: Protect shared registries and resource ownership

1. 🔳 Prevent lost registry/index updates and replacement-owner deletion across claimed coordination backends, with synchronized process evidence (issues 9–10).
2. 🔳 Establish protection and recovery for supported job lifetimes, partial acquisition, descendant registration, expiration/reacquisition, and lease failure (issues 10, 12).

## C6: Reconcile conservatively and expose force cleanup

1. 🔳 Reconcile using retained submission/start/lease/result evidence; missing result rows or lookup errors alone never release uncertain work (issues 6, 11).
2. 🔳 Make force cleanup explicit, owner-safe, repeatable, and truthfully reported; preserve terminal retention and cleanup after launches are disabled (issues 3, 10–11).

## C7: Review consumer alignment and hand over to Phase D

1. 🔳 Align sample scenarios D1–D6 and consumer assertions with intentional contract corrections; keep configuration permutations in automated tests (issues 3–8, 10–13).
2. 🔳 Verify changes in their owning suites, record real-worker/backend evidence separately, and carry outstanding presentation, documentation, and integration acceptance into Phase D (issues 1–13).
