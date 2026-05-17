# Setup & Core CRUD basics

Kick off your project by wiring PowerCRUD into an existing Django site, creating the first CRUD view, and enabling the core niceties (filtering, modals, pagination). Everything that follows in later chapters builds on this foundation.

---

## Prerequisites

- A working Django project on Django 5.2 or 6.0.
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
- If `fields` is an explicit list, entries may be model field names or supported queryset annotation names.
- Use `exclude` to remove a handful of items while keeping the rest of the list intact.
- `properties` is optional; adding a property name exposes it as a column. Use `"__all__"` to include every `@property` on the model and `properties_exclude` to hide specific ones.
- Queryset annotation fields are rendered in `fields` order and can filter/sort when the effective queryset exposes the same public annotation name. They are read-only and are not valid in form, inline-edit, or bulk-edit field lists.
- Use `list_options_enabled = True` to let users choose visible columns through **Cols** for the current session. If the table is too wide for the default view, add `default_list_fields` to show a smaller default subset. See [List Options](./advanced/list_options.md) for the full behavior and persistence rules.

**Detail view**

- The **View** button renders `detail_fields`, so this is the place to show extra context that you do not want in the table or edit forms.
- `detail_fields` inherits the resolved `fields` list via the `"__fields__"` sentinel (the default). Override with `"__all__"` or an explicit list when the detail page needs more context than the list.
- `detail_properties` defaults to an empty list, but you can reuse the list-view properties with `"__properties__"` or ask for all properties via `"__all__"`. You can also pass an explicit list such as `["is_overdue", "display_owner"]` (use the actual `@property` names, not model fields). Because detail pages are read-only, you can safely surface calculated properties that would never appear on a form.
- `detail_exclude` and `detail_properties_exclude` mirror the list exclusions so you can tweak the detail layout without rewriting the full list of items.

### Extra Buttons

Use `extra_buttons` for additional buttons above the table, alongside controls such as filter toggles and create buttons. These are page-level actions, not per-record actions.

Use `extra_buttons_mode = "dropdown"` when those page-level actions should move into a compact top toolbar overflow menu. The built-in Create button stays visible because it is not part of `extra_buttons`.

Typical uses:

- link to dashboards or reports
- open custom modals
- add list-level utilities that are not tied to a single row

Example:

```python
extra_buttons_mode = "dropdown"

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
        "modal_box_classes": "modal-box flex max-h-[calc(100dvh-2rem)] w-11/12 max-w-5xl flex-col",
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
    | `modal_box_classes` | `str` | Optional replacement classes for the shared modal box while this modal button is open. Use it for one-off width/height changes, and keep the default `flex max-h-[calc(100dvh-2rem)] flex-col` classes if you still want viewport-bounded scrolling. |
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
            "modal_box_classes": "modal-box flex max-h-[calc(100dvh-2rem)] w-11/12 max-w-5xl flex-col",
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
    | `modal_box_classes` | `str` | Optional replacement classes for the shared modal box while this modal action is open. Use it for one-off width/height changes, and keep the default `flex max-h-[calc(100dvh-2rem)] flex-col` classes if you still want viewport-bounded scrolling. |
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
- `filterset_fields` can include queryset annotation names when the queryset uses the same public `annotate(...)` name and the expression exposes an `output_field`.
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

Modal behaviour piggybacks on HTMX:

- Set `use_htmx = True` first.
- Set `use_modal = True` to load create, edit, delete, bulk, and modal-enabled custom actions into the shared dialog.
- By default, PowerCRUD renders `powercrudBaseModal` as the dialog and `powercrudModalContent` as the HTMX content target.
- The supplied modal is viewport-bounded by default: the modal box uses `max-h-[calc(100dvh-2rem)]`, and the modal content target scrolls with `overflow-y-auto`.
- When a modal form fails validation, PowerCRUD keeps the modal open and retargets the error response back into the modal content area.

Common modal settings:

| Setting | Use it for |
| --- | --- |
| `modal_id` | Match a custom dialog DOM id when you provide your own modal shell. Do not include `#`. |
| `modal_target` | Match the DOM id that receives HTMX modal content. Do not include `#`. |
| `modal_classes` | Change classes on the shared daisyUI `<dialog>` element. |
| `modal_box_classes` | Replace the default modal box classes for the whole view. Keep the default flex and `max-h-*` classes if you only want to add width. |
| `modal_body_classes` | Replace classes on the modal content target wrapper. Keep `min-h-0 flex-1 overflow-y-auto` if modal content should scroll inside the dialog. |
| `bulk_modal_box_classes` | Replace the modal box classes only while the built-in Bulk Edit modal is open. |

