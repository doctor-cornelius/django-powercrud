# Power Actions Plan

## Status

Core `PowerAction`, `PowerButton`, and primitive `disabled_state` implementation is complete on `power-actions/plan`.

The plan is not fully complete. Public docs need a clearer dedicated PowerAction/PowerButton guide and reference, and the agreed PowerField cleanup still needs implementation.

## Next

1. Tighten PowerField `default_list=True` semantics and validation.
2. Simplify the PowerField sample app declarations.
3. Add dedicated PowerAction/PowerButton docs.
4. Run focused and full test suites.
5. Commit and push each completed slice on `power-actions/plan`.

## Phase 1: Lock The Contract

1. [x] Define `PowerAction` as a row-action declaration for `extra_actions`.
2. [x] Define `PowerButton` as a toolbar-button declaration for `extra_buttons`.
3. [x] Keep constructor parameters aligned with the existing primitive dictionary keys.
4. [x] Decide the row-action and toolbar-button defaults.

## Phase 2: Add Primitive Disabled State

1. [x] Add `disabled_state` to primitive `extra_actions`.
2. [x] Preserve `disabled_if` and `disabled_reason` as legacy config.
3. [x] Reject mixed disabled-state styles on one action.
4. [x] Use the same `disabled_state` contract in `PowerAction`.

## Phase 3: Compile To Existing Dictionaries

1. [x] Add `to_dict()` and `with_options(...)` to both declarations.
2. [x] Normalize mixed lists of dictionaries and declarations.
3. [x] Keep the renderers consuming dictionaries.
4. [x] Reject invalid declaration shapes early.

## Phase 4: Prove The Reuse Case

1. [x] Add tests for reusable modal row actions with `with_options(...)`.
2. [x] Add tests for reusable selection modal toolbar buttons with `with_options(...)`.
3. [x] Prove existing primitive dictionary tests still pass.
4. [x] Add the helper example to the existing PowerField sample view.

## Phase 5: Document The Helper

1. [ ] Add a dedicated PowerAction/PowerButton guide page under `docs/mkdocs/guides/`.
2. [ ] Add a dedicated PowerAction/PowerButton reference page under `docs/mkdocs/reference/`.
3. [x] Document that dictionaries remain the primitive API.
4. [ ] Link the new pages from MkDocs navigation.
5. [ ] Keep setup/core CRUD docs concise and link out to the dedicated guide/reference pages.

## Phase 6: Tighten PowerField Semantics

1. [ ] Make `default_list=True` emit the underlying list allow-list entry as well as `default_list_fields`.
2. [ ] For `property=True`, make `default_list=True` emit `properties` plus `default_list_fields`.
3. [ ] Require list-cell metadata (`tooltip`, `column`, `link`) to have effective list visibility through `list=True`, `property=True`, or `default_list=True`.
4. [ ] Reject obvious declaration clashes and bad shapes early.
5. [ ] Keep doubtful implications explicit for now.

## Phase 7: Refresh The Sample App Demo

1. [ ] Remove redundant `list=True` from default-list PowerField sample declarations.
2. [ ] Keep property-backed list columns explicitly marked with `property=True`.
3. [ ] Keep `uneditable_field` form-display only and out of the list.
4. [ ] Preserve the PowerAction/PowerButton demo that mirrors `BookCRUDView`.

## Phase 8: Prove The Cleanup

1. [ ] Add PowerField tests for default-list list/property emission.
2. [ ] Add PowerField validation tests for bad boolean, dict, exclude, list-cell, and clash cases.
3. [ ] Add sample equivalence tests for the simplified `PowerFieldBookCRUDView`.
4. [ ] Keep list-options tests as the integration guard for default visible columns.
5. [ ] Run the focused tests.
6. [ ] Run the broader non-Playwright test suite.

## Phase 9: Finalise Branch

1. [ ] Update `power_actions-notes.md` with the final settled behavior.
2. [ ] Commit completed slices on `power-actions/plan`.
3. [ ] Push the branch to `origin`.
