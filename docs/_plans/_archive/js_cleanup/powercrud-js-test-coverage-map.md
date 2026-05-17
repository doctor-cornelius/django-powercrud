# PowerCRUD JavaScript Browser-Test Coverage Map

## Purpose

This map records current Playwright coverage by JavaScript behaviour area. It started as a static Phase 1 audit and was updated after the Phase 2 safety-rail tests were added and run.

## Coverage By Area

| Behaviour area | Existing coverage | Gaps or audit risks |
| --- | --- | --- |
| HTMX lifecycle and partial swaps | Covered indirectly through favourites, pagination, filters, bulk edit, inline edit, and tooltip reinitialisation. Strongest files: `test_filter_favourites.py`, `test_bulk_selection.py`, `test_tooltips.py`, `test_inline_editing.py`. Phase 2 adds repeated searchable-select/tooltip initialisation before and after an HTMX refresh. | No focused test for idempotent global listener registration itself. |
| Filter panel open/closed state | Tests open the panel in favourites, tooltip, and list-option flows. Tooltip tests check initial filter toggle tooltip state. | Persistence of panel open/closed state across reload, back/forward cache, or shell HTMX return is not directly asserted. |
| Optional filters and reset filters | Favourite application replacing visible filters is covered. Reset filters marking selected favourite dirty is covered. Searchable filter behaviour is covered in bulk-selection tests. | Add/remove optional-filter UI is only partly covered. Removing optional filters and reset behaviour without a selected favourite are likely gaps. |
| Filter value refresh | Text and choice filter changes after favourite apply are covered. Searchable single and multiselect filters are covered. | Debounce/cancel semantics and empty-field submit cleanup are not directly isolated. |
| Page size | Page-size query rendering with favourites enabled is covered. Phase 2 covers page-size changes marking the selected favourite dirty. | Plain current-view restore for page size independent of favourites remains under-covered. |
| Current view state | Visible-column persistence and favourite restoration of visible columns are covered. Page-size query rendering is covered. Phase 2 covers reset-view clearing filters, page size, visible columns, and selected favourite state. | Plain current-view restore for filters/page size/columns independent of favourites appears under-covered. |
| Saved favourites | Apply, selected indicator, dirty state after reset, update reapply, inline save, restored visible columns, direct return, and sample-shell HTMX return are covered in `test_filter_favourites.py`. Phase 2 adds page-size dirty state, explicit reset view, and delete clearing selected/dirty browser state. | Disabled/no-login and error responses remain under-covered. |
| List-column chooser | Save/reset/reload, last-column guard, toolbar fit, wrapped toolbar alignment, chooser placement, and draft reset on close are covered in `test_list_options.py`. | Keyboard-only chooser paths remain limited. |
| Toolbar layout and dropdown placement | Toolbar/view-control layout and column chooser placement are covered in `test_list_options.py`. Phase 2 opens the top-action dropdown for the per-trigger modal class test. | Top action dropdown layout and disabled selection-aware states remain under-covered. |
| Row action menus | Floating row action menu visibility for top and bottom rows is covered in `test_row_actions_menu.py`. Phase 2 covers action execution from the cloned floating panel into a modal. | Keyboard path and disabled action path are not directly covered. |
| Bulk selection | Toggle/clear, shift-click select range, and shift-click clear range are covered in `test_bulk_selection.py`. | Select-all, stale HTMX selection-request suppression, queued/error cleanup, and server request race handling are not directly covered. |
| Bulk edit | Bulk edit preserving active filters and searchable-select bulk edit are covered. Phase 2 asserts successful bulk edit closes the modal and clears selected counter/container/checkbox state. | Bulk delete confirmation, queued event handling, and response-error cleanup are not directly covered. |
| Inline edit | Happy path, validation recovery, cancel clearing popovers, active-row guard, searchable select update, dropdown focus, action-column fit, display truncation, and save after hiding a non-trigger visible column are covered in `test_inline_editing.py`. | Error handling while columns are hidden remains under-covered. |
| Inline dependencies | Dependent genre options refreshing after author change is covered in `test_inline_dependencies.py`. | Error handling and chained dependencies are not directly covered. |
| Modals | Create-via-modal and Tom Select in modal are covered in `test_modal_crud.py`; Phase 2 covers per-trigger modal-box classes, default class restoration, bulk modal close after success, and row-action modal launch path. | Duplicate modal cleanup is not directly covered. |
| Tooltips | Toolbar Tippy instances, overflow tooltip reinit after HTMX refresh, semantic-cell tooltip reinit, multiline semantic tooltip rendering, and repeated tooltip initialisation before/after HTMX refresh are covered in `test_tooltips.py`. | Tooltip destroy/recreate during teardown remains indirect. |
| Searchable selects / Tom Select | Exercised in filters, inline edit, bulk edit, and modal CRUD. Phase 2 covers repeated searchable-select initialisation before and after HTMX refresh. | Missing-dependency warnings and native-select restore are not directly covered. |
| DaisyUI visual classes and spinners | Some disabled/hidden/loading outcomes are indirectly covered through visible UI assertions. Phase 2 directly asserts DaisyUI modal class application for top actions and row actions. | Form/button spinner markup and many visual class toggles are not directly asserted. |

## Coverage Files

- `src/tests/playwright/test_filter_favourites.py`: saved favourites, filter refresh after favourite apply, optional-filter replacement, favourite dirty state, visible columns in favourites, shell HTMX return, page-size dirty state, reset view, favourite delete state clearing.
- `src/tests/playwright/test_list_options.py`: list-column chooser, last-column guard, draft reset on close, toolbar sizing, filter panel alignment, chooser placement.
- `src/tests/playwright/test_inline_editing.py`: inline edit lifecycle, validation, guard, searchable selects, hidden visible columns, action-column layout, tooltip/truncation display.
- `src/tests/playwright/test_inline_dependencies.py`: inline dependency refresh.
- `src/tests/playwright/test_bulk_selection.py`: row selection, shift selection, bulk edit, bulk edit modal/selection cleanup, searchable filters, pagination.
- `src/tests/playwright/test_row_actions_menu.py`: floating row-action menu placement/visibility and action execution from the cloned menu.
- `src/tests/playwright/test_tooltips.py`: toolbar, overflow, semantic-cell, multiline Tippy behaviour, and repeated tooltip/searchable-select initialisation.
- `src/tests/playwright/test_modal_crud.py`: create modal, modal form searchable select behaviour, and per-trigger modal-box class restoration.

## Test Notes For Later Phases

- Phase 2 safety rails now cover the strongest gaps identified by the audit.
- Remaining useful later tests are mostly narrower edge cases: listener registration counts, optional-filter removal, keyboard-only dropdown paths, duplicate modal cleanup, spinner class handling, and error/queued cleanup paths.
- Browser tests should remain behaviour-focused so later internal source splits can proceed without brittle selector-only assertions.
