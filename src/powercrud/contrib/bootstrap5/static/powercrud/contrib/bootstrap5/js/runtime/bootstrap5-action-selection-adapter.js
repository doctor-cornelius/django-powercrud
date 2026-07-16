/** Adapt shared disabled and spinner state to Bootstrap button presentation. */
export function createBootstrap5ActionSelectionAdapter() {
    const formSpinnerState = new WeakMap();
    const buttonSpinnerState = new WeakMap();

    function setDisabledPresentation(element, disabled, reason = '') {
        if (!(element instanceof HTMLElement)) {
            return;
        }
        element.classList.toggle('disabled', disabled);
        element.classList.toggle('opacity-50', disabled);
        if (disabled) {
            element.setAttribute('aria-disabled', 'true');
            element.style.setProperty('pointer-events', 'auto', 'important');
            element.style.setProperty('cursor', 'not-allowed');
            if (reason) {
                element.setAttribute('data-tippy-content', reason);
                element.setAttribute('data-bs-title', reason);
                element.setAttribute('data-powercrud-tooltip', 'semantic');
            }
            return;
        }
        element.removeAttribute('aria-disabled');
        element.style.removeProperty('pointer-events');
        element.style.removeProperty('cursor');
        element.removeAttribute('data-tippy-content');
        element.removeAttribute('data-bs-title');
        element.removeAttribute('data-powercrud-tooltip');
    }

    function startSpinner(element, state) {
        if (!(element instanceof HTMLElement) || state.has(element)) {
            return;
        }
        state.set(element, { html: element.innerHTML });
        element.disabled = true;
        element.style.width = `${element.offsetWidth}px`;
        element.innerHTML = '<span class="spinner-border spinner-border-sm" aria-hidden="true"></span><span class="visually-hidden">Loading</span>';
    }

    function stopSpinner(element, state) {
        const saved = state.get(element);
        if (!saved) {
            return;
        }
        element.disabled = false;
        element.innerHTML = saved.html;
        element.style.width = '';
        state.delete(element);
    }

    function startFormSpinner(form) {
        startSpinner(form?.querySelector('[data-form-save]'), formSpinnerState);
    }

    function stopFormSpinner(form) {
        stopSpinner(formSpinnerState.get(form)?.button || form?.querySelector('[data-form-save]'), formSpinnerState);
    }

    function startButtonSpinner(button) {
        startSpinner(button, buttonSpinnerState);
    }

    function stopButtonSpinner(button) {
        stopSpinner(button, buttonSpinnerState);
    }

    function syncSelectionAwareButtonVisualState(button, { disable = false, reason = '' } = {}) {
        setDisabledPresentation(button, disable, reason);
    }

    return {
        setRowActionDisabledPresentation: setDisabledPresentation,
        startButtonSpinner,
        startFormSpinner,
        stopButtonSpinner,
        stopFormSpinner,
        syncSelectionAwareButtonVisualState,
    };
}
