---
date: 2025-11-07
categories:
  - development
  - features
  - inline
---
# Implementing Inline Editing

This is the plan for adding inline row editing to PowerCRUD’s list views.
<!-- more -->

## Rationale

Inline editing lets operators tweak individual rows without breaking context or bouncing between detail pages. We already have most of the plumbing—field introspection, ModelForm generation, HTMX responses, and daisyUI styling. The missing piece is a cohesive row editor that reuses those assets, respects async conflict locks, and gives downstream projects a declarative way to configure the editable inline field set.

## Objectives

- Inline edits swap a display row for a form that uses the same ModelForm widgets as modal/detail edits.
- HTMX handles all swaps and submissions; no edit controls render when `use_htmx` resolves false.
- Row saves remain synchronous but honor async conflict locks so users never edit records in-flight elsewhere.
- Dependent-field refresh (e.g., change service type → refresh asset group choices) works via declarative metadata.
- Permission checks align with existing view policy, allowing custom per-row guards.
- UX remains accessible: clear focus states, inline error placement, obvious save/cancel cues.

## Constraints & Open Questions

- Inline editing is configured per CRUD view through `inline_edit_fields`; default remains read-only rows.
- All inline forms submit the full row. Autosave-per-field stays out of scope for v1 to avoid partial validation issues.
- Most dependency rules need declarative metadata; model introspection can help but cannot cover downstream business logic.
- Rows locked by the async conflict manager must never show inline edit controls. If a lock appears mid-edit the save call reverts back to read-only mode with a warning.
- Determine whether we expose new template partials or keep everything in `object_list.html` via HTMX targets.
- Downstream override points (templates, mixin methods) must stay stable so existing apps can customize safely.

## Design Highlights

### Inline Editing Gate

- `get_inline_editing()` resolves to True only when HTMX is in use and `inline_edit_fields` is configured.
- Views restrict scope with `inline_edit_fields` and can use a callable `inline_edit_allowed(obj, request)` for per-row decisions.
- Permission hooks (`inline_edit_requires_perm`, `inline_edit_allowed`) run for both rendering and submission so unauthorized rows never expose a form.

### Row Lifecycle & UX

1. Users enter inline edit mode by clicking any editable cell. Editable cells use hover/focus styles and a pointer/text cursor so it feels deliberate rather than accidental.
2. Clicking an editable cell swaps the row for a `<form>` built from the standard ModelForm and daisyUI helpers. Only one row can be in edit mode at a time; trying to edit another row first prompts the user to save or cancel the active row.
3. Save + Cancel buttons replace the normal action column (where Edit/Delete previously lived) and stay visible until the row returns to read-only mode. Saving requires clicking the button (or a keyboard shortcut); clicking elsewhere does not auto-save.
4. On Save, HTMX posts back to the same endpoint; success swaps in the updated display fragment, failure swaps the form with inline errors. `Hx-Trigger` events expose `inline-row-saved` / `inline-row-error` for optional downstream listeners (e.g., flashing a message).
5. Cancel simply swaps back the read-only row partial and discards pending changes.
6. Keyboard behavior mirrors the visual controls: Tab moves between fields, Enter/Space activates the focused control, and pressing Escape cancels the inline edit immediately.

### Dependent Field Pattern

- Views declare dependency business rules through `field_queryset_dependencies`, and inline wiring is derived automatically from that shared config.
- Templates emit `hx-trigger="change"` on parent fields and target a small placeholder around the dependent widget.
- Default dependency endpoint reuses FormMixin to rebuild just the child field with a filtered queryset so validation stays consistent.

### Conflict & Permission Enforcement

- Before rendering edit controls, we reuse `AsyncMixin` helpers to detect locks; locked rows stay read-only with a plain warning (no edit button shown).
- Inline save endpoint rechecks locks; if detected, it responds with an HTMX swap showing a conflict notice and reverts to read-only mode.
- Permission hooks run in both render and submit paths so unauthorized rows never expose a form.

## Plan

1. ✅ **Confirm scope & UX**
    - ✅ Align on row-level saves, HTMX-only requirement, and dependency metadata contract.
    - ✅ Document that async conflict locks must hide inline editors rather than relying on failure paths.
