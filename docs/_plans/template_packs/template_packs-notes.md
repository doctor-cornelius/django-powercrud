# Template Packs Notes

## Source And Intent

These notes preserve the reasoning from [`docs/archive/blog/posts/20251120_template_packs.md`](../../archive/blog/posts/20251120_template_packs.md) as active planning context.

The objective is to support multiple frontend presentation layers such as DaisyUI, Tailwind-base, Bootstrap, and Bulma through a modular template-pack architecture. The architectural goal is to decouple PowerCRUD functional logic from visual framework details so projects can adopt a different frontend layer without rewriting PowerCRUD internals.

## Risk And Worth

This is a substantial refactor with real complexity and risk. The archived proposal frames the effort as worthwhile if PowerCRUD is intended to become:

1. A general-purpose open-source library with real extensibility value.
2. A credible showcase of engineering quality.
3. A package that supports plug-and-play customization.

The safe implementation sequence is:

```text
contract -> extract JS -> extract CSS -> refactor DaisyUI -> add tests -> only then build new packs
```

The important planning implication is that a second template pack should not be built first. First, PowerCRUD needs a contract and an extraction path that make pack boundaries real and testable.

## JavaScript Boundary Findings

The current JavaScript boundary decision record is [`docs/_plans/js_cleanup/phase6-boundary-findings.md`](../js_cleanup/phase6-boundary-findings.md).

The current internal JavaScript runtime architecture guide is [`src/powercrud/static/powercrud/js/README.md`](../../../src/powercrud/static/powercrud/js/README.md). Template-pack planning should reference that guide rather than duplicating the module map.

Hook creation is intentionally deferred until template-pack extraction or extraction-prep starts. Phase 6 identified likely hook points, but it did not create them because unused hooks would harden an internal API before real extraction pressure proves the shape.

When template-pack JavaScript work starts, the first slice should:

1. Read the internal JavaScript runtime README.
2. Pick one mixed boundary from the Phase 6 findings.
3. Add or confirm focused characterization coverage for that behaviour.
4. Introduce the smallest internal hook, neutral event, or pack initializer needed.
5. Move only adapter-owned behaviour behind that boundary.
6. Preserve the stable public entry and `window.initPowercrud(fragment)` contract.

## Reason For Template Packs

The current implementation embeds DaisyUI-specific HTML, CSS, and JavaScript directly inside core templates and runtime behavior. That coupling limits:

1. Switching UI frameworks.
2. Supporting different styling variants.
3. Enabling community-authored packs.
4. Controlling regression risk during visual changes.
5. Maintaining clean separation between UX details and core behavior.

A template-pack system should:

1. Standardize rendering through a stable contract of template names, partials, block definitions, and context variables.
2. Isolate pack-specific CSS and JavaScript.
3. Minimize maintenance surface area.
4. Offer future extensibility with lower risk.

## Framework Approach

The archived proposal breaks the work into four major concerns:

1. Define a clear contract for templates and JavaScript.
2. Split shared core behavior from per-template-pack behavior.
3. Turn the existing DaisyUI implementation into the first pack.
4. Add a clean way to select packs and test them.

## Existing DaisyUI Template Inventory

Core view templates identified by the archived proposal:

1. `powercrud/daisyUI/object_list.html`
    1. `pcrud_content`
    2. `bulk_selection_status`
    3. `filtered_results`
    4. `pagination`
2. `powercrud/daisyUI/object_form.html`
    1. `pcrud_content`
    2. `conflict_detected`
    3. `normal_content`
3. `powercrud/daisyUI/object_detail.html`
    1. `pcrud_content`
4. `powercrud/daisyUI/object_confirm_delete.html`
    1. `pcrud_content`
    2. `conflict_detected`
    3. `normal_content`

Shared partial templates identified by the archived proposal:

1. `powercrud/daisyUI/partial/list.html`
    1. `inline_row_display`
    2. `inline_row_form`
2. `powercrud/daisyUI/partial/detail.html`
    1. Detail layout partial with no internal `partialdef`.
3. `powercrud/daisyUI/partial/bulk_edit_errors.html`
    1. `bulk_edit_error`
    2. `bulk_edit_conflict`
4. `powercrud/daisyUI/crispy_partials.html`
    1. `load_tags`
    2. `crispy_form`
5. `powercrud/daisyUI/bulk_edit_form.html`
    1. `full_form`
    2. `async_queue_success`

