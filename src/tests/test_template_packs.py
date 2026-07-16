"""Focused contract tests for dormant Phase 4 template-pack discovery."""

from dataclasses import replace
from importlib import import_module

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from powercrud.template_packs import (
    TEMPLATE_PACK_CONTRACT_VERSION,
    TemplatePack,
    get_configured_template_pack,
    get_template_pack_copy_destination,
    get_selected_template_pack,
    get_template_pack_style_key,
    get_template_pack_styles,
    get_template_pack_template_namespace,
    resolve_template_pack,
)


FIXTURE_SELECTOR = "tests.template_pack_fixtures:template_pack"


def test_builtin_daisyui_declaration_describes_the_relocated_implementation():
    """The built-in declaration must describe the permanent pack source namespace."""
    template_pack = resolve_template_pack("daisyui")

    assert template_pack == TemplatePack(
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
    ), (
        "The built-in declaration should exactly describe the relocated compatible DaisyUI "
        "implementation and require no additional browser assets."
    )


def test_template_pack_is_immutable_and_validates_declaration_shape():
    """Pack authors receive a frozen declaration with clear early shape failures."""
    template_pack = resolve_template_pack("daisyui")

    with pytest.raises(AttributeError):
        template_pack.identity = "other"
    with pytest.raises(ValueError, match="contract_version"):
        replace(template_pack, contract_version=True)
    with pytest.raises(ValueError, match="template_resource_root"):
        replace(template_pack, template_resource_root="../templates")
    with pytest.raises(ValueError, match="legacy_copy_destination"):
        replace(template_pack, legacy_copy_destination="../daisyui")
    with pytest.raises(ValueError, match="legacy_copy_destination"):
        replace(template_pack, legacy_copy_destination="nested/daisyui")
    with pytest.raises(ValueError, match="legacy_copy_destination"):
        replace(template_pack, legacy_copy_destination="daisy\\ui")
    with pytest.raises(ValueError, match="capabilities"):
        replace(template_pack, capabilities={"list"})
    with pytest.raises(ValueError, match="manual_assets"):
        replace(template_pack, manual_assets=["pack.js"])


def test_unconfigured_selector_uses_builtin_without_adding_a_conf_default():
    """Absence remains distinguishable so legacy fallback survives the next slice."""
    with override_settings(POWERCRUD_SETTINGS={}):
        template_pack = get_selected_template_pack()

    assert template_pack.identity == "daisyui", (
        "An absent new selector should select the compatible built-in pack."
    )


def test_unconfigured_default_uses_the_relocated_builtin_source():
    """The canonical legacy default must activate the permanent pack source."""
    with override_settings(POWERCRUD_SETTINGS={}):
        template_pack = get_configured_template_pack()

    assert template_pack is not None, (
        "The canonical daisyUI legacy default should resolve the compatible built-in pack "
        "rather than the generic legacy fallback."
    )
    assert template_pack.template_namespace == "powercrud/packs/daisyui", (
        "An unconfigured project should render from the relocated permanent DaisyUI source."
    )


def test_explicit_null_selector_is_an_invalid_configuration():
    """Only an absent selector receives the compatible built-in default."""
    with override_settings(POWERCRUD_SETTINGS={"POWERCRUD_TEMPLATE_PACK": None}):
        with pytest.raises(ImproperlyConfigured, match="non-empty"):
            get_selected_template_pack()


def test_explicit_builtin_and_third_party_selectors_resolve():
    """Built-in aliases and public third-party declaration paths are both supported."""
    with override_settings(POWERCRUD_SETTINGS={"POWERCRUD_TEMPLATE_PACK": "daisyui"}):
        builtin = get_selected_template_pack()
    with override_settings(POWERCRUD_SETTINGS={"POWERCRUD_TEMPLATE_PACK": FIXTURE_SELECTOR}):
        third_party = get_selected_template_pack()

    assert builtin.identity == "daisyui", "An explicit built-in selector should resolve DaisyUI."
    assert third_party.identity == "fixture-pack", (
        "A module.path:attribute selector should resolve the third-party declaration."
    )


