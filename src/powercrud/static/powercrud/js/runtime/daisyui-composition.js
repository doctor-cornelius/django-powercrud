import { createSearchableSelectRuntime } from './searchable-selects.js';
import { createDaisyuiSearchableSelectAdapter } from './daisyui-searchable-select-adapter.js';
import { createDaisyuiTooltipLifecycleAdapter } from './daisyui-tooltip-adapter.js';
import { createDaisyuiModalLifecycleAdapter } from './daisyui-modal-adapter.js';
import { createDaisyuiActionSelectionAdapter } from './daisyui-action-selection-adapter.js';
import { createDaisyuiInlinePresentationAdapter } from './daisyui-inline-presentation-adapter.js';
import { createDaisyuiListColumnPresentationAdapter } from './daisyui-list-column-presentation-adapter.js';
import { createDaisyuiFilterFavouritesPresentationAdapter } from './daisyui-filter-favourites-presentation-adapter.js';
import { createDaisyuiRowActionMenuPresentationAdapter } from './daisyui-row-action-menu-presentation-adapter.js';

/**
 * Compose the only Phase 4 browser presentation: DaisyUI without a variant.
 *
 * This stays private because the stable public entry owns the durable runtime
 * lifecycle and no browser-side pack selection contract exists yet.
 */
export function createDaisyuiComposition({
    global,
    documentObject,
    isElementVisible,
    warnMissingDependency,
}) {
    const searchableSelectAdapter = createDaisyuiSearchableSelectAdapter({
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
    const tooltipAdapter = createDaisyuiTooltipLifecycleAdapter({
        global,
        documentObject,
        warnMissingDependency,
    });
    const modalAdapter = createDaisyuiModalLifecycleAdapter({ documentObject });
    const actionSelectionAdapter = createDaisyuiActionSelectionAdapter();
    const inlinePresentationAdapter = createDaisyuiInlinePresentationAdapter({
        global,
        documentObject,
    });
    const listColumnPresentationAdapter = createDaisyuiListColumnPresentationAdapter({
        global,
        documentObject,
    });
    const filterFavouritesPresentationAdapter = createDaisyuiFilterFavouritesPresentationAdapter({
        global,
        initPowercrudSearchableSelects: searchableSelects.initPowercrudSearchableSelects,
        initPowercrudTooltips: tooltipAdapter.init,
    });
    const rowActionMenuPresentationAdapter = createDaisyuiRowActionMenuPresentationAdapter({
        global,
    });

    return {
        searchableSelects,
        tooltipAdapter,
        modalAdapter,
        actionSelectionAdapter,
        inlinePresentationAdapter,
        listColumnPresentationAdapter,
        filterFavouritesPresentationAdapter,
        rowActionMenuPresentationAdapter,
    };
}
