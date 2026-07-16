// Private DaisyUI presentation adapter for the list-column chooser shell,
// placement, focus, and disabled visuals. Core retains column state, detached
// panel ownership, request policy, and last-visible-column enforcement.
export function createDaisyuiListColumnPresentationAdapter(context) {
    const { global, documentObject } = context;

    function cloneFloatingPanel(template) {
        if (!(template instanceof HTMLElement)) {
            return null;
        }
        const panel = template.firstElementChild?.cloneNode(true);
        return panel instanceof HTMLElement ? panel : null;
    }

    function prepareFloatingPanel(panel) {
        if (!(panel instanceof HTMLElement)) {
            return false;
        }
        panel.style.position = 'fixed';
        panel.style.visibility = 'hidden';
        panel.style.pointerEvents = 'none';
        return true;
    }

    function positionFloatingPanel(panel, trigger) {
        if (!(panel instanceof HTMLElement) || !(trigger instanceof HTMLElement)) {
            return;
        }

        const viewportPadding = 8;
        const panelGap = 8;
        const triggerRect = trigger.getBoundingClientRect();
        const panelRect = panel.getBoundingClientRect();
        const spaceBelow = global.innerHeight - triggerRect.bottom - viewportPadding;
        const spaceAbove = triggerRect.top - viewportPadding;
        const shouldOpenUpward = panelRect.height > spaceBelow && spaceAbove > spaceBelow;
        const container = trigger.closest('[data-powercrud-list-columns="true"]');

        const endLeft = triggerRect.right - panelRect.width;
        const shouldOpenStart = endLeft < viewportPadding;
        let left = shouldOpenStart ? triggerRect.left : endLeft;
        let top = shouldOpenUpward
            ? triggerRect.top - panelRect.height - panelGap
            : triggerRect.bottom + panelGap;

        top = Math.max(
            viewportPadding,
            Math.min(top, global.innerHeight - panelRect.height - viewportPadding),
        );
        left = Math.max(
            viewportPadding,
            Math.min(left, global.innerWidth - panelRect.width - viewportPadding),
        );

        panel.style.top = `${top}px`;
        panel.style.left = `${left}px`;
        if (container instanceof HTMLElement) {
            container.dataset.powercrudListColumnsPlacement = shouldOpenStart ? 'start' : 'end';
        }
    }

    function showFloatingPanel(panel) {
        if (!(panel instanceof HTMLElement)) {
            return;
        }
        panel.style.visibility = '';
        panel.style.pointerEvents = '';
    }

    function syncContainerPlacement(container) {
        if (!(container instanceof HTMLDetailsElement) || !container.open) {
            return;
        }

        const trigger = container.querySelector('[data-powercrud-list-columns-trigger="true"]');
        if (!(trigger instanceof HTMLElement)) {
            return;
        }

        container.dataset.powercrudListColumnsPlacement = 'end';
        global.requestAnimationFrame(() => {
            if (!container.open) {
                return;
            }
            const triggerRect = trigger.getBoundingClientRect();
            const panelWidth = Math.min(288, documentObject.documentElement.clientWidth - 16);
            const endLeft = triggerRect.right - panelWidth;
            container.dataset.powercrudListColumnsPlacement = endLeft < 8 ? 'start' : 'end';
        });
    }

    function clearContainerPlacement(container) {
        if (container instanceof HTMLElement) {
            delete container.dataset.powercrudListColumnsPlacement;
        }
    }

    function focusFirstOption(panel, selector) {
        if (!(panel instanceof Element)) {
            return;
        }
        const firstOption = panel.querySelector(selector);
        if (firstOption instanceof HTMLInputElement) {
            global.setTimeout(() => firstOption.focus(), 0);
        }
    }

    function applyOptionDisabledState(option, disabled) {
        if (!(option instanceof HTMLElement)) {
            return;
        }
        option.classList.toggle('cursor-not-allowed', disabled);
        option.classList.toggle('opacity-70', disabled);
    }

    return {
        applyOptionDisabledState,
        clearContainerPlacement,
        cloneFloatingPanel,
        focusFirstOption,
        positionFloatingPanel,
        prepareFloatingPanel,
        showFloatingPanel,
        syncContainerPlacement,
    };
}
