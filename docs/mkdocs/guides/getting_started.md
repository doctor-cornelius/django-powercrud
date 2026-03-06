# Getting Started

!!! tip "Ready after setup?"

    Once you have the basics installed, continue with [Setup & Core CRUD basics](./setup_core_crud.md) for the full walkthrough.

## Installation

### Install Python packages

```bash
pip install neapolitan
pip install django-powercrud
```

## Dependencies

### Backend dependencies

Install `django-powercrud` and `neapolitan` via `pip`, then add the required Django apps and middleware in your settings.

PowerCRUD installs these Python dependencies automatically:

- `django-htmx`
- `django-template-partials`
- `pydantic`

??? note "Backend library docs"

    - django-htmx: [https://django-htmx.readthedocs.io/](https://django-htmx.readthedocs.io/){ target="_blank" rel="noopener noreferrer" }
    - django-template-partials: [https://github.com/carltongibson/django-template-partials](https://github.com/carltongibson/django-template-partials){ target="_blank" rel="noopener noreferrer" }
    - pydantic: [https://docs.pydantic.dev/latest/](https://docs.pydantic.dev/latest/){ target="_blank" rel="noopener noreferrer" }

### Frontend dependencies

PowerCRUD ships a frontend bundle for its interactive behaviour and default styling.

The bundled frontend includes:

- **HTMX**
- **Tom Select** (searchable single-select enhancement)
- **Tippy.js** (truncated-table tooltips/popovers)
- **Compiled default CSS** for the built-in daisyUI/Tailwind templates

Recommended: load the PowerCRUD frontend bundle in your base template using whatever asset strategy your project already uses.

If you do **not** load the bundle, you must provide equivalent frontend assets yourself or interactive features will not work correctly.

??? note "Frontend library docs"

    - HTMX: [https://htmx.org/docs/](https://htmx.org/docs/){ target="_blank" rel="noopener noreferrer" }
    - Tom Select: [https://tom-select.js.org/](https://tom-select.js.org/){ target="_blank" rel="noopener noreferrer" }
    - Tippy.js: [https://atomiks.github.io/tippyjs/](https://atomiks.github.io/tippyjs/){ target="_blank" rel="noopener noreferrer" }
    - daisyUI: [https://daisyui.com/docs/](https://daisyui.com/docs/){ target="_blank" rel="noopener noreferrer" }
    - Tailwind CSS: [https://tailwindcss.com/docs](https://tailwindcss.com/docs){ target="_blank" rel="noopener noreferrer" }

Projects that use the built-in templates but manage assets themselves should read those docs. Projects that load the packaged bundle can usually ignore the frontend package-level setup details.

## Required Configuration

!!! warning "Minimum required wiring for PowerCRUD"

    PowerCRUD depends on these Django integrations:

    - Add to `INSTALLED_APPS`: `powercrud`, `neapolitan`, `django_htmx`, `template_partials`
    - Add to `MIDDLEWARE`: `django_htmx.middleware.HtmxMiddleware`
    - Load the PowerCRUD frontend bundle in your base template, or provide equivalent frontend assets yourself
    - `pydantic` is installed automatically and needs no extra Django setup

    If `django_htmx.middleware.HtmxMiddleware` is missing, HTMX requests will fail at runtime.

Add to your `settings.py`:

```python
# Required settings
INSTALLED_APPS = [
    ...
    "powercrud",
    "neapolitan",
    "django_htmx",
    "template_partials",
    ...
]

MIDDLEWARE = [
    ...,
    "django_htmx.middleware.HtmxMiddleware",
    ...,
]

# Optional: POWERCRUD_SETTINGS overrides (all keys are optional and have defaults)
POWERCRUD_SETTINGS = {
    "POWERCRUD_CSS_FRAMEWORK": "daisyui",  # built-in default
}
```

## Frontend Integration

Use the PowerCRUD frontend bundle as the default path. That keeps the setup small and ensures interactive features behave as documented.

If you prefer to manage frontend assets yourself, that is still valid, but you then own loading the equivalent libraries and keeping behaviour aligned.

For example, when using `django-vite` in manifest mode, point it at the packaged bundle like this:

```python
from importlib import resources


POWERCRUD_ASSETS_DIR = resources.files("powercrud").joinpath("assets")

DJANGO_VITE = {
    "default": {
        "manifest_path": f"{POWERCRUD_ASSETS_DIR}/manifest.json",
    }
}
```

Then load the bundle entry in your base template:

```django
{% load django_vite %}
{% vite_asset 'config/static/js/main.js' %}
```

See `sample/templates/sample/daisyUI/base.html` for a complete Vite-based example.

**Important:** If using Tailwind CSS (default), ensure Tailwind includes powercrud's classes in its build process. See the [Styling guide](./styling_tailwind.md#tailwind-integration) for details.

## Quick Start Tutorial

### Basic Setup

Start with a basic CRUD view. For reference see [`neapolitan`'s docs](https://noumenal.es/neapolitan/).

```python
from powercrud.mixins import PowerCRUDMixin
from neapolitan.views import CRUDView
from . import models

class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Project
    fields = ["name", "owner", "last_review", "status"]
    base_template_path = "core/base.html"
```

### Add to URLs

PowerCRUD’s `UrlMixin` (inherited from Neapolitan) exposes `get_urls()` so you do not have to hand-write the five CRUD routes. Pick the style that suits your project:

```python
from django.urls import path, include
from neapolitan.views import Role
from .views import ProjectCRUDView

app_name = "my_app"  # keep namespaces aligned with your include()

urlpatterns = []
urlpatterns += ProjectCRUDView.get_urls()
```

If you prefer the unpack pattern:

```python
urlpatterns = [
    *ProjectCRUDView.get_urls(),
]
```

Need fewer routes (and therefore fewer action buttons)? Limit the registered roles:

```python
urlpatterns = [
    *ProjectCRUDView.get_urls(roles={Role.LIST, Role.DETAIL}),
]
```

Only the List and View endpoints (and their buttons) will render in that case. Finally, include the app URLs at the project level as usual:

```python
# config/urls.py
from django.urls import include, path

urlpatterns = [
    path("projects/", include("my_app.urls")),
]
```

### Your First Enhanced View

Add some powercrud features:

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Project
    base_template_path = "core/base.html"
    
    # Basic field control
    fields = ["name", "owner", "status", "created_date"]
    properties = ["is_overdue"]  # Include @property fields
    
    # Enable modern features
    use_htmx = True
    use_modal = True
    
    # Add filtering
    filterset_fields = ["owner", "status", "created_date"]
    
    # Enable pagination
    paginate_by = 25
    
    # Optional: namespace for URLs
    namespace = "my_app"
```

That's it! You now have a fully-featured CRUD interface with filtering, pagination, modals, and HTMX support.

## Next Steps

- **[Core configuration](./setup_core_crud.md#3-shape-list-detail-and-form-scopes)** - Field control and basic settings
- **[HTMX & Modals](./setup_core_crud.md#modals)** - Interactive features
- **[Filtering](./setup_core_crud.md#filtering-sorting)** - Advanced search and filter options
- **[Bulk operations](./bulk_edit_sync.md)** - Edit multiple records at once
