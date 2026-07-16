"""Declaration for the compatible built-in DaisyUI template pack."""

from powercrud.template_packs import (
    BrowserAdapterSpec,
    CrispyIntegration,
    PackAssets,
    PackageResource,
    TEMPLATE_PACK_CONTRACT_VERSION,
    TemplatePack,
    VendorRequirement,
)


template_pack = TemplatePack(
    identity="daisyui",
    contract_version=TEMPLATE_PACK_CONTRACT_VERSION,
    template_namespace="powercrud/packs/daisyui",
    template_package="powercrud",
    template_resource_root="templates/powercrud/packs/daisyui",
    server_adapter="powercrud.packs.daisyui.adapter:server_adapter",
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
    django_app="powercrud",
    assets=PackAssets(
        stylesheets=(),
        copy_roots=(),
        browser_adapter=BrowserAdapterSpec(
            api_version=1,
            static_path="powercrud/js/daisyui-adapter.js",
            source=PackageResource(
                "powercrud", "static/powercrud/js/daisyui-adapter.js"
            ),
        ),
        vendor_requirements=(
            VendorRequirement(
                name="DaisyUI and Tailwind CSS",
                purpose="Framework styling",
                manual_static_note="Load the application's compiled stylesheet first.",
            ),
            VendorRequirement(
                name="HTMX, Tom Select, and Tippy",
                purpose="PowerCRUD interactive enhancements",
                global_name="tippy",
            ),
        ),
    ),
    crispy_integrations=(CrispyIntegration("tailwind", "crispy_tailwind"),),
    legacy_copy_destination="daisyUI",
)
