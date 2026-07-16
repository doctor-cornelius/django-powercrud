/** Adapt shared inline-edit focus and saving feedback to Bootstrap controls. */
import {
    INLINE_FIELD_ERROR_POPOVER_SELECTOR,
    INLINE_FIELD_ERROR_SELECTOR,
} from '../../../../../../../../static/powercrud/js/runtime/selectors.js';
import { queryAllWithSelf } from '../../../../../../../../static/powercrud/js/runtime/dom.js';

export function createBootstrap5InlinePresentationAdapter({ global, documentObject }) {
    function resolveInlineFocusTarget(row, preferredField) {
        if (!(row instanceof Element)) {
            return null;
        }
        const selector = preferredField
            ? `.inline-field-widget[data-inline-field="${preferredField}"]`
            : '.inline-field-widget';
        const widget = row.querySelector(selector);
        const select = widget?.querySelector('select');
        if (select?.tomselect?.control_input instanceof HTMLElement) {
            return select.tomselect.control_input;
        }
        return widget?.querySelector('input:not([type="hidden"]):not([disabled]), select:not([disabled]), textarea:not([disabled])')
            || row.querySelector('[data-inline-save], [data-inline-cancel], .inline-edit-trigger');
    }

    function presentInlineFocus(target, triggerField) {
        target?.focus();
        const widget = target?.closest('.inline-field-widget');
        const select = widget?.querySelector('select');
        if (triggerField && select?.tomselect) {
            global.requestAnimationFrame(() => {
                select.tomselect.focus();
                select.tomselect.open();
            });
        }
    }

    function toggleSaveSpinner(row, isSaving) {
        const button = row?.querySelector('[data-inline-save]');
        if (!(button instanceof HTMLElement)) {
            return;
        }
        if (isSaving && !button.dataset.powercrudOriginalLabel) {
            button.dataset.powercrudOriginalLabel = button.innerHTML;
            button.style.width = `${button.offsetWidth}px`;
            button.disabled = true;
            button.innerHTML = '<span class="spinner-border spinner-border-sm loading-spinner" aria-hidden="true"></span><span class="visually-hidden">Saving</span>';
        } else if (!isSaving && button.dataset.powercrudOriginalLabel) {
            button.disabled = false;
            button.innerHTML = button.dataset.powercrudOriginalLabel;
            button.style.width = '';
            delete button.dataset.powercrudOriginalLabel;
        }
    }

    function getInlineFieldErrorText(widget) {
        if (!(widget instanceof HTMLElement)) return null;
        const control = widget.querySelector('[aria-describedby]');
        const errorId = control?.getAttribute('aria-describedby')?.split(/\s+/).find(id => id.endsWith('_inline_error'));
        const describedError = errorId ? documentObject.getElementById(errorId) : null;
        if (describedError instanceof HTMLElement) return describedError;
        const siblingError = widget.nextElementSibling;
        return siblingError instanceof HTMLElement && siblingError.dataset.inlineErrorText === 'true'
            ? siblingError
            : null;
    }

    function removeFieldErrorPopover(widget) {
        if (!(widget instanceof HTMLElement)) return;
        const errorText = getInlineFieldErrorText(widget);
        if (errorText) {
            errorText.classList.remove('visually-hidden');
            delete errorText.dataset.inlineErrorTextHidden;
        }
        widget._powercrudInlineErrorPopover?.remove();
        delete widget._powercrudInlineErrorPopover;
    }

    function positionFieldErrorPopover(widget, popover) {
        if (!(widget instanceof HTMLElement) || !(popover instanceof HTMLElement)) return;
        const rect = widget.getBoundingClientRect();
        const width = documentObject.documentElement.clientWidth || global.innerWidth;
        popover.style.left = '0px';
        popover.style.top = '0px';
        const popoverRect = popover.getBoundingClientRect();
        const above = rect.top >= popoverRect.height + 8 + 8;
        const top = above ? global.scrollY + rect.top - popoverRect.height - 8 : global.scrollY + rect.bottom + 8;
        const left = Math.max(global.scrollX + 8, Math.min(global.scrollX + rect.left, global.scrollX + width - popoverRect.width - 8));
        popover.dataset.placement = above ? 'top' : 'bottom';
        popover.style.left = `${left}px`;
        popover.style.top = `${top}px`;
    }

    function showFieldErrorPopovers(root = documentObject) {
        queryAllWithSelf(root, INLINE_FIELD_ERROR_SELECTOR).forEach(widget => {
            if (!(widget instanceof HTMLElement) || !widget.dataset.inlineErrorMessage) return;
            removeFieldErrorPopover(widget);
            const popover = documentObject.createElement('div');
            popover.className = 'pc-inline-error-popover alert alert-danger py-1 px-2 small shadow-sm';
            popover.dataset.powercrudInlineErrorPopover = 'true';
            popover.setAttribute('role', 'alert');
            popover.textContent = widget.dataset.inlineErrorMessage;
            documentObject.body.appendChild(popover);
            widget._powercrudInlineErrorPopover = popover;
            positionFieldErrorPopover(widget, popover);
            const errorText = getInlineFieldErrorText(widget);
            if (errorText) {
                errorText.classList.add('visually-hidden');
                errorText.dataset.inlineErrorTextHidden = 'true';
            }
            if (widget.dataset.inlineErrorDismissBound !== 'true') {
                widget.dataset.inlineErrorDismissBound = 'true';
                const dismiss = () => removeFieldErrorPopover(widget);
                widget.querySelectorAll('input, select, textarea').forEach(control => {
                    control.addEventListener('input', dismiss, { once: true });
                    control.addEventListener('change', dismiss, { once: true });
                });
            }
        });
    }

    function destroyFieldErrorPopovers(root = documentObject) {
        queryAllWithSelf(root, INLINE_FIELD_ERROR_SELECTOR).forEach(removeFieldErrorPopover);
        if (root === documentObject) documentObject.querySelectorAll(INLINE_FIELD_ERROR_POPOVER_SELECTOR).forEach(popover => popover.remove());
    }

    function repositionFieldErrorPopovers(root = documentObject) {
        queryAllWithSelf(root, INLINE_FIELD_ERROR_SELECTOR).forEach(widget => {
            if (widget instanceof HTMLElement && widget._powercrudInlineErrorPopover instanceof HTMLElement) {
                positionFieldErrorPopover(widget, widget._powercrudInlineErrorPopover);
            }
        });
    }

    function removeOrphanedFieldErrorPopovers() {
        const owned = new Set();
        queryAllWithSelf(documentObject, INLINE_FIELD_ERROR_SELECTOR).forEach(widget => {
            if (widget instanceof HTMLElement && widget._powercrudInlineErrorPopover instanceof HTMLElement) owned.add(widget._powercrudInlineErrorPopover);
        });
        documentObject.querySelectorAll(INLINE_FIELD_ERROR_POPOVER_SELECTOR).forEach(popover => {
            if (!owned.has(popover)) popover.remove();
        });
    }

    return {
        destroyFieldErrorPopovers,
        presentInlineFocus,
        removeOrphanedFieldErrorPopovers,
        repositionFieldErrorPopovers,
        resolveInlineFocusTarget,
        showFieldErrorPopovers,
        toggleSaveSpinner,
    };
}
