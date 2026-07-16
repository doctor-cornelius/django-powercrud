# Management Commands

powercrud provides several management commands to help with setup, template customization, and Tailwind CSS integration.

## `pcrud_mktemplate` - Copy CRUD Templates And Assets

Copy PowerCRUD templates and, when explicitly requested, pack assets to your project for customisation. For pack selection and customisation boundaries, see [Template Packs](../template_packs/index.md). To choose a focused `--component` value, use the [focused component table](../template_packs/customising.md#focused-component-overrides).

### Copy a template pack for your project

Use a plain app target to create a project-level override root. This is useful when several models need the same presentation change, or when your project needs to own a complete pack.

```bash
# Copy the four main DaisyUI templates. This is the default scope.
python manage.py pcrud_mktemplate myapp

# The same command, with the scope stated explicitly.
python manage.py pcrud_mktemplate myapp --core

# Copy only the list root; all other roots and components fall back to DaisyUI.
python manage.py pcrud_mktemplate myapp --list

# Copy every DaisyUI template, including components.
python manage.py pcrud_mktemplate myapp --all

# Copy every Bootstrap 5 template, including components.
python manage.py pcrud_mktemplate myapp --source-template-pack bootstrap5 --all

# Copy the four main DaisyUI templates and an app-owned manual-static asset snapshot.
python manage.py pcrud_mktemplate myapp --assets

# Copy all Bootstrap 5 templates and its app-owned manual-static asset snapshot.
python manage.py pcrud_mktemplate myapp --source-template-pack bootstrap5 --all --assets
```

`--source-template-pack` accepts `daisyui`, `bootstrap5`, or an installed pack's `module.path:attribute` selector. If it is omitted, the command copies DaisyUI. It does not choose your runtime pack, install a framework, configure Crispy Forms, or load vendor assets. Configure those separately, and select the same pack that you copied with `POWERCRUD_TEMPLATE_PACK` in `POWERCRUD_SETTINGS`.

For example, a complete Bootstrap copy needs a Bootstrap runtime selection:

```python
POWERCRUD_SETTINGS = {
    "POWERCRUD_TEMPLATE_PACK": "powercrud.contrib.bootstrap5:template_pack",
}
```

The command writes to a pack-identified directory beneath the app's normal template directory. For `myapp` and DaisyUI, every app-level scope uses this root:

```text
myapp/
    templates/
        myapp/
            powercrud/
                daisyui/
                    object_list.html             # default/--core/--all, or --list
                    object_detail.html           # default/--core/--all, or --detail
                    object_form.html             # default/--core/--all, or --form
                    object_confirm_delete.html   # default/--core/--all, or --delete
                    partial/                 # present with --all
                    ...                      # other pack files with --all
```

It overwrites matching copied files but leaves files that exist only in the destination. Add the printed setting to every PowerCRUD view that should use the copy:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    model = Project
    template_override_path = "myapp/powercrud/daisyui"
```

PowerCRUD tries templates in this order: a model-specific override, the project-level `template_override_path`, then the selected pack. Therefore `--core` is safe: the four copied root templates are used, while any component or nested template that you did not copy comes from the selected runtime pack.

### Copy one root template for a project

Use a plain app target plus one root selector when all views configured with the same project root need one shared screen change:

```bash
python manage.py pcrud_mktemplate myapp --list
python manage.py pcrud_mktemplate myapp --detail
python manage.py pcrud_mktemplate myapp --form
python manage.py pcrud_mktemplate myapp --delete
```

`--create` and `--update` are aliases for `--form`. Each command copies one `object_*.html` file to `myapp/templates/myapp/powercrud/daisyui/`. Use `--source-template-pack bootstrap5` to take that one root from Bootstrap instead. Missing roots, components, and nested templates continue to fall back to the selected runtime pack, so do not set `template_override_complete = True` for this scope.

For a complete copy, add the second setting printed by the command:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    model = Project
    template_override_path = "myapp/powercrud/daisyui"
    template_override_complete = True
```

This makes direct nested includes use the copied root as well. `--all` then gives the project an editable copy of every current template, but it also means the project must decide when to take future package template changes. Keep all files needed by the copied templates; `template_override_complete` is an explicit complete-ownership choice.

Use a project-level override root for all views where you set `template_override_path`; it is not tied to one model. A model-specific copied template still takes precedence for every view using that model. For a one-view-only variation, use an explicit `get_template_names()` override as described in [Customising a template pack](../template_packs/customising.md#override-all-main-templates-for-one-model).

### Copy a pack's manual-static assets

Add `--assets` to a plain app command when the project needs to own the selected pack's PowerCRUD CSS and JavaScript. It can be combined with a one-root, default four-root, or `--all` template scope; it does not change template lookup. The command copies package-owned assets under the app's static namespace:

```text
myapp/
    static/
        myapp/
            powercrud/
                css/
                js/
                    runtime/
                contrib/bootstrap5/     # Bootstrap only
                    css/
                    js/
```

For DaisyUI, this is the shared PowerCRUD runtime and its adapter. For Bootstrap, it also includes the Bootstrap PowerCRUD stylesheet and adapter modules. An independently published pack contributes the paths declared by that pack. The command deliberately does not copy vendor dependencies such as DaisyUI, Bootstrap, HTMX, Tom Select, or Tippy.

The command prints the exact `{% static %}` stylesheet and module-script tags for the selected pack. Replace the package-owned PowerCRUD tags in the base template with those application-owned tags; do not load both. The runtime uses a duplicate-load guard, so the first entry loaded determines the active presentation.

An asset snapshot is complete ownership with no file-by-file package fallback. If a copied CSS or JavaScript file is removed, restore it or deliberately change the base-template entry. Keep `POWERCRUD_TEMPLATE_PACK` aligned with the copied source pack.

`--assets` supports manual-static loading only. It does not generate or modify a Vite entry or manifest. A project using PowerCRUD's packaged Vite entry must maintain its own custom frontend entry before it can own pack runtime assets; do not load the generated manual-static snapshot alongside the packaged Vite entry.

Assets are application and pack scoped because the base template loads them. `app.Model` targets and `--component` cannot use `--assets`; app-level root selectors such as `myapp --list --assets` can. Model-specific template overrides continue to work with either the package-owned or app-owned runtime.

## `pcrud_starttemplatepack` - Start an independent package

Create a normal Python/Django package for a new CSS framework or presentation system. The command copies the full template tree from a maintained source and creates a declaration, neutral adapters, package-data configuration, and a small CSS/JavaScript entry point:

```bash
# Start from the default DaisyUI template tree.
python manage.py pcrud_starttemplatepack my_powercrud_pack ../my-powercrud-pack

# Start from the Bootstrap 5 template tree instead.
python manage.py pcrud_starttemplatepack my_powercrud_pack ../my-powercrud-pack \
  --source-template-pack bootstrap5
```

The first argument is the Python package name. The second is a new or empty destination directory; the command refuses to overwrite a populated directory. Use `--identity` only when the public pack identity should differ from the package name.

The starter has no framework-name registration. Edit the copied templates and the optional adapter hooks, then test and publish it as a normal Python distribution. See [Authoring and publishing a template pack](../template_packs/authoring-and-publishing.md) for the complete workflow.

### Copy templates for one model

Use the dotted `app.Model` target when only one model needs an override:

```bash
# Copy all four main CRUD templates for Project.
python manage.py pcrud_mktemplate myapp.Project --all

# Copy one main template for Project.
python manage.py pcrud_mktemplate myapp.Project --list
python manage.py pcrud_mktemplate myapp.Project --detail
python manage.py pcrud_mktemplate myapp.Project --form
python manage.py pcrud_mktemplate myapp.Project --delete

# Copy one focused component for Project.
python manage.py pcrud_mktemplate myapp.Project --component pagination
```

These files are written directly to `{app}/templates/{app}/`. Model `--all` creates `{model}_list.html`, `{model}_detail.html`, `{model}_form.html`, and `{model}_confirm_delete.html`; a focused component creates `{model}_{component}.html`. They apply to every PowerCRUD view whose `model` is that model, not merely to a class with a matching name.

Choose the component name from the [focused component table](../template_packs/customising.md#focused-component-overrides). The detailed sections below explain each generated template's context and preservation rules.

### Arguments and options

- `target` - An app name (for example, `myapp`) or `app.Model` (for example, `myapp.Project`).
- `--core` - With an app name, copy the four main CRUD templates. This is the default when no scope is supplied.
- `--all` - With an app name, copy the complete source pack. With `app.Model`, copy the four main templates for that model.
- `--source-template-pack SELECTOR` - Choose the source for an app-level copy. `SELECTOR` may be `daisyui`, `bootstrap5`, or an installed pack's `module.path:attribute` declaration selector. The default is `daisyui`; this option is not used with `app.Model`.
- `--assets` - With an app name, copy the selected pack's PowerCRUD-owned manual-static CSS and JavaScript snapshot. It may be combined with any app-level template scope. This option is not available for `app.Model` or focused components.
- `template_override_complete = True` - View setting used with an app-level `--all` copy. It makes direct nested includes use the copied complete root. Do not set it for a `--core` copy.
- `--list` (`-l`) - With an app name, copy the selected pack's list root. With `app.Model`, copy that model's list template only.
- `--detail` (`-d`) - With an app name, copy the selected pack's detail root. With `app.Model`, copy that model's detail template only.
- `--create` (`-c`), `--update` (`-u`), `--form` (`-f`) - With an app name, copy the selected pack's form root. With `app.Model`, copy that model's create/update form template.
- `--delete` - With an app name, copy the selected pack's delete root. With `app.Model`, copy that model's delete template only.
- `--component NAME` - Copy one focused component for a model. Choose `NAME` from the [focused component table](../template_packs/customising.md#focused-component-overrides).

`POWERCRUD_CSS_FRAMEWORK` remains a legacy compatibility setting; it does not select the optional Bootstrap pack.

### Focused Pagination Override

`--component pagination` copies the pagination navigation to:

```text
{app}/templates/{app}/{model}_pagination.html
```

For example, `library.Book` produces `library/templates/library/book_pagination.html`. PowerCRUD selects this file for that model before its built-in pagination component.

You can change the navigation's markup, classes, labels, and icons without copying PowerCRUD JavaScript or the whole list template. Keep the pagination context (`paginator`, `page_obj`, `request`, `use_htmx`, and `original_target`), the `data-powercrud-pagination` attribute, and the existing page-link behaviour. The page-size selector remains part of the list toolbar; it is not copied by this command.

The legacy `object_list.html#pagination` fragment remains available during the 0.x compatibility period.

### Focused Page-size Selector Override

`--component page-size` copies the selector to:

```text
{app}/templates/{app}/{model}_page_size_selector.html
```

For example, `library.Book` produces `library/templates/library/book_page_size_selector.html`. PowerCRUD selects this file for that model before its built-in selector component.

You can change the selector markup, classes, labels, and surrounding text without copying PowerCRUD JavaScript or the list template. Keep `page_size_options`, `default_page_size`, `page_size_all_enabled`, and `request` in use; preserve `#page-size-form`, `#page-size-select`, `name="page_size"`, `data-powercrud-page-size-select`, and the Rows-per-page tooltip.

### Focused List Actions Override

`--component list-actions` copies the Create and extra-action controls to:

```text
{app}/templates/{app}/{model}_list_actions.html
```

For example, `library.Book` produces `library/templates/library/book_list_actions.html`. PowerCRUD selects this file for that model before its built-in list-actions component.

You can change the Create and extra-action markup without copying PowerCRUD JavaScript or the list template. Keep `create_view_url`, `use_htmx`, `htmx_target`, `modal_id`, `object_verbose_name`, and `view` available; preserve the Create link's normal and HTMX/modal behaviour and `{% extra_buttons view %}`. The surrounding `data-powercrud-action-controls` wrapper and bulk-selection bridge remain owned by the list template.

### Focused Filter Trigger Override

`--component filter-toggle` copies the filter trigger to:

```text
{app}/templates/{app}/{model}_filter_trigger.html
```

For example, `library.Book` produces `library/templates/library/book_filter_trigger.html`. PowerCRUD selects this file for that model before its built-in filter trigger.

You can change the trigger markup, classes, and icons without copying PowerCRUD JavaScript or the list template. Keep the trigger inside the list toolbar and preserve `#filterToggleBtn`, `aria-controls="filterCollapse"`, `data-powercrud-filter-toggle`, semantic tooltip metadata, and both `data-powercrud-filter-toggle-icon-*` hooks. The filter panel remains owned by the list template.

### Focused Filter-panel Actions Override

`--component filter-panel-actions` copies the add-filter and reset controls to:

```text
{app}/templates/{app}/{model}_filter_panel_actions.html
```

For example, `library.Book` produces `library/templates/library/book_filter_panel_actions.html`. PowerCRUD selects this file for that model before its built-in filter-panel actions.

You can change the add-filter and reset markup without copying PowerCRUD JavaScript or the list template. Keep `addable_filter_choices`, `use_htmx`, `view`, and `original_target` available; preserve the add-filter container and select hooks, the reset link, and the non-HTMX `form="filter-form"` relationship. The filter form and its fields remain owned by the list template.

### Focused Filter Form Override

`--component filter-form` copies the filter form to:

```text
{app}/templates/{app}/{model}_filter_form.html
```

For example, `library.Book` produces `library/templates/library/book_filter_form.html`. PowerCRUD selects this file for that model before its built-in filter form.

You can change filter fields, layout, labels, and remove controls without copying PowerCRUD JavaScript or the list template. Keep `request`, `visible_filter_fields`, `persisted_optional_filter_names`, and `visible_filter_param_name` available; preserve `#filter-form`, its HTMX attributes, `data-powercrud-visible-filters-state`, and optional-filter remove hooks. Filter-panel actions and the surrounding filter shell remain owned by the list template.

### Focused List-column Chooser Override

`--component list-columns` copies the list-column chooser to:

```text
{app}/templates/{app}/{model}_list_columns.html
```

For example, `library.Book` produces `library/templates/library/book_list_columns.html`. PowerCRUD selects this file for that model before its built-in list-column component.

You can change the chooser's markup, classes, labels, and icons without copying PowerCRUD JavaScript or the whole list template. Keep `view`, `list_column_state`, `list_options_url`, `list_view_url`, `use_htmx`, `original_target`, and the request-aware context available. Preserve the list-column trigger, hidden template, panel, checkbox, query-state, Save, and Reset hooks so the detached panel, last-column guard, favourites integration, and normal or HTMX submissions continue working. The feature guard and surrounding toolbar remain owned by the list template.

### Focused Row Actions Override

`--component row-actions` copies the resolved row-action presentation to:

```text
{app}/templates/{app}/{model}_row_actions.html
```

For example, `library.Book` produces `library/templates/library/book_row_actions.html`. PowerCRUD selects this file for that model before its built-in row-actions component.

The component receives `object` and `row_actions`. PowerCRUD has already resolved URLs, permissions, visibility, disabled and lock state, HTMX behavior, modal behavior, lazy-state indices, and framework classes. The override should render only that supplied presentation data; do not repeat authorization, state-hook, or URL decisions in the template.

You can change the arrangement, classes, labels, and icons without copying PowerCRUD JavaScript or the list template. Preserve `data-inline-action` plus the dropdown, lazy-state, disabled-tooltip, HTMX, modal, and modal-close-refresh attributes used by the behavior you retain. The legacy `action_links()` function and `row.actions`/`row.has_actions` list-template values remain available during the 0.x compatibility period.

### Focused Table Header Override

`--component table-header` copies the table header to:

```text
{app}/templates/{app}/{model}_table_header.html
```

For example, `library.Book` produces `library/templates/library/book_table_header.html`. PowerCRUD selects this file for that model before its built-in table-header component.

You can change header layout, classes, labels, sort icons, and help icons without copying PowerCRUD JavaScript or the whole list template. Keep `headers`, `current_sort`, `filter_params`, `use_htmx`, `request`, `has_row_actions`, `enable_selection_controls`, and the existing selection-state context available. Preserve the sorting URL and HTMX attributes, semantic help trigger, conditional Actions heading, and select-all hooks for the behavior you retain. The table shell and rows remain separately overridable, while the select-all column delegates to the focused bulk-selection controls component.

### Focused Table Row Override

`--component table-row` copies the normal display row to:

```text
{app}/templates/{app}/{model}_table_row.html
```

For example, `library.Book` produces `library/templates/library/book_table_row.html`. PowerCRUD selects this file for that model before its built-in normal-row component.

You can change row and cell arrangement, classes, and presentation without copying PowerCRUD JavaScript or the whole list template. Keep `row`, `inline_edit`, `enable_selection_controls`, `selected_ids`, `list_view_url`, and `has_row_actions` available. Preserve the row, selection, inline-display, dependency, cell-link, tooltip, and row-action hooks used by the behavior you retain. The selection cell delegates to focused bulk-selection controls. The built-in row and direct `partial/list.html#inline_row_display` fragment are compatibility façades over the focused inline display row, while `#inline_row_form` remains the direct edit-row façade through 0.x.

### Focused Table Shell Override

`--component table-shell` copies the responsive table wrapper and table structure to:

```text
{app}/templates/{app}/{model}_table_shell.html
```

For example, `library.Book` produces `library/templates/library/book_table_shell.html`. PowerCRUD selects this file for that model before its built-in table-shell component.

You can change the responsive wrapper, table classes, header/row arrangement, and normal-row loop without copying PowerCRUD JavaScript or the whole legacy list template. Keep `inline_edit`, `table_classes`, `enable_selection_controls`, `keyBase`, `selection_key_suffix`, `table_header_template_paths`, `table_row_template_paths`, and `object_list` available. Preserve the wrapper/table geometry plus selection-key and inline-enabled attributes used by the behavior you retain, and continue delegating to the focused header and row candidates if those model overrides should remain active.

The legacy `partial/list.html` remains the 0.x inclusion-tag façade and still owns all table/inline styles plus the direct inline display and form fragments.

### Focused Bulk-selection Status Override

`--component bulk-selection-status` copies the selected-count and bulk-action controls to:

```text
{app}/templates/{app}/{model}_bulk_selection_status.html
```

For example, `library.Book` produces `library/templates/library/book_bulk_selection_status.html`. PowerCRUD selects this file for that model before its built-in bulk-selection-status component, including after direct selection-status HTMX swaps.

You can change the arrangement, classes, labels, and icons without copying PowerCRUD JavaScript or the whole list template. Keep `selected_count`, `enable_bulk_edit`, `list_view_url`, `view`, `modal_target`, `modal_id`, `bulk_modal_presentation_attrs`, `modal_uses_legacy_classes`, and the legacy `bulk_modal_box_classes` available. Preserve `#bulk-actions-container`, `#selected-items-counter`, `data-powercrud-bulk-actions`, `data-powercrud-clear-selection`, the existing HTMX outer-swap endpoints, and modal trigger metadata for the behavior you retain.

The toolbar feature guard and matching-record selection prompt remain owned by `object_list.html`. Its legacy `#bulk_selection_status` fragment remains available during the 0.x compatibility period.

### Focused Bulk-selection Controls Override

`--component bulk-selection-controls` copies the three selection-control presentations to:

```text
{app}/templates/{app}/{model}_bulk_selection_controls.html
```

For example, `library.Book` produces `library/templates/library/book_bulk_selection_controls.html`. PowerCRUD selects this same model override for all three `selection_control` modes: `matching` in filtered-results metadata, `select_all` in the table header, and `row` in each normal table row.

Keep all three modes. Matching mode receives the matching-selection flags, label or limit message, `request`, and `list_view_url`. Select-all mode receives `all_selected` and `some_selected`. Row mode receives `row`, `selected_ids`, and `list_view_url`. Preserve the select-all, row-selection, initial-state, matching-action, status-target, and outer-swap hooks used by the behavior you retain.

The surrounding results metadata, table header, table row, and table shell remain separate focused or legacy surfaces. Selection persistence remains server-session owned, and repeated initialization and range-selection behavior remain in PowerCRUD JavaScript.

### Focused Bulk Form And Fields Overrides

`--component bulk-form` creates `{app}/templates/{app}/{model}_bulk_form.html`; `--component bulk-fields` creates `{app}/templates/{app}/{model}_bulk_fields.html`.

The bulk form receives `request`, `selected_ids`, `selected_count`, `model_name_plural`, `enable_bulk_update`, `enable_bulk_delete`, `modal_target`, `field_info`, and `bulk_fields_template_paths`. Preserve `#bulk-edit-form`, CSRF, `bulk_submit`, `selected_ids[]`, `data-powercrud-form="bulk"`, `data-form-save`, and the existing delete-confirmation and HTMX metadata. Continue delegating to `bulk_fields_template_paths` if model-specific field controls should remain active.

The bulk-fields component receives `field_info`. Preserve `fields_to_update`, exact model field names, `field-input-container`, choice and relationship values, searchable-select metadata, and `<field>_action` names for many-to-many operations.

The legacy `bulk_edit_form.html#full_form` fragment remains server-addressable and retains the package-owned field-toggle and delete-confirmation behavior. Focused copies contain no functional PowerCRUD JavaScript.

### Focused Bulk Outcomes Override

`--component bulk-outcomes` creates `{app}/templates/{app}/{model}_bulk_outcomes.html`. It renders four `bulk_outcome` modes: `operation_errors`, `error`, `conflict`, and `queued`. Keep all four modes and the applicable `errors`, `error`, conflict context, or queued task/progress/modal context. Preserve outcome, polling, progress, and modal hooks.

The existing operation-error surface, `bulk_edit_errors.html#bulk_edit_error`, `#bulk_edit_conflict`, and `bulk_edit_form.html#async_queue_success` remain server-addressable façades. They retain the package-owned progress behavior; the focused copy contains no functional PowerCRUD JavaScript.

### Focused Modal Shell Override

`--component modal-shell` creates `{app}/templates/{app}/{model}_modal_shell.html`. It receives `modal_id`, `modal_target`, the legacy class values, `modal_presentation_attrs`, `bulk_modal_presentation_attrs`, and `modal_uses_legacy_classes`.

Preserve the configured dialog and content-target IDs, `data-powercrud-modal`, `data-powercrud-modal-box`, `data-powercrud-default-modal-box-classes`, native `method="dialog"` close controls, backdrop, and any viewport/scroll classes needed by your presentation. Modal triggers and the form, detail, delete, or bulk content loaded into the target remain separately owned.

The direct `partial/modal.html` template remains the 0.x compatibility façade. Modal sizing, duplicate cleanup, closing, tooltip lifecycle, refresh-on-close, and repeated initialization remain in PowerCRUD JavaScript.

### Focused Modal Content Override

`--component modal-content` creates `{app}/templates/{app}/{model}_modal_content.html`. It receives `modal_target`, `modal_body_classes`, `modal_presentation_attrs`, and `modal_uses_legacy_classes` and remains the empty host for HTMX inner-content replacement. Preserve the configured target ID, semantic attributes, and applicable body classes.

The dialog, box, close/backdrop controls, triggers, returned CRUD/bulk markup, tooltip lifecycle, and refresh-on-close remain separate. A custom `modal-shell` override must continue delegating through `modal_content_template_paths` if the nested model override should remain active. The direct `partial/modal.html` compatibility façade remains available through 0.x.

### Focused Form Shell Override

`--component form-shell` creates `{app}/templates/{app}/{model}_form_shell.html`. It receives the bound `form`, optional `object`, `object_verbose_name`, contextual `form_display_items`, create/update URLs, request query state, HTMX/modal settings, and nested field/action candidate paths.

Preserve the create/update heading and context display, POST action, multipart encoding, CSRF token, retained `_powercrud_filter_*` inputs, `data-powercrud-form="object"`, and normal/modal HTMX attributes. Continue delegating through `form_fields_template_paths` and `form_actions_template_paths` when those nested overrides should remain active.

The legacy `object_form.html#normal_content` and `#pcrud_content` fragments remain server-addressable through 0.x. Form lifecycle behavior remains package-owned; the focused copy contains no PowerCRUD JavaScript.

### Focused Form Fields Override

`--component form-fields` creates `{app}/templates/{app}/{model}_form_fields.html`. It receives `form`, `use_crispy`, and `framework_template_path` and renders either the native Django form or the Crispy fragment for the selected pack.

Preserve both rendering branches and do not add an outer form or CSRF token: those belong to the form shell. `crispy_partials.html#load_tags` and `#crispy_form` remain legacy compatibility fragments through 0.x. The focused copy contains no PowerCRUD JavaScript.

### Focused Form Actions Override

`--component form-actions` creates `{app}/templates/{app}/{model}_form_actions.html`. The built-in component requires no template context and supplies the Save submit control inside the form shell.

Keep an accessible submit control and preserve `data-form-save` when package-owned spinner behavior is required. Action URLs, CSRF, multipart, HTMX, and modal behavior remain owned by the form shell; the focused copy contains no PowerCRUD JavaScript.

### Focused Form Conflict Override

`--component form-conflict` creates `{app}/templates/{app}/{model}_form_conflict.html`. It receives the conflict message and object plus modal/HTMX mode, list URL, request/query state, and the original target.

Preserve modal return-control suppression, the normal list link, and the HTMX return target, history, and current query construction for any behavior you retain. `object_form.html#conflict_detected` and `#pcrud_content` remain server-addressable legacy façades; non-HTMX POST conflicts remain plain 409 responses. The focused copy contains no PowerCRUD JavaScript.

### Focused Detail Shell And Content Overrides

`--component detail-shell` creates `{app}/templates/{app}/{model}_detail_shell.html`. It receives `object` and `view` and owns the card, object heading, and `{% object_detail object view %}` composition call. Keep that call when the separately focused content override should remain active.

`--component detail-content` creates `{app}/templates/{app}/{model}_detail_content.html`. It receives the inclusion tag's formatted `object` iterable of `(label, value)` pairs and owns only table/row/cell presentation. Field order and formatting remain tag-owned.

`object_detail.html#pcrud_content` remains the whole-page, HTMX, and modal response façade, while direct `partial/detail.html` remains the inclusion-tag façade. Detail permissions, transport, and modal lifecycle remain separately owned; neither focused copy contains PowerCRUD JavaScript.

### Focused Delete Shell And Content Overrides

`--component delete-shell` creates `{app}/templates/{app}/{model}_delete_shell.html`. It receives `delete_content_template_paths`, owns the normal outer card, and should keep nested content delegation when that separate override remains active.

`--component delete-content` creates `{app}/templates/{app}/{model}_delete_content.html`. It receives request/object/error/form/transport context plus `delete_actions_template_paths`. Preserve confirmation and validation errors, the POST action, CSRF, repeated `_powercrud_filter_*` inputs, normal/modal HTMX attributes, form rendering, and nested action delegation for behavior you retain.

`object_confirm_delete.html#pcrud_content` remains the normal/conflict router and `#normal_content` remains directly addressable and body-only. Permissions, guards, deletion, redirects, error normalization, and modal retargeting remain Python-owned; neither focused copy contains PowerCRUD JavaScript.

### Focused Delete Actions And Conflict Overrides

`--component delete-actions` creates `{app}/templates/{app}/{model}_delete_actions.html`. The built-in leaf requires no context and supplies the destructive Delete submit control inside delete content. Keep an accessible submit control; form transport remains content-owned.

`--component delete-conflict` creates `{app}/templates/{app}/{model}_delete_conflict.html`. Full GET context includes message/object/modal/HTMX/list/page-size/target values. Preserve modal return suppression, the normal list link, and HTMX page-size, target, and history hooks for behavior you retain. Direct HTMX POST conflicts intentionally retain their historically minimal context.

`object_confirm_delete.html#conflict_detected` remains directly addressable and body-only; `#pcrud_content` remains its outer-card router. Deletion, permission, conflict checks, and modal lifecycle remain Python-owned; neither focused copy contains PowerCRUD JavaScript.

### Focused Inline Display Row Override

`--component inline-row-display` creates `{app}/templates/{app}/{model}_inline_row_display.html`. It receives resolved `row`, `inline_edit`, selection/list/action context, and focused bulk-selection candidates. Preserve row identity/status/URL, field and dependency metadata, editable and blocked affordances, links, tooltips, selection delegation, and aligned actions for behavior you retain.

The built-in `table-row` and direct `partial/list.html#inline_row_display` are compatibility façades over this canonical component. Existing custom table-row and full-list overrides remain supported. Inline lifecycle, focus/width handling, HTMX events, guards, selection, and tooltips remain package-owned; the focused copy contains no PowerCRUD JavaScript.

### Focused Inline Form Row Override

`--component inline-row-form` creates `{app}/templates/{app}/{model}_inline_row_form.html`. It receives row/form/hidden-field/config/save/cancel/selection/list/action context. Preserve active-row identity and URL, bound fields and labels, hidden preserved values, CSRF, dependency and error metadata, the aligned action cell, and exact Save/Cancel HTMX hooks for behavior you retain.

Direct `partial/list.html#inline_row_form` remains the server-addressable façade used by entry and invalid-save responses. Inline fields have their own focused dependency-response boundary; validation stays in `inline-row-form` because widget error attributes, adjacent messages, and non-field errors form one row contract. Focus, widths, searchable widgets, dependency swaps, spinners, events, error popovers, and repeated initialization remain package-owned; the focused copy contains no PowerCRUD JavaScript.

### Focused Inline Field Override

`--component inline-field` creates `{app}/templates/{app}/{model}_inline_field.html`. It receives one bound `field`, `field_name`, optional `field_dependency`, and `dependency_endpoint_url`. Preserve a single stable `.inline-field-widget[data-inline-field]` root, dependency parent/endpoint metadata, and the bound field with all widget-supplied attributes.

The direct `partial/inline_field.html` path remains the built-in 0.x fallback. This component is used only for dependency-refresh replacements; inline-row-form retains initial/invalid-save validation ownership. OuterHTML replacement, dependency wiring, searchable-select initialization, failure restoration, and repeated swaps remain package-owned; the focused copy contains no PowerCRUD JavaScript.

---

## `pcrud_extract_tailwind_classes` - Extract Tailwind CSS Classes

Copy compiled CSS files and generate Tailwind safelist for your build process.

### Usage

```bash
# Basic usage (requires TAILWIND_SAFELIST_JSON_LOC setting)
python manage.py pcrud_extract_tailwind_classes

# Specify output location
python manage.py pcrud_extract_tailwind_classes --output ./config/

# Specify exact filename
python manage.py pcrud_extract_tailwind_classes --output ./config/safelist.json
```

### Options

- `--output PATH` - Specify output path (directory or file path)
- `--legacy` - Use legacy method of extracting classes (currently unused)

### Configuration

Set the output location in your Django settings:

```python
# settings.py
POWERCRUD_SETTINGS = {
    'TAILWIND_SAFELIST_JSON_LOC': 'config',           # BASE_DIR/config/powercrud_tailwind_safelist.json
    # or, to pin a specific file path:
    # 'TAILWIND_SAFELIST_JSON_LOC': 'config/safelist.json',
    # ... other settings
}
```

### Examples

```bash
# Using settings configuration
python manage.py pcrud_extract_tailwind_classes

# Override with command line
python manage.py pcrud_extract_tailwind_classes --output ./static/css/

# Specify exact output file
python manage.py pcrud_extract_tailwind_classes --output ./tailwind/safelist.json
```

### Integration with Tailwind

Use the generated file in your `tailwind.config.js`:

```javascript
module.exports = {
  content: [
    // your content paths
  ],
  safelist: require('./config/powercrud_tailwind_safelist.json')
}
```

See [Styling & Tailwind](../guides/styling_tailwind.md) for more details.

---

## `pcrud_cleanup_async` - Cleanup Async Artifacts

Remove stale locks, progress keys, and dashboard rows left behind by completed or abandoned async tasks.

### Usage

```bash
# Human-readable summary
python manage.py pcrud_cleanup_async

# Structured output for scripts/monitoring
python manage.py pcrud_cleanup_async --json
```

### Behaviour

- Skips execution when `POWERCRUD_SETTINGS["ASYNC_ENABLED"]` is `False`.
- Inspects the cache of active tasks, checking `django_q.Task` for completion.
- Removes conflict locks and progress entries when safe, then calls the configured async manager’s `cleanup_dashboard_data`.
- Returns a summary dictionary (or JSON) detailing cleaned and skipped tasks.

### Example summary

```
PowerCRUD Async Cleanup Summary
Active tasks inspected: 3

Cleaned 2 task(s):
  - 9f2b... (completed successfully) [locks=5, progress=1, dashboard=1]
  - 174c... (completed with failure) [locks=3, progress=1, dashboard=1]

Skipped 1 active task(s):
  - 2cd0...: task still running
```

Use the JSON mode to feed the data into logging or alerting pipelines.

---

## `pcrud_help` - Open Documentation

Opens the powercrud documentation in your default browser.

### Usage

```bash
python manage.py pcrud_help
```

### Behavior

Opens your default web browser to the powercrud documentation at:
`https://doctor-cornelius.github.io/django-powercrud/`

---

## Common Use Cases

### Initial Setup

```bash
# 1. Copy templates for customization
python manage.py pcrud_mktemplate myapp --all

# 2. Generate Tailwind safelist (if using Tailwind)
python manage.py pcrud_extract_tailwind_classes --output ./config/
```

### Template Customization Workflow

```bash
# Copy specific templates you want to modify
python manage.py pcrud_mktemplate myapp.Book --list
python manage.py pcrud_mktemplate myapp.Book --form

# Templates are now in myapp/templates/myapp/ for customization
```

### Tailwind CSS Workflow

```bash
# Generate safelist for Tailwind build
python manage.py pcrud_extract_tailwind_classes

# Add to your tailwind.config.js safelist
# Rebuild your CSS

# Optional: clear stale async state
python manage.py pcrud_cleanup_async --json
```
