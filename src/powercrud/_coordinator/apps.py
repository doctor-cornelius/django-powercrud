"""Minimal Django startup hook for standalone coordinator applications."""

from django.apps import AppConfig


class CoordinatorConfig(AppConfig):
    """Register coordinator q2 signals without loading PowerCRUD integration."""

    name = "powercrud._coordinator"
    label = "powercrud_coordinator"

    def ready(self):
        """Connect worker identity signals only when django-q2 is installed."""
        from django.apps import apps

        if apps.is_installed("django_q"):
            from .q2 import register_signals

            register_signals()
