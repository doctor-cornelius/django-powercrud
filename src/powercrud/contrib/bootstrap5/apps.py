"""Django application configuration for the optional Bootstrap 5 pack."""

from django.apps import AppConfig


class PowercrudBootstrap5Config(AppConfig):
    """Register optional Bootstrap 5 templates and static assets."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "powercrud.contrib.bootstrap5"
    verbose_name = "PowerCRUD Bootstrap 5 pack"
