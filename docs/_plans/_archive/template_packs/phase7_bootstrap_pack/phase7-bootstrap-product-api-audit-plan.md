# Phase 7 Bootstrap Product API Coverage Audit

## Status

Audit complete; the 7.10 contract-hardening follow-up is implemented. Its focused default/Bootstrap server and browser gates pass, as do the final canonical default server regression and isolated full default browser regression. This document remains the authoritative record for the post-Phase 7 question: which relevant public PowerCRUD presentation APIs are honoured by the Bootstrap pack, translated into Bootstrap-native behaviour, intentionally unsupported, defective, or still unverified.

The completed Phase 7 child plan and [`phase7-bootstrap-styling-api-audit-plan.md`](phase7-bootstrap-styling-api-audit-plan.md) remain unchanged. This audit uses the earlier styling audit as an input but is deliberately broader and row-oriented.

## Purpose

Validate the Bootstrap pack against the public product-facing presentation contract. The audit is read-only with respect to product code and tests. It may run existing focused verification, but it does not implement fixes or add permanent tests. Findings that need code, test, or documentation changes become follow-up recommendations.

## Scope And Boundaries

Included:

- Documented view configuration and presentation-related getters.
- Structured action/button and list-cell link metadata that changes rendered controls.
- Form, modal, filter, table, list-option, favourites, bulk, async, inline, tooltip, and responsive presentation settings.
- `get_framework_styles()` and the selected pack's style mapping.
- Focused-template override context, semantic hooks, direct fragments, pack selection, assets, and native/crispy form requirements where they affect Bootstrap's product contract.
- Public management-command guidance where it promises a downstream template override contract.

Excluded from the primary matrix:

- Persistence, queryset, permissions, storage, URL, and business-state APIs whose semantics are independent of presentation, except where their output creates a public control or visible state.
- Private runtime internals, except for tracing a public API to the selected Bootstrap template or adapter.
- Subjective visual preference that does not affect the documented API contract.

## Classification

- **Honoured** — Bootstrap applies the documented value directly.
- **Framework-translated** — the semantic outcome works through a Bootstrap-native interpretation.
- **Intentionally unsupported** — an accepted decision excludes the control and that limit is recorded explicitly.
- **Defect** — a relevant public option is accepted but silently ignored or behaves incorrectly.
- **Not applicable** — the contract is explicitly DaisyUI-specific and is not portable by meaning.
- **Unverified** — the available evidence does not establish the result; the missing probe or test is named.

Every inventory item must receive one classification or an explicit documented reason it is not a Bootstrap presentation concern.

## Authoritative Inventory

This is the frozen inventory for the delegated review. A matrix row represents one independently configurable public behaviour; aliases and their corresponding getters may share one row only when they have the same observable contract.

### Core template and page presentation

- `base_template_path`, `templates_path`, `url_base`, `namespace`, `model`, `fields`, `exclude`, `properties`, `properties_exclude`, `detail_fields`, `detail_exclude`, `detail_properties`, `detail_properties_exclude`.
- `view_title`, `view_instructions`, `view_help`, `view_help_default_color`, `view_help_min_width`, `show_record_count`.
- `paginate_by`, `page_size_options`, `page_size_all_enabled`, `default_htmx_target`, `use_htmx`, `use_modal`, `modal_id`, `modal_target`.

### Table, columns, links, and tooltips

- `table_classes`, `table_max_height`, `table_pixel_height_other_page_elements`, `table_max_col_width`, `table_header_min_wrap_width`.
- `column_alignments`, `column_help_text`, `column_sort_fields_override`, `column_value_formats`, `default_datetime_value_format`, `field_labels`.
- `link_fields`, `list_cell_link_default_open_in`, `get_list_cell_link()`.
- `list_cell_tooltip_fields`, `get_list_cell_tooltip()`, field-specific tooltip hooks, `column_help_text`.
- `list_options_enabled`, `default_list_fields`.

### Filters and saved favourites

- `filterset_fields`, `filterset_class`, `default_filterset_fields`, `filter_null_fields_exclude`, `filter_queryset_options`, `m2m_filter_and_logic`, `dropdown_sort_options`.
- `get_filter_queryset_for_field()`, `filter_favourites_enabled`, `get_filter_favourite_user()`.