## Framework Styles Direction

Current state from the archived proposal:

1. `HtmxMixin.get_framework_styles()` returns a dict keyed by framework name, currently only `daisyUI`.
2. DaisyUI style data includes:
    1. `base` button classes.
    2. `filter_attrs` for filter widgets.
    3. `actions` mapping action names to button classes.
    4. `extra_default` for extra buttons.
    5. `modal_attrs` with DaisyUI-specific modal-trigger behavior.
3. Current call sites include:
    1. `FilteringMixin.get_filterset()` for filter widget attributes.
    2. `action_links` and `extra_buttons` in `src/powercrud/templatetags/powercrud.py`.
    3. Existing tests that provide small `get_framework_styles()` stubs.

Problems with the current approach:

1. DaisyUI configuration lives in a core mixin.
2. One dict mixes filter widget attributes, button styling, and modal JavaScript behavior.
3. `modal_attrs` hardcodes DaisyUI `showModal()` behavior in Python.
4. The model assumes one `POWERCRUD_CSS_FRAMEWORK` rather than discoverable pack-local style modules.
5. There is no clear place for a pack such as `powercrud_bootstrap5` to ship its own style contract.

Refactoring direction:

1. Each template pack provides a Python module such as `powercrud_daisyui.styles`.
2. The module exports `PACK_STYLES`.
3. Core delegates style lookup to a helper such as `get_pack_styles(active_pack_name)`.
4. Style data should split concerns into:
    1. `filter_attrs`
    2. `buttons`
    3. `modal`
5. Modal metadata should use neutral attributes such as `data-pc-open-modal`, with pack JS translating that to DaisyUI, Bootstrap, or another framework.
6. Future widget-registry work can extend `PACK_STYLES` with a `widgets` section without changing the basic pack architecture.

## Template Structure Principles

1. Keep one orchestrator template per CRUD view type:
    1. `object_list.html`
    2. `object_form.html`
    3. `object_detail.html`
    4. `object_confirm_delete.html`
2. View-specific logic can stay as inline `partialdef` blocks inside the orchestrator.
3. Large, reusable, or natural override points should move to dedicated `partial/*.html` files.
4. Filter UI, table body, pagination, bulk actions, and inline row templates should be separable override points.
5. PowerCRUD does not own the full HTML base shell. The downstream project owns navigation, `<head>`, global assets, and `base_template_path`.
6. Template packs own the inner CRUD templates and partials.

## Template Placement Direction

For `object_list.html`:

1. `pcrud_content` stays inline as the orchestrator wrapper.
2. `bulk_selection_status` should become a thin wrapper around a dedicated `partial/bulk_actions.html`.
3. `filtered_results` stays inline as a thin wrapper around the list/table partial and pagination.
4. `pagination` should become a thin wrapper around `partial/pagination.html`.

For `object_form.html`:

1. `pcrud_content` stays inline.
2. `conflict_detected` stays inline.
3. `normal_content` stays inline.

For `object_detail.html`:

1. `pcrud_content` stays inline.

For `object_confirm_delete.html`:

1. `pcrud_content` stays inline.
2. `conflict_detected` stays inline.
3. `normal_content` stays inline.

For shared partials:

1. `partial/list.html` remains the natural override point for list rows.
2. `inline_row_display` stays in `partial/list.html`.
3. `inline_row_form` stays in `partial/list.html`.
4. `partial/detail.html` stays as a single simple partial.
5. `partial/bulk_edit_errors.html` keeps `bulk_edit_error` and `bulk_edit_conflict`.
6. `crispy_partials.html` keeps `load_tags` and `crispy_form`, though the long-term pack layout may move this under `partial/`.
7. `bulk_edit_form.html` keeps `full_form` and `async_queue_success` because it is itself the bulk-edit modal orchestrator.

## Context Variables To Preserve

List and table context:

1. `object_list`
2. `object_verbose_name`
3. `object_verbose_name_plural`
4. `headers`
5. `row.cells`
6. `row.actions`
7. `row.inline_url`
8. `row.inline_allowed`
9. `row.inline_blocked_reason`
10. `row.inline_blocked_label`

Pagination context:

1. `is_paginated`
2. `paginator`
3. `page_obj`
4. `page_size_options`
5. `default_page_size`

Selection and bulk-edit context:

1. `enable_bulk_edit`
2. `selected_ids`
3. `selected_count`
4. `all_selected`
5. `some_selected`
6. `list_view_url`
7. `selection_key_suffix`
8. `keyBase`

