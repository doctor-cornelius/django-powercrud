from django.apps import AppConfig

from powercrud.conf import get_powercrud_setting
from django.core.exceptions import ImproperlyConfigured

class powercrudConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "powercrud"
    verbose_name = "powercrud"

    # def ready(self):
    #         # Example: ensure cleanup interval is reasonable
    #         interval = get_powercrud_setting('CLEANUP_SCHEDULE_INTERVAL')
    #         if interval < 60:
    #             raise ImproperlyConfigured("CLEANUP_SCHEDULE_INTERVAL must be >= 60 seconds")