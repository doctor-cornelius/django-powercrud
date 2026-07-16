"""Durable test-only proof that two pack identities may share DaisyUI."""

from django.template.loader import get_template
from django.test import override_settings

from powercrud.template_pack_validation import validate_template_pack
from powercrud.template_packs import (
    get_template_pack_server_adapter,
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
    assert fixture_pack.server_adapter == standard_pack.server_adapter, (
        "The fixture should explicitly reuse the same public server adapter path."
    )
    assert not fixture_pack.assets.stylesheets and fixture_pack.assets.browser_adapter is None, (
        "The fixture must not claim its own stylesheet or browser adapter."
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


def test_same_adapter_fixture_resolves_the_reused_public_server_adapter():
    """Selection should import the explicitly declared reusable public adapter."""
    with override_settings(
        POWERCRUD_SETTINGS={"POWERCRUD_TEMPLATE_PACK": SAME_ADAPTER_SELECTOR}
    ):
        assert get_template_pack_server_adapter().api_version == 1, (
            "The fixture should resolve the declared DaisyUI server adapter without a framework registry."
        )
