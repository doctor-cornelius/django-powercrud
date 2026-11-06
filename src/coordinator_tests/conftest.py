import shutil

import pytest
from django.conf import settings
from django.core.cache import caches


@pytest.fixture(scope="session", autouse=True)
def release_coordinator_test_resources():
    """Clear and remove only the temporary resources owned by this suite."""
    yield
    for alias in ("default", "coordinator_async"):
        caches[alias].clear()
    shutil.rmtree(settings.TEST_CACHE_DIR, ignore_errors=True)


@pytest.fixture(scope="session", autouse=True)
def reject_powercrud_consumer_imports():
    """Detect CRUD or sample imports after coordinator tests have completed."""
    yield
    import sys

    forbidden = [
        module_name
        for module_name in sys.modules
        if module_name == "sample"
        or module_name.startswith("sample.")
        or module_name == "powercrud.mixins"
        or module_name.startswith("powercrud.mixins.")
        or module_name == "powercrud.views"
        or module_name.startswith("powercrud.views.")
    ]
    assert not forbidden, f"Coordinator suite imported consumer modules: {forbidden}"
