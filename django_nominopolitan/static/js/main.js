// =========================================
// Font Imports
// =========================================
// IBM Plex Family
import "@fontsource/ibm-plex-sans/300.css";
import "@fontsource/ibm-plex-sans/400.css";
import "@fontsource/ibm-plex-sans/500.css";
import "@fontsource/ibm-plex-sans/700.css";

import "@fontsource/ibm-plex-serif/300.css";
import "@fontsource/ibm-plex-serif/400.css";
import "@fontsource/ibm-plex-serif/500.css";
import "@fontsource/ibm-plex-serif/700.css";

import "@fontsource/ibm-plex-mono/300.css";
import "@fontsource/ibm-plex-mono/400.css";
import "@fontsource/ibm-plex-mono/500.css";
import "@fontsource/ibm-plex-mono/700.css";

// Sans-Serif Fonts
import "@fontsource/open-sans/300.css";
import "@fontsource/open-sans/400.css";
import "@fontsource/open-sans/500.css";
import "@fontsource/open-sans/700.css";

// =========================================
// Library Imports and Initialization
// =========================================

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

// Initialize everything when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Start Alpine after DOM is ready
    Alpine.start()
    
    // Initialize tooltips if needed
    tippy('[data-tippy-content]')
})
