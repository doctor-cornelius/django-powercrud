# Customisation tips

Once the basics are in place you may want to tailor templates, extend mixins, or integrate PowerCRUD into broader workflows. This chapter rounds up the common tweaks and points to deeper references.

---

## 1. Copy and tweak templates

Use the management command to copy PowerCRUD templates into your app:

```bash
# Copy entire structure
python manage.py pcrud_mktemplate myapp --all

# Just the CRUD templates for a model
python manage.py pcrud_mktemplate myapp.Project --all

# Specific pieces
python manage.py pcrud_mktemplate myapp.Project --list
python manage.py pcrud_mktemplate myapp.Project --form
```

Model-root and focused copies land directly in `myapp/templates/myapp/` and are selected automatically before the packaged default, so removing one restores that default. App-wide `myapp --all` instead creates a cohesive `myapp/templates/myapp/{framework}/` tree; set `templates_path = "myapp/{framework}"` on the view to use it, and do not rely on arbitrary deleted files falling back outside that selected tree.

---

## 2. Override pagination only

If you only want different pagination navigation, copy that component instead of the whole list template:

```bash
python manage.py pcrud_mktemplate myapp.Project --component pagination
```

This creates `myapp/templates/myapp/project_pagination.html`. Change its markup, classes, labels, or icons while keeping `data-powercrud-pagination` and the existing page-link behaviour. You do not need to copy PowerCRUD JavaScript.

