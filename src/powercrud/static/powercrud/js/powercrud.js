(function powercrudRuntime(global) {
    'use strict';

    if (global.__powercrudRuntimeLoaded) {
        return;
    }
    global.__powercrudRuntimeLoaded = true;

    const SEARCHABLE_SELECT_ATTR = 'data-powercrud-searchable-select';
    const SEARCHABLE_MULTISELECT_ATTR = 'data-powercrud-searchable-multiselect';
    const NATIVE_TABINDEX_ATTR = 'data-powercrud-native-tabindex';
    const NATIVE_STYLE_ATTR = 'data-powercrud-native-style';

    const warnedDeps = {
        htmx: false,
        tippy: false,
        tomSelect: false,
    };

    function warnMissingDependency(name, detail) {
        if (warnedDeps[name]) {
            return;
        }
        warnedDeps[name] = true;
        console.warn(`PowerCRUD frontend: missing ${detail}.`);
    }

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

    function isElementVisible(element) {
        if (!(element instanceof Element)) {
            return false;
        }
        return element.getClientRects().length > 0;
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

    function hideNativeSelect(selectElement) {
        if (!(selectElement instanceof HTMLSelectElement)) {
            return;
        }
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
            if (!settings.plugins || settings.plugins.length === 0) {
                throw error;
            }

            // If plugin registration is missing (common in manual installs that use
            // core Tom Select without explicit plugin setup), retry without plugins
            // so the field remains usable.
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

    function enhanceSearchableSelect(selectElement) {
        if (!isSearchableSelectCandidate(selectElement)) {
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
        const isInlineSelect = Boolean(selectElement.closest('[data-inline-row="true"]'));
        const settings = {
            create: false,
            maxItems: 1,
            maxOptions: null,
            closeAfterSelect: true,
            allowEmptyOption: true,
            placeholder,
            openOnFocus: true,
            // Improve single-select search UX: once user types, drop the existing
            // selected item so the textbox contains only the new query.
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

        if (isInlineSelect) {
            instance.dropdown.classList.add('powercrud-inline-single-dropdown');
            instance.on('dropdown_open', function () {
                const controlWidth = Math.ceil(instance.control.getBoundingClientRect().width);
                const viewportMax = Math.max(240, window.innerWidth - 32);
                const desiredWidth = Math.min(Math.max(controlWidth, 320), viewportMax);
                instance.dropdown.style.setProperty('min-width', `${desiredWidth}px`, 'important');
            });
        }

        if (!isInlineSelect) {
            instance.wrapper.classList.add('powercrud-clearable-single');
        }

        if (!isInlineSelect && !instance.control.querySelector('.clear-button')) {
            const clearButton = document.createElement('button');
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

    function initPowercrudSearchableSelects(root = document) {
        if (!(root instanceof Element) && root !== document) {
            return;
        }

        const TomSelectCtor = getTomSelectCtor();
        if (!TomSelectCtor) {
            return;
        }

        const scope = root === document ? document : root;
        scope.querySelectorAll(`select[${SEARCHABLE_SELECT_ATTR}="true"]`).forEach(enhanceSearchableSelect);
        scope.querySelectorAll(`select[${SEARCHABLE_MULTISELECT_ATTR}="true"]`).forEach(enhanceSearchableMultiselect);

        if (root instanceof HTMLSelectElement) {
            enhanceSearchableSelect(root);
            enhanceSearchableMultiselect(root);
        }
    }

    function destroyPowercrudSearchableSelects(root = document) {
        if (!(root instanceof Element) && root !== document) {
            return;
        }
        const scope = root === document ? document : root;
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

    function getHtmxEventRoots(event) {
        const roots = [];
        const detail = event?.detail || {};

        if (detail.elt instanceof Element) {
            roots.push(detail.elt);
        }
        if (detail.target instanceof Element && detail.target !== detail.elt) {
            roots.push(detail.target);
        }

        return roots;
    }

    global.initPowercrudSearchableSelects = initPowercrudSearchableSelects;
    global.destroyPowercrudSearchableSelects = destroyPowercrudSearchableSelects;

    document.addEventListener('DOMContentLoaded', () => {
        const htmx = global.htmx;
        if (htmx?.process) {
            htmx.process(document.body);
        } else {
            warnMissingDependency('htmx', 'window.htmx. Load HTMX before powercrud/js/powercrud.js');
        }

        const tippy = global.tippy;
        if (typeof tippy === 'function') {
            tippy('[data-tippy-content]');
        } else {
            warnMissingDependency('tippy', 'window.tippy. Load Tippy.js before powercrud/js/powercrud.js');
        }

        initPowercrudSearchableSelects(document);
    });

    document.addEventListener('htmx:beforeSwap', event => {
        getHtmxEventRoots(event).forEach(root => destroyPowercrudSearchableSelects(root));
    });

    document.addEventListener('htmx:afterSwap', event => {
        getHtmxEventRoots(event).forEach(root => initPowercrudSearchableSelects(root));
    });

    document.addEventListener('htmx:afterSettle', event => {
        getHtmxEventRoots(event).forEach(root => initPowercrudSearchableSelects(root));
    });
})(window);
