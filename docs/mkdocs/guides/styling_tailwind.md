# Styling, Template Packs & Tailwind

Use this page after the first screen works. Most applications need only to use the DaisyUI default or select Bootstrap 5, then follow the frontend-loading route in [Getting Started](./getting_started.md#3-load-frontend-assets). The later sections are for application CSS, table tuning, a project-owned Tailwind build, and manual assets.

## 1. Choose the selected template pack {#1-daisyui-default-and-bootstrap-selection}

```python
# Leave POWERCRUD_TEMPLATE_PACK unset for the DaisyUI default.
#
# To select Bootstrap, install powercrud.contrib.bootstrap5 and use:
POWERCRUD_SETTINGS = {
    "POWERCRUD_TEMPLATE_PACK": "powercrud.contrib.bootstrap5:template_pack",
}
```

- **DaisyUI** (Tailwind v4) is the compatible default.
- **Bootstrap 5** is a supported non-default pack. It has its own frontend asset requirements.
- Class settings such as `table_classes` are selected-framework inputs: write DaisyUI/Tailwind classes for the default, or Bootstrap classes when Bootstrap is selected. They are not translated between frameworks.

Do not use `POWERCRUD_CSS_FRAMEWORK` to select Bootstrap; it is a legacy compatibility setting. For a requirement beyond the supported packs, start with focused template overrides and discuss any maintained-pack work explicitly. See [Template Packs](../template_packs/index.md) for pack selection, cross-pack contracts, and Bootstrap requirements.

---

## 2. Common styling controls

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Project

    table_classes = "table-zebra table-sm"
    action_button_classes = "btn-xs"
    extra_button_classes = "btn-sm btn-primary"
```

- `table_classes` appends to the base table class.
- `action_button_classes` targets edit/delete/etc. buttons per row.
- `extra_button_classes` targets the buttons above the table.

### Tooltip theme variables

PowerCRUD exposes a small set of CSS custom properties for tooltip styling, so downstream projects can restyle tooltips in app CSS without adding Python configuration:

```css
:root {
    --pc-tooltip-bg: var(--color-neutral);
    --pc-tooltip-fg: var(--color-neutral-content);
    --pc-tooltip-arrow: var(--pc-tooltip-bg);
    --pc-tooltip-radius: var(--radius-field, 0.25rem);
    --pc-tooltip-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
}
```

Those are the PowerCRUD defaults. Use CSS token values such as `var(--color-neutral)` and `var(--color-neutral-content)`, not utility class names such as `bg-neutral` or `text-neutral-content`.

If you want a project-specific override, set different values in a stylesheet that loads after `powercrud/css/powercrud.css`, for example:

```css
:root {
    --pc-tooltip-bg: var(--color-primary);
    --pc-tooltip-fg: var(--color-primary-content);
}
```

If you manage your own app bundle, load the override CSS after `powercrud/css/powercrud.css` so your `:root` variable values win in the cascade.

??? note "Accepted Tooltip Variable Values"

    Each tooltip variable accepts the normal CSS value type for the property it drives:

    - `--pc-tooltip-bg`: any valid `background-color` value, such as `var(--color-neutral)`, `#272728`, `rgb(39 39 40)`, or `oklch(...)`
    - `--pc-tooltip-fg`: any valid text `color` value
    - `--pc-tooltip-arrow`: any valid `color` value; this is usually kept the same as `--pc-tooltip-bg`
    - `--pc-tooltip-radius`: any valid `border-radius` value, such as `0.25rem`, `8px`, or `var(--radius-field)`
    - `--pc-tooltip-shadow`: any valid `box-shadow` value

    In practice, the cleanest downstream overrides usually use design tokens such as `var(--color-neutral)` / `var(--color-neutral-content)` for defaults or `var(--color-primary)` / `var(--color-primary-content)` for project-specific emphasis, plus existing radius tokens where available.

### Let PowerCRUD choose column widths first {#column-size-controls}

For a table that mixes text with dates, amounts, IDs, and checkmarks, start with semantic widths:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # …
    column_width_policy = "semantic"
```

This keeps automatic IDs and booleans narrow, sizes dates and numbers around their values, and leaves descriptive text room to breathe. Use `column_width_modes` only when your application knows that one named column needs a different treatment. See [Semantic column widths](./setup_core_crud.md#column-widths) for the complete explanation and examples.

??? info "Fine-grained table constraints"

    These existing settings tune the wider table layout and scroll area. Use them when semantic sizing does not answer the layout problem, not as a substitute for choosing a sensible width policy:

    ```python
    table_max_col_width = 30                   # characters
    table_header_min_wrap_width = 15
    table_pixel_height_other_page_elements = 100
    table_max_height = 80                      # percent of remaining viewport
    ```

    They control truncation/popovers and the scrollable table height.

### Keep row actions at a table edge {#row-actions-column-layout}

For a wide table, placement and horizontal pinning are portable view settings rather than framework classes:

```python
row_actions_column_position = "start"  # or "end"
row_actions_column_sticky = True
```

Both DaisyUI and Bootstrap 5 render the Actions header, ordinary row actions, and inline Save/Cancel controls at the selected logical edge. Pack styling supplies the sticky positioning, surface background, edge separation, and table-layer ordering. `start` and `end` follow document direction. When selection is enabled, its checkbox column is always pinned at logical start; sticky start-positioned actions follow it, while sticky end-positioned actions remain at the opposite edge. In `extra_actions_mode = "all_dropdown"`, the visible heading is removed to match the compact ellipsis trigger, while screen-reader-only **Actions** text preserves the column name.

The default is logical-end placement with stickiness enabled. Set `row_actions_column_sticky = False` when an application intentionally wants the action column to scroll out of view with the table.

Below 640px, pack styling hides the configured wider-screen action group and shows one neutral **Actions** kebab backed by the canonical responsive action collection. This applies to `buttons`, extras-only `dropdown`, and `all_dropdown`; the first two keep their configured presentation at 640px and above. Custom CSS should preserve the `data-powercrud-row-actions-responsive="desktop"` / `"mobile"` visibility split rather than showing both control groups together.

Stickiness is horizontal only. Rows continue to move normally during vertical scrolling, and detached row-action panels remain body-level so they are not clipped by the table wrapper. When a panel opens, PowerCRUD copies the originating table cell's computed font size onto the detached panel. Row-action menus therefore follow `table-xs`, `table-sm`, and downstream table typography even though normal CSS inheritance ends when the panel moves under `<body>`; each pack still owns its control sizing and fallback presentation. If you own a pack or override CSS, preserve the semantic `data-powercrud-row-actions-column`, `data-powercrud-row-actions-position`, and optional `data-powercrud-row-actions-sticky` markers instead of relying on first-party utility classes.

The first-party action styling is deliberately quiet. Built-in View/Edit icons and both menu triggers are transparent and neutral at rest, gain neutral fill for hover/focus/open state, and retain semantic tooltips while icon-only. Delete uses the only destructive colour. Dropdown entries are labelled, left-aligned rows rather than stacked coloured buttons; all-dropdown reserves an icon gutter for the standard actions and keeps Delete last behind a conditional divider. Configured `extra_actions[].button_class` remains effective only when an extra action is rendered as a visible button.

### Dropdown sorting

Use `dropdown_sort_options` when queryset-backed selects should be ordered by a predictable field instead of PowerCRUD's default heuristics.

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Project

    dropdown_sort_options = {
        "owner": "name",
        "category": "label",
    }
```

In that example:

- the `owner` dropdown is ordered by `name`
- the `category` dropdown is ordered by `label`

This affects queryset-backed choices across the standard PowerCRUD surfaces, including forms, filters, and bulk editing. Use it when the default `name` / `title` style ordering is not the field you want users to scan by.

For broader bulk-editing context, see [Bulk editing (synchronous)](./bulk_edit_sync.md).

---

## 3. Tailwind integration {#tailwind-integration}

You only need this section if you are running your **own** Tailwind build.

If you are using the packaged PowerCRUD frontend bundle and the built-in templates as-is, the compiled default CSS is already included.

Tailwind’s JIT needs to see the CSS classes PowerCRUD uses when you manage Tailwind yourself. Choose one of the methods below.

`@source "/path/to/site-packages/powercrud"` is only for Tailwind class discovery. It does **not** load PowerCRUD runtime JS/CSS by itself.

### Method A · Import package source

```css
/* your tailwind.css */
@import "tailwindcss";
@source "/path/to/site-packages/powercrud";
```

Find the exact path in a shell:

```python
python manage.py shell
>>> import powercrud
>>> powercrud.__path__
['/venv/lib/python3.13/site-packages/powercrud']
```

### Method B · Safelist generator

1. Configure output location:

```python
POWERCRUD_SETTINGS = {
    "TAILWIND_SAFELIST_JSON_LOC": "config/powercrud/",
}
```

2. Generate the safelist:

```bash
python manage.py pcrud_extract_tailwind_classes --pretty
```

3. Reference it in `tailwind.config.js`:

```javascript
module.exports = {
  content: [
    "./templates/**/*.html",
    "./powercrud/**/*.html",
  ],
  safelist: require("./config/powercrud/powercrud_tailwind_safelist.json"),
};
```

Re-run the command whenever you upgrade PowerCRUD or adjust templates heavily.

---

## 4. External assets

The complete, copyable setup for either frontend-loading route is in [Getting Started](./getting_started.md#3-load-frontend-assets). The same rules apply here; this summary is for styling work that needs to check asset order.

Choose one loading path for PowerCRUD's frontend assets:

- Bundled mode: load the packaged bundle with `{% vite_asset 'config/static/js/main.js' app='powercrud' %}`
- Manual mode: load `HTMX`, `Tom Select`, `Tippy.js`, then PowerCRUD runtime assets (`powercrud/js/powercrud.js` as a module entry, plus `powercrud/css/powercrud.css`)

Optional extra table tooling such as `tablesort` can be layered on top of either path if your project uses it.

If you use bundled mode via `django-vite`, ensure the PowerCRUD app entry is configured with:

- `manifest_path` pointing to `powercrud/assets/manifest.json`
- absolute `static_url_prefix` (for example `"/static/"`)
- `powercrud/assets` included in `STATICFILES_DIRS`

For manual mode, if dependencies are bundled through your own JS pipeline, make sure those libraries are exposed as globals before the `powercrud/js/powercrud.js` module entry runs:

- `window.htmx`
- `window.TomSelect`
- `window.tippy`

Load only `powercrud/js/powercrud.js` with `type="module"`; the browser follows PowerCRUD's internal module imports.

Your application supplies the vendor runtimes, while the selected pack's browser adapter owns the plugin setup for its controls. Do not separately register Tom Select's `checkbox_options`, `remove_button`, or `clear_button` plugins when the pack already does so.

Do not mix packaged-bundle mode and manual mode on the same page. Pick one path.

### Tom Select theme behavior

The compatible DaisyUI pack applies semantic-colour overrides to Tom Select so searchable selects follow the active `data-theme` in both light and dark themes.

If you manage assets yourself, keep Tom Select's vendor CSS loaded before `powercrud/css/powercrud.css`; the pack stylesheet is the layer that replaces Tom Select's light-theme defaults with theme-aware DaisyUI colours.

If you also override PowerCRUD tooltip variables in your own CSS, load that override stylesheet after `powercrud/css/powercrud.css`.

If you manage assets yourself and still want the default visual style, refer to:

- DaisyUI docs: [https://daisyui.com/docs/](https://daisyui.com/docs/){ target="_blank" rel="noopener noreferrer" }
- Tailwind CSS docs: [https://tailwindcss.com/docs](https://tailwindcss.com/docs){ target="_blank" rel="noopener noreferrer" }

PowerCRUD does not ship a full HTML shell; instead, your project must define its own base template (for example, see the sample app’s `sample/templates/sample/daisyUI/base.html`) and point `base_template_path` at it.

---

## 5. Key options

| Setting | Default | Typical values | Purpose |
|---------|---------|----------------|---------|
| `POWERCRUD_CSS_FRAMEWORK` | `'daisyUI'` | legacy compatibility value | Retain the compatible DaisyUI styling path; use `POWERCRUD_TEMPLATE_PACK` to select a supported pack. |
| `table_classes`, `action_button_classes`, `extra_button_classes` | `''` | CSS classes | Style tables and buttons. |
| `column_width_policy`, `column_width_modes` | `'bounded'`, `None` | semantic policy and per-column overrides | Let PowerCRUD choose practical widths, then override a named column when needed. |
| `table_max_col_width`, `table_header_min_wrap_width` | `25`, same as max | integers | Advanced table constraints for truncation and header wrapping. |
| `table_max_height`, `table_pixel_height_other_page_elements` | `70`, `0` | integers | Limit table height and scroll behaviour. |
| `dropdown_sort_options` | `{}` | dict | Order entries in dropdowns. |
| `TAILWIND_SAFELIST_JSON_LOC` | `None` | path | Where to write the Tailwind safelist. |

_See the [configuration reference](../reference/config_options.md) for full details._

---

## Next steps

- Need to override templates or extend components? Head to [Customisation tips](advanced/customisation_tips.md).
- Looking for exhaustive settings? Check the [configuration reference](../reference/config_options.md).