2. ✅ **API surface & mixin updates**
    - ✅ Add new CoreMixin attributes: `inline_edit_fields`, `inline_edit_requires_perm`, and `inline_edit_allowed`.
    - ✅ Update `PowerCRUDMixinValidator` so the new settings are type-checked and defaulted.
    - ✅ Implement helper methods (`get_inline_editing()`, `get_inline_edit_fields()`, `get_inline_dependencies()`, `can_inline_edit(obj, request)`) so downstream views can override behavior cleanly.
    - ✅ Expose FormMixin hooks to build inline forms via the existing `get_form_class()`/`get_form_kwargs()` pipeline.
    - ✅ Provide TableMixin (or new inline mixin) helpers that add inline config to the template context (editable cells, dependency metadata, row targets).
    - ✅ Add URL/HTMX helpers (possibly via UrlMixin/HtmxMixin) to resolve the inline row endpoint and per-row HTMX targets.
    - ✅ Integrate permission checks using `inline_edit_requires_perm` and custom callables before rendering inline controls or accepting saves.
    - ✅ Surface async conflict status via a helper (e.g., `is_row_locked(obj)`) so templates and save views can share the same logic.
3. ✅ **Template & HTMX wiring**
    - ✅ Annotate row containers with predictable IDs so HTMX can target individual rows (`pc-row-{{ pk }}`) and swap entire rows when needed.
    - ✅ In `partial/list.html`, mark cells corresponding to `inline_edit.fields` with hover/focus styles, keyboard focusability, and `hx-get` to fetch the inline form.
    - ✅ Replace the action column with Save/Cancel buttons while a row is in edit mode; ensure only one row can be active.
    - ✅ Wire editable cells with `hx-trigger` for click + Enter/Space; add hover cues and keyboard-friendly focus styles.
    - ✅ Add Escape handling so `keyup[Escape]` cancels the inline form and restores the display row (scaffolded in the inline form partial).
    - ✅ Create the inline form partial so HTMX swaps stay scoped.
    - ✅ Emit HTMX attributes for dependent fields (`hx-trigger="change"`, target placeholders) based on `inline_edit.dependencies`.
    - ✅ Ensure keyboard shortcuts (Tab, Enter, Escape) map cleanly to inline edit behavior with appropriate ARIA/focus handling.
4. ✅ **Dependency endpoint & HTMX wiring**
    - ✅ Add inline row HTMX endpoints: GET returns the inline form snippet for a row, POST validates/saves and returns either the refreshed display row or the form with errors (plus HTMX triggers).
    - ✅ Register URL patterns (`…-inline-row`, `…-inline-dependency`) via `UrlMixin` so every CRUD view automatically exposes the endpoints.
    - ✅ Implement the dependency refresh endpoint that rebuilds just the child field widget using the standard form pipeline and returns that fragment.
    - ✅ Wire the inline form partial with `hx-post`/`hx-get` attributes for Save/Cancel and `hx-trigger="keyup[Escape]"`; add a tiny JS helper to enforce one active row at a time and fire dependency refresh requests.
5. ☐ **Conflict & permission handling**
    - ✅ Surface lock/permission metadata in the list payload so templates suppress inline triggers and show “read-only” cues when `is_inline_row_locked` or permission hooks fail.
    - ✅ Re-check locks/permissions inside the inline-row GET/POST endpoints and return HTMX-friendly 4xx responses that swap the row back plus emit `inline-row-locked` / `inline-row-forbidden` triggers.
    - ✅ Thread async-lock details (owner, timestamp) into those responses so the UI can explain why editing stopped, and add a helper to re-fetch the display fragment when conflicts clear.
    - ✅ Extend the inline JS to listen for the new triggers, clear the active-row state, and show toast/banner feedback; ensure dependency listeners are removed when a row falls back to read-only.
6. ✅ **Sample app inline coverage**
    - ✅ Enable inline editing on `BookCRUDView` with a curated field list plus author→genre dependency metadata so the sample can demonstrate the feature.
    - ✅ Confirm the sample DaisyUI template inherits the shared inline partials/JS so no extra wiring is required.
    - ✅ Wire dependency metadata so changing `author` inline refreshes the `genres` widget via the dependency endpoint.
    - ☐ Give the sample data model a real dependency (e.g., `Author.available_genres`) so the inline dropdown filter is verifiably scoped by the parent field.
