# Bulk Editing (Synchronous)

Let users edit or delete multiple records at once without bringing async into the picture yet. This chapter shows the minimum configuration, common tweaks, and guardrails. Async queuing, progress, and conflict locks arrive in the next chapter.

---

## Prerequisites

- [Setup & Core CRUD basics](./setup_core_crud.md) completed (PowerCRUD view up and running).
- HTMX + modals enabled (`use_htmx = True`, `use_modal = True`).
- Your templates include the HTMX script and modal markup (as per [Setup & Core CRUD basics](./setup_core_crud.md)).

---

## 1. Enable bulk edit & delete

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Project
    base_template_path = "myapp/base.html"

    use_htmx = True
    use_modal = True

    bulk_fields = ["status", "owner", "priority"]
    bulk_delete = True
```

Every entry in `bulk_fields` must also appear in your normal `fields` list (or be part of the model’s editable fields) so the bulk form can render and save correctly.

- `bulk_fields` lists the fields that appear in the bulk edit form.
- `bulk_delete = True` adds a “Delete selected” option.
- HTMX + modal support are required for the bulk UI.

Selections persist across pagination because PowerCRUD stores them in the session for the current view.

---

## 2. Validation & save behaviour

By default PowerCRUD runs `full_clean()` and then `save()` for each object. If you trust the inputs and want throughput:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # …
    bulk_full_clean = False   # skip full_clean per object
```

Operations remain atomic—if any record fails the whole transaction rolls back.

---

## 3. Dropdowns & choices {#dropdowns-choices}

### Configure dropdowns

These settings control the dropdowns users see when editing choice/foreign key fields in the bulk form.

#### Sort dropdown options

```python
dropdown_sort_options = {
    "owner": "name",
    "priority": "-order",
}
```

#### Restrict options

Override `get_bulk_choices_for_field` if the defaults are too broad:

```python
def get_bulk_choices_for_field(self, field_name, field):
    qs = super().get_bulk_choices_for_field(field_name, field)
    if field_name == "owner":
        return qs.filter(active=True)
    return qs
```

---

## 4. Selection persistence

PowerCRUD stores selections per view in the Django session. They survive pagination, sorting, and filter changes until the user clears them (or the session expires). You can scope them further:

```python
def get_bulk_selection_key_suffix(self):
    return f"user_{self.request.user.id}"
```

This keeps each user’s selection independent.

### Select all matching records

When at least one row is selected and the active filtered queryset still contains additional rows, PowerCRUD can offer a contextual bulk-selection action on the metadata line above the table.

- Set `show_bulk_selection_meta = False` if you want to hide this metadata action row independently of `show_record_count`.
- The action adds rows from the **currently filtered queryset**, in the queryset's current ordering, into the persisted bulk selection.
- Existing selections outside the current filter are preserved.
- If the user changes filters afterward, the global bulk-selection count stays as-is until they clear it.
- When the filtered queryset is larger than the remaining capacity, PowerCRUD offers a clickable capped action such as `Add 998 more from 1030 matching records`.

Configure the global cap in `POWERCRUD_SETTINGS`:

```python
POWERCRUD_SETTINGS = {
    "BULK_MAX_SELECTED_RECORDS": 1000,
}
```

This cap is a PowerCRUD product limit for the current bulk-selection pipeline. It is separate from Django's lower-level `DATA_UPLOAD_MAX_NUMBER_FIELDS` safeguard.

In practice, `BULK_MAX_SELECTED_RECORDS` should usually be at or below `DATA_UPLOAD_MAX_NUMBER_FIELDS`. If you raise the PowerCRUD cap, you will often also need to raise Django's field-count limit. Keep in mind the safe usable limit is slightly lower than `DATA_UPLOAD_MAX_NUMBER_FIELDS`, because bulk edit submissions also include CSRF, field toggles, and edited values.

??? note "Table of Illustrative Record Selection States"

    | Situation | Result line | Toolbar / selection UI |
    |-------------|-------------|------------------------|
    | No filters, nothing selected | `Showing 1-15 of 173 total records` | no bulk controls |
    | 4 rows selected on current page | `Showing 1-15 of 173 total records` | `Bulk Edit 4`, `Clear Selection` |
    | 4 rows selected, total 173, within cap | `Showing 1-15 of 173 total records` | `Bulk Edit 4`, `Clear Selection`, plus `Select all 173 matching records` on the metadata line |
    | 5 rows selected, total 1032, default cap 1000 | no record-count line unless enabled | `Bulk Edit 5`, `Clear Selection`, plus `Add 995 more from 1032 matching records` on the metadata line |
    | User clicked `Select all 173 matching records` | `Showing 1-15 of 173 total records` | `Bulk Edit 173`, `Clear Selection` |
    | User later changes filter and only 50 rows display, but 173 remain selected globally | `Showing 1-15 of 50 matching records` | `Bulk Edit 173`, `Clear Selection` |

---

## 5. UX hints

???+ info "Hints for UX Refinements"

    | Requirement | Why it matters |
    |-------------|----------------|
    | `DATA_UPLOAD_MAX_NUMBER_FIELDS` | If users select thousands of rows, raise this Django setting to avoid request truncation. Keep it aligned with your PowerCRUD bulk-selection cap. |
    | `POWERCRUD_SETTINGS["BULK_MAX_SELECTED_RECORDS"]` | Caps how many records PowerCRUD will allow in the persisted selection for the current bulk-selection flow. Default is `1000`, and it should usually be at or below Django's `DATA_UPLOAD_MAX_NUMBER_FIELDS`. |
    | Clear feedback | Bulk operations run immediately; add success/error messages or redirect logic in your view if needed. |
    | Template tweaks | Copy the bulk modal template with `pcrud_mktemplate` if you want to change layout or copy. |

---

## 6. Troubleshooting

- **Nothing happens when I click “Bulk edit”** – confirm `use_htmx`/`use_modal` are `True` and the HTMX script is loaded.
- **Validation errors but selections disappear** – confirm you did not override the bulk form template without preserving the hidden selection field.
- **Pagination loses checks** – ensure you are not overriding the list template in a way that removes the selection persistence script.

For a full list of settings (including every bulk_* option) see the [configuration reference](../reference/config_options.md).

## Next steps

Bulk editing is now running synchronously. Continue with [Bulk editing (async)](bulk_edit_async.md) to move long-running operations into the background.
