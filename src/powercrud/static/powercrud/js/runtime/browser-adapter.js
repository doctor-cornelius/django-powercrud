/**
 * Convert the public browser-adapter hooks into the internal composition used
 * by the stable PowerCRUD lifecycle. External packs only implement the hooks
 * documented in the public contract; this module owns every legacy method
 * name consumed by the runtime modules.
 */

function noop() {}

function identity(value) {
    return value;
}

function neutralHooks() {
    return {
        fragment: { init: noop, destroy: noop },
        searchableSelects: { init: noop, destroy: noop, syncValues: noop },
        tooltips: { init: noop, hide: noop, destroy: noop },
        modals: {
            applyTrigger: noop,
            bindClose: noop,
            cleanupDuplicates: noop,
            show(modal) {
                if (modal instanceof HTMLDialogElement) {
                    modal.showModal();
                }
            },
            closeAll(root) {
                root?.querySelectorAll?.('dialog[open]').forEach(dialog => dialog.close());
            },
            dispose: noop,
        },
        controls: {
            setDisabled(element, { disabled }) {
                if (!(element instanceof HTMLElement)) return;
                element.toggleAttribute('disabled', disabled);
                element.setAttribute('aria-disabled', String(disabled));
            },
            setBusy(element, { busy }) {
                if (!(element instanceof HTMLElement)) return;
                element.toggleAttribute('aria-busy', busy);
            },
            syncSelectionAction: noop,
        },
        floatingPanels: {
            clone(_kind, template) { return template?.content?.firstElementChild?.cloneNode(true) || null; },
            prepare: noop,
            position: noop,
            show: noop,
            hide: noop,
            focusFirst: noop,
            setOptionDisabled: noop,
        },
        inline: {
            resolveFocusTarget: identity,
            presentFocus: noop,
            setSaving: noop,
            showErrors: noop,
            destroyErrors: noop,
            removeOrphanedErrors: noop,
            repositionErrors: noop,
        },
        filters: {
            setPanelOpen(panel, open) { if (panel instanceof HTMLElement) panel.hidden = !open; },
            setFavouritesOpen(panel, open) { if (panel instanceof HTMLElement) panel.hidden = !open; },
            setAddFilterVisible(container, visible) { if (container instanceof HTMLElement) container.hidden = !visible; },
            showFavouritesToolbar: noop,
            syncFilterToggle: noop,
            syncFavouriteTrigger: noop,
        },
    };
}

function mergeHooks(base, supplied) {
    const merged = { ...base };
    Object.entries(supplied || {}).forEach(([name, hooks]) => {
        if (hooks && typeof hooks === 'object' && base[name]) {
            merged[name] = { ...base[name], ...hooks };
        }
    });
    return merged;
}

