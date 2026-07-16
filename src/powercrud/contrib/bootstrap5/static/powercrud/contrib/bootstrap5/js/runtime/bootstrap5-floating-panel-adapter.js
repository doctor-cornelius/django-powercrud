/** Provide Bootstrap-neutral geometry for detached list-column and row-action panels. */
export function createBootstrap5FloatingPanelAdapter({ global, documentObject }) {
    function clone(template) {
        const panel = template?.firstElementChild?.cloneNode(true);
        return panel instanceof HTMLElement ? panel : null;
    }

    function prepare(panel) {
        if (!(panel instanceof HTMLElement)) {
            return false;
        }
        // Bootstrap keeps dropdown menus display:none until .show is present.
        // Apply it while the clone is invisible so positioning uses its real size.
        panel.classList.add('show');
        Object.assign(panel.style, { position: 'fixed', visibility: 'hidden', pointerEvents: 'none', zIndex: '1080' });
        return true;
    }

    function position(panel, trigger) {
        if (!(panel instanceof HTMLElement) || !(trigger instanceof HTMLElement)) {
            return;
        }
        const padding = 8;
        const gap = 4;
        const triggerRect = trigger.getBoundingClientRect();
        const panelRect = panel.getBoundingClientRect();
        const roomBelow = global.innerHeight - triggerRect.bottom - padding;
        const roomAbove = triggerRect.top - padding;
        const openUpward = panelRect.height > roomBelow && roomAbove >= panelRect.height;
        panel.style.top = `${Math.max(padding, Math.min(openUpward ? triggerRect.top - panelRect.height - gap : triggerRect.bottom + gap, global.innerHeight - panelRect.height - padding))}px`;
        panel.style.left = `${Math.max(padding, Math.min(triggerRect.right - panelRect.width, global.innerWidth - panelRect.width - padding))}px`;
    }

    function show(panel) {
        if (panel instanceof HTMLElement) {
            panel.classList.add('show');
            panel.style.visibility = '';
            panel.style.pointerEvents = '';
        }
    }

    function focusFirstOption(panel, selector) {
        const option = panel?.querySelector(selector);
        if (option instanceof HTMLInputElement) {
            global.setTimeout(() => option.focus(), 0);
        }
    }

    function applyOptionDisabledState(option, disabled) {
        if (option instanceof HTMLElement) {
            option.classList.toggle('opacity-50', disabled);
            option.classList.toggle('disabled', disabled);
        }
    }

    function syncContainerPlacement(container) {
        if (!(container instanceof HTMLDetailsElement) || !container.open) {
            return;
        }
        const trigger = container.querySelector('[data-powercrud-list-columns-trigger="true"]');
        if (!(trigger instanceof HTMLElement)) {
            return;
        }
        container.dataset.powercrudListColumnsPlacement = trigger.getBoundingClientRect().right < 296 ? 'start' : 'end';
    }

    function clearContainerPlacement(container) {
        if (container instanceof HTMLElement) {
            delete container.dataset.powercrudListColumnsPlacement;
        }
    }

    return { applyOptionDisabledState, clearContainerPlacement, clone, focusFirstOption, position, prepare, show, syncContainerPlacement };
}
