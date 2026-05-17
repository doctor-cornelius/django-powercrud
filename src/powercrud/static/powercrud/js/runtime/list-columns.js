import { queryAllWithSelf } from './dom.js';
import {
    LIST_COLUMNS_SELECTOR,
    LIST_COLUMN_CHECKBOX_SELECTOR,
} from './selectors.js';

export function createListColumnsRuntime(context) {
    const {
        global,
        documentObject,
        applyListColumnOptionVisualState,
        clearListColumnChooserPlacement,
        syncListColumnChooserPlacement,
    } = context;

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

    function closeListColumnChoosers(scope = documentObject, focusTrigger = false) {
        queryAllWithSelf(scope, LIST_COLUMNS_SELECTOR).forEach(container => {
            if (!(container instanceof HTMLDetailsElement) || !container.open) {
                return;
            }
            container.open = false;
            resetListColumnChooserDraft(container);
            if (focusTrigger) {
                const trigger = container.querySelector('[data-powercrud-list-columns-trigger="true"]');
                if (trigger instanceof HTMLElement) {
                    trigger.focus();
                }
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
        if (!trigger.closest(LIST_COLUMNS_SELECTOR)) {
            closeListColumnChoosers(documentObject);
        }
    }

    function handleListColumnsToggle(event) {
        const chooser = event.target instanceof Element ? event.target : null;
        if (!(chooser instanceof HTMLDetailsElement) || !chooser.matches(LIST_COLUMNS_SELECTOR)) {
            return false;
        }
        syncListColumnChooser(chooser);
        if (chooser.open) {
            syncListColumnChooserPlacement(chooser);
            focusFirstListColumnCheckbox(chooser);
            return true;
        }
        clearListColumnChooserPlacement?.(chooser);
        resetListColumnChooserDraft(chooser);
        return true;
    }

    function handleListColumnCheckboxChange(target) {
        if (!(target instanceof Element) || !target.matches(LIST_COLUMN_CHECKBOX_SELECTOR)) {
            return false;
        }
        const chooser = target.closest(LIST_COLUMNS_SELECTOR);
        if (chooser instanceof Element) {
            const checkedBoxes = getListColumnCheckboxes(chooser).filter(checkbox => checkbox.checked);
            if (target instanceof HTMLInputElement && !target.checked && !checkedBoxes.length) {
                target.checked = true;
            }
            syncListColumnChooser(chooser);
        }
        return true;
    }

    return {
        buildListColumnResetRequest,
        closeForOutsideClick,
        closeListColumnChoosers,
        getVisibleListColumnNames,
        handleListColumnCheckboxChange,
        handleListColumnsToggle,
        syncListColumnChoosers,
    };
}
