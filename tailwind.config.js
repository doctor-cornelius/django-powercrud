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

        /* All templates in apps directory */
        './django_nominopolitan/templates/**/*.html',

        /* Main templates directory */
        './django_nominopolitan/sample/templates/**/*.html',

        /**
             * JS: If you use Tailwind CSS in JavaScript
             */
        './django_nominopolitan/static/js/**/*.js',
        './nominopolitan/**/*.py',  // Add this
        './nominopolitan/templates/nominopolitan/**/*.html', 
        './sample/**/*.py',          // Add this
        /* Ignore node_modules */
        '!**/node_modules/**'
    ],
    safelist: [

    ],
    daisyui: {
        themes: ["light"]  // or any other theme you prefer
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
        require('@tailwindcss/forms'),
        require('@tailwindcss/typography'),
        require('@tailwindcss/aspect-ratio'),
        require('daisyui'),
    ],
}