### Actions, buttons, selection, and row controls

- `action_button_classes`, `extra_button_classes`, `extra_buttons`, `extra_buttons_mode`, `extra_button_selection_controls_disabled`.
- `extra_actions`, `extra_actions_mode`, `extra_actions_dropdown_open_upward_bottom_rows`.
- Structured `PowerAction` and `PowerButton` fields that affect rendering: labels, classes, attributes, modal metadata, selection behaviour, disabled-state behaviour, visibility, permissions, and refresh/clear-selection policy.
- `can_update_object()`, `get_update_disabled_reason()`, `can_delete_object()`, `get_delete_disabled_reason()` where they produce disabled or explanatory presentation.

### Forms, modals, and field presentation

- `form_class`, `form_fields`, `form_fields_exclude`, `form_display_fields`, `form_disabled_fields`, `field_queryset_dependencies`, `dropdown_sort_options`, `use_crispy`.
- `modal_presentation`, `bulk_modal_presentation`, and deprecated `modal_classes`, `modal_box_classes`, `modal_body_classes`, `bulk_modal_box_classes`.
- Native field labels, required state, help text, bound values, errors, CSRF, multipart encoding, and accessible relationships.
- Crispy template-pack selection and server-addressable form fragments for native and `crispy-bootstrap5` rendering.

### Bulk, async, and inline presentation

- `bulk_fields`, `bulk_delete`, `bulk_async`, `bulk_min_async_records`, `bulk_async_notification`, `show_bulk_selection_meta`.
- `inline_edit_fields`, `inline_edit_allowed`, `inline_edit_always_visible`, `inline_edit_highlight_accent`, `inline_edit_requires_perm`, `inline_save_refresh_policy`, `inline_preserve_required_fields`.
- Inline dependency presentation from `field_queryset_dependencies`, lock/error/loading/success/conflict/progress/empty states, and related public hooks that determine visible affordances.

### Framework, pack, and downstream override contracts

- `get_framework_styles()` and the recognized style-map keys: `base`, `filter_attrs`, `actions`, `action_group_item`, `extra_default`, `list_cell_link_class`, and `modal_attrs`.
- Selected-pack declaration, namespace resolution, capabilities, adapter identity, variant identity, manual/Vite assets, and native/crispy form requirements.
- Focused component candidate resolution, named partials, semantic `data-powercrud-*` and `data-inline-*` hooks, and `pcrud_mktemplate` guidance for list, bulk, modal, and related component overrides.

## Review Method

1. Trace every inventory item from published contract or public declaration through configuration resolution, context construction, Bootstrap template/style/adapter consumption, and existing test evidence.
2. Record the exact source and test references for each result; do not infer support merely because a value is accepted by configuration validation.
3. Distinguish semantic support from raw DaisyUI/Tailwind class portability. A Bootstrap-native equivalent may be **Framework-translated** even when the original class string is not copied.
4. Recheck every **Intentionally unsupported**, **Defect**, and **Unverified** result in the primary-agent synthesis pass.
5. Run only existing focused server/browser checks that directly support matrix rows under default and Bootstrap settings where applicable. Missing sentinel-value coverage is a finding, not permission to add tests during this audit.

## Delegated Review Lanes

After the primary agent freezes this inventory, use three concurrent, read-only explorer sub-agents on the configured lesser model at medium reasoning. Each receives a non-overlapping subset of rows and returns classifications, evidence references, tests found, uncertainties, and suspected defects. Sub-agents do not edit files or make final policy decisions.

1. **List and layout:** core page/list presentation, table geometry, columns, pagination, filters, help, links, tooltips, list options, favourites, and responsive layout.
2. **Interaction surfaces:** forms, native/crispy rendering, modals, actions/buttons, selection, bulk, async, inline editing, disabled/loading/error/conflict states, and lifecycle-sensitive presentation.
3. **Extension contracts:** framework style maps, focused overrides, named fragments, pack selection, assets, template-copy tooling, and public documentation/test coverage.

If the execution environment cannot select a genuinely lesser model, stop before delegation and report that constraint rather than silently substituting an equal or stronger model.

## Findings And Acceptance

The completed audit must contain:

