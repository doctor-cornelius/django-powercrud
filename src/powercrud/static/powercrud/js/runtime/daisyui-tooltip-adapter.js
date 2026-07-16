import { TOOLTIP_TRIGGER_SELECTOR } from './selectors.js';
import { isElementVisible, queryAllWithSelf } from './dom.js';

// Private DaisyUI presentation adapter for Tippy-specific behavior. Core owns
// lifecycle ordering and exposes the existing public compatibility forwards.
export function createDaisyuiTooltipLifecycleAdapter(context) {
    const {
        global,
        documentObject,
        warnMissingDependency,
    } = context;

    const lazyCellTooltipRequests = new WeakMap();
    let tooltipResizeTimer = null;

    function getTippyCtor() {
        const ctor = global.tippy;
        if (typeof ctor !== 'function') {
            warnMissingDependency('tippy', 'window.tippy. Load Tippy.js before powercrud/js/powercrud.js');
            return null;
        }
        return ctor;
    }

    function isTooltipOverflowTarget(trigger) {
        return trigger?.dataset?.powercrudTooltip === 'overflow';
    }

    function isTooltipSemanticTarget(trigger) {
        return trigger?.dataset?.powercrudTooltip === 'semantic';
    }

    function isTooltipSemanticCellTarget(trigger) {
        return trigger?.dataset?.powercrudTooltip === 'semantic-cell';
    }

    function isLazyCellTooltipTarget(trigger) {
        return (
            isTooltipSemanticCellTarget(trigger)
            && trigger?.dataset?.powercrudTooltipMode === 'lazy'
        );
    }

    function isTooltipTriggerActive(trigger) {
        return (
            trigger instanceof HTMLElement
            && trigger.isConnected
            && (
                trigger.matches(':hover')
                || trigger.matches(':focus')
                || trigger.matches(':focus-within')
            )
        );
    }

    function getTooltipTheme(trigger) {
        if (isTooltipSemanticCellTarget(trigger)) {
            return 'powercrud-semantic-cell';
        }
        return 'powercrud';
    }

    function isTruncated(trigger) {
        if (!(trigger instanceof HTMLElement) || !isElementVisible(trigger)) {
            return false;
        }
        return (
            (trigger.scrollWidth - trigger.clientWidth) > 1
            || (trigger.scrollHeight - trigger.clientHeight) > 1
        );
    }

    function destroy(root = documentObject) {
        queryAllWithSelf(root, TOOLTIP_TRIGGER_SELECTOR).forEach(trigger => {
            if (trigger._tippy) {
                trigger._tippy.destroy();
            }
            lazyCellTooltipRequests.delete(trigger);
        });
    }

    function hide(root = documentObject) {
        queryAllWithSelf(root, TOOLTIP_TRIGGER_SELECTOR).forEach(trigger => {
            if (trigger._tippy) {
                trigger._tippy.hide();
            }
        });
    }

    function init(root = documentObject) {
        const tippyCtor = getTippyCtor();
        if (!tippyCtor) {
            return;
        }

        queryAllWithSelf(root, TOOLTIP_TRIGGER_SELECTOR).forEach(trigger => {
            if (!(trigger instanceof HTMLElement)) {
                return;
            }
            if (trigger._tippy) {
                trigger._tippy.destroy();
            }
            const isOverflowTarget = isTooltipOverflowTarget(trigger);
            const isSemanticTarget = isTooltipSemanticTarget(trigger);
            const isSemanticCellTarget = isTooltipSemanticCellTarget(trigger);
            const isLazyCellTarget = isLazyCellTooltipTarget(trigger);
            if (!isOverflowTarget && !isSemanticTarget && !isSemanticCellTarget) {
                return;
            }
            tippyCtor(trigger, {
                theme: getTooltipTheme(trigger),
                placement: 'top',
                onShow(instance) {
                    if (isLazyCellTarget) {
                        return handleLazyCellTooltipShow(instance);
                    }
                    if (!isOverflowTarget) {
                        return true;
                    }
                    return isTruncated(instance.reference);
                },
            });
        });
    }

    function handleLazyCellTooltipShow(instance) {
        const trigger = instance.reference;
        if (!(trigger instanceof HTMLElement)) {
            return false;
        }
        if (trigger.dataset.powercrudTooltipLazyReplay === 'true') {
            delete trigger.dataset.powercrudTooltipLazyReplay;
            return true;
        }
        if (trigger.dataset.powercrudTooltipLazyState === 'loaded') {
            return Boolean(trigger.getAttribute('data-tippy-content'));
        }
        if (trigger.dataset.powercrudTooltipLazyState === 'empty') {
            return false;
        }

        hydrateLazyCellTooltip(instance);
        return false;
    }

    async function hydrateLazyCellTooltip(instance) {
        const trigger = instance.reference;
        if (!(trigger instanceof HTMLElement) || !trigger.isConnected) {
            return;
        }

        const url = trigger.dataset.powercrudTooltipUrl || '';
        if (!url) {
            trigger.dataset.powercrudTooltipLazyState = 'empty';
            return;
        }

        let request = lazyCellTooltipRequests.get(trigger);
        if (!request) {
            trigger.dataset.powercrudTooltipLazyState = 'loading';
            request = global.fetch(url, {
                method: 'GET',
                credentials: 'same-origin',
                headers: {
                    Accept: 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                },
            }).then(response => {
                if (!response.ok) {
                    throw new Error(`Lazy tooltip request failed with ${response.status}`);
                }
                return response.json();
            }).finally(() => {
                lazyCellTooltipRequests.delete(trigger);
            });
            lazyCellTooltipRequests.set(trigger, request);
        }

        try {
            const payload = await request;
            if (!(trigger instanceof HTMLElement) || !trigger.isConnected) {
                return;
            }
            const tooltip = typeof payload?.tooltip === 'string' ? payload.tooltip.trim() : '';
            if (!tooltip) {
                trigger.dataset.powercrudTooltipLazyState = 'empty';
                trigger.setAttribute('data-tippy-content', '');
                instance.setContent('');
                return;
            }
            trigger.dataset.powercrudTooltipLazyState = 'loaded';
            trigger.setAttribute('data-tippy-content', tooltip);
            instance.setContent(tooltip);
            if (!isTooltipTriggerActive(trigger)) {
                instance.hide();
                return;
            }
            hide(documentObject);
            trigger.dataset.powercrudTooltipLazyReplay = 'true';
            instance.show();
        } catch {
            if (trigger instanceof HTMLElement && trigger.isConnected) {
                trigger.dataset.powercrudTooltipLazyState = 'empty';
                trigger.setAttribute('data-tippy-content', '');
                instance.setContent('');
            }
        }
    }

    function scheduleInit(root = documentObject, delay = 0) {
        global.setTimeout(() => {
            init(root);
        }, delay);
    }

    function scheduleResizeInit(root = documentObject, delay = 100) {
        if (tooltipResizeTimer) {
            global.clearTimeout(tooltipResizeTimer);
        }
        tooltipResizeTimer = global.setTimeout(() => init(root), delay);
    }

    return {
        destroy,
        hide,
        init,
        scheduleInit,
        scheduleResizeInit,
    };
}
