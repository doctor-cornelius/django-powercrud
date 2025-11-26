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
- [Add the PowerCRUD apps/settings](./getting_started.md#settings-configuration), including `django_htmx`.
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

## 3. Shape list, detail, and form scopes

### Field, detail, and form scopes

PowerCRUD layers a few convenient defaults so you can start with zero configuration and progressively override what appears in list, detail, and form views.

**List fields**

- If `fields` is unset or set to `"__all__"`, every concrete model field is included.
- Use `exclude` to remove a handful of items while keeping the rest of the list intact.
- `properties` is optional; adding a property name exposes it as a column. Use `"__all__"` to include every `@property` on the model and `properties_exclude` to hide specific ones.

**Detail view**

- The **View** button renders `detail_fields`, so this is the place to show extra context that you do not want in the table or edit forms.
- `detail_fields` inherits the resolved `fields` list via the `"__fields__"` sentinel (the default). Override with `"__all__"` or an explicit list when the detail page needs more context than the list.
- `detail_properties` defaults to an empty list, but you can reuse the list-view properties with `"__properties__"` or ask for all properties via `"__all__"`. You can also pass an explicit list such as `["is_overdue", "display_owner"]` (use the actual `@property` names, not model fields). Because detail pages are read-only, you can safely surface calculated properties that would never appear on a form.
- `detail_exclude` and `detail_properties_exclude` mirror the list exclusions so you can tweak the detail layout without rewriting the full list of items.

**Forms & inline editing**

- When no `form_fields` are specified, the mixin selects every *editable* field from `detail_fields`. Set `form_fields = "__fields__"` to mirror the list exactly, or `form_fields = "__all__"` to include every editable field.
- `form_fields_exclude` lets you remove sensitive or read-only fields while keeping the automatic selection logic.
- Inline editing (enabled via `inline_edit_enabled = True` + HTMX) reuses the resolved `form_fields`. Override `inline_edit_fields` with `"__fields__"`, `"__all__"`, or an explicit list if you want inline editing to expose a different subset, and PowerCRUD will automatically ignore anything that is not part of the form.

### Buttons & extra actions

`extra_buttons` and `extra_actions` dictionaries describe additional top-level buttons or per-row actions (URL name, label, modal behaviour, extra attributes). See [Customisation tips](./customisation_tips.md) for full examples.

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
```

What happens by default:

- With *no* `filterset_fields`, the view renders the list immediately and ignores any query parameters except `page`, `page_size`, and `sort`.
- Setting `filterset_fields` automatically builds a `django-filter` `FilterSet` for those fields, including sensible widgets based on field type and optional HTMX attributes if `use_htmx` is True.

Dial it up when you need more control:

- Pass a custom `filterset_class` for hand-crafted filters (PowerCRUD still wires in HTMX helpers).
- Use `filter_queryset_options` or `dropdown_sort_options` to scope/queryset-sort the choices in generated dropdowns.
- Toggle `m2m_filter_and_logic = True` if many-to-many filters must match *all* selected values instead of the default OR behaviour.
- Sorting is wired into the table headers. Clicking a column toggles `?sort=field` / `?sort=-field` on the URL (so you can share `/projects/?sort=status`). PowerCRUD applies that ordering server-side and always adds a secondary `pk` sort so pagination stays stable. Properties can be sorted too, as long as the property name is listed in `properties`.

HTMX is optional but recommended: when enabled, filter submissions post back to the list endpoint and the results replace the table without a full reload. Pagination automatically resets to page 1 after each filter submit.

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

- Move on to [Bulk editing (synchronous)](./bulk_edit_sync.md) to enable multi-record edit/delete.
- Need more detail on individual settings? See the [Configuration reference](../reference/config_options.md).
