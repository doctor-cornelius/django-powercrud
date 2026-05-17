import {
    SEARCHABLE_SELECT_ATTR,
    SEARCHABLE_MULTISELECT_ATTR,
    NATIVE_TABINDEX_ATTR,
    NATIVE_STYLE_ATTR,
    INLINE_ROW_SELECTOR,
} from './selectors.js';

export function createSearchableSelectRuntime(context) {
    const {
        global,
        documentObject,
        warnMissingDependency,
        isElementVisible,
    } = context;

    function getTomSelectCtor() {
        const ctor = global.TomSelect;
        if (!ctor) {
            warnMissingDependency('tomSelect', "window.TomSelect. Load Tom Select before powercrud/js/powercrud.js");
            return null;
        }
        return ctor;
    }

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

    function syncTomSelectDisabledState(selectElement) {
        if (!selectElement?.tomselect) {
            return;
        }
        if (selectElement.disabled) {
            selectElement.tomselect.disable();
            return;
        }
        selectElement.tomselect.enable();
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

    function hideNativeSelect(selectElement) {
        if (!(selectElement instanceof HTMLSelectElement)) {
            return;
        }
        // Keep enough original native state to restore the select before HTMX
        // removes or reuses the fragment that Tom Select enhanced.
        if (!selectElement.hasAttribute(NATIVE_STYLE_ATTR)) {
            selectElement.setAttribute(NATIVE_STYLE_ATTR, selectElement.getAttribute('style') || '');
        }
        if (!selectElement.hasAttribute(NATIVE_TABINDEX_ATTR)) {
            const current = selectElement.getAttribute('tabindex');
            selectElement.setAttribute(NATIVE_TABINDEX_ATTR, current === null ? '' : current);
        }
        selectElement.style.setProperty('display', 'none', 'important');
        selectElement.style.setProperty('visibility', 'hidden', 'important');
        selectElement.style.setProperty('position', 'absolute', 'important');
        selectElement.style.setProperty('width', '1px', 'important');
        selectElement.style.setProperty('height', '1px', 'important');
        selectElement.style.setProperty('pointer-events', 'none', 'important');
        selectElement.classList.add('ts-hidden-accessible');
        selectElement.hidden = true;
        selectElement.setAttribute('tabindex', '-1');
        selectElement.setAttribute('aria-hidden', 'true');
    }

    function restoreNativeSelect(selectElement) {
        if (!(selectElement instanceof HTMLSelectElement)) {
            return;
        }
        if (selectElement.hasAttribute(NATIVE_STYLE_ATTR)) {
            const originalStyle = selectElement.getAttribute(NATIVE_STYLE_ATTR) || '';
            if (originalStyle) {
                selectElement.setAttribute('style', originalStyle);
            } else {
                selectElement.removeAttribute('style');
            }
            selectElement.removeAttribute(NATIVE_STYLE_ATTR);
        }
        selectElement.classList.remove('ts-hidden-accessible');
        selectElement.hidden = false;
        if (selectElement.hasAttribute(NATIVE_TABINDEX_ATTR)) {
            const original = selectElement.getAttribute(NATIVE_TABINDEX_ATTR);
            if (original) {
                selectElement.setAttribute('tabindex', original);
            } else {
                selectElement.removeAttribute('tabindex');
            }
            selectElement.removeAttribute(NATIVE_TABINDEX_ATTR);
        }
        selectElement.removeAttribute('aria-hidden');
    }

    function createTomSelectInstance(selectElement, settings) {
        const TomSelectCtor = getTomSelectCtor();
        if (!TomSelectCtor) {
            return null;
        }

        try {
            return new TomSelectCtor(selectElement, settings);
        } catch (error) {
            // Older or custom Tom Select builds may not include optional
            // plugins. Fall back without plugins rather than dropping the field.
            if (!settings.plugins || settings.plugins.length === 0) {
                throw error;
            }

            const fallbackSettings = { ...settings };
            delete fallbackSettings.plugins;
            return new TomSelectCtor(selectElement, fallbackSettings);
        }
    }

    function normaliseTomSelectControl(instance) {
        instance.wrapper.classList.remove('select', 'select-bordered', 'select-sm', 'select-md', 'select-lg');
        instance.control.classList.remove('select', 'select-bordered', 'select-sm', 'select-md', 'select-lg');
        instance.wrapper.classList.add('w-full');
        instance.control.classList.add('w-full');
    }

    function isFilterFavouritesSelect(selectElement) {
        return (
            selectElement instanceof HTMLSelectElement
            && selectElement.getAttribute('data-powercrud-favourite-select') === 'true'
        );
    }

    function normaliseFilterFavouritesTomSelect(selectElement) {
        if (!isFilterFavouritesSelect(selectElement) || !selectElement.tomselect) {
            return;
        }

        selectElement.tomselect.wrapper.classList.add('powercrud-filter-favourite-select');
        selectElement.tomselect.control.classList.add('powercrud-filter-favourite-select-control');
        selectElement.tomselect.dropdown.classList.add('powercrud-filter-favourite-select-dropdown');
    }

    function enhanceSearchableSelect(selectElement) {
        if (!isSearchableSelectCandidate(selectElement)) {
            return;
        }
        if (selectElement.tomselect) {
            normaliseFilterFavouritesTomSelect(selectElement);
            syncTomSelectDisabledState(selectElement);
            hideNativeSelect(selectElement);
            return;
        }
        if (!isElementVisible(selectElement)) {
            return;
        }

        const placeholder = selectElement.getAttribute('data-powercrud-searchable-placeholder') || '';
        const dialogElement = selectElement.closest('dialog');
        const isInlineSelect = Boolean(selectElement.closest(INLINE_ROW_SELECTOR));
        const isFavouritesSelect = isFilterFavouritesSelect(selectElement);
        // Inline and favourites selects get specialised classes/width handling
        // because they live in constrained floating or table-cell contexts.
        const settings = {
            create: false,
            maxItems: 1,
            maxOptions: null,
            closeAfterSelect: true,
            allowEmptyOption: true,
            placeholder,
            openOnFocus: true,
            onType(query) {
                if (this.items.length === 0) {
                    return;
                }
                this.clear(true);
                this.setTextboxValue(query);
                this.refreshOptions(true);
            },
        };
        if (!dialogElement) {
            settings.dropdownParent = 'body';
        }

        const instance = createTomSelectInstance(selectElement, settings);
        if (!instance) {
            return;
        }

        normaliseTomSelectControl(instance);
        normaliseFilterFavouritesTomSelect(selectElement);

        if (isInlineSelect) {
            instance.dropdown.classList.add('powercrud-inline-single-dropdown');
            instance.on('dropdown_open', function () {
                const controlWidth = Math.ceil(instance.control.getBoundingClientRect().width);
                const viewportMax = Math.max(240, global.innerWidth - 32);
                const desiredWidth = Math.min(Math.max(controlWidth, 320), viewportMax);
                instance.dropdown.style.setProperty('min-width', `${desiredWidth}px`, 'important');
            });
        }

        if (!isInlineSelect && !isFavouritesSelect) {
            instance.wrapper.classList.add('powercrud-clearable-single');
        }

        if (!isInlineSelect && !isFavouritesSelect && !instance.control.querySelector('.clear-button')) {
            const clearButton = documentObject.createElement('button');
            clearButton.type = 'button';
            clearButton.className = 'clear-button';
            clearButton.title = 'Clear';
            clearButton.setAttribute('aria-label', 'Clear selection');
            clearButton.innerHTML = '&times;';
            clearButton.addEventListener('click', event => {
                if (instance.isLocked) {
                    return;
                }
                instance.clear(true);
                instance.setTextboxValue('');
                instance.refreshOptions(false);
                selectElement.dispatchEvent(new Event('change', { bubbles: true }));
                event.preventDefault();
                event.stopPropagation();
                instance.focus();
            });
            if (instance.control_input && instance.control_input.parentElement === instance.control) {
                instance.control.insertBefore(clearButton, instance.control_input);
            } else {
                instance.control.appendChild(clearButton);
            }
        }

        syncTomSelectDisabledState(selectElement);
        hideNativeSelect(selectElement);
    }

    function enhanceSearchableMultiselect(selectElement) {
        if (!isSearchableMultiselectCandidate(selectElement)) {
            return;
        }
        if (selectElement.tomselect) {
            syncTomSelectDisabledState(selectElement);
            hideNativeSelect(selectElement);
            return;
        }
        if (!isElementVisible(selectElement)) {
            return;
        }

        const placeholder = selectElement.getAttribute('data-powercrud-searchable-placeholder') || '';
        const dialogElement = selectElement.closest('dialog');
        const settings = {
            create: false,
            maxItems: null,
            maxOptions: null,
            closeAfterSelect: false,
            allowEmptyOption: true,
            hideSelected: false,
            placeholder,
            openOnFocus: true,
            plugins: ['remove_button'],
            onItemAdd() {
                this.setTextboxValue('');
                this.refreshOptions(true);
                selectElement.dispatchEvent(new Event('change', { bubbles: true }));
            },
            onItemRemove() {
                this.setTextboxValue('');
                this.refreshOptions(true);
                selectElement.dispatchEvent(new Event('change', { bubbles: true }));
            },
        };
        if (!dialogElement) {
            settings.dropdownParent = 'body';
        }

        const instance = createTomSelectInstance(selectElement, settings);
        if (!instance) {
            return;
        }

        normaliseTomSelectControl(instance);
        syncTomSelectDisabledState(selectElement);
        hideNativeSelect(selectElement);
    }

    function initPowercrudSearchableSelects(root = documentObject) {
        if (!(root instanceof Element) && root !== documentObject) {
            return;
        }

        const TomSelectCtor = getTomSelectCtor();
        if (!TomSelectCtor) {
            return;
        }

        const scope = root === documentObject ? documentObject : root;
        scope.querySelectorAll(`select[${SEARCHABLE_SELECT_ATTR}="true"]`).forEach(enhanceSearchableSelect);
        scope.querySelectorAll(`select[${SEARCHABLE_MULTISELECT_ATTR}="true"]`).forEach(enhanceSearchableMultiselect);

        if (root instanceof HTMLSelectElement) {
            enhanceSearchableSelect(root);
            enhanceSearchableMultiselect(root);
        }
    }

    function destroyPowercrudSearchableSelects(root = documentObject) {
        if (!(root instanceof Element) && root !== documentObject) {
            return;
        }
        const scope = root === documentObject ? documentObject : root;
        scope
            .querySelectorAll(`select[${SEARCHABLE_SELECT_ATTR}="true"], select[${SEARCHABLE_MULTISELECT_ATTR}="true"]`)
            .forEach(selectElement => {
                if (selectElement.tomselect) {
                    selectElement.tomselect.destroy();
                }
                restoreNativeSelect(selectElement);
            });

        if (root instanceof HTMLSelectElement) {
            if (root.tomselect) {
                root.tomselect.destroy();
            }
            restoreNativeSelect(root);
        }
    }

    return {
        destroyPowercrudSearchableSelects,
        initPowercrudSearchableSelects,
        syncTomSelectValues,
    };
}
