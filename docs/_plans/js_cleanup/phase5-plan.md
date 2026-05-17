# Phase 5 Plan: Reduce Cross-Control Coupling

## Status

Phase 4 is complete. The runtime now has a stable ES-module public entry, a persistent manual-static smoke path, `window.initPowercrud(fragment)`, shared fragment teardown, centralised once-only listener registration, and repeated-init idempotency.

Phase 5 implementation slices are complete. The phase reduced direct coupling between list controls without changing the public entry path, template contracts, or user-visible behaviour.

## Objective

Phase 5 should make shared list state easier to reason about by replacing direct cross-control DOM/storage/state updates with narrow helper APIs.

The goal is not to move more code into files for its own sake. Phase 3 already split the large file into modules. Phase 5 should focus on ownership boundaries between behaviours that currently affect each other:

1. Current list-view state.
2. Saved-favourite selected and dirty state.
3. Visible-column state and reset-view coordination.
4. Bulk-selection state.
5. Inline-row state.

## Non-Goals And Caveats

1. Do not introduce a broad state-management abstraction unless the smaller helper approach clearly fails.
2. Do not create `powercrud_daisyui`, separate pack JavaScript, or `initPowercrudPack(fragment)` in Phase 5.
3. Do not change the public manual-loading contract:

    ```html
    <script type="module" src="{% static 'powercrud/js/powercrud.js' %}"></script>
    ```

4. Do not require manual users to load internal `runtime/*.js` modules directly.
5. Do not change the bundled/Vite manifest entry path.
6. Do not change stable `data-powercrud-*` or `data-inline-*` contracts unless a slice explicitly proves that a contract change is required and Michael approves it.
7. Keep `powercrud.js` as the stable public entry and compatibility bridge while internals continue to settle.
8. Do not touch `CHANGELOG.md`; Michael owns changelog updates.
9. Treat template-pack extraction as future work. Phase 5 may clarify future pack boundaries, but it should not implement them.

## Orchestration Approach

Proceed one slice at a time.

For each slice:

1. Brief one read-only sub-agent to plan that slice only.
2. The read-only sub-agent must read all JS cleanup plan and audit files, not just the active plan and notes.
3. The read-only sub-agent must not edit files.
4. The coordinator reviews the proposed slice plan before implementation starts.
5. Implement only the accepted slice.
6. Run focused tests for the touched behaviour area.
7. Run the broader lifecycle/browser slice when a change touches shared startup, lifecycle, module imports, or cross-feature state.
8. Update the relevant plan, notes, and handover docs.
9. Commit and push the completed slice before starting the next slice.
10. Stop and report back if a test failure exposes ambiguous intended behaviour or if the slice cannot stay narrow.

Do not run multiple implementation agents against the same runtime boundary in parallel. Read-only planning agents are useful for mapping a slice, but implementation should stay coordinated because these modules share state and tests.

## Required Reading For Every Phase 5 Planning Agent

Every read-only Phase 5 planning agent must read:

1. `AGENTS/AGENTS.md`
2. `AGENTS/AGENTS_planning.md`
3. `docs/_plans/js_cleanup/js_cleanup-plan.md`
4. `docs/_plans/js_cleanup/js_cleanup-notes.md`
5. `docs/_plans/js_cleanup/phase4-handover.md`
6. `docs/_plans/js_cleanup/phase5-plan.md`
7. `docs/_plans/js_cleanup/powercrud-js-behaviour-inventory.md`
8. `docs/_plans/js_cleanup/powercrud-js-contract-map.md`
9. `docs/_plans/js_cleanup/powercrud-js-listeners-and-dependencies.md`
10. `docs/_plans/js_cleanup/powercrud-js-test-coverage-map.md`
11. `docs/_plans/template_packs/template_packs-plan.md` and `docs/_plans/template_packs/template_packs-notes.md` for future-boundary context only.

The agent should then inspect the current runtime files relevant to that slice, not rely only on the older audit snapshot.

## Slice 5.0: Read-Only Coupling Map

Status: complete.

Objective:

Map the real post-Phase-4 cross-control coupling before making Phase 5 code changes.

Scope:

1. Identify where one runtime module directly reads or writes another control's DOM, storage, or module-owned state.
2. Produce a small table of:
    1. Source module or handler.
    2. Target state/control.
    3. Current coupling mechanism.
    4. Suggested helper owner.
    5. Risk and focused test file.
3. Confirm or adjust the Phase 5 slice order based on the live code.

Expected code areas to inspect:

1. `src/powercrud/static/powercrud/js/powercrud.js`
2. `src/powercrud/static/powercrud/js/runtime/list-view-state.js`
3. `src/powercrud/static/powercrud/js/runtime/filter-favourites.js`
4. `src/powercrud/static/powercrud/js/runtime/list-columns.js`
5. `src/powercrud/static/powercrud/js/runtime/bulk-actions.js`
6. `src/powercrud/static/powercrud/js/runtime/inline-edit.js`
7. `src/powercrud/static/powercrud/js/runtime/startup.js`

