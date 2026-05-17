# JavaScript Cleanup Notes

## Context

PowerCRUD has recently added or refined several interactive list features:

1. List-column selection.
2. Saved favourites that include filters, page size, and visible columns.
3. Session-backed current view state.
4. Extra top-button dropdown mode.
5. Filter-panel layout and toolbar positioning.
6. Inline-edit compatibility with hidden list columns.
7. Tippy tooltip handling across toolbar controls and list cells.

Those features are valuable, but they increased the responsibility carried by `src/powercrud/static/powercrud/js/powercrud.js`. The file now coordinates several pieces of state that can affect each other: URL/query state, session-backed view state, favourite state, toolbar layout, HTMX refreshes, inline-edit row rendering, dropdown placement, and tooltip reinitialisation.

The practical risk is not that the current behaviours are wrong. The risk is that future changes can easily break one interaction while fixing another because too much behaviour is coupled through shared DOM selectors, global event listeners, and direct cross-control updates.

## Why This Should Precede Template Packs

The template-pack plan already depends on splitting core runtime behavior from framework-specific behavior. That split will be harder and riskier if the current JavaScript remains a single large file with unclear internal boundaries.

This cleanup should therefore happen before, or at the very start of, the template-pack JavaScript work. It is not the same as implementing template packs. The goal is first to stabilise the current runtime while keeping the same public bundle, globals, templates, and behaviour.

After that, the template-pack split can move code across a clearer boundary:

1. Core PowerCRUD behavior tied to stable `data-*` contracts.
2. DaisyUI-specific visual behavior such as modal APIs, tooltip theme details, and styling embellishments.

## Current Friction Points

The main friction points to investigate are:

1. Global document listeners are spread across many behaviours.
2. HTMX lifecycle handling, fragment reinitialisation, and tooltip refreshes are interleaved with feature logic.
3. Filter, favourites, page-size, visible-column, and reset-view state update each other through direct DOM manipulation.
4. Toolbar layout and dropdown placement are runtime geometry concerns mixed into the same file as CRUD data behaviours.
5. Inline edit depends on current list-column visibility and can be affected by table rendering assumptions.
6. Tom Select, Tippy, HTMX, modal, and row-action wiring each have their own initialisation rules.
7. It is difficult to tell which code is reusable core behavior and which code is DaisyUI-pack behavior.

## Desired Direction

The cleanup should be conservative. It should avoid redesigning the public API while refactoring internals.

Preferred direction:

1. Keep the generated public bundle path and behaviour stable during the cleanup.
2. Add focused browser safety rails around behaviours that protect the future shared-versus-pack boundary.
3. Split source code by responsibility inside the current bundle before creating separate pack JS.
4. Centralise once-only global listener registration and per-fragment shared initialisation.
5. Introduce small state/event helpers where controls currently update each other directly.
6. Keep the browser tests as the main guardrail for list interactions.
7. Defer moving code into an actual `powercrud_daisyui` package until the runtime boundaries are proven in the current bundle.

## Phase 5 Planning

The detailed Phase 5 orchestration plan is in [`phase5-plan.md`](phase5-plan.md).

Phase 5 should reduce direct cross-control coupling after the Phase 3 module split and Phase 4 lifecycle cleanup. The intended shape is a sequence of narrow state-helper slices, not a broad state-management rewrite.

The main caveats are:

1. Keep the stable public entry path and manual `type="module"` contract unchanged.
2. Do not require manual users to import internal runtime modules directly.
3. Do not start template-pack extraction in Phase 5.
4. Do not create `powercrud_daisyui`, separate pack JavaScript, or `initPowercrudPack(fragment)` yet.
5. Do not touch `CHANGELOG.md`; Michael owns changelog updates.

The orchestration should remain one slice at a time: read-only sub-agent plan, coordinator review, implementation for that slice only, focused tests, plan/notes update, commit, push, and clean branch before the next slice.

Every read-only planning sub-agent must be briefed on all JS cleanup audit files, not just the main plan and notes.

### Phase 5.0 Coupling Map Result

The Phase 5.0 read-only pass confirmed the planned sequence. No ambiguous behaviour was found that should stop implementation.

Current live coupling map:

1. `powercrud.js` still orchestrates bootstrap order across list state, columns, favourites, and bulk state. Keep that orchestration in the entry file for now, but make module calls narrower.
2. `powercrud.js` still handles reset-filter clicks by directly coordinating view storage, optional-filter state, filter form clearing, and favourite dirty/selection state. This should move behind a named list-view-state helper in Slice 5.1.
3. `runtime/list-view-state.js` reads favourite toolbar/select state and calls favourite dirty/selection helpers during remember, refresh, and reset paths. This is the main Phase 5 hotspot.
4. `runtime/filter-favourites.js` uses the lazy `getListViewStateApi()` bridge for state capture, reset view, visible-filter persistence, and remembered state. Keep the bridge for now to avoid circular ES-module risk; narrow the API rather than replacing the bridge in Slice 5.1.
5. `runtime/list-view-state.js` reads list-column checkboxes for favourite state and posts list-options reset during reset-view. Save deeper visible-column ownership cleanup for Slice 5.3.
6. `runtime/bulk-actions.js` uses injected `getCurrentFilters()` for table refresh after bulk events. Save that for the bulk-selection slice unless Slice 5.1 naturally clarifies the query helper.
7. HTMX lifecycle ordering in `powercrud.js` remains cross-feature and order-sensitive. Leave it alone unless a current slice touches startup, module imports, or shared lifecycle.
8. Inline-edit state is mostly self-contained after Phase 4, but timing, focus, validation, dependency refresh, and error popover state make it a later high-risk slice.

Accepted first implementation slice:

1. Start with Slice 5.1 in `runtime/list-view-state.js`.
2. Consolidate current list-view state helpers for current root query/state capture, current-view storage, list refresh, and reset-filter/reset-view coordination.
3. Do not redesign favourites in Slice 5.1.
4. Preserve reset-filter versus reset-view semantics with explicit helper names.
5. Keep focused verification on `test_filter_favourites.py`, `test_list_options.py`, and packaging if assets are rebuilt.

### Phase 5.1 Current List-View State Result

Slice 5.1 reduced the reset-filter/list-view-state coupling without changing the public runtime contract.

Implementation result:

1. `runtime/list-view-state.js` now owns `resetCurrentFilters(root)`, replacing the reset-filter orchestration that previously lived in `powercrud.js`.
2. `runtime/list-view-state.js` now centralises favourite toolbar/select/dirty context for current-view remember and restore checks.
3. Current root query collection was renamed internally to `getCurrentListViewQueryValues(root, options)` so the list-view boundary is explicit.
4. Current-view storage and optional-filter clearing are shared through an internal `clearCurrentListViewState(root, options)` helper.
5. Full reset-view still clears filter-panel state and performs the existing list-options reset POST or GET fallback.
6. Reset-filter still clears current view state, optional-filter state, and form values, then marks the selected favourite dirty and syncs favourite presentation. It does not become full reset-view and does not add a new HTMX refresh.
7. Favourite selected/dirty ownership, visible-column ownership, bulk refresh, and HTMX lifecycle order were left for later slices.

Validation run:

1. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_filter_favourites.py src/tests/playwright/test_list_options.py"` passed, 19 tests.
2. `./runproj exec --command "./runtests --rebuild-assets src/tests/test_frontend_asset_packaging.py"` passed, 14 tests.

### Phase 5.2 Favourite Selected And Dirty State Result

Slice 5.2 moved favourite selected/dirty-state knowledge behind named helpers owned by `runtime/filter-favourites.js`.

Implementation result:

1. `runtime/filter-favourites.js` now exposes `getSelectedFilterFavouriteViewContext(root, toolbar)` for the selected favourite id and dirty state.
2. `runtime/filter-favourites.js` now exposes `clearSelectedFilterFavouriteSelection(root, toolbar)` for selected-state clearing.
3. `runtime/filter-favourites.js` now exposes `syncSelectedFilterFavouritePresentation(root)` for intent-level presentation sync.
4. Dirty-storage primitives remain internal to favourites.
5. `runtime/list-view-state.js` no longer receives direct select/value/dirty-storage callbacks. It still receives `getFilterFavouritesContainer` for view-state storage scoping and filter/favourite toolbar visibility.
6. The lazy favourites/list-view bridge, reset-view semantics, visible-column ownership, bulk refresh, and HTMX lifecycle order were left unchanged.

Validation run:

1. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_filter_favourites.py"` passed, 14 tests.
2. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_filter_favourites.py src/tests/playwright/test_list_options.py"` passed, 19 tests.
3. `./runproj exec --command "./runtests --rebuild-assets src/tests/test_frontend_asset_packaging.py"` passed, 14 tests.

