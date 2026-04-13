# Single Delete UX Notes

## Problem Summary

PowerCRUD currently gives create/update forms and bulk operations explicit modal-safe error handling, but built-in single-object delete does not appear to have the same protection.

In the downstream case that prompted this plan, the model's `delete()` method validly raises `ValidationError` for protected rows. In a PowerCRUD HTMX modal flow, that currently bubbles to an HTTP 500, and the modal appears to sit there because HTMX does not receive a successful swap response.

## Current Implementation Notes

1. `neapolitan.CRUDView.process_deletion()` is a thin path: fetch object, call `delete()`, redirect.
2. `PowerCRUDAsyncMixin.process_deletion()` currently adds conflict checking, then delegates to the inherited delete path rather than handling model-level delete refusals itself.
3. `FormMixin.form_invalid()` already contains the modal-safe pattern we probably want to mirror for delete failures:
    - render a handled response
    - retarget to modal content
    - trigger modal redisplay
4. Bulk delete already treats per-row deletion errors as user-facing errors instead of hard 500s.
5. The built-in row action rendering supports `disabled_if` and `disabled_reason` for `extra_actions`, but not for the standard Delete action.

## Why This Looks Like A Real PowerCRUD Gap

The problem is not just that Neapolitan is minimal. PowerCRUD already chose to wrap create/update and bulk flows with stronger HTMX/modal UX guarantees. Single delete still behaves more like the raw Neapolitan path than like the rest of the PowerCRUD surface.

That leaves downstream projects with an inconsistent contract:

1. Form validation errors are handled cleanly.
2. Bulk delete/update errors are handled cleanly.
3. Single-object delete refusal errors can still produce an HTTP 500.

That inconsistency is the strongest argument for doing this upstream.

## First-Patch Shape

The smallest worthwhile enhancement is:

1. Catch expected delete refusal exceptions during single-object delete.
2. Normalize them into displayable messages.
3. Re-render `object_confirm_delete.html` with error state.
4. For HTMX modal requests:
    - return HTTP 200
    - retarget to the modal content target
    - trigger modal redisplay
5. For non-HTMX requests:
    - re-render the confirmation page with the same error content

This would stop the "modal hangs while server returns 500" behavior without forcing an API redesign.

For phase 1, the refusal contract is intentionally narrow:

1. Catch `ValidationError`.
2. Leave unexpected exception handling unchanged.
3. Do not redesign successful single-delete HTMX list refresh behavior in the same patch.

## Candidate Follow-On Enhancement

Add built-in delete guard hooks for standard row actions, likely something close to:

- `can_delete_object(obj, request) -> bool`
- `get_delete_disabled_reason(obj, request) -> str | None`

This would bring standard Delete closer to `extra_actions`, where row-level disablement is already supported.

This is explicitly deferred until after phase 1 refusal handling is solid.

## Important Constraints

1. Do not catch broad exceptions and present them all as user-facing validation problems.
2. Keep conflict handling in `PowerCRUDAsyncMixin` working as-is.
3. Make the HTMX retarget behavior explicit for error responses; the current delete form posts toward the list target for the success case.
4. Preserve filter/sort context cleanly on both success and error paths.
5. Keep the first patch backward compatible for projects that do not raise delete-time validation errors.

## Design Risks

1. The delete confirm template currently posts with list-redisplay semantics. A handled error response cannot rely on the normal list-target behavior; it needs explicit modal retargeting.
2. `ValidationError` payload shapes vary. The response helper should normalize strings, lists, and dict-like payloads into something stable for templates.
3. Guard hooks should not replace server-side protection. They are UX improvements, not the enforcement layer.

## Open Questions

1. What exact context contract should `object_confirm_delete.html` receive for handled delete errors?
2. Should the delete refusal helper live in the main sync path, the shared HTMX layer, or a dedicated delete helper on the CRUD stack?
3. When the later guard-hook phase happens, should it apply only to Delete, or should PowerCRUD define a more general standard-action policy surface for View/Edit/Delete?

## Decisions Locked

1. Phase 1 catches only `ValidationError` for single-object delete refusal handling.
2. Phase 1 does not broaden PowerCRUD into a general "user-correctable persistence exception" contract.
3. Phase 1 does not change the existing successful HTMX single-delete flow.
4. Built-in delete guard hooks are deferred to a later phase.

## Likely Code Areas

- `src/powercrud/mixins/async_mixin.py`
- `src/powercrud/mixins/htmx_mixin.py`
- `src/powercrud/templates/powercrud/daisyUI/object_confirm_delete.html`
- `src/powercrud/templatetags/powercrud.py`
- `src/tests/`

## Promotion Target Later

If this lands and proves stable, the durable documentation probably belongs in `docs/mkdocs/reference/` or an advanced guide covering PowerCRUD error-handling expectations for custom persistence and model-level refusal rules.
