"""Durable test-only proof that two pack identities may share DaisyUI."""

from django.template.loader import get_template
from django.test import override_settings

from powercrud.template_pack_validation import validate_template_pack
from powercrud.template_packs import (
    get_template_pack_styles,
    resolve_template_pack,
)


SAME_ADAPTER_SELECTOR = "tests.template_pack_fixtures:same_adapter_template_pack"


def test_same_adapter_fixture_has_distinct_resources_and_validates():
    """The fixture must keep its own namespace while reusing the standard adapter."""
    standard_pack = resolve_template_pack("daisyui")
    fixture_pack = resolve_template_pack(SAME_ADAPTER_SELECTOR)

    assert fixture_pack.identity != standard_pack.identity, (
        "The durable fixture must prove a genuinely distinct template-pack identity."
    )
    assert fixture_pack.template_namespace != standard_pack.template_namespace, (
        "The durable fixture must keep independently addressable template resources."
    )
    assert fixture_pack.framework_adapter == standard_pack.framework_adapter == "daisyui", (
        "The distinct pack identities should reuse the one supported DaisyUI adapter."
    )
    assert fixture_pack.variant_adapter is None and not fixture_pack.manual_assets and not fixture_pack.vite_assets, (
        "The fixture must not copy an adapter, declare a variant, or add functional assets."
    )

    validate_template_pack(fixture_pack)
    for template_name in (
        "object_list.html#pcrud_content",
        "object_list.html#filtered_results",
        "object_list.html#pagination",
        "object_form.html#pcrud_content",
        "object_form.html#normal_content",
        "object_detail.html#pcrud_content",
        "object_confirm_delete.html#pcrud_content",
        "object_confirm_delete.html#normal_content",
    ):
        get_template(f"{fixture_pack.template_namespace}/{template_name}")


def test_same_adapter_fixture_selects_existing_daisyui_styles_without_sample_settings():
    """Selection should retain existing adapter styles without becoming a visible pack."""
    with override_settings(
        POWERCRUD_SETTINGS={"POWERCRUD_TEMPLATE_PACK": SAME_ADAPTER_SELECTOR}
    ):
        assert get_template_pack_styles({"daisyui": "shared adapter styles"}) == "shared adapter styles", (
            "The fixture should resolve the existing adapter style entry rather than a copied one."
        )
