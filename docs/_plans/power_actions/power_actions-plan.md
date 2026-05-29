# Power Actions Plan

## Status

Implementation and docs are complete on `power-actions/plan`.

The branch includes `PowerAction`, `PowerButton`, primitive `disabled_state`, the PowerField `default_list=True` cleanup, sample app updates, dedicated public docs, focused tests, and the broader non-Playwright suite.

## Next

1. Review the branch before merge.

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

1. [x] Add a dedicated PowerAction/PowerButton guide page under `docs/mkdocs/guides/`.
2. [x] Add a dedicated PowerAction/PowerButton reference page under `docs/mkdocs/reference/`.
3. [x] Document that dictionaries remain the primitive API.
4. [x] Link the new pages from MkDocs navigation.
5. [x] Keep setup/core CRUD docs concise and link out to the dedicated guide/reference pages.

## Phase 6: Tighten PowerField Semantics

1. [x] Make `default_list=True` emit the underlying list allow-list entry as well as `default_list_fields`.
2. [x] For `property=True`, make `default_list=True` emit `properties` plus `default_list_fields`.
3. [x] Require list-cell metadata (`tooltip`, `column`, `link`) to have effective list visibility through `list=True`, `property=True`, or `default_list=True`.
4. [x] Reject obvious declaration clashes and bad shapes early.
5. [x] Keep doubtful implications explicit for now.

## Phase 7: Refresh The Sample App Demo

1. [x] Remove redundant `list=True` from default-list PowerField sample declarations.
2. [x] Keep property-backed list columns explicitly marked with `property=True`.
3. [x] Keep `uneditable_field` form-display only and out of the list.
4. [x] Preserve the PowerAction/PowerButton demo that mirrors `BookCRUDView`.

## Phase 8: Prove The Cleanup

1. [x] Add PowerField tests for default-list list/property emission.
2. [x] Add PowerField validation tests for bad boolean, dict, exclude, list-cell, and clash cases.
3. [x] Add sample equivalence tests for the simplified `PowerFieldBookCRUDView`.
4. [x] Keep list-options tests as the integration guard for default visible columns.
5. [x] Run the focused tests.
6. [x] Run the broader non-Playwright test suite.

## Phase 9: Finalise Branch

1. [x] Update `power_actions-notes.md` with the final settled behavior.
2. [x] Commit completed slices on `power-actions/plan`.
3. [x] Push the branch to `origin`.
