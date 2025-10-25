# 02. Bulk editing (synchronous)

Let users edit or delete multiple records at once without bringing async into the picture yet. This chapter shows the minimum configuration, common tweaks, and guardrails. Async queuing, progress, and conflict locks arrive in the next chapter.

---

## Prerequisites

- [Section 01](./01_setup_core_crud.md) completed (PowerCRUD view up and running).
- HTMX + modals enabled (`use_htmx = True`, `use_modal = True`).
- Your templates include the HTMX script and modal markup (as per [Section 01](./01_setup_core_crud.md)).

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

Selections persist across pagination while the user stays on the page.

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

PowerCRUD stores selections per view. You can scope them further:

```python
def get_bulk_selection_key_suffix(self):
    return f"user_{self.request.user.id}"
```

This keeps each user’s selection independent.

---

## 5. UX hints

| Requirement | Why it matters |
|-------------|----------------|
| `DATA_UPLOAD_MAX_NUMBER_FIELDS` | If users select thousands of rows, raise this Django setting to avoid request truncation. |
| Clear feedback | Bulk operations run immediately; add success/error messages or redirect logic in your view if needed. |
| Template tweaks | Copy the bulk modal template with `pcrud_mktemplate` if you want to change layout or copy. |

---

## 6. Troubleshooting

- **Nothing happens when I click “Bulk edit”** – confirm `use_htmx`/`use_modal` are `True` and the HTMX script is loaded.
- **Validation errors but selections disappear** – confirm you did not override the bulk form template without preserving the hidden selection field.
- **Pagination loses checks** – ensure you are not overriding the list template in a way that removes the selection persistence script.

For a full list of settings (including every bulk_* option) see the [configuration reference](../reference/config_options.md).

### Key options

| Setting | Default | Typical values | Purpose |
|---------|---------|----------------|---------|
| `bulk_fields` | `[]` | list of field names | Fields editable in the bulk form. |
| `bulk_delete` | `False` | bool | Enable the “Delete selected” action. |
| `bulk_full_clean` | `True` | bool | Skip per-object validation to speed up saves. |
| `dropdown_sort_options` | `{}` | dict | Order bulk dropdown choices. |
| `get_bulk_choices_for_field` | method | override | Filter/limit available options per field. |
| `get_bulk_selection_key_suffix` | `None` | override | Scope selection persistence (per user/team). |
| `DATA_UPLOAD_MAX_NUMBER_FIELDS` | `1000` | int | Increase if users submit very large selections. |

_See the [configuration reference](../reference/config_options.md) for full definitions and additional settings._

---

## Next steps

Bulk editing is now running synchronously. Continue with [04 Bulk editing (async)](04_bulk_edit_async.md) to move long-running operations into the background.
