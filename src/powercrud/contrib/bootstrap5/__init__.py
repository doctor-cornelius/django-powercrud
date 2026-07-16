"""Optional Bootstrap 5 template-pack declaration."""

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
    identity="bootstrap5",
    contract_version=TEMPLATE_PACK_CONTRACT_VERSION,
    template_namespace="powercrud/packs/bootstrap5",
    template_package="powercrud",
    template_resource_root="contrib/bootstrap5/templates/powercrud/packs/bootstrap5",
    server_adapter="powercrud.contrib.bootstrap5.adapter:server_adapter",
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
    django_app="powercrud.contrib.bootstrap5",
    assets=PackAssets(
        stylesheets=("powercrud/contrib/bootstrap5/css/bootstrap5.css",),
        copy_roots=(
            PackageResource(
                "powercrud",
                "contrib/bootstrap5/static/powercrud/contrib/bootstrap5",
            ),
        ),
        browser_adapter=BrowserAdapterSpec(
            api_version=1,
            # Preserve the established manual-static entry. It registers the
            # public adapter before loading the stable PowerCRUD runtime.
            static_path="powercrud/contrib/bootstrap5/js/bootstrap5.js",
            source=PackageResource(
                "powercrud",
                "contrib/bootstrap5/static/powercrud/contrib/bootstrap5/js/bootstrap5.js",
            ),
        ),
        vendor_requirements=(
            VendorRequirement(
                name="Bootstrap 5",
                purpose="Framework styling and modal/tooltip behaviour",
                global_name="bootstrap",
                vite_import="bootstrap",
            ),
            VendorRequirement(
                name="HTMX and Tom Select",
                purpose="PowerCRUD interactive enhancements",
            ),
        ),
    ),
    crispy_integrations=(CrispyIntegration("bootstrap5", "crispy_bootstrap5"),),
)
