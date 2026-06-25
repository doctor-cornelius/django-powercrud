import { RANGE_SELECT_SUPPRESS_CLASS } from './selectors.js';

export function createBulkActionsRuntime(context) {
    const {
        global,
        documentObject,
        ensureObjectListState,
        getHtmxInstance,
        getObjectListRoot,
        getAffectedObjectListRoots,
        getCurrentFilters,
        closePowercrudModals,
        syncSelectionAwareButtonVisualState,
    } = context;

    function getBulkSelectionControls(root) {
        return {
            selectAllCheckbox: root?.querySelector?.('[data-powercrud-select-all="true"]') || null,
            rowCheckboxes: getRowSelectionCheckboxes(root),
            counter: root?.querySelector?.('#selected-items-counter') || null,
            actionsContainer: root?.querySelector?.('#bulk-actions-container') || null,
        };
    }

    function getSelectedBulkRowIds(root) {
        return getRowSelectionCheckboxes(root)
            .filter(checkbox => checkbox.checked)
            .map(checkbox => checkbox.dataset.id || '')
            .filter(Boolean);
    }

    function setBulkRowsChecked(root, checked) {
        getRowSelectionCheckboxes(root).forEach(checkbox => {
            checkbox.checked = checked;
        });
    }

    function getCounterValue(counter) {
        const selectedCount = Number.parseInt(counter?.textContent || '0', 10);
        return Number.isFinite(selectedCount) ? selectedCount : 0;
    }

    function syncSelectAllState(controls) {
        const { selectAllCheckbox, rowCheckboxes } = controls;
        if (!(selectAllCheckbox instanceof HTMLInputElement) || !rowCheckboxes.length) {
            return;
        }

        const selectedCount = rowCheckboxes.filter(checkbox => checkbox.checked).length;
        if (selectedCount === 0) {
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = false;
        } else if (selectedCount === rowCheckboxes.length) {
            selectAllCheckbox.checked = true;
            selectAllCheckbox.indeterminate = false;
        } else {
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = true;
        }
    }

    function syncBulkSelectionPresentation(root, explicitCount = null) {
        if (!(root instanceof Element)) {
            return;
        }

        const controls = getBulkSelectionControls(root);
        syncSelectAllState(controls);

        const selectedCount = explicitCount === null
            ? getCounterValue(controls.counter)
            : explicitCount;
        if (explicitCount !== null) {
            if (controls.counter) {
                controls.counter.textContent = selectedCount;
            }
            if (controls.actionsContainer) {
                controls.actionsContainer.classList.toggle('hidden', selectedCount === 0);
            }
        }
        syncSelectionAwareExtraButtons(root, selectedCount);
    }

    function showBulkActionsContainer(root) {
        const container = root.querySelector('#bulk-actions-container');
        if (container) {
            container.classList.remove('hidden');
        }
    }

    function syncSelectionAwareExtraButtons(root, explicitCount = null) {
        if (!(root instanceof Element)) {
            return;
        }
        const buttons = Array.from(root.querySelectorAll('[data-powercrud-selection-aware="true"]'));
        if (!buttons.length) {
            return;
        }

        let selectedCount = explicitCount;
        if (selectedCount === null) {
            const counter = root.querySelector('#selected-items-counter');
            selectedCount = Number.parseInt(counter?.textContent || '0', 10);
        }
        if (!Number.isFinite(selectedCount)) {
            selectedCount = 0;
        }

        buttons.forEach(button => {
            const minCount = Number.parseInt(button.dataset.powercrudSelectionMinCount || '0', 10);
            const behavior = button.dataset.powercrudSelectionMinBehavior || 'allow';
            const reason = button.dataset.powercrudSelectionMinReason || '';
            const disable = behavior === 'disable' && selectedCount < minCount;
            syncSelectionAwareButtonVisualState?.(button, { disable, reason });
        });
    }

    function syncBulkSelectionState(root) {
        syncSelectAllState(getBulkSelectionControls(root));
    }

    function clearBulkSelection(root) {
        if (!(root instanceof Element)) {
            return;
        }
        setBulkRowsChecked(root, false);
        ensureObjectListState(root).lastRowSelectionAnchorId = null;
        syncBulkSelectionPresentation(root, 0);
    }

    function clearSelectionOptimistic(root) {
        clearBulkSelection(root);
    }

    function getRowSelectionCheckboxes(root) {
        if (!(root instanceof Element)) {
            return [];
        }
        return Array.from(root.querySelectorAll('[data-powercrud-row-select="true"]'))
            .filter(checkbox => checkbox instanceof HTMLInputElement);
    }

    function hydrateCheckboxInitialState(checkbox) {
        if (
            !(checkbox instanceof HTMLInputElement)
            || checkbox.dataset.powercrudSelectionHydrated === 'true'
        ) {
            return;
        }
        checkbox.checked = checkbox.dataset.powercrudInitialChecked === 'true';
        checkbox.dataset.powercrudSelectionHydrated = 'true';
    }

    function hydrateBulkSelectionState(root) {
        getRowSelectionCheckboxes(root).forEach(hydrateCheckboxInitialState);
        const selectAllCheckbox = root.querySelector('[data-powercrud-select-all="true"]');
        if (
            selectAllCheckbox instanceof HTMLInputElement
            && selectAllCheckbox.dataset.powercrudSelectionHydrated !== 'true'
        ) {
            selectAllCheckbox.checked = selectAllCheckbox.dataset.powercrudInitialChecked === 'true';
            selectAllCheckbox.indeterminate = (
                selectAllCheckbox.dataset.powercrudInitialIndeterminate === 'true'
            );
            selectAllCheckbox.dataset.powercrudSelectionHydrated = 'true';
        }
    }

    function hydrateRenderedSelectionState(root) {
        hydrateBulkSelectionState(root);
    }

    function clearDocumentSelection() {
        const selection = global.getSelection ? global.getSelection() : null;
        if (selection && typeof selection.removeAllRanges === 'function') {
            selection.removeAllRanges();
        }
    }

    function nextSelectionRequestVersion(root) {
        // Each row-selection request carries a version so stale HTMX responses
        // cannot overwrite newer selection state.
        const state = ensureObjectListState(root);
        state.selectionRequestVersion += 1;
        return state.selectionRequestVersion;
    }

    function getSelectionRequestVersion(root) {
        return ensureObjectListState(root).selectionRequestVersion;
    }

    function clearRowSelectionRequestState(checkbox) {
        if (!(checkbox instanceof HTMLInputElement)) {
            return;
        }
        delete checkbox.dataset.powercrudSelectionRequestPending;
        delete checkbox.dataset.powercrudSelectionRequestVersion;
    }

    function abortPendingRowSelectionRequests(root) {
        const htmx = getHtmxInstance();
        if (!root || !htmx) {
            return;
        }
        getRowSelectionCheckboxes(root).forEach(checkbox => {
            if (checkbox.dataset.powercrudSelectionRequestPending !== 'true') {
                return;
            }
            htmx.trigger(checkbox, 'htmx:abort');
            clearRowSelectionRequestState(checkbox);
        });
    }

    function setRangeSelectionSuppressed(suppressed) {
        if (!(documentObject.body instanceof HTMLBodyElement)) {
            return;
        }
        documentObject.body.classList.toggle(RANGE_SELECT_SUPPRESS_CLASS, suppressed);
    }

    function hasShiftSelectionAnchor(root, checkbox) {
        if (!root || !(checkbox instanceof HTMLInputElement)) {
            return false;
        }
        const state = ensureObjectListState(root);
        const anchorId = state.lastRowSelectionAnchorId;
        if (!anchorId || checkbox.dataset.id === anchorId) {
            return false;
        }
        const anchor = getRowSelectionCheckboxes(root).find(cb => cb.dataset.id === anchorId);
        return (
            anchor instanceof HTMLInputElement
            && anchor !== checkbox
        );
    }

    function persistBulkSelectionBatch(root, objectIds, action) {
        if (!root || !objectIds.length) {
            return;
        }
        const htmx = getHtmxInstance();
        const listUrl = root.dataset.powercrudListUrl;
        if (!htmx || !listUrl) {
            return;
        }
        htmx.ajax('POST', `${listUrl}toggle-all-selection/`, {
            values: {
                object_ids_csv: objectIds.join(','),
                action,
            },
            target: '#bulk-actions-container',
            swap: 'outerHTML',
        });
    }

    function toggleAllSelection(selectAllCheckbox) {
        const root = getObjectListRoot(selectAllCheckbox);
        if (!root) {
            return;
        }
        setBulkRowsChecked(root, selectAllCheckbox.checked);
        syncBulkSelectionPresentation(root);
        if (selectAllCheckbox.checked) {
            showBulkActionsContainer(root);
        }

        const htmx = getHtmxInstance();
        const listUrl = root.dataset.powercrudListUrl;
        if (!htmx || !listUrl) {
            return;
        }

        const allIds = selectAllCheckbox.checked
            ? getSelectedBulkRowIds(root)
            : getRowSelectionCheckboxes(root).map(cb => cb.dataset.id);
        htmx.ajax('POST', `${listUrl}toggle-all-selection/`, {
            values: {
                object_ids_csv: allIds.join(','),
                action: selectAllCheckbox.checked ? 'add' : 'remove',
            },
            target: '#bulk-actions-container',
            swap: 'outerHTML',
        });
    }

    function handleRowSelectionChange(checkbox, event = null) {
        const root = getObjectListRoot(checkbox);
        if (!root) {
            return;
        }
        const state = ensureObjectListState(root);
        const anchor = getRowSelectionCheckboxes(root).find(
            cb => cb.dataset.id === state.lastRowSelectionAnchorId,
        );
        const hasValidAnchor = (
            anchor instanceof HTMLInputElement
            && anchor !== checkbox
        );
        const useShiftRange = (
            event?.shiftKey
            || checkbox.dataset.powercrudShiftRange === 'true'
        );
        if (checkbox.dataset.powercrudShiftRange === 'true') {
            delete checkbox.dataset.powercrudShiftRange;
        }
        if (useShiftRange && hasValidAnchor) {
            // Shift-range selection is persisted as one batch and suppresses
            // the individual checkbox request that the browser also emits.
            nextSelectionRequestVersion(root);
            abortPendingRowSelectionRequests(root);
            clearDocumentSelection();
            const checkboxes = getRowSelectionCheckboxes(root);
            const anchorIndex = checkboxes.indexOf(anchor);
            const targetIndex = checkboxes.indexOf(checkbox);
            if (anchorIndex !== -1 && targetIndex !== -1) {
                const startIndex = Math.min(anchorIndex, targetIndex);
                const endIndex = Math.max(anchorIndex, targetIndex);
                const range = checkboxes.slice(startIndex, endIndex + 1);
                range.forEach(cb => {
                    cb.checked = checkbox.checked;
                });
                syncBulkSelectionState(root);
                if (checkbox.checked) {
                    showBulkActionsContainer(root);
                }
                persistBulkSelectionBatch(
                    root,
                    range.map(cb => cb.dataset.id),
                    checkbox.checked ? 'add' : 'remove',
                );
                setRangeSelectionSuppressed(false);
                state.lastRowSelectionAnchorId = checkbox.dataset.id || null;
                return;
            }
        }
        setRangeSelectionSuppressed(false);
        syncBulkSelectionState(root);
        if (checkbox.checked) {
            showBulkActionsContainer(root);
        }
        state.lastRowSelectionAnchorId = checkbox.dataset.id || null;
    }

    function refreshTable(root, options = {}) {
        const htmx = getHtmxInstance();
        const listUrl = root?.dataset?.powercrudListUrl;
        const resultsTarget = root?.querySelector('#filtered_results');
        if (!htmx || !listUrl || !resultsTarget) {
            return;
        }
        htmx.ajax('GET', listUrl, {
            target: '#filtered_results',
            headers: {
                'X-Filter-Sort-Request': 'true',
            },
            swap: 'innerHTML',
            pushURL: true,
            values: getCurrentFilters({ preservePage: options.resetPage !== true }),
        });
    }

    function handleSelectionExtraButtonAfterRequest(event, target) {
        if (
            event.detail?.successful !== true
            || !(target instanceof Element)
            || !target.matches('[data-powercrud-clear-selection-on-success="true"]')
        ) {
            return false;
        }

        const htmx = getHtmxInstance();
        const root = getObjectListRoot(target);
        const listUrl = root?.dataset?.powercrudListUrl;
        const actionsContainer = root?.querySelector('#bulk-actions-container');
        if (!htmx || !root || !listUrl || !actionsContainer) {
            return false;
        }

        clearSelectionOptimistic(root);
        htmx.ajax('POST', `${listUrl}clear-selection/`, {
            source: actionsContainer,
            target: '#bulk-actions-container',
            swap: 'outerHTML',
        });
        return true;
    }

    function setBulkActionButtonsDisabled(source, disabled) {
        const root = source?.closest ? source.closest('#bulk-edit-form') : null;
        if (!root) {
            return;
        }
        root.querySelectorAll('[data-form-save], [data-powercrud-bulk-delete-submit]').forEach(button => {
            if (!(button instanceof HTMLButtonElement)) {
                return;
            }
            if (button.hasAttribute('data-powercrud-bulk-delete-submit') && button.id === 'confirm-delete-button') {
                const checkbox = root.querySelector('#confirm-delete-checkbox');
                if (!disabled && checkbox instanceof HTMLInputElement && !checkbox.checked) {
                    button.disabled = true;
                    return;
                }
            }
            if (!button.hasAttribute('data-powercrud-bulk-delete-submit') || disabled || button.id !== 'confirm-delete-button') {
                button.disabled = disabled;
            }
        });
    }

    function handleClearSelectionClick(trigger) {
        const clearSelectionTrigger = trigger?.closest('[data-powercrud-clear-selection]');
        if (!clearSelectionTrigger) {
            return false;
        }
        const root = getObjectListRoot(clearSelectionTrigger);
        if (root) {
            clearBulkSelection(root);
        }
        return true;
    }

    function handleRowSelectionClickCapture(event, target) {
        if (!target || !target.matches('[data-powercrud-row-select="true"]')) {
            return false;
        }
        const root = getObjectListRoot(target);
        if (event.shiftKey && hasShiftSelectionAnchor(root, target)) {
            clearDocumentSelection();
            target.dataset.powercrudShiftRange = 'true';
            target.dataset.powercrudSkipSelectionRequest = 'true';
        }
        return true;
    }

    function handleRowSelectionMouseDownCapture(event, target) {
        if (!target || !target.matches('[data-powercrud-row-select="true"]')) {
            return false;
        }
        const root = getObjectListRoot(target);
        if (event.shiftKey && hasShiftSelectionAnchor(root, target)) {
            setRangeSelectionSuppressed(true);
            clearDocumentSelection();
        }
        return true;
    }

    function handleBulkHtmxBeforeRequest(event, target) {
        if (target && target.matches && target.matches('[data-powercrud-row-select="true"]')) {
            if (target.dataset.powercrudSkipSelectionRequest === 'true') {
                delete target.dataset.powercrudSkipSelectionRequest;
                event.preventDefault();
                return true;
            }
            const root = getObjectListRoot(target);
            if (root) {
                target.dataset.powercrudSelectionRequestPending = 'true';
                target.dataset.powercrudSelectionRequestVersion = String(
                    nextSelectionRequestVersion(root),
                );
            }
            return true;
        }
        if (target && target.matches && target.matches('[data-powercrud-bulk-delete-submit]')) {
            setBulkActionButtonsDisabled(target, true);
            return true;
        }
        return false;
    }

    function handleBulkHtmxBeforeSwap(event) {
        const requestTarget = event.detail?.requestConfig?.elt || event.detail?.elt || null;
        if (
            requestTarget instanceof HTMLInputElement
            && requestTarget.matches('[data-powercrud-row-select="true"]')
        ) {
            const root = getObjectListRoot(requestTarget);
            const requestVersion = Number.parseInt(
                requestTarget.dataset.powercrudSelectionRequestVersion || '0',
                10,
            );
            if (
                root
                && Number.isFinite(requestVersion)
                && requestVersion < getSelectionRequestVersion(root)
            ) {
                // A newer batch/checkbox request already owns the current
                // state; cancel this older swap instead of reverting the UI.
                clearRowSelectionRequestState(requestTarget);
                event.preventDefault();
                return true;
            }
        }
        return false;
    }

    function handleBulkHtmxAfterRequest(target) {
        if (
            target instanceof HTMLInputElement
            && target.matches('[data-powercrud-row-select="true"]')
        ) {
            clearRowSelectionRequestState(target);
            return true;
        }
        if (target && target.matches && target.matches('[data-powercrud-form="bulk"]')) {
            setBulkActionButtonsDisabled(target, false);
            return true;
        }
        if (target && target.matches && target.matches('[data-powercrud-bulk-delete-submit]')) {
            setBulkActionButtonsDisabled(target, false);
            return true;
        }
        return false;
    }

    function handleBulkHtmxResponseError(target) {
        if (
            target instanceof HTMLInputElement
            && target.matches('[data-powercrud-row-select="true"]')
        ) {
            clearRowSelectionRequestState(target);
            return true;
        }
        if (target && target.matches && target.matches('[data-powercrud-form="bulk"]')) {
            setBulkActionButtonsDisabled(target, false);
            return true;
        }
        if (target && target.matches && target.matches('[data-powercrud-bulk-delete-submit]')) {
            setBulkActionButtonsDisabled(target, false);
            return true;
        }
        return false;
    }

    function handleBulkEditSuccess() {
        // The event is semantic, but closing the DaisyUI dialog is still a
        // current-template callback until modal behaviour moves to an adapter.
        closePowercrudModals?.();
        getAffectedObjectListRoots(documentObject).forEach(clearBulkSelection);
    }

    function handleBulkEditQueued() {
        getAffectedObjectListRoots(documentObject).forEach(clearBulkSelection);
    }

    return {
        clearBulkSelection,
        clearSelectionOptimistic,
        clearRowSelectionRequestState,
        getRowSelectionCheckboxes,
        getSelectionRequestVersion,
        handleBulkEditQueued,
        handleBulkEditSuccess,
        handleBulkHtmxAfterRequest,
        handleBulkHtmxBeforeRequest,
        handleBulkHtmxBeforeSwap,
        handleBulkHtmxResponseError,
        handleClearSelectionClick,
        handleSelectionExtraButtonAfterRequest,
        handleRowSelectionChange,
        handleRowSelectionClickCapture,
        handleRowSelectionMouseDownCapture,
        hydrateBulkSelectionState,
        hydrateRenderedSelectionState,
        refreshTable,
        setBulkActionButtonsDisabled,
        syncBulkSelectionPresentation,
        syncBulkSelectionState,
        syncSelectionAwareExtraButtons,
        toggleAllSelection,
    };
}
