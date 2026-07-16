"""Third-party-style declarations used by template-pack discovery tests."""

from powercrud.template_packs import TEMPLATE_PACK_CONTRACT_VERSION, TemplatePack


template_pack = TemplatePack(
    identity="fixture-pack",
    contract_version=TEMPLATE_PACK_CONTRACT_VERSION,
    template_namespace="fixture/templates",
    template_package="tests",
    template_resource_root="template_packs/fixture",
    legacy_copy_destination=None,
    framework_adapter="daisyui",
    variant_adapter=None,
    capabilities=frozenset({"list"}),
    supports_native_forms=True,
    crispy_template_packs=frozenset(),
    django_app=None,
)

not_a_template_pack = object()
