"""Third-party-style declarations used by template-pack discovery tests."""

from powercrud.template_packs import (
    BaseServerAdapter,
    BrowserAdapterSpec,
    PackAssets,
    PackageResource,
    TEMPLATE_PACK_CONTRACT_VERSION,
    TemplatePack,
)


class FixtureServerAdapter(BaseServerAdapter):
    """Provide the neutral server contract for selection-only fixture declarations."""


server_adapter = FixtureServerAdapter()


template_pack = TemplatePack(
    identity="fixture-pack",
    contract_version=TEMPLATE_PACK_CONTRACT_VERSION,
    template_namespace="fixture/templates",
    template_package="tests",
    template_resource_root="template_packs/fixture",
    server_adapter="tests.template_pack_fixtures:server_adapter",
    capabilities=frozenset({"list"}),
    supports_native_forms=True,
    django_app=None,
)


same_adapter_template_pack = TemplatePack(
    identity="same-adapter-fixture",
    contract_version=TEMPLATE_PACK_CONTRACT_VERSION,
    template_namespace="tests/template_packs/same_adapter",
    template_package="tests",
    template_resource_root="templates/tests/template_packs/same_adapter",
    server_adapter="powercrud.packs.daisyui.adapter:server_adapter",
    capabilities=frozenset({"list", "form", "detail", "delete"}),
    supports_native_forms=True,
    django_app=None,
)


external_browser_template_pack = TemplatePack(
    identity="external-browser-fixture",
    contract_version=TEMPLATE_PACK_CONTRACT_VERSION,
    template_namespace="tests/template_packs/same_adapter",
    template_package="tests",
    template_resource_root="templates/tests/template_packs/same_adapter",
    server_adapter="tests.template_pack_fixtures:server_adapter",
    capabilities=frozenset({"list", "form", "detail", "delete"}),
    supports_native_forms=True,
    django_app="tests",
    assets=PackAssets(
        browser_adapter=BrowserAdapterSpec(
            api_version=1,
            static_path="powercrud/packs/external-browser-fixture/js/adapter.js",
            source=PackageResource(
                "tests",
                "static/powercrud/packs/external-browser-fixture/js/adapter.js",
            ),
        ),
    ),
)

not_a_template_pack = object()
