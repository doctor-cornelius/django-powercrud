# Inline Editing

Let users tweak individual rows without leaving the list view. PowerCRUD renders inline form fields inside the table, swaps rows with HTMX, and keeps the action column focused on “Save / Cancel” while editing.

---

## Prerequisites

- [Setup & Core CRUD basics](./setup_core_crud.md) completed.
- HTMX enabled (`use_htmx = True`) and the standard PowerCRUD list template in use.
- Optional but recommended: `use_modal = True` so the inline scripts and global spinners are already loaded.

---

## 1. Enable inline editing

```python
class BookCRUDView(PowerCRUDMixin, CRUDView):
    model = Book
    base_template_path = "core/base.html"

    use_htmx = True
    inline_edit_fields = ["title", "author", "published_date", "genres"]
    inline_edit_always_visible = True
    inline_edit_highlight_accent = "#14b8a6"
```

!!! warning "Legacy `inline_edit_enabled` compatibility"

    `inline_edit_enabled` is now legacy compatibility-only behavior.
    New code should configure inline editing only through `inline_edit_fields`.

    Older views that still set `inline_edit_enabled = True` continue to work temporarily.
    If they do not define `inline_edit_fields`, PowerCRUD temporarily falls back to the resolved form fields to preserve the old behavior.

    Downstream projects should migrate away from `inline_edit_enabled`.

- `inline_edit_fields` both enables inline editing and controls which columns show the hover/focus shim and respond to clicks.
- Leave `inline_edit_fields` unset to disable inline editing for the view.
- Explicit `inline_edit_fields` entries must be editable model fields. If you include a field with `editable=False`, PowerCRUD raises a configuration error during view setup.
- `inline_edit_fields` must match fields exposed by the actual form returned by `get_form_class()`. If you use a custom `form_class`, PowerCRUD still filters the inline list to fields that really exist on that form.
- Stock inline editing still builds the full edit form, then reposts any non-rendered form fields as hidden inputs so inline saves behave like the normal edit form.
- `form_disabled_fields` does not disable the same field inline. It remains an update-form feature only.
- Only columns actually rendered in the list can be clicked inline, so a field must be both inline-configured and visible in the list to behave as an inline-editable cell.
- `inline_edit_always_visible` defaults to `True`, which means editable cells show a subtle resting hint even before hover.
- `inline_edit_highlight_accent` defaults to `"#14b8a6"`. PowerCRUD derives the lighter resting tint, stronger hover/focus tint, and active-row highlight from that single hex accent automatically.
- The mixin automatically injects inline metadata into the row payload and exposes two HTMX endpoints:
    - `…-inline-row` – swaps the display/form row and handles POST saves.
    - `…-inline-dependency` – rebuilds a single field widget for dependent dropdowns.

The DaisyUI template already includes the triggers, Save/Cancel buttons, and `inline-row-*` events; no manual template work is required unless you are overriding the list partial.

### Styling the inline-edit affordance

Use the default configuration when the built-in teal hint is fine:

```python
inline_edit_always_visible = True
inline_edit_highlight_accent = "#14b8a6"
```

To keep the stronger hover/focus cue but remove only the always-on resting tint:

```python
inline_edit_always_visible = False
```

Hover and focus highlighting still remain active in this mode; only the persistent resting tint is removed.

To use a different accent, provide a hex color and let PowerCRUD derive the lighter and stronger variants automatically:

```python
inline_edit_highlight_accent = "#3b82f6"
```

Notes:

- Only hex colors are supported here: `#rgb` and `#rrggbb`.
- This API intentionally keeps the surface small. If you need per-state color control beyond the single accent, override the list partial in your project.

---

## 2. Configure dependencies and helpers

Inline editing reuses the existing form machinery, so any widget or queryset customisations carry over. Keep `inline_edit_fields` aligned with whatever the form actually exposes; if a field is excluded from `form_class`, PowerCRUD drops it from the inline list after the initial editable-field validation. List rendering still controls which cells are clickable, so an inline field should normally also be present in your list `fields`. Fields that belong to the full form but are not rendered as visible inline widgets are still reposted as hidden inputs so save validation matches the normal edit form. One exception is `form_disabled_fields`: that setting does not lock the same field inline and remains update-form-only. For dynamic dropdowns, declare the shared queryset dependency once:

```python
class BookCRUDView(PowerCRUDMixin, CRUDView):
    # …
    field_queryset_dependencies = {
        "genres": {
            "depends_on": ["author"],
            "filter_by": {"authors": "author"},
            "order_by": "name",
            "empty_behavior": "all",
        }
    }
```

- `depends_on` lists the parent fields that drive the child queryset.
- `filter_by` maps child queryset lookups to those parent form fields.
- Each dependent field renders a placeholder + spinner; the JS helper issues a POST to the dependency endpoint and swaps the widget.
- If the underlying form raises a validation error, the inline row re-renders with the field errors plus a banner (`inline-row-error` HTMX trigger).

The same helpers drive both inline rows and lock-sensitive action buttons, so `_build_inline_row_payload()` contains everything the template needs (row id, inline URLs, lock metadata).

### Cookbook: parent/child dropdowns that refresh inline

The most reliable pattern is:

