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

    function copyInlineTomSelectPalette(instance) {
        const table = instance.control.closest('table[data-inline-enabled="true"]');
        if (!table) {
            return;
        }

        // Inline menus are appended to body for viewport-aware placement, so
        // copy the table's view-configured inline palette to the detached menu.
        const palette = global.getComputedStyle(table);
        for (const property of [
            '--pc-ts-option-active-bg',
            '--pc-ts-option-active-text',
            '--pc-ts-option-keyboard-bg',
            '--pc-ts-option-selected-bg',
            '--pc-ts-option-hover-bg',
        ]) {
            const value = palette.getPropertyValue(property).trim();
            if (value) {
                instance.dropdown.style.setProperty(property, value);
            }
        }
    }

    function positionInlineMultiselectDropdown(instance) {
        const controlRect = instance.control.getBoundingClientRect();
        const dropdown = instance.dropdown;
        const dropdownContent = instance.dropdown_content;
        const tableCell = instance.control.closest('td');
        if (tableCell) {
            // Inline dropdowns live under body to avoid table overflow. Copy the
            // table cell's computed size so downstream table typography applies
            // to both the control and the detached option list.
            dropdown.style.fontSize = global.getComputedStyle(tableCell).fontSize;
        }
        const viewportHeight = documentObject.documentElement.clientHeight || global.innerHeight;
        const viewportWidth = documentObject.documentElement.clientWidth || global.innerWidth;
        const viewportEdge = 8;
        const dropdownGap = 4;
        const spaceAbove = Math.max(0, controlRect.top - viewportEdge - dropdownGap);
        const spaceBelow = Math.max(0, viewportHeight - controlRect.bottom - viewportEdge - dropdownGap);
        const renderedHeight = dropdown.getBoundingClientRect().height;
        const opensUpward = spaceBelow < renderedHeight && spaceAbove >= spaceBelow;
        const availableSpace = opensUpward ? spaceAbove : spaceBelow;
        const contentHeight = dropdownContent.getBoundingClientRect().height;
        const dropdownChrome = Math.max(0, renderedHeight - contentHeight);
        const maxContentHeight = Math.max(0, Math.floor(availableSpace - dropdownChrome));
        const maxWidth = Math.max(0, viewportWidth - (viewportEdge * 2));
        const width = Math.min(controlRect.width, maxWidth);
        const left = Math.max(
            viewportEdge,
            Math.min(controlRect.left, viewportWidth - width - viewportEdge),
        );

        dropdownContent.style.maxHeight = `${maxContentHeight}px`;
        dropdown.style.margin = '0';
        dropdown.style.width = `${width}px`;
        dropdown.style.left = `${global.scrollX + left}px`;
        dropdown.classList.toggle('powercrud-inline-dropdown-upward', opensUpward);

        const positionedHeight = dropdown.getBoundingClientRect().height;
        const top = opensUpward
            ? controlRect.top - positionedHeight - dropdownGap
            : controlRect.bottom + dropdownGap;
        dropdown.style.top = `${global.scrollY + top}px`;
    }

    function enableInlineMultiselectDropdownPlacement(instance) {
        instance.on('dropdown_open', () => {
            global.requestAnimationFrame(() => positionInlineMultiselectDropdown(instance));
        });
    }

    function enableCompactMultiselectSummary(instance) {
        const summary = documentObject.createElement('span');
        summary.className = 'powercrud-compact-multiselect-summary';
        summary.setAttribute('aria-live', 'polite');
        instance.control.appendChild(summary);

        const refreshSummary = () => {
            const count = instance.items.length;
            summary.textContent = count ? `${count} selected` : '';
            summary.hidden = count === 0 || Boolean(instance.control_input?.value);
        };
        instance.on('item_add', refreshSummary);
        instance.on('item_remove', refreshSummary);
        instance.on('type', refreshSummary);
        instance.on('dropdown_open', refreshSummary);
        instance.on('dropdown_close', refreshSummary);
        instance.control_input?.addEventListener('input', refreshSummary);
        refreshSummary();
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
            maxOptions: 50,
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
        const isInlineSelect = Boolean(selectElement.closest(INLINE_ROW_SELECTOR));
        const isCompact = selectElement.getAttribute('data-powercrud-widget-variant') === 'compact';
        const settings = {
            create: false,
            maxItems: null,
            maxOptions: 50,
            closeAfterSelect: false,
            allowEmptyOption: true,
            hideSelected: false,
            placeholder,
            openOnFocus: true,
            plugins: isCompact
                ? {
                    checkbox_options: {},
                    clear_button: { title: 'Clear all selected options' },
                }
                : {
                    remove_button: {},
                    checkbox_options: {},
                    clear_button: { title: 'Clear all selected options' },
                },
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
        if (isInlineSelect) {
            copyInlineTomSelectPalette(instance);
            instance.wrapper.classList.add('powercrud-inline-multiselect');
            instance.dropdown.classList.add('powercrud-inline-multiselect-dropdown');
            enableInlineMultiselectDropdownPlacement(instance);
        }
        if (isCompact) {
            instance.wrapper.classList.add('powercrud-compact-multiselect');
            enableCompactMultiselectSummary(instance);
        }
        syncDisabledState(selectElement);
        hideNativeSelect(selectElement);
    }

    function destroy(selectElement, { restoreNative = true } = {}) {
        if (selectElement.tomselect) {
            selectElement.tomselect.destroy();
        }
        if (restoreNative) {
            restoreNativeSelect(selectElement);
        } else {
            hideNativeSelect(selectElement);
        }
    }

    return {
        destroy,
        enhanceMultiple,
        enhanceSingle,
        ensureAvailable,
    };
}
