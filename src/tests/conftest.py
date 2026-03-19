"""Shared pytest fixtures for cross-suite test isolation."""

import pytest
from django.core.cache import caches


@pytest.fixture(autouse=True)
def clear_powercrud_test_caches():
    """Clear shared test caches around each test to prevent async-state leakage."""
    for alias in ("default", "powercrud_async"):
        try:
            caches[alias].clear()
        except Exception:
            continue

    yield

    for alias in ("default", "powercrud_async"):
        try:
            caches[alias].clear()
        except Exception:
            continue
