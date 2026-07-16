import {
    SEARCHABLE_SELECT_ATTR,
    SEARCHABLE_MULTISELECT_ATTR,
} from './selectors.js';

export function createSearchableSelectRuntime(context) {
    const {
        documentObject,
        isElementVisible,
        ensureSearchableSelectAdapterAvailable,
        enhanceSearchableSelect,
        enhanceSearchableMultiselect,
        destroySearchableSelect,
    } = context;

    function isSearchableSelectCandidate(element) {
        return (
            element instanceof HTMLSelectElement
            && element.getAttribute(SEARCHABLE_SELECT_ATTR) === 'true'
            && !element.multiple
        );
    }

    function isSearchableMultiselectCandidate(element) {
        return (
            element instanceof HTMLSelectElement
            && element.getAttribute(SEARCHABLE_MULTISELECT_ATTR) === 'true'
            && element.multiple
        );
    }

    function syncTomSelectValue(selectElement) {
        if (!(selectElement instanceof HTMLSelectElement) || !selectElement.tomselect) {
            return;
        }

        if (typeof selectElement.tomselect.sync === 'function') {
            selectElement.tomselect.sync();
            return;
        }

        const selectedValue = selectElement.tomselect.getValue();
        if (selectElement.multiple) {
            const selectedValues = Array.isArray(selectedValue) ? selectedValue.map(String) : [];
            Array.from(selectElement.options).forEach(option => {
                option.selected = selectedValues.includes(option.value);
            });
            return;
        }

        const normalizedValue = Array.isArray(selectedValue)
            ? (selectedValue[0] ?? '')
            : (selectedValue ?? '');
        selectElement.value = String(normalizedValue);
    }

    function syncTomSelectValues(container) {
        if (!(container instanceof Element)) {
            return;
        }
        container.querySelectorAll('select').forEach(selectElement => {
            syncTomSelectValue(selectElement);
        });
    }

    function enhanceSingleCandidate(selectElement) {
        if (!isSearchableSelectCandidate(selectElement)) {
            return;
        }
        enhanceSearchableSelect(selectElement, isElementVisible(selectElement));
    }

    function enhanceMultipleCandidate(selectElement) {
        if (!isSearchableMultiselectCandidate(selectElement)) {
            return;
        }
        enhanceSearchableMultiselect(selectElement, isElementVisible(selectElement));
    }

    function initPowercrudSearchableSelects(root = documentObject) {
        if (!(root instanceof Element) && root !== documentObject) {
            return;
        }
        if (!ensureSearchableSelectAdapterAvailable()) {
            return;
        }

        const scope = root === documentObject ? documentObject : root;
        scope.querySelectorAll(`select[${SEARCHABLE_SELECT_ATTR}="true"]`).forEach(enhanceSingleCandidate);
        scope.querySelectorAll(`select[${SEARCHABLE_MULTISELECT_ATTR}="true"]`).forEach(enhanceMultipleCandidate);

        if (root instanceof HTMLSelectElement) {
            enhanceSingleCandidate(root);
            enhanceMultipleCandidate(root);
        }
    }

    function destroyPowercrudSearchableSelects(root = documentObject) {
        if (!(root instanceof Element) && root !== documentObject) {
            return;
        }
        const scope = root === documentObject ? documentObject : root;
        scope
            .querySelectorAll(`select[${SEARCHABLE_SELECT_ATTR}="true"], select[${SEARCHABLE_MULTISELECT_ATTR}="true"]`)
            .forEach(destroySearchableSelect);

        if (root instanceof HTMLSelectElement) {
            destroySearchableSelect(root);
        }
    }

    return {
        destroyPowercrudSearchableSelects,
        initPowercrudSearchableSelects,
        syncTomSelectValues,
    };
}
