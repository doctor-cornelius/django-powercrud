import '@/css/main.css'
import htmx from 'htmx.org'
// import 'htmx.org/dist/ext/multi-swap.js'
import TomSelect from 'tom-select'
import 'tom-select/dist/css/tom-select.css'

window.htmx = htmx
window.TomSelect = TomSelect

function updateTomSelectSummary(instance) {
    if (!instance || !instance.control) {
        return
    }
    const selectedItems = instance.items.map((value) => {
        const option = instance.options[value]
        return option ? option.text : value
    })
    const text = selectedItems.length ? selectedItems.join(', ') : 'Select...'
    instance.control.setAttribute('data-selected-text', text)
}

function initTomSelectWidgets(container) {
    if (!window.TomSelect) {
        return
    }
    const scope = container && container.querySelectorAll ? container : document
    const selects = scope.querySelectorAll('.pc-tomselect-m2m select[multiple]')
    if (!selects.length) {
        return
    }
    selects.forEach((select) => {
        if (select.dataset.tomselectBound === 'true') {
            if (select._pcTomSelect) {
                select._pcTomSelect.sync()
                updateTomSelectSummary(select._pcTomSelect)
            }
            return
        }
        const instance = new window.TomSelect(select, {
            plugins: ['checkbox_options'],
            persist: false,
            create: false,
            hideSelected: false,
            closeAfterSelect: false,
            dropdownParent: 'body',
        })
        select.dataset.tomselectBound = 'true'
        select._pcTomSelect = instance
        updateTomSelectSummary(instance)
        instance.on('change', () => updateTomSelectSummary(instance))
    })
}

window.initTomSelectWidgets = initTomSelectWidgets

// Bootstrap
import * as bootstrap from 'bootstrap'
window.bootstrap = bootstrap

// Alpine.js
import Alpine from 'alpinejs'
window.Alpine = Alpine

// Tippy.js
import tippy from 'tippy.js';
import 'tippy.js/dist/tippy.css';
window.tippy = tippy;

// Make htmx available globally
document.addEventListener('DOMContentLoaded', () => {
    // Start htmx after DOM is ready
    htmx.process(document.body)

    // Start Alpine after DOM is ready
    Alpine.start()
    
    // Initialize tooltips if needed
    tippy('[data-tippy-content]')
})
