import '@/css/main.css'
import htmx from 'htmx.org'
// import 'htmx.org/dist/ext/multi-swap.js'
import TomSelect from 'tom-select'
import 'tom-select/dist/css/tom-select.css'

window.htmx = htmx
window.TomSelect = TomSelect

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
