# Getting Started

Use this page to add PowerCRUD to an existing Django project and render your first useful list screen. Follow the numbered sections in order. You do not need saved favourites, manual asset loading, Tailwind configuration, or async work to get that first screen running.

???+ tip "Your first pass through this guide"

    1. Install the Python packages.
    2. Add the required Django apps and middleware.
    3. Load the packaged frontend bundle, unless you already know you need the manual asset route.
    4. Declare the view and add its URLs.

After that, continue with [Setup & Core CRUD basics](./setup_core_crud.md) to shape the screen. Read [PowerCRUD Concepts](./concepts.md) once the main features are familiar and you want a map of the terminology.

## 1. Install PowerCRUD {#installation}

### Install Python packages

```bash
pip install neapolitan
pip install django-powercrud
```

??? info "Optional saved favourites"

    If you want saved favourites, also add the optional contrib app to `INSTALLED_APPS`, run migrations, and mount `powercrud.urls` with namespace `powercrud`. The detailed behavior and UI guidance live in [Saved Favourites](./advanced/filter_favourites.md).

## 2. Configure Django {#required-configuration}

!!! warning "Minimum required wiring for PowerCRUD"

    PowerCRUD depends on these Django integrations:

    - Add to `INSTALLED_APPS`: `powercrud`, `neapolitan`, `django_htmx`
    - On Django 5.2 only, also add `template_partials`
    - Add to `MIDDLEWARE`: `django_htmx.middleware.HtmxMiddleware`
    - Load the PowerCRUD frontend bundle in your base template, or provide equivalent frontend assets yourself
    - `pydantic` is installed automatically and needs no extra Django setup

    If `django_htmx.middleware.HtmxMiddleware` is missing, HTMX requests will fail at runtime.

Add to your `settings.py`:

```python
# Required settings
import django


POWERCRUD_COMPAT_APPS = []
if django.VERSION < (6, 0):
    POWERCRUD_COMPAT_APPS.append("template_partials")

INSTALLED_APPS = [
    ...
    "powercrud",
    "neapolitan",
    "django_htmx",
    *POWERCRUD_COMPAT_APPS,
    ...
]

MIDDLEWARE = [
    ...,
    "django_htmx.middleware.HtmxMiddleware",
    ...,
]

# Optional: POWERCRUD_SETTINGS overrides (all keys are optional and have defaults)
POWERCRUD_SETTINGS = {
    # Add only the settings your project needs.
}
```

If your own templates define partials and need to support both Django 5.2 and 6.1, load PowerCRUD's compatibility tag library:

```django
{% load powercrud_partials %}
{% partialdef toolbar %}
    ...
{% endpartialdef toolbar %}
{% partial toolbar %}
```

Django 6.1 includes template partials in core, so do not add `template_partials` to `INSTALLED_APPS` on Django 6 projects.

If you want the optional saved favourites feature:

```python
INSTALLED_APPS = [
    ...,
    "powercrud.contrib.favourites",
]
```

```bash
python manage.py migrate
```

```python
urlpatterns = [
    # ...
    path("powercrud/", include("powercrud.urls", namespace="powercrud")),
]
```

The URL prefix can be different, but the namespace must stay `powercrud`.

If you do not install that contrib app and mount its shared URLs, filtering still works normally and the favourites UI simply remains unavailable.

