# Setup & Core CRUD basics

Kick off your project by wiring PowerCRUD into an existing Django site, creating the first CRUD view, and enabling the core niceties (filtering, modals, pagination). Everything that follows in later chapters builds on this foundation.

---

## Prerequisites

- A working Django project (any recent 4.x/5.x release).
- Python 3.12+ (Docker images currently default to Python 3.14).
- Optional but recommended: virtual environment to isolate dependencies.

If you have not yet installed PowerCRUD and its base dependencies, complete the steps in [Getting Started](./getting_started.md) first.

---

## 1. Finish the basics

Before enabling the richer helpers, work through the [Getting Started](./getting_started.md) guide:

- [Install the dependencies](./getting_started.md#installation) and wire up the base template assets you plan to use.
- [Complete the required Django wiring](./getting_started.md#required-configuration), including `django_htmx.middleware.HtmxMiddleware`.
- [Declare your first view](./getting_started.md#basic-setup) and confirm the list/template renders without HTMX extras.
- [Expose the view somewhere in your project URLs](./getting_started.md#add-to-urls).

When you can load the plain CRUD view end-to-end, come back here to turn on the opinionated defaults.

---

## 2. Wire up URLs

If you followed [Getting Started](./getting_started.md#add-to-urls) you already have the fundamentals in place, but here is a slightly fuller example that mirrors the sample project. PowerCRUD inherits Neapolitan’s `get_urls()` helper, so you never have to hand-write the per-role paths.

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

Need to restrict the registered routes (and therefore the action buttons that appear)? Pass a subset of roles:

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

### Field and detail scopes

PowerCRUD layers a few convenient defaults so you can start with zero configuration and progressively override what appears in list and detail views.

**List fields**

- If `fields` is unset or set to `"__all__"`, every concrete model field is included.
- Use `exclude` to remove a handful of items while keeping the rest of the list intact.
- `properties` is optional; adding a property name exposes it as a column. Use `"__all__"` to include every `@property` on the model and `properties_exclude` to hide specific ones.

**Detail view**

- The **View** button renders `detail_fields`, so this is the place to show extra context that you do not want in the table or edit forms.
- `detail_fields` inherits the resolved `fields` list via the `"__fields__"` sentinel (the default). Override with `"__all__"` or an explicit list when the detail page needs more context than the list.
- `detail_properties` defaults to an empty list, but you can reuse the list-view properties with `"__properties__"` or ask for all properties via `"__all__"`. You can also pass an explicit list such as `["is_overdue", "display_owner"]` (use the actual `@property` names, not model fields). Because detail pages are read-only, you can safely surface calculated properties that would never appear on a form.
- `detail_exclude` and `detail_properties_exclude` mirror the list exclusions so you can tweak the detail layout without rewriting the full list of items.

### Extra Buttons

Use `extra_buttons` for additional buttons above the table, alongside controls such as filter toggles and create buttons. These are page-level actions, not per-record actions.

Typical uses:

- link to dashboards or reports
- open custom modals
- add list-level utilities that are not tied to a single row

Example:

```python
extra_buttons = [
    {
        "url_name": "home",
        "text": "Home",
        "button_class": "btn-success",
        "needs_pk": False,
        "display_modal": False,
        "htmx_target": "content",
    },
    {
        "url_name": "projects:selected-summary",
        "text": "Selected Summary",
        "button_class": "btn-primary",
        "needs_pk": False,
        "display_modal": True,
        "uses_selection": True,
        "selection_min_count": 1,
        "selection_min_behavior": "disable",
        "selection_min_reason": "Select at least one row first.",
    },
]
```

Selection-aware header buttons read the current persisted PowerCRUD bulk selection at the endpoint rather than expecting row IDs in the URL. Keep server-side validation in the endpoint even when you also disable the button in the UI.

??? info "Parameter Guide"

    | Parameter | Type | What it does |
    | --- | --- | --- |
    | `url_name` | `str` | Django URL name for the endpoint to call when the button is clicked. |
    | `text` | `str` | Visible button label shown above the table. |
    | `button_class` | `str` | CSS class applied to the button, such as `btn-primary` or `btn-success`. |
    | `needs_pk` | `bool` | Usually `False` for header buttons because they are page-level actions rather than row-level actions. |
    | `display_modal` | `bool` | If `True`, PowerCRUD opens the response in the standard modal target instead of treating it as a normal page/content navigation. |
    | `htmx_target` | `str` | HTMX target element to swap into when the button is clicked and it is not using the default modal target. |
    | `extra_attrs` | `str` | Raw HTML attributes appended to the button element when you need custom HTMX or data attributes. |
    | `extra_class_attrs` | `str` | Extra CSS classes appended to the button in addition to `button_class`. |
    | `uses_selection` | `bool` | When `True`, the endpoint should operate on the current persisted PowerCRUD bulk selection. |
    | `selection_min_count` | `int` | Minimum number of selected rows required before the button is considered ready. |
    | `selection_min_behavior` | `str` | `'allow'` leaves the button clickable below the minimum and lets the endpoint handle the error; `'disable'` greys it out in the UI. |
    | `selection_min_reason` | `str` | Tooltip/help text shown when a selection-aware button is disabled because too few rows are selected. |

### Extra Actions

Use `extra_actions` for additional per-row actions in the list table. These render in the row action area next to the built-in `View`, `Edit`, and `Delete` actions.

For row actions, `extra_actions_mode` controls whether the extra actions stay visible as buttons or move into an overflow menu:

- `extra_actions_mode = "buttons"` keeps the legacy behavior and renders extra row actions as visible joined buttons after `View/Edit/Delete`.
- `extra_actions_mode = "dropdown"` keeps `View/Edit/Delete` visible and moves only the configured `extra_actions` into a `More` dropdown.
- `extra_actions_dropdown_open_upward_bottom_rows = 3` makes the `More` dropdown open upward for the last three rendered rows on the current page. Set it to `0` to keep every row opening downward.

Example:

```python
class AuthorCRUDView(PowerCRUDMixin, CRUDView):
    # ...
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

    def is_view_again_disabled(self, obj, request):
        return obj.birth_date is None

    def get_view_again_disabled_reason(self, obj, request):
        if obj.birth_date is None:
            return "Birth date is required before viewing this record again."
        return None
```

`"buttons"` remains the default for backward compatibility, so existing projects only change if they opt in.

??? info "Parameter Guide"

    | Parameter | Type | What it does |
    | --- | --- | --- |
    | `url_name` | `str` | Django URL name for the per-row endpoint that the action should call. |
    | `text` | `str` | Visible label for the row action button or dropdown entry. |
    | `needs_pk` | `bool` | Usually `True` for row actions so PowerCRUD includes the current row primary key in the URL. |
    | `button_class` | `str` | CSS class used when the action is rendered as a visible button. |
    | `display_modal` | `bool` | If `True`, the response opens in the standard modal instead of replacing page content. |
    | `htmx_target` | `str` | HTMX target element used for non-modal actions when you need a custom swap target. |
    | `hx_post` | `bool` | If `True`, renders the action as an HTMX POST instead of the default GET. |
    | `lock_sensitive` | `bool` | Reuses PowerCRUD's existing blocked-row/lock logic so the action disables automatically when the row is not currently actionable. |
    | `disabled_if` | `str` | Name of a view method with signature `(obj, request) -> bool` that decides whether this row action should be disabled. |
    | `disabled_reason` | `str` | Name of a view method with signature `(obj, request) -> str | None` that returns the tooltip/help text when the action is disabled. |

!!! note

    When `extra_actions_mode = "dropdown"`:

    - per-action `button_class` values are no longer used for the dropdown menu entries themselves
    - the `More` trigger uses the framework’s `extra_default` styling instead
    - leaving `button_class` off an `extra_actions` item is therefore fine if that action only ever appears in dropdown mode

_Need the full list of knobs? See the [configuration reference](../reference/config_options.md) for every attribute, default, and dependency._

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

This is the quick-start version of filtering. The full filtering story now lives in the dedicated [Filtering](filtering.md) guide.

What happens at a high level:

- With no `filterset_fields`, the list renders immediately and ignores filter-style query parameters apart from `page`, `page_size`, and `sort`.
- Setting `filterset_fields` builds an automatic `django-filter` filterset for those fields.
- Leaving `default_filterset_fields` unset shows every allowed filter immediately.
- Setting `default_filterset_fields` to a subset keeps the rest available through the built-in `Add filter` control.
- Sorting stays wired into the table headers, so users can still share URLs such as `/projects/?sort=status`.

If a sortable relation column should use something other than the normal default, configure `column_sort_fields_override`:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # …
    column_sort_fields_override = {
        "owner": "owner__email",
        "customer": "customer__code",
    }
```

`column_sort_fields_override` is an override map, not an exhaustive declaration. If a sortable list field is not present, PowerCRUD falls back to the normal default for that field.

For the full filtering feature set, including:

- default vs optional filters
- null helpers
- `filterset_class` precedence
- M2M AND logic
- filter-side `dropdown_sort_options` and `filter_queryset_options`
- HTMX visibility persistence

see [Filtering](filtering.md).

Saved filter favourites are documented separately because they are an optional contrib add-on rather than part of the core filtering contract. See [Saved Filter Favourites](advanced/filter_favourites.md).

### Modals

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # …
    use_htmx = True
    use_modal = True
```

Modal behaviour piggybacks on HTMX. Set `use_htmx = True` first, then `use_modal = True` to have create/edit/delete views load into the default dialog (`powercrudBaseModal` / `powercrudModalContent`). If your base template already defines modal markup, override `modal_id` / `modal_target` to match your DOM IDs. When forms fail validation, the mixin keeps the modal open and injects an HX-Trigger so the dialog re-renders with error feedback.

### Pagination

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # …
    paginate_by = 25
```

The view renders every record when `paginate_by` is left unset (`None`). Supplying a number enables server-side pagination and exposes built-in tooling:

- Users can override the page size at runtime with `?page_size=10` (or `?page_size=all` to disable pagination temporarily). A standard list of sizes (5/10/25/50/100 plus your default) powers the UI selector.
- When filters change, the mixin automatically snaps back to page 1 so users do not land on empty pages.
- Pagination works with or without HTMX. With HTMX enabled, only the table/pager fragment updates on navigation.

### Record count display

If you want the list view to show a lightweight results summary above the table, enable `show_record_count`:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # …
    show_record_count = True
```

When enabled, PowerCRUD renders a small metadata line above the table inside the same HTMX-updated results region as the table and pagination controls. That means the count stays in sync with filtering, sorting, page-size changes, and page navigation automatically.

Examples:

- No active filters: `123 total records`
- Active filters without pagination: `27 matching records`
- Active filters with pagination: `Showing 1-15 of 27 matching records`

This is useful when users need quick confirmation that a filter narrowed the queryset as expected, without adding extra noise to the main button toolbar.

When synchronous bulk editing is enabled, the same metadata line can also host contextual selection actions such as `Select all N matching records` or `Add 998 more from 1030 matching records`. Leave `show_bulk_selection_meta = True` (the default) to keep that action available even when `show_record_count` is off, or disable it separately if you do not want selection prompts in that row.

### List heading, helper text, and tooltips

If you want the visible list heading to differ from the model’s `verbose_name_plural`, set `view_title` on the CRUD view. You can also add plain-text helper copy directly below it with `view_instructions`, optional plain-text help tooltips to specific headers with `column_help_text`, and optional semantic tooltips for selected rendered cells with `list_cell_tooltip_fields` plus `get_list_cell_tooltip(...)`:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # …
    view_title = "Active Client Projects"
    view_instructions = "Use the table below to review and update active projects."
    column_help_text = {
        "owner": "The client or business owner responsible for the project.",
        "display_status": "Calculated status shown for quick triage.",
    }
    list_cell_tooltip_fields = ["owner", "display_status"]

    def get_list_cell_tooltip(self, obj, field_name, *, is_property, request=None):
        if field_name == "owner":
            return f"{obj.owner.email} ({obj.owner.team.name})"
        if field_name == "display_status":
            return obj.status_explanation
        return None
```

`view_title` changes only the large heading above the list table. `view_instructions` adds a small escaped text block directly underneath that heading. `column_help_text` adds a separate info trigger next to only the configured header labels, so sorting still belongs to the header itself.

`list_cell_tooltip_fields` is opt-in. PowerCRUD only calls `get_list_cell_tooltip(...)` for rendered list fields or properties named in that list, and silently ignores configured names that are not actually visible in the table. Return plain text or `None`.

If a short categorical column would scan better centered than the default heuristic allows, use `column_alignments` to override just the list body cells for that column:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # ...
    column_alignments = {
        "status": "center",
        "priority_band": "center",
    }
```

Accepted values are `left`, `center`, and `right`. This is a semantic presentation override for rendered list body cells only; table headers keep their normal alignment, and any column not listed here continues to use PowerCRUD's built-in alignment heuristic.

Hook-backed semantic list-cell tooltip text may include newline characters when a tooltip should display as multiple lines. That multiline rendering is limited to semantic list-cell tooltips returned by `get_list_cell_tooltip(...)`; header-help and other tooltip surfaces keep their existing behavior.

Tooltip behavior stays layered:

- `column_help_text` is header help only.
- `list_cell_tooltip_fields` plus `get_list_cell_tooltip(...)` provides semantic per-cell tooltip text for selected rendered columns.
- Unconfigured cells keep the built-in overflow tooltip behavior when their rendered content is truncated.

When a semantic list-cell tooltip is configured for a cell, it takes precedence over the overflow tooltip for that same cell. PowerCRUD continues to use the model verbose names for other copy such as `Create project` and empty-state text, and `view_instructions`, `column_help_text`, and semantic list-cell tooltip text are all escaped plain text rather than HTML.

---

## 5. Verify the page

Run the development server and open `/projects/` (or whatever path you configured). You should see:

- A table listing your model fields (and properties if configured).
- A filter sidebar if you enabled filters.
- Column headers that allow sorting.
- HTMX/Modal behaviour if you turned them on.

If something renders incorrectly, double-check:

- `base_template_path` is pointing at an actual template.
- `django_htmx` middleware is installed (for reactive behaviour).
- The view’s `fields` match real model fields.

---

## Next steps

- Continue with [Forms](./forms.md) to learn how PowerCRUD builds forms, how `form_class` changes the rules, and how contextual display fields, disabled inputs, and dependent dropdowns fit together.
- Then move on to [Inline editing](./inline_editing.md) to reuse those form rules in HTMX row editing.
- After that, continue to [Bulk editing (synchronous)](./bulk_edit_sync.md) to enable multi-record edit/delete.
- Need more detail on individual settings? See the [Configuration reference](../reference/config_options.md).
