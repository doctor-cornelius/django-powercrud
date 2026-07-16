/** Turn Bootstrap's private implementation into the public adapter hook shape. */
export function createBootstrap5PublicHooks(composition) {
    const searchable = composition.searchableSelects;
    const tooltips = composition.tooltipAdapter;
    const modals = composition.modalAdapter;
    const controls = composition.actionSelectionAdapter;
    const inline = composition.inlinePresentationAdapter;
    const listColumns = composition.listColumnPresentationAdapter;
    const filters = composition.filterFavouritesPresentationAdapter;
    const rows = composition.rowActionMenuPresentationAdapter;
    return {
        searchableSelects: {
            init: searchable.initPowercrudSearchableSelects,
            destroy: searchable.destroyPowercrudSearchableSelects,
            syncValues: searchable.syncTomSelectValues,
        },
        tooltips: { init: tooltips.init, hide: tooltips.hide, destroy: tooltips.destroy },
        modals: {
            applyTrigger: modals.applyTriggerClasses,
            bindClose: modals.bindClose,
            cleanupDuplicates: modals.cleanupDuplicates,
            show: modals.show,
            closeAll: modals.closeAll,
            dispose: modals.dispose,
        },
        controls: {
            setDisabled(element, { disabled, reason }) { controls.setRowActionDisabledPresentation(element, disabled, reason); },
            setBusy(element, { busy, kind }) {
                if (kind === 'form') (busy ? controls.startFormSpinner : controls.stopFormSpinner)(element);
                else (busy ? controls.startButtonSpinner : controls.stopButtonSpinner)(element);
            },
            syncSelectionAction(element, { enabled = true, reason = '' } = {}) {
                controls.syncSelectionAwareButtonVisualState(element, {
                    disable: !enabled,
                    reason,
                });
            },
        },
        floatingPanels: {
            clone(kind, template) {
                return kind === 'row-actions' ? rows.cloneFloatingMenu(template) :
                    kind === 'list-columns' ? listColumns.cloneFloatingPanel(template) :
                        filters.cloneFavouritesFloatingPanel(template);
            },
            prepare(kind, { panel, trigger }) {
                if (kind === 'row-actions') return rows.prepareFloatingMenu(panel, trigger);
                if (kind === 'list-columns') return listColumns.prepareFloatingPanel(panel, trigger);
                return filters.prepareFavouritesFloatingPanel(panel, trigger);
            },
            position(kind, { panel, trigger }) {
                if (kind === 'row-actions') return rows.positionFloatingMenu(panel, trigger);
                if (kind === 'list-columns') return listColumns.positionFloatingPanel(panel, trigger);
                return filters.positionFavouritesFloatingPanel(panel, trigger);
            },
            show(kind, { panel, trigger }) {
                if (kind === 'row-actions') return rows.showFloatingMenu(panel, trigger);
                if (kind === 'list-columns') return listColumns.showFloatingPanel(panel, trigger);
                return filters.showFavouritesFloatingPanel(panel, trigger);
            },
            focusFirst(kind, panel, selector) {
                if (kind === 'list-columns') return listColumns.focusFirstOption(panel, selector);
            },
            setOptionDisabled(kind, option, disabled) { if (kind === 'list-columns') return listColumns.applyOptionDisabledState(option, disabled); },
        },
        inline: {
            resolveFocusTarget: inline.resolveInlineFocusTarget,
            presentFocus: inline.presentInlineFocus,
            setSaving: inline.toggleSaveSpinner,
            showErrors: inline.showFieldErrorPopovers,
            destroyErrors: inline.destroyFieldErrorPopovers,
            removeOrphanedErrors: inline.removeOrphanedFieldErrorPopovers,
            repositionErrors: inline.repositionFieldErrorPopovers,
        },
        filters: {
            setPanelOpen: filters.setFilterPanelOpen,
            setFavouritesOpen: filters.setFavouritesDropdownOpen,
            setAddFilterVisible: filters.syncAddFilterVisibility,
            showFavouritesToolbar: filters.showFavouritesToolbar,
            syncFilterToggle: filters.syncFilterToggleVisualState,
            syncFavouriteTrigger: filters.syncFavouritesTriggerVisualState,
        },
    };
}
