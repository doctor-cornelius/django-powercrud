import { asElement } from './dom.js';

export function getHtmxInstance(globalObject, warnMissingDependency) {
    const htmx = globalObject.htmx;
    if (!htmx?.ajax) {
        warnMissingDependency('htmx', 'window.htmx. Load HTMX before powercrud/js/powercrud.js');
        return null;
    }
    return htmx;
}

export function getHtmxEventRoots(event) {
    const roots = [];
    const detail = event?.detail || {};
    const eventTarget = asElement(event?.target);

    if (detail.elt instanceof Element) {
        roots.push(detail.elt);
    }
    if (detail.target instanceof Element && detail.target !== detail.elt) {
        roots.push(detail.target);
    }
    if (eventTarget && !roots.includes(eventTarget)) {
        roots.push(eventTarget);
    }

    return roots;
}
