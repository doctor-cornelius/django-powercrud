# Getting Started

!!! tip "Ready after setup?"

    Once you have the basics installed, continue with [Setup & Core CRUD basics](./setup_core_crud.md) for the full walkthrough.

## Installation

### Install Core Dependencies

```bash
pip install neapolitan
pip install django-powercrud
```

This automatically installs:

- `django-htmx`
- `django-template-partials`
- `pydantic`

### install Frontend Dependencies

You'll need to include these JavaScript libraries in your base template:

- **HTMX** - [Install from htmx.org](https://htmx.org/docs/#installing)
- **Popper.js** - For table column text truncation popovers

**Default styling:**

- daisyUI v5 with Tailwind CSS v4
- Bootstrap Icons (for sorting indicators)

!!! note "Choose Your Frontend Install Methods"

    There are many ways to include JavaScript (CDN, npm, Vite, etc.) - use whatever works for your project.*
    See the example base template in `sample/templates/sample/daisyUI/base.html` for a complete implementation with CDN links.

## Settings Configuration

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

# Optional: Set CSS framework (default is 'daisyui'); override if you build your own pack
POWERCRUD_CSS_FRAMEWORK = 'daisyui'
```

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
