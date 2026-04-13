# Single Delete UX Plan

## Status

Phases A, B, C, D, E, and F are shipped.

PowerCRUD now handles single-object delete `ValidationError` refusals cleanly in HTMX/modal and non-HTMX flows, without changing the existing successful delete path.

PowerCRUD also supports built-in row-level Delete guard hooks for the standard Delete action.

PowerCRUD also supports built-in row-level Update guard hooks for the standard Edit action, with matching inline-edit blocking for guarded rows.

There is no further active implementation phase in this plan. The remaining items are later product follow-ups.

## Next

1. Consider whether normal update views should also hard-block direct update-route access when `can_update_object()` returns `False`.
2. Consider whether create/update should gain generic handled `ValidationError` response paths during persistence.
3. Consider whether standard-action policy hooks should eventually generalize further, such as to View.

## ✅ Phase A: Lock the First Shipping Scope

1. [x] Confirm the minimum first-release outcome for refused single deletes.
    - [x] Catch expected user-facing delete refusals as `ValidationError`.
    - [x] Re-render the delete confirmation UI with a visible error instead of returning HTTP 500.
    - [x] Keep the modal open for HTMX/modal requests by retargeting back to modal content.
2. [x] Confirm what is out of scope for the first patch.
    - [x] Do not silently swallow unexpected exceptions.
    - [x] Do not regress the successful single-delete flow.
    - [x] Do not require downstream projects to replace built-in delete with `extra_actions`.
3. [x] Decide whether built-in delete guard hooks ship in phase 1 or phase 2.
    - [x] Option A: first patch only handles delete-time failures robustly.
    - [x] Option B deferred: row-level built-in delete disable hooks move to the next phase.

## ✅ Phase B: Make Single Delete Failure a First-Class Response Path

1. [x] Introduce a shared single-delete failure handler in the PowerCRUD stack.
    - [x] Single-object deletion routes model-level refusal errors into a handled response path.
    - [x] HTMX requests receive a normal 200 response with renderable delete content.
    - [x] Non-HTMX requests re-render the confirmation page with the error state.
2. [x] Normalize delete refusal messages for rendering.
    - [x] String, list, and dict `ValidationError` payloads are converted into displayable messages.
    - [x] Error content is available to templates as a stable context contract.
3. [x] Keep the current async conflict guard behavior intact.
    - [x] Conflict responses continue to work as they do today.
    - [x] Delete refusal handling composes with conflict checking rather than bypassing it.
4. [x] Keep the successful delete behavior unchanged in phase 1.
    - [x] The first patch does not redesign HTMX single-delete success semantics.
    - [x] Any later alignment with create/update success-path refresh behavior is handled separately.

## ✅ Phase C: Fix the HTMX and Template Contract

1. [x] Update the delete confirmation template to render handled errors clearly.
    - [x] The modal includes an error alert region for delete-time failures.
    - [x] Error rendering works for both modal and full-page flows.
2. [x] Make the HTMX response target correct for handled delete failures.
    - [x] Error responses retarget to the modal content container.
    - [x] Modal error responses include the trigger needed to keep the modal visible.
3. [x] Preserve list context through the delete flow.
    - [x] Filter and sort state posted via `_powercrud_filter_*` is available on error redisplay.
    - [x] The first patch preserves enough context for error redisplay without changing the current success-path contract.

## ✅ Phase D: Add Built-In Delete Guard Hooks

1. [x] Define the built-in delete policy hook contract.
    - [x] Choose stable public hook names for "can delete" and "why not".
    - [x] Ensure the contract accepts both `obj` and `request`.
2. [x] Apply the contract to standard row actions.
    - [x] Built-in Delete can render disabled before the modal opens.
    - [x] Disabled rows can expose a reason tooltip consistent with existing PowerCRUD affordances.
3. [x] Keep server-side refusal handling as the final safety net.
    - [x] A disabled UI is not the only line of defense.
    - [x] Unexpected race conditions still surface a safe handled response.

## ✅ Phase E: Verify, Document, and Land Safely

1. [x] Cover the shipped phase-1 behavior with focused tests.
    - [x] HTMX modal delete refusal re-renders the delete confirmation with error content.
    - [x] HTMX modal delete refusal retargets to the modal and keeps it open.
    - [x] Non-HTMX delete refusal re-renders the page safely.
    - [x] Successful delete behavior remains unchanged.
    - [x] Sample-app coverage demonstrates the handled refusal flow on a real CRUD screen.
2. [x] Document the shipped phase-1 behavior at the right level.
    - [x] Add notes for downstream integrators if model `delete()` may raise user-facing refusals.
    - [x] Document the sample-app delete refusal demo.
3. [x] Confirm phase-1 release-readiness.
    - [x] The first patch is backward compatible for projects that never raise delete-time validation errors.
    - [x] The final behavior is predictable in both HTMX and non-HTMX flows.
4. [x] Cover the next built-in delete guard phase with focused tests and docs.
    - [x] Standard Delete renders disabled when the delete guard hook blocks the row.
    - [x] A disabled reason tooltip is shown for guarded rows.
    - [x] Sample-app and reference docs show the new built-in Delete guard capability.

## ✅ Phase F: Add Built-In Update Guard Hooks

1. [x] Define the built-in update policy hook contract.
    - [x] Choose stable public hook names for "can update" and "why not".
    - [x] Ensure the contract accepts both `obj` and `request`.
    - [x] Default behavior allows updates unless a downstream override blocks them.
2. [x] Apply the contract to the standard Edit action.
    - [x] Built-in Edit can render disabled before the modal opens.
    - [x] Disabled rows expose a reason tooltip consistent with the delete-guard pattern.
    - [x] Existing inline-edit lock and permission affordances keep working predictably alongside the new standard Edit guard hooks.
3. [x] Keep broader persistence-refusal handling out of scope for this phase.
    - [x] This phase controls the built-in Edit affordance only.
    - [x] Save-time refusal handling for update persistence remains a separate concern.
4. [x] Verify and document the built-in update guard behavior.
    - [x] Standard Edit guard rendering is covered by focused tests.
    - [x] Sample-app and reference docs show the new built-in Update guard capability.

## Later

1. Consider whether create/update should gain equivalent save-time refusal handling when `form.save()` or `persist_single_object()` raises `ValidationError`.
2. Consider whether delete-success HTMX behavior should be aligned more closely with the create/update list-refresh path.
3. Consider whether standard-action policy hooks should eventually generalize beyond Delete and Update to View.
