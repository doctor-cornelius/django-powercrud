import {
    INLINE_FIELD_ERROR_POPOVER_SELECTOR,
    INLINE_FIELD_ERROR_SELECTOR,
} from './selectors.js';
import { queryAllWithSelf } from './dom.js';

// Private DaisyUI presentation adapter for inline focus, validation callouts,
// and save-button feedback. Core retains inline lifecycle and request policy.
export function createDaisyuiInlinePresentationAdapter(context) {
    const { global, documentObject } = context;

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

    function resolveInlineFocusTarget(row, preferredField) {
        if (!row) {
            return null;
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
        global.requestAnimationFrame(() => {
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
                        view: global,
                    })
                );
            });
        });
    }

    function maybeSelectInputValue(focusTarget, shouldHighlight) {
        if (!focusTarget || !shouldHighlight || !(focusTarget instanceof HTMLInputElement)) {
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

    function presentInlineFocus(focusTarget, triggerField, shouldHighlight) {
        focusTarget.focus();
        maybeOpenSelectDropdown(focusTarget, triggerField);
        maybeSelectInputValue(focusTarget, shouldHighlight);
    }

    function getInlineFieldErrorText(widget) {
        if (!(widget instanceof HTMLElement)) {
            return null;
        }
        const control = widget.querySelector('[aria-describedby]');
        const describedBy = control instanceof HTMLElement
            ? (control.getAttribute('aria-describedby') || '')
            : '';
        const errorId = describedBy
            .split(/\s+/)
            .find(id => id.endsWith('_inline_error'));
        if (errorId) {
            const errorText = documentObject.getElementById(errorId);
            if (errorText instanceof HTMLElement) {
                return errorText;
            }
        }
        const siblingError = widget.nextElementSibling;
        if (
            siblingError instanceof HTMLElement
            && siblingError.dataset.inlineErrorText === 'true'
        ) {
            return siblingError;
        }
        return null;
    }

    function removeInlineFieldErrorPopover(widget) {
        if (!(widget instanceof HTMLElement)) {
            return;
        }
        const errorText = getInlineFieldErrorText(widget);
        if (errorText) {
            errorText.classList.remove('sr-only');
            delete errorText.dataset.inlineErrorTextHidden;
        }
        if (widget._powercrudInlineErrorTippy) {
            widget._powercrudInlineErrorTippy.destroy();
            delete widget._powercrudInlineErrorTippy;
        }
        if (widget._powercrudInlineErrorPopover) {
            widget._powercrudInlineErrorPopover.remove();
            delete widget._powercrudInlineErrorPopover;
        }
    }

    function positionInlineFieldErrorPopover(widget, popover) {
        if (!(widget instanceof HTMLElement) || !(popover instanceof HTMLElement)) {
            return;
        }

        const viewportWidth = documentObject.documentElement.clientWidth || global.innerWidth;
        const gap = 8;
        const edgePadding = 8;
        const widgetRect = widget.getBoundingClientRect();

        popover.style.left = '0px';
        popover.style.top = '0px';

        const popoverRect = popover.getBoundingClientRect();
        const hasRoomAbove = widgetRect.top >= popoverRect.height + gap + edgePadding;
        const placement = hasRoomAbove ? 'top' : 'bottom';
        const top = placement === 'top'
            ? global.scrollY + widgetRect.top - popoverRect.height - gap
            : global.scrollY + widgetRect.bottom + gap;
        const preferredLeft = global.scrollX + widgetRect.left;
        const minLeft = global.scrollX + edgePadding;
        const maxLeft = global.scrollX + viewportWidth - popoverRect.width - edgePadding;
        const left = Math.max(minLeft, Math.min(preferredLeft, maxLeft));

        popover.dataset.placement = placement;
        popover.style.left = `${left}px`;
        popover.style.top = `${top}px`;
    }

    function repositionFieldErrorPopovers(root = documentObject) {
        queryAllWithSelf(root, INLINE_FIELD_ERROR_SELECTOR).forEach(widget => {
            if (
                widget instanceof HTMLElement
                && widget._powercrudInlineErrorPopover instanceof HTMLElement
            ) {
                positionInlineFieldErrorPopover(widget, widget._powercrudInlineErrorPopover);
            }
        });
    }

    function destroyFieldErrorPopovers(root = documentObject) {
        queryAllWithSelf(root, INLINE_FIELD_ERROR_SELECTOR).forEach(widget => {
            removeInlineFieldErrorPopover(widget);
        });
        if (root === documentObject) {
            documentObject.querySelectorAll(INLINE_FIELD_ERROR_POPOVER_SELECTOR).forEach(popover => {
                popover.remove();
            });
        }
    }

    function removeOrphanedFieldErrorPopovers() {
        const ownedPopovers = new Set();
        queryAllWithSelf(documentObject, INLINE_FIELD_ERROR_SELECTOR).forEach(widget => {
            if (
                widget instanceof HTMLElement
                && widget._powercrudInlineErrorPopover instanceof HTMLElement
            ) {
                ownedPopovers.add(widget._powercrudInlineErrorPopover);
            }
        });
        documentObject.querySelectorAll(INLINE_FIELD_ERROR_POPOVER_SELECTOR).forEach(popover => {
            if (!ownedPopovers.has(popover)) {
                popover.remove();
            }
        });
    }

    function bindInlineFieldErrorDismissal(widget) {
        if (!(widget instanceof HTMLElement) || widget.dataset.inlineErrorDismissBound === 'true') {
            return;
        }
        widget.dataset.inlineErrorDismissBound = 'true';
        const dismiss = () => {
            removeInlineFieldErrorPopover(widget);
        };
        widget.querySelectorAll('input, select, textarea').forEach(control => {
            control.addEventListener('input', dismiss, { once: true });
            control.addEventListener('change', dismiss, { once: true });
        });
    }

    function showFieldErrorPopovers(root = documentObject) {
        queryAllWithSelf(root, INLINE_FIELD_ERROR_SELECTOR).forEach(widget => {
            if (!(widget instanceof HTMLElement)) {
                return;
            }
            const message = widget.dataset.inlineErrorMessage || '';
            if (!message) {
                return;
            }
            removeInlineFieldErrorPopover(widget);
            const popover = documentObject.createElement('div');
            popover.className = 'pc-inline-error-popover';
            popover.dataset.powercrudInlineErrorPopover = 'true';
            popover.setAttribute('role', 'alert');
            popover.textContent = message;
            documentObject.body.appendChild(popover);
            widget._powercrudInlineErrorPopover = popover;
            positionInlineFieldErrorPopover(widget, popover);
            const errorText = getInlineFieldErrorText(widget);
            if (errorText) {
                errorText.classList.add('sr-only');
                errorText.dataset.inlineErrorTextHidden = 'true';
            }
            bindInlineFieldErrorDismissal(widget);
        });
    }

    function toggleSaveSpinner(row, isSaving) {
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
        destroyFieldErrorPopovers,
        presentInlineFocus,
        removeOrphanedFieldErrorPopovers,
        repositionFieldErrorPopovers,
        resolveInlineFocusTarget,
        showFieldErrorPopovers,
        toggleSaveSpinner,
    };
}
