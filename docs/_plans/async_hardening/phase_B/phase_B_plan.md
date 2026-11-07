# ✅ Phase B: Establish the internal boundary

## Status

- ✅ Phase B documents prepared on 2026-11-06 from the [Phase A handoff](../0_async_hardening-notes.md#phase-a-completion-and-handoff).
- ✅ B1 specification complete on 2026-11-07: D1–D7, exact configuration/interfaces, identity and compatibility routing, phase assignments, and source-review acceptance are recorded in the [technical specification](phase_B_notes.md#b1-technical-specification--2026-11-07).
- ✅ Specification simplified: one direct q2 submission implementation and shared tracking mixin in B; retained-identity persistence/expiry remains C lifecycle work.
- ✅ B2 q2 execution is isolated behind the internal adapter; django-q2 remains the only execution backend.
- ✅ B3 separates reusable coordination from PowerCRUD integration; implementation and suite verification are recorded in the [B3 results](phase_B_notes.md#b3-implementation-and-verification--2026-11-07).
- ✅ B4 review and Phase B completion on 2026-11-07: compatibility repairs, assertion ownership, verification limits, and the Phase C handoff are recorded in the [B4 results](phase_B_notes.md#b4-review-and-handoff--2026-11-07).
- 🔳 Hardening issues 1–13 remain open in the [shared register](../0_async_hardening-notes.md#key-async-hardening-issues).

## Next

- 🔳 Prepare Phase C's detailed plan from A1, B1, and the [B4 handoff](phase_B_notes.md#phase-c-handoff), then implement intentional hardening corrections in their owning suites.

## ✅ B1: Confirm the boundary and compatibility seams

1. ✅ Map existing entry points and dependencies to coordinator, q2 adapter, and PowerCRUD ownership, including tracking, endpoints, context, cleanup, compatibility, configuration, and test seams ([Phase B audit](phase_B_audit.md); issues 1–3, 12–13).
2. ✅ Specify explicit coordinator configuration and worker reconstruction inputs; keep PowerCRUD settings translation in the consumer layer ([configuration/interfaces](phase_B_notes.md#1-configuration-and-construction); issues 2–3, 12–13).
3. ✅ Record module paths, compatibility wrappers, hook routing, cache namespaces, source-review acceptance, and behavior intentionally retained for Phase C ([technical specification](phase_B_notes.md#b1-technical-specification--2026-11-07); issues 1–3, 6–13).

## ✅ B2: Isolate q2 execution

1. ✅ Route q2 dependency loading, queue options, enqueueing, result access, completion translation, health probes, and scheduling integration through a narrow internal adapter (issues 1–2, 13).
2. ✅ Keep worker completion entry points importable and legacy hook consumers working; preserve current effective option and result behavior (issues 8, 12–13).
3. ✅ Move q2-specific test patch targets to the adapter as implementation moves, retaining behavioral assertions (issues 4, 13).

## ✅ B3: Separate coordination from PowerCRUD integration

1. ✅ Make reusable coordination, context, tracking, endpoints, and cleanup independent of PowerCRUD configuration/logging helpers, CRUD components, sample models, and URL namespace (issues 2–3, 12–13).
2. ✅ Keep bulk decisions, CRUD workers, persistence, settings translation, conflict presentation, progress modal, and dashboard CRUD views in PowerCRUD (issue 13).
3. ✅ Preserve existing import/settings/hook/URL consumers through compatibility entry points and retain existing cache identity unless a migration is explicitly designed (issues 12–13).
4. ✅ Remove `POWERCRUD_SETTINGS` from coordinator test settings and strengthen suite isolation to reject consumer configuration dependencies (issues 4, 13).

## ✅ B4: Verify behavior preservation and hand over

1. ✅ Verify the adapter/configuration seams and legacy consumers with focused tests in their owning suites (issues 4, 13).
2. ✅ Run coordinator and PowerCRUD server suites separately through the container runner, including the consumer minimal-settings and Bootstrap selections; record exact results and evidence limits (issues 4, 13).
3. ✅ Review the dependency direction and retained assertions, record any unavoidable behavior changes explicitly, and carry unresolved hardening and backend proofs into Phase C (issues 1–13).
4. ✅ Update overall phase status and the shared register only for completed, verified outcomes; record the Phase C handoff.
