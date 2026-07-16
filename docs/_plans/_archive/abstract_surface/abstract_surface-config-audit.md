# Abstract Surface Config Audit

## Purpose

This audit groups the current PowerCRUD configuration surface by concept before any helper API is designed.

The goal is not to reduce option count immediately. The goal is to make the existing public API easier to explain and to identify where future helpers would package stable primitives rather than create a second API.

## TLDR

PowerCRUD's current configuration surface groups into these concept buckets:

1. Surface: the configured working screen for listing, filtering, sorting, paging, selecting, and acting on records.
2. Field intent: how a field or property participates in list, detail, form, inline-edit, link, tooltip, and filter behaviour.
3. Action: user-visible operations exposed through header buttons, row actions, standard CRUD actions, selection controls, and bulk flows.
4. Presentation: where and how screens, links, forms, modals, HTMX swaps, and action targets render.
5. Selection: persisted selected-row state and the rules that selection-aware controls use.
6. Bulk operation: multi-record edit/delete behaviour, validation, persistence, sync/async routing, and feedback.
7. Async operation: long-running task management, conflict locks, progress, lifecycle, cleanup, and dashboard integration.
8. Styling: table sizing, classes, column alignment, inline-edit highlighting, and template/framework presentation.
9. Compatibility and defaults: legacy behaviour, sentinel values, and unset/default rules that preserve existing views.

## Working Rule

Explicit PowerCRUD configuration remains the source of truth.

Any future helper should generate defaults only. It must not override explicit view configuration.

That rule needs design care because some explicit empty values are meaningful. For example, downstream views may set `inline_edit_fields = []`, `form_fields = []`, or `bulk_fields = []` deliberately to disable behaviour.

## Concept Buckets

### Surface

A Surface is the configured working screen: the queryset, list state, filters, sorting, pagination, counts, selection state, and available actions a user works through.

Current options and hooks include:

1. `model`
2. `queryset`
3. `url_base`
4. `namespace`
5. `view_title`
6. `view_instructions`
7. `filterset_fields`
8. `filterset_class`
9. `default_filterset_fields`
10. `filter_queryset_options`
11. `filter_null_fields_exclude`
12. `m2m_filter_and_logic`
13. `dropdown_sort_options`
14. `column_sort_fields_override`
15. `show_record_count`
16. `show_bulk_selection_meta`
17. `paginate_by`
18. `filter_favourites_enabled`
19. `get_queryset()`

Filtering belongs primarily here. Individual fields may contribute metadata, but the Surface owns how the working set is narrowed and refreshed.

### Field Intent

Field intent describes how a model field or property participates in list, detail, form, inline-edit, link, tooltip, and display behaviour.

Current options and hooks include:

1. `fields`
2. `properties`
3. `exclude`
4. `properties_exclude`
5. `detail_fields`
6. `detail_properties`
7. `detail_exclude`
8. `detail_properties_exclude`
9. `form_fields`
10. `form_fields_exclude`
11. `form_display_fields`
12. `form_disabled_fields`
13. `inline_edit_fields`
14. `field_queryset_dependencies`
15. `column_help_text`
16. `column_alignments`
17. `list_cell_tooltip_fields`
18. `get_list_cell_tooltip(...)`
19. `link_fields`
20. `list_cell_link_default_open_in`
21. `get_list_cell_link(...)`

This is the strongest future-helper candidate because one field often appears in multiple lists. It is also the riskiest because the current options have distinct meanings and precedence.

### Action

Actions are user-visible operations exposed at page, selection, row, standard CRUD, or bulk level.

Current options and hooks include:

1. `extra_buttons`
2. `extra_actions`
3. `extra_actions_mode`
4. `extra_actions_dropdown_open_upward_bottom_rows`
5. `can_update_object(...)`
6. `get_update_disabled_reason(...)`
7. `can_delete_object(...)`
8. `get_delete_disabled_reason(...)`
9. `persist_single_object(...)`
10. `persist_bulk_update(...)`

The current row-action API already contains a small declarative contract through `extra_actions`, plus hook names for disabled state. A helper may eventually be useful, but the current structure should be documented before abstraction.

### Presentation

Presentation controls where and how views, links, forms, and actions render.

Current options include:

1. `base_template_path`
2. `templates_path`
3. `use_htmx`
4. `default_htmx_target`
5. `hx_trigger`
6. `use_modal`
7. `modal_id`
8. `modal_target`
9. `modal_classes`
10. `modal_box_classes`
11. `modal_body_classes`
12. `bulk_modal_box_classes`
13. `list_cell_link_default_open_in`
14. `link_fields`

This overlaps with Field intent and Action because links and actions need a target. The concept is useful for documentation, but it may not need a standalone helper yet.

### Selection

Selection is persisted row state used by bulk operations and selection-aware controls.

Current options and hooks include:

1. `show_bulk_selection_meta`
2. `extra_buttons` with `uses_selection`
3. `selection_min_count`
4. `selection_min_behavior`
5. `selection_min_reason`
6. `get_bulk_selection_key_suffix()`
7. `get_selected_ids_from_session(...)`

Selection is a first-class behaviour in use, but the helper pressure currently appears through action/button configuration rather than a separate selection API.

### Bulk Operation

Bulk operation covers multi-record edit/delete, validation, persistence, sync/async routing, and user feedback.

Current options and hooks include:

1. `bulk_fields`
2. `bulk_delete`
3. `bulk_full_clean`
4. `bulk_modal_box_classes`
5. `persist_bulk_update(...)`
6. `bulk_update_persistence_backend_path`
7. `bulk_update_persistence_backend_config`
8. `bulk_async`
9. `bulk_async_conflict_checking`
10. `bulk_min_async_records`
11. `bulk_async_backend`
12. `bulk_async_notification`
13. `bulk_async_allow_anonymous`

