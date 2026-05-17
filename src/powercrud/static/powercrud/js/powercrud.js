import { installPowercrudGlobalListeners } from './runtime/startup.js';
import {
    RANGE_SELECT_SUPPRESS_CLASS,
    TOOLTIP_TRIGGER_SELECTOR,
} from './runtime/selectors.js';
import {
    asElement,
    getAffectedObjectListRoots,
    getObjectListRoot,
    getRootSwapTarget,
    isElementVisible,
} from './runtime/dom.js';
import {
    getHtmxInstance as resolveHtmxInstance,
    getHtmxEventRoots,
} from './runtime/htmx.js';
import { createWeakStateStore } from './runtime/state.js';
import { createListViewStateRuntime } from './runtime/list-view-state.js';
import { createFilterFavouritesRuntime } from './runtime/filter-favourites.js';
import { createListColumnsRuntime } from './runtime/list-columns.js';
import { createBulkActionsRuntime } from './runtime/bulk-actions.js';
import { createInlineEditRuntime } from './runtime/inline-edit.js';
import { createSearchableSelectRuntime } from './runtime/searchable-selects.js';
import { createCurrentTemplateRuntime } from './runtime/current-template.js';

(function powercrudRuntime(global) {
    'use strict';

    // This file is the stable public entry. Internal modules are wired here so
    // the public static path can stay fixed while implementation boundaries move.
    if (global.__powercrudRuntimeLoaded) {
        return;
    }
    global.__powercrudRuntimeLoaded = true;

    const warnedDeps = {
        htmx: false,
        tippy: false,
        tomSelect: false,
    };

    const ensureObjectListState = createWeakStateStore(() => ({
        filterRefreshTimer: null,
        lastRowSelectionAnchorId: null,
        optionalFilterVisibilityRestored: false,
        selectionRequestVersion: 0,
    }));
    function warnMissingDependency(name, detail) {
        if (warnedDeps[name]) {
            return;
        }
        warnedDeps[name] = true;
        console.warn(`PowerCRUD frontend: missing ${detail}.`);
    }

    function getHtmxInstance() {
        return resolveHtmxInstance(global, warnMissingDependency);
    }

    function normalizeFilterFieldHtmxUrls(root) {
        if (!(root instanceof Element)) {
            return;
        }

        const listUrl = root.dataset.powercrudListUrl || '';
        const filterForm = root.querySelector('#filter-form');
        if (!listUrl || !(filterForm instanceof HTMLFormElement)) {
            return;
        }

        filterForm.querySelectorAll('[hx-get]').forEach(field => {
            if (!(field instanceof HTMLElement)) {
                return;
            }
            if (field.getAttribute('hx-get') !== '') {
                return;
            }
            field.setAttribute('hx-get', listUrl);
        });
    }

    const searchableSelects = createSearchableSelectRuntime({
        global,
        documentObject: document,
        warnMissingDependency,
        isElementVisible,
    });
    const {
        destroyPowercrudSearchableSelects,
        initPowercrudSearchableSelects,
        syncTomSelectValues,
    } = searchableSelects;

    const currentTemplate = createCurrentTemplateRuntime({
        global,
        documentObject: document,
        warnMissingDependency,
        getHtmxInstance,
    });
    const {
        applyPowercrudModalClasses,
        cleanupDuplicatePowercrudModals,
        closeRowActionsMenu,
        destroyPowercrudTooltips,
        hidePowercrudTooltips,
        initPowercrudTooltips,
        schedulePowercrudTooltipRefresh,
        schedulePowercrudTooltipResizeRefresh,
        startButtonSpinner,
        startFormSpinner,
        stopButtonSpinner,
        stopFormSpinner,
        syncListToolbarWidth,
        syncListToolbarWidths,
        toggleRowActionsMenu,
    } = currentTemplate;

    const listColumns = createListColumnsRuntime({
        global,
        documentObject: document,
        applyListColumnOptionVisualState: currentTemplate.applyListColumnOptionVisualState,
        clearListColumnChooserPlacement: currentTemplate.clearListColumnChooserPlacement,
        syncListColumnChooserPlacement: currentTemplate.syncListColumnChooserPlacement,
    });

    const inlineEdit = createInlineEditRuntime({
        global,
        documentObject: document,
        getHtmxInstance,
        initPowercrudSearchableSelects,
        syncTomSelectValues,
        toggleInlineSaveSpinner: currentTemplate.toggleInlineSaveSpinner,
    });

    // Favourites need list-view state helpers, while list-view state also needs
    // favourite dirty/selection helpers. The late-bound reference keeps that
    // collaboration explicit without merging the runtimes back together.
    let listViewStateApi = null;
    const filterFavourites = createFilterFavouritesRuntime({
        global,
        documentObject: document,
        getHtmxInstance,
        initPowercrudSearchableSelects,
        initPowercrudTooltips,
        schedulePowercrudTooltipRefresh,
        prepareFilterFavouritesFloatingPanel: currentTemplate.prepareFilterFavouritesFloatingPanel,
        positionFilterFavouritesPanel: currentTemplate.positionFilterFavouritesPanel,
        setFilterFavouritesDropdownOpen: currentTemplate.setFilterFavouritesDropdownOpen,
        showPreparedFloatingPanel: currentTemplate.showPreparedFloatingPanel,
        syncFilterFavouritesTriggerPresentation: currentTemplate.syncFilterFavouritesTriggerPresentation,
        getListViewStateApi: () => listViewStateApi,
        isInlineEditRequest: inlineEdit.isInlineEditRequest,
    });

    const listViewState = createListViewStateRuntime({
        global,
        documentObject: document,
        ensureObjectListState,
        getHtmxInstance,
        getObjectListRoot,
        getRootSwapTarget,
        getVisibleListColumnNames: listColumns.getVisibleListColumnNames,
        buildListColumnResetRequest: listColumns.buildListColumnResetRequest,
        initPowercrudSearchableSelects,
        schedulePowercrudTooltipRefresh,
        getFilterFavouritesContainer: filterFavourites.getFilterFavouritesContainer,
        getSelectedFilterFavouriteViewContext: filterFavourites.getSelectedFilterFavouriteViewContext,
        markSelectedFilterFavouriteDirty: filterFavourites.markSelectedFilterFavouriteDirty,
        clearSelectedFilterFavouriteSelection: filterFavourites.clearSelectedFilterFavouriteSelection,
        closeFilterFavouritesDropdowns: filterFavourites.closeFilterFavouritesDropdowns,
        syncSelectedFilterFavouritePresentation: filterFavourites.syncSelectedFilterFavouritePresentation,
    });
    listViewStateApi = listViewState;

    const {
        addOptionalFilter,
        applyFilterPanelState,
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
        resetViewState,
        scheduleFilterValueRefresh,
        syncFilterToggleLabel,
        toggleFilterVisibility,
    } = listViewState;

    const bulkActions = createBulkActionsRuntime({
        global,
        documentObject: document,
        ensureObjectListState,
        getHtmxInstance,
        getObjectListRoot,
        getAffectedObjectListRoots,
        getCurrentFilters,
        closePowercrudModals: currentTemplate.closePowercrudModals,
        syncSelectionAwareButtonVisualState: currentTemplate.syncSelectionAwareButtonVisualState,
    });

    function bootstrapObjectList(root) {
        if (!(root instanceof Element)) {
            return;
        }
        // Bring the list root back to a coherent state after render/swap:
        // normalize HTMX targets, restore list state, then refresh UI affordances.
        cleanupDuplicatePowercrudModals();
        ensureObjectListState(root);
        normalizeFilterFieldHtmxUrls(root);
        syncListToolbarWidth(root);
        bulkActions.hydrateBulkSelectionState(root);
        applyFilterPanelState(root);
        maybeRestoreStoredOptionalFilterVisibility(root);
        listColumns.syncListColumnChoosers(root);
        filterFavourites.syncFilterFavouritesSelection(root);
        filterFavourites.maybeApplyRememberedFavourite(root);
        if (!maybeRestoreStoredViewState(root)) {
            rememberCurrentViewState(root);
        }
        bulkActions.syncBulkSelectionPresentation(root);
    }

    function bootstrapObjectLists(scope = document) {
        getAffectedObjectListRoots(scope).forEach(bootstrapObjectList);
    }

    function initPowercrud(fragment = document) {
        // Public fragment lifecycle: enhance controls, restore list state, then
        // recreate tooltips after the final visible markup is in place.
        initPowercrudSearchableSelects(fragment);
        bootstrapObjectLists(fragment);
        initPowercrudTooltips(fragment);
    }

    function destroyPowercrudFragment(fragment) {
        // Restore library-enhanced controls before HTMX removes their source
        // markup, and clear detached body-level UI tied to the fragment.
        destroyPowercrudSearchableSelects(fragment);
        destroyPowercrudTooltips(fragment);
        inlineEdit.destroyInlineFieldErrorPopovers(fragment);
    }

    function installPowercrudPublicGlobals(global) {
        global.getCurrentFilters = getCurrentFilters;
        global.initPowercrud = initPowercrud;
        global.initPowercrudSearchableSelects = initPowercrudSearchableSelects;
        global.destroyPowercrudSearchableSelects = destroyPowercrudSearchableSelects;
        global.initPowercrudTooltips = initPowercrudTooltips;
        global.hidePowercrudTooltips = hidePowercrudTooltips;
        global.destroyPowercrudTooltips = destroyPowercrudTooltips;
        global.powercrudToggleFavouriteSaveForm = filterFavourites.toggleFavouriteSaveForm;
    }

    function createPowercrudGlobalListenerHandlers() {
        return {
            handleDOMContentLoaded() {
                const htmx = global.htmx;
                if (htmx?.process) {
                    htmx.process(document.body);
                } else {
                    warnMissingDependency('htmx', 'window.htmx. Load HTMX before powercrud/js/powercrud.js');
                }

                initPowercrud(document);
                inlineEdit.bootstrapInlineRow();
            },
            handlePageShow() {
                const resyncRestoredState = () => {
                    initPowercrud(document);
                };
                resyncRestoredState();
                global.setTimeout(resyncRestoredState, 50);
            },
            handlePointerDownCapture() {
                hidePowercrudTooltips(document);
            },
            handleTooltipClickCapture() {
                global.setTimeout(() => {
                    hidePowercrudTooltips(document);
                }, 0);
            },
            handleInlineDocumentClickCapture(event) {
                const trigger = asElement(event.target);
                inlineEdit.handleDocumentClickCapture(event, trigger);
            },
            handleModalClassClickCapture(event) {
                applyPowercrudModalClasses(asElement(event.target));
            },
            handleFocusInCapture(event) {
                const focusedElement = asElement(event.target);
                if (!focusedElement?.closest(TOOLTIP_TRIGGER_SELECTOR)) {
                    hidePowercrudTooltips(document);
                }
            },
            handlePageHide() {
                hidePowercrudTooltips(document);
                closeRowActionsMenu();
                listColumns.closeListColumnChoosers(document);
                filterFavourites.closeFilterFavouritesDropdowns();
            },
            handleDocumentClick(event) {
                const trigger = asElement(event.target);
                if (!trigger) {
                    return;
                }

                const filterToggle = trigger.closest('[data-powercrud-filter-toggle]');
                if (filterToggle) {
                    const root = getObjectListRoot(filterToggle);
                    if (root) {
                        toggleFilterVisibility(root);
                    }
                    return;
                }

                const rowActionsTrigger = trigger.closest('[data-powercrud-row-actions-trigger="true"]');
                if (rowActionsTrigger instanceof HTMLElement) {
                    event.preventDefault();
                    toggleRowActionsMenu(rowActionsTrigger);
                    return;
                }

                const floatingRowActionsPanel = trigger.closest('[data-powercrud-row-actions-floating-panel="true"]');
                if (floatingRowActionsPanel instanceof Element) {
                    const actionableElement = trigger.closest('a, button');
                    if (
                        actionableElement instanceof HTMLElement
                        && actionableElement.getAttribute('aria-disabled') !== 'true'
                        && !actionableElement.classList.contains('pointer-events-none')
                    ) {
                        global.setTimeout(() => {
                            closeRowActionsMenu();
                        }, 0);
                    }
                    return;
                }

                if (filterFavourites.handleFavouritesTriggerClick(event, trigger)) {
                    return;
                }

                if (filterFavourites.handleResetViewClick(event, trigger)) {
                    return;
                }

                const resetTrigger = trigger.closest('[data-powercrud-filter-reset]');
                if (resetTrigger) {
                    const root = getObjectListRoot(resetTrigger);
                    if (root) {
                        resetCurrentFilters(root);
                    }
                    return;
                }

                const removeFilterTrigger = trigger.closest('[data-powercrud-remove-filter]');
                if (removeFilterTrigger) {
                    const root = getObjectListRoot(removeFilterTrigger);
                    if (root) {
                        removeOptionalFilter(
                            root,
                            removeFilterTrigger.dataset.powercrudRemoveFilter || '',
                        );
                    }
                    return;
                }

                if (bulkActions.handleClearSelectionClick(trigger)) {
                    return;
                }

                if (filterFavourites.handleFavouriteApplyClick(event, trigger)) {
                    return;
                }

                filterFavourites.closeForOutsideClick(trigger);
                listColumns.closeForOutsideClick(trigger);
                closeRowActionsMenu();
            },
            handleDocumentToggleCapture(event) {
                listColumns.handleListColumnsToggle(event);
            },
            handleDocumentKeydown(event) {
                const target = asElement(event.target);
                inlineEdit.handleKeydown(event, target);
                if (event.key === 'Escape') {
                    listColumns.closeListColumnChoosers(document, true);
                    filterFavourites.closeFilterFavouritesDropdowns();
                    closeRowActionsMenu();
                }
            },
            handleDocumentScrollCapture() {
                closeRowActionsMenu();
            },
            handleRowSelectionClickCapture(event) {
                const target = asElement(event.target);
                bulkActions.handleRowSelectionClickCapture(event, target);
            },
            handleRowSelectionMouseDownCapture(event) {
                const target = asElement(event.target);
                bulkActions.handleRowSelectionMouseDownCapture(event, target);
            },
            handleDocumentChange(event) {
                const target = asElement(event.target);
                if (!target) {
                    return;
                }

                if (target.matches('[data-powercrud-select-all="true"]')) {
                    bulkActions.toggleAllSelection(target);
                    return;
                }

                if (target.matches('[data-powercrud-row-select="true"]')) {
                    bulkActions.handleRowSelectionChange(target, event);
                }

                if (listColumns.handleListColumnCheckboxChange(target)) {
                    return;
                }

                if (target.matches('[data-powercrud-add-filter-select]')) {
                    const root = getObjectListRoot(target);
                    if (!root || !target.value) {
                        return;
                    }
                    addOptionalFilter(root, target.value);
                    target.value = '';
                }

                if (target.matches('[data-powercrud-page-size-select="true"]')) {
                    const root = getObjectListRoot(target);
                    if (!root) {
                        return;
                    }
                    requestObjectListRefresh(root, { preservePage: false });
                    return;
                }

                if (filterFavourites.handleFavouriteSelectChange(target)) {
                    return;
                }
            },
            handleFilterInput(event) {
                const target = asElement(event.target);
                if (isFilterValueField(target)) {
                    scheduleFilterValueRefresh(target);
                }
            },
            handleFilterChange(event) {
                const target = asElement(event.target);
                if (isFilterValueField(target)) {
                    scheduleFilterValueRefresh(target, { immediate: true });
                }
            },
            handleDocumentSubmitCapture(event) {
                const form = asElement(event.target);
                if (!form) {
                    return;
                }
                if (form.matches('[data-powercrud-filter-form="true"]')) {
                    removeEmptyFields(form);
                }
                if (form.matches('[data-powercrud-form="object"], [data-powercrud-form="bulk"]')) {
                    startFormSpinner(form);
                    if (form.matches('[data-powercrud-form="bulk"]')) {
                        bulkActions.setBulkActionButtonsDisabled(form, true);
                    }
                }
            },
            handleHtmxBeforeRequest(event) {
                hidePowercrudTooltips(document);

                const target = event.detail && event.detail.elt;
                if (isFilterValueField(target)) {
                    event.preventDefault();
                    return;
                }
                if (target && target.matches && target.matches('[data-powercrud-bulk-delete-submit]')) {
                    startButtonSpinner(target);
                }
                if (bulkActions.handleBulkHtmxBeforeRequest(event, target)) {
                    return;
                }

                if (filterFavourites.handleHtmxBeforeRequest(event, target)) {
                    return;
                }
            },
            handleHtmxConfigRequest(event) {
                const target = event.detail && event.detail.elt;
                if (!(target instanceof Element) || !target.closest) {
                    return;
                }

                const filterForm = target.matches('#filter-form')
                    ? target
                    : target.closest('#filter-form');
                const filterRoot = filterForm instanceof Element
                    ? getObjectListRoot(filterForm)
                    : null;
                if (filterRoot instanceof Element && filterRoot.dataset.powercrudListUrl) {
                    event.detail.path = filterRoot.dataset.powercrudListUrl;
                }

                filterFavourites.handleHtmxConfigRequest(event, target);
            },
            handleBulkEditSuccess: bulkActions.handleBulkEditSuccess,
            handleBulkEditQueued: bulkActions.handleBulkEditQueued,
            handleFavouriteSaved(event) {
                filterFavourites.handleFavouriteSaved(event);
            },
            handleFavouriteUpdated(event) {
                filterFavourites.handleFavouriteUpdated(event);
            },
            handleFavouriteDeleted() {
                filterFavourites.handleFavouriteDeleted();
            },
            handleRefreshTable(event) {
                const eventTarget = asElement(event.target);
                const root = getObjectListRoot(eventTarget) || getAffectedObjectListRoots(document)[0];
                const payload = event.detail && event.detail.value ? event.detail.value : (event.detail || {});
                if (root) {
                    bulkActions.refreshTable(root, { resetPage: payload.reset_page === true });
                }
            },
            handleHtmxBeforeSwap(event) {
                // Before a fragment is replaced, let feature runtimes cancel
                // stale swaps and tear down widgets tied to that DOM.
                hidePowercrudTooltips(document);

                if (bulkActions.handleBulkHtmxBeforeSwap(event)) {
                    return;
                }

                getHtmxEventRoots(event).forEach(destroyPowercrudFragment);
                closeRowActionsMenu();
                inlineEdit.handleHtmxBeforeSwap(event);
            },
            handleHtmxAfterSwap(event) {
                // Initialize swapped fragments first; the document bootstrap
                // below catches shell-level state shared across list roots.
                getHtmxEventRoots(event).forEach(initPowercrud);
                bootstrapObjectLists(document);
                schedulePowercrudTooltipRefresh(document, 50);

                const target = asElement(event.target);
                if (!(target instanceof HTMLElement)) {
                    return;
                }

                filterFavourites.handleHtmxAfterSwapTarget(target);

                if (inlineEdit.handleHtmxAfterSwapTarget(target)) {
                    return;
                }
            },
            handleHtmxAfterSettle(event) {
                // Settled dimensions are needed before layout-sensitive
                // controls such as tooltips and inline popovers are finalised.
                getHtmxEventRoots(event).forEach(root => {
                    initPowercrud(root);
                    inlineEdit.showInlineFieldErrorPopovers(root);
                });
                bootstrapObjectLists(document);
                const target = asElement(event.target);
                getAffectedObjectListRoots(target || document).forEach(rememberCurrentViewState);
                schedulePowercrudTooltipRefresh(document, 50);
                inlineEdit.removeOrphanedInlineFieldErrorPopovers();
            },
            handleInlineHtmxBeforeRequest(event) {
                inlineEdit.handleHtmxBeforeRequest(event);
            },
            handleHtmxAfterRequest(event) {
                const target = event.detail && event.detail.elt;
                if (target && target.matches && target.matches('[data-powercrud-form="object"], [data-powercrud-form="bulk"]')) {
                    stopFormSpinner(target);
                }
                if (target && target.matches && target.matches('[data-powercrud-bulk-delete-submit]')) {
                    stopButtonSpinner(target);
                }
                bulkActions.handleBulkHtmxAfterRequest(target);
                inlineEdit.handleHtmxAfterRequest(target);
            },
            handleHtmxResponseError(event) {
                const target = event.detail && event.detail.elt;
                if (target && target.matches && target.matches('[data-powercrud-form="object"], [data-powercrud-form="bulk"]')) {
                    stopFormSpinner(target);
                }
                if (target && target.matches && target.matches('[data-powercrud-bulk-delete-submit]')) {
                    stopButtonSpinner(target);
                }
                bulkActions.handleBulkHtmxResponseError(target);
                inlineEdit.handleHtmxResponseError(target);
            },
            handleInlineRowLocked(event) {
                inlineEdit.handleInlineGuardEvent(event);
            },
            handleInlineRowForbidden(event) {
                inlineEdit.handleInlineGuardEvent(event);
            },
            handleInlineRowSaved: inlineEdit.handleInlineSaved,
            handleInlineRowError(event) {
                inlineEdit.handleInlineError(event);
            },
            handleWindowResize() {
                closeRowActionsMenu();
                syncListToolbarWidths(document);
                inlineEdit.repositionInlineFieldErrorPopovers(document);
                schedulePowercrudTooltipResizeRefresh(document, 100);
            },
            handleWindowScrollCapture() {
                inlineEdit.repositionInlineFieldErrorPopovers(document);
            },
        };
    }

    function installPowercrudStartup() {
        installPowercrudGlobalListeners({
            globalObject: global,
            documentObject: document,
            rangeSelectClass: RANGE_SELECT_SUPPRESS_CLASS,
            handlers: createPowercrudGlobalListenerHandlers(),
        });
    }

    function installPowercrudRuntime(globalObject) {
        installPowercrudPublicGlobals(globalObject);
        installPowercrudStartup();
    }

    installPowercrudRuntime(global);
})(window);
