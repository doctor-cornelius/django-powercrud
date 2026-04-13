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

Every entry in `bulk_fields` must be an editable model field. If you include a field with `editable=False`, PowerCRUD raises a configuration error during view setup. In practice, bulk-edit fields should also appear in your normal `fields` list when you want the list and bulk-edit surfaces to stay aligned.

- `bulk_fields` lists the fields that appear in the bulk edit form.
- `bulk_delete = True` adds a “Delete selected” option.
- HTMX + modal support are required for the bulk UI.
- The server validates `fields_to_update` against configured `bulk_fields`, so tampered POST payloads cannot update fields outside the declared bulk-edit surface.

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

### Routing sync bulk updates through one hook

Once PowerCRUD has built the normalized sync bulk payload, it routes the write through `persist_bulk_update(...)`:

For the canonical contract, see the [Hooks reference](../reference/hooks.md#persist_bulk_update).

If you want a more practical walkthrough of routing sync bulk writes through an app service, see [Persistence Hooks for Real Write Logic](advanced/persistence_hooks_sync.md).

```python
def persist_bulk_update(
    self,
    *,
    queryset,
    fields_to_update,
    field_data,
    progress_callback=None,
):
    return super().persist_bulk_update(
        queryset=queryset,
        fields_to_update=fields_to_update,
        field_data=field_data,
        progress_callback=progress_callback,
    )
```

Use this hook when the app wants PowerCRUD to keep the modal UI, payload normalization, and result handling, but wants the actual sync bulk write orchestration to live in an application service.

Notes:

- `fields_to_update` is the normalized list of selected bulk-edit fields.
- `field_data` contains the normalized field payload PowerCRUD built from the request, including relation and many-to-many metadata.
- The hook returns the standard PowerCRUD bulk result dict with `success`, `success_records`, and `errors`.
- This hook is sync bulk-update only in this release. Bulk delete and async bulk persistence are follow-up concerns.

### Handling validation errors in `persist_bulk_update()`

If your bulk write logic needs to validate each selected row before the batch is applied, return the normal handled PowerCRUD bulk result payload instead of raising an unhandled exception.

In the current contract:

- `success` is `False`
- `success_records` is usually `0` for a validation failure in the built-in transactional path
- `errors` is a list of `(label, messages)` tuples
- PowerCRUD re-renders the bulk edit modal with those errors and keeps the selection in place

Example pattern for a bulk status-style update:

```python
def persist_bulk_update(
    self,
    *,
    queryset,
    fields_to_update,
    field_data,
    progress_callback=None,
):
    errors = []

    for obj in queryset:
        for item in field_data:
            if item["field"] == "status":
                obj.status = item["value"]

        try:
            obj.full_clean()
        except ValidationError as exc:
            if hasattr(exc, "message_dict"):
                for field, messages in exc.message_dict.items():
                    errors.append((field, list(messages)))
            else:
                errors.append(
                    ("general", list(getattr(exc, "messages", [str(exc)])))
                )

    if errors:
        return {
            "success": False,
            "success_records": 0,
            "errors": errors,
        }

    for obj in queryset:
        obj.save()

    return {
        "success": True,
        "success_records": queryset.count(),
        "errors": [],
    }
```

Important behavior notes:

- The built-in sync bulk update path is transactional. If validation fails while the built-in backend is applying the batch, the transaction is rolled back and the modal shows the handled errors.
- If you override `persist_bulk_update(...)`, your app owns the validation strategy. You can still preserve PowerCRUD's UI behavior by returning the same handled result shape.
- The first tuple item in `errors` is a generic label such as a field name or `"general"`. It is not limited to object primary keys.

If you want a real importable sample of this pattern, see the sample app note in [Sample app overview](../reference/sample_app.md).

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

See the [Hooks reference](../reference/hooks.md#get_bulk_choices_for_field) for the canonical contract for this hook and [Hooks reference](../reference/hooks.md#get_bulk_selection_key_suffix) for bulk selection scoping.

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

!!! note "Current-page range selection"

    End users can `Shift` + click row checkboxes to select or clear a contiguous range on the currently visible page.
    This shortcut only applies to rows rendered on the current page; it does not span pagination boundaries.

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
