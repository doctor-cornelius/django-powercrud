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

PowerCRUD ships package-owned frontend runtime assets and a packaged bundle.

Runtime responsibilities include:

- **HTMX**
- **Tom Select** (searchable single/multi select enhancement)
- **Tippy.js** (truncated-table tooltips/popovers)
- **PowerCRUD runtime JS/CSS** (`powercrud/js/powercrud.js`, `powercrud/css/powercrud.css`)

You can run PowerCRUD in either of these modes:

- **Bundled mode (recommended):** load PowerCRUD's packaged Vite entry (`config/static/js/main.js`).
- **Manual mode:** install frontend dependencies yourself, then load PowerCRUD runtime assets from Django static paths.

??? note "Frontend library docs"

    - HTMX: [https://htmx.org/docs/](https://htmx.org/docs/){ target="_blank" rel="noopener noreferrer" }
    - Tom Select: [https://tom-select.js.org/](https://tom-select.js.org/){ target="_blank" rel="noopener noreferrer" }
    - Tippy.js: [https://atomiks.github.io/tippyjs/](https://atomiks.github.io/tippyjs/){ target="_blank" rel="noopener noreferrer" }
    - daisyUI: [https://daisyui.com/docs/](https://daisyui.com/docs/){ target="_blank" rel="noopener noreferrer" }
    - Tailwind CSS: [https://tailwindcss.com/docs](https://tailwindcss.com/docs){ target="_blank" rel="noopener noreferrer" }

Projects that use the built-in templates but manage assets manually should read those docs. Projects that load the packaged bundle can usually ignore package-level frontend dependency wiring.

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

You can install PowerCRUD in two ways.

=== "Option A (recommended): bundled mode"

    Use the packaged bundle to keep setup small and behaviour aligned with docs.

    When using `django-vite`, configure a dedicated app entry for PowerCRUD:

    ```python
    # settings.py
    from importlib import resources


    POWERCRUD_ASSETS_DIR = resources.files("powercrud").joinpath("assets")
    STATIC_URL = "/static/"
    STATICFILES_DIRS = [
        # your existing static dirs...
        str(POWERCRUD_ASSETS_DIR),
    ]

    DJANGO_VITE = {
        "default": {
            # Your project's own frontend bundle config
        },
        "powercrud": {
            "dev_mode": False,
            "static_url_prefix": "/static/",
            "manifest_path": str(POWERCRUD_ASSETS_DIR / "manifest.json"),
        },
    }
    ```

    Then load the bundle entry in your base template:

    ```django
    {% load django_vite %}
    {% vite_asset 'config/static/js/main.js' app='powercrud' %}
    ```

    See `sample/templates/sample/daisyUI/base.html` for a complete Vite-based example.

    If your page also loads your app's own bundle, both lines can coexist:

    ```django
    {% vite_asset 'src/config/static/js/main.js' %}
    {% vite_asset 'config/static/js/main.js' app='powercrud' %}
    ```

    Bundle mode checks:

    - Generated PowerCRUD asset URLs should be absolute, for example `/static/django_assets/...`.
    - Ensure global `STATIC_URL` is absolute, for example `"/static/"`.
    - If URLs appear relative (for example `static/django_assets/...` resolving to `/your/page/path/static/...`), set `static_url_prefix` to `"/static/"`.
    - Ensure `POWERCRUD_ASSETS_DIR` is registered in `STATICFILES_DIRS` so static lookup can find `django_assets/powercrud-*.js|css`.

    Projects that do not use `django.contrib.staticfiles` are especially sensitive here: `static_url_prefix` and `STATICFILES_DIRS` become mandatory for reliable packaged-bundle resolution.

=== "Option B: manual mode (no packaged bundle)"

    If you manage frontend dependencies yourself, you must:

    1. Load vendor dependencies (`HTMX`, `Tom Select`, `Tippy.js`).
    2. Expose them as browser globals.
    3. Load PowerCRUD runtime assets.

    Template example:

    ```django
    {% load static %}

    <link rel="stylesheet" href="{% static 'powercrud/css/powercrud.css' %}">

    <script src=".../htmx.min.js"></script>
    <link rel="stylesheet" href=".../tom-select.default.min.css">
    <script src=".../tom-select.complete.min.js"></script>
    <script src=".../tippy-bundle.umd.min.js"></script>
    <script src="{% static 'powercrud/js/powercrud.js' %}"></script>
    ```

    If your project uses a JS bundler (for example Vite/Webpack) for vendor packages, expose globals in your app entry:

    ```javascript
    import htmx from "htmx.org";
    import TomSelect from "tom-select";
    import removeButtonPlugin from "tom-select/dist/js/plugins/remove_button.js";
    import "tom-select/dist/css/tom-select.css";
    import tippy from "tippy.js";
    import "tippy.js/dist/tippy.css";

    window.htmx = htmx;
    TomSelect.define("remove_button", removeButtonPlugin);
    window.TomSelect = TomSelect;
    window.tippy = tippy;
    ```

    Then load PowerCRUD runtime assets in your base template:

    ```django
    {% load static %}
    <link rel="stylesheet" href="{% static 'powercrud/css/powercrud.css' %}">
    <script defer src="{% static 'powercrud/js/powercrud.js' %}"></script>
    ```

    Manual mode requirements:

    - Load vendor dependencies before `powercrud/js/powercrud.js`.
    - Load Tom Select's vendor CSS before `powercrud/css/powercrud.css` so the package can override Tom Select with daisyUI semantic colors.
    - Register the Tom Select `remove_button` plugin if you want multi-select remove buttons.
    - If you use built-in daisyUI templates without the packaged bundle, you must provide your own daisyUI/Tailwind CSS stack.

    Do not load both integration modes on the same page:

    - Use either the packaged bundle (`{% vite_asset 'config/static/js/main.js' app='powercrud' %}`), or:
    - Manual vendor/runtime assets.

    Quick browser verification for manual mode:

    ```javascript
    Boolean(window.initPowercrudSearchableSelects) // true
    Boolean(window.TomSelect)                      // true
    Boolean(window.htmx)                           // true
    ```

    If fields have `data-powercrud-searchable-select="true"` but no Tom Select UI appears, the runtime script is not loaded or `window.TomSelect` is missing.

    **Important:** If you compile Tailwind yourself, ensure Tailwind includes PowerCRUD classes in its build process. See the [Styling guide](./styling_tailwind.md#tailwind-integration) for details.

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
