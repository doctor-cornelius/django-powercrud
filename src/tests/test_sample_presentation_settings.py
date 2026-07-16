"""Tests for the bundled sample's presentation-specific settings overlays."""

from config import settings as default_sample_settings
from config import settings_focused_overrides as focused_sample_settings
from tests import settings as default_test_settings
from tests import settings_focused_overrides as focused_test_settings


def test_focused_sample_settings_prepend_only_the_override_template_root():
    """The focused sample settings should retain the default application configuration."""
    default_template_dirs = default_sample_settings.TEMPLATES[0]["DIRS"]
    focused_template_dirs = focused_sample_settings.TEMPLATES[0]["DIRS"]

    assert focused_template_dirs[1:] == default_template_dirs, (
        "Focused sample settings should retain the default template search order after "
        "their prepended override root."
    )
    assert focused_template_dirs[0] == (
        default_sample_settings.BASE_DIR / "sample" / "template_overrides" / "focused"
    ), "Focused sample settings should prepend only the focused override directory."
    assert focused_sample_settings.ROOT_URLCONF == default_sample_settings.ROOT_URLCONF, (
        "Focused sample settings should retain the default URL configuration."
    )
    assert focused_sample_settings.INSTALLED_APPS == default_sample_settings.INSTALLED_APPS, (
        "Focused sample settings should retain the default installed applications."
    )
    assert focused_sample_settings.SAMPLE_PRESENTATION == "Standard DaisyUI + Book overrides", (
        "Focused sample settings should identify the focused-override presentation."
    )


def test_focused_test_settings_prepend_only_the_override_template_root():
    """Focused test settings should mirror the sample overlay without mutating defaults."""
    default_template_dirs = default_test_settings.TEMPLATES[0]["DIRS"]
    focused_template_dirs = focused_test_settings.TEMPLATES[0]["DIRS"]

    assert focused_template_dirs[1:] == default_template_dirs, (
        "Focused test settings should retain the default test template search order after "
        "their prepended override root."
    )
    assert focused_template_dirs[0] == (
        default_test_settings.BASE_DIR
        + "/sample/template_overrides/focused"
    ), "Focused test settings should prepend only the focused override directory."
    assert focused_test_settings.ROOT_URLCONF == default_test_settings.ROOT_URLCONF, (
        "Focused test settings should retain the default URL configuration."
    )
    assert focused_test_settings.INSTALLED_APPS == default_test_settings.INSTALLED_APPS, (
        "Focused test settings should retain the default installed applications."
    )
    assert focused_test_settings.SAMPLE_PRESENTATION == "Standard DaisyUI + Book overrides", (
        "Focused test settings should identify the focused-override presentation."
    )
