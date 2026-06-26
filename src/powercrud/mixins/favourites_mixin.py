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

    def get_current_list_state(
        self,
        filterset=None,
        list_column_state=None,
    ) -> dict[str, object]:
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

        state = {
            "filters": filters,
            "visible_filters": self.get_requested_visible_filter_names(filterset),
            "sort": self.request.GET.get("sort", "").strip(),
            "page_size": self.request.GET.get("page_size", "").strip(),
        }
        if getattr(list_column_state, "enabled", False):
            state["visible_columns"] = list(list_column_state.active_columns)
        return state

    def get_current_list_state_json(
        self,
        filterset=None,
        list_column_state=None,
    ) -> str:
        """Return the current list state serialized for HTML transport."""

        return json.dumps(
            self.get_current_list_state(
                filterset,
                list_column_state=list_column_state,
            ),
            sort_keys=True,
        )

    def get_filter_favourite_user(self, request):
        """Return the user whose saved filter favourites should render for a request."""

        from powercrud.contrib.favourites.services import get_filter_favourite_user

        return get_filter_favourite_user(request)

    def get_saved_filter_favourites(self) -> list[object]:
        """Return saved favourites for the current authenticated user and view."""

        if not self.get_favourites_contrib_installed():
            return []

        favourite_user = self.get_filter_favourite_user(self.request)
        if not favourite_user or not favourite_user.is_authenticated:
            return []

        from powercrud.contrib.favourites.services import get_saved_favourites_for_user

        return get_saved_favourites_for_user(
            user=favourite_user,
            view_key=self.get_favourites_key(),
        )

    def get_favourites_context(
        self,
        filterset=None,
        list_column_state=None,
    ) -> dict[str, object]:
        """Build template context for the optional favourites toolbar."""

        enabled = self.get_favourites_enabled()
        save_form = None

        if not enabled:
            return {
                "filter_favourites_enabled": False,
                "saved_filter_favourites": [],
            }
        favourite_user = self.get_filter_favourite_user(self.request)
        can_manage = bool(favourite_user and favourite_user.is_authenticated)
        current_state = self.get_current_list_state(
            filterset,
            list_column_state=list_column_state,
        )
        current_state_json = json.dumps(current_state, sort_keys=True)
        saved_filter_favourites = []
        selected_filter_favourite_id = None
        selected_filter_favourite_name = ""

        if can_manage:
            from powercrud.contrib.favourites.forms import FavouriteSaveForm
            from powercrud.contrib.favourites.services import find_matching_saved_favourite

            saved_filter_favourites = self.get_saved_filter_favourites()
            selected_favourite = find_matching_saved_favourite(
                saved_filter_favourites,
                current_state,
            )
            if selected_favourite:
                selected_filter_favourite_id = selected_favourite.pk
                selected_filter_favourite_name = selected_favourite.name

            save_form = FavouriteSaveForm(
                initial={
                    "view_key": self.get_favourites_key(),
                    "list_view_url": self.request.path,
                    "toolbar_dom_id": self.get_favourites_toolbar_dom_id(),
                    "current_state_json": current_state_json,
                    "state_json": current_state_json,
                    "original_target": self.get_original_target(),
                    "selected_favourite_id": selected_filter_favourite_id,
                }
            )

        return {
            "filter_favourites_enabled": True,
            "filter_favourites_can_manage": can_manage,
            "filter_favourites_requires_login": not can_manage,
            "filter_favourites_view_key": self.get_favourites_key(),
            "filter_favourites_toolbar_dom_id": self.get_favourites_toolbar_dom_id(),
            "current_list_state_json": current_state_json,
            "selected_filter_favourite_id": selected_filter_favourite_id,
            "selected_filter_favourite_name": selected_filter_favourite_name,
            "show_filter_favourite_save_form": False,
            "filter_favourite_save_form": save_form,
            "saved_filter_favourites": saved_filter_favourites,
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
        list_column_state = kwargs.get("list_column_state") or context.get(
            "list_column_state"
        )
        context.update(
            self.get_favourites_context(
                filterset,
                list_column_state=list_column_state,
            )
        )
        return context