Bulk is already a separate primitive. The persistence backend work is a good example of a narrow helper contract rather than a broad recipe abstraction.

### Async Operation

Async operation covers long-running tasks, manager resolution, conflict locks, progress, lifecycle, and dashboard persistence.

Current options include:

1. `async_manager_class`
2. `async_manager_class_path`
3. `async_manager_config`
4. `bulk_async`
5. `bulk_async_backend`
6. `bulk_async_notification`
7. `bulk_async_conflict_checking`

This should stay separate from near-term abstract-surface helpers. It has enough lifecycle complexity to deserve its own design track.

### Styling

Styling controls table sizing, classes, inline-edit highlighting, and framework/template presentation.

Current options include:

1. `table_classes`
2. `action_button_classes`
3. `extra_button_classes`
4. `table_pixel_height_other_page_elements`
5. `table_max_height`
6. `table_max_col_width`
7. `table_header_min_wrap_width`
8. `column_alignments`
9. `inline_edit_always_visible`
10. `inline_edit_highlight_accent`
11. `templates_path`

Styling should mostly remain explicit. Helpers should not hide styling behaviour unless a specific repeated pattern justifies it.

### Compatibility And Defaults

Compatibility-sensitive options and behaviour include:

1. `fields = "__all__"` and default field resolution.
2. `detail_fields = "__fields__"` mirroring resolved list fields.
3. `detail_properties = "__properties__"` mirroring list properties.
4. `form_fields = "__fields__"` using resolved list fields for forms.
5. Legacy `inline_edit_enabled` compatibility behaviour.
6. `default_filterset_fields = None` preserving all-filter-visible behaviour.
7. Future `default_list_fields = None` preserving all-column-visible behaviour.

Any helper design must preserve these defaults.

`default_list_fields` is proposed list-options API, not current live PowerCRUD API. Keep it out of current-option docs until implemented.

## Overlap And Confusion Risks

1. Field intent is spread across many options. A field may appear in `fields`, `properties`, `detail_fields`, `form_fields`, `inline_edit_fields`, `bulk_fields`, `column_help_text`, `list_cell_tooltip_fields`, and `link_fields`.
2. Some options describe visibility while others describe capability. `inline_edit_fields` controls editability, not whether the field appears in the list.
3. Empty lists can be meaningful. They may intentionally disable forms, inline editing, bulk editing, or tooltips.
4. Presentation target appears in both field-level links and action/button specs.
5. Filters and visible columns should remain independent. A hidden column may still be filterable.
6. Properties are list/detail display members, but not editable form or inline fields.
7. Base classes can mutate config before `ConfigMixin` validation, so helper precedence cannot be based only on final attribute values.
8. Some documented or inherited options are not declared directly on `PowerCRUDMixinValidator`, including `model`, `url_base`, `filterset_class`, `filter_queryset_options`, and `filter_favourites_enabled`.

## DDMS Downstream Observations

DDMS is a useful reference because it uses PowerCRUD in broad operational screens.

Observed downstream pressure:

1. The DDMS base view sets shared Surface and Presentation defaults: `use_htmx`, `use_modal`, table sizing, pagination, record counts, favourites, and bulk delete.
2. The DDMS base view mutates `fields` and `list_cell_tooltip_fields` in `__init__` to remove raw attention JSON from list display and add semantic integrity tooltips.
3. DDMS views use explicit empty lists such as `form_fields = []`, `inline_edit_fields = []`, and `bulk_fields = []` to disable behaviour on read-only or review surfaces.
4. Field intent repetition is common: the same names often appear across `fields`, `form_fields`, `inline_edit_fields`, `bulk_fields`, and `detail_fields`.
5. Semantic tooltip patterns are real. DDMS uses `list_cell_tooltip_fields` plus `get_list_cell_tooltip(...)` for attention, blocker, status-mismatch, and workflow-explanation cells.
6. Action patterns are real. DDMS uses `extra_buttons`, `extra_actions`, `disabled_if`, and `disabled_reason` for workflow actions and row handoffs.
7. Focused queue screens inherit broad view config and override only the queryset, title, or a few field lists. This supports documenting Surface as a real concept.
8. Repeated `field_queryset_dependencies` blocks show demand for clearer filtered-choice documentation or helper design, but the current declarative shape already works across forms, inline forms, filters, and bulk relation choices.
9. Explicit empty tooltip config can still be changed by base normalization in DDMS, which proves helper precedence must account for subclass declarations, inherited defaults, and instance-time normalization.

Implication: helper APIs may eventually help, but only if they respect inherited defaults, explicit empty config, and base-class mutation.

## Recommendations

1. Promote concepts and recipes before implementing helpers.
2. Keep `default_list_fields` as a narrow list-options feature, separate from `PowerField`.
3. Treat `PowerField` as a design-note candidate after the audit, not an implementation target.
4. If a helper is designed later, first define a small internal resolver for explicit-vs-inherited config.
5. Document the difference between visibility, capability, and presentation target.
6. Use DDMS-style examples as private evidence, not as public docs until generalized.
7. Document current cross-surface options such as `dropdown_sort_options` and `field_queryset_dependencies` before trying to package them in helpers.

## Candidate Public Docs Shape

A first public docs pass could be:

1. `explanation/concepts.md`: explain Surface, Field intent, Action, Presentation, Selection, Bulk, Async, and Recipe.
2. `guides/advanced/recipes.md`: show current-API recipes only.
3. `reference/config_options.md`: optionally add concept grouping links after the audit is accepted.

Do not document `PowerField` in public docs unless and until it exists.
