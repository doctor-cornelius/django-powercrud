import {
    LIST_COLUMNS_SELECTOR,
    VISIBLE_FILTERS_PARAM,
    FILTER_PANEL_STORAGE_PREFIX,
    VISIBLE_FILTERS_STORAGE_PREFIX,
    VIEW_STATE_STORAGE_PREFIX,
    IGNORED_VIEW_STATE_FIELD_NAMES,
} from './selectors.js';
import {
    buildRawStorageKey,
    buildPathStorageKey,
    buildExplicitOrPathStorageKey,
    getSessionStorageItem,
    setSessionStorageItem,
    removeSessionStorageItem,
    getLocalStorageJsonArray,
    setLocalStorageJsonArray,
} from './storage.js';
import {
    currentLocationMatchesListUrl,
    sanitizeQueryString,
    collectSearchParams,
    getSearchParamFromHref,
} from './url.js';

export function createListViewStateRuntime(context) {
    const {
        global,
        documentObject,
        ensureObjectListState,
        getHtmxInstance,
        getObjectListRoot,
        getRootSwapTarget,
        getVisibleListColumnNames,
        buildListColumnResetRequest,
        initPowercrudSearchableSelects,
        schedulePowercrudTooltipRefresh,
        getFilterFavouritesContainer,
        getSelectedFilterFavouriteViewContext,
        markSelectedFilterFavouriteDirty,
        suppressFavouriteAutoApplyOnce,
        clearSelectedFilterFavouriteSelection,
        closeFilterFavouritesDropdowns,
        syncSelectedFilterFavouritePresentation,
    } = context;

    function syncFilterToggleLabel(root) {
        const filterCollapse = root.querySelector('#filterCollapse');
        const filterBtn = root.querySelector('[data-powercrud-filter-toggle]');
        if (!filterCollapse || !filterBtn) {
            return;
        }
        const isHidden = filterCollapse.classList.contains('hidden');
        filterBtn.setAttribute('aria-expanded', isHidden ? 'false' : 'true');
        filterBtn.setAttribute('aria-label', isHidden ? 'Show filters' : 'Hide filters');
        filterBtn.setAttribute('data-tippy-content', isHidden ? 'Show filters' : 'Hide filters');
        schedulePowercrudTooltipRefresh(root);
    }

    function getFilterPanelStorageKey(root) {
        return buildRawStorageKey(FILTER_PANEL_STORAGE_PREFIX, root, global);
    }

    function getVisibleFiltersStorageKey(root) {
        return buildPathStorageKey(VISIBLE_FILTERS_STORAGE_PREFIX, root, global);
    }

    function getViewStateStorageKey(root) {
        const toolbar = root instanceof Element ? getFilterFavouritesContainer(root) : null;
        const explicitKey = toolbar?.dataset?.powercrudFilterFavouritesViewKey || '';
        return buildExplicitOrPathStorageKey(VIEW_STATE_STORAGE_PREFIX, explicitKey, root, global);
    }

    function setPersistedFilterPanelState(root, isOpen) {
        setSessionStorageItem(global, getFilterPanelStorageKey(root), isOpen ? 'open' : 'closed');
    }

    function getPersistedFilterPanelState(root) {
        return getSessionStorageItem(global, getFilterPanelStorageKey(root));
    }

    function clearPersistedFilterPanelState(root) {
        removeSessionStorageItem(global, getFilterPanelStorageKey(root));
    }

    function getAddFilterContainer(root) {
        return root.querySelector('[data-powercrud-add-filter-container]');
    }

    function syncAddFilterVisibility(root, isOpen) {
        const addFilterContainer = getAddFilterContainer(root);
        if (!addFilterContainer) {
            return;
        }

        addFilterContainer.classList.toggle('hidden', !isOpen);
        if (isOpen) {
            global.setTimeout(() => initPowercrudSearchableSelects(addFilterContainer), 0);
        }
    }

    function syncFilterFavouritesVisibility(root, _isOpen) {
        const favouritesContainer = getFilterFavouritesContainer(root);
        if (!favouritesContainer) {
            return;
        }

        favouritesContainer.classList.remove('hidden');
    }

    function getVisibleFilterStateContainer(root) {
        return root.querySelector('[data-powercrud-visible-filters-state]');
    }

    function getAddFilterSelect(root) {
        return root.querySelector('[data-powercrud-add-filter-select]');
    }

    function getVisibleFilterField(root, fieldName) {
        const form = root.querySelector('#filter-form');
        if (!form || !fieldName) {
            return null;
        }
        return form.querySelector(`[name="${CSS.escape(fieldName)}"]`);
    }

    function dedupeFilterNames(names) {
        return Array.from(new Set((names || []).filter(Boolean).map(String)));
    }

    function getPersistedOptionalFilterNames(root) {
        const container = getVisibleFilterStateContainer(root);
        if (!container) {
            return [];
        }
        return Array.from(
            container.querySelectorAll(`input[name="${VISIBLE_FILTERS_PARAM}"]`)
        ).map(input => input.value).filter(Boolean);
    }

    function getStoredOptionalFilterNames(root) {
        return getLocalStorageJsonArray(
            global,
            getVisibleFiltersStorageKey(root),
            dedupeFilterNames,
        );
    }

    function setStoredOptionalFilterNames(root, names) {
        const normalizedNames = dedupeFilterNames(names);
        setLocalStorageJsonArray(global, getVisibleFiltersStorageKey(root), normalizedNames);
    }

    function getCurrentVisibleFilterNames(root) {
        const form = root.querySelector('#filter-form');
        if (!form) {
            return [];
        }

        return dedupeFilterNames(
            Array.from(form.querySelectorAll('.filter-field-input [name]'))
                .map(field => field.name)
                .filter(name => name && name !== VISIBLE_FILTERS_PARAM)
        );
    }

    function getAvailableOptionalFilterNames(root) {
        const select = getAddFilterSelect(root);
        if (!(select instanceof HTMLSelectElement)) {
            return [];
        }

        return dedupeFilterNames(
            Array.from(select.options)
                .map(option => option.value)
                .filter(Boolean)
        );
    }

    function setPersistedOptionalFilterNames(root, names) {
        const container = getVisibleFilterStateContainer(root);
        if (!container) {
            return;
        }
        container.innerHTML = '';
        names.forEach(name => {
            const input = documentObject.createElement('input');
            input.type = 'hidden';
            input.name = VISIBLE_FILTERS_PARAM;
            input.value = name;
            container.appendChild(input);
        });
    }

    function maybeRestoreStoredOptionalFilterVisibility(root) {
        const state = ensureObjectListState(root);
        if (state.optionalFilterVisibilityRestored) {
            return;
        }
        state.optionalFilterVisibilityRestored = true;

        const { selectedFavouriteId, isDirty } = getSelectedFilterFavouriteViewContext(root);
        if (selectedFavouriteId && !isDirty) {
            return;
        }

        const normalizedNames = dedupeFilterNames([
            ...getPersistedOptionalFilterNames(root),
            ...getStoredOptionalFilterNames(root),
        ]);
        const currentVisibleNames = getCurrentVisibleFilterNames(root);
        const availableOptionalNames = getAvailableOptionalFilterNames(root);
        const allowedNames = normalizedNames.filter(
            name => currentVisibleNames.includes(name) || availableOptionalNames.includes(name)
        );

        setStoredOptionalFilterNames(root, allowedNames);
        setPersistedOptionalFilterNames(root, allowedNames);

        if (!allowedNames.some(name => !currentVisibleNames.includes(name))) {
            return;
        }

        // Keep this browser-local restoration out of the shared URL.
        requestObjectListRefresh(root, { preservePage: true, pushURL: false });
    }

    function setFilterFieldValue(field, value) {
        if (!(field instanceof Element)) {
            return;
        }

        if (field instanceof HTMLSelectElement && field.tomselect) {
            field.tomselect.setValue(value, true);
            field.tomselect.setTextboxValue('');
            return;
        }

        if (field instanceof HTMLSelectElement && field.multiple) {
            Array.from(field.options).forEach(option => {
                option.selected = false;
            });
            return;
        }

        if (field instanceof HTMLSelectElement) {
            field.selectedIndex = 0;
            return;
        }

        if (field instanceof HTMLInputElement || field instanceof HTMLTextAreaElement) {
            if (field.type === 'checkbox' || field.type === 'radio') {
                field.checked = false;
                return;
            }
            field.value = value;
        }
    }

    function getCurrentListViewQueryValues(root, options = {}) {
        const preservePage = options.preservePage === true;
        const values = {};

        root.querySelectorAll('[name]').forEach(field => {
            if (!(field instanceof HTMLInputElement || field instanceof HTMLSelectElement || field instanceof HTMLTextAreaElement)) {
                return;
            }
            if (field.disabled) {
                return;
            }
            const name = field.name;
            if (!name) {
                return;
            }
            if (IGNORED_VIEW_STATE_FIELD_NAMES.has(name)) {
                return;
            }
            if (field.closest('[data-powercrud-filter-favourites-toolbar="true"]')) {
                return;
            }
            if (field.closest(LIST_COLUMNS_SELECTOR)) {
                return;
            }
            const fieldForm = field.closest('form');
            if (
                fieldForm instanceof HTMLFormElement
                && fieldForm.id !== 'filter-form'
                && fieldForm.id !== 'page-size-form'
            ) {
                return;
            }
            if (!preservePage && name === 'page') {
                return;
            }

            if (field instanceof HTMLInputElement && (field.type === 'checkbox' || field.type === 'radio')) {
                if (!field.checked) {
                    return;
                }
            }

            if (field instanceof HTMLSelectElement && field.multiple) {
                const selectedValues = Array.from(field.selectedOptions)
                    .map(option => option.value)
                    .filter(value => String(value).trim() !== '');
                if (!selectedValues.length) {
                    return;
                }
                values[name] = selectedValues;
                return;
            }

            if (Array.isArray(values[name])) {
                values[name].push(field.value);
                return;
            }
            if (name in values) {
                values[name] = [values[name], field.value];
                return;
            }
            values[name] = field.value;
        });

        return values;
    }

    function currentLocationMatchesRoot(root) {
        if (!(root instanceof Element)) {
            return false;
        }
        return currentLocationMatchesListUrl(root.dataset.powercrudListUrl, global);
    }

    function getStoredViewQueryString(root) {
        const rawQueryString = getSessionStorageItem(global, getViewStateStorageKey(root));
        const sanitizedQueryString = sanitizeViewQueryString(rawQueryString);
        if (rawQueryString && sanitizedQueryString !== rawQueryString) {
            setStoredViewQueryString(root, sanitizedQueryString);
        }
        return sanitizedQueryString;
    }

    function sanitizeViewQueryString(queryString) {
        return sanitizeQueryString(queryString, IGNORED_VIEW_STATE_FIELD_NAMES);
    }

    function setStoredViewQueryString(root, queryString) {
        const normalizedQueryString = sanitizeViewQueryString(queryString);
        if (!normalizedQueryString) {
            removeSessionStorageItem(global, getViewStateStorageKey(root));
            return;
        }
        setSessionStorageItem(global, getViewStateStorageKey(root), normalizedQueryString);
    }

    function clearStoredViewState(root) {
        removeSessionStorageItem(global, getViewStateStorageKey(root));
    }

    function rememberCurrentViewState(root) {
        if (!(root instanceof Element) || !currentLocationMatchesRoot(root)) {
            return;
        }

        // A selected clean favourite is the source of truth. Store ad-hoc view
        // state only when there is no favourite or the favourite has diverged.
        const { selectedFavouriteId, isDirty } = getSelectedFilterFavouriteViewContext(root);
        if (selectedFavouriteId) {
            if (isDirty) {
                setStoredViewQueryString(root, global.location.search);
            }
            return;
        }

        setStoredViewQueryString(root, global.location.search);
    }

    function maybeRestoreStoredViewState(root) {
        if (!(root instanceof Element) || !currentLocationMatchesRoot(root)) {
            return false;
        }

        if (global.location.search) {
            rememberCurrentViewState(root);
            return false;
        }

        // Do not replay stored view state over a clean selected favourite; the
        // favourite auto-apply path owns that restoration.
        const { selectedFavouriteId, isDirty } = getSelectedFilterFavouriteViewContext(root);
        if (selectedFavouriteId && !isDirty) {
            return false;
        }

        const queryString = getStoredViewQueryString(root);
        const htmx = getHtmxInstance();
        const listUrl = root.dataset.powercrudListUrl;
        if (!queryString || !htmx || !listUrl) {
            return false;
        }

        htmx.ajax('GET', `${listUrl}?${queryString}`, {
            target: root,
            swap: 'outerHTML',
            headers: {
                'X-Filter-Setting-Request': 'true',
            },
            pushURL: true,
        });
        return true;
    }

    function getCurrentSortValue() {
        return getSearchParamFromHref(global.location.href, 'sort');
    }

    function getCurrentPageSizeValue(root) {
        const pageSizeSelect = root.querySelector('#page-size-select');
        if (pageSizeSelect instanceof HTMLSelectElement) {
            return pageSizeSelect.value || '';
        }

        return getSearchParamFromHref(global.location.href, 'page_size');
    }

    function appendFavouriteFilterValue(stateFilters, field, value) {
        if (!field || String(value).trim() === '') {
            return;
        }
        if (!Array.isArray(stateFilters[field])) {
            stateFilters[field] = [];
        }
        stateFilters[field].push(String(value));
    }

    function collectFavouriteStateFromRoot(root) {
        const state = {
            filters: {},
            visible_filters: [],
            sort: getCurrentSortValue(),
            page_size: getCurrentPageSizeValue(root),
        };
        const visibleColumns = getVisibleListColumnNames(root);
        if (Array.isArray(visibleColumns)) {
            state.visible_columns = visibleColumns;
        }

        const filterForm = root.querySelector('#filter-form');
        if (!filterForm) {
            return state;
        }

        filterForm.querySelectorAll('[name]').forEach(field => {
            if (!(field instanceof HTMLInputElement || field instanceof HTMLSelectElement || field instanceof HTMLTextAreaElement)) {
                return;
            }
            if (field.disabled) {
                return;
            }

            const name = field.name;
            if (!name) {
                return;
            }

            if (name === VISIBLE_FILTERS_PARAM) {
                if (String(field.value).trim() !== '') {
                    state.visible_filters.push(String(field.value));
                }
                return;
            }

            if (field instanceof HTMLInputElement && (field.type === 'checkbox' || field.type === 'radio')) {
                if (!field.checked) {
                    return;
                }
                appendFavouriteFilterValue(state.filters, name, field.value);
                return;
            }

            if (field instanceof HTMLSelectElement && field.multiple) {
                Array.from(field.selectedOptions)
                    .map(option => option.value)
                    .filter(value => String(value).trim() !== '')
                    .forEach(value => appendFavouriteFilterValue(state.filters, name, value));
                return;
            }

            appendFavouriteFilterValue(state.filters, name, field.value);
        });

        state.visible_filters = dedupeFilterNames(state.visible_filters);
        return state;
    }

    function requestObjectListRefresh(root, options = {}) {
        if (!(root instanceof Element)) {
            return;
        }

        const htmx = getHtmxInstance();
        const listUrl = root.dataset.powercrudListUrl;
        if (!htmx || !listUrl) {
            const form = root.querySelector('#filter-form');
            if (form) {
                form.requestSubmit();
            }
            return;
        }

        const values = getCurrentListViewQueryValues(root, {
            preservePage: options.preservePage === true,
        });
        // Any manual list refresh after favourite application means the
        // selected favourite remains selected but becomes dirty.
        const { toolbar } = getSelectedFilterFavouriteViewContext(root);
        markSelectedFilterFavouriteDirty(root, toolbar);
        suppressFavouriteAutoApplyOnce?.(root, toolbar);
        htmx.ajax('GET', listUrl, {
            target: getRootSwapTarget(root),
            swap: root.dataset.powercrudOriginalTarget ? 'innerHTML' : 'outerHTML',
            values,
            headers: {
                'X-Filter-Setting-Request': 'true',
            },
            pushURL: options.pushURL !== false,
        });
    }

    function isFilterValueField(target) {
        if (!(target instanceof HTMLInputElement || target instanceof HTMLSelectElement || target instanceof HTMLTextAreaElement)) {
            return false;
        }
        if (target.disabled || !target.name || target.type === 'hidden') {
            return false;
        }
        if (target.name === VISIBLE_FILTERS_PARAM) {
            return false;
        }
        return target.closest('#filter-form') instanceof HTMLFormElement;
    }

    function scheduleFilterValueRefresh(field, options = {}) {
        if (!isFilterValueField(field)) {
            return;
        }

        const root = getObjectListRoot(field);
        if (!(root instanceof Element)) {
            return;
        }

        const state = ensureObjectListState(root);
        if (state.filterRefreshTimer) {
            global.clearTimeout(state.filterRefreshTimer);
        }

        const delay = options.immediate === true ? 0 : 300;
        state.filterRefreshTimer = global.setTimeout(() => {
            state.filterRefreshTimer = null;
            if (!root.isConnected) {
                return;
            }
            requestObjectListRefresh(root, { preservePage: false });
        }, delay);
    }

    function addOptionalFilter(root, fieldName) {
        if (!fieldName) {
            return;
        }

        const persistedNames = getPersistedOptionalFilterNames(root);
        if (!persistedNames.includes(fieldName)) {
            persistedNames.push(fieldName);
            setPersistedOptionalFilterNames(root, persistedNames);
        }
        setStoredOptionalFilterNames(root, persistedNames);

        setPersistedFilterPanelState(root, true);
        requestObjectListRefresh(root, { preservePage: true });
    }

    function removeOptionalFilter(root, fieldName) {
        if (!fieldName) {
            return;
        }

        const persistedNames = getPersistedOptionalFilterNames(root)
            .filter(name => name !== fieldName);
        setPersistedOptionalFilterNames(root, persistedNames);
        setStoredOptionalFilterNames(root, persistedNames);

        const field = getVisibleFilterField(root, fieldName);
        setFilterFieldValue(field, '');

        setPersistedFilterPanelState(root, true);
        requestObjectListRefresh(root, { preservePage: true });
    }

    function removeEmptyFields(form) {
        Array.from(form.elements).forEach(el => {
            if ((el.tagName === 'INPUT' || el.tagName === 'SELECT') && !el.value && !el.multiple) {
                el.disabled = true;
            }
            if (el.tagName === 'SELECT' && el.multiple) {
                const anySelected = Array.from(el.options).some(opt => opt.selected && opt.value);
                if (!anySelected) {
                    el.disabled = true;
                }
            }
        });
        global.setTimeout(() => {
            Array.from(form.elements).forEach(el => {
                el.disabled = false;
            });
        }, 100);
        return true;
    }

    function getCurrentFilters(options = {}) {
        return collectSearchParams(global.location.search, options);
    }

    function resetFilterForm(root) {
        const form = root.querySelector('#filter-form');
        if (!form) {
            return;
        }
        form.querySelectorAll('input, select').forEach(field => {
            if (field.tagName === 'SELECT' && field.tomselect) {
                field.tomselect.clear(true);
                field.tomselect.setTextboxValue('');
                return;
            }
            if (field.type === 'select-one') {
                field.selectedIndex = 0;
            } else if (field.type === 'select-multiple') {
                Array.from(field.options).forEach(option => {
                    option.selected = false;
                });
            } else if (field.type !== 'hidden') {
                field.value = '';
            }
        });
    }

    function clearCurrentListViewState(root, options = {}) {
        clearStoredViewState(root);
        if (options.clearFilterPanel === true) {
            clearPersistedFilterPanelState(root);
        }
        setStoredOptionalFilterNames(root, []);
        setPersistedOptionalFilterNames(root, []);
    }

    function resetCurrentFilters(root) {
        if (!(root instanceof Element)) {
            return;
        }
        const { toolbar } = getSelectedFilterFavouriteViewContext(root);
        clearCurrentListViewState(root);
        resetFilterForm(root);
        markSelectedFilterFavouriteDirty(root, toolbar);
        syncSelectedFilterFavouritePresentation(root);
    }

    function resetViewState(root) {
        if (!(root instanceof Element)) {
            return;
        }

        const htmx = getHtmxInstance();
        const listUrl = root.dataset.powercrudListUrl;
        if (!htmx || !listUrl) {
            global.location.href = listUrl || global.location.pathname;
            return;
        }

        clearCurrentListViewState(root, { clearFilterPanel: true });
        clearSelectedFilterFavouriteSelection(root);
        closeFilterFavouritesDropdowns();

        // Visible-column defaults live server-side, so reset them before the
        // final list refresh when a reset endpoint is available.
        const listColumnResetRequest = buildListColumnResetRequest(root, listUrl);
        if (listColumnResetRequest) {
            htmx.ajax('POST', listColumnResetRequest.url, {
                target: getRootSwapTarget(root),
                swap: root.dataset.powercrudOriginalTarget ? 'innerHTML' : 'outerHTML',
                values: listColumnResetRequest.values,
            });
            return;
        }

        htmx.ajax('GET', listUrl, {
            target: getRootSwapTarget(root),
            swap: root.dataset.powercrudOriginalTarget ? 'innerHTML' : 'outerHTML',
            pushURL: true,
        });
    }

    function applyFilterPanelState(root) {
        const filterCollapse = root.querySelector('#filterCollapse');
        if (!filterCollapse) {
            return;
        }

        const shouldOpen = getPersistedFilterPanelState(root) === 'open';
        filterCollapse.classList.toggle('hidden', !shouldOpen);
        syncFilterToggleLabel(root);
        syncAddFilterVisibility(root, shouldOpen);
        syncFilterFavouritesVisibility(root, shouldOpen);
        if (shouldOpen) {
            global.setTimeout(() => initPowercrudSearchableSelects(filterCollapse), 0);
        }
    }

    function toggleFilterVisibility(root) {
        const filterCollapse = root.querySelector('#filterCollapse');
        if (!filterCollapse) {
            return;
        }
        filterCollapse.classList.toggle('hidden');
        const isOpen = !filterCollapse.classList.contains('hidden');
        setPersistedFilterPanelState(root, isOpen);
        syncFilterToggleLabel(root);
        syncAddFilterVisibility(root, isOpen);
        syncFilterFavouritesVisibility(root, isOpen);
        if (isOpen) {
            global.setTimeout(() => initPowercrudSearchableSelects(filterCollapse), 0);
        }
    }

    return {
        addOptionalFilter,
        applyFilterPanelState,
        clearStoredViewState,
        collectFavouriteStateFromRoot,
        dedupeFilterNames,
        getCurrentFilters,
        isFilterValueField,
        maybeRestoreStoredOptionalFilterVisibility,
        maybeRestoreStoredViewState,
        rememberCurrentViewState,
        removeEmptyFields,
        removeOptionalFilter,
        requestObjectListRefresh,
        resetCurrentFilters,
        resetFilterForm,
        resetViewState,
        scheduleFilterValueRefresh,
        setPersistedOptionalFilterNames,
        setStoredOptionalFilterNames,
        syncFilterToggleLabel,
        toggleFilterVisibility,
    };
}
