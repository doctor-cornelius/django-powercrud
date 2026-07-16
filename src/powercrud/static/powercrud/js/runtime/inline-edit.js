import {
    INLINE_ROW_SELECTOR,
    INLINE_TABLE_SELECTOR,
} from './selectors.js';

export function createInlineEditRuntime(context) {
    const {
        global,
        documentObject,
        getHtmxInstance,
        initPowercrudSearchableSelects,
        syncTomSelectValues,
        toggleInlineSaveSpinner,
        resolveInlineFocusTarget,
        presentInlineFocus,
        showInlineFieldErrorPopovers,
        destroyInlineFieldErrorPopovers,
        removeOrphanedInlineFieldErrorPopovers,
        repositionInlineFieldErrorPopovers,
    } = context;

    let activeRowId = null;
    let pendingColumnWidths = null;
    let activeColumnWidths = null;
    let lockedTableRef = null;
    let pendingInlineFocusField = null;
    let pendingInlineSelectHighlight = false;

    function isInlineEditRequest(target) {
        return (
            target instanceof Element
            && (
                target.matches('[data-inline-save], [data-inline-cancel], .inline-edit-trigger')
                || Boolean(target.closest('[data-inline-row="true"]'))
                || Boolean(target.closest('.inline-field-widget'))
            )
        );
    }

    function targetTouchesInlineRows(target) {
        if (!(target instanceof HTMLElement)) {
            return false;
        }
        if (target.matches(INLINE_ROW_SELECTOR)) {
            return true;
        }
        if (typeof target.querySelector === 'function') {
            return Boolean(target.querySelector(INLINE_ROW_SELECTOR));
        }
        return false;
    }

    function isTableCell(el) {
        return el && (el.tagName === 'TD' || el.tagName === 'TH');
    }

    function snapshotRowWidths(row) {
        if (!row) {
            return null;
        }
        const cells = Array.from(row.children).filter(isTableCell);
        if (!cells.length) {
            return null;
        }
        return cells.map(cell => cell.getBoundingClientRect().width || 0);
    }

    function applyRowWidths(row, widths) {
        if (!row || !Array.isArray(widths) || !widths.length) {
            return;
        }
        const cells = Array.from(row.children).filter(isTableCell);
        if (cells.length !== widths.length) {
            return;
        }
        cells.forEach((cell, idx) => {
            const width = Math.max(0, Math.round(widths[idx]));
            cell.style.width = `${width}px`;
            cell.style.minWidth = `${width}px`;
            cell.style.maxWidth = `${width}px`;
            cell.dataset.inlineWidthLocked = 'true';
        });
        row.dataset.inlineWidthLocked = 'true';
    }

    function clearRowWidths(row) {
        if (!row) {
            return;
        }
        const cells = Array.from(row.children).filter(isTableCell);
        cells.forEach(cell => {
            if (cell.dataset.inlineWidthLocked === 'true') {
                delete cell.dataset.inlineWidthLocked;
            }
            cell.style.width = '';
            cell.style.minWidth = '';
            cell.style.maxWidth = '';
        });
        delete row.dataset.inlineWidthLocked;
    }

    function lockTableWidth(table) {
        if (!table || table.dataset.inlineTableLocked === 'true') {
            return;
        }
        table.dataset.inlineTableLocked = 'true';
        table.style.width = `${table.offsetWidth}px`;
        lockedTableRef = table;
    }

    function unlockTableWidth(table) {
        const target = table || lockedTableRef;
        if (!target || target.dataset.inlineTableLocked !== 'true') {
            return;
        }
        target.style.width = '';
        delete target.dataset.inlineTableLocked;
        if (lockedTableRef === target) {
            lockedTableRef = null;
        }
    }

    function getActiveRow() {
        return activeRowId ? documentObject.getElementById(activeRowId) : null;
    }

    function setActiveRow(row) {
        documentObject
            .querySelectorAll(`${INLINE_ROW_SELECTOR}[data-inline-active="true"]`)
            .forEach(el => el.removeAttribute('data-inline-active'));

        if (row && row.id) {
            activeRowId = row.id;
            row.setAttribute('data-inline-active', 'true');
        } else {
            activeRowId = null;
        }
    }

    function clearActiveRow() {
        activeRowId = null;
        destroyInlineFieldErrorPopovers(documentObject);
        documentObject
            .querySelectorAll(`${INLINE_ROW_SELECTOR}[data-inline-active="true"]`)
            .forEach(el => {
                el.removeAttribute('data-inline-active');
                clearRowWidths(el);
            });
    }

    function clearInlineLayoutState(table = null) {
        pendingColumnWidths = null;
        activeColumnWidths = null;
        unlockTableWidth(table);
    }

    function capturePendingInlineRowState(trigger, row, options = {}) {
        const { captureFocus = true } = options;
        if (captureFocus) {
            pendingInlineFocusField = trigger?.dataset?.inlineField || null;
            pendingInlineSelectHighlight = true;
        }
        if (!row) {
            return;
        }
        // Lock widths before the display row is replaced by a form row so the
        // table does not reflow during the inline edit swap.
        const table = row.closest(INLINE_TABLE_SELECTOR);
        if (table) {
            lockTableWidth(table);
        }
        pendingColumnWidths = snapshotRowWidths(row);
    }

    function applyPendingInlineRowWidths(row) {
        const widthsToApply = pendingColumnWidths || activeColumnWidths;
        if (!widthsToApply || !widthsToApply.length) {
            return;
        }
        applyRowWidths(row, widthsToApply);
        activeColumnWidths = widthsToApply.slice();
        pendingColumnWidths = null;
    }

    function focusRow(row, preferredField) {
        if (!row) {
            return;
        }
        row.classList.add('inline-row-attention');
        const triggerField = preferredField || pendingInlineFocusField;
        const focusTarget = resolveInlineFocusTarget(row, triggerField);
        pendingInlineFocusField = null;
        if (focusTarget) {
            presentInlineFocus(focusTarget, triggerField, pendingInlineSelectHighlight);
            pendingInlineSelectHighlight = false;
        }
        row.scrollIntoView({ behavior: 'smooth', block: 'center' });
        global.setTimeout(() => row.classList.remove('inline-row-attention'), 600);
    }

    function initInlineSearchableSelects(container) {
        if (container) {
            initPowercrudSearchableSelects(container);
        }
    }

    function bindInlineRowHotkeys(row) {
        if (!row || row.dataset.inlineHotkeysBound === 'true') {
            return;
        }
        row.dataset.inlineHotkeysBound = 'true';
        row.addEventListener('keydown', event => {
            if (event.defaultPrevented || event.key !== 'Enter') {
                return;
            }
            if (event.metaKey || event.ctrlKey || event.altKey || event.shiftKey) {
                return;
            }
            const target = event.target;
            if (!target || !(target instanceof HTMLElement)) {
                return;
            }
            if (target.tagName === 'TEXTAREA' || target.isContentEditable) {
                return;
            }
            if (target.matches('button, [role="button"], [data-inline-save], [data-inline-cancel]')) {
                return;
            }
            if (target.closest('[data-inline-actions="true"]')) {
                return;
            }
            const saveBtn = row.querySelector('[data-inline-save]');
            if (!saveBtn || saveBtn.disabled) {
                return;
            }
            event.preventDefault();
            saveBtn.click();
        });
    }

    function buildDependencyMap(container) {
        const map = {};
        container.querySelectorAll('.inline-field-widget[data-inline-dependent="true"]').forEach(widget => {
            const fieldName = widget.dataset.inlineField;
            const dependsOnRaw = widget.dataset.inlineDependsOn || '';
            const endpoint = widget.dataset.inlineEndpoint;
            if (!fieldName || !endpoint || !dependsOnRaw) {
                return;
            }
            dependsOnRaw
                .split(',')
                .map(name => name.trim())
                .filter(Boolean)
                .forEach(parent => {
                    if (!map[parent]) {
                        map[parent] = [];
                    }
                    map[parent].push({ fieldName, endpoint });
                });
        });
        return map;
    }

    function getWidgetControl(widget) {
        if (!widget) {
            return null;
        }
        return widget.querySelector('select, textarea, input:not([type="hidden"])');
    }

    function clearWidgetControlValue(control) {
        if (!control || control.disabled) {
            return;
        }
        if (control.tagName === 'SELECT') {
            if (control.multiple) {
                Array.from(control.options).forEach(option => {
                    option.selected = false;
                });
                return;
            }
            control.selectedIndex = -1;
            return;
        }
        if (control.type === 'checkbox' || control.type === 'radio') {
            control.checked = false;
            return;
        }
        control.value = '';
    }

    function setWidgetRefreshing(widget, isRefreshing) {
        if (!widget) {
            return;
        }
        const control = getWidgetControl(widget);
        if (isRefreshing) {
            widget.dataset.inlineRefreshing = 'true';
            widget.setAttribute('aria-busy', 'true');
            clearWidgetControlValue(control);
            if (control) {
                control.disabled = true;
            }
            return;
        }
        delete widget.dataset.inlineRefreshing;
        widget.removeAttribute('aria-busy');
        if (control) {
            control.disabled = false;
        }
    }

    function refreshDependentField(container, dep) {
        const widget = container.querySelector(
            `.inline-field-widget[data-inline-field="${dep.fieldName}"]`
        );
        if (!widget || !dep.endpoint) {
            return;
        }

        // Sync enhanced controls back to native fields before serialising the
        // parent values used to refresh the dependent widget.
        syncTomSelectValues(container);
        setWidgetRefreshing(widget, true);

        const values = {};
        container.querySelectorAll('[name]').forEach(input => {
            const name = input.getAttribute('name');
            if (!name || input.disabled) {
                return;
            }
            if ((input.type === 'checkbox' || input.type === 'radio') && !input.checked) {
                return;
            }
            if (input.tagName === 'SELECT' && input.multiple) {
                values[name] = Array.from(input.selectedOptions).map(option => option.value);
                return;
            }
            values[name] = input.value;
        });
        values.field = dep.fieldName;

        const htmx = getHtmxInstance();
        if (!htmx) {
            return;
        }
        htmx.ajax('POST', dep.endpoint, {
            source: widget,
            target: widget,
            swap: 'outerHTML',
            values,
        });
    }

    function wireInlineDependencies(container) {
        const dependencyMap = buildDependencyMap(container);
        Object.entries(dependencyMap).forEach(([parentField, dependents]) => {
            const control = container.querySelector(`[name="${parentField}"]`);
            if (!control) {
                return;
            }
            if (control.dataset.inlineDependencyBound === 'true') {
                return;
            }
            control.dataset.inlineDependencyBound = 'true';
            control.addEventListener('change', () => {
                dependents.forEach(dep => refreshDependentField(container, dep));
            });
        });
    }

    function wireInlineRow(row) {
        if (!row) {
            return;
        }
        initInlineSearchableSelects(row);
        wireInlineDependencies(row);
        bindInlineRowHotkeys(row);
    }

    function activateInlineFormRow(row) {
        setActiveRow(row);
        wireInlineRow(row);
        focusRow(row);
        showInlineFieldErrorPopovers(row);
        applyPendingInlineRowWidths(row);
        removeOrphanedInlineFieldErrorPopovers();
    }

    function findInlineFormRow(root) {
        if (!(root instanceof HTMLElement)) {
            return null;
        }
        const rows = Array.from(root.querySelectorAll(INLINE_ROW_SELECTOR));
        return rows.find(row => row.querySelector('[data-inline-save]')) || null;
    }

    function bootstrapInlineRow() {
        const row = documentObject.querySelector(`${INLINE_ROW_SELECTOR}[data-inline-active="true"]`);
        if (row) {
            setActiveRow(row);
            wireInlineRow(row);
        }
    }

    function refreshInlineRow(refresh) {
        if (!refresh || !refresh.url) {
            return;
        }
        const htmx = getHtmxInstance();
        if (!htmx) {
            return;
        }
        const targetId = refresh.row_id;
        htmx.ajax('GET', refresh.url, {
            target: targetId ? `#${targetId}` : '#filtered_results',
            swap: targetId ? 'outerHTML' : 'innerHTML',
        });
    }

    function handleInlineGuardEvent(event) {
        const payload = event.detail && event.detail.value ? event.detail.value : (event.detail || {});
        const refreshPayload = payload.refresh;
        clearActiveRow();
        clearInlineLayoutState();
        refreshInlineRow(refreshPayload);
    }

    function handleDocumentClickCapture(_event, trigger) {
        if (trigger?.closest('[data-inline-cancel]')) {
            destroyInlineFieldErrorPopovers(documentObject);
            return true;
        }
        return false;
    }

    function handleKeydown(event, target) {
        if (event.key === 'Escape' && target?.closest(INLINE_ROW_SELECTOR)) {
            destroyInlineFieldErrorPopovers(documentObject);
            return true;
        }
        return false;
    }

    function handleHtmxBeforeSwap(event) {
        if (!activeRowId) {
            return false;
        }
        const target = event.target instanceof Element ? event.target : null;
        if (targetTouchesInlineRows(target)) {
            clearActiveRow();
        }
        return false;
    }

    function handleHtmxAfterSwapTarget(target) {
        if (!(target instanceof HTMLElement)) {
            return false;
        }

        if (targetTouchesInlineRows(target) && !target.matches(INLINE_ROW_SELECTOR)) {
            const targetHasActiveInlineRow = Boolean(
                target.querySelector(`${INLINE_ROW_SELECTOR}[data-inline-active="true"]`)
            );
            const inlineFormRow = findInlineFormRow(target);
            if (!targetHasActiveInlineRow && inlineFormRow) {
                activateInlineFormRow(inlineFormRow);
                return true;
            }
            if (!targetHasActiveInlineRow) {
                clearActiveRow();
            }
        }

        if (target.matches(INLINE_ROW_SELECTOR)) {
            if (target.dataset.inlineActive === 'true') {
                activateInlineFormRow(target);
            } else if (activeRowId && target.id === activeRowId) {
                setActiveRow(null);
                destroyInlineFieldErrorPopovers(documentObject);
                clearRowWidths(target);
                clearInlineLayoutState(target.closest(INLINE_TABLE_SELECTOR));
            } else {
                clearRowWidths(target);
                if (!documentObject.querySelector(`${INLINE_ROW_SELECTOR}[data-inline-active="true"]`)) {
                    clearInlineLayoutState(target.closest(INLINE_TABLE_SELECTOR));
                }
            }
            removeOrphanedInlineFieldErrorPopovers();
            return true;
        }

        if (target.matches('.inline-field-widget[data-inline-field]')) {
            setWidgetRefreshing(target, false);
            initInlineSearchableSelects(target);
            showInlineFieldErrorPopovers(target);
        }

        if (activeRowId) {
            const row = target.closest(INLINE_ROW_SELECTOR);
            if (row && row.id === activeRowId && row.dataset.inlineActive === 'true') {
                wireInlineRow(row);
                showInlineFieldErrorPopovers(row);
            }
        }
        removeOrphanedInlineFieldErrorPopovers();
        return false;
    }

    function handleHtmxBeforeRequest(event) {
        const target = event.detail && event.detail.elt;
        if (target && target.matches && target.matches('[data-inline-cancel]')) {
            destroyInlineFieldErrorPopovers(documentObject);
        }
        if (target && target.matches && target.matches('[data-inline-save]')) {
            const row = target.closest(INLINE_ROW_SELECTOR);
            syncTomSelectValues(row);
            toggleInlineSaveSpinner?.(row, true);
        }

        const trigger = event.detail && event.detail.elt instanceof Element
            ? event.detail.elt
            : null;
        if (!trigger || !trigger.classList.contains('inline-edit-trigger')) {
            return false;
        }
        capturePendingInlineRowState(trigger, null);
        const row = trigger.closest(INLINE_ROW_SELECTOR);
        const activeRow = getActiveRow();
        if (activeRow && row && activeRow !== row) {
            // Keep a single active inline row. A second edit request would
            // otherwise replace DOM while the first row still owns state.
            event.preventDefault();
            console.debug('[powercrud] Inline guard prevented second row edit', {
                activeRowId,
                blockedRowId: row.id,
            });
            focusRow(activeRow);
            return true;
        }
        capturePendingInlineRowState(trigger, row, { captureFocus: false });
        return false;
    }

    function handleHtmxAfterRequest(target) {
        if (target && target.matches && target.matches('[data-inline-save]')) {
            const row = target.closest(INLINE_ROW_SELECTOR);
            toggleInlineSaveSpinner?.(row, false);
            return true;
        }
        return false;
    }

    function handleHtmxResponseError(target) {
        if (target instanceof HTMLElement && target.matches('.inline-field-widget[data-inline-refreshing="true"]')) {
            setWidgetRefreshing(target, false);
            return true;
        }
        return false;
    }

    function handleInlineSaved() {
        destroyInlineFieldErrorPopovers(documentObject);
    }

    function handleInlineError(event) {
        const payload = event.detail && event.detail.value ? event.detail.value : (event.detail || {});
        if (payload.row_id) {
            const errorRow = documentObject.getElementById(payload.row_id);
            if (errorRow) {
                focusRow(errorRow);
                showInlineFieldErrorPopovers(errorRow);
            }
        }
    }

    return {
        bootstrapInlineRow,
        destroyInlineFieldErrorPopovers,
        handleDocumentClickCapture,
        handleKeydown,
        handleHtmxBeforeSwap,
        handleHtmxAfterSwapTarget,
        handleHtmxBeforeRequest,
        handleHtmxAfterRequest,
        handleHtmxResponseError,
        handleInlineGuardEvent,
        handleInlineSaved,
        handleInlineError,
        isInlineEditRequest,
        removeOrphanedInlineFieldErrorPopovers,
        repositionInlineFieldErrorPopovers,
        showInlineFieldErrorPopovers,
    };
}
