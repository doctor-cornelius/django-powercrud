# Configuration Options

Complete alphabetical reference of all available configuration options with defaults, types, and descriptions.

## Core Configuration

| Setting | Type | Default | Description | Reference |
|---------|------|---------|-------------|-----------|
| `action_button_classes` | str | `''` | Additional CSS classes for action buttons (edit, delete, etc.) | [Section 06](../guides/06_styling_tailwind.md) |
| `base_template_path` | str | Framework-specific | Path to your project's base template | [Section 01](../guides/01_setup_core_crud.md) |
| `bulk_async` | bool | `False` | Enable asynchronous processing for bulk operations | [Section 04](../guides/04_bulk_edit_async.md) |
| `bulk_async_backend` | str | `'q2'` | Backend for async processing (currently only 'q2' supported) | [Section 04](../guides/04_bulk_edit_async.md) |
| `bulk_async_notification` | str | `'status_page'` | Notification method for async operations ('status_page', 'email', 'messages') | [Section 04](../guides/04_bulk_edit_async.md) |
| `bulk_delete` | bool | `False` | Enable bulk delete functionality | [Section 02](../guides/02_bulk_edit_sync.md) |
| `bulk_fields` | list | `[]` | List of fields available for bulk editing | [Section 02](../guides/02_bulk_edit_sync.md) |
| `bulk_full_clean` | bool | `True` | Run full_clean() on each object during bulk operations | [Section 02](../guides/02_bulk_edit_sync.md) |
| `bulk_min_async_records` | int | `20` | Minimum number of records to trigger async processing | [Section 04](../guides/04_bulk_edit_async.md) |
| `default_htmx_target` | str | `'#content'` | Default target for HTMX responses | [Section 01](../guides/01_setup_core_crud.md) |
| `detail_exclude` | list | `[]` | Fields to exclude from detail view | [Section 01](../guides/01_setup_core_crud.md) |
| `detail_fields` | list/str | Same as `fields` | Fields to show in detail view (`'__all__'`, `'__fields__'`, or list) | [Section 01](../guides/01_setup_core_crud.md) |
| `detail_properties` | list/str | `[]` | Properties to show in detail view (`'__all__'`, `'__properties__'`, or list) | [Section 01](../guides/01_setup_core_crud.md) |
| `detail_properties_exclude` | list | `[]` | Properties to exclude from detail view | [Section 01](../guides/01_setup_core_crud.md) |
| `dropdown_sort_options` | dict | `{}` | Sort options for dropdown fields (applies to forms, filters, bulk operations) | [Section 02](../guides/02_bulk_edit_sync.md) |
| `exclude` | list | `[]` | Fields to exclude from list view | [Section 01](../guides/01_setup_core_crud.md) |
| `extra_actions` | list | `[]` | Additional actions for each record in the list | [Complete Example](complete_example.md) |
| `extra_button_classes` | str | `''` | Additional CSS classes for extra buttons at top of page | [Section 06](../guides/06_styling_tailwind.md) |
| `extra_buttons` | list | `[]` | Additional buttons at the top of the page | [Complete Example](complete_example.md) |
| `fields` | list/str | All model fields | Fields to show in list view (`'__all__'` or list) | [Section 01](../guides/01_setup_core_crud.md) |
| `filter_queryset_options` | dict | `{}` | Restrict options in filter dropdowns | [Filter controls](#filter-controls) |
| `filter_sort_options` | dict | `{}` | Sort options for filter dropdown fields | [Filter controls](#filter-controls) |
| `filterset_class` | FilterSet | Auto-generated | Custom filterset class for advanced filtering | [Filter controls](#filter-controls) |
| `filterset_fields` | list | `[]` | Fields to enable filtering on | [Filter controls](#filter-controls) |
| `form_class` | ModelForm | Auto-generated | Custom form class (overrides form_fields) | [Form controls](#form-controls) |
| `form_fields` | list/str | Editable fields from `detail_fields` | Fields to include in forms (`'__all__'`, `'__fields__'`, or list) | [Form controls](#form-controls) |
| `form_fields_exclude` | list | `[]` | Fields to exclude from forms | [Form controls](#form-controls) |
| `hx_trigger` | str/dict | `None` | Custom HTMX triggers for responses | [Section 01](../guides/01_setup_core_crud.md) |
| `m2m_filter_and_logic` | bool | `False` | Use AND logic for M2M filters (default is OR) | [Filter controls](#filter-controls) |
| `modal_id` | str | `"powercrudBaseModal"` | ID of modal container | [Section 01](../guides/01_setup_core_crud.md) |
| `modal_target` | str | `"powercrudModalContent"` | Target for modal content (no # prefix) | [Section 01](../guides/01_setup_core_crud.md) |
| `model` | Model | **Required** | Django model class for the CRUD view | [Section 01](../guides/01_setup_core_crud.md) |
| `namespace` | str | `None` | URL namespace (must match app_name in urls.py) | [Section 01](../guides/01_setup_core_crud.md) |
| `paginate_by` | int | `None` | Default page size (enables pagination) | [Section 01](../guides/01_setup_core_crud.md) |
| `properties` | list/str | `[]` | Properties to show in list view (`'__all__'` or list) | [Section 01](../guides/01_setup_core_crud.md) |
| `properties_exclude` | list | `[]` | Properties to exclude from list view | [Section 01](../guides/01_setup_core_crud.md) |
| `table_classes` | str | `''` | Additional CSS classes for tables | [Section 06](../guides/06_styling_tailwind.md) |
| `table_header_min_wrap_width` | int | Same as `table_max_col_width` | Minimum width for column headers when they wrap (ch units) | [Section 06](../guides/06_styling_tailwind.md) |
| `table_max_col_width` | int | `25` | Maximum column width in characters | [Section 06](../guides/06_styling_tailwind.md) |
| `table_max_height` | int | `70` | Max table height as percentage of remaining viewport | [Section 06](../guides/06_styling_tailwind.md) |
| `table_pixel_height_other_page_elements` | int/float | `0` | Height of other page elements in pixels | [Section 06](../guides/06_styling_tailwind.md) |
| `templates_path` | str | `"powercrud/{framework}"` | Path to override templates | [Section 07](../guides/07_customisation_tips.md) |
| `url_base` | str | Model name | Base for URL patterns | [Section 01](../guides/01_setup_core_crud.md) |
| `use_crispy` | bool | `True` if installed | Enable crispy forms styling | [Form controls](#form-controls) |
| `use_htmx` | bool | `None` | Enable HTMX for reactive updates | [Section 01](../guides/01_setup_core_crud.md) |
| `use_modal` | bool | `None` | Enable modal dialogs for CRUD operations | [Section 01](../guides/01_setup_core_crud.md) |

## Settings Configuration

| Setting | Default | Description | Reference |
|---------|---------|-------------|-----------|
| `ASYNC_ENABLED` | `False` | Master toggle for async features | [Section 03](../guides/03_async_manager.md) |
| `CACHE_NAME` | `'default'` | Cache alias used for conflict locks and progress | [Section 03](../guides/03_async_manager.md) |
| `CONFLICT_TTL` | `3600` | Cache TTL (seconds) for lock entries | [Section 03](../guides/03_async_manager.md) |
| `PROGRESS_TTL` | `7200` | Cache TTL (seconds) for progress entries | [Section 03](../guides/03_async_manager.md) |
| `CLEANUP_GRACE_PERIOD` | `86400` | Grace period before scheduled cleanup reclaims tasks | [Section 03](../guides/03_async_manager.md) |
| `MAX_TASK_DURATION` | `3600` | Threshold for treating a task as stuck | [Section 03](../guides/03_async_manager.md) |
| `CLEANUP_SCHEDULE_INTERVAL` | `300` | Suggested interval (seconds) for scheduled cleanup jobs | [Section 03](../guides/03_async_manager.md) |
| `POWERCRUD_CSS_FRAMEWORK` | `'daisyui'` | CSS framework choice (`'daisyui'`, `'bootstrap5'`, or custom) | [Section 06](../guides/06_styling_tailwind.md) |
| `TAILWIND_SAFELIST_JSON_LOC` | `None` | Location for Tailwind safelist file generation | [Section 06](../guides/06_styling_tailwind.md) |

## Filter controls

Fine-tune what users can filter and how options are presented by combining `filterset_fields`, `filter_queryset_options`, `filter_sort_options`, and `m2m_filter_and_logic`. Start with the [Filtering & sorting walkthrough](../guides/01_setup_core_crud.md#filtering-sorting) and the dropdown guidance in [Bulk editing (synchronous)](../guides/02_bulk_edit_sync.md#dropdowns-choices).

## Form controls

Override or refine the automatically generated forms with `form_class`, `form_fields`, and `form_fields_exclude`, and enable Crispy Forms support via `use_crispy`. See the form configuration examples in [Core CRUD basics](../guides/01_setup_core_crud.md#7-common-adjustments) and the complete view example in [reference/complete_example.md](complete_example.md).

## Notes

- **Required settings**: Only `model` and `base_template_path` are required
- **Auto-detection**: `use_crispy` and `use_htmx` auto-detect library availability
- **Dependencies**: Bulk operations require both `use_htmx = True` and `use_modal = True`
- **Field shortcuts**: Use `'__all__'` for all fields, `'__fields__'` to reference the `fields` setting
- **Property shortcuts**: Use `'__all__'` for all properties, `'__properties__'` to reference the `properties` setting