- A concise executive summary with classification counts.
- A complete row-oriented API matrix using the frozen inventory.
- Confirmed Bootstrap support and framework translations.
- Intentional limitations and whether the public documentation states them clearly.
- Confirmed defects with user impact and the owning component boundary.
- Unverified areas with exact proposed characterization tests.
- Follow-up recommendations separated into code, tests, and stable documentation.
- A decision register for items requiring Michael's direction.

Completion means every inventory row has evidence or an explicit **Unverified** gap; no public API point is silently omitted. No product code, test, generated asset, existing Phase 7 plan, or existing styling audit is changed by this audit.

## Review Results

The three read-only review lanes completed against the frozen inventory. The result is that Bootstrap preserves most semantic PowerCRUD behaviour, but it does not currently respond to every documented presentation control. The earlier styling audit correctly identified several intentional Bootstrap limits, while this broader product-API review also found implementation defects and documentation gaps that were outside that narrower audit.

### Core page, table, and list APIs

| API surface | Result | Evidence and qualification |
| --- | --- | --- |
| `view_title`, `view_instructions`, pagination, page-size options | Honoured / framework-translated | Bootstrap owns the corresponding list templates and preserves shared HTMX/query-state hooks. Existing Bootstrap template-pack and shared behaviour tests cover these paths. |
| `view_help` summary/details/default-open semantics | Honoured | Bootstrap renders the public help content through its native `<details>` structure. |
| `view_help_default_color`, `view_help_min_width` | Framework-translated | Bootstrap consumes the resolved semantic/hex colour through Bootstrap CSS variables and applies the validated minimum width with a container-safe clamp. These settings are portable rather than Bootstrap exclusions. |
| `table_max_height`, `table_pixel_height_other_page_elements` | Honoured / framework-translated | Bootstrap's list partial applies the same viewport calculation through Bootstrap-owned wrapper CSS. A dedicated Bootstrap sentinel test is absent. |
| `table_classes` | Honoured as raw passthrough | Extra classes reach the table. DaisyUI/Tailwind class strings are not translated, which is a portability caveat rather than a semantic failure. |
| `table_max_col_width` | Honoured / framework-translated | The resolved CSS custom property is consumed by Bootstrap table CSS for bounded width and ellipsis. Bootstrap-specific sentinel coverage is absent. |
| `table_header_min_wrap_width` | Honoured / framework-translated | 7.10 passes the resolved width into both pack templates. Bootstrap consumes it through `--pc-table-header-min-wrap-width` and permits ordinary headers to wrap; the shared browser matrix now checks computed geometry. |
| `column_alignments` | Honoured / framework-translated | 7.10 maps the semantic `left`/`center`/`right` values to Bootstrap `text-start`/`text-center`/`text-end`, including inline controls and links. |
| `column_help_text` | Framework-translated with presentation caveat | Text is preserved through a native `title` on the header control rather than the DaisyUI adjacent help trigger. Semantic help remains available, but markup-level parity is different. |
| sort overrides, value formats, datetime defaults, field labels | Honoured | Core resolves values and metadata; Bootstrap renders those resolved values. Existing core and shared matrix tests cover the behavior, with limited Bootstrap-specific sentinel rendering. |
| list-cell links and `get_list_cell_link()` | Honoured / framework-translated | Bootstrap preserves URL, target, relation, modal metadata, and inline-link precedence through Bootstrap-native templates and modal triggers. |
| list-cell semantic/lazy/overflow tooltips | Honoured / framework-translated | Bootstrap maps the shared tooltip contract to `data-bs-title` and Bootstrap Tooltip, including compatibility with legacy tooltip attributes. |
| list options and column chooser | Honoured / framework-translated | Shared persistence, endpoints, visible-column state, and semantic hooks are retained by the Bootstrap chooser. |
| filters and saved favourites | Honoured / framework-translated | Bootstrap templates and adapters preserve filter state, optional filter controls, Tom Select, favourites endpoints, and saved-state behavior. |
| responsive list layout | Framework-translated; verification gap | Bootstrap owns responsive overflow and wrapping, and existing browser checks exercise interactions, but there is no dedicated Bootstrap narrow-viewport geometry assertion for the full public layout contract. |

### Forms, modals, actions, bulk, and inline APIs

