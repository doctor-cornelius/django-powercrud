# Authoring and Publishing a Template Pack

This page records the declaration boundary used by PowerCRUD's maintained packs. It is primarily for PowerCRUD maintainers and for package authors discussing a deliberately supported integration. It is not a promise that arbitrary framework adapters, variants, or Crispy integrations can be dropped into an application and supported automatically.

## Declare the pack in Python

The selector accepts the built-in `daisyui` alias or a Python declaration path in the form `module.path:attribute`. A declaration is a `TemplatePack` value with an identity, a contract version, template-location data, capabilities, form support, and asset metadata.

The two maintained declarations show the expected shape:

```python
from powercrud.template_packs import TEMPLATE_PACK_CONTRACT_VERSION, TemplatePack


template_pack = TemplatePack(
    identity="example",
    contract_version=TEMPLATE_PACK_CONTRACT_VERSION,
    template_namespace="powercrud/packs/example",
    template_package="example_package",
    template_resource_root="templates/powercrud/packs/example",
    legacy_copy_destination=None,
    framework_adapter="daisyui",
    variant_adapter=None,
    capabilities=frozenset({"list", "form", "detail", "delete", "filters", "modal", "bulk", "async", "inline", "favourites"}),
    supports_native_forms=True,
    crispy_template_packs=frozenset({"tailwind"}),
    django_app="example_package",
)
```

The declaration describes resources; it does not load templates or frontend assets. `template_package` and `template_resource_root` identify packaged templates, while `template_namespace` is the namespace PowerCRUD resolves at runtime.

## Stay within the current contract

The current runtime accepts the shipped `daisyui` and `bootstrap5` framework adapters. Variant adapters are not supported. Crispy integration is similarly bounded to the maintained `tailwind` and `bootstrap5` combinations.

An external package may expose a declaration path while reusing one of those shipped adapter identities and the corresponding supported Crispy pack. That is a narrow packaging arrangement, not a generic framework-adapter plugin system. It needs explicit compatibility review before being described as supported.

## Package templates and assets

Ship template resources inside the Python distribution and add the package's Django app to `INSTALLED_APPS` when the declaration requires it. Declare manual asset paths and Vite entries accurately so users can choose one loading path.

The Bootstrap declaration is the reference for an optional app with both manual assets and a Vite entry. The DaisyUI declaration is the reference for the built-in default. Follow their structure rather than inventing a separate registry or runtime switch.

## Publish only with acceptance evidence

Before claiming support, validate the declaration, packaged wheel and source-distribution resources, shared server behaviour, pack-specific presentation and asset behaviour, and browser risks where they apply. The repository's installed-artifact harness currently names the first-party DaisyUI and Bootstrap packs directly, so it is not a generic third-party certification tool.

See [Testing and acceptance](testing-and-acceptance.md) for the required evidence and [Customising](customising.md) when the real need is an application override rather than a maintained pack.
