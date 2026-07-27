# Authoring and Publishing a Template Pack

You can create and publish a PowerCRUD template pack for any CSS framework. It is a normal Python/Django package: it owns its templates, framework CSS, optional browser behaviour, and its own tests. It does not need a framework name registered in PowerCRUD.

PowerCRUD still owns CRUD operations, HTMX requests, saved list state, selection, persistence, and the order in which the browser lifecycle runs. Your pack supplies the presentation layer around that behaviour.

This guide follows that boundary from the generated starter through widget policy, browser behaviour, testing, packaging, and the instructions your consumers need.

## The author journey

1. Create a starter package from a maintained pack.
2. Replace its template classes and markup with your framework's presentation.
3. Define the pack's server-side widget policy and add browser hooks only where the framework needs them.
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

The generated Python adapter is neutral too. It is a valid starting point: Django keeps its compatible widgets until you deliberately add framework classes, compatible widget variants, or semantic enhancements.

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

`adapter.py` translates server-side presentation choices into your framework's classes or attributes. It must expose an object with `api_version = 2`, `get_presentation(context)`, and `get_widget_presentation(context)`. Start with `BaseServerAdapter`: it supplies neutral action and widget presentation, then lets the pack declare semantic defaults and small surface-specific adjustments.

This replaced the short-lived earlier adapter shape before PowerCRUD 1.0. A pack created against that shape must be regenerated or updated; PowerCRUD does not run old and new adapter contracts in parallel.

### Define the server-side widget policy

PowerCRUD supplies facts about one control; the selected pack returns its presentation. A simple adapter can declare base defaults by semantic kind and override only the surfaces that need a different presentation:

```python
from django import forms

from powercrud.template_packs import BaseServerAdapter, WidgetPresentation


class LocalDateTimeInput(forms.DateTimeInput):
    """Render a browser-local datetime control while preserving seconds."""

    input_type = "datetime-local"

    def __init__(self, attrs=None):
        """Use the format expected by a datetime-local input."""
        super().__init__(attrs=attrs, format="%Y-%m-%dT%H:%M:%S")


class ServerAdapter(BaseServerAdapter):
    """Supply this pack's server-side widget presentation."""

    widget_defaults = {
        "date": WidgetPresentation(
            widget_class=forms.DateInput,
            attrs={"type": "date", "class": "my-input"},
        ),
        "datetime": WidgetPresentation(
            widget_class=LocalDateTimeInput,
            attrs={"step": "1", "class": "my-input"},
        ),
        "select": WidgetPresentation(enhancement="searchable-select"),
        "multiselect": WidgetPresentation(
            enhancement="searchable-multiselect",
            variant="standard",
        ),
    }
    widget_surface_overrides = {
        ("inline", "multiselect"): WidgetPresentation(variant="compact"),
        ("filter", "select"): WidgetPresentation(
            attrs={"class": "my-select my-select-small"},
        ),
    }


server_adapter = ServerAdapter()
```

The semantic widget kinds are `text`, `textarea`, `number`, `date`, `datetime`, `time`, `boolean`, `select`, `multiselect`, and `file`. You do not have to repeat neutral entries: an omitted kind resolves to an empty `WidgetPresentation`, which leaves Django's compatible widget in place.

`WidgetPolicyContext` describes why and where the widget is being rendered:

| Context value | Meaning |
| --- | --- |
| `surface` | `form`, `inline`, `filter`, or `bulk`. |
| `kind` | One of the semantic widget kinds above. |
| `render_mode` | `native` or `crispy`. |
| `field_name` | The application-facing field name. |
| `required`, `disabled` | Current Django field state. |
| `is_relation` | Whether the control represents a relation. |
| `has_dependency` | Whether PowerCRUD manages a queryset dependency for this field. |
| `enhancement_intent` | `default`, `enabled`, or `disabled` application intent. |

A returned `WidgetPresentation` may set:

| Field | Pack decision |
| --- | --- |
| `widget_class` | A compatible Django widget class, or `None` to retain the existing class. |
| `attrs` | Framework classes and presentation attributes merged onto the widget. |
| `enhancement` | `searchable-select`, `searchable-multiselect`, or `None`. |
| `variant` | `standard`, `compact`, or `None`. |

`BaseServerAdapter` resolves a semantic base default first and merges an optional `(surface, kind)` override onto it. An explicit disabled enhancement intent then removes the enhancement; an explicit enabled intent requests the matching searchable enhancement for select and multiselect controls. Do not replace those generic values, choices, querysets, validation, submission semantics, dependencies, or HTMX lifecycle in the pack.

The policy applies to PowerCRUD-generated fields and to model-backed visible fields in a custom `ModelForm` that still use Django's silent default widget. An application-declared field, `Meta.widgets` entry, runtime widget replacement, non-model field, or hidden field remains application-owned and bypasses the pack default.

### Add browser behaviour only when needed

The optional browser module sets `window.PowerCRUDAdapter` before the stable `powercrud/js/powercrud.js` entry loads. It has `apiVersion: 1`, the same `identity` as the Python declaration, and a `create(context)` function. Server-adapter version 2 and browser-adapter version 1 are separate compatibility markers. The browser adapter returns only the semantic hook groups the framework needs; PowerCRUD supplies no-op defaults for the rest.

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

??? success "Template pack release checklist"

    === "Contract and policy"

        - [ ] The declaration uses the current contract and a safe identity, namespace, package resource root, capability set, and form-support claim.
        - [ ] The server adapter uses `api_version = 2` and exposes the required presentation methods.
        - [ ] Every semantic widget kind has a deliberate pack decision or an intentional neutral fallback.
        - [ ] Surface overrides are limited to real form, inline, filter, or bulk presentation differences.
        - [ ] The documentation preserves the application-owned custom-widget boundary.

    === "Templates and browser"

        - [ ] Required templates preserve the documented `data-powercrud-*`, target, and ARIA relationships for the behaviour they retain.
        - [ ] The browser adapter uses `apiVersion: 1`, matches the declaration identity, and is loaded once before the PowerCRUD entry.
        - [ ] PowerCRUD retains request, selection, modal-cleanup, and HTMX lifecycle ownership.
        - [ ] Pack-owned CSS and JavaScript are separated from consumer-owned vendor dependencies.
        - [ ] Manual-static and Vite consumers receive the correct load order without combining frontend routes.

    === "Tests and packaging"

        - [ ] The public conformance helper passes for the package declaration.
        - [ ] Native forms and every declared Crispy integration have appropriate coverage.
        - [ ] Server and browser tests cover the pack-specific behaviour that generic contract checks cannot see.
        - [ ] Both the wheel and source distribution pass isolated-install validation.
        - [ ] Installed artifacts contain every declared template and static resource.

    === "Consumer documentation"

        - [ ] Installation, `INSTALLED_APPS`, the selector, frontend assets, vendor requirements, and any Crispy setup are documented.
        - [ ] Supported PowerCRUD versions and known presentation limits are stated clearly.
        - [ ] Unsupported or untested behaviour is described rather than silently implied.

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

## Current contract boundaries

This is a public template-pack contract, not a generic frontend build system. The current server-adapter API is version 2; the browser-adapter API remains version 1. These numbers identify different interfaces rather than two generations of the same complete pack contract.

A pack author must ship the Python package resources and document vendor dependencies. The automated manual-static route is supported. Vite users own their entry, aliases, npm dependencies, and manifest because only their project knows that build layout.

Application-owned template copies and asset snapshots are a separate choice from publishing a selectable pack. See [Customising](customising.md) for those override layers and [Testing and acceptance](testing-and-acceptance.md) for the release evidence expected of a supported pack.
