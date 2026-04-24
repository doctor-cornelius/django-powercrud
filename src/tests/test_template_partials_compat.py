"""Tests for Django template partial compatibility across supported versions."""

import django
from pathlib import Path
from django.conf import settings
from django.template import Context, Template


def test_powercrud_partials_tag_loads_and_renders_partial():
    """The PowerCRUD shim should render partials on Django 5.2 and Django 6."""

    template = Template(
        "{% load powercrud_partials %}"
        "{% partialdef greeting %}Hello {{ name }}{% endpartialdef %}"
        "{% partial greeting %}"
    )

    rendered = template.render(Context({"name": "PowerCRUD"}))

    assert rendered == "Hello PowerCRUD", (
        "The powercrud_partials shim should make partialdef/partial render across supported Django versions."
    )


def test_template_partials_app_is_only_configured_before_django_6():
    """Django 5.2 needs the third-party loader app, but Django 6 ships partials in core."""

    has_template_partials_app = "template_partials" in settings.INSTALLED_APPS

    assert has_template_partials_app is (django.VERSION < (6, 0)), (
        "template_partials should only be installed while running Django versions before 6.0."
    )


def test_template_partials_builtin_is_not_required_by_test_settings():
    """PowerCRUD templates should load the compatibility shim instead of relying on builtins."""

    builtins = settings.TEMPLATES[0]["OPTIONS"].get("builtins", [])

    assert "template_partials.templatetags.partials" not in builtins, (
        "Test settings should not expose template_partials as a global builtin; templates load "
        "powercrud_partials explicitly."
    )


def test_templates_using_partials_load_powercrud_partials():
    """Templates with partial tags should load the compatibility shim explicitly."""

    template_roots = [
        Path(settings.BASE_DIR) / "powercrud" / "templates",
        Path(settings.BASE_DIR) / "sample" / "templates",
    ]
    missing_loads = []

    for template_root in template_roots:
        for template_path in template_root.rglob("*.html"):
            template_source = template_path.read_text()
            uses_partials = "{% partial" in template_source or "{%  partial" in template_source
            loads_powercrud_partials = "{% load powercrud_partials" in template_source
            if uses_partials and not loads_powercrud_partials:
                missing_loads.append(str(template_path.relative_to(settings.BASE_DIR)))

    assert missing_loads == [], (
        "Templates using partial tags must load powercrud_partials explicitly: "
        f"{', '.join(missing_loads)}"
    )
