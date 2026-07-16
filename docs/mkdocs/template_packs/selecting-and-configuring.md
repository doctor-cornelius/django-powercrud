# Selecting and Configuring a Template Pack

Choose the template pack in `POWERCRUD_SETTINGS` before Django starts. The selection applies to the whole process. PowerCRUD does not support changing it from a query parameter, a view attribute, or while the process is running.

## Use the DaisyUI default

Leave `POWERCRUD_TEMPLATE_PACK` unset to use the built-in DaisyUI pack. If you prefer to make that choice explicit, put the lowercase `"daisyui"` selector inside `POWERCRUD_SETTINGS`:

```python
POWERCRUD_SETTINGS = {
    "POWERCRUD_TEMPLATE_PACK": "daisyui",
}
```

The legacy `POWERCRUD_CSS_FRAMEWORK` setting remains for compatibility; its bundled default is the exact value `"daisyUI"`. It does not select Bootstrap or another optional pack. The selector `"daisyui"` and the legacy value `"daisyUI"` are deliberately different spellings.

Use the regular PowerCRUD frontend entry in your base template when using the packaged Vite bundle:

```django
{% load django_vite %}
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
{% load django_vite %}
{% vite_asset 'config/static/js/bootstrap5.js' %}
```

For a manual asset setup, load the Bootstrap CSS and JavaScript dependencies, then PowerCRUD's Bootstrap CSS and JavaScript in the documented order. The sample application's `templates_bootstrap/sample/manual_static/base.html` is the maintained working example. Do not mix the packaged-bundle and manual-asset paths on one page.

## Use an application-owned asset snapshot

If the project needs to change a supported pack's PowerCRUD CSS or JavaScript, generate a manual-static snapshot with `pcrud_mktemplate myapp --assets`. It copies only PowerCRUD-owned assets to the Django app's static namespace and prints the replacement stylesheet and module-script tags for the base template.

Keep the selected `POWERCRUD_TEMPLATE_PACK` aligned with the copied source. The snapshot does not include vendor dependencies and has no package fallback for deleted files. Replace the package-owned PowerCRUD tags; do not load both entries, and do not combine the generated manual-static entry with the packaged Vite entry. Vite users need to maintain their own custom frontend entry for this level of ownership.

## Configure forms deliberately

Both supported packs render native Django forms. Set `use_crispy = False` if you need native rendering in a project that has Crispy Forms installed.

If you use Crispy Forms, configure its template pack yourself so it matches the selected PowerCRUD pack. PowerCRUD does not select a Crispy pack, install its integration package, or check that your Crispy configuration matches:

```python
# DaisyUI
CRISPY_TEMPLATE_PACK = "tailwind"

# Bootstrap 5
CRISPY_TEMPLATE_PACK = "bootstrap5"
```

Install and add the related Crispy integration app, then configure any allowed-pack setting required by your Crispy setup. PowerCRUD's pack selection and Crispy's template-pack setting are separate choices, so keep them aligned.

## Know which template root is in use

The selected pack normally supplies its own template namespace. An explicit `templates_path` setting takes precedence over that namespace. Use it only when you intentionally own a complete template root; for ordinary changes, prefer the focused overrides described in [Customising](customising.md).

Your `base_template_path` is separate again: it must point to the application template that provides your site's outer HTML, assets, and navigation.
