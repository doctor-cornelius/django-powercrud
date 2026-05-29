# Power Actions Plan

## Status

Implementation is complete on `power-actions/plan`. The core helper declarations, primitive `disabled_state`, sample-app wiring, focused tests, broader non-Playwright tests, and first public docs pass are complete.

## Next

1. Review whether any additional public docs wording is needed before merge.

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

1. [x] Add concise guide documentation beside the current action/button docs.
2. [x] Add reference documentation for constructor parameters and defaults.
3. [x] Document that dictionaries remain the primitive API.
4. [x] Promote only settled wording into `docs/mkdocs/`.
