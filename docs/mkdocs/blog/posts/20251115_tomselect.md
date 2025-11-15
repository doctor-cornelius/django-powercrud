---
date: 2025-11-15
categories:
  - styling
  - inline_edit
  - enhancement
---
# Using Tom Select for Inline Edit Multi-Select

The standard multi select gets too tall and makes the row expand. The Tom Select one will not. We will vendor Tom Select, and set `renovate` to update the lock file version, and we will replace the standard multi select widget.
<!-- more -->

## Design

Goal: replace the default `<select multiple>` used in inline edit rows with Tom Select so each cell stays a single row tall while still allowing M2M edits.

### Inline Widget Anatomy

- Each form field keeps the Django `<select multiple>` markup so POST payloads stay identical.
- `_render_inline_row_form` in `src/powercrud/mixins/inline_editing_mixin.py:305` renders `partial/list.html#inline_row_form`, which in turn includes `partial/inline_field.html`. That partial currently outputs `{{ field }}`, so it is the hook for wrapping inline widgets in a `.pc-tomselect-m2m` container (or adding `data-tom-select="true"` attributes) without rewriting how forms are built.
- CSS should live in `src/powercrud/templates/powercrud/daisyUI/layout/inline_field.html` because HTMX swaps re-render that layout snippet whenever a row enters edit mode. We can drop a `<style>` block scoped to `.pc-tomselect-m2m` or use a `{% block inline_field_styles %}` override if we add one.
- JS must be emitted from `src/powercrud/templates/powercrud/daisyUI/object_list.html` only. This template is always on the page (even when rows are swapped via HTMX), so adding a `<script type="module">` there ensures the Tom Select initializer runs after every `htmx:afterSwap`.
- Once those hooks exist, JS upgrades `.pc-inline-table .pc-tomselect-m2m select[multiple]` to Tom Select after HTMX swaps, CSS enforces a fixed height wrapper and hides pill chips so the control shows summarized text only, and Tom Select writes the joined labels into a `data-selected-text` attribute that the CSS surfaces.

### Reference Implementation

Exactly the same demo that already works in `docs/mkdocs/blog/posts/tomselect.html`, ready to embed in MkDocs for design sign-off.

=== "html"

    ```html
    {% load static django_vite %}
    <!DOCTYPE html>
    <html lang="en" data-theme="light">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Tom Select Table Demo</title>
        {% vite_asset 'config/static/js/main.js' %}
    </head>
    <body class="p-8">
        <div class="overflow-x-auto">
            <table class="table table-zebra">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Tags</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>1</td>
                        <td>John Doe</td>
                        <td>
                            <select class="tag-select w-36" multiple>
                                <option value="python">Python</option>
                                <option value="javascript">JavaScript</option>
                                <option value="django">Django</option>
                                <option value="react">React</option>
                            </select>
                        </td>
                        <td><span class="badge badge-success">Active</span></td>
                    </tr>
                </tbody>
            </table>
        </div>
    </body>
    </html>
    ```

=== "css"

    ```css
    .ts-wrapper {
        width: 150px !important;
        max-width: 150px !important;
    }

    .ts-wrapper .ts-control {
        min-height: 38px !important;
        max-height: 38px !important;
        height: 38px !important;
        overflow: hidden !important;
        padding: 8px 12px !important;
        display: flex !important;
        align-items: center !important;
    }

    .ts-wrapper.multi .ts-control > div,
    .ts-wrapper.multi .ts-control input {
        display: none !important;
    }

    .ts-wrapper.multi .ts-control:after {
        content: attr(data-selected-text);
        color: #333;
        line-height: 1;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        width: 100%;
    }
    ```

=== "js"

    ```js
    import TomSelect from 'tom-select'
    import 'tom-select/dist/css/tom-select.css'

    const initTomSelect = () => {
        document.querySelectorAll('.tag-select').forEach((el) => {
            const ts = new TomSelect(el, {
                plugins: ['checkbox_options'],
                persist: false,
                create: false,
                hideSelected: false,
                closeAfterSelect: false,
                dropdownParent: 'body',
                onChange: function () {
                    const selectedItems = this.items.map((value) => {
                        const option = this.options[value]
                        return option ? option.text : value
                    })

                    const text = selectedItems.length > 0
                        ? selectedItems.join(', ')
                        : 'Select...'

                    this.control.setAttribute('data-selected-text', text)
                },
                onInitialize: function () {
                    this.control.setAttribute('data-selected-text', 'Select...')
                }
            })

            el.addEventListener('htmx:afterSwap', () => ts.sync())
        })
    }

    document.addEventListener('DOMContentLoaded', initTomSelect)
    document.body.addEventListener('htmx:afterSwap', initTomSelect)
    ```

