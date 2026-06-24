# PowerCRUD Concepts

PowerCRUD can be used directly through the Base API: class attributes, hooks, lists, and dictionaries. That remains the underlying contract.

As CRUD screens grow, the same ideas appear repeatedly across the settings: a working list surface, field intent, actions, permissions, modals, selection, bulk work, async work, and styling. This page names those ideas so the individual options are easier to reason about.

## Why This Page Exists

The configuration reference tells you what each option does. This page explains what kind of thing you are configuring.

That distinction matters because not every setting that mentions a field has the same job. For example, `fields` controls list display, `filterset_fields` controls filtering, and `inline_edit_fields` controls editability. Those settings can use the same model field name while expressing different intent, and list/filter settings can also use supported queryset annotation names.

## Concept Buckets

### Surface

A Surface is the configured working screen for a model: queryset, list columns, filters, sorting, pagination, record counts, selection state, and available actions.

Surface options include `model`, `queryset`, `url_base`, `view_title`, `view_instructions`, `view_help`, `filterset_fields`, `filterset_class`, `default_filterset_fields`, `list_options_enabled`, `default_list_fields`, `paginate_by`, `show_record_count`, and `get_queryset()`.

Filters belong primarily to the Surface because they narrow the current working set. A field can contribute to filtering, but the Surface owns how filter state is applied and refreshed.

Because the queryset defines the working row set, a Surface can expose supported queryset annotations as first-class list and filter columns. Use this when a database expression belongs in the operational table order instead of being appended as a display-only property.

### Field Intent

Field intent describes how a model field, queryset annotation, or property participates in the screen.

Base Field Intent options include `fields`, `properties`, `detail_fields`, `detail_properties`, `form_fields`, `form_display_fields`, `form_disabled_fields`, `inline_edit_fields`, `bulk_fields`, `field_labels`, `column_help_text`, `list_cell_tooltip_fields`, `link_fields`, and `get_list_cell_link(...)`.

`PowerField` is the Structured Declaration API for repeated Field Intent. It lets you declare repeated field participation in `power_fields`, then PowerCRUD compiles that declaration into the same base configuration. A view must choose one Field Intent style: base Field Intent attributes or `power_fields`.

Keep visibility and capability separate. A field can be filterable while hidden from the list. A field can be visible but not editable. A field can be editable in a form but not inline-editable.

List-column visibility is display state, not field capability. `fields` and `properties` define the allowed rendered columns; `list_options_enabled` lets users show or hide allowed columns for the current session without changing filtering, editability, row actions, or bulk selection. `default_list_fields` optionally narrows the default visible subset.

Queryset annotation fields sit between model fields and properties: they are placed in `fields` order, can participate in generated filters and sorting when the effective queryset exposes the same annotation name, and remain read-only. Properties stay Python attributes listed through `properties`; editable surfaces such as forms, inline editing, and bulk editing still require editable model fields.

### Action

An Action is a user-visible operation: a header button, row action, standard View/Edit/Delete action, selection-aware action, or bulk operation.

Action options and hooks include `extra_buttons`, `extra_actions`, `extra_actions_mode`, `can_update_object(...)`, `get_update_disabled_reason(...)`, `can_delete_object(...)`, `get_delete_disabled_reason(...)`, `persist_single_object(...)`, and `persist_bulk_update(...)`.

`PowerAction` and `PowerButton` are Structured Declaration API objects for reusable `extra_actions` and `extra_buttons` declarations. Base API dictionaries remain the underlying Action API, and may be mixed with `PowerAction` or `PowerButton` entries.

Actions should keep their business rules server-side. Disabled-state hooks and persistence hooks are the right place for rules that should not depend only on frontend affordances.

### Permission

Permission describes whether the current user can perform an operation at all.

Permission-aware affordances let a screen stay readable while hiding or disabling operations that the current user cannot perform. This is different from screen access: a user may be allowed to open a list or detail page while being denied create, edit, delete, approval, export, or other operations on that page.

Permission options and hooks include `permission`, `permission_check`, `permission_behavior`, `permission_denied_reason`, `has_power_permission(...)`, `has_power_create_permission(...)`, `has_power_update_permission(...)`, `has_power_delete_permission(...)`, and `handle_power_permission_denied(...)`.

Keep the concepts separate:

- Permission hooks and permission fields decide whether the user can see or use an operation at all.
- `hidden_if`, `disabled_state`, `can_update_object()`, and `can_delete_object()` describe row or workflow state after permission has passed.
- PowerCRUD-owned Create/Edit/Delete endpoints enforce their permission hooks server-side.
- Downstream-owned custom endpoints must still enforce their own backend permissions.