Exit criteria:

1. [x] No code edits.
2. [x] Coordinator has an updated slice-order recommendation.
3. [x] Any unexpected coupling is recorded in notes before implementation begins.

Result:

The read-only planning pass found no ambiguous behaviour that should stop implementation. The coordinator accepted the recommendation to start implementation with Slice 5.1, focused on `runtime/list-view-state.js`.

The main caveat is that reset-filter and reset-view semantics are related but not identical. Keep helper names explicit and preserve that distinction in tests. Also keep the lazy favourites/list-view bridge unless a later slice proves that direct ES imports can avoid circular dependency risk.

## Slice 5.1: Current List-View State Helpers

Status: complete.

Objective:

Make current list-view state the first explicit helper boundary because filters, page size, visible filters, visible columns, sorting, and favourites all depend on it.

Scope:

1. Formalise narrow helpers in or around `runtime/list-view-state.js` for reading and writing current list-view state.
2. Prefer named helpers over repeated ad hoc mixes of DOM reads, session-storage keys, URL query handling, and favourite-state collection.
3. Keep existing public globals and event behaviour stable.
4. Do not redesign saved favourites in this slice except where they call the new list-view helpers.

Likely tests:

1. `src/tests/playwright/test_filter_favourites.py`
2. `src/tests/playwright/test_list_options.py`
3. `src/tests/test_frontend_asset_packaging.py` with `--rebuild-assets` if static assets are rebuilt.

Exit criteria:

1. [x] Current view capture, persistence, reset, page-size changes, and favourite dirty-state comparisons still pass.
2. [x] Helper ownership is documented in notes if the public module boundary changes.

Result:

Slice 5.1 kept implementation scope inside `runtime/list-view-state.js` plus one delegation change in `powercrud.js`.

New or clarified list-view-state helpers:

1. `getSelectedFavouriteViewContext(root)` centralises the favourite toolbar/select/dirty-state context used by current-view remember/restore paths.
2. `getCurrentListViewQueryValues(root, options)` gives the current root query collection a list-view-specific name while preserving existing field exclusion semantics.
3. `clearCurrentListViewState(root, options)` centralises clearing current-view storage and optional-filter state, with optional filter-panel clearing for full reset-view.
4. `resetCurrentFilters(root)` owns the former reset-filter orchestration from `powercrud.js` while preserving the distinction between reset filters and full reset view.

The slice deliberately did not redesign favourite selected/dirty storage, move visible-column ownership, change bulk refresh, or touch HTMX lifecycle ordering.

Validation run:

1. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_filter_favourites.py src/tests/playwright/test_list_options.py"` passed, 19 tests.
2. `./runproj exec --command "./runtests --rebuild-assets src/tests/test_frontend_asset_packaging.py"` passed, 14 tests.

## Slice 5.2: Favourite Selected And Dirty State

Status: complete.

Objective:

Make favourite selected and dirty state explicit so other behaviours do not need to know how favourite UI controls, session keys, and comparison state are represented.

Scope:

1. Keep favourite-specific ownership in `runtime/filter-favourites.js`.
2. Add or refine narrow helpers for selected favourite state, dirty state, delete/update/apply transitions, and current-state comparison.
3. Avoid pulling generic list-view behaviour into the favourites module.
4. Keep the existing favourite storage keys, events, and DOM contracts stable.

Likely tests:

1. `src/tests/playwright/test_filter_favourites.py`
2. Manual-static smoke if the slice changes public init or module import behaviour.
3. Packaging test with `--rebuild-assets` if static assets are rebuilt.

Exit criteria:

1. [x] Favourite apply, update, delete, dirty-state, and reset-view interactions still pass.
2. [x] Other modules call favourites through named helpers instead of direct selected/dirty implementation details where practical.

Result:

Slice 5.2 kept the selected/dirty state implementation in `runtime/filter-favourites.js` and narrowed the list-view integration surface.

New favourite helper boundary:

1. `getSelectedFilterFavouriteViewContext(root, toolbar)` returns the selected favourite id and dirty state without exposing select/value/dirty-storage details to list-view state.
2. `clearSelectedFilterFavouriteSelection(root, toolbar)` owns clearing selected favourite browser state and related hidden fields.
3. `syncSelectedFilterFavouritePresentation(root)` gives list-view state an intent-level presentation sync helper.
4. Dirty storage helpers stay private inside `runtime/filter-favourites.js`.

