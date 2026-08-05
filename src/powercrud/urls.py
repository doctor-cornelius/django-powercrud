from django.apps import apps
from django.urls import include, path

app_name = "powercrud"  # Default namespace

urlpatterns = []

if apps.is_installed("django_q"):
    from .async_manager import AsyncManager

    urlpatterns.append(AsyncManager.get_url(name="async_progress"))

if apps.is_installed("powercrud.contrib.favourites"):
    urlpatterns.append(
        path(
            "favourites/",
            include("powercrud.contrib.favourites.urls"),
        )
    )
