function getListUrl(root, globalObject) {
    return root?.dataset?.powercrudListUrl || globalObject.location.pathname || 'default';
}

export function buildRawStorageKey(prefix, root, globalObject) {
    return `${prefix}${getListUrl(root, globalObject)}`;
}

export function buildPathStorageKey(prefix, root, globalObject) {
    const listUrl = getListUrl(root, globalObject);
    try {
        const url = new URL(listUrl, globalObject.location.origin);
        return `${prefix}${url.pathname}`;
    } catch (_error) {
        return `${prefix}${listUrl}`;
    }
}

export function buildExplicitOrPathStorageKey(prefix, explicitKey, root, globalObject) {
    if (explicitKey) {
        return `${prefix}${explicitKey}`;
    }
    return buildPathStorageKey(prefix, root, globalObject);
}

export function getSessionStorageItem(globalObject, key) {
    return globalObject.sessionStorage?.getItem(key) || '';
}

export function setSessionStorageItem(globalObject, key, value) {
    globalObject.sessionStorage?.setItem(key, value);
}

export function removeSessionStorageItem(globalObject, key) {
    globalObject.sessionStorage?.removeItem(key);
}

export function getLocalStorageJsonArray(globalObject, key, normalizeItems) {
    try {
        const rawValue = globalObject.localStorage?.getItem(key);
        if (!rawValue) {
            return [];
        }

        const parsedValue = JSON.parse(rawValue);
        if (!Array.isArray(parsedValue)) {
            return [];
        }
        return normalizeItems(parsedValue);
    } catch (_error) {
        return [];
    }
}

export function setLocalStorageJsonArray(globalObject, key, values) {
    if (!values.length) {
        globalObject.localStorage?.removeItem(key);
        return;
    }

    globalObject.localStorage?.setItem(key, JSON.stringify(values));
}
