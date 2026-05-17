# PowerCRUD JavaScript Behaviour Inventory

## Purpose

This is a Phase 1 inventory of `src/powercrud/static/powercrud/js/powercrud.js`. It maps the current runtime by behaviour area before any JavaScript cleanup or template-pack extraction starts.

The classifications here are planning labels only:

- Core: PowerCRUD runtime behaviour tied to stable semantics and neutral `data-*` contracts.
- DaisyUI-specific: behaviour tied to current DaisyUI markup, classes, modal APIs, geometry, or visual conventions.
- Boundary/unclear: behaviour that mixes durable PowerCRUD semantics with current DaisyUI presentation.

## Runtime Shell

| Area | Current behaviour | Classification | Notes |
| --- | --- | --- | --- |
| Guarded runtime load | The file is a single IIFE guarded by `window.__powercrudRuntimeLoaded`. | Core | This protects against duplicate listener registration while the public bundle remains a single file. |
| Dependency lookup | Looks up `window.htmx`, `window.tippy`, and `window.TomSelect`, warning once if missing. | Boundary/unclear | The warning and dependency shape are core runtime concerns, but specific libraries are current-pack assumptions. |
| Public globals | Exposes `getCurrentFilters`, searchable-select lifecycle helpers, tooltip lifecycle helpers, and `powercrudToggleFavouriteSaveForm` on `window`. | Core | Preserve this surface during cleanup unless a later public API decision explicitly changes it. |
| Shared root state | Uses `WeakMap` state per object-list root and module-level active-panel/menu/tooltip state. | Core | State ownership is central to future lifecycle cleanup. |

## Behaviour Areas

| Behaviour area | Current behaviour | Classification | Boundary notes |
| --- | --- | --- | --- |
| HTMX lifecycle and fragment initialisation | Processes initial DOM, destroys widgets before swaps, reinitialises searchable selects, object lists, tooltips, inline rows, and remembered view state after swaps and settles. | Core | Current implementation is once-only global listeners plus repeated per-fragment lifecycle calls, but no single `initPowercrud(fragment)` yet. |
| Searchable selects | Enhances `data-powercrud-searchable-select` and `data-powercrud-searchable-multiselect` native selects with Tom Select; syncs disabled/value state; hides/restores native selects; special-cases inline and favourites selects. | Boundary/unclear | The `data-powercrud-*` opt-in contract is core-ish. Tom Select setup, dropdown placement, clear button, and wrapper class normalisation are pack/presentation concerns. |
| Tooltips | Creates, destroys, hides, and refreshes Tippy tooltips for semantic, semantic-cell, and overflow targets. | Boundary/unclear | Tooltip meaning can be core, but Tippy, theme, placement, and visual rendering belong near pack JS. |
| Filter panel | Toggles `#filterCollapse`, persists panel state, updates labels/tooltips, shows add-filter and favourites controls, and initialises selects when the panel opens. | Boundary/unclear | Filter open/closed semantics and persistence are core. `hidden`, button labels, and tooltip treatment are DaisyUI/current-template details. |
| Optional filters | Tracks visible filters in rendered hidden inputs and local storage, restores optional visibility, adds/removes optional fields, and refreshes the list. | Core | Mostly stable semantics around `visible_filters`, with current form IDs as a contract to document before extraction. |
| Filter value refresh | Schedules HTMX list refreshes from filter input/change events and removes empty fields on submit. | Core | Bound to `#filter-form`, root list URL, and request-preserving behaviour. |
| Page size and current view state | Captures/restores query-string state for filters, page size, and visible columns through session storage. | Core | Depends on stable root/list URL semantics and the page-size select contract. |
| Saved favourites | Tracks selected and dirty favourite state, compares favourite JSON against current list state, opens a floating management panel, applies favourites through HTMX, and responds to saved/updated/deleted events. | Boundary/unclear | State capture/comparison is core. Floating panel geometry, icon toggles, `dropdown-open`, tooltip labels, and Tom Select handling are current presentation. |
| Reset view | Clears stored view state, optional filters, favourite selection, and list-column state, then refreshes via HTMX or falls back to navigation. | Core | Tightly couples filters, favourites, and columns. This is a dependency hotspot. |
| List-column chooser | Enforces at least one visible column, resets unchecked draft state on close, focuses first checkbox, and flips chooser placement based on viewport. | Boundary/unclear | Visible-column semantics are core; `<details>` dropdown behaviour and placement data are DaisyUI/current-template concerns. |
| Toolbar layout | Measures table width, applies toolbar/filter-panel widths, and marks wrapped toolbar state. | DaisyUI-specific | Runtime geometry exists to fit current DaisyUI toolbar/table markup. |
| Row action menus | Clones hidden row-action template content into a fixed body-level floating panel, processes HTMX on it, initialises tooltips, positions it, and closes it on global interactions. | Boundary/unclear | Action semantics are core. Floating menu cloning, viewport placement, and menu classes are pack-specific. |
| Bulk selection | Maintains select-all/row-selection state, shift-range selection, counters, selection-aware button disabled state, optimistic clear, and persistence to the server through HTMX. | Core | Some disabled classes/tooltips are DaisyUI-specific, but selection semantics are core. |
| Bulk edit | Starts/stops form and button spinners, disables bulk buttons, closes modals after success, clears selection after queued/success events, and preserves active filters on refresh. | Boundary/unclear | Bulk result semantics are core; modal close, spinners, and button classes are pack-specific. |
| Inline edit | Owns active row state, width locking, focus, hotkeys, save/cancel guards, inline event handling, error popovers, and row refresh. | Core | Lifecycle semantics are core. Popover classes, spinners, and layout geometry are boundary/presentation details. |
| Inline dependencies | Maps parent controls to dependent inline widgets and refreshes child widgets through HTMX when parent fields change. | Core | Core semantics as long as the `data-inline-*` dependency attributes stay neutral. |
| Modal handling | Cleans duplicate modal elements and applies per-trigger modal-box classes before a DaisyUI dialog opens. | DaisyUI-specific | Directly tied to `<dialog>`, `showModal()`, `modal-box`, and per-trigger class strings. |
| Form/button spinners | Replaces button contents with DaisyUI loading-spinner markup during object, bulk, and inline requests. | DaisyUI-specific | Visual treatment should move toward pack ownership later. |

## Public Bundle Assumptions To Preserve

- Keep the single public static bundle path unless a later phase explicitly changes it.
- Keep `window.__powercrudRuntimeLoaded` duplicate-load guard behaviour.
- Keep current global helpers available: `getCurrentFilters`, `initPowercrudSearchableSelects`, `destroyPowercrudSearchableSelects`, `initPowercrudTooltips`, `hidePowercrudTooltips`, `destroyPowercrudTooltips`, and `powercrudToggleFavouriteSaveForm`.
- Keep existing template includes, inline handlers, custom events, and HTMX trigger semantics unchanged during Phase 1 and any later source-only cleanup.

