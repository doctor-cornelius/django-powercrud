"""Optional Bootstrap 5 template-pack declaration."""

from powercrud.template_packs import TEMPLATE_PACK_CONTRACT_VERSION, TemplatePack


template_pack = TemplatePack(
    identity="bootstrap5",
    contract_version=TEMPLATE_PACK_CONTRACT_VERSION,
    template_namespace="powercrud/packs/bootstrap5",
    template_package="powercrud",
    template_resource_root="contrib/bootstrap5/templates/powercrud/packs/bootstrap5",
    legacy_copy_destination=None,
    framework_adapter="bootstrap5",
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
    crispy_template_packs=frozenset({"bootstrap5"}),
    django_app="powercrud.contrib.bootstrap5",
    manual_assets=(
        "powercrud/contrib/bootstrap5/css/bootstrap5.css",
        "powercrud/contrib/bootstrap5/js/bootstrap5.js",
    ),
    vite_assets=("config/static/js/bootstrap5.js",),
)
