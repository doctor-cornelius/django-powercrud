import {
    LIST_COLUMNS_SELECTOR,
    VISIBLE_FILTERS_PARAM,
    IGNORED_VIEW_STATE_FIELD_NAMES,
} from './selectors.js';
import {
    collectSearchParams,
    getSearchParamFromHref,
    normaliseListUrl,
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

    const pendingFilterPanelOpenCounts = new Map();

    function getFilterPanelRenderKey(root) {
        return normaliseListUrl(root?.dataset?.powercrudListUrl || '', global)
            || global.location.pathname
            || 'default';
    }

    function markFilterPanelOpenForNextRender(root) {
        if (root instanceof Element) {
            pendingFilterPanelOpenCounts.set(getFilterPanelRenderKey(root), 4);
        }
    }

    function consumeFilterPanelOpenForNextRender(root) {
        const key = getFilterPanelRenderKey(root);
        const remainingCount = pendingFilterPanelOpenCounts.get(key) || 0;
        if (remainingCount < 1) {
            return false;
        }
        if (remainingCount === 1) {
            pendingFilterPanelOpenCounts.delete(key);
        } else {
            pendingFilterPanelOpenCounts.set(key, remainingCount - 1);
        }
        return true;
    }

    function isDjangoNullBooleanUnknownValue(field, value) {
        if (!(field instanceof HTMLSelectElement) || field.multiple) {
            return false;
        }
        if (String(value || '').trim() !== 'unknown') {
            return false;
        }

        const optionValues = Array.from(field.options)
            .map(option => String(option.value || '').trim())
            .filter(Boolean)
            .sort();
        return optionValues.length === 3
            && optionValues[0] === 'false'
            && optionValues[1] === 'true'
            && optionValues[2] === 'unknown';
    }

    function hasFilterValue(field, value) {
        const normalizedValue = String(value || '').trim();
        if (normalizedValue === '') {
            return false;
        }
        return !isDjangoNullBooleanUnknownValue(field, normalizedValue);
    }

    function hasActiveFilterValues(root) {
        const form = root.querySelector('#filter-form');
        if (!form) {
            return false;
        }

        return Array.from(form.querySelectorAll('[name]')).some(field => {
            if (!(field instanceof HTMLInputElement || field instanceof HTMLSelectElement || field instanceof HTMLTextAreaElement)) {
                return false;
            }
            if (field.disabled || !field.name || field.name === VISIBLE_FILTERS_PARAM) {
                return false;
            }
            if (field instanceof HTMLInputElement && field.type === 'hidden') {
                return false;
            }
            if (field instanceof HTMLInputElement && (field.type === 'checkbox' || field.type === 'radio')) {
                return field.checked && String(field.value || '').trim() !== '';
            }
            if (field instanceof HTMLSelectElement && field.multiple) {
                return Array.from(field.selectedOptions)
                    .some(option => String(option.value || '').trim() !== '');
            }
            return hasFilterValue(field, field.value);
        });
    }

    function syncFilterToggleLabel(root) {
        const filterCollapse = root.querySelector('#filterCollapse');
        const filterBtn = root.querySelector('[data-powercrud-filter-toggle]');
        if (!filterCollapse || !filterBtn) {
            return;
        }
        const isHidden = filterCollapse.classList.contains('hidden');
        const hasActiveFilters = hasActiveFilterValues(root);
        const baseLabel = isHidden ? 'Show filters' : 'Hide filters';
        const label = hasActiveFilters ? `${baseLabel} - filters active` : baseLabel;
        filterBtn.setAttribute('aria-expanded', isHidden ? 'false' : 'true');
        filterBtn.setAttribute('aria-label', label);
        filterBtn.setAttribute('data-tippy-content', label);
        filterBtn.setAttribute('data-powercrud-filters-active', hasActiveFilters ? 'true' : 'false');
        const outlineIcon = filterBtn.querySelector('[data-powercrud-filter-toggle-icon-outline="true"]');
        const filledIcon = filterBtn.querySelector('[data-powercrud-filter-toggle-icon-filled="true"]');
        if (outlineIcon instanceof HTMLElement || outlineIcon instanceof SVGElement) {
            outlineIcon.classList.toggle('hidden', hasActiveFilters);
        }
        if (filledIcon instanceof HTMLElement || filledIcon instanceof SVGElement) {
            filledIcon.classList.toggle('hidden', !hasActiveFilters);
        }
        schedulePowercrudTooltipRefresh(root);
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

            if (!hasFilterValue(field, field.value) && isDjangoNullBooleanUnknownValue(field, field.value)) {
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

            if (!hasFilterValue(field, field.value)) {
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
        const filterCollapse = root.querySelector('#filterCollapse');
        if (
            options.preserveFilterPanel !== false
            && filterCollapse instanceof Element
            && !filterCollapse.classList.contains('hidden')
        ) {
            markFilterPanelOpenForNextRender(root);
        }
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
        requestObjectListRefresh(root, { preservePage: true });
    }

    function removeOptionalFilter(root, fieldName) {
        if (!fieldName) {
            return;
        }

        const persistedNames = getPersistedOptionalFilterNames(root)
            .filter(name => name !== fieldName);
        setPersistedOptionalFilterNames(root, persistedNames);

        const field = getVisibleFilterField(root, fieldName);
        setFilterFieldValue(field, '');

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

    function clearCurrentListViewState(root) {
        pendingFilterPanelOpenCounts.delete(getFilterPanelRenderKey(root));
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

        clearCurrentListViewState(root);
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

        const shouldOpen = consumeFilterPanelOpenForNextRender(root);
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
        collectFavouriteStateFromRoot,
        dedupeFilterNames,
        getCurrentFilters,
        isFilterValueField,
        removeEmptyFields,
        removeOptionalFilter,
        requestObjectListRefresh,
        resetCurrentFilters,
        resetFilterForm,
        resetViewState,
        scheduleFilterValueRefresh,
        setPersistedOptionalFilterNames,
        syncFilterToggleLabel,
        toggleFilterVisibility,
    };
}
