import '@/css/main.css'

import htmx from 'htmx.org'
import TomSelect from 'tom-select'
import 'tom-select/dist/css/tom-select.css'
import removeButtonPlugin from 'tom-select/dist/js/plugins/remove_button.js'

import tippy from 'tippy.js'
import 'tippy.js/dist/tippy.css'

// Expose vendor libraries for package-owned runtime code and template scripts.
window.htmx = htmx
TomSelect.define('remove_button', removeButtonPlugin)
window.TomSelect = TomSelect
window.tippy = tippy

// Import package-owned runtime assets while preserving the historical
// bundle entry key: config/static/js/main.js
import '../../../powercrud/static/powercrud/css/powercrud.css'
import '../../../powercrud/static/powercrud/js/powercrud.js'

// Load sample-app overrides after package CSS so :root custom properties win.
import '@/css/app.custom.css'
