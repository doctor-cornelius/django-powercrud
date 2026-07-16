"""Tests for the standalone Bootstrap sample presentation settings."""

from config import settings as default_sample_settings
from config import settings_bootstrap as bootstrap_sample_settings
import pytest
from django.conf import settings
from django.urls import reverse
from tests import settings as default_test_settings
from tests import settings_bootstrap as bootstrap_test_settings


BOOTSTRAP_SELECTOR = "powercrud.contrib.bootstrap5:template_pack"


def test_bootstrap_settings_prepend_only_the_bootstrap_sample_template_root():
    """Bootstrap overlays must select a sample shell without mutating DaisyUI defaults."""
    expected_sample_root = (
        default_sample_settings.BASE_DIR / "sample" / "templates_bootstrap"
    )
    expected_test_root = (
        default_test_settings.BASE_DIR + "/sample/templates_bootstrap"
    )

    assert bootstrap_sample_settings.TEMPLATES[0]["DIRS"][0] == expected_sample_root, (
        "Bootstrap sample settings should put their local sample template root first."
    )
    assert bootstrap_sample_settings.TEMPLATES[0]["DIRS"][1:] == default_sample_settings.TEMPLATES[0]["DIRS"], (
        "Bootstrap sample settings should retain the default template search roots after their overlay."
    )
    assert bootstrap_test_settings.TEMPLATES[0]["DIRS"][0] == expected_test_root, (
        "Bootstrap test settings should mirror the Bootstrap sample template-root overlay."
    )
    assert bootstrap_test_settings.TEMPLATES[0]["DIRS"][1:] == default_test_settings.TEMPLATES[0]["DIRS"], (
        "Bootstrap test settings should retain the default template search roots after their overlay."
    )
    assert "POWERCRUD_TEMPLATE_PACK" not in default_sample_settings.POWERCRUD_SETTINGS, (
        "Default sample settings must keep compatible implicit DaisyUI selection."
    )
    assert "POWERCRUD_TEMPLATE_PACK" not in default_test_settings.POWERCRUD_SETTINGS, (
        "Default test settings must keep compatible implicit DaisyUI selection."
    )


def test_bootstrap_settings_select_the_shared_catalogue_and_bootstrap_pack():
    """Bootstrap presentation settings must reuse the existing project and sample app."""
    for presentation_settings in (bootstrap_sample_settings, bootstrap_test_settings):
        assert presentation_settings.ROOT_URLCONF == default_sample_settings.ROOT_URLCONF, (
            "Bootstrap presentation settings must retain the shared sample URL catalogue."
        )
        assert "sample" in presentation_settings.INSTALLED_APPS, (
            "Bootstrap presentation settings must retain the existing sample application."
        )
        assert presentation_settings.POWERCRUD_SETTINGS["POWERCRUD_TEMPLATE_PACK"] == BOOTSTRAP_SELECTOR, (
            "Bootstrap presentation settings must select the optional Bootstrap template pack at startup."
        )
        assert presentation_settings.POWERCRUD_SETTINGS["POWERCRUD_CSS_FRAMEWORK"] == "bootstrap5", (
            "Framework-named sample fragments must resolve to the Bootstrap presentation."
        )
        assert presentation_settings.SAMPLE_PRESENTATION == "Bootstrap 5 pack", (
            "Bootstrap presentation settings must identify the active sample presentation."
        )


def test_development_compose_publishes_the_bootstrap_sample_port():
    """The documented side-by-side Bootstrap server must be reachable from the host."""
    compose_path = default_sample_settings.BASE_DIR.parent / "docker" / "docker-compose.yml"
    compose = compose_path.read_text(encoding="utf-8")

    assert "- 8001:8001" in compose, (
        "The development Compose configuration must retain the default sample port."
    )
    assert "- 8002:8002" in compose, (
        "The development Compose configuration must publish the documented Bootstrap sample port."
    )