Filtering, sorting, and HTMX context:

1. `filterset`
2. `filter_params`
3. `table_max_col_width`
4. `table_max_height`
5. `table_pixel_height_other_page_elements`
6. `table_classes`
7. `request.GET`
8. `use_htmx`
9. `use_modal`
10. `original_target`
11. `htmx_target`
12. `header_title`

Forms, detail, delete, and bulk-edit context:

1. `form`
2. `use_crispy`
3. `update_view_url`
4. `create_view_url`
5. `object`
6. `conflict_detected`
7. `conflict_message`
8. `bulk_fields`
9. `field_info`
10. `model_name_plural`
11. `enable_bulk_delete`
12. `task_name`
13. `message`

## Post-Phase-6 Runtime Truth

JavaScript cleanup Phases 3 through 6 changed the starting point for template-pack work. The future template-pack split should start from the current module runtime, not from the older archived proposal.

Current truth:

1. `powercrud/js/powercrud.js` is the stable public runtime entry.
2. The entry is an ES module and imports internal runtime modules.
3. Manual users load only the stable entry with:

    ```html
    <script type="module" src="{% static 'powercrud/js/powercrud.js' %}"></script>
    ```

4. Bundled/Vite users continue through `config/static/js/main.js`, which imports the stable package entry.
5. `window.initPowercrud(fragment)` already exists.
6. `initPowercrudPack(fragment)` does not exist yet.
7. No `powercrud_daisyui`, separate pack JavaScript, loader helper, or new public static asset path exists yet.

Before pack JavaScript extraction starts:

1. Design the adapter hook or initializer orchestration for work that runs after `initPowercrud(fragment)`.
2. Add a neutral event or hook for row-action cloned-menu HTMX execution if that behaviour moves out of the current bundle.
3. Add modal, Tippy, and Tom Select safeguards before moving those presentation adapters.
4. Preserve the stable public entry and manual module-script loading contract.
5. Do not add public paths, pack loaders, or `powercrud_daisyui` without explicit extraction approval.

## JavaScript Contract

Core initializer:

1. `initPowercrud(fragment)` is exposed on `window` by core JS today.
2. `fragment` is either `document` or the root element of an HTMX swap.
3. It may be called multiple times.
4. It must be idempotent.
5. It must guard once-per-page wiring.
6. It must not reset filter values or user-entered state.
7. It owns core behavior tied to PowerCRUD `data-*` attributes.

Core responsibilities:

1. One-time global wiring on `document` and `document.body`.
2. HTMX event listeners.
3. Inline-edit helpers.
4. Bulk-selection helpers.
5. Form spinners.
6. Per-fragment wiring for PowerCRUD hooks.

Pack initializer:

A future pack initializer may be named `initPowercrudPack(fragment)`, but that API does not exist today. The hook shape should be decided from the Phase 6 boundary map before pack extraction starts.

If `initPowercrudPack(fragment)` is approved later:

1. It should be exposed on `window` by each pack JS file.
2. It should be optional.
3. It should be called with the same fragment as core initialization.
4. It should run after `initPowercrud`.
5. It should be responsible only for framework-specific behavior.
6. It must be safe to call multiple times.
7. It must avoid duplicate global listener registration.

Pack responsibilities may include:

1. Mapping neutral modal triggers to framework APIs.
2. Attaching framework-specific tooltips.
3. Showing framework-specific toasts or visual feedback.
4. Handling pack-only UX embellishments that do not change core event semantics.

Preferred wiring:

1. The project base loads the stable runtime entry once.
2. Bundled/Vite users load through `config/static/js/main.js`.
3. Manual users load the stable entry with the module script snippet above.
4. Full-page loads call `initPowercrud(document)`.
5. Core JS registers a single global `htmx:load` listener.
6. The listener calls `initPowercrud(event.detail.elt)`.
7. Future pack JS loading and hook orchestration remain deferred until extraction is approved.

Alternative wiring:

1. A future adapter hook may call pack/current-template initialization from core after `initPowercrud(fragment)`.
2. Fragments may explicitly call both initializers through `hx-on` only if the global listener proves too broad or too implicit.

## Events And Hooks

Core JS listens to HTMX events including:

1. `htmx:beforeRequest`
2. `htmx:afterRequest`
3. `htmx:afterSwap`
4. `htmx:beforeSwap`
5. `htmx:responseError`