Example wider modal defaults:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # …
    use_htmx = True
    use_modal = True

    modal_box_classes = "modal-box flex max-h-[calc(100dvh-2rem)] w-11/12 max-w-4xl flex-col"
    bulk_modal_box_classes = "modal-box flex max-h-[calc(100dvh-2rem)] w-11/12 max-w-6xl flex-col"
```

Individual modal `extra_buttons` and `extra_actions` may also set `modal_box_classes` when one action needs different sizing:

```python
extra_actions = [
    {
        "url_name": "projects:timeline",
        "text": "Timeline",
        "display_modal": True,
        "modal_box_classes": "modal-box flex max-h-[calc(100dvh-2rem)] w-11/12 max-w-5xl flex-col",
    },
]
```

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

## 5. List presentation adjustments

These options adjust how the list surface reads and scans once the core CRUD page is already working: heading text, helper copy, tooltip affordances, and per-column body-cell alignment.

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

`view_help` renders a collapsed daisyUI disclosure below `view_instructions` and above the list toolbar. The `summary` is the one-line clickable bar, and `details` is escaped plain text. Separate paragraphs with blank lines. Add `"default_open": True` only when the guidance should start expanded.

By default, the help block uses the quiet `base` colour, aligns to the rendered table width, and will not shrink below `view_help_min_width = "40rem"` unless the surrounding container is narrower. Set `view_help_default_color` or `view_help_min_width` on the view to change those defaults. A specific `view_help` can override the colour with `"color": "info"` or a hex value such as `"#0ea5e9"`, and can override the width floor with `"min_width": "34rem"`. Semantic and hex colours are applied as subtle tints, with the summary bar slightly stronger than the content area.

Most views should use either `view_instructions` for a short always-visible sentence or `view_help` for longer optional guidance. Use both only when the short description and expandable detail carry distinct information.

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

`column_help_text` adds a separate info trigger next to only the configured header labels, so sorting still belongs to the header itself.

### List-cell tooltips

If you want semantic tooltips for selected rendered list cells, configure `list_cell_tooltip_fields` and override `get_list_cell_tooltip(...)`:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # …
    list_cell_tooltip_fields = ["owner", "display_status"]

    def get_list_cell_tooltip(self, obj, field_name, *, is_property, request=None):
        if field_name == "owner":
            return f"{obj.owner.email} ({obj.owner.team.name})"
        if field_name == "display_status":
            return obj.status_explanation
        return None
```

`list_cell_tooltip_fields` is opt-in. PowerCRUD only calls `get_list_cell_tooltip(...)` for rendered list fields or properties named in that list, and silently ignores configured names that are not actually visible in the table. Return plain text or `None`.

Hook-backed semantic list-cell tooltip text may include newline characters when a tooltip should display as multiple lines. That multiline rendering is limited to semantic list-cell tooltips returned by `get_list_cell_tooltip(...)`; header-help and other tooltip surfaces keep their existing behavior.

Tooltip behavior stays layered:

- `column_help_text` is header help only.
- `list_cell_tooltip_fields` plus `get_list_cell_tooltip(...)` provides semantic per-cell tooltip text for selected rendered columns.
- Unconfigured cells keep the built-in overflow tooltip behavior when their rendered content is truncated.

