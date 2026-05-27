"""List-column visibility helpers for PowerCRUD list views."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
    QueryDict,
)
from django.shortcuts import redirect
from neapolitan.views import Role

from .config_mixin import resolve_class_config

LIST_OPTIONS_SESSION_KEY = "powercrud_list_options"


@dataclass(frozen=True)
class ListColumnChoice:
    """One selectable data column in the list-column chooser."""

    name: str
    label: str
    is_active: bool
    is_default: bool
    is_property: bool


@dataclass(frozen=True)
class ListColumnState:
    """Resolved list-column state for one request."""

    enabled: bool
    allowed_columns: tuple[str, ...]
    default_columns: tuple[str, ...]
    active_columns: tuple[str, ...]
    choices: tuple[ListColumnChoice, ...]


class ListOptionsMixin:
    """Resolve and persist opt-in list-column visibility state."""

    list_options_action: str | None = None

    @classmethod
    def has_list_options_urls(cls) -> bool:
        """Return True when the class declares list-options endpoints."""

        cfg = resolve_class_config(cls)
        list_options_enabled = getattr(cfg, "list_options_enabled", None)
        if list_options_enabled is not None:
            return bool(list_options_enabled)
        return getattr(cfg, "default_list_fields", None) is not None

    def get_list_options_enabled(self) -> bool:
        """Return True when this list view has opted into selectable columns."""

        list_options_enabled = getattr(self.config(), "list_options_enabled", None)
        declared_enabled = (
            bool(list_options_enabled)
            if list_options_enabled is not None
            else getattr(self.config(), "default_list_fields", None) is not None
        )
        return (
            getattr(self, "role", None) == Role.LIST
            and declared_enabled
        )

    def get_list_options_key(self) -> str:
        """Return the stable preference scope key for this CRUD/list view."""

        return f"{self.__class__.__module__}.{self.__class__.__name__}"

    def get_list_options_endpoint_name(self) -> str | None:
        """Return the URL name that serves list-column preference updates."""

        return f"{self.get_prefix()}-columns"

    def get_allowed_list_columns(self, queryset: Any | None = None) -> list[str]:
        """Return selectable data-column names in render order."""

        fields = list(getattr(self.config(), "fields", []) or [])
        properties = list(getattr(self.config(), "properties", []) or [])
        if queryset is not None:
            self.validate_list_fields_against_queryset(fields, queryset)
        return self._dedupe_preserving_first([*fields, *properties])

    def get_default_list_columns(self, queryset: Any | None = None) -> list[str]:
        """Return default visible data-column names in allowed-column order."""

        allowed_columns = self.get_allowed_list_columns(queryset=queryset)
        default_columns = getattr(self.config(), "default_list_fields", None)
        if default_columns is None:
            return allowed_columns

        if queryset is not None:
            field_defaults = [
                column_name
                for column_name in default_columns
                if column_name in getattr(self.config(), "fields", [])
            ]
            self.validate_list_fields_against_queryset(
                field_defaults,
                queryset,
                config_name="default_list_fields",
            )

        default_set = set(default_columns)
        resolved_defaults = [
            column_name for column_name in allowed_columns if column_name in default_set
        ]
        if not resolved_defaults:
            raise ValueError("default_list_fields must resolve to at least one column")
        missing_columns = [
            column_name
            for column_name in default_columns
            if column_name not in allowed_columns
        ]
        if missing_columns:
            raise ValueError(
                "The following default_list_fields are not valid list columns: "
                f"{', '.join(missing_columns)}"
            )
        return resolved_defaults

    def normalise_visible_list_columns(
        self,
        raw_columns: Any,
        *,
        queryset: Any | None = None,
        fallback_to_default: bool = True,
    ) -> list[str]:
        """Return a valid active-column list from arbitrary submitted/saved state."""

        allowed_columns = self.get_allowed_list_columns(queryset=queryset)
        default_columns = self.get_default_list_columns(queryset=queryset)

        if isinstance(raw_columns, (list, tuple)):
            requested = [str(value).strip() for value in raw_columns if str(value).strip()]
        else:
            requested = []

        requested_set = set(self._dedupe_preserving_first(requested))
        resolved = [
            column_name for column_name in allowed_columns if column_name in requested_set
        ]
        if resolved:
            return resolved
        if fallback_to_default:
            return default_columns
        return []

    def get_saved_list_column_state(self) -> dict[str, Any] | None:
        """Return saved session-backed list-column state for this request."""

        request = getattr(self, "request", None)
        session = getattr(request, "session", None)
        if session is None:
            return None

        state_store = session.get(LIST_OPTIONS_SESSION_KEY, {})
        if not isinstance(state_store, dict):
            return None

        state = state_store.get(self.get_list_options_key())
        if not isinstance(state, dict):
            return None
        return state

    def save_list_column_state(self, active_columns: list[str]) -> None:
        """Store visible list-column state for this view in the current session."""

        request = getattr(self, "request", None)
        session = getattr(request, "session", None)
        if session is None:
            return

        raw_state_store = session.get(LIST_OPTIONS_SESSION_KEY, {})
        state_store = dict(raw_state_store) if isinstance(raw_state_store, dict) else {}
        state_store[self.get_list_options_key()] = {"visible_columns": active_columns}
        session[LIST_OPTIONS_SESSION_KEY] = state_store
        self._mark_list_options_session_modified(session)

    def clear_list_column_state(self) -> None:
        """Clear visible list-column state for this view from the current session."""

        request = getattr(self, "request", None)
        session = getattr(request, "session", None)
        if session is None:
            return

        raw_state_store = session.get(LIST_OPTIONS_SESSION_KEY, {})
        if not isinstance(raw_state_store, dict):
            session.pop(LIST_OPTIONS_SESSION_KEY, None)
            self._mark_list_options_session_modified(session)
            return

        state_store = dict(raw_state_store)
        state_store.pop(self.get_list_options_key(), None)
        if state_store:
            session[LIST_OPTIONS_SESSION_KEY] = state_store
        else:
            session.pop(LIST_OPTIONS_SESSION_KEY, None)
        self._mark_list_options_session_modified(session)

    def _mark_list_options_session_modified(self, session: Any) -> None:
        """Mark Django session objects as modified after nested state changes."""

        if hasattr(session, "modified"):
            session.modified = True

    def get_active_list_columns(self, queryset: Any | None = None) -> list[str]:
        """Return the active visible data columns for this request."""

        if not self.get_list_options_enabled():
            return self.get_allowed_list_columns(queryset=queryset)

        state = self.get_saved_list_column_state()
        if state is None:
            return self.get_default_list_columns(queryset=queryset)

        return self.normalise_visible_list_columns(
            state.get("visible_columns", []),
            queryset=queryset,
        )

    def build_list_column_state(self, queryset: Any | None = None) -> ListColumnState:
        """Build template-friendly list-column state for this request."""

        allowed_columns = self.get_allowed_list_columns(queryset=queryset)
        default_columns = self.get_default_list_columns(queryset=queryset)
        active_columns = self.get_active_list_columns(queryset=queryset)
        active_set = set(active_columns)
        default_set = set(default_columns)
        properties = set(getattr(self.config(), "properties", []) or [])
        choices = tuple(
            ListColumnChoice(
                name=column_name,
                label=self.get_list_column_label(column_name, queryset=queryset),
                is_active=column_name in active_set,
                is_default=column_name in default_set,
                is_property=column_name in properties,
            )
            for column_name in allowed_columns
        )
        return ListColumnState(
            enabled=self.get_list_options_enabled(),
            allowed_columns=tuple(allowed_columns),
            default_columns=tuple(default_columns),
            active_columns=tuple(active_columns),
            choices=choices,
        )

    def get_list_column_label(
        self,
        column_name: str,
        queryset: Any | None = None,
    ) -> str:
        """Return the display label for one list-column chooser option."""

        if column_name in (getattr(self.config(), "properties", []) or []):
            prop_obj = getattr(self.model, column_name, None)
            if (
                prop_obj
                and hasattr(prop_obj.fget, "short_description")
                and prop_obj.fget.short_description
            ):
                return str(prop_obj.fget.short_description)
            return column_name.replace("_", " ").title()

        field = self._get_effective_list_field(column_name, queryset=queryset)
        verbose_name = getattr(field, "verbose_name", None)
        if verbose_name:
            return str(verbose_name).title()
        return column_name.replace("_", " ").title()

    def _get_effective_list_field(
        self,
        column_name: str,
        queryset: Any | None = None,
    ):
        """Return model or queryset-annotation field metadata for a list column."""

        try:
            return self.model._meta.get_field(column_name)
        except Exception:
            annotation_getter = getattr(self, "_get_queryset_annotation_output_field", None)
            if callable(annotation_getter):
                return annotation_getter(column_name, queryset=queryset)
        return None

    def list(self, request, *args, **kwargs):
        """Handle list requests, including list-column preference updates."""

        if getattr(self, "list_options_action", None) == "columns":
            return self.handle_list_columns_request(request, *args, **kwargs)
        return super().list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Route list-column preference POSTs before CRUD form handling."""

        if getattr(self, "list_options_action", None) == "columns":
            return self.handle_list_columns_request(request, *args, **kwargs)
        return super().post(request, *args, **kwargs)

    def handle_list_columns_request(self, request, *args, **kwargs):
        """Validate, persist, and redirect after a list-column chooser submit."""

        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])
        if not self.get_list_options_enabled():
            return HttpResponseBadRequest("List options are not enabled for this view.")

        queryset = self.get_queryset()
        action = request.POST.get("list_columns_action", "apply").strip() or "apply"
        if action == "reset":
            self.clear_list_column_state()
            active_columns = self.get_default_list_columns(queryset=queryset)
        else:
            active_columns = self.normalise_visible_list_columns(
                request.POST.getlist("visible_columns"),
                queryset=queryset,
                fallback_to_default=False,
            )
            if not active_columns:
                return HttpResponseBadRequest("Select at least one list column.")
            self.save_list_column_state(active_columns)

        target_url = self.build_list_columns_target_url(
            active_columns=active_columns,
        )
        if getattr(request, "htmx", False):
            response = HttpResponse()
            hx_location_payload = {
                "path": target_url,
                "push": target_url,
            }
            original_target = self.get_original_target()
            if original_target:
                hx_location_payload["target"] = original_target
                hx_location_payload["swap"] = "innerHTML"
            response["HX-Location"] = json.dumps(hx_location_payload)
            return response

        return redirect(target_url)

    def build_list_columns_target_url(self, *, active_columns: list[str]) -> str:
        """Return the list URL to load after list-column state changes."""

        query = QueryDict("", mutable=True)
        for key, values in self.request.POST.lists():
            if key in {
                "csrfmiddlewaretoken",
                "visible_columns",
                "list_columns_action",
                "list_view_url",
                "page",
            }:
                continue
            for value in values:
                query.appendlist(key, value)

        sort_param = query.get("sort", "")
        sort_column = sort_param[1:] if sort_param.startswith("-") else sort_param
        if sort_column and sort_column not in active_columns:
            query.pop("sort", None)

        target_url = self.request.POST.get("list_view_url", "").strip() or self.request.path
        if query:
            target_url = f"{target_url}?{query.urlencode()}"
        return target_url
