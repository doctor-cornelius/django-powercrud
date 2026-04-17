# Styling & Tailwind

PowerCRUD ships with daisyUI/Tailwind defaults and a packaged frontend bundle, but you can still bring your own CSS framework or customise tables/buttons/layout. This chapter covers the common knobs and Tailwind integration; deeper options live in the reference.

---

## 1. Choose a framework

```python
# settings.py
POWERCRUD_SETTINGS = {
    "POWERCRUD_CSS_FRAMEWORK": "daisyui",   # default
}
```

- **daisyUI** (Tailwind v4) is the maintained path.
- Custom frameworks are possible by copying templates (see [Customisation tips](./customisation_tips.md)) and wiring in a new pack.

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
    --pc-tooltip-bg: var(--color-primary);
    --pc-tooltip-fg: var(--color-primary-content);
    --pc-tooltip-arrow: var(--pc-tooltip-bg);
    --pc-tooltip-radius: var(--radius-field, 0.25rem);
    --pc-tooltip-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
}
```

Use CSS token values such as `var(--color-primary)` and `var(--color-primary-content)`, not utility class names such as `bg-primary` or `text-primary-content`.

If you manage your own app bundle, load the override CSS after `powercrud/css/powercrud.css` so your `:root` variable values win in the cascade.

??? note "Accepted Tooltip Variable Values"

    Each tooltip variable accepts the normal CSS value type for the property it drives:

    - `--pc-tooltip-bg`: any valid `background-color` value, such as `var(--color-primary)`, `#2563eb`, `rgb(37 99 235)`, or `oklch(...)`
    - `--pc-tooltip-fg`: any valid text `color` value
    - `--pc-tooltip-arrow`: any valid `color` value; this is usually kept the same as `--pc-tooltip-bg`
    - `--pc-tooltip-radius`: any valid `border-radius` value, such as `0.25rem`, `8px`, or `var(--radius-field)`
    - `--pc-tooltip-shadow`: any valid `box-shadow` value

    In practice, the cleanest downstream overrides usually use design tokens such as `var(--color-primary)` and `var(--color-primary-content)`, plus existing radius tokens where available.

### Column size controls

```python
table_max_col_width = 30                   # characters
table_header_min_wrap_width = 15
table_pixel_height_other_page_elements = 100
table_max_height = 80                      # percent of remaining viewport
```

These values control truncation/popovers and scrollable table height.

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

Choose one loading path for PowerCRUD's frontend assets:

- Bundled mode: load the packaged bundle with `{% vite_asset 'config/static/js/main.js' app='powercrud' %}`
- Manual mode: load `HTMX`, `Tom Select`, `Tippy.js`, then PowerCRUD runtime assets (`powercrud/js/powercrud.js`, `powercrud/css/powercrud.css`)

Optional extra table tooling such as `tablesort` can be layered on top of either path if your project uses it.

If you use bundled mode via `django-vite`, ensure the PowerCRUD app entry is configured with:

- `manifest_path` pointing to `powercrud/assets/manifest.json`
- absolute `static_url_prefix` (for example `"/static/"`)
- `powercrud/assets` included in `STATICFILES_DIRS`

For manual mode, if dependencies are bundled through your own JS pipeline, make sure those libraries are exposed as globals before `powercrud/js/powercrud.js` runs:

- `window.htmx`
- `window.TomSelect`
- `window.tippy`

Do not mix packaged-bundle mode and manual mode on the same page. Pick one path.

### Tom Select theme behavior

PowerCRUD applies daisyUI semantic-color overrides to Tom Select so searchable selects follow the active `data-theme` in both light and dark themes.

If you manage assets yourself, keep Tom Select's vendor CSS loaded before `powercrud/css/powercrud.css`; the package stylesheet is the layer that replaces Tom Select's light-theme defaults with theme-aware daisyUI colors.

If you also override PowerCRUD tooltip variables in your own CSS, load that override stylesheet after `powercrud/css/powercrud.css`.

If you manage assets yourself and still want the default visual style, refer to:

- daisyUI docs: [https://daisyui.com/docs/](https://daisyui.com/docs/){ target="_blank" rel="noopener noreferrer" }
- Tailwind CSS docs: [https://tailwindcss.com/docs](https://tailwindcss.com/docs){ target="_blank" rel="noopener noreferrer" }

PowerCRUD does not ship a full HTML shell; instead, your project must define its own base template (for example, see the sample app’s `sample/templates/sample/daisyUI/base.html`) and point `base_template_path` at it.

---

## 5. Key options

| Setting | Default | Typical values | Purpose |
|---------|---------|----------------|---------|
| `POWERCRUD_CSS_FRAMEWORK` | `'daisyui'` | `'daisyui'`, custom pack name | Choose the styling stack. |
| `table_classes`, `action_button_classes`, `extra_button_classes` | `''` | CSS classes | Style tables and buttons. |
| `table_max_col_width`, `table_header_min_wrap_width` | `25`, same as max | integers | Control column widths and truncation. |
| `table_max_height`, `table_pixel_height_other_page_elements` | `70`, `0` | integers | Limit table height and scroll behaviour. |
| `dropdown_sort_options` | `{}` | dict | Order entries in dropdowns. |
| `TAILWIND_SAFELIST_JSON_LOC` | `None` | path | Where to write the Tailwind safelist. |

_See the [configuration reference](../reference/config_options.md) for full details._

---

## Next steps

- Need to override templates or extend components? Head to [Customisation tips](customisation_tips.md).
- Looking for exhaustive settings? Check the [configuration reference](../reference/config_options.md).
