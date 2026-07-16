import { TOOLTIP_TRIGGER_SELECTOR } from '../../../../../../../../static/powercrud/js/runtime/selectors.js';

const BOOTSTRAP_TOOLTIP_SELECTOR = `${TOOLTIP_TRIGGER_SELECTOR}, [data-powercrud-tooltip][data-bs-title]`;

/** Adapt PowerCRUD tooltip semantics to Bootstrap Tooltip instances. */
export function createBootstrap5TooltipLifecycleAdapter({ global, documentObject, warnMissingDependency }) {
    let resizeTimer = null;
    const overflowListeners = new WeakSet();

    function getTooltipConstructor() {
        const constructor = global.bootstrap?.Tooltip;
        if (typeof constructor !== 'function') {
            warnMissingDependency('bootstrap', 'window.bootstrap.Tooltip. Load Bootstrap before the Bootstrap PowerCRUD entry.');
            return null;
        }
        return constructor;
    }

    function isVisible(element) {
        return element instanceof HTMLElement && element.isConnected && element.getClientRects().length > 0;
    }

    function query(root) {
        if (!(root instanceof Element) && root !== documentObject) {
            return [];
        }
        const descendants = Array.from(root.querySelectorAll(BOOTSTRAP_TOOLTIP_SELECTOR));
        return root instanceof Element && root.matches(BOOTSTRAP_TOOLTIP_SELECTOR) ? [root, ...descendants] : descendants;
    }

    function isOverflowTarget(trigger) {
        return trigger.dataset.powercrudTooltip === 'overflow';
    }

    function init(root = documentObject) {
        const Tooltip = getTooltipConstructor();
        if (!Tooltip) {
            return;
        }
        query(root).forEach(trigger => {
            if (!(trigger instanceof HTMLElement)) {
                return;
            }
            // Reuse an active instance so repeated HTMX initialization cannot
            // dispose Bootstrap's trigger state while a hover or focus event is pending.
            Tooltip.getOrCreateInstance(trigger, {
                boundary: documentObject.body,
                title: () => trigger.getAttribute('data-bs-title') || trigger.getAttribute('data-tippy-content') || '',
                trigger: 'hover focus',
            });
            if (!overflowListeners.has(trigger)) {
                trigger.addEventListener('show.bs.tooltip', event => {
                    if (isOverflowTarget(trigger) && (!isVisible(trigger) || trigger.scrollWidth - trigger.clientWidth <= 1)) {
                        event.preventDefault();
                    }
                });
                overflowListeners.add(trigger);
            }
        });
    }

    function destroy(root = documentObject) {
        const Tooltip = getTooltipConstructor();
        query(root).forEach(trigger => Tooltip?.getInstance(trigger)?.dispose());
    }

    function hide(root = documentObject) {
        const Tooltip = getTooltipConstructor();
        query(root).forEach(trigger => Tooltip?.getInstance(trigger)?.hide());
    }

    function scheduleInit(root = documentObject, delay = 0) {
        global.setTimeout(() => init(root), delay);
    }

    function scheduleResizeInit(root = documentObject, delay = 100) {
        if (resizeTimer) {
            global.clearTimeout(resizeTimer);
        }
        resizeTimer = global.setTimeout(() => init(root), delay);
    }

    return { destroy, hide, init, scheduleInit, scheduleResizeInit };
}
