"""Declaration for the compatible built-in DaisyUI template pack."""

from powercrud.template_packs import TEMPLATE_PACK_CONTRACT_VERSION, TemplatePack


template_pack = TemplatePack(
    identity="daisyui",
    contract_version=TEMPLATE_PACK_CONTRACT_VERSION,
    template_namespace="powercrud/packs/daisyui",
    template_package="powercrud",
    template_resource_root="templates/powercrud/packs/daisyui",
    legacy_copy_destination="daisyUI",
    framework_adapter="daisyui",
    variant_adapter=None,
    capabilities=frozenset(
        {
            "list",
            "form",
            "detail",
            "delete",
            "filters",
            "modal",
            "bulk",
            "async",
            "inline",
            "favourites",
        }
    ),
    supports_native_forms=True,
    crispy_template_packs=frozenset({"tailwind"}),
    django_app="powercrud",
)
