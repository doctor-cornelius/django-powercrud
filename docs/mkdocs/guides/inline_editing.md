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
    inline_edit_enabled = True
    inline_edit_fields = ["title", "author", "published_date", "genres"]
```

- `inline_edit_enabled` toggles the feature per view.
- `inline_edit_fields` controls which columns show the hover/focus shim and respond to clicks. Omit it to default to the form fields.
- The mixin automatically injects inline metadata into the row payload and exposes two HTMX endpoints:
  - `…-inline-row` – swaps the display/form row and handles POST saves.
  - `…-inline-dependency` – rebuilds a single field widget for dependent dropdowns.

The DaisyUI template already includes the triggers, Save/Cancel buttons, and `inline-row-*` events; no manual template work is required unless you are overriding the list partial.

---

## 2. Configure dependencies and helpers

Inline editing reuses the existing form machinery, so any widget or queryset customisations carry over. Keep `inline_edit_fields` aligned with whatever the form actually exposes—if a field is excluded from `form_class`, it must also be dropped from the inline list or you’ll get “unknown field” errors. For dynamic dropdowns, declare dependencies and finite endpoints:

```python
class BookCRUDView(PowerCRUDMixin, CRUDView):
    # …
    inline_field_dependencies = {
        "genres": {
            "depends_on": ["author"],
            "endpoint_name": "sample:book-inline-dependency",  # optional override
        }
    }
```

- `depends_on` lists parent fields that should trigger a refresh.
- Each dependent field renders a placeholder + spinner; the JS helper issues a POST to the dependency endpoint and swaps the widget.
- If the underlying form raises a validation error, the inline row re-renders with the field errors plus a banner (`inline-row-error` HTMX trigger).

The same helpers drive both inline rows and lock-sensitive action buttons, so `_build_inline_row_payload()` contains everything the template needs (row id, inline URLs, lock metadata).

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

- **Column widths** – editable columns reserve a small width buffer so swapping to a widget (with icons or date pickers) does not push neighbouring columns. Non-editable columns keep their natural width.
- **Multi-select fields** – a row can temporarily grow taller when editing ManyToMany fields (e.g., genres). This is expected; if you need a single-line control, swap the widget for a chips/combobox style component.
- **HTMX targets** – inline rows target themselves (`hx-target="#pc-row-{{ pk }}"`) so partial updates do not reload the entire table.
- **Testing** – unit tests can call `_dispatch_inline_row()` and `_dispatch_inline_dependency()` directly (see `src/tests/test_inline_editing_mixin.py` for a harness). Browser tests should assert the `inline-row-*` triggers fire correctly.

Continue with [Bulk editing (synchronous)](bulk_edit_sync.md) if you also need row-level bulk operations, or jump ahead to [Async Manager](async_manager.md) / [Bulk editing (async)](bulk_edit_async.md) once you want background processing and conflict locks.
