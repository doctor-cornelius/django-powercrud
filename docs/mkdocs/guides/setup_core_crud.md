# Setup & Core CRUD basics

Use this guide after [Getting Started](./getting_started.md) when your first PowerCRUD list page already renders. It shows how to make that page useful day to day: choose what users see, add filtering and pagination, then improve the table's presentation.

???+ info "How to use this guide"

    For a first useful screen, work through list/detail fields, filtering, pagination, and the list-presentation options that matter to your users. The custom-button, row-action, and detailed modal sections are here when you need them; they are not prerequisites for a working CRUD screen.

---

## Prerequisites

- A working Django project running Django 5.2 or 6.0.
- Python 3.12 or later.

If you have not yet installed PowerCRUD and its base dependencies, complete the steps in [Getting Started](./getting_started.md) first.

---

## 1. Finish the basics

Before enabling the richer features, work through the [Getting Started](./getting_started.md) guide:

- [Install the dependencies](./getting_started.md#installation) and wire up the base template assets you plan to use.
- [Complete the required Django wiring](./getting_started.md#required-configuration), including `django_htmx.middleware.HtmxMiddleware`.
- [Declare your first view](./getting_started.md#basic-setup) and confirm the list/template renders without HTMX extras.
- [Expose the view somewhere in your project URLs](./getting_started.md#add-to-urls).

When you can load the plain CRUD view end-to-end, come back here to add the features your screen needs.

---

## 2. Wire up URLs

If you followed [Getting Started](./getting_started.md#add-to-urls), this is already in place. PowerCRUD uses Neapolitan’s `get_urls()` helper, so you do not write separate paths for the list, create, detail, edit, and delete views.

```python
# myapp/urls.py
from django.urls import path
from neapolitan.views import Role
from . import views

app_name = "projects"

urlpatterns = [
    *views.ProjectCRUDView.get_urls(),
    path("projects/reports/", views.project_report, name="project-report"),
]
```

If this screen should expose only some operations, pass the roles you want:

```python
urlpatterns = [
    *views.ProjectCRUDView.get_urls(roles={Role.LIST, Role.DETAIL}),
]
```

Include the app URLs from your project-level `urls.py` as usual:

```python
# config/urls.py
from django.urls import include, path

urlpatterns = [
    path("projects/", include("myapp.urls")),
]
```

For the full background, see Neapolitan’s [“URLs and view callables”](https://noumenal.es/neapolitan/crud-view/#urls-and-view-callables); PowerCRUD uses the same mechanics.

---

## 3. Shape list and detail scopes

### Choose list and detail content {#field-and-detail-scopes}

Start with the information a user needs to scan in the table. Add detail-only context later; you do not need to configure every surface at once.

**For the list**

- Leave `fields` unset, or set it to `"__all__"`, to show every concrete model field.
- Use an explicit list when the table needs only selected fields. That list can also include supported queryset annotation names.
- Use `exclude` when it is shorter to name what should not appear.
- Add a computed `@property` through `properties`. Use `"__all__"` only when every model property is suitable for a list column.
- Set `list_options_enabled = True` to give users a **Cols** chooser. Add `default_list_fields` when the useful default is a smaller subset of the available columns.

Queryset annotations are read-only list fields. They can filter and sort when the active queryset exposes the same annotation name. They do not belong in form, inline-edit, or bulk-edit field lists.

**For the detail view**

- The **View** button uses `detail_fields`, so this is the place for context you do not need in the table or edit forms.
- `detail_fields` uses the resolved list fields by default. Set it to `"__all__"` or an explicit list when the detail page needs more context.
- `detail_properties` starts empty. Add calculated values here with an explicit list, reuse list properties with `"__properties__"`, or use `"__all__"` when that is genuinely suitable.
- `detail_exclude` and `detail_properties_exclude` let you fine-tune those choices without repeating every field name.

### Optional custom buttons {#extra-buttons}

Skip this section until the standard list is working. Use `extra_buttons` for page-level actions above the table, such as a report, an import, or a summary of selected records. They are not actions on an individual row. The standard configuration API uses dictionaries for these entries.

Use `extra_buttons_mode = "dropdown"` when several page-level actions would make the toolbar hard to scan. The built-in Create button remains visible because it is not part of `extra_buttons`.

Typical uses:

- link to dashboards or reports
- open custom modals
- add list-level utilities that are not tied to a single row

Start with a normal link or endpoint:

```python
extra_buttons = [
    {
        "url_name": "projects:report",
        "text": "Project report",
        "needs_pk": False,
        "display_modal": False,
    },
]
```

??? info "Selection, permissions, and modal buttons"

    A button with `uses_selection = True` reads PowerCRUD's persisted selection at its endpoint; it does not receive row IDs in the URL. It can show row-selection controls even when bulk edit and bulk delete are disabled.

    A successful selection-aware HTMX request clears that selection by default. Set `clear_selection_on_success = False` for a read-only summary or preview that should leave the selection in place. Failed requests leave it intact.

    Set `extra_button_selection_controls_disabled = True` only when a button reads a selection that comes from another part of the page or from your own selection control. Bulk edit and bulk delete still need their normal checkboxes.

    Use `permission` or `permission_check` when the button should be hidden or disabled for users who cannot use it. This only controls the PowerCRUD UI: your endpoint must still validate permissions and input.

    A button can set `display_modal = True` and a partial `modal_presentation` when it should open in a modal. See [Modals](#modals) for the shared modal settings.

??? info "All button options"

    | Parameter | Type | What it does |
    | --- | --- | --- |
    | `url_name` | `str` | Django URL name for the endpoint to call when the button is clicked. |
    | `text` | `str` | Visible button label shown above the table. |
    | `button_class` | `str` | CSS class applied to the button, such as `btn-primary` or `btn-success`. |
    | `needs_pk` | `bool` | Usually `False` for header buttons because they are page-level actions rather than row-level actions. |
    | `display_modal` | `bool` | If `True`, PowerCRUD opens the response in the standard modal target instead of treating it as a normal page/content navigation. |
    | `modal_presentation` | `dict` | Optional portable override for this modal button: size, maximum width/height, scroll ownership, fullscreen, and vertical alignment. |
    | `refresh_list_on_modal_close` | `bool` | Optional. When `True` on a modal button, closing that modal refreshes the current list partial. Defaults to `False`. |
    | `htmx_target` | `str` | HTMX target element to swap into when the button is clicked and it is not using the default modal target. |
    | `extra_attrs` | `str` | Raw HTML attributes appended to the button element when you need custom HTMX or data attributes. |
    | `extra_class_attrs` | `str` | Extra CSS classes appended to the button in addition to `button_class`. |
    | `uses_selection` | `bool` | When `True`, the endpoint should operate on the current persisted PowerCRUD selection. |
    | `clear_selection_on_success` | `bool` | Clears the persisted selection after a successful HTMX request from a selection-aware button. Defaults to `True` when `uses_selection=True`, otherwise `False`; ignored unless `uses_selection=True`. |
    | `selection_min_count` | `int` | Minimum number of selected rows required before the button is considered ready. |
    | `selection_min_behavior` | `str` | `'allow'` leaves the button clickable below the minimum and lets the endpoint handle the error; `'disable'` greys it out in the UI. |
    | `selection_min_reason` | `str` | Tooltip/help text shown when a selection-aware button is disabled because too few rows are selected. |

??? note "Refreshing the list after custom modal close"

    Prefer having a custom endpoint emit `HX-Trigger: {"refreshTable": true}` when that endpoint knows it changed data. That keeps refresh behavior tied to the mutation.

    Use `refresh_list_on_modal_close = True` only when the modal itself is the practical boundary for refreshing, for example a custom modal workflow that cannot easily emit response headers from the final action. The option is ignored unless `display_modal=True`.

### Optional row actions {#extra-actions}

Use `extra_actions` only when a row needs an operation beyond the built-in **View**, **Edit**, and **Delete** controls. These actions belong to your application, so build and secure their endpoints as you would any other Django view. The standard configuration API uses dictionaries for these entries.

For row actions, `extra_actions_mode` controls whether the extra actions stay visible as buttons or move into an overflow menu:

- `extra_actions_mode = "buttons"` renders the extra actions beside the built-in controls.
- `extra_actions_mode = "dropdown"` keeps the built-in controls visible and puts only your extra actions in **More**.
- `extra_actions_dropdown_open_upward_bottom_rows = 3` opens **More** upward for the last three rows on the page. Set it to `0` when every menu should open downward.

Start with the smallest useful action:

```python
class AuthorCRUDView(PowerCRUDMixin, CRUDView):
    # ...
    extra_actions = [
        {
            "url_name": "projects:project-timeline",
            "text": "Timeline",
            "needs_pk": True,
            "display_modal": True,
        },
    ]
```

??? info "Conditional and permission-aware row actions"

    Use `permission` or `permission_check` to hide or disable an action for users who cannot use it. PowerCRUD checks permission before row-state checks, but your custom endpoint must still enforce the same rules.

    Use `hidden_if` when an action does not apply to a row. Use `disabled_state` when it does apply but needs to remain visible with an explanation. `hidden_if_mode = "lazy"` and `disabled_state_mode = "lazy"` defer expensive checks until a user opens a dropdown **More** menu.

    Set `display_modal = True` for a modal response, and add partial `modal_presentation` only when this action needs a different modal size or placement from the view default.

??? info "All row-action options"

    | Parameter | Type | What it does |
    | --- | --- | --- |
    | `url_name` | `str` | Django URL name for the per-row endpoint that the action should call. |
    | `text` | `str` | Visible label for the row action button or dropdown entry. |
    | `needs_pk` | `bool` | Usually `True` for row actions so PowerCRUD includes the current row primary key in the URL. |
    | `button_class` | `str` | CSS class used when the action is rendered as a visible button. |
    | `display_modal` | `bool` | If `True`, the response opens in the standard modal instead of replacing page content. |
    | `modal_presentation` | `dict` | Optional portable override for this modal action: size, maximum width/height, scroll ownership, fullscreen, and vertical alignment. |
    | `refresh_list_on_modal_close` | `bool` | Optional. When `True` on a modal action, closing that modal refreshes the current list partial. Defaults to `False`. |
    | `htmx_target` | `str` | HTMX target element used for non-modal actions when you need a custom swap target. |
    | `hx_post` | `bool` | If `True`, renders the action as an HTMX POST instead of the default GET. |
    | `lock_sensitive` | `bool` | Reuses PowerCRUD's existing blocked-row/lock logic so the action disables automatically when the row is not currently actionable. |
    | `hidden_if` | `str` | Name of a view method with signature `(obj, request) -> bool` that decides whether this row action should be omitted. |
    | `hidden_if_mode` | `'eager' \| 'lazy'` | Defaults to `'eager'`. Use `'lazy'` with dropdown row actions to resolve `hidden_if` when the row `More` menu opens. |
    | `disabled_state` | `str` | Name of a view method with signature `(obj, request) -> str | None | bool`. Return a non-empty string to disable the action and show the reason; return `None`, `False`, or an empty string to keep it enabled. |
    | `disabled_state_mode` | `'eager' \| 'lazy'` | Defaults to `'eager'`. Use `'lazy'` with dropdown row actions to resolve `disabled_state` when the row `More` menu opens. |
    | `disabled_if` | `str` | Deprecated. Name of a view method with signature `(obj, request) -> bool` that decides whether this row action should be disabled. Use `disabled_state` instead. |
    | `disabled_reason` | `str` | Deprecated. Name of a view method with signature `(obj, request) -> str | None` that returns the tooltip/help text when the action is disabled. Use `disabled_state` instead. |

    Do not combine `disabled_state` with `disabled_if` or `disabled_reason` on the same action.

    Use `hidden_if` when an action is not applicable for a row. Use `disabled_state` when the action is applicable but unavailable and needs an explanatory reason. Add lazy modes only for dropdown row actions with expensive hooks. The legacy `disabled_if` / `disabled_reason` pair is deprecated and targeted for removal in v1.0.

??? note "Refreshing the list after custom modal close"

    Prefer having a custom endpoint emit `HX-Trigger: {"refreshTable": true}` when that endpoint knows it changed data. That keeps refresh behavior tied to the mutation.

    Use `refresh_list_on_modal_close = True` only when closing the modal is the practical refresh boundary. This is mainly for custom modal workflows outside the normal PowerCRUD form success path. The option is ignored unless `display_modal=True`.

!!! note

    When `extra_actions_mode = "dropdown"`:

    - per-action `button_class` values are no longer used for the dropdown menu entries themselves
    - the `More` trigger uses the framework’s `extra_default` styling instead
    - leaving `button_class` off an `extra_actions` item is therefore fine if that action only ever appears in dropdown mode

### Reusable action and button declarations

Use the Structured API only when related views repeat the same action with small changes. `PowerAction` and `PowerButton` group the same configuration into reusable Python objects, and they can be mixed with dictionaries in one list.

For reusable action patterns, see [PowerAction and PowerButton](structured_api/poweractions.md) and [Structured API Recipes](structured_api/recipes.md). For the full constructor contract, see [PowerAction and PowerButton Reference](../reference/poweractions.md).

For operation permission, hide versus disable behavior, and backend enforcement boundaries, see [Permission-Aware Affordances](advanced/permission_aware_affordances.md).

---

## 4. Enable UI helpers

Once the basic view works, turn on the built-in enhancements.

### Filtering & sorting {#filtering-sorting}

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # …
    use_htmx = True
    filterset_fields = ["owner", "status", "created_date"]
    default_filterset_fields = ["owner", "status"]
```

This is the quickest way to add filters. Use the dedicated [Filtering](filtering.md) guide when you need more than these generated controls.

What happens at a high level:

- With no `filterset_fields`, the list loads without generated filters. Sorting and pagination still work.
- `filterset_fields` asks PowerCRUD to build ordinary `django-filter` controls for those fields.
- Leave `default_filterset_fields` unset to show every allowed filter. Set it to a smaller subset to keep the rest in **Add filter**.
- Typed queryset annotations can be filters when the active queryset exposes the same `annotate(...)` name.
- Sorting stays in the table headers, so users can still share URLs such as `/projects/?sort=status`.

If a sortable relation column should use something other than the normal default, configure `column_sort_fields_override`:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # …
    column_sort_fields_override = {
        "owner": "owner__email",
        "customer": "customer__code",
    }
```

`column_sort_fields_override` changes only the named columns. Other sortable fields keep their normal ordering.

For the full filtering feature set, including:

- default vs optional filters
- null helpers
- `filterset_class` precedence
- M2M AND logic
- filter-side `dropdown_sort_options` and `filter_queryset_options`
- queryset annotation fields
- HTMX visibility persistence

see [Filtering](filtering.md).

Saved favourites are documented separately because they are an optional contrib add-on rather than part of the core filtering contract. See [Saved Favourites](advanced/filter_favourites.md).

### Modals

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # …
    use_htmx = True
    use_modal = True
```

Most screens need only these two settings. Modals depend on HTMX:

- Set `use_htmx = True` first.
- Set `use_modal = True` to open create, edit, delete, bulk, and modal-enabled custom actions in the standard PowerCRUD dialog.
- Failed validation stays in that dialog, so users can correct the form without losing their place in the list.

??? info "Naming and customising the standard modal"

    When `use_modal = True`, PowerCRUD renders and owns the modal shell and its lifecycle. The supplied modal is centred, bounded by the viewport, and scrolls its body by default in both first-party packs. Its normal id is `powercrudBaseModal`; its HTMX content target is `powercrudModalContent`.

    Set `modal_id` or `modal_target` only when the PowerCRUD-rendered shell needs different, page-unique ids. Do not include `#`, and do not reuse an id belonging to a modal or content host already rendered by the application.

    Use `modal_presentation` for the view-wide choices that PowerCRUD maps to the selected pack: named size, maximum width or height, scroll ownership, fullscreen, and vertical alignment. Use `bulk_modal_presentation` only when the built-in Bulk Edit dialog should differ. For structural or behavioural changes, [override the focused modal shell](advanced/customisation_tips.md#override-the-modal-shell) or [customise the selected template pack](../template_packs/customising.md) while preserving PowerCRUD's documented lifecycle hooks.

    `modal_presentation` is a partial mapping. Omitted values use the normal defaults:

    ```python
    {
        "size": "default",                 # compact, default, wide, extra_wide
        "max_width": None,                  # or a safe CSS length such as "48rem"
        "max_height": "viewport",          # or a safe CSS length
        "scroll": "body",                  # body or modal
        "fullscreen": False,
        "vertical_alignment": "center",    # top or center
    }
    ```

    `max_width` overrides the named size. `fullscreen=True` wins over width, height, and alignment. Safe CSS lengths use non-negative `px`, `rem`, `em`, `ch`, `%`, `vw`, `vh`, `dvw`, or `dvh` values; functions such as `calc()` are not accepted in configuration.

When the whole view needs more room, set its modal defaults:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # …
    use_htmx = True
    use_modal = True

    modal_presentation = {"size": "wide"}
    bulk_modal_presentation = {"size": "extra_wide"}
```

An individual modal button, row action, or list-cell link can set its own partial `modal_presentation` when only that one trigger needs different sizing:

```python
extra_actions = [
    {
        "url_name": "projects:timeline",
        "text": "Timeline",
        "display_modal": True,
        "modal_presentation": {"max_width": "64rem", "vertical_alignment": "top"},
    },
]
```

??? warning "Older framework-specific modal classes"

    `modal_classes`, `modal_box_classes`, `modal_body_classes`, `bulk_modal_box_classes`, and per-trigger `modal_box_classes` still work for existing framework-specific templates, but emit `FutureWarning` and are planned for removal before 1.0. Do not combine a new presentation mapping with its older class equivalent. See [Deprecations](../reference/deprecations.md).

### Pagination

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # …
    paginate_by = 25
```

PowerCRUD shows 25 rows per page by default. Set `paginate_by` to another default, or set `paginate_by = None` only when a view should show every record at once.

- By default, the selector shows `5/10/25/50/100` plus **All**.
- Set `page_size_options = [10, 25, 50]` to offer only those finite choices and accept only those values in `?page_size=`.
- Set `page_size_all_enabled = False` to remove **All** and make `?page_size=all` fall back to `paginate_by`.
- When filters change, the mixin automatically snaps back to page 1 so users do not land on empty pages.
- Pagination works with or without HTMX. With HTMX enabled, only the table/pager fragment updates on navigation.

### Record count display

If you want the list view to show a lightweight results summary above the table, enable `show_record_count`:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # …
    show_record_count = True
```

PowerCRUD renders a small line above the table. It updates with filtering, sorting, page-size changes, and page navigation.

Examples:

- No active filters: `123 total records`
- Active filters without pagination: `27 matching records`
- Active filters with pagination: `Showing 1-15 of 27 matching records`

This is useful when users need quick confirmation that a filter narrowed the queryset as expected, without adding extra noise to the main button toolbar.

When row selection controls are enabled, this area can also offer actions such as **Select all matching records**. Leave `show_bulk_selection_meta = True` (the default) to keep that option, even when the record count is off.

## 5. Make the list easier to read

Use these options after the screen's data and interactions are right. They improve scanability without changing what the screen does.

### List heading

If you want the visible list heading to differ from the model’s `verbose_name_plural`, set `view_title` on the CRUD view:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # …
    view_title = "Active Client Projects"
```

`view_title` changes only the large heading above the list table. It does not affect model verbose names or other UI copy such as button labels.

### Helper text

If you want plain-text helper copy directly below the visible list heading, set `view_instructions`:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # …
    view_instructions = "Use the table below to review and update active projects."
```

`view_instructions` adds a small escaped text block directly underneath the heading.

### Collapsed screen help

If you want longer screen-level guidance without making the page header heavy, set `view_help`:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # …
    view_help = {
        "summary": "About this screen",
        "details": (
            "Use this screen to review active projects.\n\n"
            "Inline fields can be edited directly from the table."
        ),
        "color": "info",
    }
```

`view_help` renders a collapsed help panel below `view_instructions` and above the list toolbar. The `summary` is the one-line clickable bar, and `details` is plain text. Separate paragraphs with blank lines. Add `"default_open": True` only when the guidance should start expanded.

??? info "Help-panel appearance"

    The panel uses the quiet `base` colour, follows the rendered table width, and does not shrink below `view_help_min_width = "40rem"` unless its container is narrower. Set `view_help_default_color` or `view_help_min_width` on the view to change those defaults.

    A particular `view_help` can use `"color": "info"` or a hex value such as `"#0ea5e9"`, and can set its own minimum width with `"min_width": "34rem"`. Both first-party packs support these semantic colours and subtle hex tints.

Most views should use either `view_instructions` for a short always-visible sentence or `view_help` for longer optional guidance. Use both only when the short description and expandable detail carry distinct information.

See [Testing and accepting a template pack](../template_packs/testing-and-acceptance.md) for the support boundary across packs.

### Field labels

PowerCRUD normally uses each model field's `verbose_name` for display labels. If a view needs an explicit label, use `field_labels`:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # …
    field_labels = {
        "designated_execution_owner": "DDMS Execution Owner",
    }
```

Explicit labels render exactly on list headers, the column chooser, generated forms, inline edit labels, display-only form items, and bulk edit labels. If no explicit label is configured, PowerCRUD preserves the model field `verbose_name` without applying title case, so acronym labels such as `"DDMS Execution Owner"` stay intact.

### Header tooltips

If you want plain-text help tooltips on selected column headers, use `column_help_text`:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # …
    column_help_text = {
        "owner": "The client or business owner responsible for the project.",
        "display_status": "Calculated status shown for quick triage.",
    }
```

`column_help_text` adds an info trigger beside only the configured labels. Sorting still works normally on the header.

### Tooltips for table cells {#list-cell-tooltips}

Use a list-cell tooltip when a visible value needs a row-specific explanation that would make the table too busy if shown all the time. Configure `list_cell_tooltip_fields` as a field-to-method mapping:

- The key is the rendered field or property name, such as `"owner"`.
- The value is the name of a method on the view, such as `"get_owner_tooltip"`.

PowerCRUD calls that method only for visible cells and uses the returned text as the tooltip.

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # …
    list_cell_tooltip_fields = {
        "owner": "get_owner_tooltip",
        "display_status": "get_display_status_tooltip",
    }

    def get_owner_tooltip(self, obj, request=None):
        return f"{obj.owner.email} ({obj.owner.team.name})"

    def get_display_status_tooltip(self, obj, request=None):
        return obj.status_explanation
```

For expensive tooltip hooks, see [Lazy Evaluation](advanced/lazy_evaluation.md).

Each method receives the row object and should return plain text, or `None` when that row should not show a tooltip. Configured names that are not visible in the table are ignored.

Returned list-cell tooltip text may include newline characters for multiple lines. Header-help and other tooltip surfaces remain single-line.

??? warning "Deprecated generic tooltip hook: legacy list form"

    `list_cell_tooltip_fields = ["owner"]` with `get_list_cell_tooltip(...)` still works for compatibility, but it is deprecated and targeted for removal before v1.0. See [Deprecations](../reference/deprecations.md).

    The deprecations page shows the legacy hook signature, explains how the generic `field_name` branching works, and shows the migration to field-specific hook methods.

Choose the tooltip that matches the job:

- `column_help_text` is header help only.
- `list_cell_tooltip_fields = {"field": "hook_name"}` provides semantic per-cell tooltip text for selected rendered columns.
- Unconfigured cells keep the built-in overflow tooltip behavior when their rendered content is truncated.

When a row-specific tooltip is configured, it replaces the overflow tooltip for that cell. `view_instructions`, `view_help`, `column_help_text`, and list-cell tooltip text are escaped plain text, not HTML.

### Links from table cells {#list-cell-links}

If a rendered value should open another page, configure `link_fields`. The key is the displayed field or property name. For the common internal-link case, the value is simply a Django URL name; use the longer dictionary form only when a link needs extra information:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # …
    list_cell_link_default_open_in = "modal"

    link_fields = {
        # Minimal internal link. Because owner is a relation, PowerCRUD uses
        # obj.owner_id as the pk for reversing crm:owner-detail. Because this
        # view sets list_cell_link_default_open_in, it opens in the modal.
        "owner": "crm:owner-detail",

        # Link this row's own project detail in the shared PowerCRUD modal
        # with per-cell modal sizing. Because reference_code is not a relation,
        # pk_attr defaults to "pk".
        "reference_code": {
            "view_name": "projects:project-detail",
            "modal_presentation": {"size": "extra_wide"},
        },

        # Link a property column to this row's detail view in the current page.
        "display_status": {
            "view_name": "projects:project-detail",
            "pk_attr": "pk",
            "open_in": "current",
        },

        # Static external URL for a rendered property. Browser settings decide
        # tab vs window.
        "is_overdue": {
            "url": "https://docs.example.com/projects",
            "open_in": "new",
        },
    }
```

The supported shapes are:

- keys are rendered list field/property names
- string values are treated as Django `view_name` links
- dict values must include exactly one of `view_name` or `url`
- dict values may also include `pk_attr` for `view_name` links
- dict values may include `open_in`
- dict values may include `modal_presentation` only for modal-opening links

`list_cell_link_default_open_in` sets the view-wide opening style: `"current"`, `"new"`, or `"modal"`. If you omit it, links open in a new browser context. Use `"modal"` when a drill-in should preserve the current list, or `"current"` for normal navigation. An individual link's `open_in` always wins.

`pk_attr` names the current-row attribute PowerCRUD should use as the `pk` URL kwarg for a `view_name`. If you omit it, PowerCRUD uses these defaults:

- relation fields such as `owner` use `<field_name>_id`
- non-relation fields and properties use the current row `pk`

That keeps common links short:

- `{"owner": "crm:owner-detail"}` means “link the `owner` column to the related owner detail using `owner_id`”
- `{"reference_code": "projects:project-detail"}` means “link the `reference_code` column to this project row’s own detail using `pk`”

`open_in` controls an individual link:

- omitted uses `list_cell_link_default_open_in`; if that view option is also omitted, PowerCRUD assumes `"new"`
- `"current"` opens as a normal same-page anchor
- `"new"` renders `target="_blank"` and defaults `rel="noopener noreferrer"`
- `"modal"` reuses the view’s existing PowerCRUD modal target and modal-open attributes

If a link requests `open_in = "modal"` but the view does not use HTMX modals, PowerCRUD falls back to normal current-page navigation.

`modal_presentation` on a modal list-cell link changes the modal only for that clicked cell. It uses the same per-trigger choices as modal buttons and row actions; for example, set
`{"size": "extra_wide"}` or `{"max_width": "64rem"}`.

For conditional links or richer metadata, override `get_list_cell_link(...)`:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # …
    link_fields = {
        "owner": "crm:owner-detail",
    }

    def get_list_cell_link(self, obj, field_name, value, *, is_property, request=None):
        if field_name == "display_status" and obj.status_report_url:
            return {
                "url": obj.status_report_url,
                "title": "Open external status report",
                "open_in": "new",
            }
        if field_name == "reference_code":
            return {
                "url": self.safe_reverse("projects:project-detail", kwargs={"pk": obj.pk}),
                "open_in": "modal",
                "modal_presentation": {"size": "extra_wide"},
            }
        if field_name == "owner" and request and not request.user.has_perm("crm.view_owner"):
            return False
        return None
```

The hook returns one of these values:

- return a dict with at least `url` to link that cell
- include `open_in` when the cell should open somewhere other than the view-wide default
- include `modal_presentation` only with `open_in = "modal"` for portable per-cell modal sizing
- return `None` to fall back to `link_fields`
- return `False` to suppress `link_fields` for that cell

Keep these boundaries in mind:

- inline-editable cells are never linked, because inline click-to-edit takes precedence
- if a field appears in both `link_fields` and `inline_edit_fields`, PowerCRUD logs a warning and silently skips the link at render time
- the hook applies to fields and properties, not only relations

### Column alignment

PowerCRUD chooses a sensible body-cell alignment from the field type. If a short categorical value would scan better centred or right-aligned, override that one column:

??? info "Default body-cell alignment"

    | Field or value category | Default alignment |
    | --- | --- |
    | Text-like fields: `CharField`, `TextField`, `SlugField`, `EmailField`, and `URLField` | Left |
    | Relations, including foreign keys and many-to-many fields | Left |
    | All other typed Django fields, including booleans, numbers, dates, times, and automatic primary keys | Centre |
    | Typed queryset annotations | Follows the same rule using the annotation's declared `output_field` |
    | Untyped computed properties whose value is boolean | Centre |
    | Other untyped computed properties | Left |

    Numeric values are centred rather than right-aligned. First-party packs centre column headers independently of these body-cell defaults.

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # ...
    column_alignments = {
        "status": "center",
        "priority_band": "center",
    }
```

Use `left`, `center`, or `right`. This changes body cells only. First-party packs centre headers independently, and other columns keep PowerCRUD's usual alignment.

### Column widths

Tables often mix short values, such as checkmarks, IDs, dates, and amounts, with names and descriptions. Turn on automatic column sizing to keep the short columns from taking more room than they need and leave more space for the text people read:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # ...
    column_width_policy = "semantic"
```

With `"semantic"`, PowerCRUD chooses one of three width modes from the field type:

- `"compact"` keeps automatic IDs and checkmarks as narrow as practical. Long header labels can wrap instead of making the column unnecessarily wide.
- `"auto"` sizes dates, times, and numbers around their values.
- `"bounded"` gives descriptive text, relations, computed properties, and other columns without a short-value rule a sensible maximum width.

Queryset annotations use their declared Django `output_field`, so Boolean, numeric, and temporal annotations receive the same automatic treatment as those model-field types. A computed Python property has no such type metadata; choose a width explicitly when its value is known to be short.

Normally, you can leave those choices to PowerCRUD. Override an individual column only when your application knows better. For example, a short asset code stored in a text field can use the compact treatment:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # ...
    column_width_policy = "semantic"
    column_width_modes = {
        "asset_code": "compact",
    }
```

You can use `"compact"`, `"auto"`, or `"bounded"` in `column_width_modes` whenever an individual column needs a different treatment. Without `column_width_policy = "semantic"`, PowerCRUD keeps its normal general-purpose table sizing.

Using `PowerField`? Put the same choice on the field declaration:

```python
PowerField("asset_code", column={"width": "compact"})
```

Column widths affect list layout only. They do not change values, sorting, filtering, or body-cell alignment. See the [configuration reference](../reference/config_options.md) and [PowerField reference](../reference/powerfields.md) for the complete option lists.

### How dates and times appear in lists {#temporal-list-value-formats}

Date, time, and datetime columns use Django's `DATE_FORMAT`, `TIME_FORMAT`, and `DATETIME_FORMAT` settings. `DateField` shows a date, `TimeField` shows a time, and `DateTimeField` shows a date by default.

Set these Django settings explicitly when PowerCRUD should use a particular regional display format:

```python
# settings.py
DATE_FORMAT = "d/m/Y"
TIME_FORMAT = "H:i"
DATETIME_FORMAT = "d/m/Y H:i"
```

If they are unset, Django uses its own defaults. Set `default_datetime_value_format` when most datetime columns on one screen should show a time or both date and time. Use `column_value_formats` for named `DateTimeField` or typed datetime-annotation overrides:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # ...
    default_datetime_value_format = "datetime"
    column_value_formats = {
        "updated_at": "time",
        "completed_at": "datetime",
    }
```

The available lower-case modes are `date`, `time`, and `datetime`. `DateField` accepts only `date`; `TimeField` accepts only `time`; and `DateTimeField` accepts all three. PowerCRUD validates model fields during setup and typed annotations before rendering. A property or annotation without a known temporal type raises `ImproperlyConfigured` rather than guessing.

---

## 6. Verify the page

Run the development server and open `/projects/` (or whatever path you configured). You should see:

- A table listing your model fields (and properties if configured).
- A filter sidebar if you enabled filters.
- Column headers that allow sorting.
- HTMX/Modal behaviour if you turned them on.

If something renders incorrectly, double-check:

- `base_template_path` is pointing at an actual template.
- `django_htmx` middleware is installed (for reactive behaviour).
- The view’s `fields` match real model fields or queryset annotations on the effective queryset.

---

## 7. Next steps

- Continue with [Forms](./forms.md) to learn how PowerCRUD builds forms, how `form_class` changes the rules, and how contextual display fields, disabled inputs, and dependent dropdowns fit together.
- Then move on to [Inline editing](./inline_editing.md) to reuse those form rules in HTMX row editing.
- After that, continue to [Bulk editing (synchronous)](./bulk_edit_sync.md) to enable multi-record edit/delete.
- Need more detail on individual settings? See the [Configuration reference](../reference/config_options.md).
