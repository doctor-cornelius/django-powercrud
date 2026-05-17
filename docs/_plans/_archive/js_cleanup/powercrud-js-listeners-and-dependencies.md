# PowerCRUD JavaScript Listener And Dependency Map

## Purpose

This map separates once-only global listeners from repeated per-fragment initialisation, then records the main cross-feature dependencies inside `powercrud.js`.

## Once-Only Page Listeners

All listeners below are registered once by the guarded bundle. They are global page listeners, not per-fragment listeners.

| Listener | Behaviour areas | Notes |
| --- | --- | --- |
| `DOMContentLoaded` | Initial HTMX processing, searchable selects, object lists, tooltips, inline row bootstrap. | Current closest equivalent to full-page `initPowercrud(document)`. |
| `pageshow` | Object lists and tooltips. | Handles browser history/restored page state. |
| `pagehide` | Tooltips, row actions, list-column chooser, favourites dropdowns. | Global cleanup before navigation/cache. |
| Capturing `pointerdown` | Tooltips. | Hides active tooltips before pointer interactions. |
| Capturing `click` | Tooltips. | Defers tooltip hiding until click handling completes. |
| Capturing `click` for inline cancel | Inline edit. | Destroys inline field error popovers on cancel. |
| Capturing `click` for modal classes | Modals. | Applies per-trigger modal-box classes before inline `showModal()` handlers run. |
| Capturing `focusin` | Tooltips. | Hides tooltips when focus moves outside tooltip triggers. |
| Delegated `click` | Filters, row actions, favourites, reset view, reset filters, optional filters, bulk clear, global dropdown/menu close. | Highest-coupling listener. It mixes core actions with presentation dismissal. |
| Capturing `toggle` | List-column chooser. | Syncs last-column guard, placement, focus, and draft reset for `<details>`. |
| `keydown` | Inline edit, list columns, favourites, row actions. | Escape closes or clears active UI. |
| Capturing `scroll` on document | Row actions. | Closes floating row-action menu. |
| Capturing `click` on row checkbox | Bulk selection. | Prepares shift-range suppression before checkbox change. |
| Capturing `mousedown` on row checkbox | Bulk selection. | Prevents text selection during shift-range selection. |
| Delegated `change` | Bulk selection, list columns, optional filters, page size, favourites. | Second highest-coupling listener. |
| Delegated `input` | Filter refresh. | Schedules debounced filter refresh. |
| Delegated `change` for filter fields | Filter refresh. | Schedules immediate filter refresh. |
| Capturing `submit` | Filter form, object form, bulk form. | Removes empty filter fields and starts spinners. |
| `htmx:beforeRequest` | Tooltips, filters, selection, bulk delete, favourites dirty/guard state. | First of two `beforeRequest` listeners. |
| `htmx:configRequest` | Filters, favourites. | Rewrites filter request path and injects current favourite state. |
| Body `bulkEditSuccess` | Bulk edit, modals, selection. | Closes modals, removes duplicate modals, clears selection. |
| Body `bulkEditQueued` | Bulk edit, selection. | Clears selection after queued edit. |
| Body `powercrud:favourite-saved` | Favourites. | Stores selected favourite and closes panels. |
| Body `powercrud:favourite-updated` | Favourites. | Stores updated favourite and closes panels. |
| Body `powercrud:favourite-deleted` | Favourites. | Clears selected favourite and closes panels. |
| Body `refreshTable` | List refresh. | Refreshes current object list. |
| `htmx:beforeSwap` | Tooltips, searchable selects, inline edit, selection. | Destroys per-fragment widgets and blocks stale selection swaps. |
| `htmx:afterSwap` | Searchable selects, object lists, tooltips, favourites panels/forms, inline edit. | Reinitialises fragments and repairs active inline/favourite UI. |
| `htmx:afterSettle` | Searchable selects, object lists, tooltips, inline popovers, current view state. | Second lifecycle pass after DOM settles. |
| `htmx:beforeRequest` | Inline edit. | Second `beforeRequest` listener for inline save/cancel/guard logic. |
| `htmx:afterRequest` | Selection, forms, bulk delete, inline save. | Clears pending state and stops spinners. |
| `htmx:responseError` | Selection, forms, bulk delete, inline widgets. | Clears pending state after failed HTMX responses. |
| Body `inline-row-locked` | Inline edit. | Refreshes or focuses affected row. |
| Body `inline-row-forbidden` | Inline edit. | Refreshes or focuses affected row. |
| Body `inline-row-saved` | Inline edit. | Clears inline error popovers. |
| Body `inline-row-error` | Inline edit. | Focuses errored row and shows popovers. |
| `resize` on window | Row actions, toolbar, inline error popovers, tooltips. | Geometry refresh and floating UI cleanup. |
| Capturing `scroll` on window | Inline edit. | Repositions inline field error popovers. |

