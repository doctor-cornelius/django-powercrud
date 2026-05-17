import { OBJECT_LIST_ROOT_SELECTOR } from './selectors.js';

export function asElement(value) {
    if (value instanceof Element) {
        return value;
    }
    if (value instanceof Node && value.parentElement instanceof Element) {
        return value.parentElement;
    }
    return null;
}

export function queryAllWithSelf(root, selector) {
    if (root === document) {
        return Array.from(document.querySelectorAll(selector));
    }
    if (!(root instanceof Element)) {
        return [];
    }
    const matches = [];
    if (root.matches(selector)) {
        matches.push(root);
    }
    matches.push(...root.querySelectorAll(selector));
    return matches;
}

export function getAffectedObjectListRoots(scope = document) {
    if (scope === document) {
        return queryAllWithSelf(document, OBJECT_LIST_ROOT_SELECTOR);
    }
    if (!(scope instanceof Element)) {
        return [];
    }

    const roots = queryAllWithSelf(scope, OBJECT_LIST_ROOT_SELECTOR);
    if (roots.length) {
        return roots;
    }

    const closestRoot = scope.closest(OBJECT_LIST_ROOT_SELECTOR);
    return closestRoot ? [closestRoot] : [];
}

export function getObjectListRoot(node) {
    if (!(node instanceof Element)) {
        return null;
    }
    return node.closest(OBJECT_LIST_ROOT_SELECTOR);
}

export function getRootSwapTarget(root) {
    if (!(root instanceof Element)) {
        return root;
    }
    const originalTarget = root.dataset.powercrudOriginalTarget || '';
    return originalTarget || root;
}

export function isElementVisible(element) {
    if (!(element instanceof Element)) {
        return false;
    }
    return element.getClientRects().length > 0;
}
