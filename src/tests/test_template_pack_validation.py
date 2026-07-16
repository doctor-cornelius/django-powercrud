"""Tests for reusable development and CI template-pack validation."""

from dataclasses import replace

import pytest
from django.conf import settings
from django.template import TemplateDoesNotExist

from powercrud import template_pack_validation as validation
from powercrud.template_pack_validation import (
    TemplatePackValidationError,
    validate_template_pack,
)
from powercrud.template_pack_testing import assert_template_pack_conforms
from powercrud.template_packs import (
    BrowserAdapterSpec,
    CrispyIntegration,
    PackAssets,
    PackageResource,
    resolve_template_pack,
)


BOOTSTRAP_SELECTOR = "powercrud.contrib.bootstrap5:template_pack"


def test_validator_accepts_the_default_daisyui_production_pack():
    """The default DaisyUI pack should satisfy the reusable validation contract."""
    validate_template_pack(resolve_template_pack("daisyui"))


@pytest.mark.skipif(
    settings.SETTINGS_MODULE != "tests.settings_bootstrap",
    reason="Bootstrap validation requires the optional Bootstrap settings overlay.",
)
def test_validator_accepts_the_bootstrap_production_pack():
    """The Bootstrap pack should satisfy the reusable validation contract when selected."""
    validate_template_pack(resolve_template_pack(BOOTSTRAP_SELECTOR))


def test_validator_reports_declaration_failures_together():
    """Declaration mistakes should be actionable without fixing them one at a time."""
    template_pack = replace(
        resolve_template_pack("daisyui"),
        capabilities=frozenset({"list", "form", "detail", "async", "unknown"}),
        server_adapter="tests.template_pack_fixtures:missing_adapter",
        assets=PackAssets(
            stylesheets=("compact.css",),
            copy_roots=(PackageResource("tests", "template_packs/missing"),),
            browser_adapter=BrowserAdapterSpec(
                api_version=2,
                static_path="compact.js",
                source=PackageResource("tests", "template_packs/missing.js"),
            ),
        ),
        supports_native_forms=False,
        crispy_integrations=(CrispyIntegration("unknown", "unknown_dependency"),),
    )

    with pytest.raises(TemplatePackValidationError) as error:
        validate_template_pack(template_pack)

    message = str(error.value)
    for expected_fragment in (
        "unknown capabilities: unknown",
        "missing baseline capabilities: delete",
        "capability 'async' requires: bulk",
        "cannot import server_adapter",
        "missing stylesheet 'compact.css'",
        "missing copy root",
        "browser adapter API 2",
        "missing browser adapter static path 'compact.js'",
        "missing browser adapter source",
        "must support native Django forms",
        "unknown_dependency",
    ):
        assert expected_fragment in message, (
            "The validator should report every independent declaration mistake in one "
            f"result; missing {expected_fragment!r}."
        )


def test_validator_reports_missing_package_resources():
    """A declaration cannot point at a package directory that was not distributed."""
    template_pack = replace(
        resolve_template_pack("daisyui"),
        identity="missing-resources",
        template_namespace="powercrud/packs/missing_resources",
        template_resource_root="templates/powercrud/packs/missing_resources",
    )

    with pytest.raises(TemplatePackValidationError, match="template resource root"):
        validate_template_pack(template_pack)


def test_validator_reports_a_missing_direct_fragment(monkeypatch):
    """Required server-rendered fragments should fail independently of file discovery."""
    original_get_template = validation.get_template

    def get_template_without_pagination(template_name):
        """Simulate a loader that cannot resolve the list pagination fragment."""
        if template_name.endswith("object_list.html#pagination"):
            raise TemplateDoesNotExist(template_name)
        return original_get_template(template_name)

    monkeypatch.setattr(validation, "get_template", get_template_without_pagination)

    with pytest.raises(TemplatePackValidationError, match="object_list.html#pagination"):
        validate_template_pack(resolve_template_pack("daisyui"))


def test_validator_reports_a_missing_focused_component(monkeypatch):
    """Every advertised focused override point must be a validated package resource."""
    original_get_template = validation.get_template

    def get_template_without_table_header(template_name):
        """Simulate a pack whose focused table-header template is unavailable."""
        if template_name.endswith("partial/table_header.html"):
            raise TemplateDoesNotExist(template_name)
        return original_get_template(template_name)

    monkeypatch.setattr(validation, "get_template", get_template_without_table_header)

    with pytest.raises(TemplatePackValidationError, match="partial/table_header.html"):
        validate_template_pack(resolve_template_pack("daisyui"))


def test_validator_reports_an_unavailable_declared_crispy_integration(monkeypatch):
    """Declared crispy support must name an installable integration dependency."""
    original_find_spec = validation.find_spec

    def find_no_crispy_tailwind(module_name):
        """Hide the declared crispy integration while preserving unrelated lookups."""
        if module_name == "crispy_tailwind":
            return None
        return original_find_spec(module_name)

    monkeypatch.setattr(validation, "find_spec", find_no_crispy_tailwind)

    with pytest.raises(TemplatePackValidationError, match="crispy_tailwind"):
        validate_template_pack(resolve_template_pack("daisyui"))


def test_public_author_test_helper_returns_the_validated_declaration():
    """External package tests can validate their declaration without test internals."""
    template_pack = assert_template_pack_conforms(
        "tests.template_pack_fixtures:same_adapter_template_pack"
    )

    assert template_pack.identity == "same-adapter-fixture"
