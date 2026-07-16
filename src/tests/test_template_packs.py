"""Focused contract tests for dormant Phase 4 template-pack discovery."""

from dataclasses import replace
from importlib import import_module
import warnings

import pytest
from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from powercrud.contrib.bootstrap5.apps import PowercrudBootstrap5Config
from powercrud.contrib.bootstrap5.styles import (
    get_bootstrap5_framework_styles,
    get_bootstrap5_view_help_style,
)
from powercrud.contrib.bootstrap5.templatetags.powercrud_bootstrap5 import (
    bootstrap5_field,
    bootstrap5_text_alignment,
)
from powercrud.template_packs import (
    DECLARABLE_PRESENTATION_OPTIONS,
    PackAssets,
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

    assert template_pack.identity == "daisyui", "The built-in identity must remain DaisyUI."
    assert template_pack.contract_version == TEMPLATE_PACK_CONTRACT_VERSION, (
        "The built-in declaration must use the public v1 contract."
    )
    assert template_pack.server_adapter == "powercrud.packs.daisyui.adapter:server_adapter", (
        "The built-in declaration must use its public server adapter."
    )
    assert template_pack.assets.stylesheets == (), (
        "DaisyUI relies on the application's compiled framework stylesheet, not a second pack CSS file."
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
    with pytest.raises(ValueError, match="stylesheets"):
        replace(template_pack, assets=PackAssets(stylesheets=["pack.css"]))
    with pytest.raises(ValueError, match="unknown presentation"):
        replace(
            template_pack,
            unsupported_presentation_options=frozenset({"unknown_option"}),
        )


def test_presentation_contract_separates_portable_and_framework_specific_options():
    """First-party packs must use one explicit vocabulary for presentation limits."""
    from powercrud.template_packs import (
        FRAMEWORK_SPECIFIC_PRESENTATION_OPTIONS,
        PORTABLE_PRESENTATION_OPTIONS,
    )

    assert PORTABLE_PRESENTATION_OPTIONS.isdisjoint(
        FRAMEWORK_SPECIFIC_PRESENTATION_OPTIONS
    ), "A presentation option must be either portable or framework-specific."
    assert DECLARABLE_PRESENTATION_OPTIONS == (
        PORTABLE_PRESENTATION_OPTIONS | FRAMEWORK_SPECIFIC_PRESENTATION_OPTIONS
    ), "Pack declarations must validate against the complete public presentation vocabulary."

    template_pack = resolve_template_pack("daisyui")
    with pytest.raises(ValueError, match="cannot exclude portable"):
        replace(
            template_pack,
            unsupported_presentation_options=frozenset({"modal_presentation"}),
        )


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
    with override_settings(
        POWERCRUD_SETTINGS={
            "POWERCRUD_TEMPLATE_PACK": "powercrud.contrib.bootstrap5:template_pack"
        }
    ):
        bootstrap = get_selected_template_pack()

    assert builtin.identity == "daisyui", "An explicit built-in selector should resolve DaisyUI."
    assert third_party.identity == "fixture-pack", (
        "A module.path:attribute selector should resolve the third-party declaration."
    )
    assert bootstrap.identity == "bootstrap5", (
        "A module.path:attribute selector should resolve the Bootstrap declaration."
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


def test_bootstrap_honours_portable_help_and_deprecates_legacy_modal_classes():
    """Bootstrap should not misclassify portable settings as unsupported."""
    from powercrud.mixins.config_mixin import ConfigMixin
    from powercrud.template_packs import TemplatePackCompatibilityWarning
    from sample.models import Book

    class UnsupportedBootstrapPresentationView(ConfigMixin):
        """Small configuration harness that opts into Bootstrap-incompatible styling."""

        model = Book
        view_help = {
            "summary": "Help",
        "details": "Bootstrap translates this styling through its own variables.",
            "color": "info",
            "min_width": "52rem",
        }
        modal_classes = "modal custom-shell"
        modal_body_classes = "custom-body"

    with override_settings(
        POWERCRUD_SETTINGS={
            "POWERCRUD_TEMPLATE_PACK": "powercrud.contrib.bootstrap5:template_pack"
        }
    ):
        with warnings.catch_warnings(record=True) as recorded_warnings:
            warnings.simplefilter("always")
            UnsupportedBootstrapPresentationView()

    compatibility_warnings = [
        warning
        for warning in recorded_warnings
        if issubclass(warning.category, TemplatePackCompatibilityWarning)
    ]
    warning_messages = {str(item.message) for item in recorded_warnings}
    assert not compatibility_warnings, (
        "Portable Bootstrap help and legacy raw classes should not use the unsupported-option warning path."
    )
    assert any("modal_classes" in message for message in warning_messages), (
        "An explicit Bootstrap modal shell class should emit its deprecation warning."
    )
    assert any("modal_body_classes" in message for message in warning_messages), (
        "An explicit Bootstrap modal body class should emit its deprecation warning."
    )


def test_default_presentation_values_do_not_warn_for_bootstrap():
    """Bootstrap should stay quiet when an application uses portable defaults only."""
    from powercrud.mixins.config_mixin import ConfigMixin
    from powercrud.template_packs import TemplatePackCompatibilityWarning
    from sample.models import Book

    class DefaultBootstrapPresentationView(ConfigMixin):
        """Small configuration harness retaining every presentation default."""

        model = Book

    with override_settings(
        POWERCRUD_SETTINGS={
            "POWERCRUD_TEMPLATE_PACK": "powercrud.contrib.bootstrap5:template_pack"
        }
    ):
        with warnings.catch_warnings(record=True) as recorded_warnings:
            warnings.simplefilter("always")
            DefaultBootstrapPresentationView()

    compatibility_warnings = [
        warning
        for warning in recorded_warnings
        if issubclass(warning.category, TemplatePackCompatibilityWarning)
    ]
    assert not compatibility_warnings, (
        "Bootstrap defaults should not generate compatibility noise for every view."
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


def test_default_framework_style_override_point_uses_the_selected_public_adapter():
    """HtmxMixin must expose the selected pack's adapter presentation only."""
    from powercrud.mixins.htmx_mixin import HtmxMixin

    class AdapterView(HtmxMixin):
        """Provide the small configuration surface required by HtmxMixin."""

        def get_modal_id(self):
            """Return one stable modal identifier."""
            return "#modal"

        def get_modal_target(self):
            """Return one stable modal target identifier."""
            return "#modal-content"

        def get_use_htmx(self):
            """Enable HTMX for the adapter context."""
            return True

        def get_use_modal(self):
            """Enable modal rendering for the adapter context."""
            return True

    styles = AdapterView().get_framework_styles()
    assert set(styles) == {"daisyui"}, (
        "The public adapter path must expose only the selected declaration identity."
    )
    assert styles["daisyui"]["modal_attrs"] == 'data-powercrud-modal-trigger="true"', (
        "Modal triggers must now use the framework-neutral semantic hook."
    )


def test_pack_without_legacy_copy_destination_uses_its_safe_identity():
    """External packs use their own identity as the whole-tree copy destination."""
    with override_settings(POWERCRUD_SETTINGS={"POWERCRUD_TEMPLATE_PACK": FIXTURE_SELECTOR}):
        assert get_template_pack_copy_destination() == "fixture-pack", (
            "A generic external pack must have a deterministic project copy destination."
        )


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
    ],
)
def test_invalid_declared_contracts_are_rejected(monkeypatch, replacement, message):
    """Public v1 declarations reject malformed metadata without framework whitelists."""
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


def test_bootstrap_helpers_cover_the_optional_pack_public_surface():
    """Bootstrap helpers should render the supported widgets and semantic styles."""

    class BootstrapForm(forms.Form):
        """Exercise the native widgets exposed by the Bootstrap template tags."""

        name = forms.CharField(help_text="Shown to collaborators")
        enabled = forms.BooleanField(required=False)
        category = forms.ChoiceField(choices=(("fiction", "Fiction"),))
        attachment = forms.FileField(required=False)

    invalid_form = BootstrapForm(data={"name": "", "category": "fiction"})
    assert not invalid_form.is_valid()
    invalid_name = bootstrap5_field(invalid_form["name"])
    assert "form-control is-invalid" in invalid_name
    assert 'aria-describedby="id_name_help id_name_errors"' in invalid_name
    assert 'aria-invalid="true"' in invalid_name

    valid_form = BootstrapForm(data={"name": "Example", "category": "fiction"})
    assert valid_form.is_valid()
    assert "form-check-input pc-inline-checkbox" in bootstrap5_field(valid_form["enabled"], small=True)
    assert "form-select form-select-sm" in bootstrap5_field(valid_form["category"], small=True)
    assert "form-control" in bootstrap5_field(valid_form["attachment"], include_help=False)

    assert [bootstrap5_text_alignment(value) for value in ("left", "center", "right", "unknown", None)] == [
        "start",
        "center",
        "end",
        "start",
        "start",
    ]
    assert "--pc-view-help-border: var(--bs-border-color)" in get_bootstrap5_view_help_style("base")
    assert "rgb(var(--bs-danger-rgb))" in get_bootstrap5_view_help_style("error")
    assert "#123abc" in get_bootstrap5_view_help_style("#123abc")

    first_styles = get_bootstrap5_framework_styles(object())
    first_styles["bootstrap5"]["actions"]["View"] = "changed"
    assert get_bootstrap5_framework_styles(object())["bootstrap5"]["actions"]["View"] == "btn-info"

    config = PowercrudBootstrap5Config("powercrud.contrib.bootstrap5", import_module("powercrud.contrib.bootstrap5"))
    assert config.name == "powercrud.contrib.bootstrap5"
    assert config.verbose_name == "PowerCRUD Bootstrap 5 pack"