| API surface | Result | Evidence and qualification |
| --- | --- | --- |
| `form_class`, `form_fields`, exclusions, display fields, disabled fields | Honoured | Bootstrap consumes the resolved bound form and display context without field-name assumptions. Existing form-mixin and Bootstrap native/crispy tests cover these paths. |
| `field_queryset_dependencies` and inline dependency metadata | Honoured / framework-translated | Core owns queryset semantics; Bootstrap retains `data-inline-*` metadata and Bootstrap-compatible controls. Existing server and browser dependency tests cover this. |
| native forms and `use_crispy` / `crispy-bootstrap5` | Honoured | Bootstrap has native and crispy field paths, required fragments, and settings/dependency evidence. |
| `modal_presentation`, `bulk_modal_presentation` | Framework-translated | Bootstrap maps portable size presets to native dialog sizes, exact safe widths to `--bs-modal-width`, and maps scrolling, height, fullscreen, and alignment through the Bootstrap dialog adapter and CSS. |
| legacy `modal_classes`, `modal_box_classes`, `modal_body_classes`, `bulk_modal_box_classes` | Honoured as deprecated framework-specific passthrough | Bootstrap renders the corresponding raw shell, dialog, and body classes without claiming cross-framework semantics. Explicit use emits `FutureWarning`; the settings are targeted for removal in v1.0 and cannot be mixed with the portable API. |
| `extra_buttons` and selection-aware behavior | Honoured / framework-translated | Core selection, permission, HTMX, modal, clear-selection, and disabled-state semantics are preserved by the Bootstrap partial. Raw consumer class strings remain passthrough values. |
| `extra_button_classes` in buttons mode | Honoured | The configured classes reach individual Bootstrap buttons. |
| `extra_button_classes` in dropdown mode | Honoured | 7.10 applies the configured classes to each generated Bootstrap dropdown action as well as to the `More` summary. |
| `extra_buttons_mode` | Framework-translated | Bootstrap supplies native `details`/menu presentation and shared close-after-selection behavior. 7.10 scopes Bootstrap menu visibility to the native open state, so the menu is not exposed while its `details` control is closed. |
| `extra_actions`, mode, visibility, permission, disabled, modal, lazy-state, and refresh metadata | Honoured / framework-translated | Bootstrap row-action templates preserve action semantics and use Bootstrap-native menu/tooltip/modal attributes. Raw custom classes are not automatically converted from DaisyUI values. |
| selection and bulk controls, async outcomes | Honoured / framework-translated | Shared state, endpoints, progress, success, warning, error, conflict, and dismissal semantics are retained through Bootstrap templates and the shared runtime. |
| inline editing policy, permissions, locks, dependencies, save/refresh policy | Honoured / framework-translated | Core retains policy and request semantics; Bootstrap owns controls, active/error rows, spinners, and error presentation. Existing inline server/browser evidence covers the lifecycle. |
| inline highlight accent | Honoured / framework-translated | Bootstrap's list partial already exposes the resolved highlight palette as Bootstrap-owned CSS variables. The original audit classification was corrected during the 7.10 implementation review. |

### Extension, pack, and downstream override APIs

| API surface | Result | Evidence and qualification |
| --- | --- | --- |
| `get_framework_styles()` and all seven recognized keys | Honoured / framework-translated | Bootstrap supplies a native `bootstrap5` style map for `base`, `filter_attrs`, `actions`, `action_group_item`, `extra_default`, `list_cell_link_class`, and `modal_attrs`, while the public override seam remains. Direct Bootstrap override and per-key sentinel coverage are unverified. |
| Bootstrap declaration, namespace, capabilities, adapter identity, assets, native/crispy requirements | Honoured | Declaration/resource tests and Phase 7.9 installed-artifact evidence cover the selectable pack and its co-distributed resources. |
| focused component candidate precedence | Honoured at resolver level; Bootstrap-specific verification gap | Generic resolver tests cover precedence, but no focused Bootstrap test proves a downstream model override wins for every Bootstrap component. |
| named partials and semantic `data-powercrud-*`/`data-inline-*` hooks | Honoured for shipped Bootstrap resources | Bootstrap templates preserve the runtime hooks and direct fragments exercised by existing tests. A complete optional-partial render matrix is absent. |
| reusable validator coverage for the complete focused-partial contract | Honoured | 7.10 expands the capability matrix to compile the focused list, form, detail, delete, filter, modal, bulk, inline, and favourites components, with a negative missing-focused-component test. |
| `pcrud_mktemplate` focused component copying | Honoured for focused components | Selected-pack source resolution and script-free component copying remain available. |
| `pcrud_mktemplate` whole-tree copying for Bootstrap | Intentionally unsupported; documentation gap | Bootstrap declares no legacy whole-tree copy destination. The public guidance does not clearly explain this Bootstrap limit. |
| `pcrud_mktemplate` Bootstrap form-field guidance | Honoured | 7.10 uses pack-neutral wording for the selected pack's crispy renderer. |
| public Bootstrap pack and crispy/asset documentation | Documentation gap | The sample launch guidance exists, but public docs do not explain the Bootstrap selector, namespace, assets, `crispy-bootstrap5`, style-map key, or focused-override boundaries. |
| variant adapter, public browser registry, runtime pack switcher, CSS-framework-only Bootstrap selection | Not applicable / intentionally unsupported | Phase 7 deliberately keeps variant JavaScript, browser registries, runtime switching, and `POWERCRUD_CSS_FRAMEWORK="bootstrap5"` alone outside the contract. |