### Phase 5.3 Visible Columns And Reset-View Coordination Result

Slice 5.3 moved visible-column state knowledge behind helpers owned by `runtime/list-columns.js`.

Implementation result:

1. `runtime/list-columns.js` now exposes `getVisibleListColumnNames(root)` for current visible-column collection.
2. `runtime/list-columns.js` now exposes `buildListColumnResetRequest(root, listUrl)` for list-options reset form discovery, reset URL selection, CSRF extraction, and reset POST values.
3. `runtime/list-view-state.js` still coordinates full reset-view semantics, but no longer reads list-column checkboxes or builds the list-options reset POST itself.
4. Chooser UI/draft behaviour, favourite comparison semantics, list-options server/template contracts, and reset-view trigger ownership were left unchanged.

Validation run:

1. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_list_options.py"` passed, 5 tests.
2. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_filter_favourites.py"` passed, 14 tests.
3. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_inline_editing.py::test_inline_edit_saves_after_hiding_non_trigger_column"` passed, 1 test.
4. `./runproj exec --command "./runtests --rebuild-assets src/tests/test_frontend_asset_packaging.py"` passed, 14 tests.

### Phase 5.4 Bulk Selection State Result

Slice 5.4 moved bulk-selection presentation and mutation details behind helpers owned by `runtime/bulk-actions.js`.

Implementation result:

1. `runtime/bulk-actions.js` now centralises selection control lookup through `getBulkSelectionControls(root)`.
2. Checked row id collection, mass row checking, selection presentation sync, optimistic clearing, and batch persistence each have named helper boundaries.
3. `powercrud.js` now calls `hydrateBulkSelectionState(root)` and `syncBulkSelectionPresentation(root)` during bootstrap instead of coordinating hydration, select-all state, and selection-aware buttons separately.
4. The Phase 4 repeated-init hydration guard remains intact.
5. Listener order, template contracts, HTMX endpoints, swap targets, bulk edit refresh behaviour, and form spinner/button handling were left unchanged.

Validation run:

1. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_bulk_selection.py"` passed, 9 tests.
2. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_manual_static_assets.py"` passed, 1 test.
3. `./runproj exec --command "./runtests --rebuild-assets src/tests/test_frontend_asset_packaging.py"` passed, 14 tests.

### Phase 5.5 Inline Row State Result

Slice 5.5 moved inline-edit transient row state behind helpers owned by `runtime/inline-edit.js`.

Implementation result:

1. Pending focus/highlight capture, table-width locking, and row-width snapshots are now coordinated through `capturePendingInlineRowState(trigger, row, options)`.
2. Pending and active column-width cleanup plus table-width unlocking now flow through `clearInlineLayoutState(table)`.
3. Applying pending or active row widths after HTMX swaps now flows through `applyPendingInlineRowWidths(row)`.
4. Re-activating an inline form row after an HTMX swap now flows through `activateInlineFormRow(row)`.
5. The slice did not change public inline runtime method names, listener ordering, template `data-*` contracts, inline dependency endpoint semantics, or initial `bootstrapInlineRow()` focus/scroll behaviour.

Validation run:

1. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_inline_editing.py src/tests/playwright/test_inline_dependencies.py"` passed, 10 tests.
2. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_list_options.py::test_book_list_column_chooser_saves_and_resets_columns src/tests/playwright/test_inline_editing.py::test_inline_edit_saves_after_hiding_non_trigger_column"` passed, 2 tests.
3. `./runproj exec --command "./runtests --rebuild-assets src/tests/test_frontend_asset_packaging.py"` passed, 14 tests.

An initial parallel run of the targeted list/hidden-column checks failed because it collided with the active inline suite while both tried to create the shared test database. The targeted checks passed when rerun sequentially.

### Phase 5 Closeout

Phase 5 is complete. It reduced cross-control coupling through narrow helper boundaries rather than a broad state-management abstraction.

Final helper ownership boundaries:

1. `runtime/list-view-state.js` owns current list-view query capture, stored optional filter names, reset-view state clearing, and reset-filter orchestration.
2. `runtime/filter-favourites.js` owns selected favourite context, dirty selected-favourite presentation, and selected favourite clearing.
3. `runtime/list-columns.js` owns visible-column name collection and list-options reset request construction.
4. `runtime/bulk-actions.js` owns bulk-selection control lookup, selected row ids, mass row checking, selection presentation sync, optimistic clearing, batch persistence, and rendered selection hydration.
5. `runtime/inline-edit.js` owns inline pending focus/highlight capture, locked width state, active form-row activation, and inline layout cleanup.

Phase 5 preserved the stable public entry path, the manual `type="module"` loading contract, bundled/Vite manifest loading, public runtime globals, listener ordering, HTMX/template contracts, and current user-visible behaviour. It did not create `powercrud_daisyui`, separate pack JavaScript, or `initPowercrudPack(fragment)`.

Phase 6 should start with a renewed core-versus-current-template-versus-presentation-library boundary review using the current post-Phase-5 runtime, then update the template-pack plan before any template-pack JavaScript extraction starts.

### Phase 6 Planning Setup

Phase 6 should prove the future template-pack boundary without extracting a template pack. The detailed plan is in [`phase6-plan.md`](phase6-plan.md).

Use five working classifications:

1. Core runtime: template/framework independent PowerCRUD semantics and stable `data-*` contracts.
2. Current-template DOM adapter: code that depends on the current HTML shape, selectors, IDs, DOM placement, and toolbar/list layout.
3. Presentation-library adapter: code that depends on DaisyUI, Tippy, Tom Select visual APIs, spinner markup/classes, icon classes, button classes, or colour classes.
4. Mixed adapter boundary: code that combines shared semantics with current-template or presentation-library implementation and probably needs a neutral event, hook, or injected adapter before later extraction.
5. Characterization needed: code that should not be classified without a focused browser proof.

Phase 6 may add characterization tests if a boundary is too risky to classify from code review alone. It should not create `powercrud_daisyui`, separate pack JavaScript, `initPowercrudPack(fragment)`, template-pack loader code, or new public static asset paths.

### Phase 6.0 Runtime Boundary Map Result

Slice 6.0 refreshed the runtime classification against the current post-Phase-5 source tree. This is a boundary map only; it does not authorize template-pack extraction.

