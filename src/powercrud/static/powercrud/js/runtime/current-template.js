import {
    DEFAULT_MODAL_BOX_CLASSES,
    LIST_TOOLBAR_SELECTOR,
    PAGINATION_SELECTOR,
    TOOLTIP_TRIGGER_SELECTOR,
    VIEW_HELP_SELECTOR,
} from './selectors.js';
import {
    getAffectedObjectListRoots,
    getObjectListRoot,
    isElementVisible,
    queryAllWithSelf,
} from './dom.js';

// Current-template adapter: this module owns today's DOM geometry and
// presentation-library glue. Shared PowerCRUD semantics should stay in the
// feature runtimes that call these callbacks.
export function createCurrentTemplateRuntime(context) {
    const {
        global,
        documentObject,
        warnMissingDependency,
        getHtmxInstance,
    } = context;

    const FORM_SPINNER_STATE = new WeakMap();
    const BUTTON_SPINNER_STATE = new WeakMap();
    let tooltipResizeTimer = null;
    let activeRowActionsMenu = null;
    let activeRowActionsTrigger = null;

    function cleanupDuplicatePowercrudModals() {
        // HTMX swaps can leave an old dialog and a new dialog with the same id;
        // keep the open instance, otherwise keep the newest rendered instance.
        const modalsById = new Map();
        documentObject.querySelectorAll('[data-powercrud-modal]').forEach(modal => {
            if (!(modal instanceof HTMLDialogElement) || !modal.id) {
                return;
            }

            const existingModal = modalsById.get(modal.id);
            if (!(existingModal instanceof HTMLDialogElement)) {
                modalsById.set(modal.id, modal);
                return;
            }

            if (existingModal.open && !modal.open) {
                modal.remove();
                return;
            }

            if (!existingModal.open && modal.open) {
                existingModal.remove();
                modalsById.set(modal.id, modal);
                return;
            }

            existingModal.remove();
            modalsById.set(modal.id, modal);
        });
    }

    function applyPowercrudModalClasses(trigger) {
        if (!(trigger instanceof Element)) {
            return;
        }
        const modalTrigger = trigger.closest('[data-powercrud-modal-trigger="true"]');
        if (!(modalTrigger instanceof Element)) {
            return;
        }
        cleanupDuplicatePowercrudModals();
        const root = getObjectListRoot(modalTrigger) || documentObject;
        const modal = root.querySelector('[data-powercrud-modal]') || documentObject.querySelector('[data-powercrud-modal]');
        const modalBox = modal?.querySelector('[data-powercrud-modal-box]');
        if (!(modalBox instanceof HTMLElement)) {
            return;
        }
        const defaultClasses = modalBox.dataset.powercrudDefaultModalBoxClasses || DEFAULT_MODAL_BOX_CLASSES;
        const requestedClasses = modalTrigger.getAttribute('data-powercrud-modal-box-classes');
        modalBox.className = requestedClasses || defaultClasses;
    }

    function closePowercrudModals() {
        documentObject.querySelectorAll('[data-powercrud-modal]').forEach(modal => {
            if (modal instanceof HTMLDialogElement && typeof modal.close === 'function') {
                modal.close();
            }
        });
        cleanupDuplicatePowercrudModals();
    }

    function getTippyCtor() {
        const ctor = global.tippy;
        if (typeof ctor !== 'function') {
            warnMissingDependency('tippy', 'window.tippy. Load Tippy.js before powercrud/js/powercrud.js');
            return null;
        }
        return ctor;
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

    function destroyPowercrudTooltips(root = documentObject) {
        queryAllWithSelf(root, TOOLTIP_TRIGGER_SELECTOR).forEach(trigger => {
            if (trigger._tippy) {
                trigger._tippy.destroy();
            }
        });
    }

    function hidePowercrudTooltips(root = documentObject) {
        queryAllWithSelf(root, TOOLTIP_TRIGGER_SELECTOR).forEach(trigger => {
            if (trigger._tippy) {
                trigger._tippy.hide();
            }
        });
    }

    function initPowercrudTooltips(root = documentObject) {
        const tippyCtor = getTippyCtor();
        if (!tippyCtor) {
            return;
        }

        // Tippy instances are presentation-only and are recreated after swaps
        // because the same semantic tooltip attributes can land on new nodes.
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

    function schedulePowercrudTooltipRefresh(root = documentObject, delay = 0) {
        global.setTimeout(() => {
            initPowercrudTooltips(root);
        }, delay);
    }

    function schedulePowercrudTooltipResizeRefresh(root = documentObject, delay = 100) {
        if (tooltipResizeTimer) {
            global.clearTimeout(tooltipResizeTimer);
        }
        tooltipResizeTimer = global.setTimeout(() => initPowercrudTooltips(root), delay);
    }

    function syncListToolbarWidth(root) {
        if (!(root instanceof Element)) {
            return;
        }
        const toolbar = root.querySelector(LIST_TOOLBAR_SELECTOR);
        const filterCollapse = root.querySelector('#filterCollapse');
        const pagination = root.querySelector(PAGINATION_SELECTOR);
        const viewHelp = root.querySelector(VIEW_HELP_SELECTOR);
        const table = root.querySelector('#filtered_results table');
        if (!(toolbar instanceof HTMLElement) || !(table instanceof HTMLElement)) {
            return;
        }

        // The current template visually aligns the toolbar and filter panel to
        // the rendered table instead of letting those controls span the page.
        const tableWidth = Math.ceil(table.getBoundingClientRect().width || table.offsetWidth);
        if (!tableWidth) {
            toolbar.style.width = '';
            toolbar.style.maxWidth = '';
            if (filterCollapse instanceof HTMLElement) {
                filterCollapse.style.width = '';
                filterCollapse.style.maxWidth = '';
            }
            if (pagination instanceof HTMLElement) {
                pagination.style.width = '';
                pagination.style.maxWidth = '';
            }
            if (viewHelp instanceof HTMLElement) {
                viewHelp.style.width = '';
                viewHelp.style.maxWidth = '';
            }
            return;
        }
        toolbar.style.width = `${tableWidth}px`;
        toolbar.style.maxWidth = '100%';
        if (filterCollapse instanceof HTMLElement) {
            filterCollapse.style.width = `${tableWidth}px`;
            filterCollapse.style.maxWidth = '100%';
        }
        if (pagination instanceof HTMLElement) {
            pagination.style.width = `${tableWidth}px`;
            pagination.style.maxWidth = '100%';
        }
        if (viewHelp instanceof HTMLElement) {
            const minWidth = viewHelp.dataset.powercrudViewHelpMinWidth || '40rem';
            viewHelp.style.width = `min(100%, max(${minWidth}, ${tableWidth}px))`;
            viewHelp.style.maxWidth = '100%';
        }

        global.requestAnimationFrame(() => {
            const actionControls = toolbar.querySelector('[data-powercrud-action-controls]');
            const viewControls = toolbar.querySelector('[data-powercrud-view-controls]');
            if (!(actionControls instanceof HTMLElement) || !(viewControls instanceof HTMLElement)) {
                toolbar.removeAttribute('data-powercrud-toolbar-wrapped');
                return;
            }

            const actionTop = actionControls.getBoundingClientRect().top;
            const viewTop = viewControls.getBoundingClientRect().top;
            if (viewTop > actionTop + 2) {
                toolbar.setAttribute('data-powercrud-toolbar-wrapped', 'true');
                return;
            }
            toolbar.removeAttribute('data-powercrud-toolbar-wrapped');
        });
    }

    function syncListToolbarWidths(scope = documentObject) {
        getAffectedObjectListRoots(scope).forEach(syncListToolbarWidth);
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

        // Row actions render from hidden in-row markup but execute from a
        // body-level clone so the menu can escape table overflow clipping.
        const menuElement = template.firstElementChild?.cloneNode(true);
        if (!(menuElement instanceof HTMLElement)) {
            return;
        }

        menuElement.dataset.powercrudRowActionsFloatingPanel = 'true';
        menuElement.style.position = 'fixed';
        menuElement.style.visibility = 'hidden';
        menuElement.style.pointerEvents = 'none';

        documentObject.body.appendChild(menuElement);

        const htmx = getHtmxInstance();
        if (htmx?.process) {
            htmx.process(menuElement);
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

    function startFormSpinner(form) {
        if (!form || FORM_SPINNER_STATE.has(form)) {
            return;
        }
        const saveBtn = form.querySelector('[data-form-save]');
        if (!saveBtn) {
            return;
        }
        // Spinner markup/classes are presentation-library details; the stored
        // HTML lets request handlers restore the exact original button.
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

    function applyListColumnOptionVisualState(option, isLastChecked) {
        if (!(option instanceof HTMLElement)) {
            return;
        }
        option.classList.toggle('cursor-not-allowed', isLastChecked);
        option.classList.toggle('opacity-70', isLastChecked);
    }

    function syncListColumnChooserPlacement(container) {
        if (!(container instanceof HTMLDetailsElement) || !container.open) {
            return;
        }

        const panel = container.querySelector('[data-powercrud-list-columns-panel="true"]');
        const trigger = container.querySelector('[data-powercrud-list-columns-trigger="true"]');
        if (!(panel instanceof HTMLElement) || !(trigger instanceof HTMLElement)) {
            return;
        }

        // Placement is current-template geometry. Core list-column state only
        // decides which columns are visible.
        container.dataset.powercrudListColumnsPlacement = 'end';
        global.requestAnimationFrame(() => {
            if (!container.open) {
                return;
            }
            const triggerRect = trigger.getBoundingClientRect();
            const panelWidth = Math.min(
                panel.offsetWidth,
                documentObject.documentElement.clientWidth - 16,
            );
            const margin = 8;
            const endLeft = triggerRect.right - panelWidth;
            const shouldOpenStart = endLeft < margin;
            container.dataset.powercrudListColumnsPlacement = shouldOpenStart ? 'start' : 'end';
        });
    }

    function clearListColumnChooserPlacement(container) {
        if (container instanceof HTMLElement) {
            delete container.dataset.powercrudListColumnsPlacement;
        }
    }

    function syncSelectionAwareButtonVisualState(button, options = {}) {
        if (!(button instanceof HTMLElement)) {
            return;
        }
        const { disable = false, reason = '' } = options;

        // Selection rules live in bulk-actions; this adapter only renders the
        // disabled visual treatment and optional tooltip reason.
        button.classList.toggle('btn-disabled', disable);
        button.classList.toggle('opacity-50', disable);
        button.classList.toggle('pointer-events-none', disable);

        if (disable) {
            button.setAttribute('aria-disabled', 'true');
            if (reason) {
                button.setAttribute('data-tippy-content', reason);
                button.setAttribute('data-powercrud-tooltip', 'semantic');
            }
            return;
        }

        button.removeAttribute('aria-disabled');
        if (button.dataset.powercrudSelectionMinReason) {
            button.removeAttribute('data-tippy-content');
            button.removeAttribute('data-powercrud-tooltip');
        }
    }

    function syncFilterFavouritesTriggerPresentation(options = {}) {
        const {
            toolbar,
            trigger,
            triggerLabel,
            selectedLabel = '',
            defaultLabel = 'Favourites',
            isDirty = false,
        } = options;

        if (triggerLabel instanceof Element) {
            const displayLabel = selectedLabel && isDirty
                ? `${selectedLabel} (edited)`
                : selectedLabel;
            triggerLabel.textContent = displayLabel || defaultLabel;
        }

        if (trigger instanceof HTMLElement) {
            if (trigger._tippy) {
                trigger._tippy.destroy();
            }

            if (selectedLabel) {
                const displayLabel = isDirty ? `${selectedLabel} (edited)` : selectedLabel;
                trigger.dataset.powercrudFilterFavouritesSelected = 'true';
                trigger.dataset.powercrudFilterFavouritesDirty = isDirty ? 'true' : 'false';
                trigger.setAttribute('aria-label', `Saved favourite: ${displayLabel}`);
                trigger.setAttribute('data-powercrud-tooltip', 'semantic');
                trigger.setAttribute('data-tippy-content', displayLabel);
            } else {
                trigger.dataset.powercrudFilterFavouritesSelected = 'false';
                trigger.dataset.powercrudFilterFavouritesDirty = 'false';
                trigger.setAttribute('aria-label', defaultLabel);
                trigger.setAttribute('data-powercrud-tooltip', 'semantic');
                trigger.setAttribute('data-tippy-content', defaultLabel);
            }

            const outlineIcon = trigger.querySelector('[data-powercrud-filter-favourites-icon-outline="true"]');
            const filledIcon = trigger.querySelector('[data-powercrud-filter-favourites-icon-filled="true"]');
            if (outlineIcon instanceof HTMLElement) {
                outlineIcon.classList.toggle('hidden', Boolean(selectedLabel));
            }
            if (filledIcon instanceof HTMLElement) {
                filledIcon.classList.toggle('hidden', !selectedLabel);
                filledIcon.classList.toggle('text-primary', Boolean(selectedLabel) && !isDirty);
                filledIcon.classList.toggle('text-warning', Boolean(selectedLabel) && isDirty);
            }
        }

        if (selectedLabel && toolbar instanceof Element) {
            schedulePowercrudTooltipRefresh(toolbar);
        }
    }

    function setFilterFavouritesDropdownOpen(toolbar, isOpen) {
        if (!(toolbar instanceof Element)) {
            return;
        }
        toolbar.classList.toggle('dropdown-open', Boolean(isOpen));
    }

    function prepareFilterFavouritesFloatingPanel(panelShell, toolbar) {
        if (!(panelShell instanceof HTMLElement)) {
            return false;
        }
        // Favourites state remains in filter-favourites; this body-level panel
        // is current-template presentation to avoid toolbar overflow clipping.
        panelShell.dataset.powercrudFilterFavouritesFloatingPanel = 'true';
        panelShell.dataset.powercrudToolbarDomId = toolbar?.id || '';
        panelShell.style.position = 'fixed';
        panelShell.style.visibility = 'hidden';
        panelShell.style.pointerEvents = 'none';
        return true;
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

    function showPreparedFloatingPanel(panelShell) {
        if (!(panelShell instanceof HTMLElement)) {
            return;
        }
        panelShell.style.visibility = '';
        panelShell.style.pointerEvents = '';
    }

    function toggleInlineSaveSpinner(row, isSaving) {
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

    return {
        applyListColumnOptionVisualState,
        applyPowercrudModalClasses,
        cleanupDuplicatePowercrudModals,
        clearListColumnChooserPlacement,
        closePowercrudModals,
        closeRowActionsMenu,
        destroyPowercrudTooltips,
        hidePowercrudTooltips,
        initPowercrudTooltips,
        positionFilterFavouritesPanel,
        prepareFilterFavouritesFloatingPanel,
        schedulePowercrudTooltipRefresh,
        schedulePowercrudTooltipResizeRefresh,
        setFilterFavouritesDropdownOpen,
        showPreparedFloatingPanel,
        startButtonSpinner,
        startFormSpinner,
        stopButtonSpinner,
        stopFormSpinner,
        syncFilterFavouritesTriggerPresentation,
        syncListColumnChooserPlacement,
        syncListToolbarWidth,
        syncListToolbarWidths,
        syncSelectionAwareButtonVisualState,
        toggleInlineSaveSpinner,
        toggleRowActionsMenu,
    };
}
