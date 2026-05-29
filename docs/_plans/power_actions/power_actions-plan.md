# Power Actions Plan

## Status

Planning started for `PowerAction` and `PowerButton` helpers over the existing `extra_actions` and `extra_buttons` dictionary APIs.

## Next

1. Confirm the plain constructor contract.
2. Decide the few default values that should differ between row actions and toolbar buttons.
3. Implement the smallest proof against the existing render path.

## Phase 1: Lock The Contract

1. [ ] Define `PowerAction` as a row-action declaration for `extra_actions`.
2. [ ] Define `PowerButton` as a toolbar-button declaration for `extra_buttons`.
3. [ ] Keep constructor parameters aligned with the existing primitive dictionary keys.
4. [ ] Decide the row-action and toolbar-button defaults.

## Phase 2: Compile To Existing Dictionaries

1. [ ] Add `to_dict()` and `with_options(...)` to both declarations.
2. [ ] Normalize mixed lists of dictionaries and declarations.
3. [ ] Keep the renderers consuming dictionaries.
4. [ ] Reject invalid declaration shapes early.

## Phase 3: Prove The Reuse Case

1. [ ] Add tests for reusable modal row actions with `with_options(...)`.
2. [ ] Add tests for reusable selection modal toolbar buttons with `with_options(...)`.
3. [ ] Prove existing primitive dictionary tests still pass.
4. [ ] Add one sample-app example that shows why the helper exists.

## Phase 4: Document The Helper

1. [ ] Add concise guide documentation beside the current action/button docs.
2. [ ] Add reference documentation for constructor parameters and defaults.
3. [ ] Document that dictionaries remain the primitive API.
4. [ ] Promote only settled wording into `docs/mkdocs/`.
