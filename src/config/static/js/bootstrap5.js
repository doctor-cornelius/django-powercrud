import htmx from 'htmx.org'
import TomSelect from 'tom-select'
import 'tom-select/dist/css/tom-select.css'
import removeButtonPlugin from 'tom-select/dist/js/plugins/remove_button.js'
import * as bootstrap from 'bootstrap'
import 'bootstrap/dist/css/bootstrap.min.css'

import '../../../powercrud/contrib/bootstrap5/static/powercrud/contrib/bootstrap5/css/bootstrap5.css'
import { createBootstrap5BaselineComposition } from '../../../powercrud/contrib/bootstrap5/static/powercrud/contrib/bootstrap5/js/runtime/bootstrap5-composition.js'

// Expose only the vendor globals consumed by the selected Bootstrap runtime.
window.htmx = htmx
window.TomSelect = TomSelect
window.bootstrap = bootstrap
TomSelect.define('remove_button', removeButtonPlugin)

window.__powercrudPrivateDeferInstall = true

try {
  const { installPowercrudRuntime } = await import('../../../powercrud/static/powercrud/js/powercrud.js')
  installPowercrudRuntime({ createComposition: createBootstrap5BaselineComposition })
} finally {
  delete window.__powercrudPrivateDeferInstall
}
