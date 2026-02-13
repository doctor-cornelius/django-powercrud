import pytest
from django.test import override_settings

from powercrud.conf import get_powercrud_setting, DEFAULTS
from powercrud.logging import get_logger, BASE_LOGGER_NAME
from powercrud.validators import PowerCRUDMixinValidator


def test_get_powercrud_setting_prefers_user_value():
    with override_settings(
        POWERCRUD_SETTINGS={"TAILWIND_SAFELIST_JSON_LOC": "custom/path"}
    ):
        assert get_powercrud_setting("TAILWIND_SAFELIST_JSON_LOC") == "custom/path"


def test_get_powercrud_setting_falls_back_to_default():
    with override_settings(POWERCRUD_SETTINGS={}):
        assert get_powercrud_setting("CACHE_NAME") == DEFAULTS["CACHE_NAME"]


def test_get_powercrud_setting_allows_explicit_default_override():
    with override_settings(POWERCRUD_SETTINGS={}):
        assert get_powercrud_setting("UNKNOWN_KEY", default="fallback") == "fallback"


def test_get_logger_uses_namespaced_children():
    logger = get_logger("module.submodule")
    assert logger.name == f"{BASE_LOGGER_NAME}.module.submodule"
    root_logger = get_logger()
    assert root_logger.name == BASE_LOGGER_NAME


def test_validator_rejects_non_string_fields():
    with pytest.raises(ValueError):
        PowerCRUDMixinValidator(fields=[123])


def test_validator_requires_target_for_htmx():
    with pytest.raises(ValueError):
        PowerCRUDMixinValidator(use_htmx=True, default_htmx_target=None)


def test_validator_accepts_valid_payload():
    validator = PowerCRUDMixinValidator(
        namespace="sample",
        templates_path="powercrud/daisyUI",
        base_template_path="powercrud/base.html",
        use_crispy=False,
        fields=["title"],
        properties=["isbn"],
        exclude=[],
        properties_exclude=[],
        detail_fields=["title"],
        detail_exclude=[],
        detail_properties=["isbn"],
        detail_properties_exclude=[],
        use_modal=False,
        modal_id="modal",
        modal_target="target",
        use_htmx=True,
        default_htmx_target="#content",
        hx_trigger={"refresh": True},
        form_fields=["title"],
        form_fields_exclude=["isbn"],
        table_pixel_height_other_page_elements=0,
        table_max_height=50,
        table_max_col_width=20,
    )
    assert validator.hx_trigger == {"refresh": True}


def test_validator_rejects_bad_hx_trigger():
    with pytest.raises(ValueError):
        PowerCRUDMixinValidator(use_htmx=False, hx_trigger={1: "value"})


def test_validator_rejects_bad_form_fields():
    with pytest.raises(ValueError):
        PowerCRUDMixinValidator(form_fields=[1, 2, 3])


def test_validator_rejects_invalid_bulk_fields():
    with pytest.raises(ValueError):
        PowerCRUDMixinValidator(bulk_fields=[123])


def test_validator_rejects_invalid_dropdown_sort_options():
    with pytest.raises(ValueError):
        PowerCRUDMixinValidator(dropdown_sort_options={"author": 1})


def test_validator_accepts_dropdown_sort_options():
    validator = PowerCRUDMixinValidator(
        namespace="sample",
        templates_path="powercrud/daisyUI",
        base_template_path="powercrud/base.html",
        use_crispy=False,
        fields=["title"],
        properties=["isbn"],
        exclude=[],
        properties_exclude=[],
        detail_fields=["title"],
        detail_exclude=[],
        detail_properties=["isbn"],
        detail_properties_exclude=[],
        use_modal=False,
        modal_id="modal",
        modal_target="target",
        use_htmx=False,
        form_fields=["title"],
        form_fields_exclude=[],
        table_pixel_height_other_page_elements=0,
        table_max_height=50,
        table_max_col_width=20,
        dropdown_sort_options={"author": "-name"},
    )
    assert validator.dropdown_sort_options == {"author": "-name"}
