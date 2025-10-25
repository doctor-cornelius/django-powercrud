# 01. Setup & Core CRUD basics

Kick off your project by wiring PowerCRUD into an existing Django site, creating the first CRUD view, and enabling the core niceties (filtering, modals, pagination). Everything that follows in later chapters builds on this foundation.

---

## Prerequisites

- A working Django project (any recent 4.x/5.x release).
- Python 3.12+ (PowerCRUD is tested there).
- Optional but recommended: virtual environment to isolate dependencies.

If you have not yet installed PowerCRUD and its base dependencies, complete the steps in [Getting Started](../getting_started.md) first.

---

## 1. Install packages

```bash
pip install django-powercrud neapolitan django-htmx crispy-tailwind
```

PowerCRUD pulls in a few helpers automatically:

- `django-template-partials`
- `pydantic`
- `django-htmx`

For styling we assume the default daisyUI/Tailwind stack; you can switch later (see [this section](./06_styling_tailwind.md)).

---

## 2. Update `settings.py`

Add the required apps (order is flexible but keep it readable):

```python
INSTALLED_APPS = [
    # Django core…
    "django.contrib.admin",
    "django.contrib.auth",
    # …

    # Third-party
    "django_htmx",
    "crispy_forms",
    "crispy_tailwind",

    # PowerCRUD stack
    "powercrud",
    "neapolitan", # neapolitan must be listed after powercrud
]
```

### Global PowerCRUD settings

Add (or extend) the `POWERCRUD_SETTINGS` dict:

```python
POWERCRUD_SETTINGS = {
    "POWERCRUD_CSS_FRAMEWORK": "daisyui",  # default styling
    # Optional: configure Tailwind safelist output later
}
```

If you plan to use async later, you’ll add more keys in [Section 03](./03_async_manager.md) but nothing else is required now.

### HTMX middleware

PowerCRUD relies on HTMX for reactive updates, so ensure the middleware is present:

```python
MIDDLEWARE = [
    # …
    "django_htmx.middleware.HtmxMiddleware",
]
```

---

## 3. Create a model (if you do not already have one)

```python
# myapp/models.py
from django.db import models

class Project(models.Model):
    name = models.CharField(max_length=200)
    owner = models.CharField(max_length=200)
    status = models.CharField(max_length=50, choices=[("active", "Active"), ("archived", "Archived")])
    created_date = models.DateField(auto_now_add=True)

    @property
    def is_overdue(self):
        return self.status != "archived"

    def __str__(self):
        return self.name
```

Run migrations if this is a brand new model.

---

## 4. Define your first PowerCRUD view

```python
# myapp/views.py
from neapolitan.views import CRUDView
from powercrud.mixins import PowerCRUDMixin

from . import models


class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Project
    base_template_path = "myapp/base.html"  # point at your real base template
    # use_htmx = True  # uncomment for reactive updates; leave out for classic page loads
```

### Template notes

- `base_template_path` should reference the base template that provides your site chrome. PowerCRUD extends `<base_template_path>.html` and expects that template to:
  - load the HTMX script (and any other front-end assets you rely on),
  - include the modal markup/powercrud partials (see the example in `powercrud/base.html`),
  - provide the standard `{% block content %}` that PowerCRUD will populate.
- If you want to override PowerCRUD’s templates later, set `templates_path` or copy them with `pcrud_mktemplate` (covered in Section 07).

---

## 5. Wire up URLs

```python
# myapp/urls.py
from django.urls import path

from .views import ProjectCRUDView

app_name = "projects"  # matches view.namespace if you set one

urlpatterns = [
    path("projects/", ProjectCRUDView.as_view(), name="project"),
]
```

Include the app URLs from your project-level `urls.py` as usual.

---

## 6. Enable UI helpers

Once the basic view works, turn on the built-in enhancements.

### Filtering & sorting {#filtering-sorting}

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # …
    use_htmx = True                      # enables reactive updates
    filterset_fields = ["owner", "status", "created_date"]
