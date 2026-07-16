# Template Packs

PowerCRUD keeps CRUD behaviour in one framework-neutral core. A selected template pack supplies the templates, assets, form-rendering requirements, and framework presentation needed to render that behaviour.

The compatible default is DaisyUI. Bootstrap 5 is a supported, opt-in alternative; selecting it does not change projects that keep the default configuration.

## Supported packs

| Pack | Status | Forms | Customization |
| --- | --- | --- | --- |
| DaisyUI | Supported default and compatibility baseline | Native Django forms and the tested Crispy Tailwind integration | Focused overrides; model-scoped roots; deprecated app-wide whole-tree copy during 0.x |
| Bootstrap 5 | Supported non-default pack | Native Django forms and the tested crispy-bootstrap5 integration | Focused overrides and model-scoped roots |

## Selecting Bootstrap

Leave `POWERCRUD_TEMPLATE_PACK` unset to use the compatible DaisyUI default.

To select Bootstrap 5 at process startup, install its optional Django app and set its declaration path:

~~~python
INSTALLED_APPS = [
    # ...
    "powercrud",
    "powercrud.contrib.bootstrap5",
]

POWERCRUD_SETTINGS = {
    "POWERCRUD_TEMPLATE_PACK": "powercrud.contrib.bootstrap5:template_pack",
}
~~~

The Bootstrap pack requires its selected frontend assets. In bundled Vite mode, load its package entry:

~~~django
{% load django_vite %}
{% vite_asset 'config/static/js/bootstrap5.js' %}
~~~

In manual mode, load Bootstrap's own CSS and JavaScript together with the package-owned Bootstrap CSS and module entry. See the sample Bootstrap base template for the complete manual-static arrangement.

Pack selection happens at process startup. Runtime, query-parameter, and per-view framework switching are not supported.

`POWERCRUD_CSS_FRAMEWORK` is retained for legacy compatibility and is not a substitute for selecting the Bootstrap template pack.

## Forms and Crispy

Every supported first-party pack supports native Django form rendering. Crispy remains an application choice:

- DaisyUI has a tested `tailwind` Crispy integration.
- Bootstrap has a tested `bootstrap5` integration using `crispy-bootstrap5`.

Set `use_crispy` and your Crispy settings in the application. PowerCRUD does not silently enable Crispy, choose a Crispy pack on your behalf, or prevent you from trying another compatible integration.

## Presentation contract

PowerCRUD public presentation inputs fall into three categories:

1. **Portable semantic settings** express product intent. Every supported pack implements them or rejects the configuration clearly.
2. **Framework-translated settings** have shared meaning but use pack-native markup, CSS, or browser behaviour.
3. **Framework-specific inputs** pass raw framework values to the selected pack and are never translated.

Supported packs must not silently ignore accepted portable configuration. A genuine limitation must be explicit through configuration validation, a warning or error where appropriate, and documentation.

| Surface | DaisyUI | Bootstrap 5 |
| --- | --- | --- |
| Core CRUD, filtering, favourites, bulk, async, inline editing, links, and tooltips | Supported | Supported through Bootstrap-native templates and lifecycle handling |
| `modal_presentation`, `bulk_modal_presentation`, `view_help`, table geometry, and semantic alignment | Supported | Supported through framework translation |
| Native forms | Supported | Supported |
| Tested Crispy integration | `tailwind` | `bootstrap5` |
| Raw table, action, and button classes; style-map values; deprecated raw modal classes | Selected-framework inputs | Selected-framework inputs |
| Focused component and model-scoped root overrides | Supported | Supported |
| Plain-app `pcrud_mktemplate myapp --all` tree copy | Deprecated during 0.x; removed in v1.0 | Unavailable |
| Runtime, query-parameter, or per-view pack switching | Unsupported | Unsupported |

Raw classes are not portable settings. For example, a Tailwind class string passed to `table_classes` is accepted as a DaisyUI/Tailwind input; Bootstrap does not translate it into Bootstrap classes. Use semantic settings when a portable outcome is required.

Legacy raw modal class settings remain available only for framework-specific compatibility and emit `FutureWarning`. Use portable modal presentation for new configuration; see [Deprecations](../reference/deprecations.md).

## Customization

Use focused component overrides for normal application customization. They preserve PowerCRUD-owned JavaScript, HTMX behaviour, and nested override boundaries while letting an application change targeted markup and classes.

Model-scoped root copies remain supported where they meet the application's need. The app-wide DaisyUI whole-tree copy is a deprecated compatibility path: it creates an application-owned snapshot that does not receive later package template fixes. Use focused overrides for bounded changes, or create a custom template pack when the application needs complete presentation ownership.

See [Customisation tips](../guides/advanced/customisation_tips.md) and [Management Commands](../reference/mgmt_commands.md).

## Supported-pack validation

The DaisyUI default is the compatibility baseline. A supported pack needs:

1. the shared server behaviour matrix for applicable product behaviour;
2. pack-specific server tests for framework translation, declared resources, forms, and explicit boundaries;
3. targeted Playwright coverage for browser-only lifecycle, HTMX reinitialization, focus, modal/dropdown ownership, geometry, and responsive overflow; and
4. installed wheel and sdist validation of declared templates, assets, adapters, and form requirements.

Cross-pack parity means equivalent supported behaviour and truthful semantic outcomes. It does not require identical DOM, CSS classes, or pixels.

See [Testing](../reference/testing.md) for the project test commands and supported-pack acceptance guidance.
