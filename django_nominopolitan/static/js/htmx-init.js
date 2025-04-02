import htmx from 'htmx.org'
import 'htmx.org/dist/ext/multi-swap.js'

// Make htmx available globally
window.htmx = htmx

document.addEventListener('DOMContentLoaded', () => {
    htmx.process(document.body)
})