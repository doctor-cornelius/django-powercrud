# Configuration Options

Complete alphabetical reference of all available configuration options with defaults, types, and descriptions.

## Core Configuration

| Setting | Type | Default | When unset | Description | Reference |
|---------|------|---------|------------|-------------|-----------|
| `action_button_classes` | str | `""` | Buttons keep the built-in daisyUI/Material classes | Additional CSS classes for the View/Edit/Delete buttons. | [Styling & Tailwind](../guides/styling_tailwind.md) |
| `base_template_path` | str | `powercrud/{POWERCRUD_CSS_FRAMEWORK}/base.html` | Extends PowerCRUD’s bundled base for the selected CSS framework | Template path PowerCRUD inherits from. Override to point at your site chrome. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `bulk_async` | bool | `False` | Bulk actions run synchronously | Enable asynchronous processing for bulk operations. | [Bulk editing (async)](../guides/bulk_edit_async.md) |
| `bulk_async_allow_anonymous` | bool | `True` | Anonymous users may trigger async jobs | Require authentication for async bulk operations by setting to `False`. | [Bulk editing (async)](../guides/bulk_edit_async.md) |
| `bulk_async_backend` | str | `'q2'` | Uses the django-q2 backend | Backend identifier for async processing. | [Bulk editing (async)](../guides/bulk_edit_async.md) |
| `bulk_async_conflict_checking` | bool | `True` | Conflict locks are validated before queuing | Toggle optimistic locking for async bulk edits. | [Bulk editing (async)](../guides/bulk_edit_async.md) |
| `bulk_async_notification` | str | `'status_page'` | Users are redirected to the status page | Notification mechanism for async jobs (`'status_page'`, `'email'`, `'messages'`). | [Bulk editing (async)](../guides/bulk_edit_async.md) |
| `bulk_delete` | bool | `False` | Bulk delete buttons are hidden | Enable bulk delete functionality. | [Bulk editing (synchronous)](../guides/bulk_edit_sync.md) |
| `bulk_fields` | list[str] | `[]` | Bulk edit form is disabled | Fields exposed in the bulk edit form. | [Bulk editing (synchronous)](../guides/bulk_edit_sync.md) |
| `bulk_full_clean` | bool | `True` | Each object runs `full_clean()` during bulk edits | Skip expensive validation by setting to `False`. | [Bulk editing (synchronous)](../guides/bulk_edit_sync.md) |
| `bulk_min_async_records` | int | `20` | Async path activates when at least 20 rows are selected | Threshold for switching from sync to async bulk operations. | [Bulk editing (async)](../guides/bulk_edit_async.md) |
| `default_htmx_target` | str | `'#content'` | Responses target the main content container | Default HTMX target selector (ignored when HTMX is off). | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `detail_exclude` | list[str] | `[]` | Detail view mirrors the resolved `detail_fields` | Remove specific fields from the detail layout. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `detail_fields` | list/str | `'__fields__'` | Inherits the list view fields | Fields rendered on the detail page (`'__all__'`, `'__fields__'`, or a list). | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `detail_properties` | list/str | `[]` | No properties appear on the detail page | Add computed properties to the detail view (`'__properties__'` or list). | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `detail_properties_exclude` | list[str] | `[]` | All listed detail properties render | Remove specific properties from the detail page. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `dropdown_sort_options` | dict | `{}` | PowerCRUD orders dropdowns by `name/title/...` heuristics | Explicit ordering for dropdowns in filters, forms, and bulk edit widgets. | [Bulk editing (synchronous)](../guides/bulk_edit_sync.md) |
| `exclude` | list[str] | `[]` | Every concrete model field is shown | Remove individual fields from the list view while keeping the rest. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `extra_actions` | list[dict] | `[]` | Only the default action buttons render | Define extra per-row actions (URL, label, attributes). | [Complete Example](complete_example.md) |
| `extra_button_classes` | str | `""` | Extra buttons use the default button styling | Additional CSS classes shared by every entry in `extra_buttons`. | [Styling & Tailwind](../guides/styling_tailwind.md) |
| `extra_buttons` | list[dict] | `[]` | No extra header buttons are shown | Add top-of-page buttons (e.g., custom actions, links). | [Complete Example](complete_example.md) |
| `fields` | list/str | `'__all__'` | All concrete model fields show in the list view | Columns displayed in the list view. Combine with `exclude`. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `filter_queryset_options` | dict | `{}` | Filter dropdowns query the entire related table | Restrict or pre-filter related dropdown options per field. | [Filter controls](#filter-controls) |
| `filterset_class` | FilterSet | `None` | A dynamic `FilterSet` is generated from `filterset_fields` | Provide a custom `FilterSet` subclass for complex filtering. | [Filter controls](#filter-controls) |
| `filterset_fields` | list[str] | `[]` | No filter sidebar is rendered | Fields to include in the auto-generated filterset. | [Filter controls](#filter-controls) |
| `form_class` | ModelForm | `None` | PowerCRUD builds a `ModelForm` from `form_fields` | Override the form entirely with a custom class. | [Form controls](#form-controls) |
| `form_fields` | list/str | `None` | All editable `detail_fields` appear in the form | Fields included in create/update forms (`'__fields__'`, `'__all__'`, or list). | [Form controls](#form-controls) |
| `form_fields_exclude` | list[str] | `[]` | The auto-selected form fields render untouched | Remove individual fields from the generated form. | [Form controls](#form-controls) |
| `hx_trigger` | str/dict | `None` | No HX-Trigger header is sent | Custom HTMX triggers to fire after responses. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `inline_edit_allowed` | callable | `None` | Every row follows the standard permission checks | Optional predicate to allow/block inline editing per row. | [Inline editing](../guides/inline_editing.md) |
| `inline_edit_enabled` | bool | `None` | Inline editing is disabled | Toggle inline row editing (requires `use_htmx = True`). | [Inline editing](../guides/inline_editing.md) |
| `inline_edit_fields` | list/str | `None` | Inline editing reuses the resolved `form_fields` list | Fields editable inline (`'__fields__'`, `'__all__'`, or list). | [Inline editing](../guides/inline_editing.md) |
| `inline_preserve_required_fields` | bool | `True` | Inline POSTs must include every required field manually | Reuse the object’s existing values for required form fields that aren’t rendered inline so saves keep working. | [Inline editing](../guides/inline_editing.md) |
| `inline_edit_requires_perm` | str | `None` | Inline editing shows for anyone who can edit the object | Permission codename required before showing inline controls. | [Inline editing](../guides/inline_editing.md) |
| `inline_field_dependencies` | dict \| None | `None` | Inline widgets do not declare dependencies | Dependency metadata for inline widgets (parent fields, endpoints). | [Inline editing](../guides/inline_editing.md) |
| `m2m_filter_and_logic` | bool | `False` | Multi-select filters use OR logic | Switch ManyToMany filters to AND logic. | [Filter controls](#filter-controls) |
| `modal_id` | str | `None` | Falls back to `'powercrudBaseModal'` | DOM id of the modal element (without `#`). | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `modal_target` | str | `None` | Falls back to `'powercrudModalContent'` | DOM id of the element that receives modal content. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `model` | Model | **Required** | PowerCRUD cannot run without a model | Django model class for the CRUD view. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `namespace` | str | `None` | URL names are generated without a namespace | Set to match `app_name` when including the view in namespaced URLs. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `paginate_by` | int | `None` | All rows render on one page | Page size for list views; users can override via `?page_size=`. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `properties` | list/str | `[]` | No computed properties show in the list view | Computed properties to display alongside fields (`'__all__'` or list). | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `properties_exclude` | list[str] | `[]` | Every listed property renders | Remove individual properties from the list view. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `table_classes` | str | `""` | Tables use the default daisyUI classes | Additional classes applied to the main table element. | [Styling & Tailwind](../guides/styling_tailwind.md) |
| `table_header_min_wrap_width` | int | `None` | Matches `table_max_col_width` | Minimum width (in `ch`) before header labels wrap. | [Styling & Tailwind](../guides/styling_tailwind.md) |
| `table_max_col_width` | int | `None` | Columns clamp at `25ch` | Maximum column width (in `ch`) for list and inline edit layouts. | [Styling & Tailwind](../guides/styling_tailwind.md) |
| `table_max_height` | int | `70` | Table height is 70% of remaining viewport | Percentage of remaining viewport height allocated to the table. | [Styling & Tailwind](../guides/styling_tailwind.md) |
| `table_pixel_height_other_page_elements` | int/float | `0` | No extra offset is subtracted | Pixels reserved for other fixed-height elements (e.g., navbars). | [Styling & Tailwind](../guides/styling_tailwind.md) |
| `templates_path` | str | `powercrud/{POWERCRUD_CSS_FRAMEWORK}` | Uses bundled templates for the configured framework | Base directory for all template overrides. | [Customisation tips](../guides/customisation_tips.md) |
| `url_base` | str | Model name | Defaults to the model’s lowercase name | URL slug used when generating routes (e.g., `project-list`). | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `use_crispy` | bool | `None` | Auto-detects: `True` when `crispy_forms` is installed | Toggle Crispy Forms rendering for generated forms. | [Form controls](#form-controls) |
| `use_htmx` | bool | `None` | HTMX is disabled | Enable HTMX responses (modals, inline updates, partial refreshes). | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `use_modal` | bool | `None` | Modals stay disabled | Enable HTMX-driven modal forms (requires `use_htmx = True`). | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |

## Settings Configuration

All of the following keys live inside the optional `POWERCRUD_SETTINGS` dict in your Django settings. Every entry has a default; you only override what you need.

| Setting | Default | When unset | Description | Reference |
|---------|---------|------------|-------------|-----------|
| `ASYNC_ENABLED` | `False` | Async helpers remain inactive | Master toggle for async features. | [Async Manager](../guides/async_manager.md) |
| `CACHE_NAME` | `'default'` | Uses Django’s default cache backend | Cache alias used for conflict locks and progress entries. | [Async Manager](../guides/async_manager.md) |
| `CONFLICT_TTL` | `3600` | Locks expire after one hour | Cache TTL (seconds) for conflict lock entries. | [Async Manager](../guides/async_manager.md) |
| `PROGRESS_TTL` | `7200` | Progress data expires after two hours | Cache TTL (seconds) for async progress entries. | [Async Manager](../guides/async_manager.md) |
| `CLEANUP_GRACE_PERIOD` | `86400` | Completed tasks are eligible for cleanup after 24h | Grace period before scheduled cleanup reclaims finished tasks. | [Async Manager](../guides/async_manager.md) |
| `MAX_TASK_DURATION` | `3600` | Tasks longer than an hour are treated as stuck | Threshold for flagging slow async jobs. | [Async Manager](../guides/async_manager.md) |
| `CLEANUP_SCHEDULE_INTERVAL` | `300` | Cleanup jobs should run roughly every 5 minutes | Suggested cadence (seconds) for any periodic cleanup runner. | [Async Manager](../guides/async_manager.md) |
| `POWERCRUD_CSS_FRAMEWORK` | `'daisyui'` | Built-in templates and styles target daisyUI | CSS framework choice (`'daisyui'` or your custom pack). | [Styling & Tailwind](../guides/styling_tailwind.md) |
| `TAILWIND_SAFELIST_JSON_LOC` | `None` | Must be set or passed via `--output` when running `pcrud_extract_tailwind_classes` | File path for Tailwind safelist output (used by management commands). | [Styling & Tailwind](../guides/styling_tailwind.md) |

## Filter controls

Fine-tune what users can filter and how options are presented by combining `filterset_fields`, `filter_queryset_options`, `dropdown_sort_options`, and `m2m_filter_and_logic`. Start with the [Filtering & sorting walkthrough](../guides/setup_core_crud.md#filtering-sorting) and the dropdown guidance in [Bulk editing (synchronous)](../guides/bulk_edit_sync.md#dropdowns-choices).

## Form controls

Override or refine the automatically generated forms with `form_class`, `form_fields`, and `form_fields_exclude`, and enable Crispy Forms support via `use_crispy`. See the form configuration examples in [Setup & Core CRUD basics](../guides/setup_core_crud.md#3-shape-list-detail-and-form-scopes) and the complete view example in [reference/complete_example.md](complete_example.md).

## Notes

- **Required settings**: Only `model` and `base_template_path` are required.
- **Auto-detection**: `use_crispy` auto-detects whether `crispy_forms` is installed; everything else is opt-in.
- **Dependencies**: Bulk operations require both `use_htmx = True` and `use_modal = True`.
- **Field shortcuts**: Use `'__all__'` for all fields, `'__fields__'` to reference the `fields` setting.
- **Property shortcuts**: Use `'__all__'` for all properties, `'__properties__'` to reference the `properties` setting.