| Runtime area | Phase 6 classification | Boundary note |
| --- | --- | --- |
| `powercrud.js` runtime shell, public globals, and module construction | Mixed adapter boundary | The duplicate-load guard, public globals, `window.initPowercrud(fragment)`, fragment teardown, and module assembly are core lifecycle concerns, but the shell still injects current-template callbacks into feature runtimes. |
| `powercrud.js` `bootstrapObjectList()`, `bootstrapObjectLists()`, and `initPowercrud()` | Mixed adapter boundary | The initializer owns shared per-fragment lifecycle order, but that order currently includes searchable selects, modal cleanup, toolbar width sync, tooltips, favourites presentation, list state, and bulk selection. |
| `powercrud.js` once-only listener handler map | Mixed adapter boundary | The listener registration contract is core, but individual handlers still coordinate core events with presentation dismissal, spinners, tooltips, modal classes, row menus, and current-template cleanup. |
| `runtime/dom.js`, `runtime/url.js`, `runtime/storage.js`, `runtime/state.js`, and `runtime/htmx.js` | Core runtime | These modules provide neutral root discovery, query handling, storage-key helpers, weak state, HTMX lookup, and HTMX event-root helpers. |
| `runtime/startup.js` | Core runtime with a small current-template edge | Once-only listener installation and ordering are core runtime. The injected range-selection `user-select` style is a small DOM/presentation concern to revisit later, but it does not require characterization for Slice 6.0. |
| `runtime/selectors.js` | Mixed adapter boundary | The file intentionally centralises both stable core contracts and presentation constants. Core entries include object-list roots, inline contracts, storage prefixes, and view-state ignored fields; adapter entries include tooltip selectors, toolbar/list-column selectors, range-selection CSS, and `DEFAULT_MODAL_BOX_CLASSES`. |
| `runtime/list-view-state.js` view/filter/query/storage and HTMX refresh semantics | Core runtime | Current list-view query capture, optional-filter persistence, current-view storage, reset-view state clearing, filter refresh, page-size refresh, and favourite-state collection are shared PowerCRUD semantics. |
| `runtime/list-view-state.js` filter-panel display helpers | Mixed adapter boundary | The stored open/closed state is core, but the implementation manipulates `#filterCollapse`, `hidden`, trigger labels, tooltip content, add-filter visibility, favourites visibility, and searchable-select initialization. |
| `runtime/filter-favourites.js` state comparison, storage, selection, dirty state, and apply semantics | Core runtime | Favourite state normalization, selected/dirty storage, server-selected reconciliation, apply requests, remembered favourite application, and favourite saved/updated/deleted event handling are shared semantics. |
| `runtime/filter-favourites.js` floating panel, trigger presentation, and save-form UI | Mixed adapter boundary | The same module also clones current-template panel markup, processes HTMX on the floating panel, initializes Tom Select and Tippy, coordinates trigger presentation, manages focus, and depends on current toolbar/panel DOM shape. |
| `runtime/list-columns.js` visible-column semantics | Mixed adapter boundary | Visible-column collection and reset-request construction are core; chooser `<details>` lifecycle, first-checkbox focus, close-on-outside behaviour, visual last-column state, and injected placement callbacks are current-template adapter concerns. |
| `runtime/bulk-actions.js` selection state and server persistence | Core runtime | Row id collection, select-all state, shift range selection, request-version guards, server persistence, clear selection, refresh-table semantics, and queued/success selection clearing are shared semantics. |
| `runtime/bulk-actions.js` counters, containers, disabled visuals, and bulk modal success | Mixed adapter boundary | Selection-aware minimum-count semantics are core, but `#selected-items-counter`, `#bulk-actions-container`, `hidden` toggles, disabled visual classes/tooltips, bulk form button disabling, and DaisyUI modal close are adapter concerns. |
| `runtime/inline-edit.js` active row, guards, dependencies, and row refresh | Core runtime | Active-row state, guard events, save/cancel/error events, dependency mapping, child-widget refresh, and HTMX row refresh are shared inline-edit semantics. |
| `runtime/inline-edit.js` layout, focus, error popovers, and spinners | Mixed adapter boundary | Table width locking, scroll/focus treatment, Tom Select dropdown behaviour, body-level inline error popovers, `sr-only` hiding, and save-spinner callbacks combine shared semantics with current-template presentation. |
| `runtime/searchable-selects.js` | Presentation-library adapter with a core opt-in contract | `data-powercrud-searchable-*` is a core opt-in contract, but Tom Select construction, plugins, dropdown placement, native-select hiding/restoration, clear-button markup, and inline/favourite classes are presentation-library adapter behaviour. |
| `runtime/current-template.js` modal, tooltip, toolbar, row-action, spinner, list-column, favourites, and inline visual helpers | Current-template DOM adapter plus presentation-library adapter | This module is adapter-heavy, but it should be split by concern later: DaisyUI/dialog/modal classes, Tippy setup, spinner markup, icon/colour classes, current table/toolbar geometry, floating row-action/favourites placement, and HTMX processing of cloned panels are not all the same kind of dependency. |

Slice 6.0 uncertainties carried forward:

1. Tom Select native restore and repeated-initialisation edges may need characterization before later extraction.
2. Duplicate modal cleanup is adapter-owned, but current coverage is indirect.
3. Selection-aware buttons need a later decision separating core minimum-count semantics from adapter classes and tooltip copy.
4. Inline error popovers remain one of the largest mixed boundaries.
5. Row-action floating menus process HTMX from adapter-like code, so later extraction likely needs a neutral menu/action hook or event decision.

### Phase 6.1 Core-Owned Contract Result

Slice 6.1 identified the neutral contracts that shared core must continue to own. Some contracts still use current-template selectors today; those are marked as uncertain rather than forced into core.

| Contract group | Core-owned contracts | Core responsibility | Boundary note |
| --- | --- | --- | --- |
| Object-list scope | `data-powercrud-object-list`, `data-powercrud-list-url`, `data-powercrud-original-target` | Root discovery, canonical list refresh URL, storage scoping, and outer-versus-inner swap target selection. | Core must keep these stable even if pack templates move. |
| Filter and optional-filter state | `data-powercrud-filter-form`, `data-powercrud-add-filter-select`, `data-powercrud-remove-filter`, `data-powercrud-visible-filters-state`, `visible_filters` | Filter refresh, optional-filter add/remove, hidden optional-filter state, and query-state persistence. | Add-filter control placement remains adapter-owned. |
| Page size and list query state | `data-powercrud-page-size-select`, `#filter-form`, `#page-size-form` | Page-size refresh, current list query capture, and current/favourite view-state comparison. | The form IDs are current contracts used by core; later pack work should decide whether they stay as required template-pack contract. |
| Favourite semantic state | `data-powercrud-filter-favourites-view-key`, `data-powercrud-favourite-state-json`, `data-powercrud-favourite-visible-filters`, `data-powercrud-favourite-manage-action`, `data-powercrud-favourite-apply`, `data-powercrud-reset-view` | Explicit storage-key scoping, favourite state comparison, optional-filter restoration, action guards, favourite apply, and reset-view semantics. | Floating panel, trigger, icon, and dropdown markup remain adapter or mixed. |
| Visible columns | `data-powercrud-list-column-checkbox`, `data-powercrud-initial-checked`, `data-powercrud-last-visible-column`, `visible_columns`, `list_columns_action`, `list_view_url` | Visible-column collection, server-rendered baseline, last-column guard, and reset/persist request payloads. | Chooser shell, placement, and option visuals remain adapter-owned. |
| Bulk selection | `data-powercrud-select-all`, `data-powercrud-row-select`, row checkbox `data-id`, `data-powercrud-initial-checked`, `data-powercrud-initial-indeterminate`, `data-powercrud-clear-selection` | Select-all and row selection state, rendered selection hydration, row id persistence, and clear-selection semantics. | Counter/container rendering remains mixed. |
| Bulk selection request guards | `data-powercrud-shift-range`, `data-powercrud-skip-selection-request`, `data-powercrud-selection-request-pending`, `data-powercrud-selection-request-version` | Shift-range request suppression and stale HTMX selection-request protection. | Internal, but core-owned while selection semantics stay in core. |
| Selection-aware action semantics | `data-powercrud-selection-aware`, `data-powercrud-selection-min-count`, `data-powercrud-selection-min-behavior`, `data-powercrud-selection-min-reason` | Minimum selected-count requirement and reason payload. | Disabled classes and tooltip rendering are adapter-owned. |
| Searchable-select opt-in | `data-powercrud-searchable-select`, `data-powercrud-searchable-multiselect`, `data-powercrud-searchable-placeholder` | Stable opt-in and placeholder semantics for enhanced selects. | Tom Select construction, plugins, native-select restore, dropdown placement, and clear-button rendering are adapter or characterization-needed. |
| Inline row lifecycle | `table[data-inline-enabled]`, `tr[data-inline-row]`, `data-inline-active`, `data-inline-row-url`, `data-inline-status`, `.inline-edit-trigger`, `data-inline-save`, `data-inline-cancel` | Inline table/row discovery, active-row state, row refresh/cancel URL, guard state, edit entry, and save/cancel lifecycle. | `.inline-edit-trigger` is a class-based semantic contract today. |
| Inline fields and dependencies | `data-inline-field`, `data-inline-cell`, `data-inline-dependent`, `data-inline-depends-on`, `data-inline-endpoint`, `data-inline-refreshing` | Field identity, editable-cell identity, parent-child dependency mapping, child-widget refresh endpoint, and refresh marker. | Widget DOM shape remains mixed. |
| Inline validation payload | `data-inline-field-error`, `data-inline-error-field`, `data-inline-error-label`, `data-inline-error-message` | Validation error discovery and payload transfer from rendered markup to runtime. | Error popover rendering and error-text hiding remain mixed. |
| Public globals | `window.__powercrudRuntimeLoaded`, `window.initPowercrud(fragment)`, `window.getCurrentFilters(options)`, `window.initPowercrudSearchableSelects`, `window.destroyPowercrudSearchableSelects`, `window.initPowercrudTooltips`, `window.hidePowercrudTooltips`, `window.destroyPowercrudTooltips`, `window.powercrudToggleFavouriteSaveForm` | Duplicate-load guard, public per-fragment initializer, current filter helper, and compatibility lifecycle hooks. | Searchable-select, tooltip, and favourite-save implementations may move later, but the globals remain stable unless Michael approves a public API change. |
| HTMX lifecycle events | `htmx:beforeRequest`, `htmx:configRequest`, `htmx:beforeSwap`, `htmx:afterSwap`, `htmx:afterSettle`, `htmx:afterRequest`, `htmx:responseError` | Request shaping, lifecycle teardown/init, stale request handling, and inline/bulk cleanup. | Listener ordering is core. Presentation work inside handlers remains a later boundary decision. |
| PowerCRUD body events | `bulkEditSuccess`, `bulkEditQueued`, `refreshTable`, `powercrud:favourite-saved`, `powercrud:favourite-updated`, `powercrud:favourite-deleted`, `inline-row-locked`, `inline-row-forbidden`, `inline-row-saved`, `inline-row-error` | Selection clearing, list refresh, favourite selected/dirty reconciliation, inline guard/result handling, row refresh, and error focus. | Modal close, panel close, and error-popover presentation remain adapter or mixed. |
| Storage keys | `powercrud:visible-filters:<path>`, `powercrud:view-state:<view-key-or-path>`, `powercrud:selected-filter-favourite:<view-key-or-path>`, `powercrud:selected-filter-favourite-dirty:<view-key-or-path>` | Optional-filter persistence, current list query state, selected favourite id, and dirty selected favourite id. | `powercrud:filter-panel:<list-url>` is carried forward as mixed because the state is semantic but the panel is current-template DOM. |
| URL/query-state rules | `data-powercrud-list-url`, list query params from filter/page-size forms, `page` preservation rules, `sort`, `page_size`, `visible_filters`, `visible_columns`, ignored view-state field names, `X-Filter-Setting-Request`, `X-Filter-Sort-Request` | Canonical refresh path, query capture, current/favourite comparison, sanitized stored query state, and server-side refresh intent. | `visible_columns` remains optional for older favourite payloads. |

