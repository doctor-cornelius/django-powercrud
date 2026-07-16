# Customising a Template Pack

Start with the smallest override that expresses the change. PowerCRUD keeps the surrounding behaviour, nested template selection, and JavaScript lifecycle until you explicitly take ownership of a wider layer.

There are three different ownership levels, and they do not substitute for one another:

1. **A model or view override** changes templates for selected screens. It can be as small as one component and does not copy CSS or JavaScript.
2. **A project override** shares copied templates across views that opt into one `template_override_path`. `--all` makes that project tree a complete template copy; `--assets` separately makes the base-template runtime application-owned.
3. **An independent template pack** is a publishable Django package that another project can select at startup. It owns its templates, optional adapters, and pack assets. It is the right choice for a new CSS framework, not for one project-specific layout change.

The package remains the final template fallback unless you deliberately take complete ownership. Assets are always app/base-template-wide: they are never model-specific or view-specific.

## Choose the narrowest override layer

These layers are deliberately different. Choose the row whose scope matches the change you need; copying a wider layer also means taking responsibility for more package markup during upgrades.

| If you need to change... | Use this layer | Who it affects |
| --- | --- | --- |
| One reusable part of a screen, such as pagination or form actions | A focused component: `myapp.Project --component NAME` | Every PowerCRUD view for that model. |
| One or all four main screens for one model | A model root: `myapp.Project --list`, `--detail`, `--form`, `--delete`, or `--all` | Every PowerCRUD view for that model. |
| A main screen for one particular view class | An explicit candidate in that view's `get_template_names()` | Only that view class. |
| One or all main screens shared by selected views across models | A project root: `myapp --list`, `--detail`, `--form`, `--delete`, or the default four roots | Views that set that project root's `template_override_path`. |
| Every current template and component in the selected pack | A complete project pack: `myapp --all` | Views that set that project root's `template_override_path`. |
| The selected pack's CSS or JavaScript | An app-level asset snapshot: `myapp --assets` | Every page using that base template and selected pack. |
| A separately selectable presentation implementation | A custom template pack | Any application that selects that pack at startup. |

Model roots take precedence over a configured project root, and the selected package remains the final fallback. A view-specific candidate can be placed before those normal candidates when one view needs a different template. `--all` is the only project-copy scope that takes complete template ownership; it requires `template_override_complete = True`. `--assets` is separate from template scope and is never model- or view-specific.

