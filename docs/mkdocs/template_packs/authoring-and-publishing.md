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
    contract_version=3,
    template_namespace="powercrud/packs/my-pack",
    template_package="my_powercrud_pack",
    template_resource_root="templates/powercrud/packs/my-pack",
    server_adapter="my_powercrud_pack.adapter:server_adapter",
    # capabilities and assets omitted here
)
```

Keep the copied template tree complete for every capability your declaration claims. The templates must preserve PowerCRUD's documented `data-powercrud-*` attributes and relevant ARIA/target relationships. They may use completely different CSS classes, elements, and layout.

`contract_version=3` is a numeric compatibility pin, not a reference to PowerCRUD's current-version constant. Version 3 adds the portable row-action column layout and compact all-actions dropdown. Your table header, display row, active inline form, and direct HTMX display/form fragments must all honour `row_actions_column_position` (`start` or `end`) and `row_actions_column_sticky`. Keep the selection system column always sticky and outermost at logical start, offset sticky start actions after it, use logical CSS insets for RTL/LTR portability, and preserve the semantic selection/action-column data markers. Sticky cells need an opaque pack-native background, edge separation, and table-layer z-index ordering; they remain vertically attached to their rows.

For `extra_actions_mode = "all_dropdown"`, render canonical `dropdown_actions` rather than recomposing permissions, guards, disabled state, lazy hooks, URLs, or order. For the pack's narrow layout, render `responsive_dropdown_actions` for every mode and expose only that all-actions control group; first-party packs switch below 640px. Standard menu actions have an icon and visible label; configured extras have a visible label and an empty icon gutter. Keep ordinary entries neutral, reserve destructive treatment for Delete, and do not apply configured extra-button fills inside menus. Keep the visual heading compact while preserving screen-reader-only **Actions** text, keep inline Save/Cancel visible, and preserve the existing body-level floating-menu hooks. Core copies the originating table cell's computed font size to the detached menu, while the pack remains responsible for fallback typography and control sizing. The compatibility standard and extra collections remain available for existing overrides.

`adapter.py` translates server-side presentation choices into your framework's classes or attributes. It must expose an object with `api_version = 2`, `get_presentation(context)`, and `get_widget_presentation(context)`. Start with `BaseServerAdapter`: it supplies neutral action and widget presentation, then lets the pack declare semantic defaults and small surface-specific adjustments.

This replaced the short-lived earlier adapter shape before PowerCRUD 1.0. A pack created against that shape must be regenerated or updated; PowerCRUD does not run old and new adapter contracts in parallel.

### Define the server-side widget policy

PowerCRUD supplies facts about one control; the selected pack returns its presentation. A simple adapter can declare base defaults by semantic kind and override only the surfaces that need a different presentation:

```python
from django import forms

from powercrud.template_packs import BaseServerAdapter, WidgetPresentation


class NativeDateInput(forms.DateInput):
    """Render a native date control with an HTML-compatible value."""

    input_type = "date"

    def __init__(self, attrs=None):
        """Use the format expected by a native date input."""
        super().__init__(attrs=attrs, format="%Y-%m-%d")


class LocalDateTimeInput(forms.DateTimeInput):
    """Render a browser-local datetime control while preserving seconds."""

    input_type = "datetime-local"

    def __init__(self, attrs=None):
        """Use the format expected by a datetime-local input."""
        super().__init__(attrs=attrs, format="%Y-%m-%dT%H:%M:%S")


class NativeTimeInput(forms.TimeInput):
    """Render a native time control while preserving seconds."""

    input_type = "time"

    def __init__(self, attrs=None):
        """Use the format expected by a native time input."""
        super().__init__(attrs=attrs, format="%H:%M:%S")


