# Phase 2 Focused DaisyUI Override Points Plan

## Status

Complete. Phases 2.1–2.9 are independently verified and integrated into `staging/main`; all agreed Phase 2 focused override areas are complete.

## Next

Phase 3 is next. Await direction before creating its child plan or beginning reusable JavaScript adapter work.

## Phase 2.0: Apply Shared Slice Safeguards

1. [x] Begin each slice from the current integration base and scope it to one agreed override area.
2. [x] Characterize only the selected area's current rendering, direct fragment use, semantic hooks, HTMX behaviour, and relevant existing tests.
3. [x] Preserve legacy paths, direct fragment names, documented context, semantic hooks, and runtime behaviour for the selected area.
4. [x] Reuse applicable existing tests and add a focused test only where the selected override contract is not already covered.
5. [x] Document the released focused override and extend the focused-copy workflow only after that component has shipped.
6. [x] Merge the verified slice before beginning the next override area.
7. [x] Use two fresh read-only maps per sub-slice: one for runtime/template contracts and one for existing tests and genuine gaps.
8. [x] Commit and push every completed sub-slice, run the full phase gate, squash-integrate the numbered branch into `staging/main`, and retire it before starting the next phase.
9. [x] Record a genuine blocker in `phase2-blockers.md` only when it first occurs; continue independent same-phase work but do not bypass dependencies or implement a later phase from an unintegrated base.

## Phase 2.1: Extract Pagination

1. [x] Characterize pagination, page-size, filters, list refresh, and the `#pagination` legacy fragment.
2. [x] Extract the pack-local pagination component without changing default DaisyUI output or interaction.
3. [x] Preserve pagination context and page-size/list-refresh semantic hooks.
4. [x] Publish the first focused pagination override instructions and its available copy workflow.
5. [x] Verify the existing applicable unit and browser coverage, adding only an uncovered contract test.
6. [x] Merge the completed pagination slice independently.

## Phase 2.2: Extract List Toolbar And Filters

1. [x] 2.2.1 Extract the page-size selector as a focused override; preserve `#page-size-form`, `#page-size-select`, page-size query behaviour, tooltip metadata, and list refresh.
2. [x] 2.2.2 Extract primary list actions; preserve create links, HTMX modal behaviour, permissions, extra actions, and `data-powercrud-action-controls` while leaving bulk selection for Phase 2.4.
3. [x] 2.2.3 Extract the filter trigger; preserve its ID, ARIA state, icons, tooltip, active-filter state, and `data-powercrud-filter-toggle` behaviour.
4. [x] 2.2.4 Extract filter-panel actions; preserve add-filter choices, non-HTMX submit, reset behaviour, and `data-powercrud-add-filter-container`.
5. [x] 2.2.5 Extract the filter form and optional-filter state; preserve `#filter-form`, filter values, validation, `visible_filters`, HTMX headers, target, and history behaviour.
6. [x] For every 2.2 sub-slice, publish its focused-copy command and public guidance, run focused unit/browser checks, commit, and push before beginning the next sub-slice.
7. [x] Keep favourites, visible-column controls, bulk selection, the toolbar shell, and all JavaScript semantics outside this workstream.

## Phase 2.3: Extract Table Structure And Row Actions

1. [x] 2.3.1 Extract the list-column chooser; preserve saved and draft state, POST/HTMX behaviour, query inputs, geometry hooks, and the outer toolbar.
2. [x] 2.3.2 Extract row actions from Python-generated markup into resolved action context plus a focused template; retain `action_links()`, `row.actions`, and `row.has_actions` compatibility.
3. [x] 2.3.3 Extract the table header; preserve sorting, filter/page-size query state, normal and HTMX navigation, help tooltips, action heading, and the select-all bridge.
4. [x] 2.3.4 Extract normal display rows and cells; preserve row/cell metadata, links, tooltips, actions, selection hooks, and inline-display hooks.
5. [x] 2.3.5 Extract the table shell; preserve responsive overflow, sizing, table classes, selection-key metadata, legacy `partial/list.html`, and inline named fragments.
6. [x] Preserve `object_list.html#filtered_results`, the `{% object_list object_list view %}` tag, existing full-template overrides, and unchanged JavaScript throughout Phase 2.3.
7. [x] For every 2.3 sub-slice, publish its focused-copy command and public guidance, run focused unit/browser checks, commit, and push before beginning the next sub-slice.
8. [x] Run the full non-browser and Playwright regression suite after 2.3.5 and record the unintegrated branch evidence.

