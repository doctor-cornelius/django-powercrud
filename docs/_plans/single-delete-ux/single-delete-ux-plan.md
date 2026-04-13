# Single Delete UX Plan

## Status

Phase 1 scope is now locked around graceful handling of single-object delete `ValidationError` responses in HTMX/modal and non-HTMX flows, without changing the existing successful delete path.

## Next

1. Lock the concrete response contract for handled delete refusals in HTMX modal flows.
2. Lock the template/context shape for rendering delete-time errors.
3. Lock the test matrix before code changes so the first patch has a clear completion line.

## ✅ Phase A: Lock the First Shipping Scope

1. [ ] Confirm the minimum first-release outcome for refused single deletes.
    - [x] Catch expected user-facing delete refusals as `ValidationError`.
    - [x] Re-render the delete confirmation UI with a visible error instead of returning HTTP 500.
    - [x] Keep the modal open for HTMX/modal requests by retargeting back to modal content.
2. [ ] Confirm what is out of scope for the first patch.
    - [x] Do not silently swallow unexpected exceptions.
    - [x] Do not regress the successful single-delete flow.
    - [x] Do not require downstream projects to replace built-in delete with `extra_actions`.
3. [ ] Decide whether built-in delete guard hooks ship in phase 1 or phase 2.
    - [x] Option A: first patch only handles delete-time failures robustly.
    - [ ] Option B: first patch also adds row-level built-in delete disable hooks.

## ✅ Phase B: Make Single Delete Failure a First-Class Response Path

1. [ ] Introduce a shared single-delete failure handler in the PowerCRUD stack.
    - [ ] Single-object deletion routes model-level refusal errors into a handled response path.
    - [ ] HTMX requests receive a normal 200 response with renderable delete content.
    - [ ] Non-HTMX requests re-render the confirmation page with the error state.
2. [ ] Normalize delete refusal messages for rendering.
    - [ ] String, list, and dict `ValidationError` payloads are converted into displayable messages.
    - [ ] Error content is available to templates as a stable context contract.
3. [ ] Keep the current async conflict guard behavior intact.
    - [ ] Conflict responses continue to work as they do today.
    - [ ] Delete refusal handling composes with conflict checking rather than bypassing it.
4. [ ] Keep the successful delete behavior unchanged in phase 1.
    - [ ] The first patch does not redesign HTMX single-delete success semantics.
    - [ ] Any later alignment with create/update success-path refresh behavior is handled separately.

## ✅ Phase C: Fix the HTMX and Template Contract

1. [ ] Update the delete confirmation template to render handled errors clearly.
    - [ ] The modal includes an error alert region for delete-time failures.
    - [ ] Error rendering works for both modal and full-page flows.
2. [ ] Make the HTMX response target correct for handled delete failures.
    - [ ] Error responses retarget to the modal content container.
    - [ ] Modal error responses include the trigger needed to keep the modal visible.
3. [ ] Preserve list context through the delete flow.
    - [ ] Filter and sort state posted via `_powercrud_filter_*` is available on error redisplay.
    - [ ] The first patch preserves enough context for error redisplay without changing the current success-path contract.

## ✅ Phase D: Add Built-In Delete Guard Hooks If Included

1. [ ] Define the built-in delete policy hook contract.
    - [ ] Choose stable public hook names for "can delete" and "why not".
    - [ ] Ensure the contract accepts both `obj` and `request`.
2. [ ] Apply the contract to standard row actions.
    - [ ] Built-in Delete can render disabled before the modal opens.
    - [ ] Disabled rows can expose a reason tooltip consistent with existing PowerCRUD affordances.
3. [ ] Keep server-side refusal handling as the final safety net.
    - [ ] A disabled UI is not the only line of defense.
    - [ ] Unexpected race conditions still surface a safe handled response.

## ✅ Phase E: Verify, Document, and Land Safely

1. [ ] Cover the new behavior with focused tests.
    - [ ] HTMX modal delete refusal re-renders the delete confirmation with error content.
    - [ ] HTMX modal delete refusal retargets to the modal and keeps it open.
    - [ ] Non-HTMX delete refusal re-renders the page safely.
    - [ ] Successful delete behavior remains unchanged.
    - [ ] Guard-hook rendering is covered if that API ships in the same patch.
2. [ ] Document the new behavior at the right level.
    - [ ] Add notes for downstream integrators if model `delete()` may raise user-facing refusals.
    - [ ] Document any new built-in delete guard hooks if they are introduced.
3. [ ] Confirm release-readiness.
    - [ ] The first patch is backward compatible for projects that never raise delete-time validation errors.
    - [ ] The final behavior is predictable in both HTMX and non-HTMX flows.