1. Add an explicit relation that describes which child records are allowed for each parent.
2. Declare `field_queryset_dependencies` on the CRUD view.
3. Use a custom `form_class` only for form concerns that remain outside the generic dependency rule.
4. Let PowerCRUD resolve the parent field from bound POST data first, then fall back to the instance.

The sample app demonstrates this with `Book.author -> Book.genres`, where the allowed genres come from `Author.genres`:

???+ note "Sample App Dynamic Inline Field Overrides Example"

    === "`BookCRUDView`"

        ```python
        class BookCRUDView(PowerCRUDMixin, CRUDView):
            model = Book
            form_class = BookForm
            field_queryset_dependencies = {
                "genres": {
                    "depends_on": ["author"],
                    "filter_by": {"authors": "author"},
                    "order_by": "name",
                    "empty_behavior": "all",
                }
            }

            use_htmx = True
            inline_edit_fields = [
                "title",
                "author",
                "genres",
                "published_date",
                "bestseller",
                "isbn",
                "description",
            ]
        ```

    === "`BookForm`"

        ```python
        class BookForm(forms.ModelForm):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.fields["genres"].required = False
        ```

Why this works:

- The normal create/update form and the inline row share the same dependency rule.
- The inline dependency endpoint rebuilds only the dependent field widget, but it reuses the same form pipeline as the regular edit form.
- When the user changes `author` inline, PowerCRUD syncs the current row controls, posts the row state, rebuilds the `genres` widget, clears the stale selection, and swaps the constrained widget back into the row.

Use this pattern whenever a child dropdown should change immediately in response to another inline field.

For a fuller explanation of `filter_by`, multiple-parent mappings, and migration from older inline-only dependency patterns, see [Forms](./forms.md#dependent-form-fields).

---

## 3. Respect locks and permissions

Inline editing piggybacks on the same hooks the bulk/async flows use:

- `inline_edit_requires_perm` – e.g. `"sample.change_book"`.
- `inline_edit_allowed(self, obj, request)` – custom per-row checks.
- `is_inline_row_locked(self, obj)` / `get_inline_lock_details(self, obj)` – pair with `AsyncManager` to keep rows read-only while background jobs run.

When a guard fails:

- The row swaps back to read-only and emits `inline-row-locked` or `inline-row-forbidden`.
- Action buttons and extra per-row actions marked `lock_sensitive` are disabled automatically.
- The list payload exposes `_blocked_reason` / `_blocked_label` so you can show tooltips or badges even before a user clicks.

The DaisyUI template also disables Save/Cancel buttons and shows a spinner while HTMX POSTs are in-flight, matching the regular object form behaviour.

---

## 4. Know the client-side events

```text
inline-row-saved     # payload: {"pk": …}
inline-row-error     # payload: {"pk": …, "message": …}
inline-row-locked    # payload: {"message": …, "refresh": {...}}
inline-row-forbidden # payload: {"message": …}
```

- Listen for these events (e.g. via `document.body.addEventListener`) to flash custom banners or refresh related widgets.
- The inline helper script already listens for `inline-row-locked` / `inline-row-forbidden`, shows a toast with an optional “Refresh Row” button, and clears the active state.
- When a row finishes saving, HTMX swaps the table row back to display mode and restores the previous column widths so the layout does not jump.

---

## 5. UX notes & troubleshooting

- **Fields you don’t expose inline** – Stock inline editing reposts the rest of the full form as hidden inputs, so saves preserve non-rendered values and validate against the same form surface as regular edits. `inline_preserve_required_fields` remains as a defensive fallback for custom inline builders that still omit required inputs from POST data.
- **Column widths** – editable columns reserve a small width buffer so swapping to a widget (with icons or date pickers) does not push neighbouring columns. Non-editable columns keep their natural width.
- **Single-select fields** – eligible dropdowns are enhanced with Tom Select by default, so users can type to filter options inline without changing backend form contracts. Disable globally with `searchable_selects = False` or per field with `get_searchable_select_enabled_for_field()`.
- **Multi-select fields** – a row can temporarily grow taller when editing ManyToMany fields (e.g., genres). This is expected; if you need a single-line control, swap the widget for a chips/combobox style component.
- **HTMX targets** – inline rows target themselves (`hx-target="#pc-row-{{ pk }}"`) so partial updates do not reload the entire table.
- **Keyboard flow** – the row automatically focuses the cell that triggered edit mode (or the first editable field) so users can start typing immediately. Text/number inputs are pre-selected on first focus so typing replaces the current value. Press `Enter` to trigger the same Save action as the button (except inside textareas), and `Esc` mirrors the Cancel button. `<Tab>` will tab between editable fields in the row.
- **Testing** – unit tests can call `_dispatch_inline_row()` and `_dispatch_inline_dependency()` directly (see `src/tests/test_inline_editing_mixin.py` for a harness). Browser tests should assert the `inline-row-*` triggers fire correctly.

### Manual test checklist for dependent inline fields

1. Open a row in inline mode.
2. Change the parent dropdown.
3. Confirm the child field clears immediately.
4. Re-open the child dropdown without saving the row.
5. Confirm only the allowed options are present.
6. Save the row and confirm the same constraint still applies when reopening inline mode.

Continue with [Bulk editing (synchronous)](bulk_edit_sync.md) if you also need row-level bulk operations, or jump ahead to [Async Manager](async_manager.md) / [Bulk editing (async)](bulk_edit_async.md) once you want background processing and conflict locks.
