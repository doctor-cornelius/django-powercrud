# 06. Styling & Tailwind

PowerCRUD ships with daisyUI/Tailwind defaults but you can bring your own CSS framework or customise tables/buttons/layout. This chapter covers the common knobs and Tailwind integration; deeper options live in the reference.

---

## 1. Choose a framework

```python
# settings.py
POWERCRUD_SETTINGS = {
    "POWERCRUD_CSS_FRAMEWORK": "daisyui",   # default
    # "POWERCRUD_CSS_FRAMEWORK": "bootstrap5",
}
```

- **daisyUI** (Tailwind v4) is the maintained path.
- Bootstrap 5 templates exist but lag behind—expect to tweak them.
- Custom frameworks are possible by copying templates (see [Section 07](./07_customisation_tips.md)).

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

`dropdown_sort_options` affects choices in forms, filters, and bulk editing (see [Section 02](./02_bulk_edit_sync.md)).

---

## 3. Tailwind integration {#tailwind-integration}

Tailwind’s JIT needs to see the CSS classes PowerCRUD uses. Choose one of the methods below.

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

- HTMX script.
- Popper.js (for truncated-table popovers).
- Optional: tablesort or Alpine.js if you use them.

The quickest way is to copy the examples from `powercrud/templates/powercrud/base.html` and adjust to taste.

---

## 5. Bootstrap (legacy) notes

If you opt for Bootstrap 5:

- Copy templates with `python manage.py pcrud_mktemplate myapp --all`.
- Update them to match your bootstrap version (buttons, table classes, modal markup).
- Many newer PowerCRUD features were built against daisyUI—test thoroughly.

---

### Key options

| Setting | Default | Typical values | Purpose |
|---------|---------|----------------|---------|
| `POWERCRUD_CSS_FRAMEWORK` | `'daisyui'` | `'daisyui'`, `'bootstrap5'` | Choose the styling stack. |
| `table_classes`, `action_button_classes`, `extra_button_classes` | `''` | CSS classes | Style tables and buttons. |
| `table_max_col_width`, `table_header_min_wrap_width` | `25`, same as max | integers | Control column widths and truncation. |
| `table_max_height`, `table_pixel_height_other_page_elements` | `70`, `0` | integers | Limit table height and scroll behaviour. |
| `dropdown_sort_options` | `{}` | dict | Order entries in dropdowns. |
| `TAILWIND_SAFELIST_JSON_LOC` | `None` | path | Where to write the Tailwind safelist. |

_See the [configuration reference](../reference/config_options.md) for full details._

---

## Next steps

- Need to override templates or extend components? Head to [07 Customisation tips](07_customisation_tips.md).
- Looking for exhaustive settings? Check the [configuration reference](../reference/config_options.md).