def test_resolution_helpers_preserve_legacy_fallback_until_selection_is_explicit():
    """The new selector cannot override a legacy namespace merely by being absent."""
    with override_settings(POWERCRUD_SETTINGS={"POWERCRUD_CSS_FRAMEWORK": "legacy"}):
        assert get_configured_template_pack() is None, (
            "An absent selector should retain the distinct legacy-fallback state."
        )
        assert get_template_pack_template_namespace() == "powercrud/legacy", (
            "Legacy CSS settings should continue to supply the view-template namespace."
        )
        assert get_template_pack_style_key() == "legacy", (
            "Legacy CSS settings should continue to supply the style dictionary key."
        )
    with override_settings(POWERCRUD_SETTINGS={"POWERCRUD_TEMPLATE_PACK": "daisyui"}):
        assert get_template_pack_template_namespace() == "powercrud/packs/daisyui", (
            "An explicit built-in selector should supply its declared template namespace."
        )
        assert get_template_pack_style_key() == "daisyui", (
            "Explicit selection should report the pack's canonical adapter identity."
        )


def test_config_mixin_resolves_selected_namespace_at_runtime():
    """A real ConfigMixin instance must not retain an import-time template default."""
    from powercrud.mixins.config_mixin import ConfigMixin
    from sample.models import Book

    class RuntimeConfigView(ConfigMixin):
        """Small concrete configuration harness for template-path resolution."""

        model = Book

    view = RuntimeConfigView()
    with override_settings(POWERCRUD_SETTINGS={"POWERCRUD_CSS_FRAMEWORK": "legacy"}):
        assert view.config().templates_path == "powercrud/legacy", (
            "ConfigMixin should apply the legacy fallback while no new selector exists."
        )
    with override_settings(POWERCRUD_SETTINGS={"POWERCRUD_TEMPLATE_PACK": "daisyui"}):
        assert view.config().templates_path == "powercrud/packs/daisyui", (
            "ConfigMixin should reread an explicit template pack after class import."
        )


def test_explicit_daisyui_selection_preserves_legacy_style_overrides():
    """The selected adapter must remain compatible with existing style dictionaries."""
    from powercrud.mixins.htmx_mixin import HtmxMixin

    class LegacyStyleView(HtmxMixin):
        """Represent a downstream override that exposes only the legacy key."""

        def get_framework_styles(self):
            """Return the historical public DaisyUI style dictionary shape."""
            return {"daisyUI": {"filter_attrs": {}}}

    with override_settings(POWERCRUD_SETTINGS={"POWERCRUD_TEMPLATE_PACK": "daisyui"}):
        styles = get_template_pack_styles(LegacyStyleView().get_framework_styles())

    assert styles == {"filter_attrs": {}}, (
        "Explicit DaisyUI selection should not require downstream style overrides to rename "
        "their established daisyUI key."
    )


def test_explicit_pack_style_lookup_prefers_the_canonical_adapter_key():
    """New overrides may adopt the canonical key without losing compatibility fallback."""
    styles = {"daisyui": {"source": "canonical"}, "daisyUI": {"source": "legacy"}}

    with override_settings(POWERCRUD_SETTINGS={"POWERCRUD_TEMPLATE_PACK": "daisyui"}):
        resolved = get_template_pack_styles(styles)

    assert resolved == {"source": "canonical"}, (
        "The selected-pack adapter key should win when a style override offers both keys."
    )


def test_default_framework_style_override_point_delegates_to_the_daisyui_pack(monkeypatch):
    """HtmxMixin keeps its public override method while the built-in provider relocates."""
    from powercrud.mixins import htmx_mixin as htmx_module

    view = htmx_module.HtmxMixin()
    received_views = []
    expected_styles = {"daisyUI": {"source": "pack"}}

    def fake_pack_styles(received_view):
        """Capture the public mixin instance passed to the pack provider."""
        received_views.append(received_view)
        return expected_styles

    monkeypatch.setattr(htmx_module, "get_daisyui_framework_styles", fake_pack_styles)

    assert view.get_framework_styles() == expected_styles, (
        "The established HtmxMixin override point should return the DaisyUI pack provider's "
        "mapping by default."
    )
    assert received_views == [view], (
        "The DaisyUI style provider should receive the view so modal attributes remain dynamic."
    )


