"""Service helpers for PowerCRUD saved favourites."""

from __future__ import annotations

from collections import OrderedDict
import json

from django.core.exceptions import ImproperlyConfigured
from django.http import QueryDict
from django.urls import NoReverseMatch, reverse
from django.utils.module_loading import import_string

from powercrud.conf import get_powercrud_setting
from powercrud.mixins.list_options_mixin import LIST_OPTIONS_SESSION_KEY

from .models import SavedFilterFavourite


REQUIRED_FAVOURITES_ROUTE_NAMES = (
    "powercrud:favourites-toolbar",
    "powercrud:favourites-save",
    "powercrud:favourites-apply",
    "powercrud:favourites-update",
    "powercrud:favourites-delete",
)


def _dedupe_preserving_order(values: list[str]) -> list[str]:
    """Return unique string values in first-seen order."""

    return list(OrderedDict.fromkeys(str(value) for value in values if str(value).strip()))


def get_required_favourites_route_names() -> tuple[str, ...]:
    """Return the named routes required for the favourites contrib UI."""

    return REQUIRED_FAVOURITES_ROUTE_NAMES


def get_unavailable_favourites_route_names() -> list[str]:
    """Return any favourites route names that are not currently reversible."""

    unavailable_routes: list[str] = []
    for route_name in REQUIRED_FAVOURITES_ROUTE_NAMES:
        try:
            reverse(route_name)
        except NoReverseMatch:
            unavailable_routes.append(route_name)
    return unavailable_routes


def favourites_routes_available() -> bool:
    """Return whether the shared favourites endpoints are mounted and reversible."""

    return not get_unavailable_favourites_route_names()


def get_filter_favourite_user(request):
    """Return the user whose saved filter favourites should be used for a request."""

    resolver = get_powercrud_setting("FILTER_FAVOURITE_USER_RESOLVER")
    if not resolver:
        return getattr(request, "user", None)

    if isinstance(resolver, str):
        try:
            resolver = import_string(resolver)
        except ImportError as exc:
            raise ImproperlyConfigured(
                "POWERCRUD_SETTINGS['FILTER_FAVOURITE_USER_RESOLVER'] must be "
                "a callable or dotted import path."
            ) from exc

    if not callable(resolver):
        raise ImproperlyConfigured(
            "POWERCRUD_SETTINGS['FILTER_FAVOURITE_USER_RESOLVER'] must be "
            "a callable or dotted import path."
        )

    return resolver(request)


def normalise_saved_state(raw_state: object) -> dict[str, object]:
    """Normalize arbitrary input into the saved favourite JSON contract."""

    if not isinstance(raw_state, dict):
        return {
            "filters": {},
            "visible_filters": [],
            "sort": "",
            "page_size": "",
        }

    raw_filters = raw_state.get("filters", {})
    normalized_filters: dict[str, list[str]] = {}
    if isinstance(raw_filters, dict):
        for field_name, values in raw_filters.items():
            if not isinstance(field_name, str) or not field_name.strip():
                continue
            if isinstance(values, (list, tuple)):
                normalized_values = [
                    str(value) for value in values if str(value).strip()
                ]
            else:
                normalized_values = [str(values)] if str(values).strip() else []
            if normalized_values:
                normalized_filters[field_name] = normalized_values

    raw_visible_filters = raw_state.get("visible_filters", [])
    if isinstance(raw_visible_filters, (list, tuple)):
        visible_filters = _dedupe_preserving_order(list(raw_visible_filters))
    else:
        visible_filters = []

    normalized_state = {
        "filters": normalized_filters,
        "visible_filters": visible_filters,
        "sort": str(raw_state.get("sort", "") or "").strip(),
        "page_size": str(raw_state.get("page_size", "") or "").strip(),
    }
    if "visible_columns" in raw_state:
        raw_visible_columns = raw_state.get("visible_columns", [])
        if isinstance(raw_visible_columns, (list, tuple)):
            visible_columns = _dedupe_preserving_order(list(raw_visible_columns))
        else:
            visible_columns = []
        normalized_state["visible_columns"] = visible_columns
    return normalized_state


def get_saved_favourites_for_user(*, user, view_key: str) -> list[SavedFilterFavourite]:
    """Return saved favourites for one user/view pair."""

    saved_favourites = list(
        SavedFilterFavourite.objects.filter(user=user, view_key=view_key).order_by(
            "name", "pk"
        )
    )
    for favourite in saved_favourites:
        normalized_state = normalise_saved_state(favourite.state)
        favourite.powercrud_normalized_state = normalized_state
        favourite.powercrud_state_json = json.dumps(normalized_state, sort_keys=True)
        favourite.powercrud_query_string = build_query_string_from_state(normalized_state)
        favourite.powercrud_visible_filters_json = json.dumps(
            normalized_state.get("visible_filters", [])
        )
    return saved_favourites


