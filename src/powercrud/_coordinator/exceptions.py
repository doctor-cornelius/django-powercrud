"""Typed configuration failures raised by explicit coordinator operations."""

from django.core.exceptions import ImproperlyConfigured


class AsyncConfigurationError(ImproperlyConfigured):
    """An explicit async operation cannot run with the current configuration."""


class AsyncDisabledError(AsyncConfigurationError):
    """A new async launch was requested while launches are disabled."""
