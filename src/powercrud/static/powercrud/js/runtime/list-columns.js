import { queryAllWithSelf } from './dom.js';
import {
    LIST_COLUMNS_SELECTOR,
    LIST_COLUMN_CHECKBOX_SELECTOR,
} from './selectors.js';

export function createListColumnsRuntime(context) {
    const {
        global,
        documentObject,
        getObjectListRoot,
        getHtmxInstance,
        initPowercrudTooltips,
        applyListColumnOptionVisualState,
        clearListColumnChooserPlacement,
        positionListColumnChooserPanel,
        prepareListColumnChooserFloatingPanel,
        showPreparedFloatingPanel,
        syncListColumnChooserPlacement,
    } = context;

    const LIST_COLUMNS_FLOATING_SELECTOR = '[data-powercrud-list-columns-floating-panel="true"]';
    const LIST_COLUMNS_TEMPLATE_SELECTOR = '[data-powercrud-list-columns-template="true"]';
    const LIST_COLUMNS_TRIGGER_SELECTOR = '[data-powercrud-list-columns-trigger="true"]';

    let nextChooserId = 0;
    let activePanel = null;
    let activeContainer = null;
    let activeTrigger = null;

    function ensureListColumnContainerId(container) {
        if (!(container instanceof HTMLElement)) {
            return '';
        }
        if (!container.id) {
            nextChooserId += 1;
            container.id = `powercrud-list-columns-${nextChooserId}`;
        }
        return container.id;
    }

    function getListColumnContainerFromElement(element) {
        if (!(element instanceof Element)) {
            return null;
        }

        const container = element.closest(LIST_COLUMNS_SELECTOR);
        if (container instanceof HTMLDetailsElement) {
            return container;
        }

        const floatingPanel = element.closest(LIST_COLUMNS_FLOATING_SELECTOR);
        if (!(floatingPanel instanceof HTMLElement)) {
            return null;
        }

        const containerId = floatingPanel.dataset.powercrudListColumnsDomId || '';
        const sourceContainer = containerId ? documentObject.getElementById(containerId) : null;
        return sourceContainer instanceof HTMLDetailsElement ? sourceContainer : null;
    }

    function getListColumnRootFromElement(element) {
        const sourceContainer = getListColumnContainerFromElement(element);
        if (sourceContainer instanceof Element) {
            const sourceRoot = getObjectListRoot?.(sourceContainer);
            if (sourceRoot instanceof Element) {
                return sourceRoot;
            }
        }

        return getObjectListRoot?.(element) || null;
    }

    function getListColumnCheckboxes(container) {
        if (!(container instanceof Element)) {
            return [];
        }
        return Array.from(container.querySelectorAll(LIST_COLUMN_CHECKBOX_SELECTOR))
            .filter(checkbox => checkbox instanceof HTMLInputElement);
    }

    function syncListColumnChooser(container) {
        if (!(container instanceof Element)) {
            return;
        }

        const checkboxes = getListColumnCheckboxes(container);
        const checkedBoxes = checkboxes.filter(checkbox => checkbox.checked);
        checkboxes.forEach(checkbox => {
            // Preserve at least one visible column; the adapter callback only
            // renders the disabled visual state for the current template.
            const isLastChecked = checkedBoxes.length === 1 && checkbox.checked;
            checkbox.setAttribute('aria-disabled', isLastChecked ? 'true' : 'false');
            checkbox.dataset.powercrudLastVisibleColumn = isLastChecked ? 'true' : 'false';
            const option = checkbox.closest('[data-powercrud-list-column-option="true"]');
            applyListColumnOptionVisualState?.(option, isLastChecked);
        });
    }

    function getListColumnTrigger(container) {
        if (!(container instanceof Element)) {
            return null;
        }
        const trigger = container.querySelector(LIST_COLUMNS_TRIGGER_SELECTOR);
        return trigger instanceof HTMLElement ? trigger : null;
    }

    function closeActiveListColumnChooser(focusTrigger = false) {
        if (!(activePanel instanceof HTMLElement)) {
            activePanel = null;
            activeContainer = null;
            activeTrigger = null;
            return;
        }

        resetListColumnChooserDraft(activePanel);
        if (activePanel.parentNode) {
            activePanel.parentNode.removeChild(activePanel);
        }

        if (activeContainer instanceof HTMLDetailsElement) {
            activeContainer.open = false;
            clearListColumnChooserPlacement?.(activeContainer);
        }
        if (activeTrigger instanceof HTMLElement) {
            activeTrigger.setAttribute('aria-expanded', 'false');
            if (focusTrigger) {
                activeTrigger.focus();
            }
        }

        activePanel = null;
        activeContainer = null;
        activeTrigger = null;
    }

    function syncListColumnChoosers(root = documentObject) {
        queryAllWithSelf(root, LIST_COLUMNS_SELECTOR).forEach(container => {
            syncListColumnChooser(container);
            syncListColumnChooserPlacement(container);
        });
    }

    function resetListColumnChooserDraft(container) {
        if (!(container instanceof Element)) {
            return;
        }

        getListColumnCheckboxes(container).forEach(checkbox => {
            checkbox.checked = checkbox.dataset.powercrudInitialChecked === 'true';
        });
        // Closing without save discards the draft and returns to the server
        // rendered initial state for this chooser.
        syncListColumnChooser(container);
    }

    function focusFirstListColumnCheckbox(container) {
        const firstCheckbox = getListColumnCheckboxes(container)[0];
        if (firstCheckbox instanceof HTMLInputElement) {
            global.setTimeout(() => firstCheckbox.focus(), 0);
        }
    }

    function openListColumnChooser(container) {
        if (!(container instanceof HTMLDetailsElement)) {
            return;
        }

        const template = container.querySelector(LIST_COLUMNS_TEMPLATE_SELECTOR);
        const trigger = getListColumnTrigger(container);
        if (!(template instanceof HTMLElement) || !(trigger instanceof HTMLElement)) {
            return;
        }

        closeActiveListColumnChooser();

        const panel = template.firstElementChild?.cloneNode(true);
        if (!(panel instanceof HTMLElement)) {
            return;
        }

        ensureListColumnContainerId(container);
        prepareListColumnChooserFloatingPanel?.(panel, container);

        documentObject.body.appendChild(panel);

        const htmx = getHtmxInstance?.();
        if (htmx?.process) {
            htmx.process(panel);
        }
        initPowercrudTooltips?.(panel);
        syncListColumnChooser(panel);
        positionListColumnChooserPanel?.(panel, trigger);
        showPreparedFloatingPanel?.(panel);
        trigger.setAttribute('aria-expanded', 'true');

        activePanel = panel;
        activeContainer = container;
        activeTrigger = trigger;
        focusFirstListColumnCheckbox(panel);
    }

    function closeListColumnChoosers(scope = documentObject, focusTrigger = false) {
        closeActiveListColumnChooser(focusTrigger);
        queryAllWithSelf(scope, LIST_COLUMNS_SELECTOR).forEach(container => {
            if (!(container instanceof HTMLDetailsElement)) {
                return;
            }
            container.open = false;
            resetListColumnChooserDraft(container);
            clearListColumnChooserPlacement?.(container);
            const trigger = getListColumnTrigger(container);
            if (trigger instanceof HTMLElement) {
                trigger.setAttribute('aria-expanded', 'false');
            }
        });
    }

    function getListOptionsForm(root) {
        if (!(root instanceof Element)) {
            return null;
        }
        const form = root.querySelector(`${LIST_COLUMNS_SELECTOR} form`);
        return form instanceof HTMLFormElement ? form : null;
    }

    function getVisibleListColumnNames(root) {
        if (!(root instanceof Element)) {
            return null;
        }
        const chooser = root.querySelector(LIST_COLUMNS_SELECTOR);
        if (!(chooser instanceof Element)) {
            return null;
        }

        return Array.from(new Set(
            getListColumnCheckboxes(chooser)
                .filter(checkbox => checkbox.checked)
                .map(checkbox => String(checkbox.value || '').trim())
                .filter(Boolean)
        ));
    }

    function buildListColumnResetRequest(root, listUrl) {
        const form = getListOptionsForm(root);
        const url = form?.getAttribute('hx-post')
            || form?.getAttribute('action')
            || '';
        if (!(form instanceof HTMLFormElement) || !url) {
            return null;
        }

        const csrfField = form.querySelector('input[name="csrfmiddlewaretoken"]');
        const csrfToken = csrfField instanceof HTMLInputElement ? csrfField.value : '';
        const values = {
            list_columns_action: 'reset',
            list_view_url: listUrl,
        };
        if (csrfToken) {
            values.csrfmiddlewaretoken = csrfToken;
        }
        return { url, values };
    }

    function closeForOutsideClick(trigger) {
        if (!(trigger instanceof Element)) {
            return;
        }
        if (
            trigger.closest(LIST_COLUMNS_SELECTOR)
            || trigger.closest(LIST_COLUMNS_FLOATING_SELECTOR)
        ) {
            return;
        }
        closeListColumnChoosers(documentObject);
    }

    function handleListColumnsToggle(event) {
        const chooser = event.target instanceof Element ? event.target : null;
        if (!(chooser instanceof HTMLDetailsElement) || !chooser.matches(LIST_COLUMNS_SELECTOR)) {
            return false;
        }
        syncListColumnChooser(chooser);
        if (chooser.open) {
            openListColumnChooser(chooser);
            return true;
        }
        if (activeContainer === chooser) {
            closeActiveListColumnChooser();
        } else {
            clearListColumnChooserPlacement?.(chooser);
            resetListColumnChooserDraft(chooser);
            const trigger = getListColumnTrigger(chooser);
            trigger?.setAttribute('aria-expanded', 'false');
        }
        return true;
    }

    function handleListColumnCheckboxChange(target) {
        if (!(target instanceof Element) || !target.matches(LIST_COLUMN_CHECKBOX_SELECTOR)) {
            return false;
        }
        const chooser = getListColumnContainerFromElement(target);
        const chooserSurface = target.closest(LIST_COLUMNS_FLOATING_SELECTOR)
            || target.closest(LIST_COLUMNS_SELECTOR);
        if (chooser instanceof Element && chooserSurface instanceof Element) {
            const checkedBoxes = getListColumnCheckboxes(chooserSurface).filter(checkbox => checkbox.checked);
            if (target instanceof HTMLInputElement && !target.checked && !checkedBoxes.length) {
                target.checked = true;
            }
            syncListColumnChooser(chooserSurface);
        }
        return true;
    }

    function handleListColumnsHtmxBeforeRequest(target) {
        if (!(target instanceof Element)) {
            return false;
        }
        const form = target.matches('form') ? target : target.closest('form');
        if (!(form instanceof HTMLFormElement)) {
            return false;
        }
        if (
            !form.closest(LIST_COLUMNS_SELECTOR)
            && !form.closest(LIST_COLUMNS_FLOATING_SELECTOR)
        ) {
            return false;
        }
        global.setTimeout(() => {
            closeListColumnChoosers(documentObject);
        }, 0);
        return true;
    }

    function isListColumnsForm(element) {
        if (!(element instanceof HTMLFormElement)) {
            return false;
        }
        return Boolean(
            element.closest(LIST_COLUMNS_SELECTOR)
            || element.closest(LIST_COLUMNS_FLOATING_SELECTOR)
        );
    }

    return {
        buildListColumnResetRequest,
        closeForOutsideClick,
        closeListColumnChoosers,
        getListColumnRootFromElement,
        getVisibleListColumnNames,
        handleListColumnsHtmxBeforeRequest,
        handleListColumnCheckboxChange,
        handleListColumnsToggle,
        isListColumnsForm,
        syncListColumnChoosers,
    };
}
