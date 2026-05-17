# PowerCRUD JavaScript Selector And Contract Map

## Purpose

This map records the selectors, attributes, storage keys, globals, and events used by `powercrud.js`. It is grouped by behaviour area so later cleanup can separate stable PowerCRUD contracts from DaisyUI/current-template assumptions.

## Core Shell And Object Lists

| Contract | Used for | Owner classification |
| --- | --- | --- |
| `data-powercrud-object-list="true"` | Root list scope for most behaviours. | Core |
| `data-powercrud-list-url` | List refresh URL and storage-key source. | Core |
| `data-powercrud-original-target` | Chooses inner versus outer swap target. | Core |
| `#filtered_results` | Table/list refresh target and toolbar measurement source. | Boundary/unclear |
| `window.__powercrudRuntimeLoaded` | Once-only bundle guard. | Core |
| `window.getCurrentFilters` | Public helper for current filter query state. | Core |

## Searchable Selects

| Contract | Used for | Owner classification |
| --- | --- | --- |
| `data-powercrud-searchable-select="true"` | Opt in a single-select field for Tom Select enhancement. | Boundary/unclear |
| `data-powercrud-searchable-multiselect="true"` | Opt in a multiselect field for Tom Select enhancement. | Boundary/unclear |
| `data-powercrud-searchable-placeholder` | Tom Select placeholder. | Boundary/unclear |
| `data-powercrud-favourite-select="true"` | Special handling for the favourites selector. | Boundary/unclear |
| `data-powercrud-native-tabindex` / `data-powercrud-native-style` | Internal native-select restore state. | Core |
| `.powercrud-filter-favourite-select*`, `.powercrud-inline-single-dropdown`, `.clear-button` | Current Tom Select styling and clear affordance. | DaisyUI-specific |
| `window.initPowercrudSearchableSelects` / `window.destroyPowercrudSearchableSelects` | Public lifecycle hooks. | Core |

## Tooltips

| Contract | Used for | Owner classification |
| --- | --- | --- |
| `data-powercrud-tooltip="semantic"` | Always attach semantic tooltip. | Boundary/unclear |
| `data-powercrud-tooltip="semantic-cell"` | Attach semantic list-cell tooltip. | Boundary/unclear |
| `data-powercrud-tooltip="overflow"` | Attach only when rendered text overflows. | Boundary/unclear |
| `data-tippy-content` | Tooltip text. | Boundary/unclear |
| `data-tippy-root`, Tippy `_tippy` instance | Tippy runtime state and rendered tooltip checks. | DaisyUI-specific |
| `window.initPowercrudTooltips`, `window.hidePowercrudTooltips`, `window.destroyPowercrudTooltips` | Public lifecycle hooks. | Core |

## Filters, Page Size, And View State

| Contract | Used for | Owner classification |
| --- | --- | --- |
| `#filter-form` | Filter form discovery and HTMX request path rewriting. | Core |
| `#filterCollapse` | Filter panel open/closed state. | Boundary/unclear |
| `data-powercrud-filter-toggle` | Filter panel toggle button. | Boundary/unclear |
| `data-powercrud-filter-form="true"` | Submit cleanup for filter forms. | Core |
| `data-powercrud-add-filter-container` | Add-filter UI visibility and select initialisation. | Boundary/unclear |
| `data-powercrud-add-filter-select` | Optional-filter add trigger. | Core |
| `data-powercrud-remove-filter` | Optional-filter remove trigger and field name. | Core |
| `data-powercrud-visible-filters-state` | Hidden state container for persisted optional filters. | Core |
| `visible_filters` | Query/form parameter for visible optional filters. | Core |
| `data-powercrud-page-size-select="true"` | Page-size refresh trigger. | Core |
| `powercrud:filter-panel:*` | Session key for filter panel open state. | Boundary/unclear |
| `powercrud:visible-filters:*` | Local-storage key for optional filters. | Core |
| `powercrud:view-state:*` | Session key for current query/view state. | Core |

## Saved Favourites