Contracts carried forward for Slice 6.3 or Slice 6.4:

1. Tooltip attributes and Tippy runtime state: `data-powercrud-tooltip`, `data-tippy-content`, `_tippy`, and `data-tippy-root`.
2. Filter panel shell contracts: `#filterCollapse`, `data-powercrud-filter-toggle`, and `data-powercrud-add-filter-container`.
3. Favourites panel and trigger presentation contracts: toolbar, trigger, template, panel, floating-panel, trigger-label, icon, selected, and dirty attributes.
4. List-column chooser shell contracts: `data-powercrud-list-columns`, trigger, panel, placement, and option attributes.
5. Row-action menu contracts: dropdown, trigger, template, floating panel, panel, and cloned HTMX processing.
6. Bulk UI contracts: `#selected-items-counter`, `#bulk-actions-container`, `data-powercrud-form="bulk"`, and bulk-delete confirmation IDs.
7. Inline presentation/runtime bookkeeping: inline error text hiding, body-level inline error popovers, width locks, table locks, hotkey-bound markers, dependency-bound markers, and error-dismiss markers.
8. Tom Select native restore contracts: `data-powercrud-native-tabindex` and `data-powercrud-native-style`.
9. Server HX triggers that are public but not wholly owned by current runtime JS: `formError`, `formSuccess`, `modalFormSuccess`, `refreshList`, `refreshUrl`, and `showModal`.

### Phase 6.2 Adapter Behaviour Result

Slice 6.2 separated future current-template DOM adapter behaviour from direct presentation-library behaviour. This table is still a planning classification; it does not move code.

Current-template DOM adapter behaviours:

| Behaviour | Future adapter-owned concern | Shared semantics to leave in core |
| --- | --- | --- |
| Toolbar and filter-panel width sync | Measuring `#filtered_results table`, sizing `[data-powercrud-list-toolbar]` and `#filterCollapse`, and setting `data-powercrud-toolbar-wrapped`. | Object-list root discovery, list refresh, filter/query state, and current view state. |
| Row-action floating menu | Hidden template lookup, body-level clone, fixed positioning, viewport clamping, `aria-expanded`, and close-on-scroll/outside/Escape behaviour. | Row action meaning, HTMX action execution, and `data-inline-action` semantics. |
| Favourites floating panel placement | Toolbar template clone, body-level floating shell, toolbar id back-reference, fixed placement, and visibility/pointer-events staging. | Favourite state comparison, selected/dirty storage, apply/update/delete events, and current-state JSON. |
| List-column chooser shell | `<details>` open/close lifecycle, first-checkbox focus, outside/Escape close, draft reset on close, and placement attribute. | Visible-column collection, last-visible-column guard, and reset request construction. |
| Filter panel display shell | `#filterCollapse`, `hidden` toggling, add-filter/favourites visibility, trigger label, and tooltip refresh. | Persisted filter-panel open state, visible optional filters, and filter refresh semantics. |
| Bulk-selection display containers | `#selected-items-counter`, `#bulk-actions-container`, and `hidden` visibility toggles. | Selected ids, select-all/indeterminate state, shift-range selection, server persistence, and minimum-count semantics. |

Presentation-library adapter behaviours:

| Behaviour | Future adapter-owned concern | Shared semantics to leave in core |
| --- | --- | --- |
| Modal API and modal-box classes | `<dialog>` / `HTMLDialogElement`, duplicate dialog cleanup, DaisyUI `modal-box` default classes, per-trigger class application, and modal closing. | Modal-trigger intent and server/form result events. |
| Tippy tooltip runtime | `window.tippy`, `_tippy`, Tippy themes, placement, destroy/hide/recreate lifecycle, and overflow-on-show check. | Tooltip intent attributes and tooltip content semantics. |
| Tom Select enhancement | `window.TomSelect`, Tom Select settings/plugins/events, dropdown parent, wrapper/control normalization, native-select hide/restore, and clear-button markup. | Searchable-select opt-in contract and value synchronization before core submit/refresh paths. |
| Form, button, and inline spinners | `loading loading-spinner` markup, spinner sizing classes, and fixed button width during loading. | Request lifecycle decisions about when object, bulk, and inline operations start or stop. |
| Selection-aware disabled visuals | `btn-disabled`, `opacity-50`, `pointer-events-none`, and Tippy reason attributes. | Minimum selected-count rule, disable/allow decision, and reason payload. |
| Favourite trigger icon and colour treatment | Outline/filled icon toggles, `hidden`, `text-primary`, `text-warning`, and Tippy content refresh. | Selected favourite id, dirty state, and selected display label. |
| List-column disabled visual state | `cursor-not-allowed` and `opacity-70` on current option containers. | Last-visible-column guard and checkbox state correction. |
| Inline error popover presentation | Body-level `pc-inline-error-popover`, `sr-only` hiding, popover positioning, and placement data. | Inline validation error payload, field ownership, save/error events, and error focus. |

Mixed behaviours carried forward for Slice 6.3:

1. `initPowercrud()` ordering: core lifecycle order currently invokes Tom Select, toolbar sizing, tooltip setup, favourites presentation, list-column presentation, and bulk presentation together.
2. Favourites panel opening: `openFilterFavouritesPanel()` mixes selected/panel state sync with template cloning, HTMX processing, Tom Select, Tippy, and floating geometry.
3. Filter panel visibility: open/closed persistence is core, but `#filterCollapse`, `hidden`, tooltip label updates, add-filter visibility, and searchable-select initialization are adapter-shaped.
4. Searchable selects: the `data-powercrud-searchable-*` opt-in is core, but Tom Select construction and visual normalization are presentation-library behaviour.
5. Selection-aware actions: minimum-count semantics are core, while disabled classes and tooltip reason rendering are adapter-owned.
6. Inline focus and errors: active-row/save/error semantics are core, while Tom Select focus routing, body popovers, `sr-only`, and geometry are adapter/presentation.
7. Bulk modal success: bulk success/queued semantics are core, while DaisyUI modal close and duplicate modal cleanup are presentation-library behaviour.
8. Row-action cloned menu HTMX processing: menu presentation is current-template-owned, but executing HTMX actions from cloned markup likely needs a neutral menu/action hook before extraction.

### Phase 6.3 Boundary Hook And Characterization Result

Slice 6.3 converted the mixed-boundary list into decisions for later implementation. These decisions do not extract code; they describe what future extraction should do first.