def find_matching_saved_favourite(
    saved_favourites: list[SavedFilterFavourite],
    state: object,
) -> SavedFilterFavourite | None:
    """Return the first saved favourite whose normalized state matches ``state``."""

    normalized_state = normalise_saved_state(state)
    for favourite in saved_favourites:
        favourite_state = getattr(
            favourite,
            "powercrud_normalized_state",
            normalise_saved_state(favourite.state),
        )
        comparable_state = dict(normalized_state)
        if "visible_columns" in favourite_state:
            comparable_state["visible_columns"] = sorted(
                comparable_state.get("visible_columns", [])
            )
        else:
            comparable_state.pop("visible_columns", None)
        comparable_favourite_state = {
            **favourite_state,
        }
        if "visible_columns" in favourite_state:
            comparable_favourite_state["visible_columns"] = sorted(
                favourite_state.get("visible_columns", [])
            )
        if comparable_favourite_state == comparable_state:
            return favourite
    return None


def create_saved_favourite(*, user, view_key: str, name: str, state: dict[str, object]) -> SavedFilterFavourite:
    """Create a new saved favourite record."""

    return SavedFilterFavourite.objects.create(
        user=user,
        view_key=view_key,
        name=name.strip(),
        state=normalise_saved_state(state),
    )


def build_query_string_from_state(state: dict[str, object]) -> str:
    """Serialize a saved state payload back into query parameters."""

    normalized_state = normalise_saved_state(state)
    query_dict = QueryDict(mutable=True)

    filters = normalized_state.get("filters", {})
    if isinstance(filters, dict):
        for field_name, values in filters.items():
            for value in values:
                query_dict.appendlist(field_name, value)

    for field_name in normalized_state.get("visible_filters", []):
        query_dict.appendlist("visible_filters", field_name)

    sort_value = str(normalized_state.get("sort", "") or "").strip()
    if sort_value:
        query_dict["sort"] = sort_value

    page_size = str(normalized_state.get("page_size", "") or "").strip()
    if page_size:
        query_dict["page_size"] = page_size

    return query_dict.urlencode()


def sync_visible_columns_state_to_session(
    *,
    session,
    view_key: str,
    state: dict[str, object],
) -> None:
    """Apply saved visible-column state to the session-backed list-options store."""

    normalized_state = normalise_saved_state(state)
    visible_columns = normalized_state.get("visible_columns")

    raw_state_store = session.get(LIST_OPTIONS_SESSION_KEY, {})
    state_store = dict(raw_state_store) if isinstance(raw_state_store, dict) else {}
    state_store.pop(view_key, None)

    if isinstance(visible_columns, list) and visible_columns:
        state_store[view_key] = {"visible_columns": visible_columns}

    if state_store:
        session[LIST_OPTIONS_SESSION_KEY] = state_store
    else:
        session.pop(LIST_OPTIONS_SESSION_KEY, None)
    session.modified = True


def build_toolbar_context(
    *,
    user,
    view_key: str,
    list_view_url: str,
    toolbar_dom_id: str,
    current_state_json: str,
    original_target: str,
    toolbar_url: str,
    save_url: str,
    apply_url: str,
    update_url: str,
    delete_url: str,
    selected_favourite_id: int | None = None,
    show_save_form: bool = False,
    save_form=None,
) -> dict[str, object]:
    """Build the favourites-toolbar template context for one request/view."""

    can_manage = bool(user and user.is_authenticated)
    saved_filter_favourites = (
        get_saved_favourites_for_user(
            user=user,
            view_key=view_key,
        )
        if can_manage
        else []
    )
    if selected_favourite_id is None:
        try:
            current_state = json.loads(current_state_json) if current_state_json else {}
        except json.JSONDecodeError:
            current_state = {}
        matched_favourite = find_matching_saved_favourite(
            saved_filter_favourites,
            current_state,
        )
        selected_favourite_id = matched_favourite.pk if matched_favourite else None

    selected_filter_favourite_name = ""
    if selected_favourite_id:
        selected_filter_favourite_name = next(
            (
                favourite.name
                for favourite in saved_filter_favourites
                if favourite.pk == selected_favourite_id
            ),
            "",
        )

    return {
        "filter_favourites_enabled": True,
        "filter_favourites_can_manage": can_manage,
        "filter_favourites_requires_login": not can_manage,
        "filter_favourites_view_key": view_key,
        "filter_favourites_toolbar_dom_id": toolbar_dom_id,
        "current_list_state_json": current_state_json,
        "selected_filter_favourite_id": selected_favourite_id,
        "selected_filter_favourite_name": selected_filter_favourite_name,
        "show_filter_favourite_save_form": show_save_form,
        "filter_favourite_save_form": save_form,
        "saved_filter_favourites": saved_filter_favourites,
        "filter_favourites_toolbar_url": toolbar_url,
        "filter_favourites_save_url": save_url,
        "filter_favourites_apply_url": apply_url,
        "filter_favourites_update_url": update_url,
        "filter_favourites_delete_url": delete_url,
        "list_view_url": list_view_url,
        "original_target": original_target,
    }
