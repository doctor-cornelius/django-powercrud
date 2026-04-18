"""Admin registration for the optional PowerCRUD favourites contrib app."""

from django.contrib import admin

from .models import SavedFilterFavourite


@admin.register(SavedFilterFavourite)
class SavedFilterFavouriteAdmin(admin.ModelAdmin):
    """Admin view for saved list favourites."""

    list_display = ("name", "view_key", "user", "updated_at")
    list_filter = ("view_key", "updated_at")
    search_fields = ("name", "view_key", "user__username", "user__email")