### Presentation

Presentation controls where and how UI is rendered.

Presentation options include `base_template_path`, `templates_path`, `use_htmx`, `default_htmx_target`, `hx_trigger`, `use_modal`, `modal_id`, `modal_target`, `modal_box_classes`, `bulk_modal_box_classes`, `list_cell_link_default_open_in`, and per-trigger modal settings.

Presentation overlaps with field links and actions because both need a target. The important distinction is that a field or action describes what the user can do; presentation describes where the result opens.

### Selection

Selection is persisted row state used by bulk operations and selection-aware controls.

Selection-related options include `show_bulk_selection_meta`, `extra_buttons` with `uses_selection`, `selection_min_count`, `selection_min_behavior`, `extra_button_selection_controls_disabled`, and selection session helpers.

Selection is separate from visible columns. Hiding or showing columns should not change which rows are selected.

Built-in bulk edit/delete and selection-aware toolbar buttons can both render selector controls. Set `extra_button_selection_controls_disabled = True` if a button uses selected rows, but the list should not show checkboxes just because of that button. This is mainly useful when the selected rows come from somewhere else, or when the page has its own custom way to choose rows. Bulk edit and bulk delete still show checkboxes because they need them.

### Bulk Operation

A Bulk operation applies work to multiple records.

Bulk options and hooks include `bulk_fields`, `bulk_delete`, `bulk_full_clean`, `bulk_modal_box_classes`, `persist_bulk_update(...)`, `bulk_update_persistence_backend_path`, and `bulk_update_persistence_backend_config`.

Bulk configuration should stay explicit because bulk work has validation, permission, persistence, and feedback concerns that are different from single-object form saves.

### Async Operation

Async operation covers long-running work: queueing, conflict checks, progress, lifecycle cleanup, and optional dashboard persistence.

Async options include `bulk_async`, `bulk_async_conflict_checking`, `bulk_min_async_records`, `bulk_async_backend`, `bulk_async_notification`, `async_manager_class_path`, and `async_manager_config`.

Async is related to bulk operation but has its own lifecycle. Treat it as a separate layer when designing or debugging behaviour.

### Styling

Styling controls table sizing, classes, alignments, template packs, inline-edit highlighting, and collapsed screen-help colour/width defaults.

Styling options include `table_classes`, `action_button_classes`, `extra_button_classes`, `table_max_height`, `table_max_col_width`, `table_header_min_wrap_width`, `column_alignments`, `inline_edit_always_visible`, `inline_edit_highlight_accent`, and `templates_path`.

Styling should usually stay explicit. It should not change the data or permission contract of the screen.

### Compatibility And Defaults

Compatibility and defaults preserve existing behaviour when options are omitted.

Examples include `fields = "__all__"`, `detail_fields = "__fields__"`, `detail_properties = "__properties__"`, `form_fields = "__fields__"`, legacy inline-edit compatibility, `default_filterset_fields = None`, `list_options_enabled = None`, and `default_list_fields = None`.

Unset values and explicit empty lists can mean different things. For example, an explicit `inline_edit_fields = []` should be understood as disabling inline editing for that view.

## How To Use This Model

When configuring a view, start by asking which concept you are changing:

1. Is this about the working list screen? Start with Surface options.
2. Is this about how a field appears or behaves? Start with Field intent.
3. Is this a user operation? Start with Action options and hooks.
4. Is this about whether the user may perform an operation? Start with Permission.
5. Is this about where something opens? Start with Presentation.
6. Is this about selected rows? Start with Selection.
7. Is this about many records? Start with Bulk operation.
8. Is this long-running work? Start with Async operation.
9. Is this only visual treatment? Start with Styling.

Then use the reference docs for exact accepted values.

## What This Is Not

These concepts are a mental model, not a replacement API.

PowerCRUD's Base API is already declarative: you configure class attributes, hooks, lists, and dictionaries, and PowerCRUD builds the runtime behavior. The Structured API groups repeated intent into reusable objects, then compiles back to that same base configuration.

See the [Configuration Options](../reference/config_options.md) reference for the full option list.

See [PowerCRUD Recipes](./advanced/recipes.md) for copyable examples that compose these concepts using the Base API.

See [Permission-Aware Affordances](./advanced/permission_aware_affordances.md) when a list screen should be readable by users who cannot use every operation on it.

See [Choosing an API Style](./structured_api/index.md) and [PowerField](./structured_api/powerfields.md) when repeated Field Intent config starts to obscure the screen's actual intent.
