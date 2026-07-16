# Phase 7 Bootstrap Styling API Audit

## Status

The read-only Phase 7.7 inventory and Phase 7.8 decision review are complete. Bootstrap supports the selected-pack, framework-style-map, template override, normal action, native/crispy form, row-action, link, and semantic lifecycle contracts. The accepted decisions below authorize only the named Phase 7.8 presentation batches; they do not reopen 7.1--7.7 or shared-core semantics.

## Next

Implement the accepted decisions only through the named Phase 7.8.4--7.8.7 component batches, starting with the pack-owned extra-button boundary.

## Phase 7.7.1: Record Supported Styling Contracts

1. [x] Confirm startup selection through `POWERCRUD_TEMPLATE_PACK="powercrud.contrib.bootstrap5:template_pack"`, the `bootstrap5` adapter key, and Bootstrap-owned assets/templates.
2. [x] Confirm `get_framework_styles()` supports the Bootstrap map: `base`, `filter_attrs`, `actions`, `action_group_item`, `extra_default`, `list_cell_link_class`, and `modal_attrs`.
3. [x] Confirm native and `crispy-bootstrap5` form rendering, framework class appending, normal action/button classes, row-action menus, links, focused component candidates, and complete template overrides retain their public contracts.
4. [x] Confirm semantic IDs and `data-powercrud-*`/`data-inline-*` hooks remain behaviour contracts and are retained by Bootstrap templates; they are not a user styling API.
5. [x] Confirm raw custom class values, bespoke crispy layouts, and custom style maps remain supported only when consumers supply Bootstrap-compatible values; DaisyUI values are not auto-translated.

## Phase 7.7.2: Record Explicit Limits And Decisions

1. [x] Record that `extra_buttons_mode="dropdown"` is presently DaisyUI-only: the shared helper emits DaisyUI `<details>` markup and classes even under Bootstrap selection.
2. [x] Record that disabled extra-button initial markup retains a Daisy `btn-disabled` class and legacy Tippy attribute; the Bootstrap adapter supports dynamic disabled/tooltips, but the initial presentation bridge is incomplete.
3. [x] Record that `modal_classes` and `modal_body_classes` are intentionally ignored by the Bootstrap shell; `modal_box_classes` and `bulk_modal_box_classes` are applied only when they contain safe Bootstrap modal classes.
4. [x] Record that Bootstrap does not currently consume DaisyUI-oriented table geometry, inline highlight/palette, or view-help colour/min-width controls.
5. [x] Record that copied `powercrud/daisyUI/...` overrides and the current `pcrud_mktemplate` dialog guidance do not transfer unchanged to Bootstrap.
6. [x] Ratify the Phase 7.8 recommendation that `extra_buttons_mode="dropdown"` gain a pack-owned presentation boundary rather than remain DaisyUI-only.
7. [x] Ratify the Phase 7.8 recommendation that modal body/class, table geometry, inline highlight, and view-help controls remain explicitly Bootstrap-unsupported while Bootstrap supplies suitable pack-owned defaults.
8. [x] Ratify the split Phase 7.8 recommendation to defer pack-aware `pcrud_mktemplate` guidance but move initial disabled-button presentation into the pack-owned extra-button boundary.

## Phase 7.7.3: Preserve Delivery Boundaries

1. [x] Keep Bootstrap selection process-startup-only; `POWERCRUD_CSS_FRAMEWORK="bootstrap5"` alone remains intentionally insufficient because it cannot install the pack, templates, or assets.
2. [x] Keep Bootstrap component lifecycle private behind the stable PowerCRUD runtime; do not add a public browser registry or framework switcher.
3. [x] Defer all accepted presentation refinements to bounded Phase 7.8 slices after Michael's review.
