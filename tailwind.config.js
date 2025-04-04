/**
 * This is a minimal config.
 *
 * If you need the full config, get it from here:
 * https://unpkg.com/browse/tailwindcss@latest/stubs/defaultConfig.stub.js
 */

module.exports= {
    content: [
        /**
             * HTML. Paths to Django template files that will contain Tailwind CSS classes.
             */

        // /* All templates in apps directory */
        // './django_nominopolitan/templates/**/*.html',

        // /* Main templates directory */
        // './django_nominopolitan/templates/**/*.html',
        // './django_nominopolitan/static/js/**/*.js',

        // './nominopolitan/mixins.py', // for get_framework_styles()
        // './nominopolitan/templates/nominopolitan/**/*.html', // nominopolitan templates

        // './sample/views.py', // for overrides specified in views
        // './sample/templates/sample/**/*.html', // sample templates

        /* Ignore node_modules */
        '!**/node_modules/**'
    ],
    safelist: [
    ],
    daisyui: {
        themes: [
            "light", 
            "dark", 
            "corporate", 
            "business", 
            "caramellatte",
            "nord",
            "coffee", 
            "winter",
            // "cupcake", 
            // "bumblebee", 
            // "emerald", 
            // "synthwave", 
            // "retro", 
            // "cyberpunk", 
            // "valentine", 
            // "halloween", 
            // "garden", 
            // "forest", 
            // "aqua", 
            // "lofi", 
            // "pastel", 
            // "fantasy", 
            // "wireframe", 
            // "black", 
            // "luxury", 
            // "dracula", 
            // "cmyk", 
            // "autumn", 
            // "acid", 
            // "lemonade", 
            // "night", 
        ]

    },
    theme: {
        extend: {},
    },
    plugins: [
        /**
         * '@tailwindcss/forms' is the forms plugin that provides a minimal styling
         * for forms. If you don't like it or have own styling for forms,
         * comment the line below to disable '@tailwindcss/forms'.
         */
        require('daisyui'),  // Move daisyui first        
        require('@tailwindcss/typography'),
        require('@tailwindcss/aspect-ratio'),
        require('@tailwindcss/forms'),
    ],
}