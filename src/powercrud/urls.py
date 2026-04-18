from django.apps import apps
from django.urls import include, path

from .async_manager import AsyncManager

app_name = "powercrud"  # Default namespace

urlpatterns = [
    AsyncManager.get_url(name="async_progress"),
]

if apps.is_installed("powercrud.contrib.favourites"):
    urlpatterns.append(
        path(
            "favourites/",
            include("powercrud.contrib.favourites.urls"),
        )
    )