class ServerAdapter(BaseServerAdapter):
    """Supply this pack's server-side widget presentation."""

    widget_defaults = {
        "date": WidgetPresentation(
            widget_class=NativeDateInput,
            attrs={"class": "my-input"},
        ),
        "datetime": WidgetPresentation(
            widget_class=LocalDateTimeInput,
            attrs={"step": "1", "class": "my-input"},
        ),
        "time": WidgetPresentation(
            widget_class=NativeTimeInput,
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

For native date and time controls, set `input_type` on a dedicated widget class
and give that widget the matching HTML-compatible value format. Do not add
`type` through `WidgetPresentation.attrs`: Django renders a widget's
`input_type` separately, so expressing the same semantic through attrs can
produce duplicate, conflicting attributes. When the time format includes
seconds, use `step="1"` as shown above.

#### Understand the context-to-presentation exchange

`WidgetPolicyContext` is simply PowerCRUD's read-only description of one field. Think of it as PowerCRUD saying: “This is the `genres` field, it is a multiselect, and I am rendering it inside an inline-edit row.” Your pack does not create this object.

For each field, the exchange is:

1. PowerCRUD creates the Django field and works out what it is and where it will appear.
2. PowerCRUD describes those facts in a `WidgetPolicyContext` and hands it to the selected pack.
3. The pack returns a `WidgetPresentation`: keep or change the compatible Django widget, add these attributes, request this enhancement, and use the standard or compact layout.
4. PowerCRUD applies that answer while keeping ownership of values, choices, validation, submission, dependencies, and HTMX updates.

You normally need only `BaseServerAdapter`, `WidgetPresentation`, `widget_defaults`, and `widget_surface_overrides`, as shown above. PowerCRUD calls the inherited method for you. Import `WidgetPolicyContext` only if you write your own `get_widget_presentation()` method and want to inspect facts such as `context.surface` or `context.has_dependency`.

??? info "Exact Python definition"

    `WidgetPolicyContext` is a frozen dataclass exported from `powercrud.template_packs`. You do not define or instantiate it in your pack.

    ```python
    from dataclasses import dataclass
    from typing import Literal


    @dataclass(frozen=True, slots=True)
    class WidgetPolicyContext:
        surface: Literal["form", "inline", "filter", "bulk"]
        kind: Literal[
            "text", "textarea", "number", "date", "datetime",
            "time", "boolean", "select", "multiselect", "file",
        ]
        render_mode: Literal["native", "crispy"]
        field_name: str
        required: bool
        disabled: bool
        is_relation: bool
        has_dependency: bool
        enhancement_intent: Literal["default", "enabled", "disabled"]
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

For example, an inline `Book.genres` field rendered through Crispy Forms might arrive as a `multiselect` on the `inline` surface, with `is_relation=True`, `has_dependency=True`, and `enhancement_intent="default"`. For the adapter above, `BaseServerAdapter` starts with the standard searchable `multiselect` default, merges the inline override to make it compact, and leaves the enhancement unchanged because the application expressed no explicit override.

A returned `WidgetPresentation` may set:

| Field | Pack decision |
| --- | --- |
| `widget_class` | A compatible Django widget class, or `None` to retain the existing class. |
| `attrs` | Framework classes and presentation attributes merged onto the widget. |
| `enhancement` | `searchable-select`, `searchable-multiselect`, or `None`. |
| `variant` | `standard`, `compact`, or `None`. |

`BaseServerAdapter` resolves a semantic base default first and merges an optional `(surface, kind)` override onto it. An explicit disabled enhancement intent then removes the enhancement; an explicit enabled intent requests the matching searchable enhancement for select and multiselect controls. Do not replace those generic values, choices, querysets, validation, submission semantics, dependencies, or HTMX lifecycle in the pack.

Most packs should stay with the two dictionaries. Override the method only when presentation genuinely depends on another supplied fact:

```python
from dataclasses import replace

from powercrud.template_packs import (
    BaseServerAdapter,
    WidgetPolicyContext,
    WidgetPresentation,
)


class ServerAdapter(BaseServerAdapter):
    # widget_defaults and widget_surface_overrides as above

    def get_widget_presentation(
        self, context: WidgetPolicyContext
    ) -> WidgetPresentation:
        presentation = super().get_widget_presentation(context)
        if context.kind == "select" and context.has_dependency:
            return replace(
                presentation,
                attrs={**presentation.attrs, "data-my-dependent-control": "true"},
            )
        return presentation
```

Call `super()` first so the semantic base default, surface override, and application enhancement intent continue to resolve in the documented order.

The policy applies to PowerCRUD-generated fields and to model-backed visible fields in a custom `ModelForm` that still use Django's silent default widget. An application-declared field, `Meta.widgets` entry, runtime widget replacement, non-model field, or hidden field remains application-owned and bypasses the pack default.

### Decide whether you need browser code

Most of a pack is templates, CSS, and the Python widget policy. Add browser code only when the framework or widget library needs JavaScript to do something PowerCRUD's neutral browser behaviour cannot do. Typical examples are opening a framework-specific modal, creating searchable selects, positioning detached dropdowns, or initialising tooltips.

The generated `adapter.js` is already a valid adapter:

```javascript
window.PowerCRUDAdapter = Object.freeze({
    apiVersion: 1,
    identity: "my-pack",
    create() {
        return {};
    },
});
```

In plain language:

- `identity` must exactly match `identity="my-pack"` in `template_pack.py`.
- `create()` returns the browser jobs your pack wants to replace.
- Returning `{}` means “use PowerCRUD's neutral browser behaviour for everything.”
- PowerCRUD calls `create()` for you. Your application must not call it again.

Leave this file unchanged while ordinary HTML and CSS are enough. If the pack has no JavaScript at all, you may remove its `BrowserAdapterSpec` from `PackAssets` instead of shipping an empty file.

When JavaScript is necessary, return only the callbacks you need. For example, a framework that must initialise and clean up controls whenever PowerCRUD loads or replaces part of the page could use:

```javascript
window.PowerCRUDAdapter = Object.freeze({
    apiVersion: 1,
    identity: "my-pack",
    create() {
        return {
            fragment: {
                init(root) {
                    window.MyFramework?.initialise?.(root);
                },
                destroy(root) {
                    window.MyFramework?.destroy?.(root);
                },
            },
        };
    },
});
```

PowerCRUD calls `fragment.init(root)` after the initial page load and after relevant HTMX replacements. It calls `fragment.destroy(root)` before removing an old fragment. Replace `MyFramework` with the real API used by your pack; keep data fetching, form submission, and HTMX requests in PowerCRUD.

The available callback groups correspond to ordinary browser jobs:

| Callback group | Use it when your framework must handle |
| --- | --- |
| `fragment` | General setup or cleanup for a page fragment. |
| `searchableSelects` | Creating, destroying, or synchronising enhanced selects. |
| `tooltips` | Showing and cleaning up framework tooltips. |
| `modals` | Opening, closing, or disposing of framework modals. |
| `controls` | Framework-specific busy and disabled presentation. |
| `floatingPanels` | Cloning, positioning, showing, or hiding detached menus. |
| `inline` | Focus, saving state, and error presentation during inline editing. |
| `filters` | Framework-specific filter-panel and favourites presentation. |

You do not need to implement every group or every callback. PowerCRUD fills any missing callback with neutral behaviour. The generated `BrowserAdapterSpec` tells PowerCRUD where `adapter.js` is, and the selected-pack asset tags load it before the main PowerCRUD script.

The compatibility numbers are deliberately separate: the Python server adapter uses `api_version = 2`; this JavaScript browser adapter still uses `apiVersion: 1`.

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
        - [ ] Header, display, inline-form, and HTMX-returned rows keep selection/action/data order aligned and honour start/end plus sticky row-action settings.
        - [ ] Both dropdown modes preserve resolved permissions, disabled reasons, lazy state, HTMX/modal metadata, and detached-menu hooks; all-dropdown renders the canonical labelled order with Delete last and no orphaned divider.
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

This is a public template-pack contract, not a generic frontend build system. The template-pack contract is version 3, the current server-adapter API is version 2, and the browser-adapter API remains version 1. These numbers identify different interfaces rather than three generations of the same complete contract.

A pack author must ship the Python package resources and document vendor dependencies. The automated manual-static route is supported. Vite users own their entry, aliases, npm dependencies, and manifest because only their project knows that build layout.

Application-owned template copies and asset snapshots are a separate choice from publishing a selectable pack. See [Customising](customising.md) for those override layers and [Testing and acceptance](testing-and-acceptance.md) for the release evidence expected of a supported pack.
