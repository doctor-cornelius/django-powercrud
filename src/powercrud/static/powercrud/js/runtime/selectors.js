export const SEARCHABLE_SELECT_ATTR = 'data-powercrud-searchable-select';
export const SEARCHABLE_MULTISELECT_ATTR = 'data-powercrud-searchable-multiselect';
export const NATIVE_TABINDEX_ATTR = 'data-powercrud-native-tabindex';
export const NATIVE_STYLE_ATTR = 'data-powercrud-native-style';
export const OBJECT_LIST_ROOT_SELECTOR = '[data-powercrud-object-list="true"]';
export const TOOLTIP_TRIGGER_SELECTOR = '[data-powercrud-tooltip][data-tippy-content]';
export const LIST_COLUMNS_SELECTOR = '[data-powercrud-list-columns="true"]';
export const LIST_COLUMN_CHECKBOX_SELECTOR = '[data-powercrud-list-column-checkbox="true"]';
export const LIST_TOOLBAR_SELECTOR = '[data-powercrud-list-toolbar="true"]';
export const PAGINATION_SELECTOR = '[data-powercrud-pagination="true"]';
export const VIEW_HELP_SELECTOR = '[data-powercrud-view-help="true"]';
export const INLINE_ROW_SELECTOR = 'tr[data-inline-row="true"]';
export const INLINE_TABLE_SELECTOR = 'table[data-inline-enabled="true"]';
export const INLINE_FIELD_ERROR_SELECTOR = '[data-inline-field-error="true"]';
export const INLINE_FIELD_ERROR_POPOVER_SELECTOR = '[data-powercrud-inline-error-popover="true"]';
export const RANGE_SELECT_SUPPRESS_CLASS = 'powercrud-range-selecting';
export const VISIBLE_FILTERS_PARAM = 'visible_filters';
export const FILTER_PANEL_STORAGE_PREFIX = 'powercrud:filter-panel:';
export const VISIBLE_FILTERS_STORAGE_PREFIX = 'powercrud:visible-filters:';
export const FILTER_FAVOURITE_STORAGE_PREFIX = 'powercrud:selected-filter-favourite:';
export const FILTER_FAVOURITE_DIRTY_STORAGE_PREFIX = 'powercrud:selected-filter-favourite-dirty:';
export const VIEW_STATE_STORAGE_PREFIX = 'powercrud:view-state:';
export const DEFAULT_MODAL_BOX_CLASSES = 'modal-box flex max-h-[calc(100dvh-2rem)] flex-col';
export const IGNORED_VIEW_STATE_FIELD_NAMES = new Set([
    'csrfmiddlewaretoken',
    'current_state_json',
    'favourite_id',
    'list_columns_action',
    'list_view_url',
    'original_target',
    'selected_favourite_id',
    'state_json',
    'toolbar_dom_id',
    'view_key',
    'visible_columns',
]);
