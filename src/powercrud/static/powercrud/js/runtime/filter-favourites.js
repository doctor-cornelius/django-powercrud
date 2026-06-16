import {
    asElement,
    queryAllWithSelf,
    getAffectedObjectListRoots,
    getObjectListRoot,
} from './dom.js';
import {
    FILTER_FAVOURITE_STORAGE_PREFIX,
    FILTER_FAVOURITE_DIRTY_STORAGE_PREFIX,
} from './selectors.js';
import {
    buildExplicitOrPathStorageKey,
    getSessionStorageItem,
    setSessionStorageItem,
    removeSessionStorageItem,
} from './storage.js';
import { normaliseListUrl } from './url.js';

export function createFilterFavouritesRuntime(context) {
    const {
        global,
        documentObject,
        getHtmxInstance,
        initPowercrudSearchableSelects,
        initPowercrudTooltips,
        prepareFilterFavouritesFloatingPanel,
        positionFilterFavouritesPanel,
        setFilterFavouritesDropdownOpen,
        showPreparedFloatingPanel,
        syncFilterFavouritesTriggerPresentation,
        getListViewStateApi,
        isInlineEditRequest,
    } = context;

    const suppressFavouriteAutoApplyKeys = new Set();
    const favouriteAutoApplyInFlightKeys = new Set();
    const protectedSelectedFavouriteDirtyKeys = new Set();
    const favouriteAutoApplyContextsByTarget = new WeakMap();
    const latestInteractiveRequestVersionByTarget = new WeakMap();
    const currentSwapRequestVersionByTarget = new WeakMap();
    let nextInteractiveRequestVersion = 0;
    let activeFilterFavouritesPanel = null;
    let activeFilterFavouritesTrigger = null;

    function getListViewState() {
        return getListViewStateApi?.() || {};
    }

    function collectFavouriteStateFromRoot(root) {
        return getListViewState().collectFavouriteStateFromRoot?.(root) || {
            filters: {},
            visible_filters: [],
            sort: '',
            page_size: '',
        };
    }

    function dedupeFilterNames(names) {
        return getListViewState().dedupeFilterNames?.(names)
            || Array.from(new Set((names || []).filter(Boolean).map(String)));
    }

    function getFilterFavouritesContainer(root) {
        return root.querySelector('[data-powercrud-filter-favourites-toolbar="true"]');
    }

    function getFilterFavouritesToolbarById(toolbarDomId) {
        if (!toolbarDomId) {
            return null;
        }
        const toolbar = documentObject.getElementById(toolbarDomId);
        return toolbar instanceof Element ? toolbar : null;
    }

    function getFilterFavouritesToolbarFromElement(element) {
        if (!(element instanceof Element)) {
            return null;
        }
        const directToolbar = element.closest('[data-powercrud-filter-favourites-toolbar="true"]');
        if (directToolbar instanceof Element) {
            return directToolbar;
        }
        const floatingPanel = element.closest('[data-powercrud-filter-favourites-floating-panel="true"]');
        if (!(floatingPanel instanceof HTMLElement)) {
            return null;
        }
        return getFilterFavouritesToolbarById(
            floatingPanel.dataset.powercrudToolbarDomId || ''
        );
    }

    function getFilterFavouritesDropdowns(scope = documentObject) {
        return queryAllWithSelf(scope, '[data-powercrud-filter-favourites-dropdown="true"]');
    }

    function getFilterFavouritesTemplate(toolbar) {
        if (!(toolbar instanceof Element)) {
            return null;
        }
        const template = toolbar.querySelector('[data-powercrud-filter-favourites-template="true"]');
        return template instanceof HTMLElement ? template : null;
    }

    function getFilterFavouritesPanelFromElement(element) {
        if (!(element instanceof Element)) {
            return null;
        }
        const panel = element.closest('[data-powercrud-filter-favourites-panel="true"]');
        return panel instanceof HTMLElement ? panel : null;
    }

    function getFilterFavouritesSelect(toolbar) {
        if (!(toolbar instanceof Element)) {
            return null;
        }
        const select = toolbar.querySelector('[data-powercrud-favourite-select="true"]');
        return select instanceof HTMLSelectElement ? select : null;
    }

    function syncFilterFavouritesTriggerLabel(toolbar) {
        if (!(toolbar instanceof Element)) {
            return;
        }

        const triggerLabel = toolbar.querySelector('[data-powercrud-filter-favourites-trigger-label="true"]');
        if (!(triggerLabel instanceof Element)) {
            return;
        }

        const trigger = toolbar.querySelector('[data-powercrud-filter-favourites-trigger="true"]');
        const defaultLabel = trigger
            ?.getAttribute('data-powercrud-filter-favourites-default-label')
            || 'Favourites';
        const favouriteSelect = getFilterFavouritesSelect(toolbar);
        const selectedOption = getSelectedFavouriteOption(favouriteSelect);
        const selectedLabel = selectedOption?.textContent?.trim() || '';
        const root = getObjectListRoot(toolbar);
        const selectedFavouriteId = getFavouriteSelectValue(favouriteSelect);
        const isDirty = Boolean(
            root
            && selectedFavouriteId
            && isSelectedFilterFavouriteDirty(root, toolbar, selectedFavouriteId)
        );
        // The selected/dirty semantics are core; the icon, colour, label, and
        // tooltip treatment remain current-template presentation callbacks.
        syncFilterFavouritesTriggerPresentation?.({
            toolbar,
            trigger,
            triggerLabel,
            selectedLabel,
            defaultLabel,
            isDirty,
        });
    }

    function getSelectedFavouriteOption(selectElement) {
        if (!(selectElement instanceof HTMLSelectElement) || !selectElement.value) {
            return null;
        }

        const selectedOption = selectElement.options[selectElement.selectedIndex];
        return selectedOption instanceof HTMLOptionElement ? selectedOption : null;
    }

    function getFavouriteSelectValue(selectElement) {
        if (!(selectElement instanceof HTMLSelectElement)) {
            return '';
        }
        return String(selectElement.value || '').trim();
    }

    function getFavouriteOptionByValue(selectElement, favouriteId) {
        if (!(selectElement instanceof HTMLSelectElement) || !favouriteId) {
            return null;
        }
        return Array
            .from(selectElement.options)
            .find(option => String(option.value) === String(favouriteId)) || null;
    }

    function parseFavouriteOptionState(optionElement) {
        if (!(optionElement instanceof HTMLOptionElement)) {
            return null;
        }
        return parseJsonObject(optionElement.dataset.powercrudFavouriteStateJson || '');
    }

    function parseJsonObject(rawValue) {
        try {
            const parsedValue = rawValue ? JSON.parse(rawValue) : null;
            return parsedValue && typeof parsedValue === 'object' ? parsedValue : null;
        } catch (_error) {
            return null;
        }
    }

    function getServerRenderedToolbarState(toolbar) {
        if (!(toolbar instanceof HTMLElement)) {
            return null;
        }
        return parseJsonObject(toolbar.dataset.powercrudCurrentStateJson || '');
    }

    function getCurrentFavouriteState(root, toolbar = null) {
        return getServerRenderedToolbarState(toolbar) || collectFavouriteStateFromRoot(root);
    }

    function normalizeFavouriteStateForComparison(state) {
        // Favourite comparison ignores ordering and empty values so UI changes
        // mark a favourite dirty only when the effective view state changed.
        const normalizedState = {
            filters: {},
            visible_filters: [],
            sort: '',
            page_size: '',
        };

        if (!state || typeof state !== 'object') {
            return normalizedState;
        }

        const filters = state.filters && typeof state.filters === 'object'
            ? state.filters
            : {};
        Object.entries(filters).sort(([leftName], [rightName]) => (
            String(leftName).localeCompare(String(rightName))
        )).forEach(([fieldName, values]) => {
            if (!fieldName) {
                return;
            }
            const rawValues = Array.isArray(values) ? values : [values];
            const normalizedValues = rawValues
                .map(value => String(value || '').trim())
                .filter(Boolean);
            if (normalizedValues.length) {
                normalizedState.filters[fieldName] = normalizedValues;
            }
        });

        if (Array.isArray(state.visible_filters)) {
            normalizedState.visible_filters = dedupeFilterNames(state.visible_filters).sort();
        }

        normalizedState.sort = String(state.sort || '').trim();
        normalizedState.page_size = String(state.page_size || '').trim();

        if (Array.isArray(state.visible_columns)) {
            normalizedState.visible_columns = dedupeFilterNames(state.visible_columns).sort();
        }

        return normalizedState;
    }

    function favouriteStateMatchesCurrentState(optionElement, currentState) {
        const favouriteState = parseFavouriteOptionState(optionElement);
        if (!favouriteState) {
            return false;
        }
        const comparableFavouriteState = normalizeFavouriteStateForComparison(favouriteState);
        const comparableCurrentState = normalizeFavouriteStateForComparison(currentState);
        if (!Object.prototype.hasOwnProperty.call(favouriteState, 'visible_columns')) {
            delete comparableCurrentState.visible_columns;
        }
        return JSON.stringify(comparableFavouriteState) === JSON.stringify(comparableCurrentState);
    }

    function favouriteStateMatchesRoot(optionElement, root, toolbar = null) {
        if (!(root instanceof Element)) {
            return false;
        }
        return favouriteStateMatchesCurrentState(
            optionElement,
            getCurrentFavouriteState(root, toolbar),
        );
    }

    function favouriteStateMatchesCollectedRoot(optionElement, root) {
        if (!(root instanceof Element)) {
            return false;
        }
        return favouriteStateMatchesCurrentState(
            optionElement,
            collectFavouriteStateFromRoot(root),
        );
    }

    function getFavouriteVisibleFilterNames(optionElement) {
        if (!(optionElement instanceof HTMLOptionElement)) {
            return [];
        }

        try {
            const rawValue = optionElement.dataset.powercrudFavouriteVisibleFilters || '[]';
            const parsedValue = JSON.parse(rawValue);
            return Array.isArray(parsedValue) ? dedupeFilterNames(parsedValue) : [];
        } catch (_error) {
            return [];
        }
    }

    function closeFilterFavouritesDropdowns(exceptToolbar = null) {
        getFilterFavouritesDropdowns(documentObject).forEach(toolbar => {
            const shouldRemainOpen = (
                exceptToolbar instanceof Element
                && toolbar === exceptToolbar
                && activeFilterFavouritesPanel instanceof HTMLElement
            );
            setFilterFavouritesDropdownOpen?.(toolbar, shouldRemainOpen);
        });

        if (exceptToolbar instanceof Element && activeFilterFavouritesTrigger instanceof HTMLElement) {
            const activeToolbar = activeFilterFavouritesTrigger.closest('[data-powercrud-filter-favourites-toolbar="true"]');
            if (activeToolbar === exceptToolbar) {
                return;
            }
        }

        if (activeFilterFavouritesTrigger instanceof HTMLElement) {
            activeFilterFavouritesTrigger.setAttribute('aria-expanded', 'false');
        }
        if (activeFilterFavouritesPanel instanceof HTMLElement && activeFilterFavouritesPanel.parentNode) {
            activeFilterFavouritesPanel.parentNode.removeChild(activeFilterFavouritesPanel);
        }
        activeFilterFavouritesPanel = null;
        activeFilterFavouritesTrigger = null;
    }

    function getSelectedFilterFavouriteStorageKey(root, toolbar = null) {
        const explicitKey = toolbar?.dataset?.powercrudFilterFavouritesViewKey || '';
        return buildExplicitOrPathStorageKey(FILTER_FAVOURITE_STORAGE_PREFIX, explicitKey, root, global);
    }

    function getSelectedFilterFavouriteDirtyStorageKey(root, toolbar = null) {
        // Dirty state mirrors the selected-favourite key so both survive shell
        // navigation using the same explicit view key or path fallback.
        const selectedKey = getSelectedFilterFavouriteStorageKey(root, toolbar);
        return selectedKey.replace(
            FILTER_FAVOURITE_STORAGE_PREFIX,
            FILTER_FAVOURITE_DIRTY_STORAGE_PREFIX,
        );
    }

    function getServerSelectedFilterFavouriteId(toolbar) {
        if (!(toolbar instanceof Element)) {
            return '';
        }

        const selectedField = toolbar.querySelector('input[name="selected_favourite_id"]');
        return selectedField instanceof HTMLInputElement
            ? String(selectedField.value || '').trim()
            : '';
    }

    function getPendingSelectedFilterFavouriteId(root, toolbar = null) {
        return getSessionStorageItem(global, getSelectedFilterFavouriteStorageKey(root, toolbar));
    }

    function setPendingSelectedFilterFavouriteId(root, toolbar = null, favouriteId = '') {
        const storageKey = getSelectedFilterFavouriteStorageKey(root, toolbar);
        const normalizedId = String(favouriteId || '').trim();
        if (!normalizedId) {
            removeSessionStorageItem(global, storageKey);
            return;
        }
        setSessionStorageItem(global, storageKey, normalizedId);
    }

    function getDirtySelectedFilterFavouriteId(root, toolbar = null) {
        return getSessionStorageItem(global, getSelectedFilterFavouriteDirtyStorageKey(root, toolbar));
    }

    function isSelectedFilterFavouriteDirty(root, toolbar = null, favouriteId = '') {
        const dirtyFavouriteId = getDirtySelectedFilterFavouriteId(root, toolbar);
        return Boolean(dirtyFavouriteId && String(dirtyFavouriteId) === String(favouriteId || ''));
    }

    function setSelectedFilterFavouriteDirty(root, toolbar = null, favouriteId = '') {
        const storageKey = getSelectedFilterFavouriteDirtyStorageKey(root, toolbar);
        const normalizedId = String(favouriteId || '').trim();
        if (!normalizedId) {
            removeSessionStorageItem(global, storageKey);
            protectedSelectedFavouriteDirtyKeys.delete(storageKey);
            return;
        }
        setSessionStorageItem(global, storageKey, normalizedId);
        protectedSelectedFavouriteDirtyKeys.add(storageKey);
    }

    function clearSelectedFilterFavouriteDirty(root, toolbar = null) {
        const storageKey = getSelectedFilterFavouriteDirtyStorageKey(root, toolbar);
        removeSessionStorageItem(global, storageKey);
        protectedSelectedFavouriteDirtyKeys.delete(storageKey);
    }

    function isSelectedFilterFavouriteDirtyProtected(root, toolbar = null) {
        return protectedSelectedFavouriteDirtyKeys.has(
            getSelectedFilterFavouriteDirtyStorageKey(root, toolbar)
        );
    }

    function getSelectedFilterFavouriteViewContext(root, toolbar = null) {
        const effectiveToolbar = toolbar instanceof Element
            ? toolbar
            : getFilterFavouritesContainer(root);
        const select = getFilterFavouritesSelect(effectiveToolbar);
        const selectedFavouriteId = getFavouriteSelectValue(select);
        const isDirty = Boolean(
            selectedFavouriteId
            && isSelectedFilterFavouriteDirty(root, effectiveToolbar, selectedFavouriteId)
        );
        return {
            toolbar: effectiveToolbar,
            select,
            selectedFavouriteId,
            isDirty,
        };
    }

    function markSelectedFilterFavouriteDirty(root, toolbar = null) {
        if (!(root instanceof Element)) {
            return;
        }

        const {
            toolbar: effectiveToolbar,
            select,
            selectedFavouriteId,
        } = getSelectedFilterFavouriteViewContext(root, toolbar);
        if (!(effectiveToolbar instanceof Element) || !(select instanceof HTMLSelectElement)) {
            return;
        }
        if (!selectedFavouriteId) {
            return;
        }
        setSelectedFilterFavouriteDirty(root, effectiveToolbar, selectedFavouriteId);
    }

    function suppressFavouriteAutoApplyOnce(root, toolbar = null) {
        if (!(root instanceof Element)) {
            return;
        }
        // Server responses that already applied a favourite should not trigger
        // the remembered-favourite auto-apply path again on the next bootstrap.
        suppressFavouriteAutoApplyKeys.add(getSelectedFilterFavouriteStorageKey(root, toolbar));
    }

    function shouldConsumeFavouriteAutoApplySuppression(root, toolbar = null) {
        if (!(root instanceof Element)) {
            return false;
        }
        const storageKey = getSelectedFilterFavouriteStorageKey(root, toolbar);
        if (!suppressFavouriteAutoApplyKeys.has(storageKey)) {
            return false;
        }
        suppressFavouriteAutoApplyKeys.delete(storageKey);
        return true;
    }

    function hasFavouriteAutoApplySuppression(root, toolbar = null) {
        if (!(root instanceof Element)) {
            return false;
        }
        return suppressFavouriteAutoApplyKeys.has(
            getSelectedFilterFavouriteStorageKey(root, toolbar)
        );
    }

    function getFavouriteAutoApplyKey(root, toolbar, favouriteId) {
        if (!(root instanceof Element) || !favouriteId) {
            return '';
        }
        return `${getSelectedFilterFavouriteStorageKey(root, toolbar)}:${favouriteId}`;
    }

    function releaseFavouriteAutoApplyKey(autoApplyKey) {
        if (!autoApplyKey) {
            return;
        }
        favouriteAutoApplyInFlightKeys.delete(autoApplyKey);
    }

    function getHtmxRequestConfig(event) {
        return event?.detail?.requestConfig || null;
    }

    function getHtmxRequestPath(event) {
        const detail = event?.detail || {};
        return String(detail.path || detail.requestConfig?.path || '');
    }

    function getHtmxRequestTarget(event) {
        const detail = event?.detail || {};
        const target = detail.target || detail.requestConfig?.target || null;
        return target instanceof Element ? target : null;
    }

    function getHtmxRequestElement(event, fallbackTarget = null) {
        const detail = event?.detail || {};
        const element = detail.elt || detail.requestConfig?.elt || fallbackTarget;
        return element instanceof Element ? element : null;
    }

    function isProgrammaticBodyHtmxRequest(event, fallbackTarget = null) {
        const requestConfig = getHtmxRequestConfig(event);
        const requestElement = getHtmxRequestElement(event, fallbackTarget);
        return Boolean(
            requestElement === documentObject.body
            && !requestConfig?.triggeringEvent
        );
    }

    function resolveHtmxTargetElement(target) {
        if (target instanceof Element) {
            return target;
        }
        if (typeof target !== 'string' || !target.trim()) {
            return null;
        }
        const targetElement = documentObject.querySelector(target);
        return targetElement instanceof Element ? targetElement : null;
    }

    function requestPathMatchesAutoApplyContext(path, context) {
        if (!path || !context) {
            return false;
        }
        if (path.includes('/powercrud/favourites/apply/')) {
            return true;
        }
        return normaliseListUrl(path, global) === context.listUrl;
    }

    function trackFavouriteAutoApplyRequest(event, fallbackTarget = null) {
        const requestTarget = getHtmxRequestTarget(event);
        if (!(requestTarget instanceof Element)) {
            return false;
        }

        const context = favouriteAutoApplyContextsByTarget.get(requestTarget);
        const isProgrammaticBodyRequest = isProgrammaticBodyHtmxRequest(event, fallbackTarget);
        const path = getHtmxRequestPath(event);
        if (
            context
            && isProgrammaticBodyRequest
            && requestPathMatchesAutoApplyContext(path, context)
        ) {
            if (context.stale) {
                event.preventDefault();
                favouriteAutoApplyContextsByTarget.delete(requestTarget);
                return true;
            }
            return false;
        }

        if (isProgrammaticBodyRequest) {
            return false;
        }

        const requestConfig = getHtmxRequestConfig(event);
        if (requestConfig) {
            if (!requestConfig.powercrudFavouriteInteractiveRequestVersion) {
                nextInteractiveRequestVersion += 1;
                requestConfig.powercrudFavouriteInteractiveRequestVersion = nextInteractiveRequestVersion;
            }
            latestInteractiveRequestVersionByTarget.set(
                requestTarget,
                requestConfig.powercrudFavouriteInteractiveRequestVersion,
            );
        }
        if (context) {
            context.stale = true;
        }
        return false;
    }

    function hasNewerInteractiveRequestForTarget(target) {
        if (!(target instanceof Element)) {
            return false;
        }
        const latestVersion = latestInteractiveRequestVersionByTarget.get(target) || 0;
        const currentSwapVersion = currentSwapRequestVersionByTarget.get(target) || 0;
        return latestVersion > currentSwapVersion;
    }

    function releaseTrackedFavouriteAutoApplyRequest(event) {
        const requestTarget = getHtmxRequestTarget(event);
        if (!(requestTarget instanceof Element)) {
            return;
        }

        const context = favouriteAutoApplyContextsByTarget.get(requestTarget);
        if (
            context
            && isProgrammaticBodyHtmxRequest(event)
            && requestPathMatchesAutoApplyContext(getHtmxRequestPath(event), context)
        ) {
            favouriteAutoApplyContextsByTarget.delete(requestTarget);
        }
    }

    function syncFilterFavouritesSelection(root) {
        const favouritesContainer = getFilterFavouritesContainer(root);
        const favouriteSelect = getFilterFavouritesSelect(favouritesContainer);
        if (!favouritesContainer || !favouriteSelect) {
            syncFilterFavouritesTriggerLabel(favouritesContainer);
            return;
        }

        let activeSelectedId = getPendingSelectedFilterFavouriteId(root, favouritesContainer);
        let activeSelectedOption = getFavouriteOptionByValue(favouriteSelect, activeSelectedId);
        if (activeSelectedId && !(activeSelectedOption instanceof HTMLOptionElement)) {
            setPendingSelectedFilterFavouriteId(root, favouritesContainer, '');
            clearSelectedFilterFavouriteDirty(root, favouritesContainer);
            activeSelectedId = '';
            activeSelectedOption = null;
        }
        const activeSelectedMatchesCurrent = Boolean(
            activeSelectedOption instanceof HTMLOptionElement
            && favouriteStateMatchesRoot(activeSelectedOption, root, favouritesContainer)
        );
        const activeSelectedMatchesCollectedState = Boolean(
            activeSelectedOption instanceof HTMLOptionElement
            && favouriteStateMatchesCollectedRoot(activeSelectedOption, root)
        );
        if (
            activeSelectedMatchesCurrent
            && activeSelectedMatchesCollectedState
            && !hasFavouriteAutoApplySuppression(root, favouritesContainer)
            && !isSelectedFilterFavouriteDirtyProtected(root, favouritesContainer)
        ) {
            clearSelectedFilterFavouriteDirty(root, favouritesContainer);
        }
        const matchingCandidates = [
            getServerSelectedFilterFavouriteId(favouritesContainer),
            getFavouriteSelectValue(favouriteSelect),
        ].filter(Boolean);
        const matchingSelectedId = matchingCandidates.find(candidate => {
            const candidateOption = getFavouriteOptionByValue(favouriteSelect, candidate);
            return favouriteStateMatchesRoot(candidateOption, root, favouritesContainer);
        }) || '';
        const effectiveSelectedId = activeSelectedId || matchingSelectedId;
        const hasSelectableOption = Array.from(favouriteSelect.options).some(option => option.value);
        const hasSelectedOption = Array.from(favouriteSelect.options).some(
            option => option.value === effectiveSelectedId
        );

        if (!activeSelectedId && matchingSelectedId && hasSelectedOption) {
            // Server-rendered URL state that cleanly matches a favourite should
            // become the remembered favourite for later shell navigation.
            setPendingSelectedFilterFavouriteId(root, favouritesContainer, matchingSelectedId);
            clearSelectedFilterFavouriteDirty(root, favouritesContainer);
        }

        if (hasSelectedOption && favouriteSelect.value !== effectiveSelectedId) {
            favouriteSelect.value = effectiveSelectedId;
        } else if (!effectiveSelectedId) {
            favouriteSelect.value = '';
        } else if (!hasSelectedOption) {
            favouriteSelect.value = '';
            setPendingSelectedFilterFavouriteId(root, favouritesContainer, '');
        }

        const hasSelectedFavourite = Boolean(getFavouriteSelectValue(favouriteSelect));
        favouritesContainer
            .querySelectorAll('[data-powercrud-favourite-manage-action="true"]')
            .forEach(button => {
                button.disabled = favouriteSelect.disabled || !hasSelectableOption || !hasSelectedFavourite;
            });
        syncFilterFavouritesTriggerLabel(favouritesContainer);

        const activeToolbar = getFilterFavouritesToolbarFromElement(activeFilterFavouritesPanel);
        if (activeToolbar !== favouritesContainer) {
            return;
        }

        const floatingSelect = getFilterFavouritesSelect(activeFilterFavouritesPanel);
        if (!(floatingSelect instanceof HTMLSelectElement)) {
            return;
        }

        if (hasSelectedOption && floatingSelect.value !== effectiveSelectedId) {
            floatingSelect.value = effectiveSelectedId;
        } else if (!effectiveSelectedId) {
            floatingSelect.value = '';
        } else if (!hasSelectedOption) {
            floatingSelect.value = '';
        }

        activeFilterFavouritesPanel
            .querySelectorAll('[data-powercrud-favourite-manage-action="true"]')
            .forEach(button => {
                button.disabled = floatingSelect.disabled || !hasSelectableOption || !Boolean(getFavouriteSelectValue(floatingSelect));
            });
    }

    function requestFavouriteApply(root, toolbar, favouriteSelect, options = {}) {
        const selectedFavouriteId = getFavouriteSelectValue(favouriteSelect);
        if (
            !(root instanceof Element)
            || !(toolbar instanceof Element)
            || !(favouriteSelect instanceof HTMLSelectElement)
            || !selectedFavouriteId
        ) {
            return;
        }

        const htmx = getHtmxInstance();
        if (!htmx) {
            return;
        }

        const actionForm = favouriteSelect.closest('form');
        const actionUrl = favouriteSelect.getAttribute('hx-get') || actionForm?.getAttribute('action') || '';
        if (!actionUrl) {
            return;
        }

        const isAutoApply = options.autoApply === true;
        const autoApplyKey = isAutoApply
            ? getFavouriteAutoApplyKey(root, toolbar, selectedFavouriteId)
            : '';
        if (autoApplyKey && favouriteAutoApplyInFlightKeys.has(autoApplyKey)) {
            return;
        }
        if (autoApplyKey) {
            favouriteAutoApplyInFlightKeys.add(autoApplyKey);
        }

        const toolbarSelect = getFilterFavouritesSelect(toolbar);
        if (
            toolbarSelect instanceof HTMLSelectElement
            && getFavouriteOptionByValue(toolbarSelect, selectedFavouriteId)
        ) {
            toolbarSelect.value = selectedFavouriteId;
        }
        setPendingSelectedFilterFavouriteId(root, toolbar, selectedFavouriteId);
        clearSelectedFilterFavouriteDirty(root, toolbar);
        suppressFavouriteAutoApplyOnce(root, toolbar);
        if (options.syncState !== false) {
            syncFavouriteToolbarState(toolbar);
        }

        const values = {};
        if (actionForm instanceof HTMLFormElement) {
            const formData = new FormData(actionForm);
            formData.forEach((value, key) => {
                values[key] = value;
            });
        }
        values.favourite_id = selectedFavouriteId;
        values.selected_favourite_id = selectedFavouriteId;

        const originalTargetField = actionForm?.querySelector('input[name="original_target"]');
        const originalTarget = originalTargetField instanceof HTMLInputElement
            ? originalTargetField.value
            : '';
        const target = originalTarget || favouriteSelect.getAttribute('hx-target') || root;
        const targetElement = resolveHtmxTargetElement(target);
        if (isAutoApply && hasNewerInteractiveRequestForTarget(targetElement)) {
            releaseFavouriteAutoApplyKey(autoApplyKey);
            return;
        }
        if (isAutoApply && targetElement instanceof Element) {
            favouriteAutoApplyContextsByTarget.set(targetElement, {
                listUrl: normaliseListUrl(root.dataset.powercrudListUrl || '', global),
                stale: false,
            });
        }

        const applyRequest = htmx.ajax('GET', actionUrl, {
            target,
            swap: 'innerHTML',
            values,
        });
        if (autoApplyKey) {
            if (applyRequest && typeof applyRequest.finally === 'function') {
                applyRequest.finally(() => {
                    global.setTimeout(() => releaseFavouriteAutoApplyKey(autoApplyKey), 1000);
                });
            } else {
                global.setTimeout(() => releaseFavouriteAutoApplyKey(autoApplyKey), 2000);
            }
        }
    }

    function maybeApplyRememberedFavourite(root) {
        if (!(root instanceof Element)) {
            return;
        }

        const toolbar = getFilterFavouritesContainer(root);
        const favouriteSelect = getFilterFavouritesSelect(toolbar);
        if (!(toolbar instanceof Element) || !(favouriteSelect instanceof HTMLSelectElement)) {
            return;
        }

        const selectedFavouriteId = getPendingSelectedFilterFavouriteId(root, toolbar);
        if (!selectedFavouriteId) {
            return;
        }

        const selectedOption = getFavouriteOptionByValue(favouriteSelect, selectedFavouriteId);
        if (!(selectedOption instanceof HTMLOptionElement)) {
            setPendingSelectedFilterFavouriteId(root, toolbar, '');
            return;
        }

        if (favouriteStateMatchesRoot(selectedOption, root, toolbar)) {
            if (
                favouriteStateMatchesCollectedRoot(selectedOption, root)
                && !isSelectedFilterFavouriteDirtyProtected(root, toolbar)
            ) {
                clearSelectedFilterFavouriteDirty(root, toolbar);
            }
            if (shouldConsumeFavouriteAutoApplySuppression(root, toolbar)) {
                return;
            }
            return;
        }

        if (isSelectedFilterFavouriteDirty(root, toolbar, selectedFavouriteId)) {
            return;
        }

        if (shouldConsumeFavouriteAutoApplySuppression(root, toolbar)) {
            return;
        }

        if (!getHtmxInstance()) {
            return;
        }

        favouriteSelect.value = selectedFavouriteId;
        requestFavouriteApply(root, toolbar, favouriteSelect, {
            autoApply: true,
            syncState: false,
        });
    }

    function syncSelectedFilterFavouritePresentation(root) {
        syncFilterFavouritesSelection(root);
    }

    function clearSelectedFilterFavouriteSelection(root, toolbar = null) {
        const favouritesContainer = toolbar instanceof Element
            ? toolbar
            : getFilterFavouritesContainer(root);
        if (!(favouritesContainer instanceof Element)) {
            return;
        }

        const favouriteSelect = getFilterFavouritesSelect(favouritesContainer);
        if (favouriteSelect) {
            favouriteSelect.value = '';
        }
        const selectedFavouriteField = favouritesContainer.querySelector('input[name="selected_favourite_id"]');
        if (selectedFavouriteField instanceof HTMLInputElement) {
            selectedFavouriteField.value = '';
        }

        setPendingSelectedFilterFavouriteId(root, favouritesContainer, '');
        clearSelectedFilterFavouriteDirty(root, favouritesContainer);
        syncSelectedFilterFavouritePresentation(root);
    }

    function syncFavouriteToolbarState(toolbar) {
        if (!(toolbar instanceof Element)) {
            return;
        }

        const root = getObjectListRoot(toolbar);
        if (!root) {
            return;
        }

        const stateJson = JSON.stringify(collectFavouriteStateFromRoot(root));
        toolbar
            .querySelectorAll('input[name="current_state_json"], input[name="state_json"]')
            .forEach(field => {
                if (field instanceof HTMLInputElement) {
                    field.value = stateJson;
                }
            });

        const favouriteSelect = getFilterFavouritesSelect(toolbar);
        const selectedFavouriteField = toolbar.querySelector('input[name="selected_favourite_id"]');
        if (favouriteSelect) {
            const selectedFavouriteId = getFavouriteSelectValue(favouriteSelect);
            if (selectedFavouriteId) {
                setPendingSelectedFilterFavouriteId(root, toolbar, selectedFavouriteId);
            }
            if (selectedFavouriteField instanceof HTMLInputElement) {
                selectedFavouriteField.value = selectedFavouriteId;
            }
        }
    }

    function syncFavouritePanelState(panel, toolbar) {
        if (!(panel instanceof Element) || !(toolbar instanceof Element)) {
            return;
        }

        const root = getObjectListRoot(toolbar);
        if (!root) {
            return;
        }

        const stateJson = JSON.stringify(collectFavouriteStateFromRoot(root));
        panel
            .querySelectorAll('input[name="current_state_json"], input[name="state_json"]')
            .forEach(field => {
                if (field instanceof HTMLInputElement) {
                    field.value = stateJson;
                }
            });

        const toolbarSelect = getFilterFavouritesSelect(toolbar);
        const panelSelect = getFilterFavouritesSelect(panel);
        const selectedFavouriteId = getFavouriteSelectValue(panelSelect)
            || getFavouriteSelectValue(toolbarSelect)
            || getPendingSelectedFilterFavouriteId(root, toolbar)
            || '';
        if (panelSelect instanceof HTMLSelectElement) {
            panelSelect.value = selectedFavouriteId;
        }
        panel.querySelectorAll('input[name="selected_favourite_id"]').forEach(field => {
            if (field instanceof HTMLInputElement) {
                field.value = selectedFavouriteId;
            }
        });

        const hasSelectableOption = panelSelect instanceof HTMLSelectElement
            ? Array.from(panelSelect.options).some(option => option.value)
            : false;
        panel
            .querySelectorAll('[data-powercrud-favourite-manage-action="true"]')
            .forEach(button => {
                button.disabled = !(panelSelect instanceof HTMLSelectElement)
                    || panelSelect.disabled
                    || !hasSelectableOption
                    || !Boolean(getFavouriteSelectValue(panelSelect));
            });
    }

    function copyFilterFavouritesPanelMarkupToTemplate(sourcePanel) {
        if (!(sourcePanel instanceof HTMLElement)) {
            return;
        }

        const toolbar = getFilterFavouritesToolbarFromElement(sourcePanel);
        const template = getFilterFavouritesTemplate(toolbar);
        const templatePanel = template?.querySelector('[data-powercrud-filter-favourites-panel="true"]');
        if (!(templatePanel instanceof HTMLElement)) {
            return;
        }

        templatePanel.innerHTML = sourcePanel.innerHTML;
    }

    function openFilterFavouritesPanel(trigger) {
        if (!(trigger instanceof HTMLElement)) {
            return;
        }

        const toolbar = trigger.closest('[data-powercrud-filter-favourites-toolbar="true"]');
        const template = getFilterFavouritesTemplate(toolbar);
        if (!(toolbar instanceof Element) || !(template instanceof HTMLElement)) {
            return;
        }

        closeFilterFavouritesDropdowns();

        const panelShell = template.firstElementChild?.cloneNode(true);
        if (!(panelShell instanceof HTMLElement)) {
            return;
        }

        // Panel geometry and HTMX processing are adapter work; favourite state
        // is synced before the cloned panel is shown.
        prepareFilterFavouritesFloatingPanel?.(panelShell, toolbar);

        const panel = panelShell.querySelector('[data-powercrud-filter-favourites-panel="true"]');
        if (!(panel instanceof HTMLElement)) {
            return;
        }

        syncFavouriteToolbarState(toolbar);
        syncFavouritePanelState(panel, toolbar);

        documentObject.body.appendChild(panelShell);

        if (global.htmx?.process) {
            global.htmx.process(panelShell);
        }
        initPowercrudSearchableSelects(panelShell);
        initPowercrudTooltips(panelShell);
        positionFilterFavouritesPanel?.(panelShell, trigger);
        showPreparedFloatingPanel?.(panelShell);
        setFilterFavouritesDropdownOpen?.(toolbar, true);
        trigger.setAttribute('aria-expanded', 'true');
        activeFilterFavouritesPanel = panelShell;
        activeFilterFavouritesTrigger = trigger;
    }

    function toggleFilterFavouritesPanel(trigger) {
        if (!(trigger instanceof HTMLElement)) {
            return;
        }

        if (
            activeFilterFavouritesTrigger === trigger
            && activeFilterFavouritesPanel instanceof HTMLElement
        ) {
            closeFilterFavouritesDropdowns();
            return;
        }

        openFilterFavouritesPanel(trigger);
    }

    function findObjectListRootByListUrl(listUrl) {
        const normalizedTarget = normaliseListUrl(listUrl, global);
        return getAffectedObjectListRoots(documentObject).find(root => {
            return normaliseListUrl(root?.dataset?.powercrudListUrl, global) === normalizedTarget;
        }) || null;
    }

    function getDetachedListColumnsRoot(target) {
        if (!(target instanceof Element)) {
            return null;
        }

        const floatingPanel = target.closest('[data-powercrud-list-columns-floating-panel="true"]');
        if (!(floatingPanel instanceof HTMLElement)) {
            return null;
        }

        const containerId = floatingPanel.dataset.powercrudListColumnsDomId || '';
        const sourceContainer = containerId ? documentObject.getElementById(containerId) : null;
        const sourceRoot = sourceContainer instanceof Element
            ? getObjectListRoot(sourceContainer)
            : null;
        if (sourceRoot instanceof Element) {
            return sourceRoot;
        }

        const listUrlField = floatingPanel.querySelector('input[name="list_view_url"]');
        const listUrl = listUrlField instanceof HTMLInputElement ? listUrlField.value : '';
        return findObjectListRootByListUrl(listUrl);
    }

    function populateFavouriteSaveForm(form) {
        if (!(form instanceof HTMLFormElement)) {
            return;
        }

        const listUrlField = form.querySelector('input[name="list_view_url"]');
        const listUrl = listUrlField instanceof HTMLInputElement ? listUrlField.value : '';
        const root = findObjectListRootByListUrl(listUrl) || getAffectedObjectListRoots(documentObject)[0];
        if (!root) {
            return;
        }

        const stateJson = JSON.stringify(collectFavouriteStateFromRoot(root));
        const stateField = form.querySelector('input[name="state_json"]');
        if (stateField instanceof HTMLInputElement) {
            stateField.value = stateJson;
        }

        const currentStateField = form.querySelector('input[name="current_state_json"]');
        if (currentStateField instanceof HTMLInputElement) {
            currentStateField.value = stateJson;
        }

        const nameField = form.querySelector('input[name="name"]');
        if (nameField instanceof HTMLInputElement) {
            global.requestAnimationFrame(() => {
                nameField.focus();
                nameField.select?.();
            });
        }
    }

    function toggleFavouriteSaveForm(trigger, isVisible) {
        const triggerElement = asElement(trigger);
        const toolbar = getFilterFavouritesToolbarFromElement(triggerElement);
        const saveForm = triggerElement?.closest('[data-powercrud-favourite-save-form="true"]')
            || activeFilterFavouritesPanel?.querySelector('[data-powercrud-favourite-save-form="true"]')
            || toolbar?.querySelector('[data-powercrud-favourite-save-form="true"]');
        if (!(saveForm instanceof HTMLFormElement)) {
            return;
        }

        saveForm.hidden = !isVisible;
        if (isVisible) {
            populateFavouriteSaveForm(saveForm);
            return;
        }

        const nameField = saveForm.querySelector('input[name="name"]');
        if (nameField instanceof HTMLInputElement && !saveForm.querySelector('.text-error')) {
            nameField.value = '';
        }
    }

    function handleFavouritesTriggerClick(event, trigger) {
        const favouritesTrigger = trigger.closest('[data-powercrud-filter-favourites-trigger="true"]');
        if (!favouritesTrigger) {
            return false;
        }
        event.preventDefault();
        toggleFilterFavouritesPanel(favouritesTrigger);
        return true;
    }

    function handleResetViewClick(event, trigger) {
        const resetViewTrigger = trigger.closest('[data-powercrud-reset-view="true"]');
        if (!resetViewTrigger) {
            return false;
        }
        event.preventDefault();
        const toolbar = getFilterFavouritesToolbarFromElement(resetViewTrigger);
        const root = toolbar ? getObjectListRoot(toolbar) : getAffectedObjectListRoots(documentObject)[0];
        if (root) {
            getListViewState().resetViewState?.(root);
        }
        return true;
    }

    function handleFavouriteApplyClick(event, trigger) {
        const favouriteApplyTrigger = trigger.closest('[data-powercrud-favourite-apply="true"]');
        if (!favouriteApplyTrigger) {
            return false;
        }

        const actionForm = favouriteApplyTrigger.closest('form');
        const favouriteSelect = actionForm?.querySelector('select[name="favourite_id"]');
        if (favouriteSelect instanceof HTMLSelectElement && !getFavouriteSelectValue(favouriteSelect)) {
            event.preventDefault();
            favouriteSelect.reportValidity?.();
            return true;
        }

        const listUrlField = actionForm?.querySelector('input[name="list_view_url"]');
        const listUrl = listUrlField instanceof HTMLInputElement ? listUrlField.value : '';
        const root = getObjectListRoot(favouriteApplyTrigger) || findObjectListRootByListUrl(listUrl);
        if (root) {
            getListViewState().syncFilterToggleLabel?.(root);
        }
        return false;
    }

    function closeForOutsideClick(trigger) {
        if (
            !trigger.closest('[data-powercrud-filter-favourites-dropdown="true"]')
            && !trigger.closest('[data-powercrud-filter-favourites-floating-panel="true"]')
        ) {
            closeFilterFavouritesDropdowns();
        }
    }

    function handleFavouriteSelectChange(target) {
        if (!target.matches('[data-powercrud-favourite-select="true"]')) {
            return false;
        }

        const toolbar = getFilterFavouritesToolbarFromElement(target);
        const root = toolbar ? getObjectListRoot(toolbar) : null;
        if (!root || !(toolbar instanceof Element)) {
            return true;
        }
        syncFavouriteToolbarState(toolbar);
        const activePanel = getFilterFavouritesPanelFromElement(target);
        if (activePanel instanceof Element) {
            syncFavouritePanelState(activePanel, toolbar);
        }
        if (!target.value) {
            setPendingSelectedFilterFavouriteId(root, toolbar, '');
            clearSelectedFilterFavouriteDirty(root, toolbar);
            syncFilterFavouritesSelection(root);
            getListViewState().rememberCurrentViewState?.(root);
            return true;
        }

        const selectedOption = getSelectedFavouriteOption(target);
        if (!(selectedOption instanceof HTMLOptionElement)) {
            return true;
        }

        const visibleFilterNames = getFavouriteVisibleFilterNames(selectedOption);
        getListViewState().setStoredOptionalFilterNames?.(root, visibleFilterNames);
        getListViewState().setPersistedOptionalFilterNames?.(root, visibleFilterNames);
        setPendingSelectedFilterFavouriteId(root, toolbar, target.value);
        clearSelectedFilterFavouriteDirty(root, toolbar);
        requestFavouriteApply(root, toolbar, target);
        closeFilterFavouritesDropdowns();
        return true;
    }

    function handleHtmxBeforeRequest(event, target) {
        if (trackFavouriteAutoApplyRequest(event, target)) {
            return true;
        }

        if (!target || !target.closest) {
            return false;
        }

        const root = getObjectListRoot(target);
        const detachedListColumnsRoot = getDetachedListColumnsRoot(target);
        const isDetachedListColumnsRequest = detachedListColumnsRoot instanceof Element;
        const favouritesToolbar = getFilterFavouritesToolbarFromElement(target)
            || (root ? getFilterFavouritesContainer(root) : null)
            || (detachedListColumnsRoot ? getFilterFavouritesContainer(detachedListColumnsRoot) : null);
        const effectiveRoot = root || detachedListColumnsRoot || (favouritesToolbar instanceof Element
            ? getObjectListRoot(favouritesToolbar)
            : null);
        const isFavouriteSelectRequest = (
            target.matches('[data-powercrud-favourite-select="true"]')
            || Boolean(target.closest('[data-powercrud-favourite-select="true"]'))
        );
        const isFavouriteManageRequest = (
            target.matches('[data-powercrud-favourite-manage-action="true"]')
            || Boolean(target.closest('[data-powercrud-favourite-manage-action="true"]'))
        );
        const isInlineRequest = isInlineEditRequest(target);
        if (
            effectiveRoot instanceof Element
            && (
                target === effectiveRoot
                || effectiveRoot.contains(target)
                || isDetachedListColumnsRequest
            )
            && !isFavouriteSelectRequest
            && !isFavouriteManageRequest
            && !isInlineRequest
        ) {
            suppressFavouriteAutoApplyOnce(effectiveRoot, favouritesToolbar);
            markSelectedFilterFavouriteDirty(effectiveRoot, favouritesToolbar);
        }
        if (effectiveRoot && favouritesToolbar instanceof Element) {
            const favouriteSelect = getFilterFavouritesSelect(favouritesToolbar);
            const selectedFavouriteId = getFavouriteSelectValue(favouriteSelect)
                || getServerSelectedFilterFavouriteId(favouritesToolbar);
            setPendingSelectedFilterFavouriteId(
                effectiveRoot,
                favouritesToolbar,
                selectedFavouriteId,
            );
        }

        if (!(favouritesToolbar instanceof Element)) {
            return false;
        }

        syncFavouriteToolbarState(favouritesToolbar);
        const activePanel = getFilterFavouritesPanelFromElement(target);
        if (activePanel instanceof Element) {
            syncFavouritePanelState(activePanel, favouritesToolbar);
        }

        if (isFavouriteManageRequest) {
            const favouriteSelect = getFilterFavouritesSelect(favouritesToolbar);
            if (!getFavouriteSelectValue(favouriteSelect)) {
                event.preventDefault();
                return true;
            }
        }

        if (isFavouriteSelectRequest) {
            const favouriteSelect = target.matches('[data-powercrud-favourite-select="true"]')
                ? target
                : target.closest('[data-powercrud-favourite-select="true"]');
            if (!getFavouriteSelectValue(favouriteSelect)) {
                event.preventDefault();
                return true;
            }
            event.preventDefault();
            return true;
        }

        return false;
    }

    function handleHtmxAfterSwap(event) {
        const requestTarget = getHtmxRequestTarget(event);
        const requestConfig = getHtmxRequestConfig(event);
        if (
            requestTarget instanceof Element
            && requestConfig?.powercrudFavouriteInteractiveRequestVersion
        ) {
            currentSwapRequestVersionByTarget.set(
                requestTarget,
                requestConfig.powercrudFavouriteInteractiveRequestVersion,
            );
        }
    }

    function handleHtmxAfterRequest(event) {
        releaseTrackedFavouriteAutoApplyRequest(event);
    }

    function handleHtmxConfigRequest(event, target) {
        const favouritesToolbar = getFilterFavouritesToolbarFromElement(target);
        if (!(favouritesToolbar instanceof Element)) {
            return;
        }

        const root = getObjectListRoot(favouritesToolbar);
        if (!root) {
            return;
        }

        const stateJson = JSON.stringify(collectFavouriteStateFromRoot(root));
        if (event.detail && event.detail.parameters) {
            event.detail.parameters.current_state_json = stateJson;
            event.detail.parameters.state_json = stateJson;
        }

        const activePanel = getFilterFavouritesPanelFromElement(target);
        if (activePanel instanceof Element) {
            syncFavouritePanelState(activePanel, favouritesToolbar);
        }
    }

    function handleFavouriteSaved(event) {
        const favouriteId = String(
            event?.detail?.favouriteId
            || event?.detail?.value?.favouriteId
            || ''
        ).trim();
        getAffectedObjectListRoots(documentObject).forEach(root => {
            const toolbar = getFilterFavouritesContainer(root);
            if (!(toolbar instanceof Element)) {
                return;
            }
            setPendingSelectedFilterFavouriteId(root, toolbar, favouriteId);
            clearSelectedFilterFavouriteDirty(root, toolbar);
            syncFilterFavouritesSelection(root);
        });
        global.setTimeout(() => {
            closeFilterFavouritesDropdowns();
        }, 0);
    }

    function handleFavouriteUpdated(event) {
        const favouriteId = String(
            event?.detail?.favouriteId
            || event?.detail?.value?.favouriteId
            || ''
        ).trim();
        getAffectedObjectListRoots(documentObject).forEach(root => {
            const toolbar = getFilterFavouritesContainer(root);
            if (!(toolbar instanceof Element)) {
                return;
            }
            setPendingSelectedFilterFavouriteId(root, toolbar, favouriteId);
            clearSelectedFilterFavouriteDirty(root, toolbar);
            syncFilterFavouritesSelection(root);
        });
        global.setTimeout(() => {
            closeFilterFavouritesDropdowns();
        }, 0);
    }

    function handleFavouriteDeleted() {
        getAffectedObjectListRoots(documentObject).forEach(root => {
            const toolbar = getFilterFavouritesContainer(root);
            if (!(toolbar instanceof Element)) {
                return;
            }
            setPendingSelectedFilterFavouriteId(root, toolbar, '');
            clearSelectedFilterFavouriteDirty(root, toolbar);
            syncFilterFavouritesSelection(root);
        });
        global.setTimeout(() => {
            closeFilterFavouritesDropdowns();
        }, 0);
    }

    function handleHtmxAfterSwapTarget(target) {
        if (!(target instanceof HTMLElement)) {
            return;
        }

        const favouritePanel = target.matches('[data-powercrud-filter-favourites-panel="true"]')
            ? target
            : target.querySelector('[data-powercrud-filter-favourites-panel="true"]');
        if (favouritePanel instanceof HTMLElement) {
            copyFilterFavouritesPanelMarkupToTemplate(favouritePanel);
            const toolbar = getFilterFavouritesToolbarFromElement(favouritePanel);
            const root = toolbar ? getObjectListRoot(toolbar) : null;
            if (root && toolbar instanceof Element) {
                syncFilterFavouritesSelection(root);
                syncFavouritePanelState(favouritePanel, toolbar);
            }
        }

        const favouriteSaveForm = target.matches('[data-powercrud-favourite-save-form="true"]')
            ? target
            : target.querySelector('[data-powercrud-favourite-save-form="true"]');
        if (favouriteSaveForm instanceof HTMLFormElement) {
            populateFavouriteSaveForm(favouriteSaveForm);
        }
    }

    return {
        clearSelectedFilterFavouriteSelection,
        closeFilterFavouritesDropdowns,
        closeForOutsideClick,
        getFilterFavouritesContainer,
        getFilterFavouritesPanelFromElement,
        getFilterFavouritesSelect,
        getFilterFavouritesToolbarFromElement,
        getFavouriteSelectValue,
        getSelectedFilterFavouriteViewContext,
        getServerSelectedFilterFavouriteId,
        handleFavouriteApplyClick,
        handleFavouriteDeleted,
        handleFavouriteSaved,
        handleFavouriteSelectChange,
        handleFavouriteUpdated,
        handleFavouritesTriggerClick,
        handleHtmxAfterSwap,
        handleHtmxAfterSwapTarget,
        handleHtmxAfterRequest,
        handleHtmxBeforeRequest,
        handleHtmxConfigRequest,
        handleResetViewClick,
        markSelectedFilterFavouriteDirty,
        maybeApplyRememberedFavourite,
        suppressFavouriteAutoApplyOnce,
        syncSelectedFilterFavouritePresentation,
        syncFavouritePanelState,
        syncFavouriteToolbarState,
        syncFilterFavouritesSelection,
        toggleFavouriteSaveForm,
    };
}
