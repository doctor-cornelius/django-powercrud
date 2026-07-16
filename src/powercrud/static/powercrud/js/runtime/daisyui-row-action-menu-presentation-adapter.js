// Private DaisyUI presentation adapter for the floating row-action menu shell
// and geometry. Core retains lazy state, semantic hooks, HTMX/modal execution,
// active references, and every detached-menu lifecycle decision.
export function createDaisyuiRowActionMenuPresentationAdapter(context) {
    const { global } = context;

    function cloneFloatingMenu(template) {
        if (!(template instanceof HTMLElement)) {
            return null;
        }
        const menu = template.firstElementChild?.cloneNode(true);
        return menu instanceof HTMLElement ? menu : null;
    }

    function prepareFloatingMenu(menu) {
        if (!(menu instanceof HTMLElement)) {
            return false;
        }
        menu.style.position = 'fixed';
        menu.style.visibility = 'hidden';
        menu.style.pointerEvents = 'none';
        return true;
    }

    function positionFloatingMenu(menu, trigger) {
        if (!(menu instanceof HTMLElement) || !(trigger instanceof HTMLElement)) {
            return;
        }

        const viewportPadding = 8;
        const menuGap = 4;
        const triggerRect = trigger.getBoundingClientRect();
        const menuRect = menu.getBoundingClientRect();
        const spaceBelow = global.innerHeight - triggerRect.bottom - viewportPadding;
        const spaceAbove = triggerRect.top - viewportPadding;
        const shouldOpenUpward = menuRect.height > spaceBelow && spaceAbove > spaceBelow;

        let top = shouldOpenUpward
            ? triggerRect.top - menuRect.height - menuGap
            : triggerRect.bottom + menuGap;
        let left = triggerRect.right - menuRect.width;

        top = Math.max(
            viewportPadding,
            Math.min(top, global.innerHeight - menuRect.height - viewportPadding),
        );
        left = Math.max(
            viewportPadding,
            Math.min(left, global.innerWidth - menuRect.width - viewportPadding),
        );

        menu.style.top = `${top}px`;
        menu.style.left = `${left}px`;
    }

    function showFloatingMenu(menu) {
        if (!(menu instanceof HTMLElement)) {
            return;
        }
        menu.style.visibility = '';
        menu.style.pointerEvents = '';
    }

    return {
        cloneFloatingMenu,
        positionFloatingMenu,
        prepareFloatingMenu,
        showFloatingMenu,
    };
}