## Per-Fragment Initialisation

These functions are called repeatedly for `document` or HTMX swap roots. Later cleanup should centralise this shape without changing behaviour.

| Initialiser | Current callers | Behaviour |
| --- | --- | --- |
| `initPowercrudSearchableSelects(root)` | `DOMContentLoaded`, filter-panel open, favourites panel open, `htmx:afterSwap`, `htmx:afterSettle`. | Enhances eligible selects and avoids re-enhancing existing Tom Select instances. |
| `destroyPowercrudSearchableSelects(root)` | `htmx:beforeSwap`. | Destroys Tom Select instances before swapped DOM is replaced. |
| `initPowercrudTooltips(root)` | `DOMContentLoaded`, `pageshow`, row actions open, favourites panel open, `htmx:afterSwap`, `htmx:afterSettle`, resize timer. | Recreates tooltip instances and skips non-overflowing overflow targets. |
| `destroyPowercrudTooltips(root)` | `htmx:beforeSwap`. | Destroys Tippy instances before DOM removal. |
| `bootstrapObjectLists(scope)` | `DOMContentLoaded`, `pageshow`, `htmx:afterSwap`, `htmx:afterSettle`. | Applies filter panel state, optional filter state, current view state, favourites state, bulk selection state, list-column chooser state, and toolbar widths. |
| `bootstrapInlineRow()` | `DOMContentLoaded`. | Repairs active inline row on full page load. Inline swap handling is otherwise in HTMX listeners. |
| `showInlineFieldErrorPopovers(root)` | Inline `afterSwap`, `afterSettle`, and inline error events. | Creates runtime popovers for inline validation errors. |
| `rememberCurrentViewState(root)` | `htmx:afterSettle` and favourites selection changes. | Captures current query/view state after list updates. |

## Dependency Map

| Source behaviour | Updates or depends on | Why it matters |
| --- | --- | --- |
| Filter value changes | HTMX list refresh, favourites dirty state, current view state, tooltip refresh. | A filter change can alter saved-favourite state, URL/query state, table rows, and tooltip targets. |
| Optional filter add/remove | Visible-filter storage, filter form DOM, favourites dirty state, HTMX refresh. | Optional filter visibility is both user preference and favourite state. |
| Page-size changes | HTMX list refresh, current view state, favourites dirty state. | Page size is part of current/favourite state but coverage is thinner than filter changes. |
| Saved favourite selection | Optional-filter storage, filter values, visible columns, current view state, HTMX list refresh, trigger tooltip/icon state. | One favourite apply can update multiple feature areas. |
| Saved favourite save/update/delete events | Session selected favourite, dirty state, panel state, toolbar labels. | Server HX events mutate browser-side favourite state. |
| Reset view | Stored view state, filter panel state, optional filters, favourite selection, list-column reset, HTMX refresh. | Highest-impact cross-feature operation. |
| List-column chooser | Server visible columns, current view state, favourite state, inline table assumptions. | Hidden columns can affect inline edit and saved favourites. |
| Toolbar geometry | Filter panel width, list toolbar width, column chooser placement. | Presentation-only code depends on the current table DOM. |
| Row action menu | HTMX processing, tooltips, modal/action links, global close listeners. | Floating cloned markup crosses template, HTMX, tooltip, and modal boundaries. |
| Bulk selection | Select-all state, row checkboxes, counters, selection-aware buttons, server selection state. | Selection changes drive both visible UI and server state. |
| Bulk edit success/queued | Modal close, selection clear, table refresh. | Core operation result currently performs DaisyUI modal cleanup too. |
| Inline edit open/save/cancel | Active row state, table width lock, Tom Select values, dependency refresh, inline popovers, HTMX row swaps. | Largest lifecycle subsystem; cleanup should isolate it carefully. |
| Inline dependency refresh | Parent controls, child widget endpoint, Tom Select sync, error popovers. | Core dependency semantics depend on current inline widget structure. |
| Tooltip lifecycle | HTMX swaps, toolbar labels, row action/favourites panels, resize/pointer/focus listeners. | Tooltips are touched by nearly every presentation area. |
| Modal class application | Trigger click order, shared modal, per-trigger class attributes. | DaisyUI-specific behaviour must run before inline `showModal()` handlers. |

## Phase 1 Risk Notes

- The two `htmx:beforeRequest` listeners split core list/favourites/bulk handling from inline handling. A later cleanup should make that split intentional before moving code.
- `bootstrapObjectLists(document)` is called after fragment-level initialisation to resynchronise global list state; this may be needed for shell-level HTMX navigation and should not be removed casually.
- Favourites, current view state, optional filters, and visible columns are tightly coupled. Treat them as a coordinated state area even if source files are later split.
- Most global listeners are once-only page listeners. The repeated work is in the functions called from HTMX lifecycle events, not in listener registration.

