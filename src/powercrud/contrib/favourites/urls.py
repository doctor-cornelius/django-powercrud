"""URL patterns for the optional PowerCRUD favourites contrib app."""

from django.urls import path

from . import views


urlpatterns = [
    path("toolbar/", views.favourites_toolbar, name="favourites-toolbar"),
    path("save/", views.favourite_save, name="favourites-save"),
    path("apply/", views.favourite_apply, name="favourites-apply"),
    path("update/", views.favourite_update, name="favourites-update"),
    path("delete/", views.favourite_delete, name="favourites-delete"),
]