| Behaviour | Decision | Rationale | Characterization need |
| --- | --- | --- | --- |
| `initPowercrud()` ordering | Needs injected adapter hook later. | Core should continue owning idempotent fragment initialization and once-only listener order, but adapter initialization for Tom Select, tooltips, toolbar geometry, list-column presentation, favourites presentation, and bulk presentation should eventually run through injected adapter callbacks. | No Phase 6 test needed; repeated-init and manual-static coverage already prove the current public lifecycle. |
| Favourites panel opening | Needs injected hook plus possible neutral panel event later. | Favourite state sync, dirty/selected storage, and apply/update/delete semantics stay core. Template cloning, body-level panel placement, Tom Select, Tippy, and trigger presentation are adapter concerns. | No Phase 6 test needed for classification; future extraction should protect panel open/apply/update/delete flows. |
| Filter panel visibility | Stay core for persisted open/closed state; move shell rendering through current-template hook later. | Optional-filter visibility and filter refresh are core. `#filterCollapse`, `hidden`, labels, tooltip content, add-filter visibility, and searchable-select initialization are current-template/presentation behaviour. | No Phase 6 test needed; optional-filter removal without favourites remains a useful future safeguard but does not block classification. |
| Searchable selects | Core keeps opt-in and value-sync contract; implementation should move as presentation-library adapter later. | `data-powercrud-searchable-*` is a stable semantic opt-in. Tom Select construction, plugins, dropdown parent, wrapper classes, native hiding/restoration, and clear-button markup are presentation-library concerns. | No Phase 6 test needed; existing repeated-init coverage is enough for classification. Native restore can be characterized before actual extraction. |
| Tooltip semantics | Core keeps tooltip intent and content contracts; Tippy setup moves later as presentation-library adapter. | Tooltip meaning is shared, but `_tippy`, themes, placement, overflow-on-show rendering, and destroy/hide/recreate APIs are Tippy-specific. | No Phase 6 test needed; tooltip reinitialization coverage is already strong enough for classification. |
| Selection-aware actions | Stay core for minimum-count decision; move visual state through injected adapter hook later. | Core owns selection count, `min-count`, behavior, and reason payload. Button classes, pointer-event blocking, opacity, and tooltip reason rendering are adapter concerns. | No Phase 6 test needed; visual-state coverage can be added before extraction if this hook is implemented. |
| Inline focus and errors | Stay core for inline row/error semantics; move focus affordances and popover presentation through hooks later. | Active row, guard events, save/cancel/error events, dependency refresh, and row refresh stay core. Tom Select focus routing, scroll treatment, body popovers, `sr-only`, geometry, and save spinner are adapter/presentation. | No Phase 6 test needed; inline validation coverage exists, but future extraction should add popover-specific protection if moving rendering. |
| Bulk modal success | Stay core for success/queued semantics; move modal close and duplicate modal cleanup as presentation-library adapter. | Core owns selection clearing and refresh semantics. DaisyUI dialog close and duplicate modal cleanup are framework-specific. | No Phase 6 test needed; duplicate modal cleanup lacks direct coverage but is classifiable from the current code. |
| Row-action cloned menu HTMX processing | Needs neutral menu/action event or injected hook before extraction. | Menu cloning and geometry are current-template presentation. Running `htmx.process()` on cloned menu content crosses into shared action execution and should not be blindly moved into pack code. | No Phase 6 test needed; current row-action modal coverage proves the path. Future extraction should protect cloned action execution. |
| List-column chooser shell | Core keeps visible-column semantics; move shell/placement visuals through injected adapter hook later. | Visible-column collection, last-column guard, and reset request stay core. `<details>` shell, focus, outside/Escape close, placement, and option visual classes are adapter concerns. | No Phase 6 test needed; existing list-options coverage protects current behaviour. |
| Duplicate modal cleanup | Move later as presentation-library adapter. | The code depends on `HTMLDialogElement`, shared modal IDs, open dialog state, and DaisyUI modal-box conventions. It is not a shared PowerCRUD data semantic. | Not needed for classification; optional future safeguard before modal adapter extraction. |
| Server HX triggers not directly consumed by runtime | Defer ownership decision to future server/template-pack work. | `formError`, `formSuccess`, `modalFormSuccess`, `refreshList`, `refreshUrl`, and `showModal` are public server/template surface but are not wholly owned by current runtime JS. | No Phase 6 test needed; keep out of the core JS-owned contract table for now. |

Slice 6.3 characterization decision:

No browser characterization test is required to classify the current boundary safely. The under-covered behaviours found during the pass are useful future extraction safeguards, not blockers for Phase 6 documentation:

1. Native-select restore when Tom Select is destroyed before HTMX swaps.
2. Duplicate modal cleanup.
3. Optional-filter removal/reset without a selected favourite.
4. Selection-aware disabled visual state.
5. Inline error popover rendering after extraction.
6. Row-action cloned-menu HTMX execution after extraction.

### Phase 6.4 Characterization Test Result

Slice 6.4 closed without adding tests. A read-only test-planning pass confirmed that the Slice 6.3 decisions are classifiable from current code and existing coverage.

Existing coverage already proves the main current behaviours needed for classification:

1. Manual-static and tooltip tests cover repeated initialization without duplicate Tom Select wrappers or lost tooltip instances.
2. Modal tests cover modal-box class application and restoration.
3. Row-action tests cover HTMX/modal execution from the cloned floating menu.
4. Inline tests cover validation popover creation and cleanup on the current path.
5. Bulk-selection tests cover selection clearing and container visibility after bulk modal success.

Remaining gaps should be handled as future extraction safeguards, not Phase 6 blockers:

1. Native-select restore before moving Tom Select implementation.
2. Duplicate modal cleanup before moving modal adapter code.
3. Optional-filter removal/reset without a favourite before changing list-view/filter state ownership.
4. Selection-aware disabled visuals before extracting the visual-state hook.
5. Inline error popover rendering before moving popover presentation.
6. Row-action cloned-menu HTMX execution before extracting floating-menu behaviour.

## Core Versus DaisyUI Classification

The cleanup should explicitly identify which JavaScript is independent PowerCRUD runtime behavior and which JavaScript belongs to the current DaisyUI presentation layer. This classification is useful even if no template-pack extraction happens in the first cleanup slice.

Use three categories:

1. Core: behavior that depends only on PowerCRUD semantics and stable `data-*` contracts.
2. DaisyUI-specific: behavior that depends on DaisyUI templates, classes, modal APIs, visual conventions, or pack-owned styling.
3. Boundary/unclear: behavior that currently mixes core state semantics with DaisyUI-specific markup or presentation.

Likely core areas include:

1. HTMX list refresh semantics.
2. Filter, page-size, and visible-column state capture.
3. Saved-favourite state comparison and dirty-state logic.
4. Bulk-selection state and server refresh coordination.
5. Inline-edit lifecycle semantics.

Likely DaisyUI-specific areas include:

1. DaisyUI modal API handling.
2. Tooltip theme and visual treatment.
3. Toolbar and dropdown placement details that depend on current DaisyUI markup.
4. Tom Select styling glue where it exists only to match the DaisyUI templates.

Boundary areas should be called out rather than forced into a category too early. The expected output is a small classification table in these notes that future template-pack work can reuse when deciding the core-vs-pack JavaScript boundary.

## Audit Conclusion

The cleanup is worth doing even before template packs because `powercrud.js` has become the shared interaction hub for list state, favourites, visible columns, bulk selection, inline edit, HTMX swaps, modals, dropdowns, tooltips, and widget initialisation. The current behaviours are valuable and should be preserved, but the coupling makes future UI work risky.

The more specific template-pack reason is that the file currently combines two different responsibilities:

1. Shared PowerCRUD runtime behaviour that every template pack should get for free.
2. DaisyUI/current-template behaviour that only the built-in DaisyUI presentation should own.

Trying to extract DaisyUI pack JS before this cleanup would risk moving shared PowerCRUD semantics into a pack, or leaving DaisyUI assumptions behind in core. The cleanup should therefore first make the boundary visible inside the existing bundle.

## Working Runtime Boundary

Shared core should own:

1. Object-list root discovery and HTMX list refresh semantics.
2. Filter, optional-filter, page-size, visible-column, and reset-view state.
3. Saved-favourite state comparison, selected state, and dirty-state semantics.
4. Bulk selection, server selection persistence, and selection-aware action semantics.
5. Inline edit lifecycle, active-row state, guard events, and dependency refresh semantics.
6. Neutral `data-powercrud-*` and `data-inline-*` contracts.
7. A future `initPowercrud(fragment)` lifecycle path that is safe for full-page loads and HTMX swaps.

DaisyUI or future pack JS should own:

1. Modal API calls and modal-box class application.
2. Tooltip library setup, placement, theme, and visual rendering.
3. Floating favourites panels and row action menus.
4. Toolbar geometry, dropdown placement, and current DaisyUI layout fixes.
5. Spinner markup, button disabled classes, icon toggles, and colour classes.
6. Any pack-only visual embellishment that does not change core event semantics.

Boundary areas should stay explicit until implementation proves the right split. Saved favourites, list columns, row actions, tooltips, Tom Select, bulk edit, and inline error popovers all contain both shared semantics and current-template presentation.

## Phase 1 Audit Outputs

The Phase 1 inventory is split across focused audit docs:

1. [`powercrud-js-behaviour-inventory.md`](powercrud-js-behaviour-inventory.md) maps current runtime behaviour areas.
2. [`powercrud-js-contract-map.md`](powercrud-js-contract-map.md) maps selectors, attributes, events, storage keys, and public globals.
3. [`powercrud-js-listeners-and-dependencies.md`](powercrud-js-listeners-and-dependencies.md) maps once-only listeners, repeated initialisation, and cross-feature dependencies.
4. [`powercrud-js-test-coverage-map.md`](powercrud-js-test-coverage-map.md) maps current Playwright coverage and likely safety-rail gaps.

## Phase 2 Safety Rails