/** Create the private runtime composition from public adapter hooks. */
export function createCompositionFromBrowserAdapter(adapter, context) {
    const supplied = adapter?.create?.(context) || {};
    if (!supplied || typeof supplied !== 'object') {
        throw new Error('PowerCRUD adapter create() must return an object.');
    }
    const hooks = mergeHooks(neutralHooks(), supplied);
    const schedule = (callback, delay = 0) => context.schedule(callback, delay);
    const initialiseVisibleFragment = root => {
        hooks.searchableSelects.init(root);
        hooks.tooltips.init(root);
        hooks.fragment.init(root);
    };
    return {
        fragmentAdapter: {
            init: hooks.fragment.init,
            destroy: hooks.fragment.destroy,
        },
        searchableSelects: {
            initPowercrudSearchableSelects: hooks.searchableSelects.init,
            destroyPowercrudSearchableSelects: hooks.searchableSelects.destroy,
            syncTomSelectValues: hooks.searchableSelects.syncValues,
        },
        tooltipAdapter: {
            init: hooks.tooltips.init,
            hide: hooks.tooltips.hide,
            destroy: hooks.tooltips.destroy,
            scheduleInit(root, delay) { schedule(() => hooks.tooltips.init(root), delay); },
            scheduleResizeInit(root, delay) { schedule(() => hooks.tooltips.init(root), delay); },
        },
        modalAdapter: {
            applyTriggerClasses(trigger, modal) { return hooks.modals.applyTrigger(trigger, modal); },
            bindClose: hooks.modals.bindClose,
            cleanupDuplicates: hooks.modals.cleanupDuplicates,
            closeAll: hooks.modals.closeAll,
            show: hooks.modals.show,
            dispose: hooks.modals.dispose,
        },
        actionSelectionAdapter: {
            startButtonSpinner(element) { hooks.controls.setBusy(element, { busy: true, kind: 'button' }); },
            startFormSpinner(element) { hooks.controls.setBusy(element, { busy: true, kind: 'form' }); },
            stopButtonSpinner(element) { hooks.controls.setBusy(element, { busy: false, kind: 'button' }); },
            stopFormSpinner(element) { hooks.controls.setBusy(element, { busy: false, kind: 'form' }); },
            setRowActionDisabledPresentation(element, disabled, reason) { hooks.controls.setDisabled(element, { disabled, reason }); },
            syncSelectionAwareButtonVisualState(element, options = {}) {
                hooks.controls.syncSelectionAction(element, {
                    enabled: !options.disable,
                    reason: options.reason || '',
                });
                // Selection state can add or remove a semantic tooltip after
                // the initial fragment pass, so refresh this one control.
                hooks.tooltips.init(element);
            },
            setBulkActionButtonsDisabled(root, disabled) {
                root?.querySelectorAll?.('[data-powercrud-selection-aware]').forEach(element => hooks.controls.setDisabled(element, { disabled }));
            },
        },
        inlinePresentationAdapter: {
            toggleSaveSpinner(root, busy) { hooks.inline.setSaving(root, busy); },
            resolveInlineFocusTarget: hooks.inline.resolveFocusTarget,
            presentInlineFocus: hooks.inline.presentFocus,
            showFieldErrorPopovers: hooks.inline.showErrors,
            destroyFieldErrorPopovers: hooks.inline.destroyErrors,
            removeOrphanedFieldErrorPopovers: hooks.inline.removeOrphanedErrors,
            repositionFieldErrorPopovers: hooks.inline.repositionErrors,
        },
        listColumnPresentationAdapter: {
            applyOptionDisabledState(option, disabled) { hooks.floatingPanels.setOptionDisabled('list-columns', option, disabled); },
            clearContainerPlacement: noop,
            cloneFloatingPanel(template) { return hooks.floatingPanels.clone('list-columns', template); },
            focusFirstOption(panel, selector) {
                hooks.floatingPanels.focusFirst('list-columns', panel, selector);
            },
            positionFloatingPanel(panel, trigger) { hooks.floatingPanels.position('list-columns', { panel, trigger }); },
            prepareFloatingPanel(panel, trigger) { hooks.floatingPanels.prepare('list-columns', { panel, trigger }); },
            showFloatingPanel(panel, trigger) { hooks.floatingPanels.show('list-columns', { panel, trigger }); },
            syncContainerPlacement: noop,
        },
        filterFavouritesPresentationAdapter: {
            cloneFavouritesFloatingPanel(template) { return hooks.floatingPanels.clone('filter-favourites', template); },
            initialiseFavouritesFloatingPanel: initialiseVisibleFragment,
            positionFavouritesFloatingPanel(panel, trigger) { hooks.floatingPanels.position('filter-favourites', { panel, trigger }); },
            prepareFavouritesFloatingPanel(panel, trigger) { hooks.floatingPanels.prepare('filter-favourites', { panel, trigger }); },
            setFavouritesDropdownOpen(panel, open) { hooks.filters.setFavouritesOpen(panel, open); },
            showFavouritesFloatingPanel(panel, trigger) { hooks.floatingPanels.show('filter-favourites', { panel, trigger }); },
            syncFavouritesTriggerVisualState(trigger, state) { hooks.filters.syncFavouriteTrigger(trigger, state); },
            scheduleFilterPanelInitialisation(root) {
                schedule(() => initialiseVisibleFragment(root), 0);
            },
            setFilterPanelOpen(panel, open) { hooks.filters.setPanelOpen(panel, open); },
            showFavouritesToolbar: hooks.filters.showFavouritesToolbar,
            syncAddFilterVisibility: hooks.filters.setAddFilterVisible,
            syncFilterToggleVisualState: hooks.filters.syncFilterToggle,
        },
        rowActionMenuPresentationAdapter: {
            cloneFloatingMenu(template) { return hooks.floatingPanels.clone('row-actions', template); },
            positionFloatingMenu(panel, trigger) { hooks.floatingPanels.position('row-actions', { panel, trigger }); },
            prepareFloatingMenu(panel, trigger) { hooks.floatingPanels.prepare('row-actions', { panel, trigger }); },
            showFloatingMenu(panel, trigger) { hooks.floatingPanels.show('row-actions', { panel, trigger }); },
        },
    };
}
