import { createSearchableSelectRuntime } from '../../../../../../../../static/powercrud/js/runtime/searchable-selects.js';
import { createBootstrap5ActionSelectionAdapter } from './bootstrap5-action-selection-adapter.js';
import { createBootstrap5FloatingPanelAdapter } from './bootstrap5-floating-panel-adapter.js';
import { createBootstrap5InlinePresentationAdapter } from './bootstrap5-inline-presentation-adapter.js';
import { createBootstrap5ModalLifecycleAdapter } from './bootstrap5-modal-adapter.js';
import { createBootstrap5SearchableSelectAdapter } from './bootstrap5-searchable-select-adapter.js';
import { createBootstrap5TooltipLifecycleAdapter } from './bootstrap5-tooltip-adapter.js';

/** Compose the private Bootstrap lifecycle without importing DaisyUI or Tippy. */
export function createBootstrap5BaselineComposition({ global, documentObject, isElementVisible, warnMissingDependency }) {
    const searchableSelectAdapter = createBootstrap5SearchableSelectAdapter({
        global,
        documentObject,
        warnMissingDependency,
    });
    const searchableSelects = createSearchableSelectRuntime({
        documentObject,
        isElementVisible,
        ensureSearchableSelectAdapterAvailable: searchableSelectAdapter.ensureAvailable,
        enhanceSearchableSelect: searchableSelectAdapter.enhanceSingle,
        enhanceSearchableMultiselect: searchableSelectAdapter.enhanceMultiple,
        destroySearchableSelect: searchableSelectAdapter.destroy,
    });
    const tooltipAdapter = createBootstrap5TooltipLifecycleAdapter({ global, documentObject, warnMissingDependency });
    const modalAdapter = createBootstrap5ModalLifecycleAdapter({ global, documentObject, warnMissingDependency });
    const actionSelectionAdapter = createBootstrap5ActionSelectionAdapter();
    const floatingPanels = createBootstrap5FloatingPanelAdapter({ global, documentObject });
    const inlinePresentationAdapter = createBootstrap5InlinePresentationAdapter({ global, documentObject });

    return {
        searchableSelects,
        tooltipAdapter,
        modalAdapter,
        actionSelectionAdapter,
        inlinePresentationAdapter,
        listColumnPresentationAdapter: {
            applyOptionDisabledState: floatingPanels.applyOptionDisabledState,
            clearContainerPlacement: floatingPanels.clearContainerPlacement,
            cloneFloatingPanel: floatingPanels.clone,
            focusFirstOption: floatingPanels.focusFirstOption,
            positionFloatingPanel: floatingPanels.position,
            prepareFloatingPanel: floatingPanels.prepare,
            showFloatingPanel: floatingPanels.show,
            syncContainerPlacement: floatingPanels.syncContainerPlacement,
        },
        filterFavouritesPresentationAdapter: {
            cloneFavouritesFloatingPanel: floatingPanels.clone,
            initialiseFavouritesFloatingPanel(panel) {
                searchableSelects.initPowercrudSearchableSelects(panel);
                tooltipAdapter.init(panel);
            },
            positionFavouritesFloatingPanel: floatingPanels.position,
            prepareFavouritesFloatingPanel: floatingPanels.prepare,
            scheduleFilterPanelInitialisation(panel) {
                global.setTimeout(() => searchableSelects.initPowercrudSearchableSelects(panel), 0);
            },
            setFavouritesDropdownOpen(toolbar, isOpen) {
                toolbar?.classList.toggle('show', Boolean(isOpen));
            },
            setFilterPanelOpen(panel, isOpen) {
                if (panel instanceof Element) {
                    panel.classList.toggle('hidden', !isOpen);
                }
            },
            showFavouritesFloatingPanel: floatingPanels.show,
            showFavouritesToolbar(toolbar) {
                toolbar?.classList.remove('d-none');
            },
            syncAddFilterVisibility(container, isOpen) {
                container?.classList.toggle('hidden', !isOpen);
                container?.classList.toggle('d-none', !isOpen);
                if (isOpen) {
                    global.setTimeout(() => searchableSelects.initPowercrudSearchableSelects(container), 0);
                }
            },
            syncFavouritesTriggerVisualState({ trigger, selectedLabel = '', isDirty = false } = {}) {
                const outline = trigger?.querySelector('[data-powercrud-filter-favourites-icon-outline="true"]');
                const filled = trigger?.querySelector('[data-powercrud-filter-favourites-icon-filled="true"]');
                if (outline instanceof Element) {
                    outline.classList.toggle('d-none', Boolean(selectedLabel));
                    outline.classList.toggle('hidden', Boolean(selectedLabel));
                }
                if (filled instanceof Element) {
                    filled.classList.toggle('d-none', !selectedLabel);
                    filled.classList.toggle('hidden', !selectedLabel);
                    filled.classList.toggle('text-primary', Boolean(selectedLabel) && !isDirty);
                    filled.classList.toggle('text-warning', Boolean(selectedLabel) && isDirty);
                }
            },
            syncFilterToggleVisualState(trigger, hasActiveFilters) {
                if (!(trigger instanceof Element)) {
                    return;
                }
                trigger.classList.toggle('btn-outline-secondary', !hasActiveFilters);
                trigger.classList.toggle('btn-secondary', hasActiveFilters);
                const outline = trigger.querySelector('[data-powercrud-filter-toggle-icon-outline="true"]');
                const filled = trigger.querySelector('[data-powercrud-filter-toggle-icon-filled="true"]');
                outline?.classList.toggle('d-none', Boolean(hasActiveFilters));
                filled?.classList.toggle('d-none', !hasActiveFilters);
            },
        },
        rowActionMenuPresentationAdapter: {
            cloneFloatingMenu: floatingPanels.clone,
            positionFloatingMenu: floatingPanels.position,
            prepareFloatingMenu: floatingPanels.prepare,
            showFloatingMenu: floatingPanels.show,
        },
    };
}