## Phase 2.4: Extract Bulk Selection And Bulk Outcomes

1. [x] 2.4.1 Extract bulk-selection status and actions while preserving selected counts, modal entry, clearing, and `#bulk_selection_status`.
2. [x] 2.4.2 Extract selection controls while preserving row/select-all state, matching-record selection, truthful initial state, and legacy selection-key behaviour.
3. [x] 2.4.3 Extract the bulk form shell and field controls while preserving update/delete choices, selected IDs, CSRF, modal targeting, searchable selects, and package-owned behaviour.
4. [x] 2.4.4 Extract bulk outcomes while preserving validation errors, operation errors, conflicts, queued success, and all server-addressable bulk fragments.
5. [x] Publish each released focused override and its copy command without requiring copied PowerCRUD JavaScript.
6. [x] Run focused checks for every sub-slice and the full regression gate before independent integration.

## Phase 2.5: Extract Modal Shell And Content

1. [x] 2.5.1 Extract the modal shell while preserving the direct `partial/modal.html` target, IDs, classes, close controls, backdrop, and sizing hooks.
2. [x] 2.5.2 Extract replaceable modal content while preserving targets, HTMX lifecycle, tooltip cleanup, repeated initialization, and refresh-on-close.
3. [x] Publish both focused overrides and copy commands without moving form, detail, delete, or bulk ownership into the modal layer.
4. [x] Run focused checks and the full regression gate before independent integration.

## Phase 2.6: Extract Form Shell, Fields, And Actions

1. [x] 2.6.1 Extract the form shell while preserving create/update context, action URLs, multipart support, CSRF, retained query state, and HTMX/modal behaviour.
2. [x] 2.6.2 Extract native and crispy form fields while preserving the crispy legacy fragments and declared rendering paths.
3. [x] 2.6.3 Extract form actions while preserving save semantics and `data-form-save`.
4. [x] 2.6.4 Extract form conflict presentation while preserving `#pcrud_content`, `#normal_content`, and `#conflict_detected`.
5. [x] Publish each focused override and copy command, then run focused checks and the full regression gate before independent integration.

## Phase 2.7: Extract Detail And Delete Surfaces

1. [x] 2.7.1 Extract detail shell and content while preserving `object_detail.html#pcrud_content`, `partial/detail.html`, and normal/modal rendering.
2. [x] 2.7.2 Extract delete shell and content while preserving confirmation, errors, CSRF, query state, HTMX redisplay, and modal behaviour.
3. [x] 2.7.3 Extract delete actions and conflict presentation while preserving all `object_confirm_delete.html` fragments.
4. [x] Publish each focused override and copy command, then run focused checks and the full regression gate before independent integration.

## Phase 2.8: Extract Inline Editing Surfaces

1. [x] 2.8.1 Extract inline display rows while reconciling the deliberate Phase 2.3 duplication without changing normal table rows.
2. [x] 2.8.2 Extract inline form rows while preserving bound values, actions, validation, save/cancel, and row metadata.
3. [x] 2.8.3 Promote inline fields through model-first focused resolution while preserving dependency metadata and widget replacement.
4. [x] 2.8.4 Extract validation only if characterization proves an independent public boundary; otherwise keep it in the inline form row and record the decision.
5. [x] Preserve both legacy inline fragments, `partial/inline_field.html`, package-owned JavaScript, and all refresh/event semantics.
6. [x] Publish each released focused override and copy command, then run focused checks and the full regression gate before independent integration.

## Phase 2.9: Complete The Focused-Copy Workflow

1. [x] Consolidate every shipped focused component into the current focused `pcrud_mktemplate` registry without introducing future pack-selection APIs.
2. [x] Verify every component's model-first destination, source, supported context, semantic hooks, capabilities, legacy bridges, and no-copied-JavaScript instructions.
3. [x] Retain legacy root-template and whole-tree copy modes through 0.x.
4. [x] Audit public documentation against shipped behaviour and run focused command/override coverage.
5. [x] Run the final full regression, integrate Phase 2.9, and mark Master Phase 2 complete only when every agreed override area is independently integrated.