## Vendoring Tom Select

1. Add Tom Select to `package.json` devDependencies at the version used above (`2.3.1` or latest available) so `npm install` pulls the assets into `node_modules`.
2. Extend `new_release.sh` to run `npm install` (if not already) and copy `node_modules/tom-select/dist/css/tom-select.css` and `node_modules/tom-select/dist/js/tom-select.complete.min.js` into `src/config/static/vendor/tom-select/`.
3. Update `src/config/static/vendor/.gitignore` (if needed) so the vendored files are committed.
4. Reference the vendored CSS from `src/powercrud/templates/powercrud/daisyUI/layout/inline_field.html` (wrap each inline select in a class and include a scoped `<style>`). Reference and initialize the vendored JS inside `src/powercrud/templates/powercrud/daisyUI/object_list.html` so HTMX fragments never miss the initializer.
5. Document in `docs/mkdocs/guides/inline_editing.md` that Tom Select assets must be regenerated via `./new_release.sh`.

### Vite + npm build

- `src/config/static/js/main.js` is the single Vite entry point (configured in `src/vite.config.mjs`).
- Import Tom Select CSS/JS inside `main.js`, e.g.:

    ```js
    import TomSelect from 'tom-select'
    import 'tom-select/dist/css/tom-select.css'
    ```

- Add the initialization module above to `main.js` (or a dedicated module imported from `main.js`). Vite automatically bundles Tom Select into `powercrud/assets/django_assets/*.js` when `npm run build` executes.
- Tailwind/DaisyUI already load via `src/config/static/css/main.css`, which is imported at the top of `main.js` (`import '@/css/main.css'`). No CDN link tags are necessary because Django serves the Vite-built files referenced with `{% vite_asset 'config/static/js/main.js' %}` during development and the manifest-backed static files in production.
- `src/vite.config.mjs` tells Vite to emit into `src/powercrud/assets`. The release workflow calls `npm run build` (which runs `vite build`), and `new_release.sh` then copies the generated JS/CSS into `src/config/static/vendor/` so Django can collect them.

### Renovate

- Update `renovate.json` to include the root `package.json` so the dependency is monitored.
- Add a rule to **not** run any npm scripts, with a comment pointing to `new_release.sh` as the canonical build step.
- Ensure `package-lock.json` is listed so version bumps flow through lockfile updates only.

## Plan

1. **Prepare assets**

    [x] Install Tom Select (`npm install tom-select@^2.3.1`).
    [x] Run `npm run build` to confirm Vite emits the bundled CSS/JS (the resulting assets land in `src/powercrud/assets` via `vite.config.mjs`).

2. **Wire up templates**

    [x] Import the vendored CSS into `inline_field.html` (or wrap the select with `<div class="pc-tomselect-m2m">`) so HTMX swaps always carry the styling.
    [x] Initialize Tom Select for `.pc-inline-table .pc-tomselect-m2m select[multiple]` via a `<script type="module">` in `object_list.html` (this script will also attach `document.body.addEventListener('htmx:afterSwap', ...)`).

3. **Inline editing integration**

    [x] Update `inline_field.html` / `partial/inline_field.html` to add `class="pc-tomselect-m2m"` (only on `field.field.widget.allow_multiple_selected` controls) so the JS can detect them.
    [x] Adjust `_render_inline_row_form` (if needed) to pass context flags telling the template which fields are M2M; otherwise inspect `field.field.widget.allow_multiple_selected` inside the template and branch there. (Not required: templates branch on `field.field.widget.allow_multiple_selected` directly.)
    [ ] Fix bugs:
        [x] **auto-focus** and open dropdown when click m2m field to open inline row edit
        [ ] **width** must be wide enough so options do not wrap in dropdown, but element width musy not be wider than before inline edit
        [ ] **row** must not get taller because tom select element is too tall
        [ ] **form errors** return a form with the default non-ts styling
    

4. **Renovate + docs**

    [ ] Modify `renovate.json` so Renovate tracks `package.json` and `package-lock.json` but skips npm build steps.
    [ ] Document workflow in `docs/mkdocs/guides/inline_editing.md` and reference this blog post from `20251113_multi_select.md`.

5. **Testing**

    [ ] Run inline edit flows locally to confirm Tom Select keeps row height constant.
    [ ] Verify `npm run lint` (if any) and Django tests still pass since we touched templates/static.