def test_bootstrap_sample_base_selects_only_the_bootstrap_vite_entry():
    """The Bootstrap shell must load its Vite entry without DaisyUI or Tailwind assets."""
    base_path = bootstrap_sample_settings.TEMPLATES[0]["DIRS"][0] / "sample" / "base.html"
    base = base_path.read_text(encoding="utf-8")

    assert "{% vite_asset 'config/static/js/bootstrap5.js' %}" in base, (
        "The Bootstrap sample base should load the Bootstrap Vite entry."
    )
    assert "config/static/js/main.js" not in base, (
        "The Bootstrap sample base must not load the default DaisyUI Vite entry."
    )
    assert "tailwind" not in base.lower() and "daisy" not in base.lower(), (
        "The Bootstrap sample base must not declare DaisyUI or Tailwind assets or classes."
    )
    assert "hx-headers='{\"X-CSRFToken\": \"{{ csrf_token }}\"}'" in base, (
        "The Bootstrap sample base must preserve the shared HTMX CSRF header."
    )


def test_bootstrap_manual_static_base_selects_only_bootstrap_vendor_assets():
    """The manual-static route must use Bootstrap without Vite or DaisyUI vendors."""
    base_path = (
        bootstrap_sample_settings.TEMPLATES[0]["DIRS"][0]
        / "sample"
        / "manual_static"
        / "base.html"
    )
    base = base_path.read_text(encoding="utf-8")

    for asset in (
        "node_modules/bootstrap/dist/css/bootstrap.min.css",
        "node_modules/bootstrap/dist/js/bootstrap.bundle.min.js",
        "powercrud/contrib/bootstrap5/css/bootstrap5.css",
        "powercrud/contrib/bootstrap5/js/bootstrap5.js",
    ):
        assert asset in base, f"Bootstrap manual-static base should load {asset}."

    assert "django_vite" not in base, (
        "Bootstrap manual-static base should not load Vite template tags."
    )
    assert "daisy" not in base.lower() and "tippy" not in base.lower(), (
        "Bootstrap manual-static base must not retain DaisyUI or Tippy assets."
    )
    assert '{% include "sample/_runtime_meta.html" %}' in base, (
        "Bootstrap manual-static base should retain the shared runtime metadata footer."
    )


def test_bootstrap_sample_base_preserves_shared_navigation_and_runtime_metadata():
    """The Bootstrap shell should change presentation only, not sample destinations."""
    base_path = bootstrap_sample_settings.TEMPLATES[0]["DIRS"][0] / "sample" / "base.html"
    base = base_path.read_text(encoding="utf-8")

    for route_name in (
        "'home'",
        "'sample:bigbook-list'",
        "'sample:annotated-book-list'",
        "'sample:powerfield-book-list'",
        "'sample:author-list'",
        "'sample:profile-list'",
        "'sample:genre-list'",
        "'sample:asynctaskrecord-list'",
    ):
        assert route_name in base, (
            f"Bootstrap sample navigation should retain the {route_name} destination."
        )

    for role_label in (
        "Book List buttons",
        "Annotated Book List buttons",
        "PowerField Book List buttons",
        "Author List buttons",
        "Profile buttons",
        "Genre List buttons",
        "Async dashboard buttons",
    ):
        assert role_label in base, (
            f"Bootstrap sample navigation should retain the {role_label} group label."
        )

    assert '{% include "sample/_runtime_meta.html" %}' in base, (
        "Bootstrap sample pages should retain the shared runtime metadata placement."
    )


@pytest.mark.django_db
@pytest.mark.skipif(
    settings.POWERCRUD_SETTINGS.get("POWERCRUD_TEMPLATE_PACK") != BOOTSTRAP_SELECTOR,
    reason="This response-level assertion runs under the derived Bootstrap settings only.",
)
def test_bootstrap_home_renders_the_selected_vite_asset_and_shared_shell(client):
    """The derived Bootstrap settings should render the Bootstrap sample base at runtime."""
    response = client.get(reverse("home"))
    response_text = response.content.decode()

    assert response.status_code == 200, "Bootstrap sample home should render successfully."
    assert "bootstrap5-" in response_text, (
        "Bootstrap sample home should emit the packaged Bootstrap Vite asset."
    )
    assert 'data-sample-runtime-meta="true"' in response_text, (
        "Bootstrap sample home should retain the shared runtime metadata shell."
    )
    assert 'aria-label="Book List buttons"' in response_text, (
        "Bootstrap sample home should retain the shared Book navigation group."
    )
