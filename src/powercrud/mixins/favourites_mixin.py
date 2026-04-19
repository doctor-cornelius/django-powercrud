"""Core list-state helpers for the optional favourites contrib app."""

from __future__ import annotations

import hashlib
import json

from django.apps import apps
from neapolitan.views import Role


class FavouritesMixin:
    """Expose optional favourites hooks without hard-coupling core to contrib."""

    filter_favourites_enabled = False
    favourites_app_label = "powercrud.contrib.favourites"

    def get_favourites_contrib_installed(self) -> bool:
        """Return True when the optional favourites contrib app is installed."""

        return apps.is_installed(self.favourites_app_label)

    def get_favourites_routes_available(self) -> bool:
        """Return True when the shared favourites endpoints are mounted."""

        if not self.get_favourites_contrib_installed():
            return False

        from powercrud.contrib.favourites.services import favourites_routes_available

        return favourites_routes_available()

    def get_favourites_enabled(self) -> bool:
        """Return True when favourites should render for the current list view."""

        return (
            self.role == Role.LIST
            and bool(getattr(self, "filter_favourites_enabled", False))
            and self.get_favourites_contrib_installed()
            and self.get_favourites_routes_available()
        )

    def get_favourites_key(self) -> str:
        """Return the derived favourites scope key for this CRUD/list view."""

        return f"{self.__class__.__module__}.{self.__class__.__name__}"

    def get_favourites_toolbar_dom_id(self) -> str:
        """Return a stable DOM id for the favourites toolbar container."""

        key = self.get_favourites_key()
        digest = hashlib.md5(key.encode("utf-8")).hexdigest()[:10]
        return f"powercrud-favourites-toolbar-{digest}"

    def get_current_list_state(self, filterset=None) -> dict[str, object]:
        """Return normalized list state suitable for saved favourites."""

        filters: dict[str, list[str]] = {}
        for field_name in self.get_effective_filter_names(filterset):
            values = [
                str(value)
                for value in self.request.GET.getlist(field_name)
                if str(value).strip()
            ]
            if values:
                filters[field_name] = values

        return {
            "filters": filters,
            "visible_filters": self.get_requested_visible_filter_names(filterset),
            "sort": self.request.GET.get("sort", "").strip(),
            "page_size": self.request.GET.get("page_size", "").strip(),
        }

    def get_current_list_state_json(self, filterset=None) -> str:
        """Return the current list state serialized for HTML transport."""

        return json.dumps(self.get_current_list_state(filterset), sort_keys=True)

    def get_saved_filter_favourites(self) -> list[object]:
        """Return saved favourites for the current authenticated user and view."""

        request_user = getattr(self.request, "user", None)
        if not request_user or not request_user.is_authenticated:
            return []

        from powercrud.contrib.favourites.services import get_saved_favourites_for_user

        return get_saved_favourites_for_user(
            user=request_user,
            view_key=self.get_favourites_key(),
        )

    def get_favourites_context(self, filterset=None) -> dict[str, object]:
        """Build template context for the optional favourites toolbar."""

        enabled = self.get_favourites_enabled()
        request_user = getattr(self.request, "user", None)
        can_manage = bool(request_user and request_user.is_authenticated)
        save_form = None

        if not enabled:
            return {
                "filter_favourites_enabled": False,
                "saved_filter_favourites": [],
            }
        current_state_json = self.get_current_list_state_json(filterset)

        if can_manage:
            from powercrud.contrib.favourites.forms import FavouriteSaveForm

            save_form = FavouriteSaveForm(
                initial={
                    "view_key": self.get_favourites_key(),
                    "list_view_url": self.request.path,
                    "toolbar_dom_id": self.get_favourites_toolbar_dom_id(),
                    "current_state_json": current_state_json,
                    "state_json": current_state_json,
                    "original_target": self.get_original_target(),
                }
            )

        return {
            "filter_favourites_enabled": True,
            "filter_favourites_can_manage": can_manage,
            "filter_favourites_requires_login": not can_manage,
            "filter_favourites_view_key": self.get_favourites_key(),
            "filter_favourites_toolbar_dom_id": self.get_favourites_toolbar_dom_id(),
            "current_list_state_json": current_state_json,
            "show_filter_favourite_save_form": False,
            "filter_favourite_save_form": save_form,
            "saved_filter_favourites": self.get_saved_filter_favourites()
            if can_manage
            else [],
            "filter_favourites_toolbar_url": self.safe_reverse(
                "powercrud:favourites-toolbar"
            ),
            "filter_favourites_save_url": self.safe_reverse("powercrud:favourites-save"),
            "filter_favourites_apply_url": self.safe_reverse(
                "powercrud:favourites-apply"
            ),
            "filter_favourites_update_url": self.safe_reverse(
                "powercrud:favourites-update"
            ),
            "filter_favourites_delete_url": self.safe_reverse(
                "powercrud:favourites-delete"
            ),
        }

    def get_context_data(self, **kwargs):
        """Add favourites context after filter visibility metadata has been resolved."""

        context = super().get_context_data(**kwargs)
        filterset = kwargs.get("filterset") or context.get("filterset")
        context.update(self.get_favourites_context(filterset))
        return context
