"""AppConfig for the optional PowerCRUD favourites contrib app."""

from django.apps import AppConfig


class PowercrudFavouritesConfig(AppConfig):
    """Configure the optional saved favourites contrib app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "powercrud.contrib.favourites"
    verbose_name = "PowerCRUD favourites"

    def ready(self) -> None:
        """Register favourites system checks when Django loads the app."""

        from . import checks

        del checks