## Verification Status

The review used the existing Phase 7 evidence and focused test references reported by the three explorers. The 7.10 implementation then added focused server/browser characterization and passed these fresh checks:

```text
./runproj exec "./runtests --pytest src/tests/test_conf_logging_validators.py src/tests/test_poweractions.py src/tests/test_form_filter_template_mixins.py src/tests/test_templatetags_powercrud.py src/tests/test_core_phase1.py src/tests/test_template_packs.py src/tests/test_bootstrap_template_pack.py"
./runproj exec "DJANGO_SETTINGS_MODULE=tests.settings_bootstrap ./runtests --pytest src/tests/test_bootstrap_template_pack.py"
./runproj exec "./runtests --playwright src/tests/playwright/test_modal_crud.py::test_portable_per_trigger_modal_presentation_is_applied_and_reset"
./runproj exec "DJANGO_SETTINGS_MODULE=tests.settings_bootstrap ./runtests --playwright src/tests/playwright/test_modal_crud.py::test_portable_per_trigger_modal_presentation_is_applied_and_reset"
```

The default focused server matrix passed 455 tests (11 Bootstrap-only skips); the selected Bootstrap matrix passed 12 tests. The portable modal browser scenario passed under both default and selected Bootstrap settings after each run rebuilt the package assets. The final canonical default server phase passed 1,018 tests (13 skips; 91 browser tests deselected), followed by an isolated default Playwright gate of 91 tests with zero failures (7 intentional skips). These are separate successful full gates, not one uninterrupted combined output. Existing documented Phase 7 server/browser/distribution results remain supporting evidence; rows still marked verification gaps need their named characterization coverage in a later approved slice.

## Recommended Follow-Up

### Code

- Consider removing the DaisyUI fallback for a missing selected-pack partial after the Phase 8 disposal work is complete.

### Tests

- Keep the new server matrix for portable modal/view-help contracts, legacy deprecation warnings, table geometry, semantic alignment, dropdown classes, and focused-partial validation in the normal pack acceptance gate.
- Add direct Bootstrap tests for canonical `bootstrap5` style-map override keys and all seven key values.
- Add Bootstrap-focused candidate-precedence tests and focused command tests for explicit whole-tree rejection.

### Stable documentation

- Document Bootstrap pack selection, namespace, assets, native/crispy requirements, style-map expectations, and process-startup-only selection.
- Document focused overrides as the supported Bootstrap customization path and state that whole-tree copy is unavailable for the Bootstrap pack.
- Publish an explicit support table for portable APIs, framework-translated APIs, framework-specific raw class settings, and any genuinely unsupported pack settings.

## Current Conclusion

Bootstrap is a serious, broadly compatible pack with explicit boundaries. The 7.10 follow-up fixed `table_header_min_wrap_width`, semantic left/right alignment, and dropdown-mode `extra_button_classes`; it also added portable modal presentation, completed portable view-help colour/width handling, and deprecated raw modal classes without silently ignoring them. Stable API documentation ships with this follow-up. Phase 9 may broaden the template-pack authoring narrative and support-table presentation, but does not defer this contract.
