# Briefing: Configurable List Toolbar Width and Alignment

## Purpose

Allow the list toolbar to use the full PowerCRUD list-container width independently of a compact table, and allow filters, columns, favourites, and page-size controls to sit immediately after the action buttons instead of being pushed to the far logical end.

Implement this after the configurable row-actions column work and the Book/PowerField Book parity change are on `main`. Create a fresh feature branch from the then-current `origin/main`.

## Confirmed Problem

With:

```python
column_width_policy = "semantic"
```

the DaisyUI table correctly shrinks to its content. PowerCRUD then sets the toolbar width to the rendered table width in `syncListToolbarWidth()`. This can wrap toolbar controls even when the surrounding list container has enough room.

The DaisyUI object-list template also applies `sm:ml-auto` to `data-powercrud-view-controls`, pushing filters, columns, favourites, and page size to the far right. Bootstrap uses equivalent `ms-md-auto` behaviour.

Relevant source locations are:

- `src/powercrud/templates/powercrud/packs/daisyui/object_list.html`
- `src/powercrud/contrib/bootstrap5/templates/powercrud/packs/bootstrap5/object_list.html`
- `src/powercrud/static/powercrud/js/runtime/current-template.js`
- `src/powercrud/static/powercrud/js/runtime/selectors.js`

The downstream workaround was:

```css
[data-powercrud-list-toolbar="true"] {
    width: 100% !important;
}

[data-powercrud-list-toolbar="true"] [data-powercrud-view-controls] {
    margin-left: 0 !important;
}
```

The first-party implementation should provide this behaviour semantically without downstream `!important` rules.

## Public API

Add two independent validated settings:

```python
list_toolbar_width_policy = "table"       # "table" or "container"
list_toolbar_alignment = "split"          # "split" or "adjacent"
```

Defaults preserve current behaviour:

- `table`: align the toolbar width to the rendered table width, capped by the available list container.
- `container`: allow the toolbar to use the full width of the PowerCRUD list container while leaving the table at its own resolved width.
- `split`: action controls remain at logical start and view controls move to logical end when space permits.
- `adjacent`: view controls immediately follow action controls in normal flex flow.

All combinations are valid:

| Width | Alignment | Result |
| --- | --- | --- |
| `table` | `split` | Current table-aligned layout with groups at opposing edges. |
| `table` | `adjacent` | Groups remain together inside the table-aligned width. |
| `container` | `split` | Full list width with groups at opposing logical edges. |
| `container` | `adjacent` | Full list width with view controls immediately after action controls. |

Start/end semantics must be logical for LTR and RTL. Do not preserve DaisyUI's physical `margin-left` as the public meaning of `split`.

## Runtime Behaviour

`syncListToolbarWidth()` currently:

- Synchronises table viewport height.
- Measures the table.
- Sizes the toolbar.
- Sizes the filter panel, pagination, and view help.
- Detects toolbar wrapping and sets `data-powercrud-toolbar-wrapped`.

Separate these responsibilities sufficiently that changing toolbar width does not accidentally change unrelated list chrome.

Required behaviour:

- Under `table`, preserve current toolbar measurement and maximum-width protection.
- Under `container`, clear stale table-derived inline toolbar widths and let pack styling make the toolbar `width: 100%` of the list container.
- Continue existing filter-panel, pagination, view-help, and table-height behaviour under both policies.
- Apply alignment before checking whether the groups genuinely wrapped.
- Preserve `data-powercrud-toolbar-wrapped`; wrapped view controls should remain full-width and logical-start aligned.
- Reapply correctly after initial load, resize, list-column changes, filtering, and HTMX list replacement.
- Add no new public JavaScript API.

Expose both resolved values through stable semantic attributes on the list toolbar. Keep the existing action-control, view-control, and wrapped markers. Framework utility classes are implementation details, not the portable contract.

## First-Party Packs and Portable Contract

DaisyUI and Bootstrap 5 must implement the same four combinations using pack-native responsive flex layout.

- `split` should use logical inline-start auto margin.
- `adjacent` should omit automatic separating margin.
- Natural wrapping must remain available on genuinely narrow screens.
- Prefer supported Tailwind/DaisyUI or Bootstrap utilities and narrowly scoped pack CSS over `!important` overrides.
- Do not make table width expand merely to accommodate the toolbar.

These settings create a portable obligation for independent template packs. Inspect the current template-pack contract version when work begins, increment it once, update the portable vocabulary and conformance fixtures, and make generated independent-pack declarations pin the resulting numeric version. Do not assume a version number from this briefing.

## Sample Application

Demonstrate the downstream-preferred combination on `AuthorCRUDView`:

```python
column_width_policy = "semantic"
list_toolbar_width_policy = "container"
list_toolbar_alignment = "adjacent"
```

Authors already reproduces the relevant mix of a semantic-width table, action controls, view controls, selection, inline editing, and many columns. Do not add sample-only CSS.

Leave at least one other sample on the default `table` plus `split` combination. Do not alter Book/PowerField Book parity.

If the all-actions dropdown feature later also uses Authors, retain both demonstrations: one controls the toolbar above the table and the other controls actions inside each row.

## Meaningful Test Coverage

Keep tests functional. Do not add exact pixel positions, spacing tolerances, whitespace assertions, visual snapshots, or exhaustive framework-class checks.

Server tests should prove:

- Defaults are `table` and `split`.
- Accepted and invalid values are validated correctly.
- Getters, compatibility shims, and list context expose resolved values.
- DaisyUI and Bootstrap emit equivalent semantic width/alignment markers.
- Adjacent mode does not apply automatic separation.
- Split mode follows logical direction semantics.
- HTMX-returned list content retains configured toolbar semantics.
- Existing filter, pagination, help, and table context remains intact.

Focused browser tests should prove:

- On Authors at a representative desktop width, container-plus-adjacent avoids an artificial toolbar wrap when the list container has sufficient room.
- Prefer the existing semantic `data-powercrud-toolbar-wrapped` state over coordinate tolerances.
- Filter, column, favourite, and page-size controls remain visible and usable.
- At a genuinely narrow viewport, controls wrap naturally and remain usable rather than overflowing or being clipped.
- HTMX replacement, list-column changes, and resize retain the configured layout.
- A default table-plus-split sample still behaves as before.
- Representative behaviour works in both first-party packs.

If one geometry assertion is necessary to prove decoupling, use a single threshold-free relative relationship, such as the toolbar being wider than a known compact table. Do not assert exact widths or coordinates.

## Documentation and Delivery

Update all usual stable documentation covering configuration, core CRUD setup, styling, the complete example, the sample app, template-pack selection/customisation/authoring/testing, and focused management-command overrides. Explain all four combinations and clarify that `container` means the PowerCRUD list container, not the browser viewport.

Do not edit `CHANGELOG.md` or package version metadata.

The runtime and bundled Bootstrap CSS will require tracked frontend assets to be rebuilt. Run focused tests during development and finish with:

```bash
./runproj exec --command "./runtests"
```

Commit semantically, push the feature branch, leave the worktree clean, and do not open a PR unless the user asks.
