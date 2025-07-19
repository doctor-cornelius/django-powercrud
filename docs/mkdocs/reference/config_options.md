# Configuration Options

Complete alphabetical reference of all available configuration options with defaults, types, and descriptions.

## Core Configuration

| Setting | Type | Default | Description | Reference |
|---------|------|---------|-------------|-----------|
| `action_button_classes` | str | `''` | Additional CSS classes for action buttons (edit, delete, etc.) | [Styling](../configuration/styling.md#button-classes) |
| `base_template_path` | str | Framework-specific | Path to your project's base template | [Core Config](../configuration/core_config.md#base-template) |
| `bulk_async` | bool | `False` | Enable asynchronous processing for bulk operations | [Bulk Operations](../configuration/bulk_operations.md) |
| `bulk_async_backend` | str | `'q2'` | Backend for async processing (currently only 'q2' supported) | [Bulk Operations](../configuration/bulk_operations.md) |
| `bulk_async_notification` | str | `'status_page'` | Notification method for async operations ('status_page', 'email', 'messages') | [Bulk Operations](../configuration/bulk_operations.md) |
| `bulk_delete` | bool | `False` | Enable bulk delete functionality | [Bulk Operations](../configuration/bulk_operations.md#basic-setup) |
| `bulk_fields` | list | `[]` | List of fields available for bulk editing | [Bulk Operations](../configuration/bulk_operations.md#basic-setup) |
| `bulk_full_clean` | bool | `True` | Run full_clean() on each object during bulk operations | [Bulk Operations](../configuration/bulk_operations.md#validation-control) |
| `bulk_min_async_records` | int | `20` | Minimum number of records to trigger async processing | [Bulk Operations](../configuration/bulk_operations.md) |
| `default_htmx_target` | str | `'#content'` | Default target for HTMX responses | [HTMX & Modals](../configuration/htmx_modals.md#htmx-target) |
| `detail_exclude` | list | `[]` | Fields to exclude from detail view | [Core Config](../configuration/core_config.md#detail-view-customization) |
| `detail_fields` | list/str | Same as `fields` | Fields to show in detail view (`'__all__'`, `'__fields__'`, or list) | [Core Config](../configuration/core_config.md#detail-view-customization) |
| `detail_properties` | list/str | `[]` | Properties to show in detail view (`'__all__'`, `'__properties__'`, or list) | [Core Config](../configuration/core_config.md#detail-view-customization) |
| `detail_properties_exclude` | list | `[]` | Properties to exclude from detail view | [Core Config](../configuration/core_config.md#detail-view-customization) |
| `dropdown_sort_options` | dict | `{}` | Sort options for dropdown fields (applies to forms, filters, bulk operations) | [Form Handling](../configuration/form_handling.md#dropdown-sorting) |
| `exclude` | list | `[]` | Fields to exclude from list view | [Core Config](../configuration/core_config.md#basic-field-selection) |
| `extra_actions` | list | `[]` | Additional actions for each record in the list | [Complete Example](complete_example.md) |
| `extra_button_classes` | str | `''` | Additional CSS classes for extra buttons at top of page | [Styling](../configuration/styling.md#button-classes) |
| `extra_buttons` | list | `[]` | Additional buttons at the top of the page | [Complete Example](complete_example.md) |
| `fields` | list/str | All model fields | Fields to show in list view (`'__all__'` or list) | [Core Config](../configuration/core_config.md#basic-field-selection) |
| `filter_queryset_options` | dict | `{}` | Restrict options in filter dropdowns | [Filtering](../configuration/filtering.md#filter-queryset-options) |
| `filter_sort_options` | dict | `{}` | Sort options for filter dropdown fields | [Filtering](../configuration/filtering.md#filter-sort-options) |
| `filterset_class` | FilterSet | Auto-generated | Custom filterset class for advanced filtering | [Filtering](../configuration/filtering.md#custom-filterset-class) |
| `filterset_fields` | list | `[]` | Fields to enable filtering on | [Filtering](../configuration/filtering.md#simple-filtering) |
| `form_class` | ModelForm | Auto-generated | Custom form class (overrides form_fields) | [Form Handling](../configuration/form_handling.md#custom-form-classes) |
| `form_fields` | list/str | Editable fields from `detail_fields` | Fields to include in forms (`'__all__'`, `'__fields__'`, or list) | [Form Handling](../configuration/form_handling.md#specify-form-fields) |
| `form_fields_exclude` | list | `[]` | Fields to exclude from forms | [Form Handling](../configuration/form_handling.md#specify-form-fields) |
| `hx_trigger` | str/dict | `None` | Custom HTMX triggers for responses | [HTMX & Modals](../configuration/htmx_modals.md#htmx-triggers) |
| `m2m_filter_and_logic` | bool | `False` | Use AND logic for M2M filters (default is OR) | [Filtering](../configuration/filtering.md#many-to-many-filter-logic) |
| `modal_id` | str | `"nominopolitanBaseModal"` | ID of modal container | [HTMX & Modals](../configuration/htmx_modals.md#modal-customization) |
| `modal_target` | str | `"nominopolitanModalContent"` | Target for modal content (no # prefix) | [HTMX & Modals](../configuration/htmx_modals.md#modal-customization) |
| `model` | Model | **Required** | Django model class for the CRUD view | [Core Config](../configuration/core_config.md) |
| `namespace` | str | `None` | URL namespace (must match app_name in urls.py) | [Core Config](../configuration/core_config.md#namespacing) |
| `paginate_by` | int | `None` | Default page size (enables pagination) | [Pagination](../configuration/pagination.md#basic-setup) |
| `properties` | list/str | `[]` | Properties to show in list view (`'__all__'` or list) | [Core Config](../configuration/core_config.md#property-fields) |
| `properties_exclude` | list | `[]` | Properties to exclude from list view | [Core Config](../configuration/core_config.md#property-fields) |
| `table_classes` | str | `''` | Additional CSS classes for tables | [Styling](../configuration/styling.md#table-classes) |
| `table_header_min_wrap_width` | int | Same as `table_max_col_width` | Minimum width for column headers when they wrap (ch units) | [Styling](../configuration/styling.md#column-width-control) |
| `table_max_col_width` | int | `25` | Maximum column width in characters | [Styling](../configuration/styling.md#column-width-control) |
| `table_max_height` | int | `70` | Max table height as percentage of remaining viewport | [Styling](../configuration/styling.md#table-height-control) |
| `table_pixel_height_other_page_elements` | int/float | `0` | Height of other page elements in pixels | [Styling](../configuration/styling.md#table-height-control) |
| `templates_path` | str | `"nominopolitan/{framework}"` | Path to override templates | [Core Config](../configuration/core_config.md#template-overrides) |
| `url_base` | str | Model name | Base for URL patterns | [Core Config](../configuration/core_config.md#custom-url-base) |
| `use_crispy` | bool | `True` if installed | Enable crispy forms styling | [Form Handling](../configuration/form_handling.md#crispy-forms-integration) |
| `use_htmx` | bool | `None` | Enable HTMX for reactive updates | [HTMX & Modals](../configuration/htmx_modals.md#enable-htmx) |
| `use_modal` | bool | `None` | Enable modal dialogs for CRUD operations | [HTMX & Modals](../configuration/htmx_modals.md#enable-modals) |

## Settings Configuration

| Setting | Default | Description | Reference |
|---------|---------|-------------|-----------|
| `NOMINOPOLITAN_CSS_FRAMEWORK` | `'daisyui'` | CSS framework choice (`'daisyui'`, `'bootstrap5'`, or custom) | [Styling](../configuration/styling.md#framework-selection) |
| `NM_TAILWIND_SAFELIST_JSON_LOC` | `None` | Location for Tailwind safelist file generation | [Styling](../configuration/styling.md#safelist-generation) |

## Notes

- **Required settings**: Only `model` and `base_template_path` are required
- **Auto-detection**: `use_crispy` and `use_htmx` auto-detect library availability
- **Dependencies**: Bulk operations require both `use_htmx = True` and `use_modal = True`
- **Field shortcuts**: Use `'__all__'` for all fields, `'__fields__'` to reference the `fields` setting
- **Property shortcuts**: Use `'__all__'` for all properties, `'__properties__'` to reference the `properties` setting