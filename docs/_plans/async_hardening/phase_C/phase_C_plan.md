# Phase C: Harden configuration and lifecycle

## Status

- ✅ Initial discussion draft prepared on 2026-11-07 from the [overall checklist](../0_async_hardening-plan.md#phase-c-harden-configuration-and-lifecycle), [A1 contracts](../phase_A/phase_A_notes.md#a1-draft-contracts-for-discussion), [B1 specification](../phase_B/phase_B_notes.md#b1-technical-specification--2026-11-07), and [B4 handoff](../phase_B/phase_B_notes.md#phase-c-handoff).
- ✅ Sequence and C1 error-handling approach agreed on 2026-11-07; see the [decision record](phase_C_notes.md#agreed-discussion-decisions--2026-11-07).
- ✅ C1 implementation completed on 2026-11-07; see the [C1 implementation record](phase_C_notes.md#c1-implementation-record--2026-11-07).
- ✅ C2.1 static feasibility investigation and C2.2 implementation plan completed on 2026-11-11; see the [findings and handoff](phase_C_notes.md#c21-feasibility-findings--2026-11-11).
- ✅ C2.3–C2.8 implementation and verification completed on 2026-11-11; see the [implementation and verification record](phase_C_notes.md#c23c28-implementation-and-verification--2026-11-11).
- 🔳 All [hardening issues 1–13](../0_async_hardening-notes.md#key-async-hardening-issues) remain open pending their complete acceptance evidence.

## Next

- ✅ C2 is complete. Stop here; C3–C7 remain unstarted.

## C1: Validate explicit use and enforce launch enablement

1. ✅ Keep dormant imports and synchronous use safe; explicit async use produces targeted configuration/dependency errors (issues 1–4).
2. ✅ Enforce enablement for new launches and threshold-triggered async work while preserving existing-task observation, completion, and cleanup (issues 2–4).

## C2: Preserve identity, context, and execution evidence

1. ✅ Investigate shared-state/q2 feasibility and record evidence for safe identity retention, execution attachment, and compatible worker/context integration; identify any concrete blocker before implementation (issues 12–13).
2. ✅ Produce an implementation plan from the feasibility findings, covering all [seven identity wrinkles](../phase_B/phase_B_notes.md#5-seven-identity-wrinkles-implementation-assignment), compatibility constraints, test ownership, and dependencies on C3–C6; resolve any blocking decision (issues 2, 10, 12–13).
3. ✅ Implement automatic identity capture from the actual selected manager, strict explicit metadata/configuration validation, and UUID/key-alias compatibility (issues 2, 12–13).
4. ✅ Implement versioned identity retention and execution/result-reference attachment in the configured coordination location, including missing/invalid identity and persistence-failure behavior (issues 12–13).
5. ✅ Carry and reconstruct that identity through supported worker and completion paths, preserving supported serialized kwargs/application config, constructor signatures, subclass overrides, and the single q2 submission path (issues 12–13).
6. ✅ Establish parent context in supported worker paths; make descendant registration and progress helpers use the parent manager/configuration, preserve original PK types, and stop protected descendant work on acquisition failure (issues 10, 12–13).
7. ✅ Make polling and cleanup reconstruct the originating manager/configuration and q2 execution/result route from retained identity in their selected location; missing identity remains unknown (issues 2, 12–13).
8. ✅ Run focused regressions and both full server suites through `./runproj exec`; update C2 evidence and checklist, check links/anchors and `git diff --check`, and make semantic commits before stopping at C2 (issues 2, 10, 12–13).

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