def test_pack_without_legacy_copy_destination_cannot_request_whole_tree_copy():
    """Phase 4 must not invent a third-party whole-tree destination convention."""
    with override_settings(POWERCRUD_SETTINGS={"POWERCRUD_TEMPLATE_PACK": FIXTURE_SELECTOR}):
        with pytest.raises(ImproperlyConfigured, match="whole-tree copy destination"):
            get_template_pack_copy_destination()


def test_selector_and_module_attribute_are_read_without_caching(monkeypatch):
    """Settings and declarations can change between calls during a running process."""
    fixture_module = import_module("tests.template_pack_fixtures")
    first = fixture_module.template_pack
    second = replace(first, identity="fixture-pack-second")

    with override_settings(POWERCRUD_SETTINGS={"POWERCRUD_TEMPLATE_PACK": FIXTURE_SELECTOR}):
        assert get_selected_template_pack() is first, (
            "The first call should resolve the current third-party module attribute."
        )
        monkeypatch.setattr(fixture_module, "template_pack", second)
        assert get_selected_template_pack() is second, (
            "The resolver must not cache a declaration after the first lookup."
        )
    with override_settings(POWERCRUD_SETTINGS={}):
        assert get_selected_template_pack().identity == "daisyui", (
            "The resolver must reread settings after an explicit third-party selection."
        )


@pytest.mark.parametrize(
    ("selector", "message"),
    [
        (None, "non-empty"),
        ("", "non-empty"),
        (" daisyui", "non-empty"),
        ("daisyUI", "Unknown"),
        ("unknown", "Unknown"),
        ("tests.template_pack_fixtures", "Unknown"),
        ("tests.template_pack_fixtures:template_pack:extra", "syntax"),
        ("tests..template_pack_fixtures:template_pack", "syntax"),
    ],
)
def test_invalid_selectors_raise_contextual_configuration_errors(selector, message):
    """Invalid identifiers fail before an ambiguous import can alter behaviour."""
    with pytest.raises(ImproperlyConfigured, match=message):
        resolve_template_pack(selector)


@pytest.mark.parametrize(
    ("selector", "message"),
    [
        ("tests.missing_template_pack:template_pack", "Could not import"),
        ("tests.template_pack_fixtures:missing", "declares no"),
        ("tests.template_pack_fixtures:not_a_template_pack", "must resolve"),
    ],
)
def test_unavailable_or_invalid_third_party_declarations_fail_clearly(selector, message):
    """Import and declaration failures name the selected-pack configuration error."""
    with pytest.raises(ImproperlyConfigured, match=message):
        resolve_template_pack(selector)


@pytest.mark.parametrize(
    ("replacement", "message"),
    [
        ({"contract_version": TEMPLATE_PACK_CONTRACT_VERSION + 1}, "contract version"),
        ({"identity": "daisyui"}, "reserved"),
        ({"framework_adapter": "bootstrap"}, "framework adapter"),
        ({"variant_adapter": "compact"}, "variant adapter"),
        ({"manual_assets": ("compact.js",)}, "browser assets"),
        ({"vite_assets": ("compact.js",)}, "browser assets"),
    ],
)
def test_unsupported_declared_contracts_are_rejected(monkeypatch, replacement, message):
    """Phase 4 rejects declarations that would require unavailable runtime support."""
    fixture_module = import_module("tests.template_pack_fixtures")
    monkeypatch.setattr(
        fixture_module,
        "template_pack",
        replace(fixture_module.template_pack, **replacement),
    )

    with pytest.raises(ImproperlyConfigured, match=message):
        resolve_template_pack(FIXTURE_SELECTOR)


def test_builtin_alias_cannot_resolve_a_declaration_with_another_identity(monkeypatch):
    """The built-in alias remains tied to PowerCRUD's registered identity."""
    builtin_module = import_module("powercrud.packs.daisyui")
    monkeypatch.setattr(
        builtin_module,
        "template_pack",
        replace(builtin_module.template_pack, identity="not-daisyui"),
    )

    with pytest.raises(ImproperlyConfigured, match="must resolve"):
        resolve_template_pack("daisyui")
