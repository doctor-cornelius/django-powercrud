# Briefing: Put All Row Actions in a Dropdown

## Purpose

Add a third valid `extra_actions_mode` that places the native View, Edit, and Delete actions, together with configured `extra_actions`, inside one compact row menu.

Do not introduce another configuration parameter. The agreed API is:

```python
extra_actions_mode = "buttons"
extra_actions_mode = "dropdown"
extra_actions_mode = "all_dropdown"
```

The meanings are:

- `buttons`: native and extra actions are visible buttons. This remains the default.
- `dropdown`: native actions remain visible and only extra actions appear under **More**. This preserves current behaviour.
- `all_dropdown`: every resolved native and extra action appears in one compact menu.

Implement this after the configurable row-actions column work and the Book/PowerField Book parity change are on `main`. Create a fresh feature branch from the then-current `origin/main`.

## Agreed User Experience

For `all_dropdown`:

- Use an icon-only vertical-ellipsis trigger.
- Give the trigger the accessible name and tooltip **Actions**.
- Do not visibly label it **More**, because no primary actions remain outside it.
- Keep the table header label as **Actions**.
- Order menu entries as View, Edit, configured extra actions, then Delete.
- Put a separator before Delete when another action precedes it.
- Show the existing native icon and a visible text label for native menu entries.
- Preserve configured text and presentation for extra actions.
- Omit actions denied by permissions exactly as today.
- Preserve disabled states and their explanations.
- Preserve modal, HTMX, history, refresh-on-close, guard, and lazy extra-action behaviour.
- Reuse the existing detached body-level floating row-action menu. Add no new public JavaScript API.
- Keep inline Save and Cancel visible; they must never move into the dropdown.

The menu must work with start/end action-column positioning, sticky/non-sticky columns, selection enabled, inline editing, and HTMX row replacement.

## Current Code to Understand

- `src/powercrud/validators.py`
- `src/powercrud/mixins/config_mixin.py`
- `src/powercrud/mixins/table_mixin.py`
- `src/powercrud/templatetags/powercrud.py`, especially `_resolve_row_action_context()`
- `src/powercrud/mixins/row_action_state_mixin.py`
- `src/powercrud/templates/powercrud/packs/daisyui/partial/row_actions.html`
- `src/powercrud/contrib/bootstrap5/templates/powercrud/packs/bootstrap5/partial/row_actions.html`
- `src/powercrud/static/powercrud/js/runtime/current-template.js`

The server already resolves permissions, URLs, disabled states, modal/HTMX attributes, and lazy extra-action state. Recompose the resolved presentation; do not reimplement those decisions in templates or JavaScript.

Keep `row_actions.standard_actions` and `row_actions.extra_actions` available for compatibility. Add the minimum semantic payload needed to expose one consistently ordered all-actions menu to both packs. Prefer building that unified order once on the server rather than making each pack merge and reorder the lists independently.

Lazy state continues to apply only where currently supported for extra actions. Preserve original extra-action indices so lazy responses still map to the correct entries.

## First-Party Packs and Portable Contract

DaisyUI and Bootstrap 5 must honour identical public behaviour while using pack-native markup and styling. Preserve the existing semantic trigger, panel, ARIA, and action hooks used by the floating-menu runtime.

This is a new portable rendering obligation for independent template packs. Inspect the actual current template-pack contract version when implementation starts, increment it once, update the portable vocabulary and conformance fixtures, and make generated independent-pack declarations pin the resulting numeric version. Do not assume a particular version number from this briefing because another feature may land first.

## Sample Application

Use `AuthorCRUDView` to demonstrate:

```python
row_actions_column_position = "start"
row_actions_column_sticky = True
extra_actions_mode = "all_dropdown"
```

Authors already has several native and custom actions, selection, inline editing, and a start-sticky action column, so it clearly demonstrates the compact result.

Keep `BookCRUDView` on the existing `dropdown` mode. Books should continue demonstrating visible native actions plus an extras-only **More** menu. Do not break the agreed behavioural parity between Book and PowerField Book.

## Meaningful Test Coverage

Keep tests functional. Do not add pixel tolerances, whitespace assertions, visual snapshots, or exhaustive class checks.

Server tests should prove:

- The default remains `buttons`.
- All three values validate and invalid values fail clearly.
- Existing `buttons` and `dropdown` semantics remain unchanged.
- `all_dropdown` produces one semantic menu with permitted native and extra actions.
- Order is View, Edit, extras, separator when required, Delete.
- Missing permissions and disabled states are represented correctly.
- Lazy extra-action metadata and indices survive the combined menu.
- DaisyUI and Bootstrap honour the same mode and order.
- Inline Save and Cancel remain visible.
- HTMX replacement rows retain all-dropdown mode and action-column layout.

Focused browser tests should prove:

- The Author trigger is exposed to users as **Actions** and opens the floating menu.
- A native action and a configured extra action can each be activated.
- Delete remains last and retains its confirmation flow.
- Disabled actions cannot be activated and expose their explanation.
- The menu remains usable after horizontal scrolling with Authors' start-sticky column.
- Existing Book **More** behaviour still works in extras-only `dropdown` mode.
- Representative behaviour works in both first-party packs.

## Documentation and Delivery

Update all usual stable documentation that covers configuration, row actions, samples, styling, template packs, custom overrides, management commands, and pack acceptance testing. Explain the three modes precisely and document the icon trigger's accessible name.

Do not edit `CHANGELOG.md` or package version metadata.

Run focused tests during development and finish with:

```bash
./runproj exec --command "./runtests"
```

Commit semantically, push the feature branch, leave the worktree clean, and do not open a PR unless the user asks.