Phase 2 added focused Playwright tests before any JavaScript refactor. The new tests intentionally cover behaviours at the future shared-runtime/template-pack boundary:

1. Saved favourites now have direct browser coverage for page-size dirty state, reset-view clearing of filters/page size/visible columns/selected favourite state, and delete clearing selected/dirty state.
2. List-column chooser draft state is covered when the chooser closes without saving.
3. Inline edit is covered after a visible-column change hides a non-trigger column.
4. DaisyUI modal-box class application is covered for per-trigger modal classes and default-class restoration.
5. Row-action floating-panel action execution is covered from the cloned menu into a DaisyUI modal.
6. Bulk edit success is covered for modal close plus selection counter/container/checkbox clearing.
7. Searchable-select and tooltip initialisers are covered for idempotent repeated calls before and after an HTMX refresh.

The implementation deliberately did not change `powercrud.js`. The point of this slice was to protect the current behaviour before splitting the source file.

Validation run:

1. Focused new/high-risk node-id run passed, 9 tests.
2. Phase 2 browser file slice passed, 45 tests.

Phase 2 browser file slice command:

```bash
./runproj exec --command "./runtests --playwright src/tests/playwright/test_filter_favourites.py src/tests/playwright/test_list_options.py src/tests/playwright/test_inline_editing.py src/tests/playwright/test_modal_crud.py src/tests/playwright/test_row_actions_menu.py src/tests/playwright/test_bulk_selection.py src/tests/playwright/test_tooltips.py"
```

## Phase 3 Sequencing

Phase 3 should be executed as small behaviour-preserving extraction slices, not as one large rewrite. The plan now treats the source split as eight ordered tasks:

1. Runtime shell, bundle guard, public globals, and startup wiring.
2. Low-level DOM, storage, URL, HTMX, selector, and state utility helpers.
3. Filters, optional filters, page size, current view state, and reset view.
4. Saved favourites.
5. List-column chooser.
6. Bulk selection and bulk edit.
7. Inline edit and inline dependencies.
8. DaisyUI/current-template behaviours.

Each slice should keep the public bundle stable, run the relevant focused browser tests, and be committed before moving to the next slice. Phase 4 and Phase 5 stay separate because they are cross-cutting lifecycle and coupling cleanup after the first mechanical source split.

### Phase 3.1 Runtime Shell Result

Phase 3.1 introduced internal runtime installer boundaries inside `powercrud.js`:

1. `installPowercrudPublicGlobals(global)` owns the existing `window.*` helper assignments.
2. `installPowercrudStartup()` owns the once-only style injection and global listener registration.
3. `installPowercrudRuntime(global)` wires the public globals and startup path together after the existing duplicate-load guard.

This first slice deliberately did not add native `import` statements or new JS files. The published docs still describe manual classic-script loading of `powercrud/js/powercrud.js`, so the first runtime-shell extraction preserved that public mode while making the startup boundary explicit.

The packaging decision after 3.1 is to proceed with real ES-module splitting for the remaining Phase 3 slices. Bundled/Vite users should continue to use the Vite manifest path and should not hard-code hashed filenames. Manual users should keep the stable entry path, but load it as a module:

```html
<script type="module" src="{% static 'powercrud/js/powercrud.js' %}"></script>
```

Manual users do not need to know or load hashed Vite filenames, and they do not need to list every imported runtime file. The browser follows relative imports from `powercrud/js/powercrud.js`. The compatibility break is only for old manual classic-script usage:

```html
<script defer src="{% static 'powercrud/js/powercrud.js' %}"></script>
```

That old form was replaced in the stable manual-loading docs during Phase 3.1A.

Validation run:

1. `./runproj exec --command "./runtests src/tests/test_frontend_asset_packaging.py"` passed, 10 tests.
2. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_filter_favourites.py src/tests/playwright/test_modal_crud.py src/tests/playwright/test_tooltips.py src/tests/playwright/test_row_actions_menu.py"` passed, 23 tests.
3. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_filter_favourites.py src/tests/playwright/test_list_options.py src/tests/playwright/test_inline_editing.py src/tests/playwright/test_modal_crud.py src/tests/playwright/test_row_actions_menu.py src/tests/playwright/test_bulk_selection.py src/tests/playwright/test_tooltips.py"` passed, 45 tests.

### Phase 3.1A Module Entry Result

Phase 3.1A introduced the first real ES-module import without moving feature behaviour:

1. `powercrud/js/powercrud.js` now imports `./runtime/startup.js`.
2. `runtime/startup.js` owns only the shift-selection text-suppression style injection.
3. The public entry remains `powercrud/js/powercrud.js`.
4. Bundled users still load through the Vite manifest entry `config/static/js/main.js`.
5. Manual users now load the stable entry with `type="module"`; they still do not list internal module files directly.

Stable docs updated:

1. `docs/mkdocs/guides/getting_started.md`
2. `docs/mkdocs/guides/styling_tailwind.md`

Validation run:

1. `./runproj exec --command "./runtests --rebuild-assets src/tests/test_frontend_asset_packaging.py"` passed, 11 tests.
2. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_filter_favourites.py src/tests/playwright/test_list_options.py src/tests/playwright/test_inline_editing.py src/tests/playwright/test_modal_crud.py src/tests/playwright/test_row_actions_menu.py src/tests/playwright/test_bulk_selection.py src/tests/playwright/test_tooltips.py"` passed, 45 tests.

### Phase 3.2 Low-Level Runtime Helper Result

Phase 3.2 extracted low-level helper modules without moving feature behaviour:

1. `runtime/selectors.js` owns stable selector, storage-prefix, and ignored-query-field constants.
2. `runtime/dom.js` owns DOM/root discovery and swap-target helpers.
3. `runtime/storage.js` owns browser-storage and storage-key helper primitives.
4. `runtime/url.js` owns URL/query-string helper primitives.
5. `runtime/htmx.js` owns HTMX lookup and event-root helpers.
6. `runtime/state.js` owns the WeakMap-backed state-store helper.

`powercrud.js` keeps the feature-level wrappers and public globals. The slice did not move filter, favourites, list-column, bulk-selection, inline-edit, modal, tooltip, or DaisyUI presentation behaviour.

Validation run:

1. `./runproj exec --command "./runtests --rebuild-assets src/tests/test_frontend_asset_packaging.py"` passed, 11 tests.
2. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_filter_favourites.py src/tests/playwright/test_list_options.py src/tests/playwright/test_inline_editing.py src/tests/playwright/test_modal_crud.py src/tests/playwright/test_row_actions_menu.py src/tests/playwright/test_bulk_selection.py src/tests/playwright/test_tooltips.py"` passed, 45 tests.

### Phase 3.3 List View State Runtime Result

Phase 3.3 extracted list-view state behaviour into `runtime/list-view-state.js`:

1. `runtime/list-view-state.js` owns filter-panel state, optional-filter visibility state, filter refresh, page-size/current-query capture, current-view persistence, favourite state collection from the active list view, and reset-view coordination.
2. `powercrud.js` still owns the stable public entry, global listener registration, saved-favourite UI wiring, list-column chooser UI, bulk selection, inline edit, modal, tooltip, and current DaisyUI presentation behaviours.
3. The module is constructed with the entry-owned dependencies it needs, including root lookup, HTMX lookup, swap-target lookup, list-column checkbox lookup, searchable-select refresh, tooltip refresh, and favourites selected/dirty helpers.
4. Public static paths and template includes remain unchanged. The manual-loading contract remains the Phase 3.1A module script contract.

Validation run:

1. `./runproj exec --command "./runtests --rebuild-assets src/tests/test_frontend_asset_packaging.py"` passed, 11 tests.
2. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_filter_favourites.py src/tests/playwright/test_tooltips.py src/tests/playwright/test_bulk_selection.py src/tests/playwright/test_list_options.py"` passed, 32 tests.
3. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_filter_favourites.py src/tests/playwright/test_list_options.py src/tests/playwright/test_inline_editing.py src/tests/playwright/test_modal_crud.py src/tests/playwright/test_row_actions_menu.py src/tests/playwright/test_bulk_selection.py src/tests/playwright/test_tooltips.py"` passed, 45 tests.

### Phase 3.4 Saved Favourites Runtime Result

Phase 3.4 extracted saved-favourites behaviour into `runtime/filter-favourites.js`:

1. `runtime/filter-favourites.js` owns saved-favourite selected/dirty storage, state comparison, apply/update/delete handling, floating favourites panel state, inline favourite save-form state, and favourite-specific HTMX request handling.
2. `powercrud.js` still owns the stable public entry and listener registration; favourite-specific listener branches now delegate into the favourites runtime.
3. The favourites runtime uses a lazy bridge back to `runtime/list-view-state.js` for current list-view state, optional-filter persistence, reset-view, and remembered current-view helpers. This avoids a circular ES-module import while preserving the Phase 3.3 ownership boundary.
4. Public static paths, public globals, favourites events, storage keys, and manual-loading contract remain unchanged.

