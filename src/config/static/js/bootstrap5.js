import htmx from 'htmx.org'
import TomSelect from 'tom-select'
import 'tom-select/dist/css/tom-select.css'
import removeButtonPlugin from 'tom-select/dist/js/plugins/remove_button.js'
import * as bootstrap from 'bootstrap'
import 'bootstrap/dist/css/bootstrap.min.css'

import '../../../powercrud/contrib/bootstrap5/static/powercrud/contrib/bootstrap5/css/bootstrap5.css'
import '../../../powercrud/contrib/bootstrap5/static/powercrud/contrib/bootstrap5/js/adapter.js'

// Expose only the vendor globals consumed by the selected Bootstrap runtime.
window.htmx = htmx
window.TomSelect = TomSelect
window.bootstrap = bootstrap
TomSelect.define('remove_button', removeButtonPlugin)

// Load the stable entry only after Bootstrap and the selected adapter exist.
void import('../../../powercrud/static/powercrud/js/powercrud.js')
