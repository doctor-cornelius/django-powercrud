const startupInstallState = new WeakMap();

function getStartupInstallState(documentObject) {
    let state = startupInstallState.get(documentObject);
    if (!state) {
        state = {
            domReadyHandled: false,
            listenersInstalled: false,
            styleInstalled: false,
        };
        startupInstallState.set(documentObject, state);
    }
    return state;
}

function installSelectionSuppressionStyle(documentObject, rangeSelectClass) {
    const selectionSuppressionStyle = documentObject.createElement('style');
    selectionSuppressionStyle.textContent = `
        body.${rangeSelectClass},
        body.${rangeSelectClass} * {
            user-select: none !important;
        }
    `;
    documentObject.head.appendChild(selectionSuppressionStyle);
}

/**
 * Install once-only PowerCRUD startup style and global event listeners.
 *
 * @param {object} options - Installation options.
 * @param {Window} options.globalObject - Window object that receives window events.
 * @param {Document} options.documentObject - Document that receives document events.
 * @param {string} options.rangeSelectClass - Body class that suppresses text selection.
 * @param {object} options.handlers - Event handlers in existing listener order.
 */
export function installPowercrudGlobalListeners({
    globalObject,
    documentObject,
    rangeSelectClass,
    handlers,
}) {
    const state = getStartupInstallState(documentObject);

    if (!state.styleInstalled) {
        installSelectionSuppressionStyle(documentObject, rangeSelectClass);
        state.styleInstalled = true;
    }

    if (state.listenersInstalled) {
        return;
    }
    state.listenersInstalled = true;

    const handleDOMContentLoadedOnce = () => {
        if (state.domReadyHandled) {
            return;
        }
        state.domReadyHandled = true;
        handlers.handleDOMContentLoaded();
    };

    // Listener order is behavioural: capture-phase guards run before the
    // delegated bubble handlers, and HTMX teardown runs before re-init hooks.
    documentObject.addEventListener('DOMContentLoaded', handleDOMContentLoadedOnce);
    globalObject.addEventListener('pageshow', handlers.handlePageShow);
    documentObject.addEventListener('pointerdown', handlers.handlePointerDownCapture, true);
    documentObject.addEventListener('click', handlers.handleDisabledActionClickCapture, true);
    documentObject.addEventListener('click', handlers.handleTooltipClickCapture, true);
    documentObject.addEventListener('click', handlers.handleInlineDocumentClickCapture, true);
    documentObject.addEventListener('click', handlers.handleModalClassClickCapture, true);
    documentObject.addEventListener('focusin', handlers.handleFocusInCapture, true);
    globalObject.addEventListener('pagehide', handlers.handlePageHide);
    documentObject.addEventListener('click', handlers.handleDocumentClick);
    documentObject.addEventListener('toggle', handlers.handleDocumentToggleCapture, true);
    documentObject.addEventListener('keydown', handlers.handleDocumentKeydown);
    documentObject.addEventListener('scroll', handlers.handleDocumentScrollCapture, true);
    documentObject.addEventListener('click', handlers.handleRowSelectionClickCapture, true);
    documentObject.addEventListener('mousedown', handlers.handleRowSelectionMouseDownCapture, true);
    documentObject.addEventListener('change', handlers.handleDocumentChange);
    documentObject.addEventListener('input', handlers.handleFilterInput);
    documentObject.addEventListener('change', handlers.handleFilterChange);
    documentObject.addEventListener('submit', handlers.handleDocumentSubmitCapture, true);
    documentObject.addEventListener('htmx:beforeRequest', handlers.handleHtmxBeforeRequest);
    documentObject.addEventListener('htmx:configRequest', handlers.handleHtmxConfigRequest);
    documentObject.body.addEventListener('bulkEditSuccess', handlers.handleBulkEditSuccess);
    documentObject.body.addEventListener('bulkEditQueued', handlers.handleBulkEditQueued);
    documentObject.body.addEventListener('powercrud:favourite-saved', handlers.handleFavouriteSaved);
    documentObject.body.addEventListener('powercrud:favourite-updated', handlers.handleFavouriteUpdated);
    documentObject.body.addEventListener('powercrud:favourite-deleted', handlers.handleFavouriteDeleted);
    documentObject.body.addEventListener('refreshTable', handlers.handleRefreshTable);
    documentObject.addEventListener('htmx:beforeSwap', handlers.handleHtmxBeforeSwap);
    documentObject.addEventListener('htmx:afterSwap', handlers.handleHtmxAfterSwap);
    documentObject.addEventListener('htmx:afterSettle', handlers.handleHtmxAfterSettle);
    documentObject.addEventListener('htmx:beforeRequest', handlers.handleInlineHtmxBeforeRequest);
    documentObject.addEventListener('htmx:afterRequest', handlers.handleHtmxAfterRequest);
    documentObject.addEventListener('htmx:responseError', handlers.handleHtmxResponseError);
    documentObject.body.addEventListener('inline-row-locked', handlers.handleInlineRowLocked);
    documentObject.body.addEventListener('inline-row-forbidden', handlers.handleInlineRowForbidden);
    documentObject.body.addEventListener('inline-row-saved', handlers.handleInlineRowSaved);
    documentObject.body.addEventListener('inline-row-error', handlers.handleInlineRowError);
    globalObject.addEventListener('resize', handlers.handleWindowResize);
    globalObject.addEventListener('scroll', handlers.handleWindowScrollCapture, true);

    // A Vite entry can finish loading after DOMContentLoaded, while its module
    // body still has vendor globals to assign. Queue the same once-only path so
    // those assignments finish before adapter hooks initialise.
    const initialiseWhenReady = () => {
        if (documentObject.body) {
            handleDOMContentLoadedOnce();
        }
    };
    if (documentObject.readyState !== 'loading') {
        if (typeof globalObject.queueMicrotask === 'function') {
            globalObject.queueMicrotask(initialiseWhenReady);
        } else {
            globalObject.setTimeout(initialiseWhenReady, 0);
        }
    } else {
        globalObject.setTimeout(initialiseWhenReady, 0);
    }
}