`runtime/list-view-state.js` no longer receives direct `getFilterFavouritesSelect`, `getFavouriteSelectValue`, or `isSelectedFilterFavouriteDirty` callbacks. It still receives `getFilterFavouritesContainer` for storage-key scoping and visibility.

Validation run:

1. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_filter_favourites.py"` passed, 14 tests.
2. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_filter_favourites.py src/tests/playwright/test_list_options.py"` passed, 19 tests.
3. `./runproj exec --command "./runtests --rebuild-assets src/tests/test_frontend_asset_packaging.py"` passed, 14 tests.

## Slice 5.3: Visible Columns And Reset-View Coordination

Status: complete.

Objective:

Reduce coupling around visible-column state, reset-view semantics, and the overlap between list columns, favourites, and current list-view state.

Scope:

1. Keep list-column UI behaviour in `runtime/list-columns.js`.
2. Centralise helper access for visible-column draft state, persisted state, reset state, and current-state capture.
3. Keep reset-view behaviour consistent across filters, page size, visible columns, and favourite selected/dirty state.
4. Avoid moving DaisyUI presentation concerns out of list-column code unless they are already isolated by the slice.

Likely tests:

1. `src/tests/playwright/test_list_options.py`
2. Favourite visible-column and reset-view coverage in `src/tests/playwright/test_filter_favourites.py`
3. Packaging test with `--rebuild-assets` if static assets are rebuilt.

Exit criteria:

1. [x] Column chooser save/reset and close-without-save behaviours still pass.
2. [x] Reset view still clears stored filters, page size, visible columns, and selected favourite state.
3. [x] Hidden-column inline-edit compatibility remains intact.

Result:

Slice 5.3 moved visible-column state helpers into `runtime/list-columns.js` while leaving full reset-view orchestration in `runtime/list-view-state.js`.

New list-column helper boundary:

1. `getVisibleListColumnNames(root)` owns current visible-column collection from the chooser checkboxes.
2. `buildListColumnResetRequest(root, listUrl)` owns list-options reset form discovery, reset URL selection, CSRF extraction, and reset POST values.
3. `runtime/list-view-state.js` now asks list-columns for visible-column state and list-column reset request data instead of reading list-column checkboxes or building the reset POST directly.

The slice deliberately did not change chooser UI/draft behaviour, favourite comparison semantics, list-options server/template contracts, or reset-view trigger ownership.

Validation run:

1. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_list_options.py"` passed, 5 tests.
2. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_filter_favourites.py"` passed, 14 tests.
3. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_inline_editing.py::test_inline_edit_saves_after_hiding_non_trigger_column"` passed, 1 test.
4. `./runproj exec --command "./runtests --rebuild-assets src/tests/test_frontend_asset_packaging.py"` passed, 14 tests.

## Slice 5.4: Bulk Selection State

Status: complete.

Objective:

Isolate bulk-selection state and selection-aware UI updates so unrelated controls do not need to manipulate selection counters, checkboxes, or server persistence details directly.

Scope:

1. Keep bulk-selection ownership in `runtime/bulk-actions.js`.
2. Add or refine helpers around selected row IDs, checkbox hydration, select-all state, selection counters, selection-aware action visibility, and server selection persistence.
3. Preserve same-DOM repeated-init selection behaviour from Phase 4.
4. Keep bulk edit modal success handling stable.

Likely tests:

1. `src/tests/playwright/test_bulk_selection.py`
2. `src/tests/playwright/test_manual_static_assets.py`
3. Packaging test with `--rebuild-assets` if static assets are rebuilt.

Exit criteria:

1. [x] Row selection, shift selection, server persistence, selection-aware actions, and bulk-edit success clearing still pass.
2. [x] Repeated `window.initPowercrud(document)` does not lose same-DOM live selection.

Result:

Slice 5.4 kept implementation scope inside `runtime/bulk-actions.js` plus a small bootstrap call-site cleanup in `powercrud.js`.

New bulk-selection helper boundary:

1. `getBulkSelectionControls(root)` centralises lookup of select-all checkbox, row checkboxes, counter, and bulk action container.
2. `getSelectedBulkRowIds(root)` owns checked row id collection.
3. `setBulkRowsChecked(root, checked)` owns mass row checkbox mutation.
4. `syncBulkSelectionPresentation(root, explicitCount)` owns select-all checked/indeterminate state, optional counter/container updates, and selection-aware button sync.
5. `clearBulkSelection(root)` owns optimistic selection clearing, anchor reset, and presentation sync.
6. `persistBulkSelectionBatch(root, objectIds, action)` gives the server-persistence helper a bulk-selection-specific name.
7. `hydrateBulkSelectionState(root)` gives the rendered-selection hydration path an intent-level name while preserving the Phase 4 repeated-init guard.

The slice deliberately did not change listener order, template contracts, HTMX endpoints, swap targets, bulk edit refresh behaviour, or form spinner/button handling.