When a semantic list-cell tooltip is configured for a cell, it takes precedence over the overflow tooltip for that same cell. PowerCRUD continues to use the model verbose names for other copy such as `Create project` and empty-state text, and `view_instructions`, `view_help`, `column_help_text`, and semantic list-cell tooltip text are all escaped plain text rather than HTML.

### List-cell links

If a rendered list cell should navigate somewhere, configure `link_fields`.
The key is the rendered field or property name, and the value is either a
short Django `view_name` string or an explicit dict:

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
            "modal_box_classes": (
                "modal-box flex max-h-[calc(100dvh-2rem)] "
                "w-11/12 max-w-5xl flex-col"
            ),
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

Current allowed shapes:

- keys are rendered list field/property names
- string values are treated as Django `view_name` links
- dict values must include exactly one of `view_name` or `url`
- dict values may also include `pk_attr` for `view_name` links
- dict values may include `open_in`
- dict values may include `modal_box_classes` only for modal-opening links

`list_cell_link_default_open_in` is optional and sets the view-wide default for
list-cell links. It accepts `"current"`, `"new"`, or `"modal"`. If the view
omits it, PowerCRUD assumes `"new"`, so links open in a new browser context by
default. Use `"modal"` on CRUD list views where drill-in links should preserve
the current list context, or `"current"` when you want normal same-page anchor
navigation. Explicit per-link `open_in` always overrides the view default.

`pk_attr` names the attribute on the current row object that PowerCRUD should
use as the `pk` URL kwarg when reversing a `view_name`. When it is omitted,
PowerCRUD uses sensible defaults:

- relation fields such as `owner` use `<field_name>_id`
- non-relation fields and properties use the current row `pk`

That makes the common cases short:

- `{"owner": "crm:owner-detail"}` means “link the `owner` column to the related owner detail using `owner_id`”
- `{"reference_code": "projects:project-detail"}` means “link the `reference_code` column to this project row’s own detail using `pk`”

`open_in` controls how an individual link opens:

- omitted uses `list_cell_link_default_open_in`; if that view option is also omitted, PowerCRUD assumes `"new"`
- `"current"` opens as a normal same-page anchor
- `"new"` renders `target="_blank"` and defaults `rel="noopener noreferrer"`
- `"modal"` reuses the view’s existing PowerCRUD modal target and modal-open attributes

When `open_in = "modal"` is configured but the view is not running with HTMX
modal support, PowerCRUD gracefully falls back to a normal current-page anchor.

`modal_box_classes` on a modal list-cell link replaces the view-level modal box
classes only for that clicked cell. It uses the same per-trigger sizing behavior
as modal `extra_buttons` and `extra_actions`. Treat it as a full replacement
class string, so keep `flex max-h-[calc(100dvh-2rem)] flex-col` when you want
the default viewport-bounded scrolling plus a custom width.

If you need conditional logic or richer link metadata, override `get_list_cell_link(...)`:

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
                "modal_box_classes": (
                    "modal-box flex max-h-[calc(100dvh-2rem)] "
                    "w-11/12 max-w-5xl flex-col"
                ),
            }
        if field_name == "owner" and request and not request.user.has_perm("crm.view_owner"):
            return False
        return None
```

Hook behavior is deliberately simple:

- return a dict with at least `url` to link that cell
- include `open_in` when the cell should open somewhere other than the view-wide default
- include `modal_box_classes` only with `open_in = "modal"` for per-cell modal sizing
- return `None` to fall back to `link_fields`
- return `False` to suppress `link_fields` for that cell

Important behavior:

- inline-editable cells are never linked, because inline click-to-edit takes precedence
- if a field appears in both `link_fields` and `inline_edit_fields`, PowerCRUD logs a warning and silently skips the link at render time
- the hook applies to fields and properties, not only relations

### Column alignment

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
