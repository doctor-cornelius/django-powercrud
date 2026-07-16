// Private DaisyUI presentation adapter for filter-panel display and the
// favourites chooser. Core retains filter/favourite state, semantic hooks,
// request policy, detached-panel ownership, and HTMX lifecycle ordering.
export function createDaisyuiFilterFavouritesPresentationAdapter(context) {
    const {
        global,
        initPowercrudSearchableSelects,
        initPowercrudTooltips,
    } = context;

    function cloneFavouritesFloatingPanel(template) {
        if (!(template instanceof HTMLElement)) {
            return null;
        }
        const panel = template.firstElementChild?.cloneNode(true);
        return panel instanceof HTMLElement ? panel : null;
    }

    function prepareFavouritesFloatingPanel(panel) {
        if (!(panel instanceof HTMLElement)) {
            return false;
        }
        panel.style.position = 'fixed';
        panel.style.visibility = 'hidden';
        panel.style.pointerEvents = 'none';
        return true;
    }

    function positionFavouritesFloatingPanel(panel, trigger) {
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

        panel.style.top = `${top}px`;
        panel.style.left = `${left}px`;
    }

    function showFavouritesFloatingPanel(panel) {
        if (!(panel instanceof HTMLElement)) {
            return;
        }
        panel.style.visibility = '';
        panel.style.pointerEvents = '';
    }

    function setFavouritesDropdownOpen(toolbar, isOpen) {
        if (toolbar instanceof Element) {
            toolbar.classList.toggle('dropdown-open', Boolean(isOpen));
        }
    }

    function initialiseFavouritesFloatingPanel(panel) {
        if (!(panel instanceof Element)) {
            return;
        }
        initPowercrudSearchableSelects?.(panel);
        initPowercrudTooltips?.(panel);
    }

    function syncFavouritesTriggerVisualState(options = {}) {
        const {
            trigger,
            selectedLabel = '',
            isDirty = false,
        } = options;
        if (!(trigger instanceof HTMLElement)) {
            return;
        }

        const outlineIcon = trigger.querySelector(
            '[data-powercrud-filter-favourites-icon-outline="true"]'
        );
        const filledIcon = trigger.querySelector(
            '[data-powercrud-filter-favourites-icon-filled="true"]'
        );
        if (outlineIcon instanceof HTMLElement) {
            outlineIcon.classList.toggle('hidden', Boolean(selectedLabel));
        }
        if (filledIcon instanceof HTMLElement) {
            filledIcon.classList.toggle('hidden', !selectedLabel);
            filledIcon.classList.toggle('text-primary', Boolean(selectedLabel) && !isDirty);
            filledIcon.classList.toggle('text-warning', Boolean(selectedLabel) && isDirty);
        }
    }

    function setFilterPanelOpen(panel, isOpen) {
        if (panel instanceof Element) {
            panel.classList.toggle('hidden', !isOpen);
        }
    }

    function syncFilterToggleVisualState(trigger, hasActiveFilters) {
        if (!(trigger instanceof Element)) {
            return;
        }
        const outlineIcon = trigger.querySelector(
            '[data-powercrud-filter-toggle-icon-outline="true"]'
        );
        const filledIcon = trigger.querySelector(
            '[data-powercrud-filter-toggle-icon-filled="true"]'
        );
        if (outlineIcon instanceof HTMLElement || outlineIcon instanceof SVGElement) {
            outlineIcon.classList.toggle('hidden', hasActiveFilters);
        }
        if (filledIcon instanceof HTMLElement || filledIcon instanceof SVGElement) {
            filledIcon.classList.toggle('hidden', !hasActiveFilters);
        }
    }

    function syncAddFilterVisibility(container, isOpen) {
        if (!(container instanceof Element)) {
            return;
        }
        container.classList.toggle('hidden', !isOpen);
        if (isOpen) {
            global.setTimeout(() => initPowercrudSearchableSelects?.(container), 0);
        }
    }

    function showFavouritesToolbar(toolbar) {
        if (toolbar instanceof Element) {
            toolbar.classList.remove('hidden');
        }
    }

    function scheduleFilterPanelInitialisation(panel) {
        if (panel instanceof Element) {
            global.setTimeout(() => initPowercrudSearchableSelects?.(panel), 0);
        }
    }

    return {
        cloneFavouritesFloatingPanel,
        initialiseFavouritesFloatingPanel,
        positionFavouritesFloatingPanel,
        prepareFavouritesFloatingPanel,
        scheduleFilterPanelInitialisation,
        setFavouritesDropdownOpen,
        setFilterPanelOpen,
        showFavouritesFloatingPanel,
        showFavouritesToolbar,
        syncAddFilterVisibility,
        syncFavouritesTriggerVisualState,
        syncFilterToggleVisualState,
    };
}