This page explains which layer to choose. [Management Commands](../reference/mgmt_commands.md#pcrud_mktemplate---copy-crud-templates-and-assets) is the detailed source of truth for options, generated paths, and preservation rules. To create a selectable pack rather than an application override, see [Authoring and publishing](authoring-and-publishing.md).

## Focused component overrides

Use a focused component override when you need to change one part of a PowerCRUD screen. Generate it for the model and surface you need to change:

```bash
python manage.py pcrud_mktemplate myapp.Project --component pagination
```

The command writes an application template such as `myapp/templates/myapp/project_pagination.html`. Keep the documented element IDs, data attributes, nested template calls, and form ownership rules in the generated file. They are the boundary between your markup and PowerCRUD's behaviour.

??? info "Every focused component"

    This is the complete current list of supported components. Each option uses `python manage.py pcrud_mktemplate myapp.Project --component NAME` and creates a model-specific template override. Choose the smallest surface that contains your change.

    | `NAME` | Surface | Use it to change |
    | --- | --- | --- |
    | `pagination` | List | Page-navigation links and their presentation. |
    | `page-size` | List | The Rows-per-page selector and its surrounding copy. |
    | `list-actions` | List | Create and extra-action controls above the list. |
    | `filter-toggle` | List | The button that opens or closes the filter panel. |
    | `filter-panel-actions` | List | Add-filter, reset, and non-HTMX filter controls. |
    | `filter-form` | List | Filter fields, their layout, and optional-filter controls. |
    | `list-columns` | List | The list-column chooser. |
    | `row-actions` | List | Per-row action controls and their menu presentation. |
    | `table-header` | List | List-table headings and header controls. |
    | `table-row` | List | Normal read-only display rows. |
    | `table-shell` | List | The list table's outer markup and scroll container. |
    | `bulk-selection-status` | Bulk editing | Selected-count status and bulk-selection actions. |
    | `bulk-selection-controls` | Bulk editing | Row checkboxes, select-all, and matching-record controls. |
    | `bulk-form` | Bulk editing | The bulk-edit form shell and its transport attributes. |
    | `bulk-fields` | Bulk editing | Bulk-update field controls. |
    | `bulk-outcomes` | Bulk editing | Bulk errors, conflicts, and queued-result presentation. |
    | `modal-shell` | Modals | The dialog, backdrop, and outer modal structure. |
    | `modal-content` | Modals | The empty host that receives HTMX modal content. |
    | `form-shell` | Create and update | The form container, heading, transport, and nested field/action slots. |
    | `form-fields` | Create and update | Native Django or configured Crispy field rendering. |
    | `form-actions` | Create and update | Save controls inside the form. |
    | `form-conflict` | Create and update | Edit-conflict presentation. |
    | `detail-shell` | Detail | The detail card, heading, and composition boundary. |
    | `detail-content` | Detail | The formatted detail table, rows, and cells. |
    | `delete-shell` | Delete | The outer delete-confirmation structure. |
    | `delete-content` | Delete | Confirmation copy, validation errors, and nested delete actions. |
    | `delete-actions` | Delete | The destructive submit control. |
    | `delete-conflict` | Delete | Delete-conflict presentation. |
    | `inline-row-display` | Inline editing | The normal and returned read-only inline row. |
    | `inline-row-form` | Inline editing | The active inline edit-form row, including validation presentation. |
    | `inline-field` | Inline editing | A field widget replaced after a dependency refresh. |

The [management-command reference](../reference/mgmt_commands.md) documents each generated template's context and the behaviour that an override must retain.

## Override all main templates for one model

Use this when one model needs a substantially different list, detail, create/edit, and delete layout. For example, every standard PowerCRUD view for the `Project` model may need a different overall presentation while the rest of the application should keep using the selected pack:

```bash
python manage.py pcrud_mktemplate myapp.Project --all
```

??? example "Where the files go, and what happens with two views"

    === "Generated files"

        The command writes these files under the Django app's template directory:

        ```text
        myapp/
            templates/
                myapp/
                    project_list.html
                    project_detail.html
                    project_form.html
                    project_confirm_delete.html
        ```

        PowerCRUD looks for these model-specific names before it looks in the selected pack. The command overwrites an existing file at the same path. A different model gets its own names: `python manage.py pcrud_mktemplate myapp.Invoice --all` creates `invoice_list.html`, `invoice_detail.html`, `invoice_form.html`, and `invoice_confirm_delete.html`.

    === "Two views, one model"

        The copies are model-specific, not view-specific. Both of these views use the `project_*.html` files because they both set `model = Project`:

        ```python
        class ProjectCRUDView(PowerCRUDMixin, CRUDView):
            model = Project


        class ProjectReviewCRUDView(PowerCRUDMixin, CRUDView):
            model = Project
        ```

        Other models continue to use the selected pack.

    === "One view needs different templates"

        For a full CRUD view with its own list, detail, form, and delete templates, add a view-specific candidate before the normal model candidates:

        ```python
        class ProjectReviewCRUDView(PowerCRUDMixin, CRUDView):
            model = Project

            def get_template_names(self):
                return [
                    f"myapp/project_review{self.template_name_suffix}.html",
                    *super().get_template_names(),
                ]
        ```

        Create the matching files, for example `myapp/templates/myapp/project_review_list.html` and `myapp/templates/myapp/project_review_form.html`. If a view-specific file is absent, PowerCRUD falls back to the normal `project_*.html` file and then to the selected pack.

        If this view must ignore an existing `project_*.html` override and render the selected pack's standard templates instead, do not call `super()`. Return only the selected pack candidate:

        ```python
        from powercrud.mixins.config_mixin import resolve_config


        class ProjectReviewCRUDView(PowerCRUDMixin, CRUDView):
            model = Project

            def get_template_names(self):
                config = resolve_config(self)
                return [
                    f"{config.templates_path}/object{self.template_name_suffix}.html",
                ]
        ```

        This view then skips `myapp/project_*.html` and renders the selected pack's list, detail, form, or delete template directly.

Remove a copied template when you no longer need it and the affected `Project` screen returns to the selected pack, including future package fixes.

## Override a template pack for your project

Use an app-level copy when several models need the same overall presentation, or when your project needs to edit the complete pack. This is different from a model override: it applies to every PowerCRUD view that sets `template_override_path`.

??? info "Project-pack command choices"

    These commands use a plain app target such as `myapp`, not `myapp.Project`. Scope flags are mutually exclusive; `--assets` is independent and can be added to any app-level template scope.

    | Choice | Allowed value or values | Result |
    | --- | --- | --- |
    | Source pack | no flag / `daisyui`; `--source-template-pack bootstrap5`; or `--source-template-pack module.path:attribute` for an installed pack | Selects the files to copy. It must match `POWERCRUD_TEMPLATE_PACK` at runtime. |
    | One root | `--list`, `--detail`, `--form` (also `--create` or `--update`), `--delete` | Copies only that root template. Other roots and components fall back to the selected pack. |
    | Four roots | no scope flag or `--core` | Copies list, detail, form, and delete roots; components still fall back. |
    | Complete templates | `--all` | Copies the full template tree. Set `template_override_complete = True` on views that use it. |
    | Runtime assets | `--assets` | Adds a manual-static CSS/JavaScript snapshot. It does not change template lookup. |

    `--component NAME` remains model-specific. An app-level root selector such as `--list` may be combined with `--assets`; a model target such as `myapp.Project` may not use `--assets`.

```bash
# Copy only the list root from DaisyUI; the other roots and components still fall back.
python manage.py pcrud_mktemplate myapp --list

# Copy the four main DaisyUI templates.
python manage.py pcrud_mktemplate myapp

# Copy every DaisyUI template, including components.
python manage.py pcrud_mktemplate myapp --all

# Copy every Bootstrap 5 template, including components.
python manage.py pcrud_mktemplate myapp --source-template-pack bootstrap5 --all

# Copy templates and a DaisyUI manual-static asset snapshot.
python manage.py pcrud_mktemplate myapp --assets
```

The default source is DaisyUI. The command writes DaisyUI copies to `myapp/templates/myapp/powercrud/daisyui/`; Bootstrap copies go to `myapp/templates/myapp/powercrud/bootstrap5/`. Add that root to each view that should use it:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    model = Project
    template_override_path = "myapp/powercrud/daisyui"
```

Model-specific templates still come first. After that, PowerCRUD tries the project root and then the selected pack. The four-template default is therefore a practical way to adjust the main screen layouts while leaving components and nested templates in the selected pack.

The one-root choices write `object_list.html`, `object_detail.html`, `object_form.html`, or `object_confirm_delete.html` under that same directory. They are useful when all configured views need one shared screen change, while all other roots and components should continue to use the selected package.

For an `--all` copy, also set `template_override_complete = True` on the views that use it. This makes direct nested includes use the copied root, so every copied component is editable. It is intentionally a complete-ownership choice: keep the files needed by the copied pack and review upstream template changes when upgrading. Do not set it for a one-root or four-root copy.

The selected runtime pack must be the same pack that you copied. The command does not configure `POWERCRUD_SETTINGS`, install a framework integration, or configure Crispy Forms. It copies CSS and JavaScript only when you add `--assets`. See [Selecting and configuring](selecting-and-configuring.md) for those steps and [Management Commands](../reference/mgmt_commands.md#copy-a-template-pack-for-your-project) for the complete command contract.

### Own the pack runtime only when you need to

`--all` copies every template and component, but it does not copy CSS or JavaScript. Add `--assets` only when the project must change the selected pack's PowerCRUD runtime or stylesheet. The command writes an application-owned manual-static snapshot to `myapp/static/myapp/powercrud/` and prints replacement asset tags for the base template.

Unlike template overrides, copied assets have no package fallback. The base template loads one entry: after switching to the application-owned entry, deleting one copied asset causes a missing file or module import rather than returning to PowerCRUD's package asset. Do not load the copied and package entries together.

Assets apply to every page using that base template and selected pack. They are not model-specific. A `Project` template override can continue to use either the package-owned or application-owned runtime, but `pcrud_mktemplate myapp.Project --assets` is intentionally unsupported. The generated snapshot is for manual-static loading only; Vite projects must maintain their own custom entry rather than combining it with the packaged Vite entry.

## Keep responsibilities clear

Your application owns its base template and any copied override markup. PowerCRUD owns request handling, selection state, HTMX lifecycle, modal cleanup, and its JavaScript unless the generated override documentation says otherwise.

??? info "Choose the right template-root setting"

    | Setting | What it adds or replaces | When to use it |
    | --- | --- | --- |
    | `template_override_path` | Adds an application-owned candidate before the selected pack. Missing templates still fall back to the pack. | A project copy that is partial, or a complete `--all` copy that explicitly sets `template_override_complete = True`. |
    | `templates_path` | Replaces the selected pack namespace. | A view that deliberately owns a complete template tree. |

    Neither setting selects a pack or changes CSS/JavaScript. The base template's chosen frontend route owns those assets.

For style settings, use classes that belong to the selected framework. Values such as `table_classes` and `action_button_classes` are passed through; they are not translated from DaisyUI to Bootstrap or the other way around.
