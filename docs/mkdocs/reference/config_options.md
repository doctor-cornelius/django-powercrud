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
| `bulk_update_persistence_backend_config` (`dict`) | `None` or `dict[str, Any]` | `None` | No backend-specific config is passed | Optional config payload passed into the configured bulk update persistence backend constructor. | [Bulk editing (async)](../guides/bulk_edit_async.md) |
| `bulk_update_persistence_backend_path` (`str`) | `None` or import path `str` | `None` | PowerCRUD uses the built-in bulk update implementation | Optional import path for a worker-safe bulk update persistence backend. When configured, the default sync bulk path and async bulk worker both delegate through it. | [Bulk editing (async)](../guides/bulk_edit_async.md) |
| `bulk_delete` (`bool`) | `True`, `False` | `False` | Bulk delete buttons are hidden | Enable bulk delete functionality. | [Bulk editing (synchronous)](../guides/bulk_edit_sync.md) |
| `bulk_fields` (`list[str]`) | `list[str]` | `[]` | Bulk edit form is disabled | Editable model fields exposed in the bulk edit form. Non-editable fields raise a configuration error. | [Bulk editing (synchronous)](../guides/bulk_edit_sync.md) |
| `bulk_full_clean` (`bool`) | `True`, `False` | `True` | Each object runs `full_clean()` during bulk edits | Skip expensive validation by setting to `False`. | [Bulk editing (synchronous)](../guides/bulk_edit_sync.md) |
| `bulk_min_async_records` (`int`) | `int` | `20` | Async path activates when at least 20 rows are selected | Threshold for switching from sync to async bulk operations. | [Bulk editing (async)](../guides/bulk_edit_async.md) |
| `column_help_text` (`dict[str, str]`) | `None` or `dict[str, str]` | `None` | Column headers render without help icons | Add plain-text help tooltips to specific list headers by field/property name. Only configured columns show the adjacent info trigger. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `column_sort_fields_override` (`dict[str, str]`) | `None` or `dict[str, str]` | `None` | Sortable list columns use their own field names, except direct relations with a concrete `name` field which default to `field__name` | Override the queryset `order_by()` expression used when a visible list column header is clicked. Keys are visible column names; values are Django ordering expressions such as `"author__name"` or `"customer__code"`. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `default_htmx_target` (`str`) | `str` | `'#content'` | Responses target the main content container | Default HTMX target selector (ignored when HTMX is off). | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `default_filterset_fields` (`list[str]`) | `None` or `list[str]` | `None` | All allowed filters render immediately | Limit the initially visible filter subset while keeping the remaining allowed filters available through the built-in Add filter control. Validated against effective filter names from the bound filter form. | [Filter controls](#filter-controls) |
| `detail_exclude` (`list[str]`) | `list[str]` | `[]` | Detail view mirrors the resolved `detail_fields` | Remove specific fields from the detail layout. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `detail_fields` (`list/str`) | `None`, `'__all__'`, `'__fields__'`, `list[str]` | `'__fields__'` | Inherits the list view fields | Fields rendered on the detail page. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `detail_properties` (`list/str`) | `None`, `'__all__'`, `'__properties__'`, `list[str]` | `[]` | No properties appear on the detail page | Add computed properties to the detail view. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `detail_properties_exclude` (`list[str]`) | `list[str]` | `[]` | All listed detail properties render | Remove specific properties from the detail page. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `dropdown_sort_options` (`dict`) | `dict[str, str]` | `{}` | PowerCRUD orders dropdowns by `name/title/...` heuristics | Explicit ordering for dropdowns in filters, forms, and bulk edit widgets. | [Bulk editing (synchronous)](../guides/bulk_edit_sync.md) |
| `exclude` (`list[str]`) | `list[str]` | `[]` | Every concrete model field is shown | Remove individual fields from the list view while keeping the rest. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `extra_actions` (`list[dict]`) | `list[action spec]` | `[]` | Only the default action buttons render | Define extra per-row actions (URL, label, attributes). | [Complete Example](complete_example.md) |
| `extra_actions_mode` (`str`) | `'buttons'`, `'dropdown'` | `'buttons'` | Extra row actions render as visible buttons after the standard actions | Control how row-level `extra_actions` are rendered. Use `'dropdown'` to keep `View/Edit/Delete` visible and move only the extra row actions into a `More` overflow menu. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `extra_actions_dropdown_open_upward_bottom_rows` (`int`) | `int >= 0` | `3` | All `More` menus open downward | In dropdown mode, open the `More` menu upward for the last N rendered rows on the current page. Set `0` to disable this behavior. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `extra_button_classes` (`str`) | `str` | `""` | Extra buttons use the default button styling | Additional CSS classes shared by every entry in `extra_buttons`. | [Styling & Tailwind](../guides/styling_tailwind.md) |
| `extra_buttons` (`list[dict]`) | `list[button spec]` | `[]` | No extra header buttons are shown | Add top-of-page buttons (e.g., custom actions, links). | [Complete Example](complete_example.md) |
| `filter_favourites_enabled` (`bool`) | `True`, `False` | `False` | No saved-favourites toolbar is rendered | Enable the optional saved filter favourites UI for this list view when the `powercrud.contrib.favourites` app is installed and `powercrud.urls` is mounted under the `powercrud` namespace. | [Saved Filter Favourites](../guides/advanced/filter_favourites.md) |
| `fields` (`list/str`) | `None`, `'__all__'`, `list[str]` | `'__all__'` | All concrete model fields show in the list view | Columns displayed in the list view. Combine with `exclude`. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `filter_null_fields_exclude` (`list[str]`) | `list[str]` | `[]` | Nullable auto-generated filters gain built-in null filtering | Opt out specific `filterset_fields` from automatic null-filter controls. | [Filter controls](#filter-controls) |
| `filter_queryset_options` (`dict`) | `dict[str, filter spec]` | `{}` | Filter dropdowns query the entire related table | Restrict or pre-filter related dropdown options per field. | [Filter controls](#filter-controls) |
| `filterset_class` (`FilterSet`) | `None` or `FilterSet` subclass | `None` | A dynamic `FilterSet` is generated from `filterset_fields` | Provide a custom `FilterSet` subclass for complex filtering. | [Filter controls](#filter-controls) |
| `filterset_fields` (`list[str]`) | `list[str]` | `[]` | No filter sidebar is rendered | Fields to include in the auto-generated filterset. | [Filter controls](#filter-controls) |
| `form_class` (`ModelForm`) | `None` or `ModelForm` subclass | `None` | PowerCRUD builds a `ModelForm` from `form_fields` | Override the form entirely with a custom class. | [Form controls](#form-controls) |
| `form_fields` (`list/str`) | `None`, `'__all__'`, `'__fields__'`, `list[str]` | `None` | All editable `detail_fields` appear in the auto-generated form | Fields included when PowerCRUD generates the form class for you. Ignored when `form_class` is set. | [Form controls](#form-controls) |
| `form_fields_exclude` (`list[str]`) | `list[str]` | `[]` | The auto-selected form fields render untouched | Remove individual fields from the auto-generated form. Ignored when `form_class` is set. | [Form controls](#form-controls) |
| `form_display_fields` (`list[str]`) | `list[str]` | `[]` | No display-only context block is shown above forms | Model fields to render as read-only context above update forms. Can include `editable=False` model fields. | [Form controls](#form-controls) |
| `form_disabled_fields` (`list[str]`) | `list[str]` | `[]` | Every update-form field stays editable | Disable specific update-form inputs while keeping them visible on the form. Must reference fields present on the built form. | [Form controls](#form-controls) |
| `field_queryset_dependencies` (`dict \| None`) | `None` or dependency map | `None` | Select fields use their default queryset | Declarative parent/child queryset scoping shared by regular forms and inline forms. | [Form controls](#form-controls) |
| `hx_trigger` (`str/int/float/dict`) | `None`, scalar trigger name, or trigger map | `None` | No HX-Trigger header is sent | Custom HTMX triggers to fire after responses. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `inline_edit_allowed` (`callable`) | `None` or predicate callable | `None` | Every row follows the standard permission checks | Optional predicate to allow/block inline editing per row. | [Inline editing](../guides/inline_editing.md) |
| `inline_edit_always_visible` (`bool`) | `True`, `False` | `True` | Editable cells keep a subtle always-on hint | Toggle whether inline-editable cells show a resting highlight before hover/focus. Setting this to `False` removes only the resting highlight; hover/focus highlighting still remains active. | [Inline editing](../guides/inline_editing.md) |
| `inline_edit_fields` (`list/str`) | `None`, `'__all__'`, `'__fields__'`, `list[str]` | `None` | Inline editing is disabled | Editable model fields editable inline. Explicit non-editable fields raise a configuration error; after that validation, PowerCRUD still filters the list to fields present on the actual form, only rendered list columns become clickable inline cells, and the inline row reposts the rest of the full form as hidden inputs on save. | [Inline editing](../guides/inline_editing.md) |
| `inline_edit_highlight_accent` (`str`) | hex color `#rgb` or `#rrggbb` | `'#14b8a6'` | Inline editing uses the built-in teal accent | Accent color used to derive the inline-edit resting, hover/focus, and active-row highlight shades. Hex input only. | [Inline editing](../guides/inline_editing.md) |
| `inline_save_refresh_policy` (`str`) | `'reset_if_filtered_out'`, `'keep_page'`, `'reset_page'` | `'reset_if_filtered_out'` | Successful inline saves refresh the current list page unless the saved row falls out of the active filters | Control whether inline-save list refreshes preserve the current `page` query parameter or drop back to page 1. Filtering, sorting, and `page_size` are always preserved. | [Inline editing](../guides/inline_editing.md) |
| `inline_preserve_required_fields` (`bool`) | `True`, `False` | `True` | Stock inline rows already repost non-rendered fields; this remains a fallback for custom omissions | Reuse the object’s existing values for required form fields when a custom inline POST still omits them. | [Inline editing](../guides/inline_editing.md) |
| `inline_edit_requires_perm` (`str`) | `None` or `str` | `None` | Inline editing shows for anyone who can edit the object | Permission codename required before showing inline controls. | [Inline editing](../guides/inline_editing.md) |
| `list_cell_tooltip_fields` (`list[str]`) | `None` or `list[str]` | `None` | No semantic list-cell tooltips are rendered | Opt specific rendered list fields/properties into semantic cell tooltips. PowerCRUD only evaluates configured names that are actually visible in the current list and silently ignores configured names that are not rendered. Hook-backed semantic cell tooltip text may include newline characters for multiline display. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `m2m_filter_and_logic` (`bool`) | `True`, `False` | `False` | Multi-select filters use OR logic | Switch ManyToMany filters to AND logic. | [Filter controls](#filter-controls) |
| `modal_id` (`str`) | `None` or `str` | `None` | Falls back to `'powercrudBaseModal'` | DOM id of the modal element (without `#`). | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `modal_target` (`str`) | `None` or `str` | `None` | Falls back to `'powercrudModalContent'` | DOM id of the element that receives modal content. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `model` (`Model`) | Django model class | **Required** | PowerCRUD cannot run without a model | Django model class for the CRUD view. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `namespace` (`str`) | `None` or `str` | `None` | URL names are generated without a namespace | Set to match `app_name` when including the view in namespaced URLs. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `paginate_by` (`int`) | `None` or `int` | `None` | All rows render on one page | Page size for list views; users can override via `?page_size=`. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `properties` (`list/str`) | `None`, `'__all__'`, `list[str]` | `[]` | No computed properties show in the list view | Computed properties to display alongside fields. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `properties_exclude` (`list[str]`) | `list[str]` | `[]` | Every listed property renders | Remove individual properties from the list view. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `searchable_selects` (`bool`) | `None`, `True`, `False` | `True` | Select widgets render as native `<select>` controls | Enable Tom Select enhancement for eligible select fields in regular forms, inline editing, bulk edit forms, and filter forms. | [Form controls](#form-controls) |
| `show_bulk_selection_meta` (`bool`) | `True`, `False` | `True` | Bulk-selection metadata actions appear above the table when a selection exists | Control the contextual bulk-selection action row independently of `show_record_count`. | [Bulk editing (synchronous)](../guides/bulk_edit_sync.md) |
| `show_record_count` (`bool`) | `True`, `False` | `False` | No results-count metadata is shown above the table | Display a small status line above the list table showing the total filtered queryset size, or the current page slice plus total when pagination is enabled. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
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
| `view_instructions` (`str`) | `None` or non-empty `str` | `None` | No helper text is shown under the list heading | Render plain-text helper copy directly beneath the visible list-page heading. Content is escaped and does not accept HTML. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |
| `view_title` (`str`) | `None` or non-empty `str` | `None` | The visible list heading uses `verbose_name_plural` | Override the visible list-page heading without changing model metadata or other singular/plural UI copy. | [Setup & Core CRUD basics](../guides/setup_core_crud.md) |

## Settings Configuration

All of the following keys live inside the optional `POWERCRUD_SETTINGS` dict in your Django settings. Every entry has a default; you only override what you need.

| Setting | Accepted values | Default | When unset | Description | Reference |
|---------|-----------------|---------|------------|-------------|-----------|
| `ASYNC_ENABLED` (`bool`) | `True`, `False` | `False` | Async helpers remain inactive | Master toggle for async features. | [Async Manager](../guides/async_manager.md) |
| `BULK_MAX_SELECTED_RECORDS` (`int`) | positive `int` | `1000` | Bulk selections can grow to 1000 rows before PowerCRUD stops adding more matching records | Global cap for the synchronous bulk-selection pipeline, including queryset-wide `Select all ...` and capped `Add ... more from ...` metadata actions. Usually keep this at or below Django's `DATA_UPLOAD_MAX_NUMBER_FIELDS`. | [Bulk editing (synchronous)](../guides/bulk_edit_sync.md) |
| `CACHE_NAME` (`str`) | `str` | `'default'` | Uses Django’s default cache backend | Cache alias used for conflict locks and progress entries. | [Async Manager](../guides/async_manager.md) |
| `CONFLICT_TTL` (`int`) | `int` | `3600` | Locks expire after one hour | Cache TTL (seconds) for conflict lock entries. | [Async Manager](../guides/async_manager.md) |
| `PROGRESS_TTL` (`int`) | `int` | `7200` | Progress data expires after two hours | Cache TTL (seconds) for async progress entries. | [Async Manager](../guides/async_manager.md) |
| `CLEANUP_GRACE_PERIOD` (`int`) | `int` | `86400` | Completed tasks are eligible for cleanup after 24h | Grace period before scheduled cleanup reclaims finished tasks. | [Async Manager](../guides/async_manager.md) |
| `MAX_TASK_DURATION` (`int`) | `int` | `3600` | Tasks longer than an hour are treated as stuck | Threshold for flagging slow async jobs. | [Async Manager](../guides/async_manager.md) |
| `CLEANUP_SCHEDULE_INTERVAL` (`int`) | `int` | `300` | Cleanup jobs should run roughly every 5 minutes | Suggested cadence (seconds) for any periodic cleanup runner. | [Async Manager](../guides/async_manager.md) |
| `POWERCRUD_CSS_FRAMEWORK` (`str`) | `str`; bundled pack: `'daisyUI'` | `'daisyUI'` | Built-in templates and styles target daisyUI | CSS framework choice (`'daisyUI'` or your custom pack). | [Styling & Tailwind](../guides/styling_tailwind.md) |
| `TAILWIND_SAFELIST_JSON_LOC` (`str`) | `str` | `'.'` | Uses the current directory as the default output location | File path for Tailwind safelist output (used by management commands). | [Styling & Tailwind](../guides/styling_tailwind.md) |

## Filter controls

Fine-tune what users can filter and how options are presented by combining `filterset_fields`, `default_filterset_fields`, `filter_queryset_options`, `dropdown_sort_options`, `filter_null_fields_exclude`, and `m2m_filter_and_logic`.

???+ note "filterset_fields vs filterset_class"

    `filterset_fields` and `filterset_class` are alternative strategies.

    If you set `filterset_class`, it takes precedence and PowerCRUD does not auto-generate filters from `filterset_fields`.

    These settings only shape the auto-generated `filterset_fields` path:

    - `filter_queryset_options`
    - `filter_null_fields_exclude`
    - `m2m_filter_and_logic`
    - filter-side `dropdown_sort_options`

    These behaviors still apply to both generated and custom filtersets after the filterset exists:

    - `default_filterset_fields`
    - `searchable_selects`
    - HTMX widget attrs when `use_htmx = True` and the custom filterset exposes `setup_htmx_attrs()`

    For custom filtersets, the recommended pattern is still to subclass `HTMXFilterSetMixin` when you want reactive filtering.

`default_filterset_fields` controls which allowed filters are visible on first render.

- Leave it unset to keep the current behavior and show every allowed filter immediately.
- Set it to a subset to keep the remaining allowed filters hidden behind the Add filter control.
- PowerCRUD validates it against the effective filter names from the bound filter form, not only against raw model field names.
- Hidden optional filters become visible automatically when they carry an active value in the URL.
- Visible optional filters persist through the reserved `visible_filters` query parameter until the user removes them explicitly.

Nullable auto-generated filters behave differently by field type:

- Nullable `ForeignKey` and `OneToOneField` filters keep a single dropdown and add an `Empty only` option near the top.
- Nullable scalar filters such as `CharField`, `TextField`, `DateField`, `TimeField`, `IntegerField`, `DecimalField`, `FloatField`, and `BooleanField` gain a separate companion `... is empty` boolean select.
- Companion null controls are rendered immediately after their parent auto-generated filter field in the form.

Auto-generated text filters use `icontains` by default. There is no separate declarative setting to change that lookup expression field by field; use `filterset_class` when you need custom lookup expressions.

`filter_null_fields_exclude` always matches the original model field names listed in `filterset_fields`.

- Use `["birth_date"]`, not `["birth_date__isnull"]`.
- Excluding a nullable scalar field suppresses the generated companion `... is empty` control.
- Excluding a nullable relation field suppresses the merged `Empty only` option.

Example:

```python
filterset_fields = ["owner", "published_date", "status"]
default_filterset_fields = ["owner"]
filter_null_fields_exclude = ["status"]
```

In that configuration, `owner` stays visible by default, while `published_date` and `status` remain allowed but optional. `owner` keeps one dropdown with `Empty only`, `published_date` gains a separate `Published date is empty` companion filter when added, and `status` gets no built-in null helper.

If you want `title` to use `iexact` or `startswith` instead of the generated `icontains` behavior, move that filter into a custom `filterset_class`.

Start with the [Filtering & sorting walkthrough](../guides/setup_core_crud.md#filtering-sorting) and the dropdown guidance in [Bulk editing (synchronous)](../guides/bulk_edit_sync.md#dropdowns-choices).

## Form controls

Override or refine the automatically generated forms with `form_class`, `form_fields`, `form_fields_exclude`, `form_display_fields`, `form_disabled_fields`, and `field_queryset_dependencies`, and enable Crispy Forms support via `use_crispy`. See the field/detail setup examples in [Setup & Core CRUD basics](../guides/setup_core_crud.md#3-shape-list-and-detail-scopes), the dedicated [Forms](../guides/forms.md) guide, and the complete view example in [reference/complete_example.md](complete_example.md).

???+ note "Relationship Between form_class and PowerCRUD Form Parameters"

    `form_class` overrides PowerCRUD form generation.

    If you set `form_class`, PowerCRUD does not use `form_fields` or `form_fields_exclude` to decide which editable fields appear on the form. Those two parameters are for auto-generated forms only.

    PowerCRUD still applies its runtime form behavior after the custom form is built, including `form_disabled_fields`, `form_display_fields`, `field_queryset_dependencies`, `dropdown_sort_options`, `searchable_selects`, and `use_crispy`.

`form_display_fields` and `form_disabled_fields` solve two different problems:

- `form_display_fields` adds a separate read-only `Context` block above update forms. Use it for contextual model data, including `editable=False` fields.
- `form_disabled_fields` keeps a real form input visible but locked on update forms. Because PowerCRUD uses Django field disabling, submitted tampering is ignored and the existing instance value is preserved. This setting does not lock the same field in create forms or inline editing.

### Dependent queryset scoping

Use `field_queryset_dependencies` for straightforward cases where one selectable child field should be filtered from another form field, or where a queryset-backed field should always be restricted to a fixed subset.

Example:

```python
field_queryset_dependencies = {
    "genres": {
        "static_filters": {"is_active": True},
        "depends_on": ["author"],
        "filter_by": {"authors": "author"},
        "order_by": "name",
        "empty_behavior": "none",
    }
}
```

Supported keys:

- `static_filters`
    Fixed queryset lookups that always apply to the field across regular forms, inline forms, and bulk edit dropdowns.
- `depends_on`
    Parent form fields whose values drive the child queryset.
- `filter_by`
    Mapping of child queryset lookups to parent form field names.
- `order_by`
    Optional ordering applied after filtering.
- `empty_behavior`
    `"none"` hides all child choices until the parent value is available. `"all"` leaves the queryset unfiltered when the parent value is empty.

Notes:

- Static queryset rules apply to regular create/update forms, inline forms, and bulk edit dropdowns.
- Dynamic dependency rules apply to regular create/update forms and inline forms through the same form pipeline.
- Overriding `get_bulk_choices_for_field()` bypasses declarative static queryset rules for bulk.
- PowerCRUD resolves parent values from bound form data first, then the current instance, then any initial form values.
- Keep this for simple equality-style filtering on queryset-backed form fields. For complex business rules, continue using a custom `form_class` or view override.
- `filter_by` maps child queryset lookups to parent form field names. The left-hand side is the lookup used against the child field queryset, while the right-hand side is the parent form field name.

Common mental model:

```python
field_queryset_dependencies = {
    "child_field": {
        "static_filters": {"is_active": True},
        "depends_on": ["parent_field"],
        "filter_by": {"child_queryset_lookup": "parent_field"},
    }
}
```

That reads as: “restrict `child_field` choices first by any fixed filters, then by `child_queryset_lookup=<value of parent_field>` when a parent-driven rule exists”.

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

For a full explanation of `filter_by`, migration from old inline-only configs, and regular-vs-inline behaviour, see [Forms](../guides/forms.md#dependent-form-fields).

## Header buttons

Use `extra_buttons` for list-level actions above the table.

Selection-aware buttons can opt into the current persisted bulk selection:

```python
extra_buttons = [
    {
        "url_name": "projects:selected-summary",
        "text": "Selected Summary",
        "display_modal": True,
        "uses_selection": True,
        "selection_min_count": 1,
        "selection_min_behavior": "disable",
        "selection_min_reason": "Select at least one row first.",
    },
]
```

Notes:

- `uses_selection` defaults to `False`.
- `selection_min_count` defaults to `0`.
- `selection_min_behavior` accepts `'allow'` or `'disable'` and defaults to `'allow'`.
- When `uses_selection=True`, the endpoint contract is “operate on current persisted PowerCRUD selection”.
- The endpoint should still validate selection size, permissions, and lock rules server-side.

??? info "Parameter Guide"

    | Parameter | Type | What it does |
    | --- | --- | --- |
    | `url_name` | `str` | Django URL name for the endpoint called by the header button. |
    | `text` | `str` | Visible label rendered on the button. |
    | `button_class` | `str` | Framework-specific button styling class such as `btn-primary`. |
    | `needs_pk` | `bool` | Should usually stay `False` for header buttons because they are not tied to a single row. |
    | `display_modal` | `bool` | Opens the response in the standard modal target when `True`. |
    | `htmx_target` | `str` | HTMX target element to update for non-modal or custom-target flows. |
    | `extra_attrs` | `str` | Raw HTML attributes appended to the button element. |
    | `extra_class_attrs` | `str` | Additional CSS classes appended after the standard button classes. |
    | `uses_selection` | `bool` | Declares that the endpoint should read the current persisted PowerCRUD selection. |
    | `selection_min_count` | `int` | Minimum selected-row count required before the button is considered ready. |
    | `selection_min_behavior` | `'allow' | 'disable'` | Controls whether the button stays clickable or becomes disabled when the selected count is below `selection_min_count`. |
    | `selection_min_reason` | `str` | Tooltip/help text shown when a selection-aware header button is disabled. |

## Row actions

Use `extra_actions` to add per-row actions beyond the built-in `View`, `Edit`, and `Delete` links.

`extra_actions_mode` controls how those extra row actions are displayed:

- `'buttons'` keeps the legacy behavior and renders extra row actions as visible joined buttons.
- `'dropdown'` keeps the standard row actions visible and moves only `extra_actions` into a `More` dropdown.

Example:

```python
extra_actions_mode = "dropdown"
extra_actions_dropdown_open_upward_bottom_rows = 3

extra_actions = [
    {
        "url_name": "sample:author-detail",
        "text": "View Again",
        "needs_pk": True,
        "display_modal": True,
        "disabled_if": "is_view_again_disabled",
        "disabled_reason": "get_view_again_disabled_reason",
    },
]
```

Notes:

- The default is `'buttons'` for backward compatibility.
- `extra_actions_mode` affects only row `extra_actions`, not top-of-page `extra_buttons`.
- In dropdown mode, the `More` trigger uses the framework’s `extra_default` button styling unless you override the framework styles.
- `extra_actions_dropdown_open_upward_bottom_rows` counts from the bottom of the currently rendered rows after filtering and pagination.
- Set `extra_actions_dropdown_open_upward_bottom_rows = 0` to keep every dropdown opening downward.
- `disabled_if` and `disabled_reason` are optional view method names used to disable a row action based on the current object and request.
- `lock_sensitive` remains available when an action should also disable under PowerCRUD's existing lock/blocked-row state.

??? info "Parameter Guide"

    | Parameter | Type | What it does |
    | --- | --- | --- |
    | `url_name` | `str` | Django URL name for the per-row endpoint that the action should call. |
    | `text` | `str` | Visible label for the action button or dropdown entry. |
    | `needs_pk` | `bool` | Usually `True` so the row primary key is included in the URL. |
    | `button_class` | `str` | Styling class used when the action renders as a visible button. |
    | `display_modal` | `bool` | Opens the response in the standard modal target when `True`. |
    | `htmx_target` | `str` | HTMX target element to update for non-modal or custom-target flows. |
    | `hx_post` | `bool` | Sends the action as an HTMX POST instead of the default GET when `True`. |
    | `lock_sensitive` | `bool` | Disables the action automatically when PowerCRUD marks the row as blocked by its existing lock logic. |
    | `disabled_if` | `str` | Name of a view method with signature `(obj, request) -> bool` that decides whether the action is disabled for that row. |
    | `disabled_reason` | `str` | Name of a view method with signature `(obj, request) -> str | None` that returns the disabled tooltip/help text. |

### Searchable select enhancement

PowerCRUD enhances eligible select dropdowns with Tom Select when `searchable_selects = True` (default).

- Applies to regular create/update forms, inline row forms, bulk edit form selects, and filter form selects.
- Single-select fields are enhanced as searchable dropdowns.
- Multi-select filter fields are enhanced as searchable multi-select controls.
- Boolean-style selects remain native controls.
- Preserves normal Django form POST semantics (the underlying `<select>` still submits the selected value).
- When using the built-in daisyUI pack, package CSS overrides Tom Select with daisyUI semantic colors so controls follow the active theme.

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

See [Forms](../guides/forms.md#dependent-form-fields) for a fuller worked example.

## Notes

- **Required settings**: Only `model` and `base_template_path` are required.
- **Auto-detection**: `use_crispy` auto-detects whether `crispy_forms` is installed; everything else is opt-in.
- **Dependencies**: Bulk operations require both `use_htmx = True` and `use_modal = True`.
- **Duplicate entries**: Supported list-style config options quietly remove duplicates and keep the first occurrence.
- **Field shortcuts**: Use `'__all__'` for all fields, `'__fields__'` to reference the `fields` setting.
- **Property shortcuts**: Use `'__all__'` for all properties, `'__properties__'` to reference the `properties` setting.
