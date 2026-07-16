import {
    INLINE_ROW_SELECTOR,
    NATIVE_STYLE_ATTR,
    NATIVE_TABINDEX_ATTR,
} from './selectors.js';

// Private DaisyUI presentation adapter for Tom Select-specific behavior. Core
// retains semantic discovery, value synchronization, and lifecycle ordering.
export function createDaisyuiSearchableSelectAdapter(context) {
    const {
        global,
        documentObject,
        warnMissingDependency,
    } = context;

    function getTomSelectCtor() {
        const ctor = global.TomSelect;
        if (!ctor) {
            warnMissingDependency('tomSelect', "window.TomSelect. Load Tom Select before powercrud/js/powercrud.js");
            return null;
        }
        return ctor;
    }

    function ensureAvailable() {
        return Boolean(getTomSelectCtor());
    }

    function syncDisabledState(selectElement) {
        if (!selectElement?.tomselect) {
            return;
        }
        if (selectElement.disabled) {
            selectElement.tomselect.disable();
            return;
        }
        selectElement.tomselect.enable();
    }

    function hideNativeSelect(selectElement) {
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

    function createInstance(selectElement, settings) {
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

    function normaliseControl(instance) {
        instance.wrapper.classList.remove('select', 'select-bordered', 'select-sm', 'select-md', 'select-lg');
        instance.control.classList.remove('select', 'select-bordered', 'select-sm', 'select-md', 'select-lg');
        instance.wrapper.classList.add('w-full');
        instance.control.classList.add('w-full');
    }

    function isFilterFavouritesSelect(selectElement) {
        return selectElement.getAttribute('data-powercrud-favourite-select') === 'true';
    }

    function normaliseFilterFavourites(selectElement) {
        if (!isFilterFavouritesSelect(selectElement) || !selectElement.tomselect) {
            return;
        }

        selectElement.tomselect.wrapper.classList.add('powercrud-filter-favourite-select');
        selectElement.tomselect.control.classList.add('powercrud-filter-favourite-select-control');
        selectElement.tomselect.dropdown.classList.add('powercrud-filter-favourite-select-dropdown');
    }

    function enhanceSingle(selectElement, isVisible) {
        if (selectElement.tomselect) {
            normaliseFilterFavourites(selectElement);
            syncDisabledState(selectElement);
            hideNativeSelect(selectElement);
            return;
        }
        if (!isVisible) {
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

        const instance = createInstance(selectElement, settings);
        if (!instance) {
            return;
        }

        normaliseControl(instance);
        normaliseFilterFavourites(selectElement);

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

        syncDisabledState(selectElement);
        hideNativeSelect(selectElement);
    }

    function enhanceMultiple(selectElement, isVisible) {
        if (selectElement.tomselect) {
            syncDisabledState(selectElement);
            hideNativeSelect(selectElement);
            return;
        }
        if (!isVisible) {
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

        const instance = createInstance(selectElement, settings);
        if (!instance) {
            return;
        }

        normaliseControl(instance);
        syncDisabledState(selectElement);
        hideNativeSelect(selectElement);
    }

    function destroy(selectElement) {
        if (selectElement.tomselect) {
            selectElement.tomselect.destroy();
        }
        restoreNativeSelect(selectElement);
    }

    return {
        destroy,
        enhanceMultiple,
        enhanceSingle,
        ensureAvailable,
    };
}