??? info "What PowerCRUD depends on"

    PowerCRUD installs `django-htmx`, `django-template-partials` (for Django 5.2 compatibility), and `pydantic` as Python dependencies. You do not configure `pydantic` in Django.

    PowerCRUD ships package-owned frontend runtime assets and a packaged bundle. The frontend runtime includes:

    - **HTMX**
    - **Tom Select** (searchable single/multi-select enhancement)
    - **Tippy.js** (truncated-table tooltips/popovers)
    - **PowerCRUD runtime JS/CSS** (`powercrud/js/powercrud.js`, `powercrud/css/powercrud.css`)

    The packaged bundle supplies those assets. You only need to manage them yourself when you choose the manual asset route below. Projects that use the built-in templates but manage assets manually should read the linked frontend library documentation; projects that load the packaged bundle can usually ignore package-level frontend dependency wiring.

    - django-htmx: [https://django-htmx.readthedocs.io/](https://django-htmx.readthedocs.io/){ target="_blank" rel="noopener noreferrer" }
    - django-template-partials: [https://github.com/carltongibson/django-template-partials](https://github.com/carltongibson/django-template-partials){ target="_blank" rel="noopener noreferrer" }
    - pydantic: [https://docs.pydantic.dev/latest/](https://docs.pydantic.dev/latest/){ target="_blank" rel="noopener noreferrer" }
    - HTMX: [https://htmx.org/docs/](https://htmx.org/docs/){ target="_blank" rel="noopener noreferrer" }
    - Tom Select: [https://tom-select.js.org/](https://tom-select.js.org/){ target="_blank" rel="noopener noreferrer" }
    - Tippy.js: [https://atomiks.github.io/tippy/](https://atomiks.github.io/tippy/){ target="_blank" rel="noopener noreferrer" }
    - DaisyUI: [https://daisyui.com/docs/](https://daisyui.com/docs/){ target="_blank" rel="noopener noreferrer" }
    - Tailwind CSS: [https://tailwindcss.com/docs](https://tailwindcss.com/docs){ target="_blank" rel="noopener noreferrer" }

## 3. Load frontend assets {#frontend-integration}

Use the packaged bundle unless your project already owns the frontend dependency pipeline. The two tabs are mutually exclusive loading routes; do not use both on one page.

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
    <script type="module" src="{% static 'powercrud/js/powercrud.js' %}"></script>
    ```

    If your project uses a JS bundler (for example Vite/Webpack) for vendor packages, expose globals in your app entry:

    ```javascript
    import htmx from "htmx.org";
    import TomSelect from "tom-select";
    import "tom-select/dist/css/tom-select.css";
    import tippy from "tippy.js";
    import "tippy.js/dist/tippy.css";

    window.htmx = htmx;
    window.TomSelect = TomSelect;
    window.tippy = tippy;
    ```

    Then load PowerCRUD runtime assets in your base template:

    ```django
    {% load static %}
    <link rel="stylesheet" href="{% static 'powercrud/css/powercrud.css' %}">
    <script type="module" src="{% static 'powercrud/js/powercrud.js' %}"></script>
    ```

    Manual mode requirements:

    - Load vendor dependencies before the module entry at `powercrud/js/powercrud.js`.
    - Load only the stable module entry; the browser follows PowerCRUD's internal module imports.
    - Load Tom Select's vendor CSS before `powercrud/css/powercrud.css` so the selected pack can apply its theme-aware overrides.
    - Provide the Tom Select vendor runtime, but do not duplicate pack-owned plugin registration. The selected pack's browser adapter registers `checkbox_options`, `remove_button`, and `clear_button` when its controls need them.
    - If you use the built-in DaisyUI templates without the packaged bundle, you must provide your own DaisyUI/Tailwind CSS stack.

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

## 4. Create the first view {#quick-start-tutorial}

### Declare the view {#basic-setup}

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

### Add the URLs {#add-to-urls}

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

With no `roles` argument, PowerCRUD registers all five built-in roles:

| Role | What it gives the user |
| --- | --- |
| `Role.LIST` | The table page that lists records. |
| `Role.DETAIL` | The **View** page for one record. |
| `Role.CREATE` | The **Create** form for a new record. |
| `Role.UPDATE` | The **Edit** form for an existing record. |
| `Role.DELETE` | The **Delete** confirmation for an existing record. |

The example registers only the list and detail routes, so users can browse records and open **View**, but cannot use PowerCRUD's built-in **Create**, **Edit**, or **Delete** controls. A missing role means PowerCRUD does not register that route or render its associated built-in action. Custom actions still need their own endpoints and permission checks.

Finally, include the app URLs at the project level as usual:

```python
# config/urls.py
from django.urls import include, path

urlpatterns = [
    path("projects/", include("my_app.urls")),
]
```

### Add the first enhancements you need {#your-first-enhanced-view}

Once the plain page renders, add only the features this screen needs. This example enables the common set:

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

You now have a list with filtering, pagination, HTMX, and modals. The next guide explains each choice without requiring you to turn on everything at once.

## Next Steps

- **[Core configuration](./setup_core_crud.md#3-shape-list-and-detail-scopes)** - Field control and basic settings
- **[HTMX & Modals](./setup_core_crud.md#modals)** - Interactive features
- **[Filtering](./filtering.md)** - Advanced search and filter options
- **[Bulk operations](./bulk_edit_sync.md)** - Edit multiple records at once
