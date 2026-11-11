from django.apps import AppConfig

from powercrud.logging import get_logger

log = get_logger(__name__)


class powercrudConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "powercrud"
    verbose_name = "powercrud"

    def ready(self):
        """Register coordinator worker signals when django-q2 is installed."""
        from django.apps import apps

        if apps.is_installed("django_q"):
            from powercrud._coordinator.q2 import register_signals

            register_signals()

    # def ready(self):
    #         # Example: ensure cleanup interval is reasonable
    #         interval = get_powercrud_setting('CLEANUP_SCHEDULE_INTERVAL')
    #         if interval < 60:
    #             raise ImproperlyConfigured("CLEANUP_SCHEDULE_INTERVAL must be >= 60 seconds")