| Contract | Used for | Owner classification |
| --- | --- | --- |
| `data-powercrud-filter-favourites-toolbar="true"` | Saved-favourites toolbar root. | Boundary/unclear |
| `data-powercrud-filter-favourites-view-key` | Explicit storage key scope for favourites/view state. | Core |
| `data-powercrud-filter-favourites-dropdown="true"` | Current DaisyUI dropdown shell. | DaisyUI-specific |
| `data-powercrud-filter-favourites-trigger="true"` | Opens the floating favourites panel. | Boundary/unclear |
| `data-powercrud-filter-favourites-template="true"` | Hidden template copied to floating panel. | DaisyUI-specific |
| `data-powercrud-filter-favourites-panel="true"` | Favourites panel content root. | Boundary/unclear |
| `data-powercrud-filter-favourites-floating-panel="true"` | Body-level floating panel marker. | DaisyUI-specific |
| `data-powercrud-filter-favourites-trigger-label="true"` | Trigger label sync. | DaisyUI-specific |
| `data-powercrud-filter-favourites-icon-outline="true"` / `data-powercrud-filter-favourites-icon-filled="true"` | Icon visibility/state toggles. | DaisyUI-specific |
| `data-powercrud-filter-favourites-selected` / `data-powercrud-filter-favourites-dirty` | Trigger state attributes. | Boundary/unclear |
| `data-powercrud-favourite-state-json` | Saved favourite comparable state payload. | Core |
| `data-powercrud-favourite-visible-filters` | Saved optional-filter set. | Core |
| `data-powercrud-favourite-select="true"` | Favourite selector. | Boundary/unclear |
| `data-powercrud-favourite-manage-action="true"` | Guard update/delete/apply controls. | Core |
| `data-powercrud-favourite-apply="true"` | Apply validation and label sync. | Core |
| `data-powercrud-favourite-save-form="true"` | Inline favourite-save form population/toggle. | Boundary/unclear |
| `data-powercrud-reset-view="true"` | Reset filters/page size/columns/favourite state. | Core |
| `current_state_json`, `state_json`, `selected_favourite_id`, `favourite_id`, `list_view_url`, `toolbar_dom_id` | Form fields used by favourite endpoints. | Core |
| `powercrud:selected-filter-favourite:*` | Session key for selected favourite. | Core |
| `powercrud:selected-filter-favourite-dirty:*` | Session key for dirty selected favourite. | Core |
| `powercrud:favourite-saved`, `powercrud:favourite-updated`, `powercrud:favourite-deleted` | Body events from favourite endpoint responses. | Core |

## List Columns And Toolbar

| Contract | Used for | Owner classification |
| --- | --- | --- |
| `data-powercrud-list-columns="true"` | List-column chooser root. | Boundary/unclear |
| `data-powercrud-list-column-checkbox="true"` | Visible-column checkbox. | Core |
| `data-powercrud-list-column-option="true"` | Option container for disabled visual state. | DaisyUI-specific |
| `data-powercrud-list-columns-panel="true"` | Chooser panel placement. | DaisyUI-specific |
| `data-powercrud-list-columns-trigger="true"` | Chooser trigger focus and tooltip. | Boundary/unclear |
| `data-powercrud-initial-checked` | Draft reset to server-rendered visible-column state. | Core |
| `data-powercrud-last-visible-column` | Last visible column guard marker. | Core |
| `data-powercrud-list-columns-placement` | Runtime placement marker. | DaisyUI-specific |
| `data-powercrud-list-toolbar="true"` | Toolbar width/wrap calculations. | DaisyUI-specific |
| `data-powercrud-action-controls` / `data-powercrud-view-controls` | Toolbar wrap detection. | DaisyUI-specific |
| `data-powercrud-toolbar-wrapped` | Runtime wrapped-state marker. | DaisyUI-specific |
| `visible_columns`, `list_columns_action` | Form fields for server-side visible-column persistence/reset. | Core |

## Row Actions

| Contract | Used for | Owner classification |
| --- | --- | --- |
| `data-powercrud-row-actions-dropdown="true"` | Row action dropdown root. | Boundary/unclear |
| `data-powercrud-row-actions-trigger="true"` | Opens/closes floating action menu. | Boundary/unclear |
| `data-powercrud-row-actions-template="true"` | Hidden row-action menu template. | DaisyUI-specific |
| `data-powercrud-row-actions-floating-panel="true"` | Body-level cloned menu marker. | DaisyUI-specific |
| `data-powercrud-row-actions-panel="true"` | Menu panel root. | DaisyUI-specific |
| `data-inline-action` | Action semantics and inline action identification. | Core |

## Bulk Selection And Bulk Edit

