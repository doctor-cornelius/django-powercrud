"""Database models for saved PowerCRUD list favourites."""

from django.conf import settings
from django.db import models


class SavedFilterFavourite(models.Model):
    """Persist a named saved list/filter state for one user and CRUD view."""

    NAME_MAX_LENGTH = 30

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="powercrud_saved_filter_favourites",
    )
    view_key = models.CharField(max_length=255)
    name = models.CharField(max_length=NAME_MAX_LENGTH)
    state = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Saved-favourite metadata."""

        ordering = ("name", "pk")
        constraints = [
            models.UniqueConstraint(
                fields=("user", "view_key", "name"),
                name="uniq_powercrud_favourite_user_view_name",
            )
        ]

    def __str__(self) -> str:
        """Return a readable label for Django admin and debugging."""

        return f"{self.name} ({self.view_key})"
