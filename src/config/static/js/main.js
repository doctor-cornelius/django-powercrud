import '@/css/main.css'
import htmx from 'htmx.org'
// import 'htmx.org/dist/ext/multi-swap.js'
import TomSelect from 'tom-select'
import 'tom-select/dist/css/tom-select.css'
import removeButtonPlugin from 'tom-select/dist/js/plugins/remove_button.js'

window.htmx = htmx
TomSelect.define('remove_button', removeButtonPlugin)

// Tippy.js
import tippy from 'tippy.js';
import 'tippy.js/dist/tippy.css';
window.tippy = tippy;
window.TomSelect = TomSelect;

const SEARCHABLE_SELECT_ATTR = 'data-powercrud-searchable-select';
const SEARCHABLE_MULTISELECT_ATTR = 'data-powercrud-searchable-multiselect';
const NATIVE_TABINDEX_ATTR = 'data-powercrud-native-tabindex';
const NATIVE_STYLE_ATTR = 'data-powercrud-native-style';

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

function enhanceSearchableSelect(selectElement) {
    if (!isSearchableSelectCandidate(selectElement)) {
        return;
    }
    if (selectElement.tomselect) {
        syncTomSelectDisabledState(selectElement);
        hideNativeSelect(selectElement);
        return;
    }
    // Hidden controls (for example, bulk modal fields before they are toggled on)
    // should be enhanced when they become visible to avoid broken dropdown geometry.
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
    // Outside a modal, body-level dropdown avoids clipping in complex layouts.
    // Inside a <dialog>, keep TomSelect default local dropdown rendering.
    if (!dialogElement) {
        settings.dropdownParent = 'body';
    }
    const instance = new TomSelect(selectElement, settings);
    // Remove Daisy native-select classes copied from <select> so TomSelect
    // wrapper/control layout is not constrained by select-only styling.
    instance.wrapper.classList.remove('select', 'select-bordered', 'select-sm', 'select-md', 'select-lg');
    instance.control.classList.remove('select', 'select-bordered', 'select-sm', 'select-md', 'select-lg');
    instance.wrapper.classList.add('w-full');
    instance.control.classList.add('w-full');
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
    const instance = new TomSelect(selectElement, settings);
    instance.wrapper.classList.remove('select', 'select-bordered', 'select-sm', 'select-md', 'select-lg');
    instance.control.classList.remove('select', 'select-bordered', 'select-sm', 'select-md', 'select-lg');
    instance.wrapper.classList.add('w-full');
    instance.control.classList.add('w-full');
    syncTomSelectDisabledState(selectElement);
    hideNativeSelect(selectElement);
}

function initPowercrudSearchableSelects(root = document) {
    if (!(root instanceof Element) && root !== document) {
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

window.initPowercrudSearchableSelects = initPowercrudSearchableSelects;
window.destroyPowercrudSearchableSelects = destroyPowercrudSearchableSelects;

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

// Make htmx available globally
document.addEventListener('DOMContentLoaded', () => {
    // Start htmx after DOM is ready
    htmx.process(document.body)
    
    // Initialize tooltips if needed
    tippy('[data-tippy-content]')

    // Enhance eligible single-select widgets.
    initPowercrudSearchableSelects(document);
})

document.addEventListener('htmx:beforeSwap', event => {
    // Avoid orphaned Tom Select wrappers when HTMX replaces markup.
    getHtmxEventRoots(event).forEach(root => destroyPowercrudSearchableSelects(root));
});

document.addEventListener('htmx:afterSwap', event => {
    getHtmxEventRoots(event).forEach(root => initPowercrudSearchableSelects(root));
});

document.addEventListener('htmx:afterSettle', event => {
    // Some outerHTML swaps settle on a newly inserted node; initialize again
    // to ensure inline rows receive Tom Select enhancement deterministically.
    getHtmxEventRoots(event).forEach(root => initPowercrudSearchableSelects(root));
});