| Contract | Used for | Owner classification |
| --- | --- | --- |
| `data-powercrud-select-all="true"` | Select-all checkbox. | Core |
| `data-powercrud-row-select="true"` | Row selection checkbox. | Core |
| `data-powercrud-initial-checked` / `data-powercrud-initial-indeterminate` | Server-rendered selection baseline. | Core |
| `data-powercrud-shift-range` / `data-powercrud-skip-selection-request` | Internal shift-range request suppression. | Core |
| `data-powercrud-selection-request-pending` / `data-powercrud-selection-request-version` | Internal stale request guard. | Core |
| `data-powercrud-bulk-actions="true"` / `#bulk-actions-container` | Bulk action toolbar visibility. | Boundary/unclear |
| `#selected-items-counter` | Selected count display. | Boundary/unclear |
| `data-powercrud-selection-aware="true"` | Disable action controls based on selection count. | Core |
| `data-powercrud-selection-min-count`, `data-powercrud-selection-min-behavior`, `data-powercrud-selection-min-reason` | Selection-aware action requirements. | Core |
| `data-powercrud-clear-selection` | Clear selected rows. | Core |
| `data-powercrud-form="bulk"` / `#bulk-edit-form` | Bulk form spinner and button disabling. | Boundary/unclear |
| `data-powercrud-bulk-delete-submit` / `#confirm-delete-button` / `#confirm-delete-checkbox` | Bulk-delete confirmation state. | Boundary/unclear |
| `bulkEditSuccess`, `bulkEditQueued` | Body events for bulk result handling. | Core |
| `refreshTable` | Body event that refreshes list results. | Core |

## Inline Edit And Dependencies

| Contract | Used for | Owner classification |
| --- | --- | --- |
| `table[data-inline-enabled="true"]` | Inline-enabled table root. | Core |
| `tr[data-inline-row="true"]` | Inline row root. | Core |
| `data-inline-active="true"` | Active inline row marker. | Core |
| `data-inline-row-url` | Row refresh/cancel URL. | Core |
| `data-inline-status` | Inline row blocked status. | Core |
| `.inline-edit-trigger` | Opens inline editing. | Boundary/unclear |
| `data-inline-field` | Field name for focus and dependency mapping. | Core |
| `data-inline-cell="true"` | Inline-editable cell marker. | Core |
| `data-inline-actions="true"` | Inline action cell. | Boundary/unclear |
| `data-inline-save` / `data-inline-cancel` | Save/cancel controls. | Core |
| `.inline-field-widget` | Inline widget root. | Boundary/unclear |
| `data-inline-dependent="true"` | Dependent field marker. | Core |
| `data-inline-depends-on` | Parent field names for dependency refresh. | Core |
| `data-inline-endpoint` | Dependency refresh endpoint. | Core |
| `data-inline-refreshing="true"` | Internal refreshing marker. | Core |
| `data-inline-field-error="true"` | Field error widget marker. | Core |
| `data-inline-error-field`, `data-inline-error-label`, `data-inline-error-message` | Error popover payload. | Core |
| `data-inline-error-text="true"` / `data-inline-error-text-hidden` | Inline error text visibility state. | Boundary/unclear |
| `data-powercrud-inline-error-popover="true"` | Runtime error popover marker. | DaisyUI-specific |
| `inline-row-locked`, `inline-row-forbidden`, `inline-row-saved`, `inline-row-error` | Body events for inline guards/results. | Core |

## Modals, Spinners, And Visual Classes

| Contract | Used for | Owner classification |
| --- | --- | --- |
| `data-powercrud-modal` | Shared modal dialog discovery and cleanup. | DaisyUI-specific |
| `data-powercrud-modal-trigger="true"` | Per-trigger modal-box class application. | DaisyUI-specific |
| `data-powercrud-modal-box` | Modal box class target. | DaisyUI-specific |
| `data-powercrud-modal-box-classes` | Per-trigger modal-box class override. | DaisyUI-specific |
| `data-powercrud-default-modal-box-classes` | Default modal-box class restore source. | DaisyUI-specific |
| `#powercrudBaseModal`, `#powercrudModalContent` | Current shared modal IDs. | DaisyUI-specific |
| `data-powercrud-form="object"` | Object form spinner lifecycle. | Boundary/unclear |
| `data-form-save` | Object/bulk save button spinner target. | Boundary/unclear |
| `modal-box`, `dropdown-open`, `hidden`, `btn-disabled`, `opacity-50`, `pointer-events-none`, `text-primary`, `text-warning`, `loading loading-spinner` | Current DaisyUI visual state classes. | DaisyUI-specific |

