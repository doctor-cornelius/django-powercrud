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

## 2. Table and button styles

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

### Column size controls

```python
table_max_col_width = 30                   # characters
table_header_min_wrap_width = 15
table_pixel_height_other_page_elements = 100
table_max_height = 80                      # percent of remaining viewport
```

These values control truncation/popovers and scrollable table height.

### Dropdown sorting

`dropdown_sort_options` affects choices in forms, filters, and bulk editing (see [Bulk editing (synchronous)](./bulk_edit_sync.md)).

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

Ensure your base template includes:

- The PowerCRUD packaged bundle (`{% vite_asset 'config/static/js/main.js' app='powercrud' %}`), or:
- Manual frontend dependencies (`HTMX`, `Tom Select`, `Tippy.js`) plus PowerCRUD runtime assets (`powercrud/js/powercrud.js`, `powercrud/css/powercrud.css`).
- Optional: extra table tooling (for example `tablesort`) if you use it.

If you use bundled mode via `django-vite`, ensure the PowerCRUD app entry is configured with:

- `manifest_path` pointing to `powercrud/assets/manifest.json`
- absolute `static_url_prefix` (for example `"/static/"`)
- `powercrud/assets` included in `STATICFILES_DIRS`

For manual mode, if dependencies are bundled through your own JS pipeline, make sure those libraries are exposed as globals before `powercrud/js/powercrud.js` runs:

- `window.htmx`
- `window.TomSelect`
- `window.tippy`

Do not mix packaged-bundle mode and manual mode on the same page. Pick one path.

If you manage assets yourself and still want the default visual style, refer to:

- daisyUI docs: [https://daisyui.com/docs/](https://daisyui.com/docs/){ target="_blank" rel="noopener noreferrer" }
- Tailwind CSS docs: [https://tailwindcss.com/docs](https://tailwindcss.com/docs){ target="_blank" rel="noopener noreferrer" }

PowerCRUD does not ship a full HTML shell; instead, your project must define its own base template (for example, see the sample app’s `sample/templates/sample/daisyUI/base.html`) and point `base_template_path` at it.

---

### Key options

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
