# Persistence Hooks Plan

## Status

Phases 1-5 complete

## Next

- Review the shipped async bulk backend contract before deciding whether phase 6 standalone `AsyncManager` reuse should be productized next.
- Decide whether standalone async worker reuse is worth adding now or whether the CRUD-driven async bulk story is sufficient for the next release.
- Keep delete persistence hooks deferred unless a concrete downstream need emerges.

## Desired outcomes

- Downstream apps can route standard form and inline writes through one explicit PowerCRUD hook.
- Downstream apps can route sync bulk update through a first-class PowerCRUD hook without overriding several internal methods.
- Async bulk has a worker-safe path to parity that does not require serializing live CRUD view instances.
- Standalone `AsyncManager` tasks can reuse the same async persistence backend contract.

## Phase 1: Finalize Sync Hook Contracts

1. [x] Lock the public single-object persistence contract for v1.
    - [x] Confirm the public method name as `persist_single_object(...)`.
    - [x] Confirm that `mode` is explicit and limited to `"form"` and `"inline"` in v1.
    - [x] Confirm whether `instance` remains in the signature for clarity and future-proofing.
2. [x] Lock the public sync bulk update persistence contract for v1.
    - [x] Confirm the public method name as `persist_bulk_update(...)`.
    - [x] Confirm that sync bulk input is normalized bulk payload, not `cleaned_data`.
    - [x] Confirm that the bulk hook returns the standard result dict shape expected by the existing UI flow.
3. [x] Lock the ownership rules that must be explicit in the first release.
    - [x] Document explicit ownership of `form.save_m2m()` when a custom single-object hook bypasses `form.save()`.
    - [x] Confirm that bulk delete is out of scope unless a concrete downstream requirement emerges.
    - [x] Confirm that no generic post-persist callback lands in the first sync release.

Done when:
The v1 sync hook names, signatures, ownership rules, and scope boundaries are agreed well enough that implementation can start without reopening API design questions.

## Phase 2: Implement Sync Single-Object Persistence Hook

1. [x] Add the public single-object hook to the mixin surface.
    - [x] Place the hook in the relevant mixin layer so both normal form and inline save can reach it naturally.
    - [x] Keep the default implementation aligned with current `form.save()` behavior.
2. [x] Route standard form persistence through the new hook.
    - [x] Update `FormMixin.form_valid()` to call the hook instead of calling `form.save()` directly.
    - [x] Preserve current redirect and HTMX response behavior.
3. [x] Route inline persistence through the same hook.
    - [x] Update `InlineEditingMixin._dispatch_inline_row()` to call the same hook after validation and guard checks.
    - [x] Preserve current inline success and error response behavior.
4. [x] Prove the new seam with tests.
    - [x] Add or update tests proving normal form save delegates through the public hook.
    - [x] Add or update tests proving inline save delegates through the same public hook.
    - [x] Add or update tests proving default behavior remains unchanged when the hook is not overridden.

Done when:
Standard form and inline persistence both delegate through one public hook and all existing default behavior still works.

## Phase 3: Implement Sync Bulk Update Hook

1. [x] Add the public sync bulk update hook.
    - [x] Define the hook around `queryset`, `fields_to_update`, `field_data`, and optional `progress_callback`.
    - [x] Keep the existing internal bulk implementation as the default fallback.
2. [x] Route sync bulk update through the new hook.
    - [x] Update `bulk_edit_process_post()` so sync bulk update delegates through the public hook.
    - [x] Leave sync bulk delete unchanged unless scope is explicitly widened later.
3. [x] Prove the bulk seam with tests.
    - [x] Add or update tests covering successful bulk update through the public hook.
    - [x] Add or update tests covering validation failures and error rendering through the public hook.
    - [x] Add or update tests proving default behavior remains unchanged when the hook is not overridden.
4. [x] Update the shipping docs for the new sync hooks before release.
    - [x] Update `docs/mkdocs/guides/customisation_tips.md` to document the new sync persistence extension points.
    - [x] Update `docs/mkdocs/guides/forms.md` to explain the single-object hook in the standard form path.
    - [x] Update `docs/mkdocs/guides/inline_editing.md` to explain the same hook in the inline save path.
    - [x] Update `docs/mkdocs/guides/bulk_edit_sync.md` to document the sync bulk persistence hook.
    - [x] Update `docs/mkdocs/reference/config_options.md` or the most appropriate reference page if any public settings or public hook references belong there.
    - [x] Update any example/reference page that should show intended override usage if the guides alone are not sufficient.

Done when:
Sync bulk update has an explicit extension seam, the sync hook story is documented in the shipped docs, and downstream apps no longer need to override private/internal methods to centralize write orchestration.

## Phase 4: Define Async Bulk Persistence Backend Contract