See [Management commands](../../reference/mgmt_commands.md#focused-pagination-override) for the component context and compatibility requirements.

### Override the page-size selector

To change only the Rows-per-page control, use:

```bash
python manage.py pcrud_mktemplate myapp.Project --component page-size
```

This creates `myapp/templates/myapp/project_page_size_selector.html`. Keep the existing IDs, `data-powercrud-page-size-select`, and selector name so PowerCRUD continues to refresh the list and preserve its query state.

### Override primary list actions

To change only the Create and extra-action controls, use:

```bash
python manage.py pcrud_mktemplate myapp.Project --component list-actions
```

This creates `myapp/templates/myapp/project_list_actions.html`. Keep the Create link's normal and HTMX/modal behaviour and `{% extra_buttons view %}`. The surrounding toolbar and bulk-selection controls stay in PowerCRUD's list template, and you do not need to copy PowerCRUD JavaScript.

### Override the filter trigger

To change only the filter-toggle button, use:

```bash
python manage.py pcrud_mktemplate myapp.Project --component filter-toggle
```

This creates `myapp/templates/myapp/project_filter_trigger.html`. Keep `#filterToggleBtn`, its `aria-controls="filterCollapse"` relationship, the filter-toggle and icon hooks, and tooltip metadata so PowerCRUD can continue to open the filter panel and show active-filter state. You do not need to copy PowerCRUD JavaScript.

### Override filter-panel actions

To change only the add-filter, reset, and non-HTMX Filter controls, use:

```bash
python manage.py pcrud_mktemplate myapp.Project --component filter-panel-actions
```

This creates `myapp/templates/myapp/project_filter_panel_actions.html`. Keep the add-filter container and selector hooks, the reset link, and the `form="filter-form"` relationship so PowerCRUD can retain optional-filter selection and progressive reset behaviour. You do not need to copy PowerCRUD JavaScript.

### Override the filter form

To change the filter-field layout or optional-filter controls, use:

```bash
python manage.py pcrud_mktemplate myapp.Project --component filter-form
```

This creates `myapp/templates/myapp/project_filter_form.html`. Keep `#filter-form`, its HTMX attributes, `data-powercrud-visible-filters-state`, and optional-filter remove hooks so PowerCRUD can retain filter values, history, and optional-filter state. You do not need to copy PowerCRUD JavaScript.

### Override the list-column chooser

To change only the visible-column chooser, use:

```bash
python manage.py pcrud_mktemplate myapp.Project --component list-columns
```

This creates `myapp/templates/myapp/project_list_columns.html`. Keep the trigger, hidden-template, panel, checkbox, query-state, Save, and Reset hooks so PowerCRUD can continue to float the panel, guard the last visible column, integrate with favourites, and submit normally or through HTMX. The outer toolbar stays in PowerCRUD's list template, and you do not need to copy PowerCRUD JavaScript.

### Override row actions

To change how each row's View, Edit, Delete, and extra actions are presented, use:

```bash
python manage.py pcrud_mktemplate myapp.Project --component row-actions
```

This creates `myapp/templates/myapp/project_row_actions.html`. PowerCRUD supplies already-authorized, resolved presentation data in `row_actions`, so the template should arrange and style those actions rather than reimplement permissions, state hooks, or URL resolution. Keep the action and any dropdown, lazy-state, disabled-tooltip, HTMX, modal, and modal-close-refresh hooks that your chosen interactions use. You do not need to copy PowerCRUD JavaScript.

### Override the table header

To change only column headings, sort indicators, or header help, use:

```bash
python manage.py pcrud_mktemplate myapp.Project --component table-header
```

This creates `myapp/templates/myapp/project_table_header.html`. Keep the current sort and query-state handling, HTMX sorting attributes, semantic help trigger, conditional Actions heading, and select-all hooks that your list uses. The retained list partial delegates separately to the focused table shell and rows, and you do not need to copy PowerCRUD JavaScript.

### Override normal table rows

To change normal display rows and their cells, use:

```bash
python manage.py pcrud_mktemplate myapp.Project --component table-row
```

This creates `myapp/templates/myapp/project_table_row.html`. Keep the row and cell metadata plus any selection, inline-display, dependency, link, tooltip, and row-action hooks your list uses. The built-in row and direct display fragment are compatibility façades over `inline-row-display`; the direct form fragment remains the `inline-row-form` façade. You do not need to copy PowerCRUD JavaScript.

### Override the table shell

To change the responsive wrapper and overall table structure, use:

```bash
python manage.py pcrud_mktemplate myapp.Project --component table-shell
```

This creates `myapp/templates/myapp/project_table_shell.html`. Keep the wrapper/table geometry, selection-key and inline-enabled attributes, object loop, and focused header/row delegation that your list uses. Styles and direct inline display/form fragments stay in PowerCRUD's legacy list partial, and you do not need to copy PowerCRUD JavaScript.

### Override bulk-selection status

To change the selected-count, bulk-action, and Clear Selection controls, use:

```bash
python manage.py pcrud_mktemplate myapp.Project --component bulk-selection-status
```

This creates `myapp/templates/myapp/project_bulk_selection_status.html`. Keep `#bulk-actions-container`, `#selected-items-counter`, the bulk-action modal metadata, the clear-selection hook, and the existing HTMX endpoints and outer swaps. The toolbar placement and matching-record selection prompt remain in PowerCRUD's list template, while selection state and behavior remain in PowerCRUD JavaScript.

### Override bulk-selection controls

To change the matching-record action, select-all cell, and row-selection cell together, use:

```bash
python manage.py pcrud_mktemplate myapp.Project --component bulk-selection-controls
```

This creates `myapp/templates/myapp/project_bulk_selection_controls.html`. It is a three-mode component selected with `selection_control` set to `matching`, `select_all`, or `row`; retain all three branches. Keep the matching-action URL and query state, select-all and row hooks, initial-state metadata, and HTMX status target. Selection persistence and repeated initialization remain package-owned.

### Override the bulk form and fields

Use `--component bulk-form` for the modal form shell and `--component bulk-fields` for only the repeated update controls. The shell must keep delegating through `bulk_fields_template_paths` if the focused fields override should remain active. Preserve submitted field names, selected IDs, CSRF, modal targets, update/delete hooks, and many-to-many action names. The legacy `#full_form` façade retains PowerCRUD's functional script, so neither copied component contains JavaScript.

Use `--component bulk-outcomes` to restyle operation errors, generic errors, conflicts, and queued results together. Keep all four `bulk_outcome` modes and their polling, progress, modal, and feedback hooks. Legacy fragments retain PowerCRUD's functional progress behavior, so the copied component remains script-free.

### Override the modal shell

Use `--component modal-shell` to change the dialog, modal box, close controls, backdrop, and empty content target without taking ownership of the forms or other content loaded into it. Preserve the configured IDs, modal and box hooks, stored default box classes, native dialog controls, and viewport/scroll behavior. PowerCRUD continues to own sizing, cleanup, closing, and repeated initialization.

Use `--component modal-content` when only the empty HTMX content host needs different classes or markup. Keep the configured target ID and an empty element for inner-content replacement. A custom modal shell must continue delegating through `modal_content_template_paths` if this nested override should remain active.

### Override the form shell

Use `--component form-shell` to change the create/update heading, contextual display, form container, and transport attributes without copying the whole object-form template. Preserve the POST action, multipart and CSRF handling, retained list-query inputs, `data-powercrud-form="object"`, and normal/modal HTMX behavior. Keep delegating through `form_fields_template_paths` and `form_actions_template_paths` if their focused overrides should remain active. The copied shell contains no PowerCRUD JavaScript.

Use `--component form-fields` when only native Django or crispy-tailwind field rendering should change. Keep both `use_crispy` branches unless the application intentionally standardizes on one renderer, and do not introduce another `<form>` or CSRF token. The shell continues to own transport and actions; the legacy crispy fragments remain available.

Use `--component form-actions` to restyle or extend the Save control. Keep it as a submit control inside the surrounding shell and retain `data-form-save` for PowerCRUD's package-owned request spinner. Do not move action URLs, CSRF, or HTMX behavior into this leaf.

Use `--component form-conflict` to restyle edit-conflict feedback and its non-modal return control. Preserve modal suppression and, where used, the existing HTMX target/history/query hooks. The direct `#conflict_detected` and routed `#pcrud_content` legacy fragments continue delegating to this component.

### Override detail presentation

Use `--component detail-shell` to change the card and object heading while retaining `{% object_detail object view %}` for separately overridable content. Use `--component detail-content` to change only the formatted label/value table. The legacy root fragment and direct detail partial remain available, and normal/modal transport and permissions stay outside both focused components.

Use `--component delete-shell` to change the normal confirmation card and `--component delete-content` to change its body, errors, and form transport. Preserve nested candidate delegation, CSRF, retained query inputs, and normal/modal HTMX attributes. Conflict and action presentation remain separate, while all deletion decisions stay in Python.

Use `--component delete-actions` to restyle the destructive submit control without taking ownership of the form. Use `--component delete-conflict` for conflict feedback and non-modal return controls, preserving its direct body-only legacy fragment, modal suppression, and existing HTMX page-size/target/history hooks.

### Override inline display rows

Use `--component inline-row-display` to change both normal list rows and rows returned by inline cancel/guard responses. Preserve identity, selection, dependency, editable/blocked, link/tooltip, and action hooks. The legacy direct fragment and built-in table-row remain façades; all inline lifecycle JavaScript stays package-owned.

Use `--component inline-row-form` to change the active edit row. Preserve named fields, hidden preserved values, selection placeholder, error/dependency metadata, and exact Save/Cancel hooks and targets. The direct legacy form fragment remains available; inline-field customization stays separate, while validation remains part of this cohesive row-form boundary.

Use `--component inline-field` to change only the widget wrapper returned by dependency refreshes. Keep one replaceable root plus the field/dependency hooks, and render the supplied bound field so values, options, and searchable attributes survive. Initial and invalid form rows remain owned by `inline-row-form`.

---

## 3. Extend mixins and views

Because PowerCRUD leans on mixins, you can override behaviour by subclassing:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # …
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(owner=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs
```

Useful hooks:

- `get_queryset`, `get_filter_queryset_for_field`.
- `get_bulk_choices_for_field`, `get_bulk_selection_key_suffix`.
- `persist_single_object` for validated standard form and inline writes.
- `persist_bulk_update` for synchronous bulk update writes.
- `get_context_data` for injecting extra template data.

If your sync bulk service needs to reject the batch with a user-facing validation message, return the standard handled bulk result payload instead of raising an unhandled exception. See [Bulk editing (synchronous)](../bulk_edit_sync.md#handling-validation-errors-in-persist_bulk_update).

Use the [Hooks reference](../../reference/hooks.md) for the canonical hook contracts and signatures.

If you want a more guided explanation of when persistence hooks are worth using, start with the [Advanced Guides](index.md), especially [Persistence Hooks](persistence_hooks_sync.md) and [Async Bulk Persistence](persistence_hooks_async_bulk.md).

### Persistence hooks

Use the sync persistence hooks when your app needs validated PowerCRUD inputs but wants business write orchestration to live in an app service rather than in several separate view overrides.

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    def persist_single_object(self, *, form, mode, instance=None):
        project = super().persist_single_object(
            form=form,
            mode=mode,
            instance=instance,
        )
        ProjectAuditService().record_save(project=project, mode=mode)
        return project

    def persist_bulk_update(
        self,
        *,
        queryset,
        fields_to_update,
        field_data,
        progress_callback=None,
    ):
        return ProjectBulkUpdateService().apply(
            queryset=queryset,
            fields_to_update=fields_to_update,
            field_data=field_data,
        )
```

Notes:

- `persist_single_object(...)` is used by both the normal form save path and inline row save path.
- `mode` is currently `"form"` or `"inline"`.
- If you bypass `form.save()` in `persist_single_object(...)`, your override owns any required `form.save_m2m()` handling.
- `persist_bulk_update(...)` is sync bulk-update only in this release. Bulk delete and async bulk persistence remain separate follow-up concerns.
- The full hook contract now lives in the [Hooks reference](../../reference/hooks.md).

### Migrating older write overrides

If an existing downstream project is overriding internal methods only to take control of persistence, move that logic onto the public hooks instead:

- move standard form-save write logic from `form_valid()` into `persist_single_object(...)`
- move inline write logic from inline-save internals into the same `persist_single_object(...)`
- move sync bulk-update write logic from bulk internals into `persist_bulk_update(...)`
- move async bulk-update write logic out of worker patches and into `BulkUpdatePersistenceBackend` plus `bulk_update_persistence_backend_path`

Keep the older override only when it also changes validation, response handling, or another non-persistence part of the flow.

---

## 3. Custom actions and buttons

For one-off toolbar buttons and row actions, use the Base Configuration API examples in [Extra Buttons](../setup_core_crud.md#extra-buttons) and [Extra Actions](../setup_core_crud.md#extra-actions).

For repeated action patterns, use `PowerButton` and `PowerAction`. They compile to the same `extra_buttons` and `extra_actions` entries and can be mixed with dictionaries in the same list. See [PowerAction and PowerButton](../structured_api/poweractions.md) and [Structured API Recipes](../structured_api/recipes.md).

Use the [Configuration options](../../reference/config_options.md) and [PowerAction and PowerButton Reference](../../reference/poweractions.md) for the full option schema.

---

## 4. Integrate with other workflows

- **Signals or admin** – Import the same async helpers ([Async Manager](../async_manager.md)) to queue work or enforce locks outside PowerCRUD.
- **Notifications** – Override `async_task_lifecycle` in your manager to send emails/slack messages on `fail`/`complete`.
- **Audit logging** – Hook into lifecycle events or override CRUD methods such as `persist_single_object(...)` / `persist_bulk_update(...)` to push entries to your logging system.

---

## 5. Useful references

- [Configuration options](../../reference/config_options.md) – complete list of view settings and defaults.
- [Hooks reference](../../reference/hooks.md) – canonical contracts for the main public override points.
- [Management commands](../../reference/mgmt_commands.md) – template copy, Tailwind safelist, async cleanup.
- [Sample app](../../reference/sample_app.md) – full working example you can mine for patterns.

---

## Next steps

You now have the full toolkit: core CRUD, synchronous and async bulk operations, reusable async helpers, dashboards, styling, and customisation. Refer back to the guides as needed and keep the reference section handy for specific settings or commands. Happy shipping!