Validation run:

1. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_bulk_selection.py"` passed, 9 tests.
2. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_manual_static_assets.py"` passed, 1 test.
3. `./runproj exec --command "./runtests --rebuild-assets src/tests/test_frontend_asset_packaging.py"` passed, 14 tests.

## Slice 5.5: Inline Row State

Status: complete.

Objective:

Add narrow ownership around inline-edit row state after the less volatile shared list controls are settled.

Scope:

1. Keep inline-edit ownership in `runtime/inline-edit.js`.
2. Add or refine helpers around active row state, pending focus, locked widths, validation recovery, dependency refresh, and inline error popover state.
3. Preserve hidden-column compatibility and searchable-select behaviour.
4. Avoid broad inline-edit rewrites; this slice is high-risk because timing, focus, HTMX swaps, and validation recovery interact.

Likely tests:

1. `src/tests/playwright/test_inline_editing.py`
2. `src/tests/playwright/test_inline_dependencies.py`
3. `src/tests/playwright/test_list_options.py` if hidden-column compatibility is touched.
4. Packaging test with `--rebuild-assets` if static assets are rebuilt.

Exit criteria:

1. Inline save, cancel, validation recovery, focus, dependency refresh, and hidden-column compatibility still pass.
2. State ownership is clearer without changing user-facing inline-edit semantics.

Result:

Slice 5.5 kept implementation scope inside `runtime/inline-edit.js` and did not change public inline runtime method names, listener ordering, template `data-*` contracts, or inline dependency endpoint semantics.

New inline-row helper boundary:

1. `capturePendingInlineRowState(trigger, row, options)` centralises pending focus/highlight capture, table width locking, and row-width snapshots before an inline edit request.
2. `clearInlineLayoutState(table)` centralises pending and active column-width cleanup plus table-width unlocking.
3. `applyPendingInlineRowWidths(row)` owns applying pending or active row widths and promoting pending widths to active widths.
4. `activateInlineFormRow(row)` centralises the after-swap form-row activation path: active-row marking, row wiring, focus, error-popover display, width application, and orphan-popover cleanup.

The slice deliberately left `bootstrapInlineRow()` unchanged so initial page load does not gain new focus or scroll behaviour.

Validation run:

1. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_inline_editing.py src/tests/playwright/test_inline_dependencies.py"` passed, 10 tests.
2. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_list_options.py::test_book_list_column_chooser_saves_and_resets_columns src/tests/playwright/test_inline_editing.py::test_inline_edit_saves_after_hiding_non_trigger_column"` passed, 2 tests.
3. `./runproj exec --command "./runtests --rebuild-assets src/tests/test_frontend_asset_packaging.py"` passed, 14 tests.

Note: an initial parallel run of the targeted list/hidden-column checks collided with the active inline suite while both tried to create the shared test database. The same targeted command passed when rerun sequentially.

## Slice 5.6: Closeout

Status: complete.

Objective:

Close Phase 5 only after all accepted coupling-reduction slices are complete.

Scope:

1. Update `js_cleanup-plan.md` checkboxes.
2. Update `js_cleanup-notes.md` with the final helper boundaries and validation runs.
3. Update or replace the handover with the next-phase state.
4. Confirm whether Phase 6 should begin with a renewed template-pack boundary review.

Likely tests:

1. Focused tests for any final touched area.
2. Broad lifecycle/browser slice if Phase 5 touched multiple shared boundaries.

Exit criteria:

1. Phase 5 state is documented.
2. The branch is clean after a final commit and push.
3. The next agent can identify the next phase without reconstructing history from commits.

Result:

Slice 5.6 closed the phase in the top-level plan, notes, and a new active Phase 5 handover. Phase 4's handover remains historical; new agents should start from `phase5-handover.md`.

Validation run:

1. `git diff --check` passed.
2. No runtime tests were run because the slice was docs-only.

## Standard Verification Commands

Packaging check:

```bash
./runproj exec --command "./runtests --rebuild-assets src/tests/test_frontend_asset_packaging.py"
```

Broad lifecycle/browser slice:

```bash
./runproj exec --command "./runtests --playwright src/tests/playwright/test_manual_static_assets.py src/tests/playwright/test_bulk_selection.py src/tests/playwright/test_tooltips.py src/tests/playwright/test_filter_favourites.py src/tests/playwright/test_list_options.py src/tests/playwright/test_inline_editing.py src/tests/playwright/test_inline_dependencies.py src/tests/playwright/test_modal_crud.py src/tests/playwright/test_row_actions_menu.py"
```

Use narrower focused commands first. Only run the broad slice when the completed implementation warrants it.

## Handover

The active new-agent handover is [`phase5-handover.md`](phase5-handover.md). Phase 4's handover remains historical context only.
