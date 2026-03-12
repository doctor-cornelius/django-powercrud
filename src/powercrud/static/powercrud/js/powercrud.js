(function powercrudRuntime(global) {
    'use strict';

    if (global.__powercrudRuntimeLoaded) {
        return;
    }
    global.__powercrudRuntimeLoaded = true;

    const SEARCHABLE_SELECT_ATTR = 'data-powercrud-searchable-select';
    const SEARCHABLE_MULTISELECT_ATTR = 'data-powercrud-searchable-multiselect';
    const NATIVE_TABINDEX_ATTR = 'data-powercrud-native-tabindex';
    const NATIVE_STYLE_ATTR = 'data-powercrud-native-style';
    const OBJECT_LIST_ROOT_SELECTOR = '[data-powercrud-object-list="true"]';
    const TOOLTIP_TRIGGER_SELECTOR = '[data-powercrud-tooltip][data-tippy-content]';
    const INLINE_ROW_SELECTOR = 'tr[data-inline-row="true"]';
    const INLINE_TABLE_SELECTOR = 'table[data-inline-enabled="true"]';
    const INLINE_NOTICE_SELECTOR = '[data-powercrud-inline-alert]';

    const warnedDeps = {
        htmx: false,
        tippy: false,
        tomSelect: false,
    };

    const objectListState = new WeakMap();
    const FORM_SPINNER_STATE = new WeakMap();
    let tooltipResizeTimer = null;

    function warnMissingDependency(name, detail) {
        if (warnedDeps[name]) {
            return;
        }
        warnedDeps[name] = true;
        console.warn(`PowerCRUD frontend: missing ${detail}.`);
    }

    function asElement(value) {
        return value instanceof Element ? value : null;
    }

    function queryAllWithSelf(root, selector) {
        if (root === document) {
            return Array.from(document.querySelectorAll(selector));
        }
        if (!(root instanceof Element)) {
            return [];
        }
        const matches = [];
        if (root.matches(selector)) {
            matches.push(root);
        }
        matches.push(...root.querySelectorAll(selector));
        return matches;
    }

    function getAffectedObjectListRoots(scope = document) {
        if (scope === document) {
            return queryAllWithSelf(document, OBJECT_LIST_ROOT_SELECTOR);
        }
        if (!(scope instanceof Element)) {
            return [];
        }

        const roots = queryAllWithSelf(scope, OBJECT_LIST_ROOT_SELECTOR);
        if (roots.length) {
            return roots;
        }

        const closestRoot = scope.closest(OBJECT_LIST_ROOT_SELECTOR);
        return closestRoot ? [closestRoot] : [];
    }

    function getObjectListRoot(node) {
        if (!(node instanceof Element)) {
            return null;
        }
        return node.closest(OBJECT_LIST_ROOT_SELECTOR);
    }

    function ensureObjectListState(root) {
        if (!objectListState.has(root)) {
            objectListState.set(root, {
                filterExpansionRestored: false,
            });
        }
        return objectListState.get(root);
    }

    function getTomSelectCtor() {
        const ctor = global.TomSelect;
        if (!ctor) {
            warnMissingDependency('tomSelect', "window.TomSelect. Load Tom Select before powercrud/js/powercrud.js");
            return null;
        }
        return ctor;
    }

    function getTippyCtor() {
        const ctor = global.tippy;
        if (typeof ctor !== 'function') {
            warnMissingDependency('tippy', 'window.tippy. Load Tippy.js before powercrud/js/powercrud.js');
            return null;
        }
        return ctor;
    }

    function getHtmxInstance() {
        const htmx = global.htmx;
        if (!htmx?.ajax) {
            warnMissingDependency('htmx', 'window.htmx. Load HTMX before powercrud/js/powercrud.js');
            return null;
        }
        return htmx;
    }

    function isSearchableSelectCandidate(element) {
        return (
            element instanceof HTMLSelectElement
            && element.getAttribute(SEARCHABLE_SELECT_ATTR) === 'true'
            && !element.multiple
        );
    }

    function isSearchableMultiselectCandidate(element) {
        return (
            element instanceof HTMLSelectElement
            && element.getAttribute(SEARCHABLE_MULTISELECT_ATTR) === 'true'
            && element.multiple
        );
    }

    function isElementVisible(element) {
        if (!(element instanceof Element)) {
            return false;
        }
        return element.getClientRects().length > 0;
    }

    function syncTomSelectDisabledState(selectElement) {
        if (!selectElement?.tomselect) {
            return;
        }
        if (selectElement.disabled) {
            selectElement.tomselect.disable();
            return;
        }
        selectElement.tomselect.enable();
    }

    function hideNativeSelect(selectElement) {
        if (!(selectElement instanceof HTMLSelectElement)) {
            return;
        }
        if (!selectElement.hasAttribute(NATIVE_STYLE_ATTR)) {
            selectElement.setAttribute(NATIVE_STYLE_ATTR, selectElement.getAttribute('style') || '');
        }
        if (!selectElement.hasAttribute(NATIVE_TABINDEX_ATTR)) {
            const current = selectElement.getAttribute('tabindex');
            selectElement.setAttribute(NATIVE_TABINDEX_ATTR, current === null ? '' : current);
        }
        selectElement.style.setProperty('display', 'none', 'important');
        selectElement.style.setProperty('visibility', 'hidden', 'important');
        selectElement.style.setProperty('position', 'absolute', 'important');
        selectElement.style.setProperty('width', '1px', 'important');
        selectElement.style.setProperty('height', '1px', 'important');
        selectElement.style.setProperty('pointer-events', 'none', 'important');
        selectElement.classList.add('ts-hidden-accessible');
        selectElement.hidden = true;
        selectElement.setAttribute('tabindex', '-1');
        selectElement.setAttribute('aria-hidden', 'true');
    }

    function restoreNativeSelect(selectElement) {
        if (!(selectElement instanceof HTMLSelectElement)) {
            return;
        }
        if (selectElement.hasAttribute(NATIVE_STYLE_ATTR)) {
            const originalStyle = selectElement.getAttribute(NATIVE_STYLE_ATTR) || '';
            if (originalStyle) {
                selectElement.setAttribute('style', originalStyle);
            } else {
                selectElement.removeAttribute('style');
            }
            selectElement.removeAttribute(NATIVE_STYLE_ATTR);
        }
        selectElement.classList.remove('ts-hidden-accessible');
        selectElement.hidden = false;
        if (selectElement.hasAttribute(NATIVE_TABINDEX_ATTR)) {
            const original = selectElement.getAttribute(NATIVE_TABINDEX_ATTR);
            if (original) {
                selectElement.setAttribute('tabindex', original);
            } else {
                selectElement.removeAttribute('tabindex');
            }
            selectElement.removeAttribute(NATIVE_TABINDEX_ATTR);
        }
        selectElement.removeAttribute('aria-hidden');
    }

    function createTomSelectInstance(selectElement, settings) {
        const TomSelectCtor = getTomSelectCtor();
        if (!TomSelectCtor) {
            return null;
        }

        try {
            return new TomSelectCtor(selectElement, settings);
        } catch (error) {
            if (!settings.plugins || settings.plugins.length === 0) {
                throw error;
            }

            const fallbackSettings = { ...settings };
            delete fallbackSettings.plugins;
            return new TomSelectCtor(selectElement, fallbackSettings);
        }
    }

    function normaliseTomSelectControl(instance) {
        instance.wrapper.classList.remove('select', 'select-bordered', 'select-sm', 'select-md', 'select-lg');
        instance.control.classList.remove('select', 'select-bordered', 'select-sm', 'select-md', 'select-lg');
        instance.wrapper.classList.add('w-full');
        instance.control.classList.add('w-full');
    }

    function enhanceSearchableSelect(selectElement) {
        if (!isSearchableSelectCandidate(selectElement)) {
            return;
        }
        if (selectElement.tomselect) {
            syncTomSelectDisabledState(selectElement);
            hideNativeSelect(selectElement);
            return;
        }
        if (!isElementVisible(selectElement)) {
            return;
        }

        const placeholder = selectElement.getAttribute('data-powercrud-searchable-placeholder') || '';
        const dialogElement = selectElement.closest('dialog');
        const isInlineSelect = Boolean(selectElement.closest(INLINE_ROW_SELECTOR));
        const settings = {
            create: false,
            maxItems: 1,
            maxOptions: null,
            closeAfterSelect: true,
            allowEmptyOption: true,
            placeholder,
            openOnFocus: true,
            onType(query) {
                if (this.items.length === 0) {
                    return;
                }
                this.clear(true);
                this.setTextboxValue(query);
                this.refreshOptions(true);
            },
        };
        if (!dialogElement) {
            settings.dropdownParent = 'body';
        }

        const instance = createTomSelectInstance(selectElement, settings);
        if (!instance) {
            return;
        }

        normaliseTomSelectControl(instance);

        if (isInlineSelect) {
            instance.dropdown.classList.add('powercrud-inline-single-dropdown');
            instance.on('dropdown_open', function () {
                const controlWidth = Math.ceil(instance.control.getBoundingClientRect().width);
                const viewportMax = Math.max(240, window.innerWidth - 32);
                const desiredWidth = Math.min(Math.max(controlWidth, 320), viewportMax);
                instance.dropdown.style.setProperty('min-width', `${desiredWidth}px`, 'important');
            });
        }

        if (!isInlineSelect) {
            instance.wrapper.classList.add('powercrud-clearable-single');
        }

        if (!isInlineSelect && !instance.control.querySelector('.clear-button')) {
            const clearButton = document.createElement('button');
            clearButton.type = 'button';
            clearButton.className = 'clear-button';
            clearButton.title = 'Clear';
            clearButton.setAttribute('aria-label', 'Clear selection');
            clearButton.innerHTML = '&times;';
            clearButton.addEventListener('click', event => {
                if (instance.isLocked) {
                    return;
                }
                instance.clear(true);
                instance.setTextboxValue('');
                instance.refreshOptions(false);
                selectElement.dispatchEvent(new Event('change', { bubbles: true }));
                event.preventDefault();
                event.stopPropagation();
                instance.focus();
            });
            if (instance.control_input && instance.control_input.parentElement === instance.control) {
                instance.control.insertBefore(clearButton, instance.control_input);
            } else {
                instance.control.appendChild(clearButton);
            }
        }

        syncTomSelectDisabledState(selectElement);
        hideNativeSelect(selectElement);
    }

    function enhanceSearchableMultiselect(selectElement) {
        if (!isSearchableMultiselectCandidate(selectElement)) {
            return;
        }
        if (selectElement.tomselect) {
            syncTomSelectDisabledState(selectElement);
            hideNativeSelect(selectElement);
            return;
        }
        if (!isElementVisible(selectElement)) {
            return;
        }

        const placeholder = selectElement.getAttribute('data-powercrud-searchable-placeholder') || '';
        const dialogElement = selectElement.closest('dialog');
        const settings = {
            create: false,
            maxItems: null,
            maxOptions: null,
            closeAfterSelect: false,
            allowEmptyOption: true,
            hideSelected: false,
            placeholder,
            openOnFocus: true,
            plugins: ['remove_button'],
            onItemAdd() {
                this.setTextboxValue('');
                this.refreshOptions(true);
            },
        };
        if (!dialogElement) {
            settings.dropdownParent = 'body';
        }

        const instance = createTomSelectInstance(selectElement, settings);
        if (!instance) {
            return;
        }

        normaliseTomSelectControl(instance);
        syncTomSelectDisabledState(selectElement);
        hideNativeSelect(selectElement);
    }

    function initPowercrudSearchableSelects(root = document) {
        if (!(root instanceof Element) && root !== document) {
            return;
        }

        const TomSelectCtor = getTomSelectCtor();
        if (!TomSelectCtor) {
            return;
        }

        const scope = root === document ? document : root;
        scope.querySelectorAll(`select[${SEARCHABLE_SELECT_ATTR}="true"]`).forEach(enhanceSearchableSelect);
        scope.querySelectorAll(`select[${SEARCHABLE_MULTISELECT_ATTR}="true"]`).forEach(enhanceSearchableMultiselect);

        if (root instanceof HTMLSelectElement) {
            enhanceSearchableSelect(root);
            enhanceSearchableMultiselect(root);
        }
    }

    function destroyPowercrudSearchableSelects(root = document) {
        if (!(root instanceof Element) && root !== document) {
            return;
        }
        const scope = root === document ? document : root;
        scope
            .querySelectorAll(`select[${SEARCHABLE_SELECT_ATTR}="true"], select[${SEARCHABLE_MULTISELECT_ATTR}="true"]`)
            .forEach(selectElement => {
                if (selectElement.tomselect) {
                    selectElement.tomselect.destroy();
                }
                restoreNativeSelect(selectElement);
            });

        if (root instanceof HTMLSelectElement) {
            if (root.tomselect) {
                root.tomselect.destroy();
            }
            restoreNativeSelect(root);
        }
    }

    function isTooltipOverflowTarget(trigger) {
        return trigger?.dataset?.powercrudTooltip === 'overflow';
    }

    function isTooltipSemanticTarget(trigger) {
        return trigger?.dataset?.powercrudTooltip === 'semantic';
    }

    function isTruncated(trigger) {
        if (!(trigger instanceof HTMLElement) || !isElementVisible(trigger)) {
            return false;
        }
        return (
            (trigger.scrollWidth - trigger.clientWidth) > 1
            || (trigger.scrollHeight - trigger.clientHeight) > 1
        );
    }

    function destroyPowercrudTooltips(root = document) {
        queryAllWithSelf(root, TOOLTIP_TRIGGER_SELECTOR).forEach(trigger => {
            if (trigger._tippy) {
                trigger._tippy.destroy();
            }
        });
    }

    function initPowercrudTooltips(root = document) {
        const tippyCtor = getTippyCtor();
        if (!tippyCtor) {
            return;
        }

        queryAllWithSelf(root, TOOLTIP_TRIGGER_SELECTOR).forEach(trigger => {
            if (!(trigger instanceof HTMLElement)) {
                return;
            }
            if (trigger._tippy) {
                trigger._tippy.destroy();
            }
            if (isTooltipOverflowTarget(trigger) && !isTruncated(trigger)) {
                return;
            }
            if (!isTooltipOverflowTarget(trigger) && !isTooltipSemanticTarget(trigger)) {
                return;
            }
            tippyCtor(trigger, {
                theme: 'dark',
                placement: 'top',
            });
        });
    }

    function syncFilterToggleLabel(root) {
        const filterCollapse = root.querySelector('#filterCollapse');
        const filterBtn = root.querySelector('[data-powercrud-filter-toggle]');
        if (!filterCollapse || !filterBtn) {
            return;
        }
        const label = filterBtn.querySelector('span');
        if (!label) {
            return;
        }
        const isHidden = filterCollapse.classList.contains('hidden');
        label.textContent = isHidden ? 'Show Filters' : 'Hide Filters';
    }

    function maybeRestoreExpandedFilters(root) {
        const state = ensureObjectListState(root);
        if (state.filterExpansionRestored) {
            return;
        }
        state.filterExpansionRestored = true;

        const filterCollapse = root.querySelector('#filterCollapse');
        if (!filterCollapse) {
            return;
        }
        if (localStorage.getItem('filterExpanded') === 'true') {
            filterCollapse.classList.remove('hidden');
            initPowercrudSearchableSelects(filterCollapse);
            localStorage.removeItem('filterExpanded');
        }
    }

    function toggleFilterVisibility(root) {
        const filterCollapse = root.querySelector('#filterCollapse');
        if (!filterCollapse) {
            return;
        }
        filterCollapse.classList.toggle('hidden');
        syncFilterToggleLabel(root);
        if (!filterCollapse.classList.contains('hidden')) {
            global.setTimeout(() => initPowercrudSearchableSelects(filterCollapse), 0);
        }
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

    function getCurrentFilters() {
        const params = new URLSearchParams(global.location.search);
        const clean = {};
        for (const [key, value] of params) {
            if (value && key !== 'page') {
                clean[key] = value;
            }
        }
        return clean;
    }

    function updateBulkActionsCounter(root, count) {
        const counter = root.querySelector('#selected-items-counter');
        if (counter) {
            counter.textContent = count;
        }
        const container = root.querySelector('#bulk-actions-container');
        if (container) {
            container.classList.toggle('hidden', count === 0);
        }
    }

    function syncBulkSelectionState(root) {
        const selectAllCheckbox = root.querySelector('[data-powercrud-select-all="true"]');
        const checkboxes = Array.from(root.querySelectorAll('[data-powercrud-row-select="true"]'));
        if (!selectAllCheckbox || !checkboxes.length) {
            return;
        }

        const selectedCount = checkboxes.filter(cb => cb.checked).length;
        if (selectedCount === 0) {
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = false;
        } else if (selectedCount === checkboxes.length) {
            selectAllCheckbox.checked = true;
            selectAllCheckbox.indeterminate = false;
        } else {
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = true;
        }
        updateBulkActionsCounter(root, selectedCount);
    }

    function clearSelectionOptimistic(root) {
        root.querySelectorAll('[data-powercrud-row-select="true"]').forEach(cb => {
            cb.checked = false;
        });
        const selectAll = root.querySelector('[data-powercrud-select-all="true"]');
        if (selectAll) {
            selectAll.checked = false;
            selectAll.indeterminate = false;
        }
        updateBulkActionsCounter(root, 0);
    }

    function toggleAllSelection(selectAllCheckbox) {
        const root = getObjectListRoot(selectAllCheckbox);
        if (!root) {
            return;
        }
        const checkboxes = Array.from(root.querySelectorAll('[data-powercrud-row-select="true"]'));
        checkboxes.forEach(cb => {
            cb.checked = selectAllCheckbox.checked;
        });
        updateBulkActionsCounter(root, selectAllCheckbox.checked ? checkboxes.length : 0);

        const htmx = getHtmxInstance();
        const listUrl = root.dataset.powercrudListUrl;
        if (!htmx || !listUrl) {
            return;
        }

        const allIds = checkboxes.map(cb => cb.dataset.id);
        htmx.ajax('POST', `${listUrl}toggle-all-selection/`, {
            values: {
                object_ids: allIds,
                action: selectAllCheckbox.checked ? 'add' : 'remove',
            },
            target: '#bulk-actions-container',
        });
    }

    function handleRowSelectionChange(checkbox) {
        const root = getObjectListRoot(checkbox);
        if (!root) {
            return;
        }
        syncBulkSelectionState(root);
    }

    function refreshTable(root) {
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
            values: getCurrentFilters(),
        });
    }

    function bootstrapObjectList(root) {
        if (!(root instanceof Element)) {
            return;
        }
        ensureObjectListState(root);
        maybeRestoreExpandedFilters(root);
        syncFilterToggleLabel(root);
        syncBulkSelectionState(root);

        const filterCollapse = root.querySelector('#filterCollapse');
        if (filterCollapse && !filterCollapse.classList.contains('hidden')) {
            initPowercrudSearchableSelects(filterCollapse);
        }
    }

    function bootstrapObjectLists(scope = document) {
        getAffectedObjectListRoots(scope).forEach(bootstrapObjectList);
    }

    function getHtmxEventRoots(event) {
        const roots = [];
        const detail = event?.detail || {};
        const eventTarget = asElement(event?.target);

        if (detail.elt instanceof Element) {
            roots.push(detail.elt);
        }
        if (detail.target instanceof Element && detail.target !== detail.elt) {
            roots.push(detail.target);
        }
        if (eventTarget && !roots.includes(eventTarget)) {
            roots.push(eventTarget);
        }

        return roots;
    }

    let activeRowId = null;
    let inlineNoticeEl = null;
    let pendingColumnWidths = null;
    let activeColumnWidths = null;
    let lockedTableRef = null;
    let pendingInlineFocusField = null;
    let pendingInlineSelectHighlight = false;

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
        return activeRowId ? document.getElementById(activeRowId) : null;
    }

    function setActiveRow(row) {
        document
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
        document
            .querySelectorAll(`${INLINE_ROW_SELECTOR}[data-inline-active="true"]`)
            .forEach(el => {
                el.removeAttribute('data-inline-active');
                clearRowWidths(el);
            });
    }

    function getInlineFocusTarget(row, preferredField) {
        if (!row) {
            return null;
        }

        function getTomSelectControlInput(widget) {
            if (!widget) {
                return null;
            }
            const select = widget.querySelector('select');
            if (!select || !select.tomselect) {
                return null;
            }
            const controlInput = select.tomselect.control_input;
            return controlInput instanceof HTMLElement ? controlInput : null;
        }

        const baseFieldSelector =
            '.inline-field-widget input:not([type="hidden"]):not([disabled]), .inline-field-widget select:not([disabled]), .inline-field-widget textarea:not([disabled]), .inline-field-widget [tabindex]:not([tabindex="-1"])';
        if (preferredField) {
            const preferredWidget = row.querySelector(
                `.inline-field-widget[data-inline-field="${preferredField}"]`
            );
            const preferredTomSelectInput = getTomSelectControlInput(preferredWidget);
            if (preferredTomSelectInput) {
                return preferredTomSelectInput;
            }
            const scopedSelector = `.inline-field-widget[data-inline-field="${preferredField}"] input:not([type="hidden"]):not([disabled]), .inline-field-widget[data-inline-field="${preferredField}"] select:not([disabled]), .inline-field-widget[data-inline-field="${preferredField}"] textarea:not([disabled]), .inline-field-widget[data-inline-field="${preferredField}"] [tabindex]:not([tabindex="-1"])`;
            const preferredTarget = row.querySelector(scopedSelector);
            if (preferredTarget) {
                return preferredTarget;
            }
        }
        const firstTomSelectInput = getTomSelectControlInput(
            row.querySelector('.inline-field-widget')
        );
        if (firstTomSelectInput) {
            return firstTomSelectInput;
        }
        const fallbackField = row.querySelector(baseFieldSelector);
        if (fallbackField) {
            return fallbackField;
        }
        return row.querySelector('[data-inline-save], [data-inline-cancel], .inline-edit-trigger');
    }

    function maybeOpenSelectDropdown(focusTarget, triggerField) {
        if (!focusTarget || !triggerField) {
            return;
        }
        let candidate = focusTarget;
        const owningWidget = candidate.closest('.inline-field-widget');
        if (!owningWidget || owningWidget.dataset.inlineField !== triggerField) {
            return;
        }
        if (candidate.tagName !== 'SELECT') {
            candidate = owningWidget.querySelector('select');
        }
        if (!candidate || candidate.disabled) {
            return;
        }
        requestAnimationFrame(() => {
            if (candidate.tomselect) {
                candidate.tomselect.focus();
                candidate.tomselect.open();
                return;
            }
            if (typeof candidate.showPicker === 'function') {
                try {
                    candidate.showPicker();
                    return;
                } catch (err) {
                    console.debug('[powercrud] showPicker fallback', err);
                }
            }
            ['mousedown', 'mouseup', 'click'].forEach(type => {
                candidate.dispatchEvent(
                    new MouseEvent(type, {
                        bubbles: true,
                        cancelable: true,
                        view: window,
                    })
                );
            });
        });
    }

    function maybeSelectInputValue(focusTarget, shouldHighlight) {
        if (!focusTarget || !shouldHighlight) {
            return;
        }
        if (!(focusTarget instanceof HTMLInputElement)) {
            return;
        }
        if (focusTarget.disabled || focusTarget.readOnly) {
            return;
        }
        const allowedTypes = ['text', 'number', 'search', 'tel', 'url', 'email', 'password'];
        const type = (focusTarget.getAttribute('type') || 'text').toLowerCase();
        if (!allowedTypes.includes(type) || !focusTarget.value) {
            return;
        }
        try {
            focusTarget.select();
        } catch (err) {
            try {
                focusTarget.setSelectionRange(0, focusTarget.value.length);
            } catch (innerErr) {
                console.debug('[powercrud] select fallback failed', innerErr);
            }
        }
    }

    function focusRow(row, preferredField) {
        if (!row) {
            return;
        }
        row.classList.add('inline-row-attention');
        const triggerField = preferredField || pendingInlineFocusField;
        const focusTarget = getInlineFocusTarget(row, triggerField);
        pendingInlineFocusField = null;
        if (focusTarget) {
            focusTarget.focus();
            maybeOpenSelectDropdown(focusTarget, triggerField);
            maybeSelectInputValue(focusTarget, pendingInlineSelectHighlight);
            pendingInlineSelectHighlight = false;
        }
        row.scrollIntoView({ behavior: 'smooth', block: 'center' });
        setTimeout(() => row.classList.remove('inline-row-attention'), 600);
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

    function findInlineFormRow(root) {
        if (!(root instanceof HTMLElement)) {
            return null;
        }
        const rows = Array.from(root.querySelectorAll(INLINE_ROW_SELECTOR));
        return rows.find(row => row.querySelector('[data-inline-save]')) || null;
    }

    function bootstrapInlineRow() {
        const row = document.querySelector(`${INLINE_ROW_SELECTOR}[data-inline-active="true"]`);
        if (row) {
            setActiveRow(row);
            wireInlineRow(row);
        }
    }

    function getNoticeElement() {
        if (inlineNoticeEl && document.body.contains(inlineNoticeEl)) {
            return inlineNoticeEl;
        }
        inlineNoticeEl = document.querySelector(INLINE_NOTICE_SELECTOR) || document.getElementById('pc-inline-alert');
        return inlineNoticeEl;
    }

    function clearNotice() {
        const host = getNoticeElement();
        if (!host) {
            return;
        }
        host.innerHTML = '';
        host.classList.add('hidden');
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

    function showInlineNotice(options) {
        const host = getNoticeElement();
        if (!host) {
            return;
        }
        const level = options.level || 'info';
        const levelClasses = {
            warning: 'alert-warning',
            error: 'alert-error',
            info: 'alert-info',
        };
        const alertClass = levelClasses[level] || levelClasses.info;
        host.classList.remove('hidden');

        const lockLabel = options.lockLabel ? `<div class="text-xs opacity-80">${options.lockLabel}</div>` : '';
        const message = options.message || 'Inline editing unavailable.';
        const actionButton = options.refresh && options.refresh.url
            ? `
                <button type="button"
                        class="btn btn-xs btn-outline"
                        data-inline-refresh-btn>
                    Refresh Row
                </button>
            `
            : '';

        host.innerHTML = `
            <div class="alert ${alertClass} shadow-sm flex flex-wrap gap-2 items-center">
                <span class="flex-1">${message}</span>
                ${lockLabel}
                ${actionButton}
                <button type="button" class="btn btn-xs btn-ghost" data-inline-dismiss>
                    Dismiss
                </button>
            </div>
        `;

        const refreshBtn = host.querySelector('[data-inline-refresh-btn]');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => refreshInlineRow(options.refresh));
        }
        const dismissBtn = host.querySelector('[data-inline-dismiss]');
        if (dismissBtn) {
            dismissBtn.addEventListener('click', clearNotice);
        }
    }

    function handleInlineGuardEvent(event, level) {
        const payload = event.detail && event.detail.value ? event.detail.value : (event.detail || {});
        const refreshPayload = payload.refresh;
        const lockMeta = payload.lock || {};
        clearActiveRow();
        showInlineNotice({
            level,
            message: payload.message,
            lockLabel: lockMeta.label,
            refresh: refreshPayload,
        });
        pendingColumnWidths = null;
        activeColumnWidths = null;
        unlockTableWidth();
    }

    function startFormSpinner(form) {
        if (!form || FORM_SPINNER_STATE.has(form)) {
            return;
        }
        const saveBtn = form.querySelector('[data-form-save]');
        if (!saveBtn) {
            return;
        }
        FORM_SPINNER_STATE.set(form, {
            button: saveBtn,
            html: saveBtn.innerHTML,
        });
        saveBtn.disabled = true;
        saveBtn.style.width = `${saveBtn.offsetWidth}px`;
        saveBtn.innerHTML = '<span class="loading loading-spinner loading-sm text-center mx-auto"></span>';
    }

    function stopFormSpinner(form) {
        const state = FORM_SPINNER_STATE.get(form);
        if (!state) {
            return;
        }
        state.button.disabled = false;
        state.button.innerHTML = state.html;
        state.button.style.width = '';
        FORM_SPINNER_STATE.delete(form);
    }

    function toggleInlineSaving(row, isSaving) {
        if (!row) {
            return;
        }
        const saveBtn = row.querySelector('[data-inline-save]');
        if (!saveBtn) {
            return;
        }
        saveBtn.disabled = isSaving;
        if (isSaving) {
            saveBtn.dataset.originalLabel = saveBtn.innerHTML;
            saveBtn.dataset.originalWidth = saveBtn.offsetWidth;
            saveBtn.style.width = `${saveBtn.dataset.originalWidth}px`;
            saveBtn.innerHTML = '<span class="loading loading-spinner loading-xs text-center mx-auto"></span>';
        } else if (saveBtn.dataset.originalLabel) {
            saveBtn.innerHTML = saveBtn.dataset.originalLabel;
            if (saveBtn.dataset.originalWidth) {
                saveBtn.style.width = '';
                delete saveBtn.dataset.originalWidth;
            }
            delete saveBtn.dataset.originalLabel;
        }
    }

    global.getCurrentFilters = getCurrentFilters;
    global.initPowercrudSearchableSelects = initPowercrudSearchableSelects;
    global.destroyPowercrudSearchableSelects = destroyPowercrudSearchableSelects;
    global.initPowercrudTooltips = initPowercrudTooltips;
    global.destroyPowercrudTooltips = destroyPowercrudTooltips;

    document.addEventListener('DOMContentLoaded', () => {
        const htmx = global.htmx;
        if (htmx?.process) {
            htmx.process(document.body);
        } else {
            warnMissingDependency('htmx', 'window.htmx. Load HTMX before powercrud/js/powercrud.js');
        }

        initPowercrudSearchableSelects(document);
        bootstrapObjectLists(document);
        initPowercrudTooltips(document);
        bootstrapInlineRow();
    });

    document.addEventListener('click', event => {
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

        const resetTrigger = trigger.closest('[data-powercrud-filter-reset]');
        if (resetTrigger) {
            const root = getObjectListRoot(resetTrigger);
            if (root) {
                resetFilterForm(root);
            }
            return;
        }

        const clearSelectionTrigger = trigger.closest('[data-powercrud-clear-selection]');
        if (clearSelectionTrigger) {
            const root = getObjectListRoot(clearSelectionTrigger);
            if (root) {
                clearSelectionOptimistic(root);
            }
        }
    });

    document.addEventListener('change', event => {
        const target = asElement(event.target);
        if (!target) {
            return;
        }

        if (target.matches('[data-powercrud-select-all="true"]')) {
            toggleAllSelection(target);
            return;
        }

        if (target.matches('[data-powercrud-row-select="true"]')) {
            handleRowSelectionChange(target);
        }
    });

    document.addEventListener('submit', event => {
        const form = asElement(event.target);
        if (!form) {
            return;
        }
        if (form.matches('[data-powercrud-filter-form="true"]')) {
            removeEmptyFields(form);
        }
        if (form.matches('[data-powercrud-form="object"]')) {
            startFormSpinner(form);
        }
    }, true);

    document.body.addEventListener('bulkEditSuccess', () => {
        const modal = document.getElementById('powercrudBaseModal');
        if (modal && typeof modal.close === 'function') {
            modal.close();
        }
        getAffectedObjectListRoots(document).forEach(clearSelectionOptimistic);
    });

    document.body.addEventListener('bulkEditQueued', () => {
        getAffectedObjectListRoots(document).forEach(clearSelectionOptimistic);
    });

    document.body.addEventListener('refreshTable', event => {
        const eventTarget = asElement(event.target);
        const root = getObjectListRoot(eventTarget) || getAffectedObjectListRoots(document)[0];
        if (root) {
            refreshTable(root);
        }
    });

    document.addEventListener('htmx:beforeSwap', event => {
        getHtmxEventRoots(event).forEach(root => {
            destroyPowercrudSearchableSelects(root);
            destroyPowercrudTooltips(root);
        });

        if (!activeRowId) {
            return;
        }
        const target = asElement(event.target);
        if (targetTouchesInlineRows(target)) {
            clearActiveRow();
            clearNotice();
        }
    });

    document.addEventListener('htmx:afterSwap', event => {
        getHtmxEventRoots(event).forEach(root => {
            initPowercrudSearchableSelects(root);
            bootstrapObjectLists(root);
            initPowercrudTooltips(root);
        });

        const target = asElement(event.target);
        if (!(target instanceof HTMLElement)) {
            return;
        }

        if (targetTouchesInlineRows(target) && !target.matches(INLINE_ROW_SELECTOR)) {
            const targetHasActiveInlineRow = Boolean(
                target.querySelector(`${INLINE_ROW_SELECTOR}[data-inline-active="true"]`)
            );
            const inlineFormRow = findInlineFormRow(target);
            if (!targetHasActiveInlineRow && inlineFormRow) {
                inlineFormRow.setAttribute('data-inline-active', 'true');
                setActiveRow(inlineFormRow);
                wireInlineRow(inlineFormRow);
                focusRow(inlineFormRow);
                const widthsToApply = pendingColumnWidths || activeColumnWidths;
                if (widthsToApply && widthsToApply.length) {
                    applyRowWidths(inlineFormRow, widthsToApply);
                    activeColumnWidths = widthsToApply.slice();
                    pendingColumnWidths = null;
                }
                return;
            }
            if (!targetHasActiveInlineRow) {
                clearActiveRow();
                clearNotice();
            }
        }

        if (target.matches(INLINE_ROW_SELECTOR)) {
            if (target.dataset.inlineActive === 'true') {
                setActiveRow(target);
                wireInlineRow(target);
                focusRow(target);
                const widthsToApply = pendingColumnWidths || activeColumnWidths;
                if (widthsToApply && widthsToApply.length) {
                    applyRowWidths(target, widthsToApply);
                    activeColumnWidths = widthsToApply.slice();
                    pendingColumnWidths = null;
                }
            } else if (activeRowId && target.id === activeRowId) {
                setActiveRow(null);
                clearRowWidths(target);
                unlockTableWidth(target.closest(INLINE_TABLE_SELECTOR));
                pendingColumnWidths = null;
                activeColumnWidths = null;
            } else {
                clearRowWidths(target);
                if (!document.querySelector(`${INLINE_ROW_SELECTOR}[data-inline-active="true"]`)) {
                    unlockTableWidth(target.closest(INLINE_TABLE_SELECTOR));
                    activeColumnWidths = null;
                    pendingColumnWidths = null;
                }
            }
            return;
        }

        if (target.matches('.inline-field-widget[data-inline-field]')) {
            setWidgetRefreshing(target, false);
            initInlineSearchableSelects(target);
        }

        if (activeRowId) {
            const row = target.closest(INLINE_ROW_SELECTOR);
            if (row && row.id === activeRowId && row.dataset.inlineActive === 'true') {
                wireInlineRow(row);
            }
        }
    });

    document.addEventListener('htmx:afterSettle', event => {
        getHtmxEventRoots(event).forEach(root => {
            initPowercrudSearchableSelects(root);
            bootstrapObjectLists(root);
            initPowercrudTooltips(root);
        });
    });

    document.addEventListener('htmx:beforeRequest', event => {
        const target = event.detail && event.detail.elt;
        if (target && target.matches && target.matches('[data-inline-save]')) {
            const row = target.closest(INLINE_ROW_SELECTOR);
            toggleInlineSaving(row, true);
        }

        const trigger = asElement(event.detail && event.detail.elt);
        if (!trigger || !trigger.classList.contains('inline-edit-trigger')) {
            return;
        }
        pendingInlineFocusField = trigger.dataset.inlineField || null;
        pendingInlineSelectHighlight = true;
        const row = trigger.closest(INLINE_ROW_SELECTOR);
        const activeRow = getActiveRow();
        if (activeRow && row && activeRow !== row) {
            event.preventDefault();
            console.debug('[powercrud] Inline guard prevented second row edit', {
                activeRowId,
                blockedRowId: row.id,
            });
            focusRow(activeRow);
            return;
        }
        if (row) {
            const table = row.closest(INLINE_TABLE_SELECTOR);
            if (table) {
                lockTableWidth(table);
            }
            pendingColumnWidths = snapshotRowWidths(row);
        }
    });

    document.addEventListener('htmx:afterRequest', event => {
        const target = event.detail && event.detail.elt;
        if (target && target.matches && target.matches('[data-powercrud-form="object"]')) {
            stopFormSpinner(target);
        }
        if (target && target.matches && target.matches('[data-inline-save]')) {
            const row = target.closest(INLINE_ROW_SELECTOR);
            toggleInlineSaving(row, false);
        }
    });

    document.addEventListener('htmx:responseError', event => {
        const target = event.detail && event.detail.elt;
        if (target && target.matches && target.matches('[data-powercrud-form="object"]')) {
            stopFormSpinner(target);
        }
        if (target instanceof HTMLElement && target.matches('.inline-field-widget[data-inline-refreshing="true"]')) {
            setWidgetRefreshing(target, false);
        }
    });

    document.body.addEventListener('inline-row-locked', event => {
        handleInlineGuardEvent(event, 'warning');
    });

    document.body.addEventListener('inline-row-forbidden', event => {
        handleInlineGuardEvent(event, 'error');
    });

    document.body.addEventListener('inline-row-error', event => {
        const payload = event.detail && event.detail.value ? event.detail.value : (event.detail || {});
        if (payload.row_id) {
            const bannerRow = document.getElementById(payload.row_id);
            if (bannerRow) {
                focusRow(bannerRow);
            }
        }
        showInlineNotice({
            level: 'error',
            message: payload.message || 'Inline save failed. Check the highlighted fields.',
        });
    });

    global.addEventListener('resize', () => {
        if (tooltipResizeTimer) {
            clearTimeout(tooltipResizeTimer);
        }
        tooltipResizeTimer = setTimeout(() => initPowercrudTooltips(document), 100);
    });
})(window);
