export function normaliseListUrl(listUrl, globalObject) {
    if (!listUrl) {
        return '';
    }
    try {
        return new URL(listUrl, globalObject.location.origin).pathname;
    } catch (_error) {
        return String(listUrl);
    }
}

export function currentLocationMatchesListUrl(listUrl, globalObject) {
    return normaliseListUrl(listUrl, globalObject) === globalObject.location.pathname;
}

export function sanitizeQueryString(queryString, ignoredParamNames) {
    const rawQueryString = String(queryString || '').replace(/^\?/, '');
    if (!rawQueryString) {
        return '';
    }

    const params = new URLSearchParams(rawQueryString);
    ignoredParamNames.forEach(name => params.delete(name));
    return params.toString();
}

export function collectSearchParams(search, options = {}) {
    const params = new URLSearchParams(search);
    const clean = {};
    const preservePage = options.preservePage === true;
    for (const [key, value] of params) {
        if (!value) {
            continue;
        }
        if (!preservePage && key === 'page') {
            continue;
        }
        if (key in clean) {
            if (Array.isArray(clean[key])) {
                clean[key].push(value);
            } else {
                clean[key] = [clean[key], value];
            }
            continue;
        }
        clean[key] = value;
    }
    return clean;
}

export function getSearchParamFromHref(href, name) {
    try {
        return new URL(href).searchParams.get(name) || '';
    } catch (_error) {
        return '';
    }
}
