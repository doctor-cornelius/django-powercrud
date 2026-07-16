# Selecting and Configuring a Template Pack

Choose the template pack in `POWERCRUD_SETTINGS` before Django starts. The selection applies to the whole process. PowerCRUD does not support changing it from a query parameter, a view attribute, or while the process is running.

Choose two things separately:

1. the complete pack that supplies presentation; and
2. the one frontend route used by the base template for that pack.

The normal frontend routes are the packaged Vite entry, package-owned manual-static tags, or an application-owned entry. Do not load more than one PowerCRUD entry on the same page.

!!! warning "A pack is not a per-view or per-tenant switch"

    The selection is process-wide. Use model or view template overrides when selected screens need different markup, but do not try to load different complete packs, adapters, or pack CSS/JavaScript for different requests.

## Use the DaisyUI default

Leave `POWERCRUD_TEMPLATE_PACK` unset to use the built-in DaisyUI pack. If you prefer to make that choice explicit, put the lowercase `"daisyui"` selector inside `POWERCRUD_SETTINGS`:

```python
POWERCRUD_SETTINGS = {
    "POWERCRUD_TEMPLATE_PACK": "daisyui",
}
```

!!! warning "Use `daisyui` to select the pack"

    The legacy `POWERCRUD_CSS_FRAMEWORK` setting remains for compatibility; its bundled default is the exact value `"daisyUI"`. That legacy value does **not** select Bootstrap or another optional pack. For the new `POWERCRUD_TEMPLATE_PACK` setting, use the lowercase selector `"daisyui"` shown above.

Use the regular PowerCRUD frontend entry in your base template when using the packaged Vite bundle:

```django
{% load django_vite powercrud %}
{% powercrud_runtime_config %}
{% vite_asset 'config/static/js/main.js' %}
```

If you manage frontend assets yourself, follow [Getting Started](../guides/getting_started.md#frontend-integration) and provide the DaisyUI/Tailwind stack your project uses.

## Select Bootstrap 5

Install the optional Django app and select its declaration path:

```python
INSTALLED_APPS = [
    # ...
    "powercrud",
    "powercrud.contrib.bootstrap5",
]

POWERCRUD_SETTINGS = {
    "POWERCRUD_TEMPLATE_PACK": "powercrud.contrib.bootstrap5:template_pack",
}
```

With the packaged Vite assets, load Bootstrap's entry from the same base template that owns your site layout:

```django
{% load django_vite powercrud %}
{% powercrud_runtime_config %}
{% vite_asset 'config/static/js/bootstrap5.js' %}
```

For a manual asset setup, load the Bootstrap CSS and JavaScript dependencies, then PowerCRUD's Bootstrap CSS and JavaScript in the documented order. The sample application's `templates_bootstrap/sample/manual_static/base.html` is the maintained working example. Do not mix the packaged-bundle and manual-asset paths on one page.

## Use an application-owned asset snapshot

If the project needs to change a supported pack's PowerCRUD CSS or JavaScript, generate a manual-static snapshot with `pcrud_mktemplate myapp --assets`. It copies only PowerCRUD-owned assets to the Django app's static namespace and prints the replacement stylesheet and module-script tags for the base template.

Keep the selected `POWERCRUD_TEMPLATE_PACK` aligned with the copied source. The snapshot does not include vendor dependencies and has no package fallback for deleted files. Replace the package-owned PowerCRUD tags; do not load both entries, and do not combine the generated manual-static entry with the packaged Vite entry. Vite users need to maintain their own custom frontend entry for this level of ownership.

## Select an independently published pack

An independently published pack is selected by its Python declaration path, not by a framework-name whitelist. Install its distribution, add the Django app named by the pack's documentation, then select it:

```python
INSTALLED_APPS = [
    # ...
    "powercrud",
    "my_powercrud_pack",
]

POWERCRUD_SETTINGS = {
    "POWERCRUD_TEMPLATE_PACK": (
        "my_powercrud_pack.template_pack:template_pack"
    ),
}
```

For a package-owned manual-static setup, load its vendors first and then let PowerCRUD output the selected pack's own CSS/module order:

```django
{% load static powercrud %}
{% powercrud_runtime_config %}
{# Your pack's required vendor tags go here. #}
{% powercrud_pack_assets %}
```

For Vite, keep the same runtime-config tag but use an application-owned entry that imports that pack's documented adapter and CSS before `powercrud/js/powercrud.js`. Do not load a manual-static entry as well. [Authoring and publishing](authoring-and-publishing.md) explains the boundary for package authors.

The exact import paths depend on the project's Vite aliases and on how the independent pack documents its source files. This is the required shape of an entry; replace the `@...` paths with aliases or paths defined by the project:

```javascript
// frontend/my-powercrud-pack.js
// Import and expose this pack's documented vendor dependencies first.
import "@my-powercrud-pack/css/powercrud.css";
import "@my-powercrud-pack/js/adapter.js";

// Dynamic import keeps the selected adapter and vendors in place before core starts.
void import("@powercrud/js/powercrud.js");
```

The matching base template loads the runtime configuration and this one entry:

```django
{% load django_vite powercrud %}
{% powercrud_runtime_config %}
{% vite_asset 'frontend/my-powercrud-pack.js' %}
```

PowerCRUD deliberately does not prescribe the aliases, npm dependencies, or Vite manifest entry because those are owned by the application. The pack author must document the required vendor imports and source locations.

## Configure forms deliberately

Both supported packs render native Django forms. Set `use_crispy = False` if you need native rendering in a project that has Crispy Forms installed.

If you use Crispy Forms, configure its template pack yourself so it matches the selected PowerCRUD pack. PowerCRUD does not select a Crispy pack, install its integration package, or check that your Crispy configuration matches:

```python
# DaisyUI
CRISPY_TEMPLATE_PACK = "tailwind"

# Bootstrap 5
CRISPY_TEMPLATE_PACK = "bootstrap5"
```

Install and add the related Crispy integration app, then configure any allowed-pack setting required by your Crispy setup. PowerCRUD's pack selection and Crispy's template-pack setting are separate choices, so keep them aligned. An independently published PowerCRUD pack must state whether it supports Crispy Forms and, if so, which Crispy integration it expects.

## Know which template root is in use

The selected pack normally supplies its own template namespace. These settings have deliberately different ownership implications:

| Setting | Use it when | Fallback behaviour |
| --- | --- | --- |
| `template_override_path` | Selected views should use a copied application root. | Missing roots, components, and nested templates can still use the selected pack unless `template_override_complete = True` is set for a complete `--all` copy. |
| `templates_path` | The view intentionally owns a complete template namespace. | It replaces the selected pack namespace; treat it as complete ownership, not a quick markup override. |

For ordinary changes, prefer the focused overrides described in [Customising](customising.md). Neither setting changes the selected pack's frontend assets.

Your `base_template_path` is separate again: it must point to the application template that provides your site's outer HTML, assets, and navigation.
