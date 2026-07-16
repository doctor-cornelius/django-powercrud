"""Tests for Django template partial compatibility across supported versions."""

import django
from pathlib import Path
from django.conf import settings
from django.template import Context, Template
from django.template.loader import get_template


LEGACY_NAMED_PARTIALS = {
    "object_list.html": (
        "pcrud_content",
        "bulk_selection_status",
        "filtered_results",
        "list_actions",
        "filter_trigger",
        "filter_panel_actions",
        "filter_form",
        "list_columns",
        "pagination",
        "page_size_selector",
    ),
    "object_form.html": ("pcrud_content", "conflict_detected", "normal_content"),
    "object_detail.html": ("pcrud_content",),
    "object_confirm_delete.html": ("pcrud_content", "conflict_detected", "normal_content"),
    "bulk_edit_form.html": ("full_form", "async_queue_success"),
    "crispy_partials.html": ("load_tags", "crispy_form"),
    "partial/list.html": ("inline_row_display", "inline_row_form"),
    "partial/bulk_edit_errors.html": ("bulk_edit_error", "bulk_edit_conflict"),
}


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


def test_relocated_daisyui_sources_and_legacy_facades_have_matching_inventory():
    """The atomic move retains every historic path without two editable source trees."""
    templates_root = Path(settings.BASE_DIR) / "powercrud" / "templates" / "powercrud"
    source_root = templates_root / "packs" / "daisyui"
    legacy_root = templates_root / "daisyUI"
    source_paths = {
        path.relative_to(source_root).as_posix()
        for path in source_root.rglob("*.html")
    }
    legacy_paths = {
        path.relative_to(legacy_root).as_posix()
        for path in legacy_root.rglob("*.html")
    }

    assert len(source_paths) == 45, (
        "The relocated compatible DaisyUI pack should contain the characterized 45 templates."
    )
    assert legacy_paths == source_paths, (
        "Every relocated template should retain its matching powercrud/daisyUI compatibility path."
    )
    stale_references = [
        path.relative_to(source_root).as_posix()
        for path in source_root.rglob("*.html")
        if "powercrud/daisyUI" in path.read_text(encoding="utf-8")
    ]
    assert stale_references == [], (
        "The permanent source tree must not include the legacy namespace: "
        f"{', '.join(stale_references)}"
    )


def test_relocated_daisyui_templates_and_legacy_named_partials_compile():
    """Both namespaces must load every root and server-addressable named fragment."""
    templates_root = Path(settings.BASE_DIR) / "powercrud" / "templates" / "powercrud"
    source_root = templates_root / "packs" / "daisyui"
    relative_paths = sorted(
        path.relative_to(source_root).as_posix()
        for path in source_root.rglob("*.html")
    )

    for namespace in ("powercrud/packs/daisyui", "powercrud/daisyUI"):
        for relative_path in relative_paths:
            template_name = f"{namespace}/{relative_path}"
            assert get_template(template_name) is not None, (
                f"The {template_name} template should compile through its supported namespace."
            )
        for relative_path, partial_names in LEGACY_NAMED_PARTIALS.items():
            for partial_name in partial_names:
                template_name = f"{namespace}/{relative_path}#{partial_name}"
                assert get_template(template_name) is not None, (
                    f"The {template_name} named partial should remain server-addressable."
                )