1. [x] Lock the worker-safe backend abstraction for async bulk update.
    - [x] Define the async bulk persistence backend contract as a worker-safe abstraction rather than a live view hook.
    - [x] Decide whether PowerCRUD ships a base class, protocol-style contract, or documented callable shape.
2. [x] Lock the backend resolution surface.
    - [x] Decide the configuration surface for backend resolution, likely path plus config.
    - [x] Decide where backend resolution helpers should live so `AsyncManager` keeps a narrow responsibility.
3. [x] Lock the execution context shape.
    - [x] Define the plain-data execution context passed to the backend.
    - [x] Confirm that the context excludes live request/view state.
4. [x] Lock parity expectations between sync and async bulk.
    - [x] Confirm whether sync bulk can optionally delegate to the same backend when configured.
    - [x] Confirm what parity means for workflow-aware downstream apps that disable async until semantics match.

Done when:
There is an agreed contract for async bulk persistence that is serializable, testable, and independent of live view instances.

## Phase 5: Implement Async Bulk Backend Resolution

1. [x] Add backend resolution support to async bulk launch.
    - [x] Pass backend path/config through worker-safe task payload from the async bulk launch path.
    - [x] Preserve existing conflict, progress, and lifecycle wiring.
2. [x] Delegate worker persistence through the configured backend.
    - [x] Update `powercrud.tasks.bulk_update_task` to resolve the backend and delegate persistence when configured.
    - [x] Preserve the existing internal bulk update path as the default fallback when no backend is configured.
3. [x] Decide delete behavior for async bulk.
    - [x] Confirm whether async bulk delete remains unchanged in this phase.
    - [x] Record any follow-up work if delete later needs a matching backend contract.
4. [x] Prove the async seam with tests.
    - [x] Add or update tests proving configured async bulk uses the backend contract rather than the raw default implementation.
    - [x] Add or update tests proving progress, conflict, and lifecycle behavior still work.

Done when:
Async bulk update can match sync bulk persistence semantics without coupling the worker to a request-scoped view object.

## Phase 6: Support Standalone `AsyncManager` Usage

1. [ ] Define the standalone reuse story for the async backend contract.
    - [ ] Confirm that workers launched via `AsyncManager.launch_async_task()` can use the same backend contract.
    - [ ] Confirm the minimum worker payload needed for that path.
2. [ ] Document and demonstrate the standalone path.
    - [ ] Add documentation showing how standalone async workers can resolve and use the same backend.
    - [ ] Provide at least one sample or reference implementation path for downstream projects.
3. [ ] Prove lifecycle compatibility in the standalone path.
    - [ ] Confirm that lifecycle metadata still works in the standalone usage pattern.
    - [ ] Confirm that progress reporting still works in the standalone usage pattern.

Done when:
The async persistence backend model is reusable outside CRUD views and downstream teams do not need a second abstraction for custom async tasks.

## Phase 7: Documentation and Rollout

1. [ ] Document migration and adoption guidance after the sync release lands.
    - [ ] Add migration guidance for downstream projects currently overriding internal methods once the final sync API is confirmed in released docs.
    - [ ] Record any release-note level caveats or upgrade notes needed for maintainers.
2. [ ] Document the async backend story after it lands.
    - [x] Add docs for async bulk backend resolution.
    - [ ] Add docs for standalone `AsyncManager` reuse of the same backend contract.
3. [ ] Document limitations and non-goals explicitly.
    - [x] Record that live CRUD view instances are not passed into async workers.
    - [x] Record that single-object and bulk persistence remain separate contracts.
    - [x] Record any deferred items such as bulk delete parity or post-persist callbacks.

Done when:
PowerCRUD exposes a documented persistence extension story that downstream maintainers can understand without reading internal implementation paths.

## Phase 8: Revisit Delete Persistence Hooks

1. [ ] Reassess whether delete persistence hooks are needed after the update hook story has shipped and settled.
    - [ ] Review whether downstream projects now have a concrete need for single-object delete hooks.
    - [ ] Review whether downstream projects now have a concrete need for sync bulk delete hooks.
    - [ ] Review whether downstream projects now have a concrete need for async bulk delete hooks.
2. [ ] Define delete as a separate persistence contract family if the need is real.
    - [ ] Confirm that delete remains separate from update contracts rather than overloading `persist_bulk_update(...)`.
    - [ ] Confirm whether delete should have sync-only hooks first or a broader phased rollout.
3. [ ] Plan implementation only after the product need is validated.
    - [ ] Record the domain and API differences that justify delete-specific contracts.
    - [ ] Add a dedicated delete-hooks plan or extend this one only if that work becomes active.

Done when:
PowerCRUD has either intentionally deferred delete hooks with clear reasoning or has a validated follow-up plan for single-object delete, sync bulk delete, and async bulk delete seams.
