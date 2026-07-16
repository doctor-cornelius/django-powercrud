# Authoring and Publishing a Template Pack

You can create and publish a PowerCRUD template pack for any CSS framework. It is a normal Python/Django package: it owns its templates, framework CSS, optional browser behaviour, and its own tests. It does not need a framework name registered in PowerCRUD.

PowerCRUD still owns CRUD operations, HTMX requests, saved list state, selection, persistence, and the order in which the browser lifecycle runs. Your pack supplies the presentation layer around that behaviour.

## The author journey

1. Create a starter package from a maintained pack.
2. Replace its template classes and markup with your framework's presentation.
3. Add small Python or browser adapters only where the framework needs them.
4. Test the package in its own repository.
5. Build and publish the Python package.
6. Consumers install the package, add its Django app, and select its declaration.

The starter is deliberately an ordinary editable project. It is not generated inside PowerCRUD and it is not another project-level override.

## Create a starter

Run the command from a Django project with PowerCRUD installed:

```bash
python manage.py pcrud_starttemplatepack my_powercrud_pack ../my-powercrud-pack
```

The command copies the complete DaisyUI template tree by default and creates this shape:

```text
my-powercrud-pack/
    pyproject.toml
    src/
        my_powercrud_pack/
            adapter.py
            apps.py
            template_pack.py
            templates/powercrud/packs/my-powercrud-pack/
            static/powercrud/packs/my-powercrud-pack/
                css/powercrud.css
                js/adapter.js
```

Use `--source-template-pack bootstrap5` if Bootstrap is a closer starting point. The source is only a starting point; it does not make the new package a DaisyUI or Bootstrap pack.

The generated package has a neutral browser adapter. That is enough for a framework that can use normal HTML dialogs, buttons, and hidden elements. Add hooks only if the framework needs something more specific, such as its own modal API, dropdown placement, tooltip API, or busy-state classes.

## What belongs in the package

`template_pack.py` exports one `TemplatePack` declaration. It identifies the package, its template namespace, its server adapter, and its pack-owned static resources. The generated file is the working reference, but its important parts look like this:

```python
from powercrud.template_packs import TemplatePack

template_pack = TemplatePack(
    identity="my-pack",
    template_namespace="powercrud/packs/my-pack",
    template_package="my_powercrud_pack",
    template_resource_root="templates/powercrud/packs/my-pack",
    server_adapter="my_powercrud_pack.adapter:server_adapter",
    # capabilities and assets omitted here
)
```

Keep the copied template tree complete for every capability your declaration claims. The templates must preserve PowerCRUD's documented `data-powercrud-*` attributes and relevant ARIA/target relationships. They may use completely different CSS classes, elements, and layout.

`adapter.py` translates small server-side presentation choices into your framework's classes or attributes. It must expose an object with `api_version = 1` and `get_presentation(context)`. Start with `BaseServerAdapter`; override it only when you need framework-specific classes or view-help colours.

The optional browser module sets `window.PowerCRUDAdapter` before the stable `powercrud/js/powercrud.js` entry loads. It has `apiVersion: 1`, the same `identity` as the Python declaration, and a `create(context)` function. It returns only the semantic hook groups the framework needs. PowerCRUD supplies no-op defaults for the rest.

This is intentionally not a list of DaisyUI or Bootstrap APIs. A pack for another CSS framework can use its own classes and library APIs, provided it preserves the semantic template hooks and implements any browser behaviour it needs.

## Own CSS and JavaScript honestly

The declaration lists only assets owned by the pack. It may declare stylesheets, a browser adapter module, and directories that `pcrud_mktemplate --assets` can copy into an application-owned manual-static snapshot. Third-party libraries remain dependencies of the consuming application; do not bundle Bootstrap, HTMX, Tom Select, Tippy, or another vendor merely because PowerCRUD uses them in a particular configuration.

For normal package-owned manual-static loading, a consumer can use the selected-pack tags:

```django
{% load static powercrud %}
{% powercrud_runtime_config %}
{% powercrud_pack_assets %}
```

Load the required vendor scripts before `powercrud_pack_assets`. It emits the selected pack adapter first and the stable PowerCRUD entry second. A browser adapter must be loaded only once.

Vite remains application-owned. A Vite project emits `powercrud_runtime_config`, then its own entry must load the pack's adapter and CSS before importing `powercrud/js/powercrud.js`. PowerCRUD does not edit a downstream Vite manifest or guess an npm package name. Do not combine that custom entry with the package-owned manual-static tags on the same page.

For Vite consumers, document a small entry with this ordering. The aliases are deliberately placeholders: the consuming project owns the aliases and source locations.

```javascript
// frontend/my-powercrud-pack.js
// Import and expose any vendor dependencies required by this pack first.
import "@my-powercrud-pack/css/powercrud.css";
import "@my-powercrud-pack/js/adapter.js";

// Dynamic import ensures adapter and vendor setup finishes before core runs.
void import("@powercrud/js/powercrud.js");
```

Document which project aliases, npm packages, globals, and CSS imports make those paths work. A Python package does not automatically become an npm package, and PowerCRUD cannot safely infer how a consuming project exposes its packaged static sources to Vite.

## Test it in the package repository

Put the tests beside the pack, not in the PowerCRUD repository. Configure a small Django test project that includes the pack app, then start with the public helper:

```python
from powercrud.template_pack_testing import assert_template_pack_conforms


def test_pack_contract():
    assert_template_pack_conforms(
        "my_powercrud_pack.template_pack:template_pack"
    )
```

That checks the declaration, packaged template resources, required templates for claimed capabilities, static resources, adapter imports, and optional Crispy integration declarations. Add normal Django tests for your templates and focused browser tests for browser-only risks such as modal ownership, dropdowns, HTMX replacement, or vendor loading.

Before release, build both a wheel and a source distribution and run the same tests in an environment that installs those artifacts. This catches missing `templates/` or `static/` package data that a source checkout can hide.

## Publish, install, and select

Publish the package to PyPI or an internal index like any other Python distribution. A consumer then installs it and adds its Django app:

```bash
python -m pip install my-powercrud-pack
```

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

The selector is a Python `module.path:attribute`, not a framework name. PowerCRUD validates the declaration and reports a missing module, wrong contract version, missing template/static resource, or incompatible adapter directly. It never falls back to DaisyUI because another pack was selected incorrectly.

## Limits of version 1

This is a public template-pack contract, not a generic frontend build system. A pack author must ship the Python package resources and document vendor dependencies. The automated manual-static route is supported. Vite users own their entry, aliases, npm dependencies, and manifest because only their project knows that build layout.

Application-owned template copies and asset snapshots are a separate choice from publishing a selectable pack. See [Customising](customising.md) for those override layers and [Testing and acceptance](testing-and-acceptance.md) for the release evidence expected of a supported pack.
