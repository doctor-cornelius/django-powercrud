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
    const RANGE_SELECT_SUPPRESS_CLASS = 'powercrud-range-selecting';
    const VISIBLE_FILTERS_PARAM = 'visible_filters';
    const VISIBLE_FILTERS_STORAGE_PREFIX = 'powercrud:visible-filters:';
    const FILTER_FAVOURITE_STORAGE_PREFIX = 'powercrud:selected-filter-favourite:';

    const warnedDeps = {
        htmx: false,
        tippy: false,
        tomSelect: false,
    };

    const objectListState = new WeakMap();
    const FORM_SPINNER_STATE = new WeakMap();
    const BUTTON_SPINNER_STATE = new WeakMap();
    let tooltipResizeTimer = null;
    let activeRowActionsMenu = null;
    let activeRowActionsTrigger = null;
    let activeFilterFavouritesPanel = null;
    let activeFilterFavouritesTrigger = null;

    function warnMissingDependency(name, detail) {
        if (warnedDeps[name]) {
            return;
        }
        warnedDeps[name] = true;
        console.warn(`PowerCRUD frontend: missing ${detail}.`);
    }

    function asElement(value) {
        if (value instanceof Element) {
            return value;
        }
        if (value instanceof Node && value.parentElement instanceof Element) {
            return value.parentElement;
        }
        return null;
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
                lastRowSelectionAnchorId: null,
                optionalFilterVisibilityRestored: false,
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

    function syncTomSelectValue(selectElement) {
        if (!(selectElement instanceof HTMLSelectElement) || !selectElement.tomselect) {
            return;
        }

        if (typeof selectElement.tomselect.sync === 'function') {
            selectElement.tomselect.sync();
            return;
        }

        const selectedValue = selectElement.tomselect.getValue();
        if (selectElement.multiple) {
            const selectedValues = Array.isArray(selectedValue) ? selectedValue.map(String) : [];
            Array.from(selectElement.options).forEach(option => {
                option.selected = selectedValues.includes(option.value);
            });
            return;
        }

        const normalizedValue = Array.isArray(selectedValue)
            ? (selectedValue[0] ?? '')
            : (selectedValue ?? '');
        selectElement.value = String(normalizedValue);
    }

    function syncTomSelectValues(container) {
        if (!(container instanceof Element)) {
            return;
        }
        container.querySelectorAll('select').forEach(selectElement => {
            syncTomSelectValue(selectElement);
        });
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
                selectElement.dispatchEvent(new Event('change', { bubbles: true }));
            },
            onItemRemove() {
                this.setTextboxValue('');
                this.refreshOptions(true);
                selectElement.dispatchEvent(new Event('change', { bubbles: true }));
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

    function isTooltipSemanticCellTarget(trigger) {
        return trigger?.dataset?.powercrudTooltip === 'semantic-cell';
    }

    function getTooltipTheme(trigger) {
        if (isTooltipSemanticCellTarget(trigger)) {
            return 'powercrud-semantic-cell';
        }
        return 'powercrud';
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
            const isOverflowTarget = isTooltipOverflowTarget(trigger);
            const isSemanticTarget = isTooltipSemanticTarget(trigger);
            const isSemanticCellTarget = isTooltipSemanticCellTarget(trigger);
            if (!isOverflowTarget && !isSemanticTarget && !isSemanticCellTarget) {
                return;
            }
            tippyCtor(trigger, {
                theme: getTooltipTheme(trigger),
                placement: 'top',
                onShow(instance) {
                    if (!isOverflowTarget) {
                        return true;
                    }
                    return isTruncated(instance.reference);
                },
            });
        });
    }

    function schedulePowercrudTooltipRefresh(root = document, delay = 0) {
        global.setTimeout(() => {
            initPowercrudTooltips(root);
        }, delay);
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

    function getFilterPanelStorageKey(root) {
        const listUrl = root?.dataset?.powercrudListUrl || global.location.pathname || 'default';
        return `powercrud:filter-panel:${listUrl}`;
    }

    function getVisibleFiltersStorageKey(root) {
        const listUrl = root?.dataset?.powercrudListUrl || global.location.pathname || 'default';

        try {
            const url = new URL(listUrl, global.location.origin);
            return `${VISIBLE_FILTERS_STORAGE_PREFIX}${url.pathname}`;
        } catch (_error) {
            return `${VISIBLE_FILTERS_STORAGE_PREFIX}${listUrl}`;
        }
    }

    function setPersistedFilterPanelState(root, isOpen) {
        global.sessionStorage?.setItem(getFilterPanelStorageKey(root), isOpen ? 'open' : 'closed');
    }

    function getPersistedFilterPanelState(root) {
        return global.sessionStorage?.getItem(getFilterPanelStorageKey(root)) || '';
    }

    function getAddFilterContainer(root) {
        return root.querySelector('[data-powercrud-add-filter-container]');
    }

    function getFilterFavouritesContainer(root) {
        return root.querySelector('[data-powercrud-filter-favourites-toolbar="true"]');
    }

    function getFilterFavouritesToolbarById(toolbarDomId) {
        if (!toolbarDomId) {
            return null;
        }
        const toolbar = document.getElementById(toolbarDomId);
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

    function getRowActionsDropdownContainer(trigger) {
        if (!(trigger instanceof Element)) {
            return null;
        }
        return trigger.closest('[data-powercrud-row-actions-dropdown="true"]');
    }

    function getRowActionsTemplate(trigger) {
        const container = getRowActionsDropdownContainer(trigger);
        if (!(container instanceof Element)) {
            return null;
        }
        const template = container.querySelector('[data-powercrud-row-actions-template="true"]');
        return template instanceof HTMLElement ? template : null;
    }

    function closeRowActionsMenu() {
        if (activeRowActionsTrigger instanceof HTMLElement) {
            activeRowActionsTrigger.setAttribute('aria-expanded', 'false');
        }
        if (activeRowActionsMenu instanceof HTMLElement && activeRowActionsMenu.parentNode) {
            activeRowActionsMenu.parentNode.removeChild(activeRowActionsMenu);
        }
        activeRowActionsMenu = null;
        activeRowActionsTrigger = null;
    }

    function positionRowActionsMenu(menuElement, triggerElement) {
        if (!(menuElement instanceof HTMLElement) || !(triggerElement instanceof HTMLElement)) {
            return;
        }

        const viewportPadding = 8;
        const menuGap = 4;
        const triggerRect = triggerElement.getBoundingClientRect();
        const menuRect = menuElement.getBoundingClientRect();

        const spaceBelow = global.innerHeight - triggerRect.bottom - viewportPadding;
        const spaceAbove = triggerRect.top - viewportPadding;
        const shouldOpenUpward = menuRect.height > spaceBelow && spaceAbove > spaceBelow;

        let top = shouldOpenUpward
            ? triggerRect.top - menuRect.height - menuGap
            : triggerRect.bottom + menuGap;
        let left = triggerRect.right - menuRect.width;

        top = Math.max(
            viewportPadding,
            Math.min(top, global.innerHeight - menuRect.height - viewportPadding),
        );
        left = Math.max(
            viewportPadding,
            Math.min(left, global.innerWidth - menuRect.width - viewportPadding),
        );

        menuElement.style.top = `${top}px`;
        menuElement.style.left = `${left}px`;
    }

    function openRowActionsMenu(trigger) {
        if (!(trigger instanceof HTMLElement)) {
            return;
        }

        const template = getRowActionsTemplate(trigger);
        if (!(template instanceof HTMLElement)) {
            return;
        }

        closeRowActionsMenu();

        const menuElement = template.firstElementChild?.cloneNode(true);
        if (!(menuElement instanceof HTMLElement)) {
            return;
        }

        menuElement.dataset.powercrudRowActionsFloatingPanel = 'true';
        menuElement.style.position = 'fixed';
        menuElement.style.visibility = 'hidden';
        menuElement.style.pointerEvents = 'none';

        document.body.appendChild(menuElement);

        if (global.htmx?.process) {
            global.htmx.process(menuElement);
        }
        initPowercrudTooltips(menuElement);

        positionRowActionsMenu(menuElement, trigger);

        menuElement.style.visibility = '';
        menuElement.style.pointerEvents = '';

        trigger.setAttribute('aria-expanded', 'true');
        activeRowActionsMenu = menuElement;
        activeRowActionsTrigger = trigger;
    }

    function toggleRowActionsMenu(trigger) {
        if (!(trigger instanceof HTMLElement)) {
            return;
        }

        if (activeRowActionsTrigger === trigger && activeRowActionsMenu instanceof HTMLElement) {
            closeRowActionsMenu();
            return;
        }

        openRowActionsMenu(trigger);
    }

    function getFilterFavouritesDropdowns(scope = document) {
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

    function syncFilterFavouritesTriggerTooltip(triggerLabel, selectedLabel) {
        if (!(triggerLabel instanceof HTMLElement)) {
            return;
        }

        const shouldShowTooltip = selectedLabel.length > 15;

        if (triggerLabel._tippy) {
            triggerLabel._tippy.destroy();
        }

        if (shouldShowTooltip) {
            triggerLabel.setAttribute('data-powercrud-tooltip', 'overflow');
            triggerLabel.setAttribute('data-tippy-content', selectedLabel);
            return;
        }

        triggerLabel.removeAttribute('data-powercrud-tooltip');
        triggerLabel.removeAttribute('data-tippy-content');
    }

    function syncFilterFavouritesTriggerLabel(toolbar) {
        if (!(toolbar instanceof Element)) {
            return;
        }

        const triggerLabel = toolbar.querySelector('[data-powercrud-filter-favourites-trigger-label="true"]');
        if (!(triggerLabel instanceof Element)) {
            return;
        }

        const defaultLabel = toolbar
            .querySelector('[data-powercrud-filter-favourites-trigger="true"]')
            ?.getAttribute('data-powercrud-filter-favourites-default-label')
            || 'Favourites';
        const favouriteSelect = getFilterFavouritesSelect(toolbar);
        const selectedOption = getSelectedFavouriteOption(favouriteSelect);
        const selectedLabel = selectedOption?.textContent?.trim() || '';
        triggerLabel.textContent = selectedLabel || defaultLabel;
        syncFilterFavouritesTriggerTooltip(triggerLabel, selectedLabel);

        if (selectedLabel) {
            schedulePowercrudTooltipRefresh(toolbar);
        }
    }

    function getSelectedFavouriteOption(selectElement) {
        if (!(selectElement instanceof HTMLSelectElement) || !selectElement.value) {
            return null;
        }

        const selectedOption = selectElement.options[selectElement.selectedIndex];
        return selectedOption instanceof HTMLOptionElement ? selectedOption : null;
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

    function setFilterFavouritesDropdownOpen(toolbar, isOpen) {
        if (!(toolbar instanceof Element)) {
            return;
        }
        toolbar.classList.toggle('dropdown-open', Boolean(isOpen));
    }

    function closeFilterFavouritesDropdowns(exceptToolbar = null) {
        getFilterFavouritesDropdowns(document).forEach(toolbar => {
            const shouldRemainOpen = (
                exceptToolbar instanceof Element
                && toolbar === exceptToolbar
                && activeFilterFavouritesPanel instanceof HTMLElement
            );
            setFilterFavouritesDropdownOpen(toolbar, shouldRemainOpen);
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
        if (explicitKey) {
            return `${FILTER_FAVOURITE_STORAGE_PREFIX}${explicitKey}`;
        }

        const listUrl = root?.dataset?.powercrudListUrl || global.location.pathname || 'default';
        try {
            const url = new URL(listUrl, global.location.origin);
            return `${FILTER_FAVOURITE_STORAGE_PREFIX}${url.pathname}`;
        } catch (_error) {
            return `${FILTER_FAVOURITE_STORAGE_PREFIX}${listUrl}`;
        }
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
        return global.sessionStorage?.getItem(getSelectedFilterFavouriteStorageKey(root, toolbar)) || '';
    }

    function setPendingSelectedFilterFavouriteId(root, toolbar = null, favouriteId = '') {
        const storageKey = getSelectedFilterFavouriteStorageKey(root, toolbar);
        const normalizedId = String(favouriteId || '').trim();
        if (!normalizedId) {
            global.sessionStorage?.removeItem(storageKey);
            return;
        }
        global.sessionStorage?.setItem(storageKey, normalizedId);
    }

    function clearAllPendingFilterFavouriteSelections() {
        if (!global.sessionStorage) {
            return;
        }

        const keysToRemove = [];
        for (let index = 0; index < global.sessionStorage.length; index += 1) {
            const key = global.sessionStorage.key(index);
            if (key && key.startsWith(FILTER_FAVOURITE_STORAGE_PREFIX)) {
                keysToRemove.push(key);
            }
        }

        keysToRemove.forEach(key => {
            global.sessionStorage?.removeItem(key);
        });
    }

    function isShellContentNavigationTrigger(element) {
        if (!(element instanceof Element) || !element.matches('[hx-target][hx-get], [hx-target][hx-post]')) {
            return false;
        }

        const targetSelector = String(element.getAttribute('hx-target') || '').trim();
        return targetSelector === '#content' && !element.closest(OBJECT_LIST_ROOT_SELECTOR);
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

    function syncFilterFavouritesVisibility(root, isOpen) {
        const favouritesContainer = getFilterFavouritesContainer(root);
        if (!favouritesContainer) {
            return;
        }

        favouritesContainer.classList.toggle('hidden', !isOpen);
    }

    function syncFilterFavouritesSelection(root) {
        const favouritesContainer = getFilterFavouritesContainer(root);
        const favouriteSelect = getFilterFavouritesSelect(favouritesContainer);
        if (!favouritesContainer || !favouriteSelect) {
            syncFilterFavouritesTriggerLabel(favouritesContainer);
            return;
        }

        const effectiveSelectedId = (
            getPendingSelectedFilterFavouriteId(root, favouritesContainer)
            || getServerSelectedFilterFavouriteId(favouritesContainer)
        );
        const hasSelectableOption = Array.from(favouriteSelect.options).some(option => option.value);
        const hasSelectedOption = Array.from(favouriteSelect.options).some(
            option => option.value === effectiveSelectedId
        );

        if (hasSelectedOption && favouriteSelect.value !== effectiveSelectedId) {
            favouriteSelect.value = effectiveSelectedId;
        } else if (!effectiveSelectedId) {
            favouriteSelect.value = '';
        } else if (!hasSelectedOption) {
            favouriteSelect.value = '';
            setPendingSelectedFilterFavouriteId(root, favouritesContainer, '');
        }

        const hasSelectedFavourite = Boolean(favouriteSelect.value);
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
                button.disabled = floatingSelect.disabled || !hasSelectableOption || !Boolean(floatingSelect.value);
            });
    }

    function clearPendingFilterFavouriteSelection(root) {
        const favouritesContainer = getFilterFavouritesContainer(root);
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
        syncFilterFavouritesSelection(root);
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
            setPendingSelectedFilterFavouriteId(root, toolbar, favouriteSelect.value);
            if (selectedFavouriteField instanceof HTMLInputElement) {
                selectedFavouriteField.value = favouriteSelect.value || '';
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
        const selectedFavouriteId = panelSelect?.value || toolbarSelect?.value || '';
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
                    || !Boolean(panelSelect.value);
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

    function positionFilterFavouritesPanel(panelElement, triggerElement) {
        if (!(panelElement instanceof HTMLElement) || !(triggerElement instanceof HTMLElement)) {
            return;
        }

        const viewportPadding = 8;
        const panelGap = 8;
        const triggerRect = triggerElement.getBoundingClientRect();
        const panelRect = panelElement.getBoundingClientRect();
        const spaceBelow = global.innerHeight - triggerRect.bottom - viewportPadding;
        const spaceAbove = triggerRect.top - viewportPadding;
        const shouldOpenUpward = panelRect.height > spaceBelow && spaceAbove > spaceBelow;

        let top = shouldOpenUpward
            ? triggerRect.top - panelRect.height - panelGap
            : triggerRect.bottom + panelGap;
        let left = triggerRect.left;

        top = Math.max(
            viewportPadding,
            Math.min(top, global.innerHeight - panelRect.height - viewportPadding),
        );
        left = Math.max(
            viewportPadding,
            Math.min(left, global.innerWidth - panelRect.width - viewportPadding),
        );

        panelElement.style.top = `${top}px`;
        panelElement.style.left = `${left}px`;
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

        panelShell.dataset.powercrudFilterFavouritesFloatingPanel = 'true';
        panelShell.dataset.powercrudToolbarDomId = toolbar.id || '';
        panelShell.style.position = 'fixed';
        panelShell.style.visibility = 'hidden';
        panelShell.style.pointerEvents = 'none';

        const panel = panelShell.querySelector('[data-powercrud-filter-favourites-panel="true"]');
        if (!(panel instanceof HTMLElement)) {
            return;
        }

        syncFavouriteToolbarState(toolbar);
        syncFavouritePanelState(panel, toolbar);

        document.body.appendChild(panelShell);

        if (global.htmx?.process) {
            global.htmx.process(panelShell);
        }
        initPowercrudSearchableSelects(panelShell);
        initPowercrudTooltips(panelShell);
        positionFilterFavouritesPanel(panelShell, trigger);

        panelShell.style.visibility = '';
        panelShell.style.pointerEvents = '';
        setFilterFavouritesDropdownOpen(toolbar, true);
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
        try {
            const rawValue = global.localStorage?.getItem(getVisibleFiltersStorageKey(root));
            if (!rawValue) {
                return [];
            }

            const parsedValue = JSON.parse(rawValue);
            if (!Array.isArray(parsedValue)) {
                return [];
            }
            return dedupeFilterNames(parsedValue);
        } catch (_error) {
            return [];
        }
    }

    function setStoredOptionalFilterNames(root, names) {
        const normalizedNames = dedupeFilterNames(names);
        const storageKey = getVisibleFiltersStorageKey(root);

        if (!normalizedNames.length) {
            global.localStorage?.removeItem(storageKey);
            return;
        }

        global.localStorage?.setItem(storageKey, JSON.stringify(normalizedNames));
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
            const input = document.createElement('input');
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

    function buildCurrentRootValues(root, options = {}) {
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
            if (field.closest('[data-powercrud-filter-favourites-toolbar="true"]')) {
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

    function normaliseListUrl(listUrl) {
        if (!listUrl) {
            return '';
        }
        try {
            return new URL(listUrl, global.location.origin).pathname;
        } catch (_error) {
            return String(listUrl);
        }
    }

    function getCurrentSortValue() {
        try {
            return new URL(global.location.href).searchParams.get('sort') || '';
        } catch (_error) {
            return '';
        }
    }

    function getCurrentPageSizeValue(root) {
        const pageSizeSelect = root.querySelector('#page-size-select');
        if (pageSizeSelect instanceof HTMLSelectElement) {
            return pageSizeSelect.value || '';
        }

        try {
            return new URL(global.location.href).searchParams.get('page_size') || '';
        } catch (_error) {
            return '';
        }
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

    function findObjectListRootByListUrl(listUrl) {
        const normalizedTarget = normaliseListUrl(listUrl);
        return getAffectedObjectListRoots(document).find(root => {
            return normaliseListUrl(root?.dataset?.powercrudListUrl) === normalizedTarget;
        }) || null;
    }

    function populateFavouriteSaveForm(form) {
        if (!(form instanceof HTMLFormElement)) {
            return;
        }

        const listUrlField = form.querySelector('input[name="list_view_url"]');
        const listUrl = listUrlField instanceof HTMLInputElement ? listUrlField.value : '';
        const root = findObjectListRootByListUrl(listUrl) || getAffectedObjectListRoots(document)[0];
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

        const values = buildCurrentRootValues(root, {
            preservePage: options.preservePage === true,
        });
        htmx.ajax('GET', listUrl, {
            target: root,
            swap: 'outerHTML',
            values,
            headers: {
                'X-Filter-Setting-Request': 'true',
            },
            pushURL: options.pushURL !== false,
        });
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
        const params = new URLSearchParams(global.location.search);
        const clean = {};
        const preservePage = options.preservePage === true;
        for (const [key, value] of params) {
            if (!value) {
                continue;
            }
            if (!preservePage && key === 'page') {
                continue;
            }
            if (key in clean) {
                if (Array.isArray(clean[key])) {
                    clean[key].push(value);
                } else {
                    clean[key] = [clean[key], value];
                }
                continue;
            }
            clean[key] = value;
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
        syncSelectionAwareExtraButtons(root, count);
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

            button.classList.toggle('btn-disabled', disable);
            button.classList.toggle('opacity-50', disable);
            button.classList.toggle('pointer-events-none', disable);

            if (disable) {
                button.setAttribute('aria-disabled', 'true');
                if (reason) {
                    button.setAttribute('data-tippy-content', reason);
                    button.setAttribute('data-powercrud-tooltip', 'semantic');
                }
            } else {
                button.removeAttribute('aria-disabled');
                if (button.dataset.powercrudSelectionMinReason) {
                    button.removeAttribute('data-tippy-content');
                    button.removeAttribute('data-powercrud-tooltip');
                }
            }
        });
    }

    function syncBulkSelectionState(root) {
        const selectAllCheckbox = root.querySelector('[data-powercrud-select-all="true"]');
        const checkboxes = getRowSelectionCheckboxes(root);
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
    }

    function clearSelectionOptimistic(root) {
        getRowSelectionCheckboxes(root).forEach(cb => {
            cb.checked = false;
        });
        const selectAll = root.querySelector('[data-powercrud-select-all="true"]');
        if (selectAll) {
            selectAll.checked = false;
            selectAll.indeterminate = false;
        }
        ensureObjectListState(root).lastRowSelectionAnchorId = null;
        updateBulkActionsCounter(root, 0);
    }

    function getRowSelectionCheckboxes(root) {
        return Array.from(root.querySelectorAll('[data-powercrud-row-select="true"]'));
    }

    function clearDocumentSelection() {
        const selection = global.getSelection ? global.getSelection() : null;
        if (selection && typeof selection.removeAllRanges === 'function') {
            selection.removeAllRanges();
        }
    }

    function setRangeSelectionSuppressed(suppressed) {
        if (!(document.body instanceof HTMLBodyElement)) {
            return;
        }
        document.body.classList.toggle(RANGE_SELECT_SUPPRESS_CLASS, suppressed);
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

    function persistSelectionBatch(root, objectIds, action) {
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
        const checkboxes = getRowSelectionCheckboxes(root);
        checkboxes.forEach(cb => {
            cb.checked = selectAllCheckbox.checked;
        });
        if (selectAllCheckbox.checked) {
            showBulkActionsContainer(root);
        }

        const htmx = getHtmxInstance();
        const listUrl = root.dataset.powercrudListUrl;
        if (!htmx || !listUrl) {
            return;
        }

        const allIds = checkboxes.map(cb => cb.dataset.id);
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
                persistSelectionBatch(
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

    function bootstrapObjectList(root) {
        if (!(root instanceof Element)) {
            return;
        }
        ensureObjectListState(root);
        getRowSelectionCheckboxes(root).forEach(checkbox => {
            checkbox.checked = checkbox.dataset.powercrudInitialChecked === 'true';
        });
        const selectAllCheckbox = root.querySelector('[data-powercrud-select-all="true"]');
        if (selectAllCheckbox instanceof HTMLInputElement) {
            selectAllCheckbox.checked = selectAllCheckbox.dataset.powercrudInitialChecked === 'true';
            selectAllCheckbox.indeterminate = (
                selectAllCheckbox.dataset.powercrudInitialIndeterminate === 'true'
            );
        }
        applyFilterPanelState(root);
        maybeRestoreStoredOptionalFilterVisibility(root);
        syncFilterFavouritesSelection(root);
        syncBulkSelectionState(root);
        syncSelectionAwareExtraButtons(root);
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

    function startButtonSpinner(button) {
        if (!button || BUTTON_SPINNER_STATE.has(button)) {
            return;
        }
        BUTTON_SPINNER_STATE.set(button, {
            html: button.innerHTML,
        });
        button.disabled = true;
        button.style.width = `${button.offsetWidth}px`;
        button.innerHTML = '<span class="loading loading-spinner loading-sm text-center mx-auto"></span>';
    }

    function stopButtonSpinner(button) {
        const state = BUTTON_SPINNER_STATE.get(button);
        if (!state) {
            return;
        }
        button.disabled = false;
        button.innerHTML = state.html;
        button.style.width = '';
        BUTTON_SPINNER_STATE.delete(button);
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
    global.powercrudToggleFavouriteSaveForm = toggleFavouriteSaveForm;

    const selectionSuppressionStyle = document.createElement('style');
    selectionSuppressionStyle.textContent = `
        body.${RANGE_SELECT_SUPPRESS_CLASS},
        body.${RANGE_SELECT_SUPPRESS_CLASS} * {
            user-select: none !important;
        }
    `;
    document.head.appendChild(selectionSuppressionStyle);

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

    global.addEventListener('pagehide', () => {
        closeRowActionsMenu();
        closeFilterFavouritesDropdowns();
        getAffectedObjectListRoots(document).forEach(root => {
            clearPendingFilterFavouriteSelection(root);
        });
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

        const favouritesTrigger = trigger.closest('[data-powercrud-filter-favourites-trigger="true"]');
        if (favouritesTrigger) {
            event.preventDefault();
            toggleFilterFavouritesPanel(favouritesTrigger);
            return;
        }

        const resetTrigger = trigger.closest('[data-powercrud-filter-reset]');
        if (resetTrigger) {
            const root = getObjectListRoot(resetTrigger);
            if (root) {
                setStoredOptionalFilterNames(root, []);
                setPersistedOptionalFilterNames(root, []);
                resetFilterForm(root);
                clearPendingFilterFavouriteSelection(root);
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

        const clearSelectionTrigger = trigger.closest('[data-powercrud-clear-selection]');
        if (clearSelectionTrigger) {
            const root = getObjectListRoot(clearSelectionTrigger);
            if (root) {
                clearSelectionOptimistic(root);
            }
            return;
        }

        const favouriteApplyTrigger = trigger.closest('[data-powercrud-favourite-apply="true"]');
        if (favouriteApplyTrigger) {
            const actionForm = favouriteApplyTrigger.closest('form');
            const favouriteSelect = actionForm?.querySelector('select[name="favourite_id"]');
            if (favouriteSelect instanceof HTMLSelectElement && !favouriteSelect.value) {
                event.preventDefault();
                favouriteSelect.reportValidity?.();
                return;
            }

            const listUrlField = actionForm?.querySelector('input[name="list_view_url"]');
            const listUrl = listUrlField instanceof HTMLInputElement ? listUrlField.value : '';
            const root = getObjectListRoot(favouriteApplyTrigger) || findObjectListRootByListUrl(listUrl);
            if (root) {
                setPersistedFilterPanelState(root, true);
            }
        }

        if (
            !trigger.closest('[data-powercrud-filter-favourites-dropdown="true"]')
            && !trigger.closest('[data-powercrud-filter-favourites-floating-panel="true"]')
        ) {
            closeFilterFavouritesDropdowns();
        }
        closeRowActionsMenu();
    });

    document.addEventListener('keydown', event => {
        if (event.key === 'Escape') {
            closeFilterFavouritesDropdowns();
            closeRowActionsMenu();
        }
    });

    document.addEventListener('scroll', () => {
        closeRowActionsMenu();
    }, true);

    document.addEventListener('click', event => {
        const target = asElement(event.target);
        if (!target || !target.matches('[data-powercrud-row-select="true"]')) {
            return;
        }
        const root = getObjectListRoot(target);
        if (event.shiftKey && hasShiftSelectionAnchor(root, target)) {
            clearDocumentSelection();
            target.dataset.powercrudShiftRange = 'true';
            target.dataset.powercrudSkipSelectionRequest = 'true';
        }
    }, true);

    document.addEventListener('mousedown', event => {
        const target = asElement(event.target);
        if (!target || !target.matches('[data-powercrud-row-select="true"]')) {
            return;
        }
        const root = getObjectListRoot(target);
        if (event.shiftKey && hasShiftSelectionAnchor(root, target)) {
            setRangeSelectionSuppressed(true);
            clearDocumentSelection();
        }
    }, true);

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
            handleRowSelectionChange(target, event);
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

        if (target.matches('[data-powercrud-favourite-select="true"]')) {
            const toolbar = getFilterFavouritesToolbarFromElement(target);
            const root = toolbar ? getObjectListRoot(toolbar) : null;
            if (!root || !(toolbar instanceof Element)) {
                return;
            }
            syncFavouriteToolbarState(toolbar);
            const activePanel = getFilterFavouritesPanelFromElement(target);
            if (activePanel instanceof Element) {
                syncFavouritePanelState(activePanel, toolbar);
            }
            if (!target.value) {
                syncFilterFavouritesSelection(root);
                return;
            }

            const selectedOption = getSelectedFavouriteOption(target);
            if (!(selectedOption instanceof HTMLOptionElement)) {
                return;
            }

            const visibleFilterNames = getFavouriteVisibleFilterNames(selectedOption);
            setStoredOptionalFilterNames(root, visibleFilterNames);
            setPersistedOptionalFilterNames(root, visibleFilterNames);
            setPendingSelectedFilterFavouriteId(root, toolbar, target.value);
            setPersistedFilterPanelState(root, true);
            closeFilterFavouritesDropdowns();
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
        if (form.matches('[data-powercrud-form="object"], [data-powercrud-form="bulk"]')) {
            startFormSpinner(form);
            if (form.matches('[data-powercrud-form="bulk"]')) {
                setBulkActionButtonsDisabled(form, true);
            }
        }
    }, true);

    document.addEventListener('htmx:beforeRequest', event => {
        const target = event.detail && event.detail.elt;
        if (isShellContentNavigationTrigger(target)) {
            clearAllPendingFilterFavouriteSelections();
        }
        if (target && target.matches && target.matches('[data-powercrud-row-select="true"]')) {
            if (target.dataset.powercrudSkipSelectionRequest === 'true') {
                delete target.dataset.powercrudSkipSelectionRequest;
                event.preventDefault();
                return;
            }
        }
        if (target && target.matches && target.matches('[data-powercrud-bulk-delete-submit]')) {
            startButtonSpinner(target);
            setBulkActionButtonsDisabled(target, true);
        }

        if (target && target.closest) {
            const root = getObjectListRoot(target);
            const favouritesToolbar = getFilterFavouritesToolbarFromElement(target)
                || (root ? getFilterFavouritesContainer(root) : null);
            const effectiveRoot = root || (favouritesToolbar instanceof Element
                ? getObjectListRoot(favouritesToolbar)
                : null);
            if (effectiveRoot && favouritesToolbar instanceof Element) {
                const favouriteSelect = getFilterFavouritesSelect(favouritesToolbar);
                const selectedFavouriteId = favouriteSelect?.value
                    || getServerSelectedFilterFavouriteId(favouritesToolbar);
                setPendingSelectedFilterFavouriteId(
                    effectiveRoot,
                    favouritesToolbar,
                    selectedFavouriteId,
                );
            }

            if (favouritesToolbar instanceof Element) {
                syncFavouriteToolbarState(favouritesToolbar);
                const activePanel = getFilterFavouritesPanelFromElement(target);
                if (activePanel instanceof Element) {
                    syncFavouritePanelState(activePanel, favouritesToolbar);
                }

                const requiresSelectedFavourite = (
                    target.matches('[data-powercrud-favourite-manage-action="true"]')
                    || Boolean(target.closest('[data-powercrud-favourite-manage-action="true"]'))
                );
                if (requiresSelectedFavourite) {
                    const favouriteSelect = getFilterFavouritesSelect(favouritesToolbar);
                    if (!favouriteSelect || !favouriteSelect.value) {
                        event.preventDefault();
                        return;
                    }
                }

                const isFavouriteSelectRequest = (
                    target.matches('[data-powercrud-favourite-select="true"]')
                    || Boolean(target.closest('[data-powercrud-favourite-select="true"]'))
                );
                if (isFavouriteSelectRequest) {
                    const favouriteSelect = target.matches('[data-powercrud-favourite-select="true"]')
                        ? target
                        : target.closest('[data-powercrud-favourite-select="true"]');
                    if (!favouriteSelect || !favouriteSelect.value) {
                        event.preventDefault();
                        return;
                    }
                }
            }
        }
    });

    document.addEventListener('htmx:configRequest', event => {
        const target = event.detail && event.detail.elt;
        if (!(target instanceof Element) || !target.closest) {
            return;
        }

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
    });

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

    document.body.addEventListener('powercrud:favourite-saved', event => {
        const favouriteId = String(
            event?.detail?.favouriteId
            || event?.detail?.value?.favouriteId
            || ''
        ).trim();
        getAffectedObjectListRoots(document).forEach(root => {
            const toolbar = getFilterFavouritesContainer(root);
            if (!(toolbar instanceof Element)) {
                return;
            }
            setPendingSelectedFilterFavouriteId(root, toolbar, favouriteId);
        });
        global.setTimeout(() => {
            closeFilterFavouritesDropdowns();
        }, 0);
    });

    document.body.addEventListener('powercrud:favourite-updated', event => {
        const favouriteId = String(
            event?.detail?.favouriteId
            || event?.detail?.value?.favouriteId
            || ''
        ).trim();
        getAffectedObjectListRoots(document).forEach(root => {
            const toolbar = getFilterFavouritesContainer(root);
            if (!(toolbar instanceof Element)) {
                return;
            }
            setPendingSelectedFilterFavouriteId(root, toolbar, favouriteId);
        });
        global.setTimeout(() => {
            closeFilterFavouritesDropdowns();
        }, 0);
    });

    document.body.addEventListener('powercrud:favourite-deleted', () => {
        getAffectedObjectListRoots(document).forEach(root => {
            const toolbar = getFilterFavouritesContainer(root);
            if (!(toolbar instanceof Element)) {
                return;
            }
            setPendingSelectedFilterFavouriteId(root, toolbar, '');
        });
        global.setTimeout(() => {
            closeFilterFavouritesDropdowns();
        }, 0);
    });

    document.body.addEventListener('refreshTable', event => {
        const eventTarget = asElement(event.target);
        const root = getObjectListRoot(eventTarget) || getAffectedObjectListRoots(document)[0];
        const payload = event.detail && event.detail.value ? event.detail.value : (event.detail || {});
        if (root) {
            refreshTable(root, { resetPage: payload.reset_page === true });
        }
    });

    document.addEventListener('htmx:beforeSwap', event => {
        getHtmxEventRoots(event).forEach(root => {
            destroyPowercrudSearchableSelects(root);
            destroyPowercrudTooltips(root);
        });
        closeRowActionsMenu();

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
        bootstrapObjectLists(document);
        schedulePowercrudTooltipRefresh(document, 50);

        const target = asElement(event.target);
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
        bootstrapObjectLists(document);
        schedulePowercrudTooltipRefresh(document, 50);
    });

    document.addEventListener('htmx:beforeRequest', event => {
        const target = event.detail && event.detail.elt;
        if (target && target.matches && target.matches('[data-inline-save]')) {
            const row = target.closest(INLINE_ROW_SELECTOR);
            syncTomSelectValues(row);
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
        if (target && target.matches && target.matches('[data-powercrud-form="object"], [data-powercrud-form="bulk"]')) {
            stopFormSpinner(target);
            if (target.matches('[data-powercrud-form="bulk"]')) {
                setBulkActionButtonsDisabled(target, false);
            }
        }
        if (target && target.matches && target.matches('[data-powercrud-bulk-delete-submit]')) {
            stopButtonSpinner(target);
            setBulkActionButtonsDisabled(target, false);
        }
        if (target && target.matches && target.matches('[data-inline-save]')) {
            const row = target.closest(INLINE_ROW_SELECTOR);
            toggleInlineSaving(row, false);
        }
    });

    document.addEventListener('htmx:responseError', event => {
        const target = event.detail && event.detail.elt;
        if (target && target.matches && target.matches('[data-powercrud-form="object"], [data-powercrud-form="bulk"]')) {
            stopFormSpinner(target);
            if (target.matches('[data-powercrud-form="bulk"]')) {
                setBulkActionButtonsDisabled(target, false);
            }
        }
        if (target && target.matches && target.matches('[data-powercrud-bulk-delete-submit]')) {
            stopButtonSpinner(target);
            setBulkActionButtonsDisabled(target, false);
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
        closeRowActionsMenu();
        if (tooltipResizeTimer) {
            clearTimeout(tooltipResizeTimer);
        }
        tooltipResizeTimer = setTimeout(() => initPowercrudTooltips(document), 100);
    });
})(window);
