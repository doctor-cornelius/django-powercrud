# Power Actions Plan

## Status

Planning started for `PowerAction` and `PowerButton` helpers over the existing `extra_actions` and `extra_buttons` dictionary APIs.

## Next

1. Confirm the plain constructor contract.
2. Add the primitive `extra_actions.disabled_state` hook.
3. Implement the smallest proof against the existing render path.

## Phase 1: Lock The Contract

1. [ ] Define `PowerAction` as a row-action declaration for `extra_actions`.
2. [ ] Define `PowerButton` as a toolbar-button declaration for `extra_buttons`.
3. [ ] Keep constructor parameters aligned with the existing primitive dictionary keys.
4. [ ] Decide the row-action and toolbar-button defaults.

## Phase 2: Add Primitive Disabled State

1. [ ] Add `disabled_state` to primitive `extra_actions`.
2. [ ] Preserve `disabled_if` and `disabled_reason` as legacy config.
3. [ ] Reject mixed disabled-state styles on one action.
4. [ ] Use the same `disabled_state` contract in `PowerAction`.

## Phase 3: Compile To Existing Dictionaries

1. [ ] Add `to_dict()` and `with_options(...)` to both declarations.
2. [ ] Normalize mixed lists of dictionaries and declarations.
3. [ ] Keep the renderers consuming dictionaries.
4. [ ] Reject invalid declaration shapes early.

## Phase 4: Prove The Reuse Case

1. [ ] Add tests for reusable modal row actions with `with_options(...)`.
2. [ ] Add tests for reusable selection modal toolbar buttons with `with_options(...)`.
3. [ ] Prove existing primitive dictionary tests still pass.
4. [ ] Add the helper example to the existing PowerField sample view.

## Phase 5: Document The Helper

1. [ ] Add concise guide documentation beside the current action/button docs.
2. [ ] Add reference documentation for constructor parameters and defaults.
3. [ ] Document that dictionaries remain the primitive API.
4. [ ] Promote only settled wording into `docs/mkdocs/`.