Validation run:

1. `./runproj exec --command "./runtests --rebuild-assets src/tests/test_frontend_asset_packaging.py"` passed, 11 tests.
2. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_filter_favourites.py"` passed, 14 tests.
3. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_filter_favourites.py src/tests/playwright/test_list_options.py src/tests/playwright/test_tooltips.py"` passed, 24 tests.
4. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_filter_favourites.py src/tests/playwright/test_list_options.py src/tests/playwright/test_inline_editing.py src/tests/playwright/test_modal_crud.py src/tests/playwright/test_row_actions_menu.py src/tests/playwright/test_bulk_selection.py src/tests/playwright/test_tooltips.py"` passed, 45 tests.

### Phase 3.5 List Column Runtime Result

Phase 3.5 extracted list-column chooser behaviour into `runtime/list-columns.js`:

1. `runtime/list-columns.js` owns list-column checkbox lookup, last-visible-column guard state, chooser draft reset, chooser focus/close handling, dropdown placement, and list-options form lookup.
2. `powercrud.js` still owns the stable public entry and listener registration; list-column listener branches now delegate into the list-column runtime.
3. `runtime/list-view-state.js` still owns current/favourite visible-column state capture and reset-view coordination, using injected list-column helpers from the new module.
4. Public static paths, selector/data contracts, visible-column form fields, and manual-loading contract remain unchanged.

Validation run:

1. `./runproj exec --command "./runtests --rebuild-assets src/tests/test_frontend_asset_packaging.py"` passed, 11 tests.
2. `./runproj exec --command "./runtests src/tests/test_list_options.py"` passed, 9 tests.
3. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_list_options.py src/tests/playwright/test_filter_favourites.py"` passed, 19 tests.
4. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_filter_favourites.py src/tests/playwright/test_list_options.py src/tests/playwright/test_inline_editing.py src/tests/playwright/test_modal_crud.py src/tests/playwright/test_row_actions_menu.py src/tests/playwright/test_bulk_selection.py src/tests/playwright/test_tooltips.py"` passed, 45 tests.

### Phase 3.6 Bulk Actions Runtime Result

Phase 3.6 extracted bulk selection and bulk edit behaviour into `runtime/bulk-actions.js`:

1. `runtime/bulk-actions.js` owns row selection checkbox lookup, select-all state, shift-range selection, server selection persistence, stale selection request suppression, clear-selection handling, selection-aware extra-action button state, bulk edit queued/success selection clearing, and bulk form/delete button disabled state.
2. `powercrud.js` still owns the stable public entry and listener registration; bulk click/change/HTMX/body-event branches now delegate into the bulk actions runtime.
3. Generic form and button spinner helpers remain in `powercrud.js` because the spinner markup is shared presentation glue, while bulk-specific button disabling moved with the bulk runtime.
4. Public static paths, selector/data contracts, body event names, HTMX targets, modal success behaviour, and manual-loading contract remain unchanged.

Validation run:

1. `./runproj exec --command "./runtests --rebuild-assets src/tests/test_frontend_asset_packaging.py"` passed, 11 tests.
2. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_bulk_selection.py"` passed, 8 tests.
3. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_filter_favourites.py src/tests/playwright/test_list_options.py src/tests/playwright/test_inline_editing.py src/tests/playwright/test_modal_crud.py src/tests/playwright/test_row_actions_menu.py src/tests/playwright/test_bulk_selection.py src/tests/playwright/test_tooltips.py"` passed, 45 tests.

### Phase 3.7 Inline Edit Runtime Result

Phase 3.7 extracted inline edit and inline dependency behaviour into `runtime/inline-edit.js`:

1. `runtime/inline-edit.js` owns inline active-row state, width locking, focus restoration, Tom Select dropdown opening for inline fields, row hotkeys, dependency refresh, inline validation popovers, inline guard/result body events, and inline save spinner state.
2. `powercrud.js` still owns the stable public entry and listener registration; inline startup, click, keydown, HTMX, resize, scroll, and body-event branches now delegate into the inline edit runtime.
3. The saved-favourites runtime now receives the inline request classifier from the inline edit runtime, preserving the existing guard that prevents favourite UI work during inline edit interactions.
4. Public static paths, selector/data contracts, inline body event names, HTMX swap semantics, validation popover markers, and manual-loading contract remain unchanged.

Validation run:

1. `./runproj exec --command "./runtests --rebuild-assets src/tests/test_frontend_asset_packaging.py"` passed, 11 tests.
2. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_inline_editing.py src/tests/playwright/test_inline_dependencies.py"` passed, 10 tests.
3. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_filter_favourites.py src/tests/playwright/test_list_options.py src/tests/playwright/test_inline_editing.py src/tests/playwright/test_modal_crud.py src/tests/playwright/test_row_actions_menu.py src/tests/playwright/test_bulk_selection.py src/tests/playwright/test_tooltips.py"` passed, 45 tests.

### Phase 3.8 Current Template Runtime Result

Phase 3.8 completed the internal source split for the current public bundle:

1. `runtime/searchable-selects.js` owns Tom Select setup, native-select hiding/restoration, filter-favourite select normalisation, inline single-select dropdown sizing, and repeated searchable-select initialisation/destruction.
2. `runtime/current-template.js` owns DaisyUI/current-template presentation glue: modal cleanup and modal-box classes, Tippy tooltip setup, toolbar geometry, row-action floating menus, generic form/button spinners, list-column option visuals and placement, filter-favourite trigger/floating-panel presentation, selection-aware button visual state, bulk modal closing, and inline save spinner rendering.
3. `powercrud.js` remains the stable public entry and listener coordinator. The bundled/Vite path and manual module-script path remain unchanged.
4. Core feature modules keep owning semantics and state; current-template presentation hooks are injected into list columns, saved favourites, bulk actions, and inline edit.
5. Inline validation popovers intentionally remain in `runtime/inline-edit.js` for now because they were just isolated with the inline lifecycle and are covered by inline packaging/browser assertions.

Validation run:

1. `./runproj exec --command "./runtests --rebuild-assets src/tests/test_frontend_asset_packaging.py"` passed, 11 tests.
2. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_modal_crud.py src/tests/playwright/test_row_actions_menu.py src/tests/playwright/test_tooltips.py src/tests/playwright/test_list_options.py src/tests/playwright/test_bulk_selection.py src/tests/playwright/test_filter_favourites.py src/tests/playwright/test_inline_editing.py src/tests/playwright/test_inline_dependencies.py"` passed, 46 tests.
3. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_filter_favourites.py src/tests/playwright/test_list_options.py src/tests/playwright/test_inline_editing.py src/tests/playwright/test_modal_crud.py src/tests/playwright/test_row_actions_menu.py src/tests/playwright/test_bulk_selection.py src/tests/playwright/test_tooltips.py"` passed, 45 tests.

### Phase 4.0 Manual Static Asset Guard Result

Phase 4.0 added a persistent test-only manual-static sample path before changing lifecycle wiring:

1. `ManualStaticBookCRUDView` reuses the existing book sample configuration but renders through `sample/manual_static/base.html`.
2. The normal sample base remains Vite-backed through `django-vite` and the `config/static/js/main.js` manifest entry.
3. The manual-static base loads local HTMX, Tom Select, and Tippy assets from `node_modules` static paths, then loads `powercrud/css/powercrud.css` and `powercrud/js/powercrud.js` through normal Django static tags.
4. The manual-static smoke test asserts that the browser requests the stable module entry and follows its internal `powercrud/js/runtime/*.js` imports.
5. The test also asserts that the manual-static path does not request Vite dev assets or hard-coded `django_assets/powercrud-*.js` files.
6. The sample and test settings now use an absolute `/static/` URL and expose local `node_modules` assets under a `node_modules/` static prefix for deterministic manual-mode browser coverage.

Validation run:

1. `./runproj exec --command "./runtests src/tests/test_frontend_asset_packaging.py"` passed, 12 tests.
2. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_manual_static_assets.py"` passed, 1 test.
3. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_tooltips.py::test_searchable_select_and_tooltip_initializers_are_idempotent_after_htmx_refresh"` passed, 1 test.

### Phase 4.2 Shared Fragment Initializer Result

Phase 4.2 introduced the first shared lifecycle helper without changing listener ownership:

