import logging

import pytest
from django.test import override_settings

from powercrud.conf import get_powercrud_setting, DEFAULTS
from powercrud.logging import get_logger, BASE_LOGGER_NAME
from powercrud.validators import PowerCRUDMixinValidator


def test_get_powercrud_setting_prefers_user_value():
    with override_settings(POWERCRUD_SETTINGS={"TAILWIND_SAFELIST_JSON_LOC": "custom/path"}):
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
