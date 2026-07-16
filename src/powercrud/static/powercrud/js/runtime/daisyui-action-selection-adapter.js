// Private DaisyUI presentation adapter for dynamic action states and generic
// request spinners. Core retains permission, selection, and request decisions.
export function createDaisyuiActionSelectionAdapter() {
    const formSpinnerState = new WeakMap();
    const buttonSpinnerState = new WeakMap();

    function setRowActionDisabledPresentation(link, disabled, reason = '') {
        if (!(link instanceof HTMLElement)) {
            return;
        }
        link.classList.toggle('btn-disabled', disabled);
        link.classList.toggle('opacity-50', disabled);
        link.classList.remove('pointer-events-none');
        if (disabled) {
            link.setAttribute('aria-disabled', 'true');
            link.style.setProperty('pointer-events', 'auto', 'important');
            link.style.setProperty('cursor', 'not-allowed');
            if (reason) {
                link.setAttribute('data-tippy-content', reason);
                link.setAttribute('data-powercrud-tooltip', 'semantic');
            }
            return;
        }
        link.removeAttribute('aria-disabled');
        link.style.removeProperty('pointer-events');
        link.style.removeProperty('cursor');
        link.removeAttribute('data-tippy-content');
        link.removeAttribute('data-powercrud-tooltip');
    }

    function syncSelectionAwareButtonVisualState(button, options = {}) {
        if (!(button instanceof HTMLElement)) {
            return;
        }
        const { disable = false, reason = '' } = options;

        button.classList.toggle('btn-disabled', disable);
        button.classList.toggle('opacity-50', disable);
        button.classList.remove('pointer-events-none');

        if (disable) {
            button.setAttribute('aria-disabled', 'true');
            button.style.setProperty('pointer-events', 'auto', 'important');
            button.style.setProperty('cursor', 'not-allowed');
            if (reason) {
                button.setAttribute('data-tippy-content', reason);
                button.setAttribute('data-powercrud-tooltip', 'semantic');
            }
            return;
        }

        button.removeAttribute('aria-disabled');
        button.style.removeProperty('pointer-events');
        button.style.removeProperty('cursor');
        if (button.dataset.powercrudSelectionMinReason) {
            button.removeAttribute('data-tippy-content');
            button.removeAttribute('data-powercrud-tooltip');
        }
    }

    function startFormSpinner(form) {
        if (!form || formSpinnerState.has(form)) {
            return;
        }
        const saveBtn = form.querySelector('[data-form-save]');
        if (!saveBtn) {
            return;
        }
        formSpinnerState.set(form, {
            button: saveBtn,
            html: saveBtn.innerHTML,
        });
        saveBtn.disabled = true;
        saveBtn.style.width = `${saveBtn.offsetWidth}px`;
        saveBtn.innerHTML = '<span class="loading loading-spinner loading-sm text-center mx-auto"></span>';
    }

    function stopFormSpinner(form) {
        const state = formSpinnerState.get(form);
        if (!state) {
            return;
        }
        state.button.disabled = false;
        state.button.innerHTML = state.html;
        state.button.style.width = '';
        formSpinnerState.delete(form);
    }

    function startButtonSpinner(button) {
        if (!button || buttonSpinnerState.has(button)) {
            return;
        }
        buttonSpinnerState.set(button, {
            html: button.innerHTML,
        });
        button.disabled = true;
        button.style.width = `${button.offsetWidth}px`;
        button.innerHTML = '<span class="loading loading-spinner loading-sm text-center mx-auto"></span>';
    }

    function stopButtonSpinner(button) {
        const state = buttonSpinnerState.get(button);
        if (!state) {
            return;
        }
        button.disabled = false;
        button.innerHTML = state.html;
        button.style.width = '';
        buttonSpinnerState.delete(button);
    }

    return {
        setRowActionDisabledPresentation,
        startButtonSpinner,
        startFormSpinner,
        stopButtonSpinner,
        stopFormSpinner,
        syncSelectionAwareButtonVisualState,
    };
}