1. `initPowercrud(fragment = document)` now coordinates searchable-select setup, object-list bootstrap, and tooltip setup for a document or HTMX fragment.
2. `destroyPowercrudFragment(fragment)` now coordinates searchable-select teardown, tooltip teardown, and inline error-popover teardown before HTMX swaps remove content.
3. `window.initPowercrud` is exposed for manual fragment reinitialisation while the older public helper globals remain unchanged.
4. `DOMContentLoaded`, `pageshow`, `htmx:afterSwap`, and `htmx:afterSettle` now call the shared initializer where they previously repeated the same call cluster.
5. Once-only listener registration remains inside `installPowercrudStartup()`; centralising listener registration is still the next Phase 4 slice.

Validation run:

1. `./runproj exec --command "./runtests src/tests/test_frontend_asset_packaging.py"` passed, 13 tests.
2. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_manual_static_assets.py src/tests/playwright/test_tooltips.py src/tests/playwright/test_filter_favourites.py src/tests/playwright/test_inline_editing.py src/tests/playwright/test_inline_dependencies.py"` passed, 30 tests.

### Phase 4.3 Global Listener Registration Result

Phase 4.3 centralised once-only listener registration without moving feature semantics:

1. `runtime/startup.js` now exports `installPowercrudGlobalListeners(...)`.
2. Startup idempotency state now lives in `runtime/startup.js` and is keyed by document with separate style/listener installed flags.
3. `powercrud.js` keeps the feature-specific listener handler bodies in `createPowercrudGlobalListenerHandlers()`.
4. `installPowercrudStartup()` now assembles the handler object and delegates registration to the startup helper.
5. Existing event names, event targets, registration order, capture/bubble options, and the two separate `htmx:beforeRequest` listeners were preserved.

Validation run:

1. `./runproj exec --command "./runtests --rebuild-assets src/tests/test_frontend_asset_packaging.py"` passed, 14 tests.
2. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_manual_static_assets.py src/tests/playwright/test_tooltips.py src/tests/playwright/test_filter_favourites.py src/tests/playwright/test_list_options.py src/tests/playwright/test_row_actions_menu.py src/tests/playwright/test_bulk_selection.py src/tests/playwright/test_inline_editing.py src/tests/playwright/test_inline_dependencies.py src/tests/playwright/test_modal_crud.py"` passed, 47 tests.

### Phase 4.4 Repeated Init Idempotency Result

Phase 4.4 hardened same-DOM repeated initialisation:

1. Bulk-selection hydration moved behind `bulkActions.hydrateRenderedSelectionState(root)`.
2. Row and select-all checkboxes now copy server-rendered `data-powercrud-initial-*` state only once per element.
3. New HTMX-swapped markup still hydrates from rendered state because new checkbox elements do not carry the hydration marker.
4. Repeated `window.initPowercrud(document)` now preserves live same-DOM row selection, bulk counter visibility, and select-all indeterminate state.
5. Manual-static coverage now also checks repeated `window.initPowercrud(document)` for Tom Select wrapper count, tooltip availability, and duplicate startup style prevention.

Validation run:

1. `./runproj exec --command "./runtests --rebuild-assets src/tests/test_frontend_asset_packaging.py"` passed, 14 tests.
2. `./runproj exec --command "./runtests --playwright src/tests/playwright/test_manual_static_assets.py src/tests/playwright/test_bulk_selection.py src/tests/playwright/test_tooltips.py src/tests/playwright/test_filter_favourites.py src/tests/playwright/test_list_options.py src/tests/playwright/test_inline_editing.py src/tests/playwright/test_inline_dependencies.py"` passed, 44 tests.

### Phase 4 Closeout

Phase 4 is complete. The current runtime now has:

1. A manual-static sample smoke path that proves the stable module entry works without the Vite sample base.
2. A shared `initPowercrud(fragment)` initializer for per-fragment searchable-select, object-list, and tooltip setup.
3. A shared fragment teardown helper for HTMX before-swap cleanup.
4. Once-only listener registration centralised in `runtime/startup.js` with document-keyed idempotency guards.
5. Same-DOM repeated-init hardening for rendered bulk-selection state.

Phase 4 intentionally did not create `initPowercrudPack(fragment)` or move code into a template-pack app. The lifecycle boundary is now clearer enough for a future pack initializer, but proving the shared-versus-pack JavaScript boundary remains Phase 6 work. Phase 5 later reduced cross-control coupling with narrow state helpers rather than a broad state-management abstraction.

## Phase 1 Classification Table

| Behaviour area | Classification | Rationale |
| --- | --- | --- |
| Runtime shell and public globals | Core | The bundle guard and exported helpers are public runtime assumptions that should stay stable during cleanup. |
| HTMX lifecycle and fragment initialisation | Core | Refresh and swap semantics are PowerCRUD runtime behaviour, even though the current wiring is not yet centralised. |
| Searchable selects / Tom Select | Boundary/unclear | PowerCRUD owns the opt-in `data-powercrud-searchable-*` contract; Tom Select setup, dropdown sizing, and styling glue are presentation-sensitive. |
| Tooltips / Tippy | Boundary/unclear | Tooltip semantics may be core, but Tippy instances, theme, placement, and rendered visual treatment belong near pack-specific JS. |
| Filter panel open/closed state | Boundary/unclear | Persisting panel state is core-ish; `#filterCollapse`, `hidden`, labels, and tooltip refreshes are current-template details. |
| Optional filters and filter value refresh | Core | Visible-filter state, filter form values, and list refresh semantics are durable PowerCRUD behaviour. |
| Page size and current view state | Core | Capturing/restoring query state for filters, page size, and visible columns is stable runtime behaviour. |
| Saved favourites state | Boundary/unclear | Favourite state comparison and dirty tracking are core; floating panel UI, icon toggles, `dropdown-open`, and tooltip labels are DaisyUI/current-template details. |
| Reset view | Core | Resetting stored filters, page size, visible columns, and favourite state is a cross-feature PowerCRUD operation. |
| List-column chooser | Boundary/unclear | Visible-column persistence and last-column guard are core; `<details>` dropdown lifecycle and placement are current DaisyUI presentation. |
| Toolbar layout and width sync | DaisyUI-specific | Runtime geometry exists to fit current DaisyUI toolbar, filter panel, and table markup. |
| Row action menus | Boundary/unclear | Row actions are core semantics; cloned floating menu markup, placement, and menu styling are presentation-specific. |
| Bulk selection | Core | Selection state, counters, select-all, shift ranges, and server persistence are durable PowerCRUD behaviour. |
| Bulk edit | Boundary/unclear | Bulk result semantics are core; modal closing, spinners, and disabled visual classes are current DaisyUI behaviour. |
| Inline edit lifecycle | Core | Active row state, row swaps, guards, focus, save/cancel, and dependency semantics are PowerCRUD runtime behaviour. |
| Inline error popovers | Boundary/unclear | Error payloads are core; runtime popover DOM, classes, and placement are presentation-specific. |
| Inline dependencies | Core | Parent/child field refresh semantics are driven by neutral `data-inline-*` contracts. |
| Modal handling | DaisyUI-specific | The implementation depends on `<dialog>`, `showModal()`, `modal-box`, and per-trigger modal-box classes. |
| Form and button spinners | DaisyUI-specific | Spinner markup uses DaisyUI loading classes and button content replacement. |

## Behaviour Areas To Preserve

The cleanup must preserve these behaviours:

1. HTMX refresh and partial-swap initialisation.
2. Filter panel open/closed state.
3. Optional filters and reset filters.
4. Saved favourites selection, dirty state, update, delete, and reset view.
5. Session-backed current view state for filters, page size, and visible columns.
6. List-column chooser save, reset, last-column guard, draft reset, and placement.
7. Top action `extra_buttons_mode`.
8. Row action menus.
9. Bulk selection and bulk edit.
10. Inline edit, including hidden list columns.
11. Modal handling.
12. Tooltips and overflow/semantic tooltip reinitialisation.

## Testing Notes

This work should lean heavily on existing Playwright tests because most risk is interaction risk rather than pure unit behavior.

Useful focused suites include:

1. `src/tests/playwright/test_filter_favourites.py`
2. `src/tests/playwright/test_list_options.py`
3. `src/tests/playwright/test_inline_editing.py`
4. `src/tests/playwright/test_inline_dependencies.py`
5. `src/tests/playwright/test_bulk_selection.py`
6. `src/tests/playwright/test_row_actions_menu.py`
7. `src/tests/playwright/test_tooltips.py`

Server-side tests should still cover rendered attributes and configuration contracts, but browser tests are the primary protection against regressions in this slice.

## Non-Goals For The First Cleanup Slice

The first cleanup slice should not:

1. Create a new template-pack app.
2. Change the documented public API.
3. Change template names or override points.
4. Replace HTMX, Tom Select, Tippy, or DaisyUI.
5. Redesign the list-toolbar UX.
6. Convert everything to a large framework abstraction in one pass.

The first success condition is a less fragile current runtime, not a completed template-pack architecture.
