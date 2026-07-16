import {
    LIST_TOOLBAR_SELECTOR,
    PAGINATION_SELECTOR,
    VIEW_HELP_SELECTOR,
} from './selectors.js';
import {
    getAffectedObjectListRoots,
    getObjectListRoot,
} from './dom.js';

// Current-template adapter: this module owns today's DOM geometry and
// presentation-library glue. Shared PowerCRUD semantics should stay in the
// feature runtimes that call these callbacks.
export function createCurrentTemplateRuntime(context) {
    const {
        global,
        documentObject,
        getHtmxInstance,
        initPowercrudTooltips,
        requestModalCloseListRefresh,
        applyPowercrudModalTriggerClasses,
        cleanupDuplicatePowercrudModals,
        closeAllPowercrudModals,
        setRowActionLinkDisabled,
        startButtonSpinner,
        stopButtonSpinner,
        cloneRowActionFloatingMenu,
        positionRowActionFloatingMenu,
        prepareRowActionFloatingMenu,
        showRowActionFloatingMenu,
    } = context;

    const MODAL_CLOSE_REFRESH_ROOTS = new WeakMap();
    const MODAL_CLOSE_REFRESH_LISTENERS = new WeakSet();
    const ROW_ACTION_STATE_REQUESTS = new WeakMap();
    const ROW_ACTION_STATE_UNAVAILABLE_MESSAGE = 'Unable to validate current availability.';
    let activeRowActionsMenu = null;
    let activeRowActionsTrigger = null;

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
        if (!applyPowercrudModalTriggerClasses(modalTrigger, modal)) {
            return;
        }
        armModalCloseListRefresh(modalTrigger, modal, root);
    }

    function getModalCloseRefreshRoot(root) {
        if (root instanceof Element && root !== documentObject) {
            return root;
        }
        return getObjectListRoot(activeRowActionsTrigger) || null;
    }

    function armModalCloseListRefresh(modalTrigger, modal, root) {
        if (
            !(modal instanceof HTMLDialogElement)
            || modalTrigger.getAttribute('data-powercrud-refresh-list-on-modal-close') !== 'true'
        ) {
            return;
        }

        const refreshRoot = getModalCloseRefreshRoot(root);
        if (!(refreshRoot instanceof Element)) {
            return;
        }

        MODAL_CLOSE_REFRESH_ROOTS.set(modal, refreshRoot);
        if (MODAL_CLOSE_REFRESH_LISTENERS.has(modal)) {
            return;
        }

        MODAL_CLOSE_REFRESH_LISTENERS.add(modal);
        modal.addEventListener('close', () => {
            const pendingRoot = MODAL_CLOSE_REFRESH_ROOTS.get(modal);
            MODAL_CLOSE_REFRESH_ROOTS.delete(modal);
            if (!(pendingRoot instanceof Element) || !pendingRoot.isConnected) {
                return;
            }
            requestModalCloseListRefresh?.(pendingRoot);
        });
    }

    function closePowercrudModals() {
        closeAllPowercrudModals(modal => {
            MODAL_CLOSE_REFRESH_ROOTS.delete(modal);
        });
    }

    function handleModalTriggerBeforeRequest(trigger) {
        applyPowercrudModalClasses(trigger);
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

    function getLazyRowActionLinks(menuElement) {
        if (!(menuElement instanceof HTMLElement)) {
            return [];
        }
        return Array.from(
            menuElement.querySelectorAll('[data-powercrud-row-action-state-mode="lazy"]'),
        ).filter(link => link instanceof HTMLElement);
    }

    function isLazyHiddenRowActionLink(link) {
        return (
            link instanceof HTMLElement
            && link.dataset.powercrudRowActionHiddenMode === 'lazy'
        );
    }

    function removeRowActionLink(link) {
        if (!(link instanceof HTMLElement)) {
            return;
        }
        const listItem = link.closest('li');
        if (listItem instanceof HTMLElement) {
            listItem.remove();
        } else {
            link.remove();
        }
    }

    function hasRowActionMenuItems(menuElement) {
        return (
            menuElement instanceof HTMLElement
            && Boolean(menuElement.querySelector('li'))
        );
    }

    function disableUnresolvedLazyRowActions(menuElement) {
        getLazyRowActionLinks(menuElement).forEach(link => {
            if (isLazyHiddenRowActionLink(link)) {
                removeRowActionLink(link);
                return;
            }
            setRowActionLinkDisabled(link, true, ROW_ACTION_STATE_UNAVAILABLE_MESSAGE);
        });
    }

    function applyLazyRowActionStates(menuElement, payload) {
        const actions = payload?.actions && typeof payload.actions === 'object'
            ? payload.actions
            : {};
        getLazyRowActionLinks(menuElement).forEach(link => {
            const actionIndex = link.dataset.powercrudRowActionIndex || '';
            const actionState = actions[actionIndex];
            if (!actionState || typeof actionState !== 'object') {
                if (isLazyHiddenRowActionLink(link)) {
                    removeRowActionLink(link);
                    return;
                }
                setRowActionLinkDisabled(link, true, ROW_ACTION_STATE_UNAVAILABLE_MESSAGE);
                return;
            }
            if (actionState.hidden === true) {
                removeRowActionLink(link);
                return;
            }
            setRowActionLinkDisabled(
                link,
                actionState.disabled === true,
                actionState.reason || '',
            );
        });
    }

    async function hydrateLazyRowActionStates(trigger, menuElement) {
        if (!getLazyRowActionLinks(menuElement).length) {
            return;
        }

        const stateUrl = trigger.dataset.powercrudRowActionStatesUrl || '';
        if (!stateUrl) {
            disableUnresolvedLazyRowActions(menuElement);
            return;
        }

        let request = ROW_ACTION_STATE_REQUESTS.get(trigger);
        if (!request) {
            request = global.fetch(stateUrl, {
                method: 'GET',
                credentials: 'same-origin',
                headers: {
                    Accept: 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                },
            }).then(response => {
                if (!response.ok) {
                    throw new Error(`Lazy row-action state request failed with ${response.status}`);
                }
                return response.json();
            }).finally(() => {
                ROW_ACTION_STATE_REQUESTS.delete(trigger);
            });
            ROW_ACTION_STATE_REQUESTS.set(trigger, request);
        }

        try {
            applyLazyRowActionStates(menuElement, await request);
        } catch {
            disableUnresolvedLazyRowActions(menuElement);
        }
    }

    async function openRowActionsMenu(trigger) {
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
        const menuElement = cloneRowActionFloatingMenu?.(template);
        if (!(menuElement instanceof HTMLElement)) {
            return;
        }

        const hasLazyRowActionState = getLazyRowActionLinks(menuElement).length > 0;
        if (hasLazyRowActionState) {
            trigger.setAttribute('aria-busy', 'true');
            startButtonSpinner(trigger);
            await hydrateLazyRowActionStates(trigger, menuElement);
            stopButtonSpinner(trigger);
            trigger.removeAttribute('aria-busy');
            if (!trigger.isConnected) {
                return;
            }
            if (!hasRowActionMenuItems(menuElement)) {
                trigger.hidden = true;
                trigger.setAttribute('aria-expanded', 'false');
                return;
            }
        }

        menuElement.dataset.powercrudRowActionsFloatingPanel = 'true';
        prepareRowActionFloatingMenu?.(menuElement);

        documentObject.body.appendChild(menuElement);

        const htmx = getHtmxInstance();
        if (htmx?.process) {
            htmx.process(menuElement);
        }
        initPowercrudTooltips(menuElement);

        positionRowActionFloatingMenu?.(menuElement, trigger);
        showRowActionFloatingMenu?.(menuElement);

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

    return {
        applyPowercrudModalClasses,
        cleanupDuplicatePowercrudModals,
        closePowercrudModals,
        closeRowActionsMenu,
        handleModalTriggerBeforeRequest,
        syncListToolbarWidth,
        syncListToolbarWidths,
        toggleRowActionsMenu,
    };
}
