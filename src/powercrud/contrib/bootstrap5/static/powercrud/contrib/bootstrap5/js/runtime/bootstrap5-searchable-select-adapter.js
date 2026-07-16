import { INLINE_ROW_SELECTOR, NATIVE_STYLE_ATTR, NATIVE_TABINDEX_ATTR } from '../../../../../../../../static/powercrud/js/runtime/selectors.js';

/** Adapt the shared searchable-select lifecycle to Bootstrap-compatible Tom Select markup. */
export function createBootstrap5SearchableSelectAdapter({ global, documentObject, warnMissingDependency }) {
    function getTomSelectConstructor() {
        const constructor = global.TomSelect;
        if (!constructor) {
            warnMissingDependency('tomSelect', 'window.TomSelect. Load Tom Select before the Bootstrap PowerCRUD entry.');
            return null;
        }
        return constructor;
    }

    function ensureAvailable() {
        return Boolean(getTomSelectConstructor());
    }

    function hideNativeSelect(select) {
        if (!select.hasAttribute(NATIVE_STYLE_ATTR)) {
            select.setAttribute(NATIVE_STYLE_ATTR, select.getAttribute('style') || '');
        }
        if (!select.hasAttribute(NATIVE_TABINDEX_ATTR)) {
            select.setAttribute(NATIVE_TABINDEX_ATTR, select.getAttribute('tabindex') || '');
        }
        Object.assign(select.style, { display: 'none', visibility: 'hidden', position: 'absolute', width: '1px', height: '1px', pointerEvents: 'none' });
        select.classList.add('ts-hidden-accessible');
        select.hidden = true;
        select.setAttribute('tabindex', '-1');
        select.setAttribute('aria-hidden', 'true');
    }

    function restoreNativeSelect(select) {
        if (select.hasAttribute(NATIVE_STYLE_ATTR)) {
            const original = select.getAttribute(NATIVE_STYLE_ATTR) || '';
            if (original) {
                select.setAttribute('style', original);
            } else {
                select.removeAttribute('style');
            }
            select.removeAttribute(NATIVE_STYLE_ATTR);
        }
        select.classList.remove('ts-hidden-accessible');
        select.hidden = false;
        if (select.hasAttribute(NATIVE_TABINDEX_ATTR)) {
            const original = select.getAttribute(NATIVE_TABINDEX_ATTR) || '';
            if (original) {
                select.setAttribute('tabindex', original);
            } else {
                select.removeAttribute('tabindex');
            }
            select.removeAttribute(NATIVE_TABINDEX_ATTR);
        }
        select.removeAttribute('aria-hidden');
    }

    function normalise(instance) {
        instance.wrapper.classList.add('powercrud-bootstrap-tomselect');
        instance.control.classList.add('form-control');
    }

    function normaliseFilterFavourites(select) {
        if (
            select.getAttribute('data-powercrud-favourite-select') !== 'true'
            || !select.tomselect
        ) {
            return;
        }
        select.tomselect.wrapper.classList.add('powercrud-filter-favourite-select');
        select.tomselect.control.classList.add('powercrud-filter-favourite-select-control');
        select.tomselect.dropdown.classList.add('powercrud-filter-favourite-select-dropdown');
    }

    function syncDisabled(select) {
        if (!select.tomselect) {
            return;
        }
        if (select.disabled) {
            select.tomselect.disable();
        } else {
            select.tomselect.enable();
        }
    }

    function create(select, settings) {
        const TomSelect = getTomSelectConstructor();
        if (!TomSelect) {
            return null;
        }
        try {
            return new TomSelect(select, settings);
        } catch (error) {
            if (!settings.plugins?.length) {
                throw error;
            }
            const fallback = { ...settings };
            delete fallback.plugins;
            return new TomSelect(select, fallback);
        }
    }

    function enhance(select, visible, multiple) {
        if (select.tomselect) {
            normalise(select.tomselect);
            normaliseFilterFavourites(select);
            syncDisabled(select);
            hideNativeSelect(select);
            return;
        }
        if (!visible) {
            return;
        }
        const isInlineSelect = Boolean(select.closest(INLINE_ROW_SELECTOR));
        const settings = {
            create: false,
            maxItems: multiple ? null : 1,
            maxOptions: null,
            closeAfterSelect: !multiple,
            allowEmptyOption: true,
            hideSelected: false,
            openOnFocus: true,
            placeholder: select.getAttribute('data-powercrud-searchable-placeholder') || '',
        };
        if (!multiple) {
            settings.onType = function onType(query) {
                if (this.items.length === 0) {
                    return;
                }
                this.clear(true);
                this.setTextboxValue(query);
                this.refreshOptions(true);
            };
        }
        if (multiple) {
            settings.plugins = ['remove_button'];
        }
        if (!select.closest('[data-powercrud-modal]')) {
            settings.dropdownParent = 'body';
        }
        const instance = create(select, settings);
        if (!instance) {
            return;
        }
        normalise(instance);
        normaliseFilterFavourites(select);
        if (isInlineSelect && !multiple) {
            instance.dropdown.classList.add('powercrud-inline-single-dropdown');
            instance.on('dropdown_open', function onInlineDropdownOpen() {
                const controlWidth = Math.ceil(instance.control.getBoundingClientRect().width);
                const viewportMax = Math.max(240, global.innerWidth - 32);
                const desiredWidth = Math.min(Math.max(controlWidth, 320), viewportMax);
                instance.dropdown.style.setProperty('min-width', `${desiredWidth}px`, 'important');
            });
        }
        syncDisabled(select);
        hideNativeSelect(select);
    }

    function destroy(select) {
        select.tomselect?.destroy();
        restoreNativeSelect(select);
    }

    return {
        destroy,
        enhanceMultiple(select, visible) { enhance(select, visible, true); },
        enhanceSingle(select, visible) { enhance(select, visible, false); },
        ensureAvailable,
    };
}