```

HTMX makes filters, pagination, and table sorting update without a full page reload.

### Modals

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # …
    use_modal = True
```

Create/edit/delete forms now open in a modal overlay. You can customise modal IDs/targets later if your base template uses different names.

### Pagination

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    # …
    paginate_by = 25
```

Pagination works with or without HTMX; when HTMX is enabled it loads pages into place without a refresh.

---

## 7. Common adjustments

| Task | Setting(s) | Notes |
|------|------------|-------|
| Hide internal fields | `exclude = ["internal_notes"]` | Works alongside `fields`. |
| Show computed values | `properties = ["is_overdue"]` | Use `property.fget.short_description` to rename columns. |
| Custom detail view | `detail_fields`, `detail_properties` | Accept `__all__`, `__fields__`, `__properties__`, or explicit lists. Defaults mirror list settings. |
| Custom URL prefix | `url_base = "active-projects"` | Useful if multiple CRUD views share a model. |
| Additional actions | `extra_buttons`, `extra_actions` | Add top-level or per-row buttons; see [Section 07](./07_customisation_tips.md). |

### Field & property options

- `fields` → defaults to `"__all__"`. Set to a list of field names or use `exclude` to hide specific ones.
- `exclude` → list of field names to remove while keeping the rest.
- `properties` → defaults to `None`. Supply a list of property names or `"__all__"`; use `properties_exclude` to hide specific properties.
- `detail_fields` → defaults to `"__fields__"` (same as `fields`). Accepts `"__all__"`, `"__fields__"`, or an explicit list.
- `detail_exclude` → remove fields from the detail view while leaving the rest intact.
- `detail_properties` → defaults to `[]`. Use `"__properties__"`, `"__all__"`, or a list of property names.
- `detail_properties_exclude` → remove selected properties from the detail view.

### Buttons & extra actions

`extra_buttons` and `extra_actions` dictionaries describe additional top-level buttons or per-row actions (URL name, label, modal behaviour, extra attributes). See [Section 07](./07_customisation_tips.md) for full examples.

### Key options

| Setting | Default | Typical values | Purpose |
|---------|---------|----------------|---------|
| `base_template_path` | framework base | Template path | Which base template PowerCRUD extends. |
| `fields` | `"__all__"` | list / `"__all__"` | Columns shown in the list view. |
| `exclude` | `[]` | list | Remove specific fields while keeping others. |
| `properties` | `None` | list / `"__all__"` | Computed properties to display. |
| `properties_exclude` | `[]` | list | Hide selected properties. |
| `detail_fields` | `"__fields__"` | list / `"__all__"` | Fields shown in the detail view. |
| `detail_exclude` | `[]` | list | Remove fields from the detail view. |
| `detail_properties` | `[]` | list / `"__properties__"` | Properties shown in the detail view. |
| `detail_properties_exclude` | `[]` | list | Remove properties from the detail view. |
| `use_htmx` | `None` | bool | Enable HTMX for reactive updates. |
| `use_modal` | `None` | bool | Open CRUD actions inside modals. |
| `paginate_by` | `None` | int | Page size; enables pagination when set. |
| `default_htmx_target` | `"#content"` | CSS selector | Target element for HTMX responses. |
| `modal_id` / `modal_target` | defaults | strings | Align PowerCRUD with custom modal markup. |
| `namespace`, `url_base` | `None`, model name | strings | Control generated URLs. |
| `templates_path` | framework path | string | Override PowerCRUD templates. |
| `hx_trigger` | `None` | string/dict | Emit custom HTMX events after responses. |

_See the [configuration reference](../reference/config_options.md) for full definitions and additional settings._

---

## 8. Verify the page

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

- Move on to [02 Bulk editing (synchronous)](02_bulk_edit_sync.md) to enable multi-record edit/delete.
- Need more detail on individual settings? See the [Configuration reference](../reference/config_options.md).
