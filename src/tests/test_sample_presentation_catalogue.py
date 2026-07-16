"""Proof that maintained presentations share one sample application catalogue."""

from config import settings as default_settings
from config import settings_bootstrap as bootstrap_settings
from config import settings_focused_overrides as focused_settings
from django.conf import settings

from powercrud.template_packs import get_configured_template_pack
from sample.urls import urlpatterns
from sample.views import BookCRUDView


BOOTSTRAP_SELECTOR = "powercrud.contrib.bootstrap5:template_pack"
PRESENTATION_SETTINGS = {
    "default": default_settings,
    "focused": focused_settings,
    "bootstrap": bootstrap_settings,
}


def test_presentation_settings_share_the_sample_application_catalogue():
    """All variants must retain the same project, sample app, routes, and Book view class."""

    route_names = {pattern.name for pattern in urlpatterns if pattern.name}
    required_book_routes = {
        "bigbook-list",
        "bigbook-create",
        "bigbook-detail",
        "bigbook-update",
        "bigbook-delete",
        "bigbook-bulk-edit",
        "bigbook-inline-row",
        "bigbook-columns",
    }

    assert required_book_routes <= route_names, (
        "The one shared sample URL catalogue should expose every Book route used by Phase 5."
    )
    assert BookCRUDView.__module__ == "sample.views", (
        "All presentations must use the existing sample BookCRUDView rather than copied views."
    )

    for presentation, presentation_settings in PRESENTATION_SETTINGS.items():
        assert presentation_settings.ROOT_URLCONF == default_settings.ROOT_URLCONF, (
            f"The {presentation} presentation must retain the default URL configuration."
        )
        assert set(default_settings.INSTALLED_APPS) <= set(presentation_settings.INSTALLED_APPS), (
            f"The {presentation} presentation must retain the shared application catalogue."
        )
        assert presentation_settings.DATABASES == default_settings.DATABASES, (
            f"The {presentation} presentation must retain the same sample database configuration."
        )

    assert "POWERCRUD_TEMPLATE_PACK" not in default_settings.POWERCRUD_SETTINGS, (
        "The default presentation must retain compatible implicit DaisyUI selection."
    )
    assert "POWERCRUD_TEMPLATE_PACK" not in focused_settings.POWERCRUD_SETTINGS, (
        "Focused overrides must retain the standard DaisyUI pack selection."
    )
    assert bootstrap_settings.POWERCRUD_SETTINGS["POWERCRUD_TEMPLATE_PACK"] == BOOTSTRAP_SELECTOR, (
        "The Bootstrap presentation should select the supported Bootstrap namespace."
    )


def test_active_presentation_uses_the_expected_shared_or_bootstrap_pack():
    """Every maintained presentation should be independently runnable against the shared app."""

    selected_pack = get_configured_template_pack()
    active_selector = settings.POWERCRUD_SETTINGS.get("POWERCRUD_TEMPLATE_PACK")

    if active_selector == BOOTSTRAP_SELECTOR:
        assert selected_pack.template_namespace == "powercrud/packs/bootstrap5", (
            "Bootstrap settings must select the Bootstrap namespace globally."
        )
        assert settings.SAMPLE_PRESENTATION == "Bootstrap 5 pack", (
            "Bootstrap settings must retain their sample-only presentation label."
        )
    else:
        assert active_selector is None, (
            "Maintained sample tests should run only under implicit DaisyUI or explicit Bootstrap settings."
        )
        assert selected_pack.template_namespace == "powercrud/packs/daisyui", (
            "Default and focused settings must continue to use the compatible DaisyUI namespace."
        )