6.1 ☐ **Inline UX polish**
    - ✅ Surface inline validation failures directly in the row so users see field + non-field errors without relying on console logs; the inline-row-error trigger now focuses the row while the JS banner echoes the same message.
    - ✅ Tidy lock presentation: suppress the giant lock badges, grey out Edit/Delete/lock-sensitive actions when a row is locked, and move the “Locked by…” copy into the tooltip so only affected rows show the notice.
    - ✅ Add visual progress to saves: toggle a spinner + disabled state on both the inline Save button and the object form Save button while HTMX posts, so the 2‑second sample `Book.save()` delay has explicit feedback without layout jumps.
7. ☐ **Tests**
    - **Backend / pytest**
        - ✅ Stand up lightweight InlineEditingMixin test views/forms so we can hit the HTMX inline-row endpoint for: GET form render, POST success swap (emits `inline-row-saved`), validation errors (422 + `inline-row-error`), and guard fallbacks (locked + forbidden states returning display rows). 
        - ✅ Cover `_dispatch_inline_dependency` happy path and failure modes (missing `field`, unknown field, pk lookups) to prove dependent widgets are rebuilt correctly without touching any bootstrap5 templates.
        - ✅ Exercise helper APIs (`get_inline_edit_fields`, `get_inline_field_dependencies`, `_get_inline_lock_metadata`, `get_inline_context`) to ensure inline_config fed into daisyUI templates includes resolved row IDs, dependency URLs, and lock metadata even when async managers throw.
        - ✅ Render the daisyUI `object_list` partial with stub data to assert `data-inline-*` attributes, Save/Cancel button states, and dependency placeholders only appear when `inline_edit_fields` resolves a non-empty editable field set.
        - ✅ Add a regression test that seeds a simulated async lock (via the sample async manager or a stub cache) and verifies list payload + inline endpoint both respect the lock.
    - **Playwright (daisyUI only)**
        - ✅ Happy-path inline edit on a sample Book row: open inline mode, change a field, save, wait for `inline-row-saved`, and assert the row text updates while only one row stays active.
        - ✅ Validation failure flow: submit an empty required field inline, expect inline error text + form persistence + guard reset after fixing the data.
        - ✅ Guard focus behavior: start editing row A, attempt row B, assert focus returns to A; cancel/refetch list (pagination/filter) and confirm a new row can be edited immediately.
    - **Order of work**
        1. Backend: build inline test doubles + pytest coverage listed above, keeping focus on daisyUI paths and excluding any bootstrap5 templates.
        2. Template assertions: render the object_list/inline partials to lock in the expected `data-inline-*` structure before UI automation relies on them.
        3. Playwright: extend the existing suite with the inline scenarios (happy path, validation, guard) and reuse current fixtures so we can run `pytest -m playwright`.
        4. Verification: run `pytest` (non-Playwright) then `pytest -m playwright`, and capture coverage deltas against `coverage.xml` for the inline mixin + templates.
8. ☐ **Docs**
    - ✅ Add cookbook-style docs showing configuration snippets, dependency examples, lock states, and the new inline JS hooks.
    - ✅ Call out that inline forms reuse the view’s `form_class` (or generated form), so any custom fields/widgets/omissions carry over; inline field lists must stay aligned with whatever that form actually exposes.
9. ☐ **Future UX polish**
    - ☐ Explore lighter-weight discoverability (e.g., helper tooltip, iconography, first-run banner) so users realize cells are editable without guesswork.
    - ✅ **URGENT** Fix the horrible jumping around of the whole table that happens when you click to open a row for inline editing. 

> 📝 **Sample dependency follow-up:** Right now `BookCRUDView`’s author→genre dependency is purely declarative—the models never limit genres per author. We still need a lightweight relationship (like an `Author.available_genres` M2M) plus form/queryset filtering so the inline widget visibly narrows its options when the parent field changes. Once that exists, the inline demo becomes self-validating and doubles as coverage for the dependency refresh endpoint.