PowerCRUD custom events include:

1. `bulkEditSuccess`
2. `bulkEditQueued`
3. `refreshTable`
4. `inline-row-locked`
5. `inline-row-forbidden`
6. `inline-row-error`
7. `bulkSelectionChanged`

Server `HX-Trigger` keys include:

1. `formError`
2. `modalFormSuccess`
3. `refreshList`
4. `refreshUrl`
5. `bulkEditSuccess`
6. `refreshTable`

Packs may listen to these events for visual behavior, but they must not change event semantics.

## Pack App Structure

Every pack is a Django app named by convention as `powercrud_<packname>`, for example:

1. `powercrud_daisyui`
2. `powercrud_bootstrap5`

Required orchestrator templates:

1. `powercrud_<packname>/templates/powercrud_<packname>/object_list.html`
2. `powercrud_<packname>/templates/powercrud_<packname>/object_form.html`
3. `powercrud_<packname>/templates/powercrud_<packname>/object_detail.html`
4. `powercrud_<packname>/templates/powercrud_<packname>/object_confirm_delete.html`

Required or expected shared partials:

1. `powercrud_<packname>/templates/powercrud_<packname>/partial/list.html`
2. `powercrud_<packname>/templates/powercrud_<packname>/partial/detail.html`
3. `powercrud_<packname>/templates/powercrud_<packname>/partial/bulk_edit_errors.html`
4. `powercrud_<packname>/templates/powercrud_<packname>/partial/bulk_edit_form.html`
5. `powercrud_<packname>/templates/powercrud_<packname>/partial/crispy_partials.html`

Static assets:

1. `powercrud_<packname>/static/powercrud_<packname>/js/...`
2. `powercrud_<packname>/static/powercrud_<packname>/css/...`

Style module:

1. `powercrud_<packname>/styles.py`
2. Exports `PACK_STYLES`.

The long-term plan is to migrate current DaisyUI templates from `powercrud/daisyUI/...` into a proper `powercrud_daisyui` app. Until then, core may need a compatibility path for the built-in pack.

## Pack Selection And Discovery

The proposed setting is:

```python
POWERCRUD_TEMPLATE_PACK = "daisyui"
```

Pack-name conventions:

1. Pack name: `daisyui`
2. App label or Python package: `powercrud_daisyui`
3. Template prefix: `powercrud_daisyui`
4. Styles module: `powercrud_daisyui.styles`

Internal helpers should include:

1. `get_active_pack()`
2. `get_pack_app_label()`
3. `get_pack_template_prefix()`
4. `get_pack_styles()`

If a configured pack cannot be imported or is not present in `INSTALLED_APPS`, core should raise a clear `ImproperlyConfigured` error.

## Official And Third-Party Packs

Official packs such as DaisyUI and Bootstrap 5 can live in this repo and ship in the same PyPI distribution as `powercrud`, while remaining separate Django apps.

Third-party packs can live in separate repos as pip-installable Django apps, as long as they provide the required templates, static assets, and `styles.py`.

The loader should not care whether a pack is official, co-located, or third-party. That distinction is governance, not core architecture.

## Compatibility And Future Widget Work

Short-term 0.x releases can tolerate breaking changes to pack loading if the changes are clearly documented.

When DaisyUI migrates into `powercrud_daisyui`, the implementation should:

1. Introduce the new pack loader.
2. Maintain compatibility for current `POWERCRUD_CSS_FRAMEWORK` usage where feasible.
3. Document `POWERCRUD_TEMPLATE_PACK` and required `INSTALLED_APPS` entries.

Future widget-registry work can extend `PACK_STYLES` with a `widgets` section. That should remain a related but separate project. The current template-pack plan should keep existing widget behavior stable and avoid introducing new hard-coded framework-specific classes into core templates or mixins.

## Template-Pack Validator

Core should provide a developer-facing validation API, likely named `validate_template_pack(pack_name="daisyui")`.

The validator should:

1. Verify that the pack app is importable.
2. Verify that the pack app is in `INSTALLED_APPS`.
3. Verify that required templates exist.
4. Optionally inspect templates for required `partialdef` names.
5. Verify that `styles.py` exists.
6. Verify that `PACK_STYLES` includes required top-level sections.

An optional management command can wrap the helper for project and CI use.

The full validator should be used in development and tests, not as a heavy runtime check. Runtime loading should still perform lightweight checks and raise clear configuration errors.
