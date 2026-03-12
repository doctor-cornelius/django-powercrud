# Configuration Options

Complete alphabetical reference of all available configuration options with defaults, accepted values, and descriptions.

Types are shown next to each setting name. `Accepted values` is the contract for each setting. `None` means the setting is left unset unless the row says otherwise.

## Core Configuration

| Setting | Accepted values | Default | When unset | Description | Reference |
|---------|-----------------|---------|------------|-------------|-----------|
| `action_button_classes` (`str`) | `str` | `""` | Buttons keep the built-in daisyUI/Material classes | Additional CSS classes for the View/Edit/Delete buttons. | [Styling & Tailwind](../guides/styling_tailwind.md) |
| `base_template_path` (`str`) | non-empty `str` | `None` (required) | Invalid when unset; must point at your project’s base template | Template path PowerCRUD inherits from (your site chrome). There is no bundled base layout. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `bulk_async` (`bool`) | `True`, `False` | `False` | Bulk actions run synchronously | Enable asynchronous processing for bulk operations. | [Bulk editing (async)](../guides/bulk_edit_async.md) |
| `bulk_async_allow_anonymous` (`bool`) | `True`, `False` | `True` | Anonymous users may trigger async jobs | Require authentication for async bulk operations by setting to `False`. | [Bulk editing (async)](../guides/bulk_edit_async.md) |
| `bulk_async_backend` (`str`) | `str` | `'q2'` | Uses the django-q2 backend | Backend identifier for async processing. | [Bulk editing (async)](../guides/bulk_edit_async.md) |
| `bulk_async_conflict_checking` (`bool`) | `True`, `False` | `True` | Conflict locks are validated before queuing | Toggle optimistic locking for async bulk edits. | [Bulk editing (async)](../guides/bulk_edit_async.md) |
| `bulk_async_notification` (`str`) | `str`; common values: `'status_page'`, `'email'`, `'messages'` | `'status_page'` | Users are redirected to the status page | Notification mechanism for async jobs. | [Bulk editing (async)](../guides/bulk_edit_async.md) |
| `bulk_delete` (`bool`) | `True`, `False` | `False` | Bulk delete buttons are hidden | Enable bulk delete functionality. | [Bulk editing (synchronous)](../guides/bulk_edit_sync.md) |
| `bulk_fields` (`list[str]`) | `list[str]` | `[]` | Bulk edit form is disabled | Fields exposed in the bulk edit form. | [Bulk editing (synchronous)](../guides/bulk_edit_sync.md) |
| `bulk_full_clean` (`bool`) | `True`, `False` | `True` | Each object runs `full_clean()` during bulk edits | Skip expensive validation by setting to `False`. | [Bulk editing (synchronous)](../guides/bulk_edit_sync.md) |
| `bulk_min_async_records` (`int`) | `int` | `20` | Async path activates when at least 20 rows are selected | Threshold for switching from sync to async bulk operations. | [Bulk editing (async)](../guides/bulk_edit_async.md) |
| `default_htmx_target` (`str`) | `str` | `'#content'` | Responses target the main content container | Default HTMX target selector (ignored when HTMX is off). | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `detail_exclude` (`list[str]`) | `list[str]` | `[]` | Detail view mirrors the resolved `detail_fields` | Remove specific fields from the detail layout. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `detail_fields` (`list/str`) | `None`, `'__all__'`, `'__fields__'`, `list[str]` | `'__fields__'` | Inherits the list view fields | Fields rendered on the detail page. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `detail_properties` (`list/str`) | `None`, `'__all__'`, `'__properties__'`, `list[str]` | `[]` | No properties appear on the detail page | Add computed properties to the detail view. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `detail_properties_exclude` (`list[str]`) | `list[str]` | `[]` | All listed detail properties render | Remove specific properties from the detail page. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `dropdown_sort_options` (`dict`) | `dict[str, str]` | `{}` | PowerCRUD orders dropdowns by `name/title/...` heuristics | Explicit ordering for dropdowns in filters, forms, and bulk edit widgets. | [Bulk editing (synchronous)](../guides/bulk_edit_sync.md) |
| `exclude` (`list[str]`) | `list[str]` | `[]` | Every concrete model field is shown | Remove individual fields from the list view while keeping the rest. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `extra_actions` (`list[dict]`) | `list[action spec]` | `[]` | Only the default action buttons render | Define extra per-row actions (URL, label, attributes). | [Complete Example](complete_example.md) |
| `extra_button_classes` (`str`) | `str` | `""` | Extra buttons use the default button styling | Additional CSS classes shared by every entry in `extra_buttons`. | [Styling & Tailwind](../guides/styling_tailwind.md) |
| `extra_buttons` (`list[dict]`) | `list[button spec]` | `[]` | No extra header buttons are shown | Add top-of-page buttons (e.g., custom actions, links). | [Complete Example](complete_example.md) |
| `fields` (`list/str`) | `None`, `'__all__'`, `list[str]` | `'__all__'` | All concrete model fields show in the list view | Columns displayed in the list view. Combine with `exclude`. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `filter_null_fields_exclude` (`list[str]`) | `list[str]` | `[]` | Nullable auto-generated filters gain built-in null filtering | Opt out specific `filterset_fields` from automatic null-filter controls. | [Filter controls](#filter-controls) |
| `filter_queryset_options` (`dict`) | `dict[str, filter spec]` | `{}` | Filter dropdowns query the entire related table | Restrict or pre-filter related dropdown options per field. | [Filter controls](#filter-controls) |
| `filterset_class` (`FilterSet`) | `None` or `FilterSet` subclass | `None` | A dynamic `FilterSet` is generated from `filterset_fields` | Provide a custom `FilterSet` subclass for complex filtering. | [Filter controls](#filter-controls) |
| `filterset_fields` (`list[str]`) | `list[str]` | `[]` | No filter sidebar is rendered | Fields to include in the auto-generated filterset. | [Filter controls](#filter-controls) |
| `form_class` (`ModelForm`) | `None` or `ModelForm` subclass | `None` | PowerCRUD builds a `ModelForm` from `form_fields` | Override the form entirely with a custom class. | [Form controls](#form-controls) |
| `form_fields` (`list/str`) | `None`, `'__all__'`, `'__fields__'`, `list[str]` | `None` | All editable `detail_fields` appear in the form | Fields included in create/update forms. | [Form controls](#form-controls) |
| `form_fields_exclude` (`list[str]`) | `list[str]` | `[]` | The auto-selected form fields render untouched | Remove individual fields from the generated form. | [Form controls](#form-controls) |
| `field_queryset_dependencies` (`dict \| None`) | `None` or dependency map | `None` | Select fields use their default queryset | Declarative parent/child queryset scoping shared by regular forms and inline forms. | [Form controls](#form-controls) |
| `hx_trigger` (`str/int/float/dict`) | `None`, scalar trigger name, or trigger map | `None` | No HX-Trigger header is sent | Custom HTMX triggers to fire after responses. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `inline_edit_allowed` (`callable`) | `None` or predicate callable | `None` | Every row follows the standard permission checks | Optional predicate to allow/block inline editing per row. | [Inline editing](../guides/inline_editing.md) |
| `inline_edit_fields` (`list/str`) | `None`, `'__all__'`, `'__fields__'`, `list[str]` | `None` | Inline editing is disabled | Fields editable inline. Setting this enables inline editing when HTMX is on; PowerCRUD then filters the list to fields present on the actual form, and only rendered list columns become clickable inline cells. | [Inline editing](../guides/inline_editing.md) |
| `inline_preserve_required_fields` (`bool`) | `True`, `False` | `True` | Inline POSTs must include every required field manually | Reuse the object’s existing values for required form fields that aren’t rendered inline so saves keep working. | [Inline editing](../guides/inline_editing.md) |
| `inline_edit_requires_perm` (`str`) | `None` or `str` | `None` | Inline editing shows for anyone who can edit the object | Permission codename required before showing inline controls. | [Inline editing](../guides/inline_editing.md) |
| `m2m_filter_and_logic` (`bool`) | `True`, `False` | `False` | Multi-select filters use OR logic | Switch ManyToMany filters to AND logic. | [Filter controls](#filter-controls) |
| `modal_id` (`str`) | `None` or `str` | `None` | Falls back to `'powercrudBaseModal'` | DOM id of the modal element (without `#`). | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `modal_target` (`str`) | `None` or `str` | `None` | Falls back to `'powercrudModalContent'` | DOM id of the element that receives modal content. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `model` (`Model`) | Django model class | **Required** | PowerCRUD cannot run without a model | Django model class for the CRUD view. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `namespace` (`str`) | `None` or `str` | `None` | URL names are generated without a namespace | Set to match `app_name` when including the view in namespaced URLs. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `paginate_by` (`int`) | `None` or `int` | `None` | All rows render on one page | Page size for list views; users can override via `?page_size=`. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `properties` (`list/str`) | `None`, `'__all__'`, `list[str]` | `[]` | No computed properties show in the list view | Computed properties to display alongside fields. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `properties_exclude` (`list[str]`) | `list[str]` | `[]` | Every listed property renders | Remove individual properties from the list view. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `searchable_selects` (`bool`) | `None`, `True`, `False` | `True` | Select widgets render as native `<select>` controls | Enable Tom Select enhancement for eligible select fields in regular forms, inline editing, bulk edit forms, and filter forms. | [Form controls](#form-controls) |
| `table_classes` (`str`) | `str` | `""` | Tables use the default daisyUI classes | Additional classes applied to the main table element. | [Styling & Tailwind](../guides/styling_tailwind.md) |
| `table_header_min_wrap_width` (`int`) | `None` or `int` | `None` | Matches `table_max_col_width` | Minimum width (in `ch`) before header labels wrap. | [Styling & Tailwind](../guides/styling_tailwind.md) |
| `table_max_col_width` (`int`) | `None` or positive `int` | `None` | Columns clamp at `25ch` | Maximum column width (in `ch`) for list and inline edit layouts. | [Styling & Tailwind](../guides/styling_tailwind.md) |
| `table_max_height` (`int`) | `int` from `0` to `100` | `70` | Table height is 70% of remaining viewport | Percentage of remaining viewport height allocated to the table. | [Styling & Tailwind](../guides/styling_tailwind.md) |
| `table_pixel_height_other_page_elements` (`int/float`) | non-negative `int` or `float` | `0` | No extra offset is subtracted | Pixels reserved for other fixed-height elements (e.g., navbars). | [Styling & Tailwind](../guides/styling_tailwind.md) |
| `templates_path` (`str`) | `str` | `powercrud/{POWERCRUD_CSS_FRAMEWORK}` | Uses bundled templates for the configured framework | Base directory for all template overrides. | [Customisation tips](../guides/customisation_tips.md) |
| `url_base` (`str`) | `str` | Model name | Defaults to the model’s lowercase name | URL slug used when generating routes (e.g., `project-list`). | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `use_crispy` (`bool`) | `None`, `True`, `False` | `None` | Auto-detects: `True` when `crispy_forms` is installed | Toggle Crispy Forms rendering for generated forms. | [Form controls](#form-controls) |
| `use_htmx` (`bool`) | `None`, `True`, `False` | `None` | HTMX is disabled | Enable HTMX responses (modals, inline updates, partial refreshes). | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `use_modal` (`bool`) | `None`, `True`, `False` | `None` | Modals stay disabled | Enable HTMX-driven modal forms (requires `use_htmx = True`). | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |

## Settings Configuration

All of the following keys live inside the optional `POWERCRUD_SETTINGS` dict in your Django settings. Every entry has a default; you only override what you need.

| Setting | Accepted values | Default | When unset | Description | Reference |
|---------|-----------------|---------|------------|-------------|-----------|
| `ASYNC_ENABLED` (`bool`) | `True`, `False` | `False` | Async helpers remain inactive | Master toggle for async features. | [Async Manager](../guides/async_manager.md) |
| `CACHE_NAME` (`str`) | `str` | `'default'` | Uses Django’s default cache backend | Cache alias used for conflict locks and progress entries. | [Async Manager](../guides/async_manager.md) |
| `CONFLICT_TTL` (`int`) | `int` | `3600` | Locks expire after one hour | Cache TTL (seconds) for conflict lock entries. | [Async Manager](../guides/async_manager.md) |
| `PROGRESS_TTL` (`int`) | `int` | `7200` | Progress data expires after two hours | Cache TTL (seconds) for async progress entries. | [Async Manager](../guides/async_manager.md) |
| `CLEANUP_GRACE_PERIOD` (`int`) | `int` | `86400` | Completed tasks are eligible for cleanup after 24h | Grace period before scheduled cleanup reclaims finished tasks. | [Async Manager](../guides/async_manager.md) |
| `MAX_TASK_DURATION` (`int`) | `int` | `3600` | Tasks longer than an hour are treated as stuck | Threshold for flagging slow async jobs. | [Async Manager](../guides/async_manager.md) |
| `CLEANUP_SCHEDULE_INTERVAL` (`int`) | `int` | `300` | Cleanup jobs should run roughly every 5 minutes | Suggested cadence (seconds) for any periodic cleanup runner. | [Async Manager](../guides/async_manager.md) |
| `POWERCRUD_CSS_FRAMEWORK` (`str`) | `str`; bundled pack: `'daisyUI'` | `'daisyUI'` | Built-in templates and styles target daisyUI | CSS framework choice (`'daisyUI'` or your custom pack). | [Styling & Tailwind](../guides/styling_tailwind.md) |
| `TAILWIND_SAFELIST_JSON_LOC` (`str`) | `str` | `'.'` | Uses the current directory as the default output location | File path for Tailwind safelist output (used by management commands). | [Styling & Tailwind](../guides/styling_tailwind.md) |

## Filter controls

Fine-tune what users can filter and how options are presented by combining `filterset_fields`, `filter_queryset_options`, `dropdown_sort_options`, `filter_null_fields_exclude`, and `m2m_filter_and_logic`. Nullable auto-generated relation filters merge an `Empty only` option into the dropdown, while nullable scalar filters gain companion `... is empty` controls. Use `filter_null_fields_exclude` to opt specific fields out. Start with the [Filtering & sorting walkthrough](../guides/setup_core_crud.md#filtering-sorting) and the dropdown guidance in [Bulk editing (synchronous)](../guides/bulk_edit_sync.md#dropdowns-choices).

## Form controls

Override or refine the automatically generated forms with `form_class`, `form_fields`, `form_fields_exclude`, and `field_queryset_dependencies`, and enable Crispy Forms support via `use_crispy`. See the form configuration examples in [Setup & Core CRUD basics](../guides/setup_core_crud.md#3-shape-list-detail-and-form-scopes), the dedicated [Dependent form fields](../guides/dependent_form_fields.md) guide, and the complete view example in [reference/complete_example.md](complete_example.md).

### Dependent queryset scoping

Use `field_queryset_dependencies` for straightforward cases where one selectable child field should be filtered from another form field.

Example:

```python
field_queryset_dependencies = {
    "genres": {
        "depends_on": ["author"],
        "filter_by": {"authors": "author"},
        "order_by": "name",
        "empty_behavior": "none",
    }
}
```

Supported keys:

- `depends_on`
    Parent form fields whose values drive the child queryset.
- `filter_by`
    Mapping of child queryset lookups to parent form field names.
- `order_by`
    Optional ordering applied after filtering.
- `empty_behavior`
    `"none"` hides all child choices until the parent value is available. `"all"` leaves the queryset unfiltered when the parent value is empty.

Notes:

- This applies to regular create/update forms and inline forms through the same form pipeline.
- PowerCRUD resolves parent values from bound form data first, then the current instance, then any initial form values.
- Keep this for simple equality-style filtering on queryset-backed form fields. For complex business rules, continue using a custom `form_class` or view override.
- `filter_by` maps child queryset lookups to parent form field names. The left-hand side is the lookup used against the child field queryset, while the right-hand side is the parent form field name.

Common mental model:

```python
field_queryset_dependencies = {
    "child_field": {
        "depends_on": ["parent_field"],
        "filter_by": {"child_queryset_lookup": "parent_field"},
    }
}
```

That reads as: “restrict `child_field` choices by filtering its queryset with `child_queryset_lookup=<value of parent_field>`”.

Worked examples:

```python
field_queryset_dependencies = {
    "genres": {
        "depends_on": ["author"],
        "filter_by": {"authors": "author"},
    }
}
```

```python
field_queryset_dependencies = {
    "cmms_asset": {
        "depends_on": ["cmms_property_asset_type_override"],
        "filter_by": {
            "property_asset_type_override": "cmms_property_asset_type_override",
        },
    }
}
```

For a full explanation of `filter_by`, migration from old inline-only configs, and regular-vs-inline behaviour, see [Dependent form fields](../guides/dependent_form_fields.md).

### Searchable select enhancement

PowerCRUD enhances eligible select dropdowns with Tom Select when `searchable_selects = True` (default).

- Applies to regular create/update forms, inline row forms, bulk edit form selects, and filter form selects.
- Single-select fields are enhanced as searchable dropdowns.
- Multi-select filter fields are enhanced as searchable multi-select controls.
- Boolean-style selects remain native controls.
- Preserves normal Django form POST semantics (the underlying `<select>` still submits the selected value).

Per-field opt-out is available via a view hook:

```python
class BookCRUDView(PowerCRUDMixin, CRUDView):
    searchable_selects = True

    def get_searchable_select_enabled_for_field(
        self, field_name: str, bound_field=None
    ) -> bool:
        return field_name != "author"
```

## Inline dependency controls

Use `field_queryset_dependencies` as the primary declaration when one inline field needs another field to be refreshed in the same row. PowerCRUD derives inline dependency wiring from that shared config automatically.

Example:

```python
field_queryset_dependencies = {
    "genres": {
        "depends_on": ["author"],
        "filter_by": {"authors": "author"},
    }
}
```

Notes:

- The child field must also be present in `inline_edit_fields`.
- Parent fields listed in `depends_on` must be inline-editable too.
- PowerCRUD handles the frontend refresh, widget swap, and child queryset restriction when the dependency is declared in `field_queryset_dependencies`.
- PowerCRUD uses the standard `...-inline-dependency` endpoint automatically.
- Older inline-only dependency config is ignored. Move any remaining business rules into `field_queryset_dependencies`.

Migration sketch:

```python
field_queryset_dependencies = {
    "cmms_asset": {
        "depends_on": ["cmms_property_asset_type_override"],
        "filter_by": {
            "property_asset_type_override": "cmms_property_asset_type_override",
        },
    }
}
```

See [Dependent form fields](../guides/dependent_form_fields.md) for a fuller worked example.

## Notes

- **Required settings**: Only `model` and `base_template_path` are required.
- **Auto-detection**: `use_crispy` auto-detects whether `crispy_forms` is installed; everything else is opt-in.
- **Dependencies**: Bulk operations require both `use_htmx = True` and `use_modal = True`.
- **Field shortcuts**: Use `'__all__'` for all fields, `'__fields__'` to reference the `fields` setting.
- **Property shortcuts**: Use `'__all__'` for all properties, `'__properties__'` to reference the `properties` setting.
