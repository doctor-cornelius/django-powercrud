import importlib
import sys


def _reload_powercrud_mixins():
    """
    Remove cached mixin modules so imports see the current settings.
    """
    for name in list(sys.modules.keys()):
        if name == "powercrud.mixins" or name.startswith("powercrud.mixins."):
            sys.modules.pop(name, None)
    return importlib.import_module("powercrud.mixins")


def test_powercrud_mixin_imports_without_async_stack():
    """
    Smoke-test that importing PowerCRUDMixin does not require async dependencies
    such as django_q or POWERCRUD_SETTINGS. When run under tests.settings_minimal
    this simulates a minimal project that has not enabled async at all.
    """
    mixins_module = _reload_powercrud_mixins()
    assert hasattr(mixins_module, "PowerCRUDMixin")
